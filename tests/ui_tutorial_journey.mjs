import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

function defaultChromePath() {
  if (process.platform !== "win32") return "chrome";
  const candidates = [
    process.env.PROGRAMFILES,
    process.env["PROGRAMFILES(X86)"],
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, "Programs"),
  ].filter(Boolean);
  if (candidates.length === 0) return "chrome.exe";
  return path.join(candidates[0], "Google", "Chrome", "Application", "chrome.exe");
}

const chromePath = process.env.SHAELVIEN_LITE_CHROME || defaultChromePath();
const baseUrl = process.env.SHAELVIEN_LITE_URL || "http://127.0.0.1:8790";
const profileDir = process.env.SHAELVIEN_LITE_UI_PROFILE || path.join(os.tmpdir(), "shaelvien-lite-ui-profile");
const reportPath = process.env.SHAELVIEN_LITE_UI_REPORT || path.join("verification", "ui-journey-report.json");
const phase = process.env.SHAELVIEN_LITE_UI_PHASE || "journey";
const viewport = process.env.SHAELVIEN_LITE_UI_VIEWPORT || "1200,900";
const debugPort = Number(process.env.SHAELVIEN_LITE_UI_DEBUG_PORT || "9231");
const screenshotPrefix = process.env.SHAELVIEN_LITE_UI_SCREENSHOT_PREFIX || "ui";

const run = {
  phase,
  baseUrl,
  profileDir,
  expected: [],
  observed: [],
  defects: [],
  consoleErrors: [],
  screenshots: [],
  stateChecks: [],
  startedAt: new Date().toISOString(),
};

function record(step, expected, observed, pass = true) {
  run.expected.push({ step, expected });
  run.observed.push({ step, observed, pass });
  if (!pass) run.defects.push({ step, observed });
}

async function delay(ms) {
  await new Promise((resolve) => setTimeout(resolve, ms));
}

async function bounded(promise, ms) {
  let timer;
  try {
    return await Promise.race([
      promise,
      new Promise((resolve) => {
        timer = setTimeout(() => resolve("timeout"), ms);
      }),
    ]);
  } finally {
    clearTimeout(timer);
  }
}

async function httpJson(url) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`${url} returned ${response.status}`);
  return response.json();
}

class Cdp {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.nextId = 1;
    this.pending = new Map();
    this.events = [];
  }

  async open() {
    await new Promise((resolve, reject) => {
      this.ws.addEventListener("open", resolve, { once: true });
      this.ws.addEventListener("error", reject, { once: true });
      this.ws.addEventListener("message", (event) => {
        const msg = JSON.parse(event.data);
        if (msg.id && this.pending.has(msg.id)) {
          const { resolve: ok, reject: bad } = this.pending.get(msg.id);
          this.pending.delete(msg.id);
          if (msg.error) bad(new Error(msg.error.message));
          else ok(msg.result);
        } else if (msg.method) {
          this.events.push(msg);
          if (msg.method === "Runtime.exceptionThrown") {
            run.consoleErrors.push({ type: "exception", details: msg.params });
          }
          if (msg.method === "Log.entryAdded" && ["error", "warning"].includes(msg.params.entry.level)) {
            run.consoleErrors.push({ type: "log", details: msg.params.entry });
          }
        }
      });
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }

  close() {
    this.ws.close();
  }
}

async function connectChrome() {
  await fs.mkdir(profileDir, { recursive: true });
  const chrome = spawn(chromePath, [
    `--remote-debugging-port=${debugPort}`,
    `--user-data-dir=${profileDir}`,
    `--window-size=${viewport}`,
    "--no-first-run",
    "--no-default-browser-check",
    `${baseUrl}/?ui-verification=${Date.now()}`,
  ], { stdio: "ignore", detached: false });

  let pageTarget;
  for (let i = 0; i < 80; i += 1) {
    try {
      const targets = await httpJson(`http://127.0.0.1:${debugPort}/json/list`);
      pageTarget = targets.find((target) => target.type === "page" && target.webSocketDebuggerUrl);
      if (pageTarget) break;
    } catch {
      await delay(250);
    }
  }
  if (!pageTarget?.webSocketDebuggerUrl) throw new Error("Chrome page DevTools endpoint did not start.");
  const cdp = new Cdp(pageTarget.webSocketDebuggerUrl);
  await cdp.open();
  await cdp.send("Page.enable");
  await cdp.send("Runtime.enable");
  await cdp.send("Log.enable");
  return { cdp, chrome };
}

async function evalJs(cdp, expression) {
  const result = await cdp.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text || "Runtime exception");
  return result.result.value;
}

