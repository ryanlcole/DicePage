const state = {
  csrfToken: "",
  boot: null,
  tab: "game",
  role: "vanguard",
  activeCharacterId: localStorage.getItem("shaelvien_lite_character") || "",
  activeCampaignId: localStorage.getItem("shaelvien_lite_campaign") || ""
};

const $ = (id) => document.getElementById(id);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const headers = {"Content-Type": "application/json"};
  if (state.csrfToken && (options.method || "GET") !== "GET") headers["X-CSRF-Token"] = state.csrfToken;
  let response;
  try {
    response = await fetch(path, {
    method: options.method || "GET",
    headers,
      credentials: "same-origin",
      body: options.body ? JSON.stringify(options.body) : undefined
    });
  } catch (error) {
    throw new Error("Shaelvien Lite is waking from rest or temporarily unavailable. Try again in a moment.");
  }
  let data = {};
  try {
    data = await response.json();
  } catch (error) {
    throw new Error("Server returned an unreadable response.");
  }
  if (!response.ok) throw new Error(data.error || "Request failed");
  return data;
}

function toast(message) {
  const node = $("toast");
  node.textContent = message;
  node.classList.remove("hidden");
  window.setTimeout(() => node.classList.add("hidden"), 3600);
}

async function bootstrap() {
  state.boot = await api("/api/bootstrap");
  state.csrfToken = state.boot.csrf_token || state.csrfToken || "";
  if (state.boot.account) {
    $("landing").classList.add("hidden");
    $("entryPanel").classList.add("hidden");
    $("shell").classList.remove("hidden");
    $("accountBadge").textContent = `${state.boot.account.handle} - ${state.boot.account.role}`;
    $("adminTab").classList.toggle("hidden", state.boot.account.role !== "owner");
    chooseActiveRecords();
    renderAll();
  } else {
    $("landing").classList.remove("hidden");
    $("entryPanel").classList.remove("hidden");
    $("shell").classList.add("hidden");
    renderRoleChoices();
  }
}

function chooseActiveRecords() {
  const characters = state.boot.characters || [];
  if (!characters.some((character) => character.character_id === state.activeCharacterId)) {
    state.activeCharacterId = characters[0]?.character_id || "";
  }
  const campaigns = state.boot.campaigns || [];
  if (!campaigns.some((campaign) => campaign.campaign_id === state.activeCampaignId)) {
    state.activeCampaignId = campaigns[0]?.campaign_id || "";
  }
  if (state.activeCharacterId) localStorage.setItem("shaelvien_lite_character", state.activeCharacterId);
  if (state.activeCampaignId) localStorage.setItem("shaelvien_lite_campaign", state.activeCampaignId);
}

function activeCharacter() {
  return (state.boot.characters || []).find((character) => character.character_id === state.activeCharacterId);
}

function activeCampaign() {
  return (state.boot.campaigns || []).find((campaign) => campaign.campaign_id === state.activeCampaignId);
}

function locationRecord(campaign) {
  if (!campaign || campaign.current_location === "emberhall_outpost") return state.boot.region.settlement;
  return state.boot.region.locations[campaign.current_location];
}

function renderAll() {
  renderRoleChoices();
  renderTabs();
  renderCharacterCreate();
  renderGame();
  renderCharacters();
  renderCamp();
  renderInventory();
  renderQuests();
  renderParty();
  renderSettings();
  renderAdmin();
}

function renderTabs() {
  document.querySelectorAll(".tabs button").forEach((button) => {
    button.classList.toggle("active", button.dataset.tab === state.tab);
  });
  document.querySelectorAll(".view").forEach((view) => view.classList.add("hidden"));
  $(`${state.tab}View`)?.classList.remove("hidden");
}

function renderRoleChoices() {
  if (!$("roleChoices") || !state.boot?.roles) return;
  $("roleChoices").innerHTML = Object.entries(state.boot.roles).map(([roleId, role]) => `
    <button class="role-card ${state.role === roleId ? "selected" : ""}" type="button" data-role="${escapeHtml(roleId)}">
      <img src="/${escapeHtml(role.portrait)}" alt="${escapeHtml(role.name)} placeholder portrait">
      <h3>${escapeHtml(role.name)}</h3>
      <p>${escapeHtml(role.origin)}</p>
      <p class="fine">${escapeHtml(role.biography)}</p>
    </button>
  `).join("");
  document.querySelectorAll("[data-role]").forEach((button) => {
    button.addEventListener("click", () => {
      state.role = button.dataset.role;
      $("roleInput").value = state.role;
      renderRoleChoices();
    });
  });
}

