'use strict';
// Runs the real built frontend. No private API or authorization responses mocked.
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const {authenticatedContext, requireTestEnvironment, runtime} = require('./auth-state.cjs');
requireTestEnvironment();
const root = path.resolve(__dirname, '../..');
const evidence = path.join(runtime, 'evidence-public');
fs.mkdirSync(evidence, {recursive:true});
const audit = !process.argv.includes('--auth-only');
const report = {startedAt:new Date().toISOString(),mode:audit?'audit':'authentication',checks:[],states:[],findings:[],consoleErrors:[],exceptions:[],networkErrors:[],blockedExternal:[]};
// Never record bearer headers, response bodies, signed URLs, query strings or traces.
function safeUrl(raw) { const u=new URL(raw); return u.origin+u.pathname.replace(/\/objects\/[^/]+/, '/objects/[redacted]'); }
function attach(page,label) {
  page.on('console', m=>{if(m.type()==='error') report.consoleErrors.push({label,text:m.text().replace(/https?:\/\/[^\s]+/g, s=>{try{return safeUrl(s)}catch{return '[url]'}})});});
  page.on('pageerror', e=>report.exceptions.push({label,message:e.message.replace(/https?:\/\/[^\s]+/g,'[url]')}));
  page.on('response', r=>{if(r.status()>=400)report.networkErrors.push({label,url:safeUrl(r.url()),status:r.status()});});
  page.on('requestfailed', r=>{const item={label,url:safeUrl(r.url()),error:r.failure()?.errorText};(new URL(r.url()).hostname==='127.0.0.1'?report.networkErrors:report.blockedExternal).push(item);});
}
async function snapshot(page,name) {
  await page.screenshot({path:path.join(evidence,name+'.png'),timeout:15000});
  const geometry=await page.evaluate(()=>({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,controls:[...document.querySelectorAll('button,input,select')].filter(e=>e.getClientRects().length&&!e.disabled).map(e=>{const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {name:e.getAttribute('aria-label')||e.textContent.trim().slice(0,100),x:r.x,y:r.y,width:r.width,height:r.height,covered:!!h&&!e.contains(h),interceptor:h?.className};})}));
  report.states.push({name,screenshot:name+'.png',geometry});
  if(geometry.scrollWidth>geometry.width+1)report.findings.push({name,issue:'Horizontal document overflow'});
}
async function check(name,fn) { try{await fn();report.checks.push({name,pass:true});}catch(e){report.checks.push({name,pass:false,error:e.message.split('\n')[0]});} }
async function launch(page,origin) {
  await page.goto(origin+'/Game/index.html');
  await page.getByRole('button',{name:'ESSENTIAL ONLY',exact:true}).waitFor({timeout:45000});
  await page.getByRole('button',{name:'ESSENTIAL ONLY',exact:true}).click();
  await page.getByRole('button',{name:'PRESS START',exact:true}).click();
  await page.locator('.control-display-right').waitFor();
}
async function clickDisplay(page,side) {await page.locator('.control-display-'+side).tap();await page.waitForTimeout(700);}
(async()=>{
  const server=spawn(process.env.PYTHON||'python3',[path.join(__dirname,'local_harness.py')],{cwd:root,env:process.env,stdio:['ignore','pipe','pipe']});
  // Intentionally do not print server logs that might include private transport details.
  server.stderr.on('data',()=>{});
  let browser;
  try {
    await new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('Local harness startup timed out')),20000);server.stdout.once('data',()=>{clearTimeout(timer);resolve();});server.once('exit',()=>{clearTimeout(timer);reject(Error('Local harness refused or failed'));});});
    browser=await chromium.launch({headless:true,...(process.env.SHAELVIEN_E2E_CHROMIUM?{executablePath:process.env.SHAELVIEN_E2E_CHROMIUM}:{})});
    const origin='http://127.0.0.1:8765';
    const guest=await browser.newContext();guest.setDefaultTimeout(10000);await guest.route('**/*',r=>new URL(r.request().url()).origin===origin?r.continue():r.abort());
    for(const route of ['/Game/index.html','/Game/'])await check('Guest direct '+route,async()=>{const p=await guest.newPage();await p.goto(origin+route);await p.waitForURL('**/Play/index.html',{timeout:45000});assert.equal(await p.locator('.rist-auth-start,.universal-shell').count(),0);await p.close();});
    await check('Guest Launcher release controls stay locked',async()=>{const p=await guest.newPage();await p.goto(origin+'/Launcher/index.html');await p.locator('#systemBadge').filter({hasText:/LOGIN REQUIRED|LOCKED/}).waitFor();assert(await p.locator('#promoteButton').isDisabled());assert(await p.locator('#revokeButton').isDisabled());await p.close();});
    await check('Private HTTP APIs reject unauthenticated requests',async()=>{for(const route of ['/api/auth/me','/api/auth/storage/list','/api/authority/authority/me','/api/authority/world/source?worldId=e2e-shared'])assert.equal((await guest.request.get(origin+route)).status(),401);});
    await guest.close();
    for(const persona of ['user','gm']) {
      const {context}=await authenticatedContext(browser,persona,{viewport:{width:375,height:667},isMobile:true,hasTouch:true});
      const page=await context.newPage();attach(page,persona+'-auth');
      await check(persona+' private start and reload',async()=>{await page.goto(origin+'/Game/index.html');await page.getByRole('button',{name:'PRESS START',exact:true}).waitFor({timeout:45000});assert.equal(page.url(),origin+'/Game/index.html');await page.reload();await page.getByRole('button',{name:'PRESS START',exact:true}).waitFor({timeout:45000});});
      await check(persona+' authenticated nested Launcher direct navigation',async()=>{const p=await context.newPage();await p.goto(origin+'/Game/Launcher/index.html');await p.getByText('AUTHENTICATED',{exact:true}).waitFor({timeout:10000});assert(await p.locator('#promoteButton').isDisabled());assert(await p.locator('#revokeButton').isDisabled());await p.close();});
      if(audit&&persona==='user') {
        await launch(page,origin);await clickDisplay(page,'right');await snapshot(page,'se-normal-user-roles');
        await clickDisplay(page,'left');await snapshot(page,'se-roleplayer');report.states.at(-1).text=(await page.locator('body').innerText()).slice(0,4000);
      }
      if(audit&&persona==='gm') {
        await snapshot(page,'se-start');
        await launch(page,origin);await snapshot(page,'se-environment');
        await clickDisplay(page,'right');await snapshot(page,'se-roles');
        await clickDisplay(page,'right');await snapshot(page,'se-gamemaster');
        await clickDisplay(page,'right');await page.getByRole('dialog',{name:'Choose a world'}).waitFor();
        await snapshot(page,'se-world-dialog');
        await page.getByLabel('WORLD NAME',{exact:true}).fill('AINPC E2E World');
        const claim=page.getByRole('button',{name:'CLAIM DEED · NO TOKEN',exact:true});
        try{await claim.click({timeout:2000});}catch {report.findings.push({name:'se-world-dialog',issue:'World creation tap intercepted by universal viewer. Keyboard-only diagnostic continuation follows.'});await claim.press('Enter');}
        await page.getByRole('dialog',{name:'Choose a world'}).waitFor({state:'hidden',timeout:15000});
        await snapshot(page,'se-world-created');
        await clickDisplay(page,'right');await snapshot(page,'se-world-open');
        // Continue through actual display controls. Record every state, not inferred success.
        for(let i=0;i<7;i++){await clickDisplay(page,'left');await snapshot(page,'se-builder-'+i);report.states.at(-1).text=(await page.locator('body').innerText()).slice(0,4000);report.states.at(-1).status=await page.locator('.viewer-status').textContent();}
        if(await page.locator('.universal-shell').getAttribute('data-semantic-context')==='shaep.pathselect') {
          report.findings.push({name:'se-builder-6',issue:'World Builder display remains at path selection after seven activation attempts; region/local/image flows not reached.'});
          await page.keyboard.press('q');await page.waitForTimeout(700);await snapshot(page,'se-builder-keyboard');report.states.at(-1).status=await page.locator('.viewer-status').textContent();
        }
        if(await page.locator('.universal-shell').getAttribute('data-semantic-context')==='shaep.worldhome') {
          await page.locator('.control-display-left').press('q');await page.waitForTimeout(700);
          await snapshot(page,'se-region-select');report.states.at(-1).status=await page.locator('.viewer-status').textContent();
          const stage=page.frameLocator('.universal-worldbuilder-frame').locator('#stage');
          await stage.tap({position:{x:160,y:180}});
          page.on('dialog',d=>d.type()==='prompt'?d.accept('AINPC E2E Region'):d.dismiss());
          await page.locator('.control-display-left').press('q');await page.waitForTimeout(1200);
          await snapshot(page,'se-region-save-attempt');report.states.at(-1).status=await page.locator('.viewer-status').textContent();
          for(let i=0;i<8;i++){
            await clickDisplay(page,'left');
            const title=page.frameLocator('.universal-worldbuilder-frame').getByRole('textbox',{name:/Name this (area|scene).*Enter to save/});
            if(await page.locator('.universal-shell').count()&&await title.count()&&await title.isVisible()){await title.fill('AINPC E2E Region');await title.press('Enter');await page.waitForTimeout(700);}
            await snapshot(page,'se-region-depth-'+i);report.states.at(-1).text=(await page.locator('body').innerText()).slice(0,3500);
            if(!await page.locator('.viewer-status').count()){report.findings.push({name:'se-region-depth-'+i,issue:'Region save crashes the application: prompt is not a function. Local/image editing cannot safely continue.'});break;}
            report.states.at(-1).status=await page.locator('.viewer-status').textContent();
          }
          // Native image upload controls, if exposed by this real viewer.
          if(await page.locator('.universal-shell').count())await check('Image tool reachable through normal viewer keyboard',async()=>{
            await stage.press('u');
            const panel=page.frameLocator('.universal-worldbuilder-frame').getByRole('dialog',{name:'Add image',exact:true});
            await panel.waitFor({timeout:3000});await snapshot(page,'se-image-tool');
            await panel.getByRole('button',{name:'Close image upload',exact:true}).tap();
          });
        }
        await page.reload();await page.getByRole('button',{name:'PRESS START',exact:true}).waitFor({timeout:45000});await snapshot(page,'se-reloaded');
        await page.getByRole('button',{name:'PRESS START',exact:true}).click();await clickDisplay(page,'right');await clickDisplay(page,'right');
        report.states.push({name:'se-after-reload-owned-world',text:await page.locator('body').innerText()});
        // Desktop uses same persisted test identity and data, with normal mouse interactions.
        await page.setViewportSize({width:1280,height:800});await snapshot(page,'desktop-owned-world');
        await clickDisplay(page,'left');await snapshot(page,'desktop-builder-entry');report.states.at(-1).status=await page.locator('.viewer-status').textContent();
        const launcher=await context.newPage();attach(launcher,'standalone-launcher');await launcher.goto(origin+'/Launcher/index.html');await launcher.locator('#systemBadge').filter({hasText:/AUTHENTICATED|LOCKED/}).waitFor();await snapshot(launcher,'standalone-launcher');
        if((await launcher.locator('#systemBadge').innerText())!=='AUTHENTICATED')report.findings.push({name:'standalone-launcher',issue:'Standalone Launcher fails to validate an otherwise valid session; ../rist.js resolves to missing /rist.js.'});
        await launcher.close();
      }
      await context.close();
    }
  } catch(e) {report.checks.push({name:'Browser journey completion',pass:false,error:e.message.split('\n')[0]});}
  finally {
    if(browser)await browser.close();
    if(server.exitCode===null){server.kill('SIGINT');await new Promise(r=>server.once('exit',r));}
    for(const name of ['user.json','gm.json'])fs.rmSync(path.join(runtime,'.auth',name),{force:true});
    report.completedAt=new Date().toISOString();fs.writeFileSync(path.join(evidence,audit?'report.json':'authentication-report.json'),JSON.stringify(report,null,2));
    const failed=report.checks.filter(c=>!c.pass).length;
    console.log(JSON.stringify({checks:report.checks,findings:report.findings,networkErrors:report.networkErrors.length,exceptions:report.exceptions.length,evidence:'.e2e-runtime/evidence-public'}));
    if(failed||(audit&&(report.findings.length||report.networkErrors.length||report.exceptions.length)))process.exitCode=1;
  }
})();