async function waitFor(cdp, expression, label, timeoutMs = 12000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const value = await evalJs(cdp, `Boolean(${expression})`);
    if (value) return;
    await delay(250);
  }
  throw new Error(`Timed out waiting for ${label}`);
}

async function screenshot(cdp, name) {
  await fs.mkdir("verification", { recursive: true });
  const shot = await cdp.send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  const file = `verification/${name}.png`;
  await fs.writeFile(file, Buffer.from(shot.data, "base64"));
  run.screenshots.push(file);
}

async function submitAction(cdp, text) {
  await waitFor(cdp, "document.querySelector('#actionInput')", "action input");
  await evalJs(cdp, `
    (() => {
      const input = document.querySelector('#actionInput');
      input.focus();
      input.value = ${JSON.stringify(text)};
      document.querySelector('#actionForm').requestSubmit();
      return true;
    })()
  `);
  await delay(950);
}

async function bootstrapState(cdp) {
  return evalJs(cdp, `fetch('/api/bootstrap', {credentials:'same-origin'}).then(r => r.json())`);
}

async function journey(cdp) {
  await waitFor(cdp, "document.querySelector('#landing') && !document.querySelector('#landing').classList.contains('hidden')", "landing page");
  record("Open Landing Page", "Shaelvien Lite landing is visible.", "Landing page visible.");
  await screenshot(cdp, `${screenshotPrefix}-01-landing`);

  const handle = `UIVerifier${Date.now()}`;
  await evalJs(cdp, `
    (() => {
      document.querySelector('#handleInput').value = ${JSON.stringify(handle)};
      document.querySelector('#passwordInput').value = 'localpass123';
      document.querySelector('#accountForm').requestSubmit();
      return true;
    })()
  `);
  await waitFor(cdp, "document.querySelector('#shell') && !document.querySelector('#shell').classList.contains('hidden')", "account dashboard");
  record("Enter or Create Account", "Account enters through form with password.", "Dashboard visible after account entry.");

  await waitFor(cdp, "document.querySelector('#characterCreate') && !document.querySelector('#characterCreate').classList.contains('hidden')", "character creation");
  await evalJs(cdp, `
    (() => {
      document.querySelector('#characterName').value = 'Mara Test';
      document.querySelector('#characterOrigin').value = 'Verification Road';
      document.querySelector('#characterForm').requestSubmit();
      return true;
    })()
  `);
  await waitFor(cdp, "document.body.innerText.includes('Begin Tutorial')", "tutorial start button");
  record("Create Character", "Primary character is created and dashboard offers tutorial.", "Character created; Begin Tutorial visible.");

  await evalJs(cdp, `document.querySelector('#startTutorialBtn').click()`);
  await waitFor(cdp, "document.body.innerText.includes('Emberhall Outpost') && document.body.innerText.includes('Ilyra Dain')", "initial campaign scene");
  record("Enter Campaign", "Campaign starts at Emberhall Outpost.", "Emberhall Outpost and Ilyra Dain visible.");
  await screenshot(cdp, `${screenshotPrefix}-02-campaign-start`);

  await submitAction(cdp, "Speak with Ilyra at the guild hall");
  await waitFor(cdp, "document.body.innerText.includes('Forest Road is the first problem')", "NPC dialogue");
  record("Meet Initial NPC", "Guild representative responds and gives situation.", "Ilyra dialogue appears in session history.");

  await submitAction(cdp, "Accept quest");
  await waitFor(cdp, "document.body.innerText.includes('Quest accepted')", "quest accepted log");
  record("Receive Tutorial Quest", "Tutorial quest becomes active.", "Quest accepted appears in session history.");

  await submitAction(cdp, "Travel to the Forest Road");
  await waitFor(cdp, "document.body.innerText.includes('Forest Road') && document.body.innerText.includes('Fresh cart ruts')", "forest road scene");
  record("Travel to Adventure Location", "Forest Road scene appears.", "Forest Road panel and exploration text visible.");
  await screenshot(cdp, `${screenshotPrefix}-03-forest-road`);

  await submitAction(cdp, "Investigate the tracks");
  await waitFor(cdp, "document.body.innerText.includes('Roll ')", "visible skill roll");
  record("Perform a Skill Check", "Investigation check roll appears in log.", "Session history shows roll calculation.");

  await submitAction(cdp, "Attack the threat");
  await waitFor(cdp, "document.body.innerText.includes('Attack') && document.body.innerText.includes('Retreat')", "combat actions");
  record("Enter Combat", "Combat action controls appear.", "Attack, Defend, Heal, Retreat controls visible.");
  await screenshot(cdp, `${screenshotPrefix}-04-combat`);

  for (let i = 0; i < 10; i += 1) {
    const boot = await bootstrapState(cdp);
    const campaign = boot.campaigns[0];
    if (!campaign.combat) break;
    await submitAction(cdp, "Attack");
  }
  const afterCombat = await bootstrapState(cdp);
  const campaign = afterCombat.campaigns[0];
  const character = afterCombat.characters[0];
  const completed = campaign.completed_encounters.includes("road_cutpurse");
  record("Complete Combat", "Road cutpurse encounter completes.", completed ? "road_cutpurse completed." : "Encounter was not completed.", completed);
  record("Receive Item or Resource Reward", "Character receives server-issued reward.", character.currency > 20 || character.inventory.trail_rations.quantity > 2 ? "Reward visible in state." : "Reward not detected.", character.currency > 20 || character.inventory.trail_rations.quantity > 2);

  await submitAction(cdp, "Return to camp");
  await waitFor(cdp, "document.body.innerText.includes('Emberhall Outpost')", "return to outpost");
  record("Return to Settlement or Camp", "Current location returns to Emberhall Outpost.", "Emberhall Outpost visible.");

  await submitAction(cdp, "Upgrade Quarters");
  await evalJs(cdp, `document.querySelector('[data-tab="camp"]').click()`);
  await waitFor(cdp, "document.body.innerText.includes('Level 1/3')", "camp upgrade level");
  await screenshot(cdp, `${screenshotPrefix}-05-camp-upgrade`);
  record("Upgrade One Camp Structure", "Quarters reaches level 1.", "Camp tab shows Level 1/3.");

  const saved = await bootstrapState(cdp);
  run.stateChecks.push({
    step: "saved-state-after-journey",
    campaign_id: saved.campaigns[0].campaign_id,
    character_id: saved.characters[0].character_id,
    location: saved.campaigns[0].current_location,
    quarters: saved.campaigns[0].camp_progression.quarters.level,
    completed_encounters: saved.campaigns[0].completed_encounters,
  });
}