function renderCharacterCreate() {
  $("characterCreate").classList.toggle("hidden", (state.boot.characters || []).length > 0);
}

function renderGame() {
  const character = activeCharacter();
  const campaign = activeCampaign();
  const view = $("gameView");
  if (!character) {
    view.innerHTML = `<section class="band"><h2>Create a character to begin</h2></section>`;
    return;
  }
  if (!campaign) {
    view.innerHTML = `
      <section class="band">
        <div class="section-head">
          <div><p class="eyebrow">Tutorial Campaign</p><h2>Arrive at Emberhall Outpost</h2></div>
          <button class="primary" id="startTutorialBtn" type="button">Begin Tutorial</button>
        </div>
      </section>`;
    $("startTutorialBtn").addEventListener("click", startTutorial);
    return;
  }
  const loc = locationRecord(campaign);
  const quest = campaign.scene_state?.active_quest_id ? campaign.quests[campaign.scene_state.active_quest_id] : null;
  const questName = quest ? state.boot.region && quest.quest_id ? questTitle(quest.quest_id) : "Quest" : "No active quest";
  const logs = campaign.session_log_ids || [];
  view.innerHTML = `
    <div class="game-layout">
      <div class="game-top">
        <div><strong>${escapeHtml(loc.name)}</strong><div class="fine">${escapeHtml(questName)}</div></div>
        <div class="resource-row">
          <span class="status-pill">${character.currency} coin</span>
          <span class="status-pill">Timber ${character.resources.timber || 0}</span>
          <span class="status-pill">Ore ${character.resources.ore || 0}</span>
          <span class="status-pill">Ember ${character.resources.ember || 0}</span>
        </div>
      </div>
      <aside class="hero-rail">${heroCard(character, true)}</aside>
      <section class="scene-panel">
        <img src="/${escapeHtml(loc.art)}" alt="${escapeHtml(loc.name)} placeholder scene">
        <div class="scene-copy">
          <p class="eyebrow">${escapeHtml(loc.kind || "scene")}</p>
          <h2>${escapeHtml(loc.name)}</h2>
          <p>${escapeHtml(loc.description || loc.summary || "")}</p>
        </div>
      </section>
      <aside class="npc-panel">
        ${npcBlock(campaign)}
        ${questBlock(campaign)}
      </aside>
      <section class="log-panel" id="logPanel">
        <h3>Session History</h3>
        <div id="logEntries">${logs.length ? "Loading log..." : "No entries yet."}</div>
      </section>
      <section class="action-panel">
        <form id="actionForm" class="action-form">
          <label class="sr-only" for="actionInput">Player action</label>
          <input id="actionInput" placeholder="Type an action" autocomplete="off" required>
          <button class="primary" type="submit">Send</button>
        </form>
        <div class="common-actions">
          ${commonActions(campaign).map((label) => `<button type="button" data-action="${escapeHtml(label)}">${escapeHtml(label)}</button>`).join("")}
        </div>
      </section>
    </div>
  `;
  $("actionForm").addEventListener("submit", submitAction);
  document.querySelectorAll("[data-action]").forEach((button) => {
    button.addEventListener("click", () => sendAction(button.dataset.action));
  });
  loadLogs(campaign.campaign_id);
}

function heroCard(character, compact = false) {
  const health = Math.round((character.vitals.health / character.vitals.maximum_health) * 100);
  const weapon = character.equipment.weapon ? itemName(character.equipment.weapon) : "Unarmed";
  return `
    <article class="hero-card ${compact ? "compact" : ""}">
      <img src="/${escapeHtml(character.portrait)}" alt="${escapeHtml(character.name)} placeholder portrait">
      <h3>${escapeHtml(character.name)}</h3>
      <div class="meta-row"><span>Level ${character.level}</span><span>${escapeHtml(character.role)}</span></div>
      <span class="status-pill">${escapeHtml(character.rarity_or_progression_tier)}</span>
      <div class="health-bar" style="--fill:${health}%"><span></span></div>
      <p class="fine">${character.vitals.health}/${character.vitals.maximum_health} health</p>
      <p class="fine">${escapeHtml(weapon)} - ${escapeHtml(character.current_assignment)}</p>
      <button class="ghost" data-tab-target="characters" type="button">Character Sheet</button>
    </article>`;
}