async function reconnect(cdp) {
  await waitFor(cdp, "document.querySelector('#shell') && !document.querySelector('#shell').classList.contains('hidden')", "reconnected dashboard", 15000);
  const boot = await bootstrapState(cdp);
  const campaign = boot.campaigns[0];
  const pass = campaign?.camp_progression?.quarters?.level === 1 && campaign.current_location === "emberhall_outpost";
  await screenshot(cdp, `${screenshotPrefix}-06-reconnect`);
  record("Restart or Reconnect", "Cookie session and saved campaign survive browser/server restart.", pass ? "Saved campaign resumed with Quarters level 1." : "Saved campaign did not resume correctly.", pass);
  run.stateChecks.push({
    step: "reconnect-state",
    location: campaign?.current_location,
    quarters: campaign?.camp_progression?.quarters?.level,
    completed_encounters: campaign?.completed_encounters || [],
  });
}

const { cdp, chrome } = await connectChrome();
try {
  await cdp.send("Page.navigate", { url: `${baseUrl}/?ui-verification=${Date.now()}` });
  await delay(1000);
} catch {
  await delay(1000);
}

try {
  if (phase === "reconnect") await reconnect(cdp);
  else await journey(cdp);
  run.finishedAt = new Date().toISOString();
  run.pass = run.defects.length === 0 && run.consoleErrors.length === 0;
} catch (error) {
  run.finishedAt = new Date().toISOString();
  run.pass = false;
  run.defects.push({ step: "script", observed: error.message });
} finally {
  await fs.mkdir("verification", { recursive: true });
  await fs.writeFile(reportPath, JSON.stringify(run, null, 2));
  try {
    await bounded(cdp.send("Browser.close").catch(() => undefined), 2000);
  } catch {
    // Fallback below.
  }
  if (chrome.exitCode === null) chrome.kill();
  cdp.close();
}

if (!run.pass) {
  console.error(JSON.stringify(run.defects, null, 2));
  process.exit(1);
}

console.log(`UI ${phase} verification passed. Report: ${reportPath}`);