function npcBlock(campaign) {
  const npc = campaign.npcs[campaign.scene_state.active_npc_id] || Object.values(campaign.npcs)[0];
  return `
    <div>
      <p class="eyebrow">NPC</p>
      <h3>${escapeHtml(npc.name)}</h3>
      <p>${escapeHtml(npc.role)}</p>
      <p class="fine">${escapeHtml(npc.personality_summary)}</p>
      <p class="fine">Disposition: ${escapeHtml(npc.disposition)}</p>
    </div>`;
}

function questBlock(campaign) {
  const active = campaign.scene_state.active_quest_id;
  const quest = campaign.quests[active];
  if (!quest) return `<div><p class="eyebrow">Quest</p><p>No active quest.</p></div>`;
  return `
    <div>
      <p class="eyebrow">Quest</p>
      <h3>${escapeHtml(questTitle(active))}</h3>
      <p class="fine">Status: ${escapeHtml(quest.status)}</p>
      <p class="fine">Steps: ${(quest.completed_steps || []).length}</p>
    </div>`;
}

function commonActions(campaign) {
  if (campaign.combat) return ["Attack", "Defend", "Use a healing draught", "Retreat"];
  if (campaign.current_location === "emberhall_outpost") {
    return ["Speak with Ilyra at the guild hall", "Accept quest", "Travel to the Forest Road", "Upgrade Quarters"];
  }
  return ["Investigate the area", "Attack the threat", "Return to Emberhall Outpost"];
}

async function loadLogs(campaignId) {
  try {
  const data = await api(`/api/session-log?campaign_id=${encodeURIComponent(campaignId)}`);
    const panel = $("logEntries");
    panel.innerHTML = data.logs.map((entry) => `
      <div class="log-entry">
        <strong>${escapeHtml(entry.type)}</strong>
        <span>${escapeHtml(entry.text)}</span>
        ${entry.roll_result ? `<span class="roll-line">Roll ${entry.roll_result.roll} + ${modifierTotal(entry.roll_result.modifiers)} = ${entry.roll_result.total} vs ${entry.roll_result.difficulty} - ${entry.roll_result.result_band}</span>` : ""}
      </div>
    `).join("");
    $("logPanel").scrollTop = $("logPanel").scrollHeight;
  } catch (error) {
    $("logEntries").textContent = error.message;
  }
}

function modifierTotal(modifiers) {
  return Object.values(modifiers || {}).reduce((total, value) => total + Number(value || 0), 0);
}

function renderCharacters() {
  const characters = state.boot.characters || [];
  $("charactersView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Heroes</p><h2>Characters</h2></div></div>
    <div class="sheet">
      <div class="card-grid">${characters.map((character) => heroCard(character)).join("")}</div>
      <div class="sheet-panel">${characters[0] ? characterSheet(activeCharacter() || characters[0]) : "No character yet."}</div>
    </div>`;
}

function characterSheet(character) {
  return `
    <h2>${escapeHtml(character.name)}</h2>
    <p>${escapeHtml(character.biography)}</p>
    <div class="sheet-list">
      <div class="sheet-row"><strong>Vitals</strong><br>${character.vitals.health}/${character.vitals.maximum_health} health, ${character.vitals.stamina}/${character.vitals.maximum_stamina} stamina</div>
      <div class="sheet-row"><strong>Attributes</strong><br>${Object.entries(character.attributes).map(([key, value]) => `${escapeHtml(key)} ${value}`).join(", ")}</div>
      <div class="sheet-row"><strong>Skills</strong><br>${Object.entries(character.skills).filter(([, value]) => value > 0).map(([key, value]) => `${escapeHtml(key)} +${value}`).join(", ") || "No trained skills"}</div>
      <div class="sheet-row"><strong>Equipment</strong><br>${Object.entries(character.equipment).map(([slot, value]) => `${escapeHtml(slot)}: ${Array.isArray(value) ? value.map(itemName).join(", ") : itemName(value)}`).join("<br>")}</div>
    </div>`;
}

function renderCamp() {
  const character = activeCharacter();
  const campaign = activeCampaign();
  if (!campaign || !character) {
    $("campView").innerHTML = `<section class="band"><h2>Begin a campaign to access camp.</h2></section>`;
    return;
  }
  $("campView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Headquarters</p><h2>Personal Camp</h2></div></div>
    <div class="resource-row">
      <span class="status-pill">${character.currency} coin</span>
      <span class="status-pill">Timber ${character.resources.timber || 0}</span>
      <span class="status-pill">Ore ${character.resources.ore || 0}</span>
      <span class="status-pill">Ember ${character.resources.ember || 0}</span>
    </div>
    <div class="camp-grid">${Object.values(campaign.camp_progression).map((structure) => `
      <article class="camp-card">
        <h3>${escapeHtml(structure.name)}</h3>
        <p>Level ${structure.level}/${structure.max_level}</p>
        <p class="fine">${escapeHtml(structure.benefit)}</p>
        <p class="fine">Cost: ${structure.upgrade_requirements.currency || 0} coin ${Object.entries(structure.upgrade_requirements.resources || {}).map(([key, value]) => `${value} ${key}`).join(" ")}</p>
        <button type="button" data-action="Upgrade ${escapeHtml(structure.name)}">Upgrade</button>
      </article>
    `).join("")}</div>`;
  document.querySelectorAll("#campView [data-action]").forEach((button) => {
    button.addEventListener("click", () => sendAction(button.dataset.action));
  });
}

function renderInventory() {
  const character = activeCharacter();
  if (!character) {
    $("inventoryView").innerHTML = `<section class="band"><h2>No inventory yet.</h2></section>`;
    return;
  }
  $("inventoryView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Inventory</p><h2>Items and Equipment</h2></div></div>
    <div class="inventory-grid">${Object.values(character.inventory).map((item) => `
      <article class="inventory-item">
        <h3>${escapeHtml(item.name)}</h3>
        <p>${escapeHtml(item.category)} x${item.quantity}</p>
        <p class="fine">${escapeHtml(item.description)}</p>
        <p class="fine">Mass ${item.mass} - Value ${item.value} - Quality ${escapeHtml(item.quality)}</p>
      </article>
    `).join("")}</div>`;
}

function renderQuests() {
  const campaign = activeCampaign();
  if (!campaign) {
    $("questsView").innerHTML = `<section class="band"><h2>No campaign quests yet.</h2></section>`;
    return;
  }
  $("questsView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Quest Hall</p><h2>Quests</h2></div></div>
    <div class="quest-list">${Object.values(campaign.quests).map((quest) => `
      <article class="quest-row">
        <h3>${escapeHtml(questTitle(quest.quest_id))}</h3>
        <span class="status-pill">${escapeHtml(quest.status)}</span>
        <div class="progress-bar" style="--fill:${questProgress(quest)}%"><span></span></div>
        <p class="fine">${escapeHtml((quest.completed_steps || []).join(", ") || "No completed steps")}</p>
      </article>
    `).join("")}</div>`;
}

function renderParty() {
  const campaign = activeCampaign();
  $("partyView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Party</p><h2>Cooperative Prep</h2></div></div>
    <div class="admin-block">
      <p>Party ID: ${escapeHtml(campaign?.party_id || "No active party")}</p>
      <p class="fine">Small-party models are persisted now. Invite UI and real-time sync are not active in this local slice.</p>
    </div>`;
}

function renderSettings() {
  $("settingsView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Settings</p><h2>Local Session</h2></div></div>
    <div class="admin-block">
      <p class="fine">Authentication status: development local password account. This is not production SSO.</p>
      <button class="danger" id="logoutBtn" type="button">Log out</button>
    </div>`;
  $("logoutBtn").addEventListener("click", async () => {
    try {
      await api("/api/account/logout", {method: "POST", body: {}});
    } catch (error) {
      toast(error.message);
    }
    state.csrfToken = "";
    localStorage.removeItem("shaelvien_lite_character");
    localStorage.removeItem("shaelvien_lite_campaign");
    location.reload();
  });
}

async function renderAdmin() {
  if (state.boot.account?.role !== "owner") return;
  $("adminView").innerHTML = `
    <div class="section-head"><div><p class="eyebrow">Owner Console</p><h2>Development Controls</h2></div></div>
    <div id="adminContent" class="admin-block">Loading...</div>`;
  try {
    const snapshot = await api("/api/admin");
    $("adminContent").innerHTML = `
      <p>Accounts: ${snapshot.accounts.length}</p>
      <p>Characters: ${snapshot.characters.length}</p>
      <p>Campaigns: ${snapshot.campaigns.length}</p>
      <p>Deployment: ${escapeHtml(snapshot.runtime?.deployment_version || "local")} (${escapeHtml(snapshot.runtime?.mode || "development")}, ${escapeHtml(snapshot.runtime?.storage_backend || "json")})</p>
      <p>Storage: last connection ${escapeHtml(snapshot.runtime?.last_storage_connection_at || "local file")}; failures ${Number(snapshot.runtime?.storage_failure_count || 0)}</p>
      <div class="toolbar">
        <button type="button" id="toggleAiBtn">AI ${snapshot.settings.ai_enabled ? "On" : "Off"}</button>
        <button type="button" id="toggleMaintBtn">Maintenance ${snapshot.settings.maintenance_mode ? "On" : "Off"}</button>
      </div>
      <h3>Recent Validation Failures</h3>
      <pre>${escapeHtml(JSON.stringify(snapshot.validation_failures.slice(-5), null, 2))}</pre>
      <h3>Recent AI Proposals</h3>
      <pre>${escapeHtml(JSON.stringify(snapshot.ai_proposals.slice(-3), null, 2))}</pre>`;
    $("toggleAiBtn").addEventListener("click", () => adminSettings({ai_enabled: !snapshot.settings.ai_enabled}));
    $("toggleMaintBtn").addEventListener("click", () => adminSettings({maintenance_mode: !snapshot.settings.maintenance_mode}));
  } catch (error) {
    $("adminContent").textContent = error.message;
  }
}

function questTitle(questId) {
  const names = {
    q_forest_road: "Lanterns on the Forest Road",
    q_mine_echoes: "Echoes Below the Mine",
    q_shrine_marks: "Marks at the Ruined Shrine",
    q_bandit_pressure: "Pressure at the Ridge Camp",
    q_outpost_rebuild: "A Camp Worth Returning To"
  };
  return names[questId] || questId;
}

function questProgress(quest) {
  const expected = {
    q_forest_road: 5,
    q_mine_echoes: 3,
    q_shrine_marks: 3,
    q_bandit_pressure: 2,
    q_outpost_rebuild: 2
  }[quest.quest_id] || 1;
  return Math.min(100, Math.round(((quest.completed_steps || []).length / expected) * 100));
}

function itemName(itemId) {
  if (!itemId) return "None";
  return state.boot.items?.[itemId]?.name || itemId;
}

async function startTutorial() {
  const character = activeCharacter();
  if (!character) return;
  try {
    const data = await api("/api/campaigns/tutorial/start", {
      method: "POST",
      body: {character_id: character.character_id}
    });
    state.activeCampaignId = data.campaign.campaign_id;
    localStorage.setItem("shaelvien_lite_campaign", state.activeCampaignId);
    await bootstrap();
  } catch (error) {
    toast(error.message);
  }
}

async function submitAction(event) {
  event.preventDefault();
  const input = $("actionInput");
  const text = input.value.trim();
  input.value = "";
  await sendAction(text);
}

async function sendAction(action) {
  const character = activeCharacter();
  const campaign = activeCampaign();
  if (!character || !campaign || !action) return;
  try {
    const data = await api("/api/game/action", {
      method: "POST",
      body: {
        campaign_id: campaign.campaign_id,
        character_id: character.character_id,
        action,
        idempotency_key: newActionKey()
      }
    });
    state.activeCharacterId = data.character.character_id;
    state.activeCampaignId = data.campaign.campaign_id;
    await bootstrap();
    toast(data.ai_response.narration);
  } catch (error) {
    toast(error.message);
  }
}

async function adminSettings(settings) {
  try {
    await api("/api/admin/settings", {method: "POST", body: settings});
    await bootstrap();
  } catch (error) {
    toast(error.message);
  }
}

$("playFreeBtn").addEventListener("click", () => $("handleInput").focus());
$("accountForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await api("/api/account/enter", {
      method: "POST",
      body: {
        handle: $("handleInput").value,
        password: $("passwordInput").value,
        invite_code: $("inviteInput").value
      }
    });
    state.csrfToken = data.csrf_token || "";
    await bootstrap();
  } catch (error) {
    toast(error.message);
  }
});

$("characterForm").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const data = await api("/api/characters", {
      method: "POST",
      body: {
        name: $("characterName").value,
        ancestry: $("characterOrigin").value,
        role_id: state.role
      }
    });
    state.activeCharacterId = data.character.character_id;
    localStorage.setItem("shaelvien_lite_character", state.activeCharacterId);
    await bootstrap();
  } catch (error) {
    toast(error.message);
  }
});

document.querySelectorAll(".tabs button").forEach((button) => {
  button.addEventListener("click", () => {
    state.tab = button.dataset.tab;
    window.scrollTo({top: 0, left: 0});
    renderAll();
  });
});

document.addEventListener("click", (event) => {
  const target = event.target.closest("[data-tab-target]");
  if (target) {
    state.tab = target.dataset.tabTarget;
    window.scrollTo({top: 0, left: 0});
    renderAll();
  }
});

bootstrap().catch((error) => toast(error.message));

function newActionKey() {
  if (crypto?.randomUUID) return crypto.randomUUID();
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}
