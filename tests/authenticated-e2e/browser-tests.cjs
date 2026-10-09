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
  page.on('response', r=>{if(r.status()>=400)report.networkErrors.push({label,url:safeUrl(r.url()),status:r.status(),method:r.request().method(),resourceType:r.request().resourceType(),worldId:new URL(r.url()).searchParams.get('worldId')||undefined});});
  page.on('requestfailed', r=>{const item={label,url:safeUrl(r.url()),error:r.failure()?.errorText};(new URL(r.url()).hostname==='127.0.0.1'?report.networkErrors:report.blockedExternal).push(item);});
}
async function snapshot(page,name) {
  await page.screenshot({path:path.join(evidence,name+'.png'),timeout:15000});
  const geometry=await page.evaluate(()=>({width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth,controls:[...document.querySelectorAll('button,input,select')].filter(e=>e.getClientRects().length&&!e.disabled).map(e=>{const r=e.getBoundingClientRect(),h=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {name:e.getAttribute('aria-label')||e.textContent.trim().slice(0,100),x:r.x,y:r.y,width:r.width,height:r.height,covered:!!h&&!e.contains(h),interceptor:h?.className};})}));
  report.states.push({name,screenshot:name+'.png',geometry});
  for(const f of page.frames().slice(1)){if(new URL(f.url()).hostname==='127.0.0.1')report.states.at(-1).viewer=await f.locator('body').innerText().catch(()=>"");}
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
async function clickDisplay(page,side) {const control=page.locator('.control-display-'+side);if(await page.evaluate(()=>navigator.maxTouchPoints>0))await control.tap();else await control.click();await page.waitForTimeout(700);}
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
        await check('World chooser keeps keyboard focus inside the dialog',async()=>{
          for(let i=0;i<12;i++){await page.keyboard.press('Tab');assert(await page.evaluate(()=>!!document.activeElement.closest('[role=dialog]')));}
        });
        await page.getByLabel('WORLD NAME',{exact:true}).fill('AINPC E2E World');
        const claim=page.getByRole('button',{name:'CLAIM DEED · NO TOKEN',exact:true});
        await claim.tap();
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
            if(await page.locator('.universal-shell').count()&&await title.count()&&await title.isVisible()){
              await check('Cancel spatial title preserves selection and allows retry',async()=>{
                await title.fill('Cancelled fixture');await title.press('Escape');await page.waitForTimeout(300);
                assert((await page.locator('.viewer-status').innerText()).includes('selection is unchanged'));
                await clickDisplay(page,'left');await title.waitFor();
              });
              await title.fill('AINPC E2E Region');await snapshot(page,'se-title-editor');await title.press('Enter');await page.waitForTimeout(1200);}
            await snapshot(page,'se-region-depth-'+i);report.states.at(-1).text=(await page.locator('body').innerText()).slice(0,3500);
            if(!await page.locator('.viewer-status').count()){report.findings.push({name:'se-region-depth-'+i,issue:'Region save crashes the application: prompt is not a function. Local/image editing cannot safely continue.'});break;}
            report.states.at(-1).status=await page.locator('.viewer-status').textContent();
            if(report.states.at(-1).status.includes('AINPC E2E Region saved'))break;
          }
          await check('Region saved through visible map title editor',async()=>{
            assert((await page.locator('.viewer-status').innerText()).includes('AINPC E2E Region'));
          });
        }
        await check('Image upload, placement and editing through viewer UI',async()=>{
          const viewer=page.frameLocator('.universal-worldbuilder-frame');
          await viewer.getByRole('tab',{name:'Image',exact:true}).tap();
          await viewer.getByRole('button',{name:'MY IMAGES: Personal folder',exact:true}).tap();
          await snapshot(page,'se-my-images');
          // Reopen Image mode through its existing tab and normal upload control.
          await viewer.getByRole('tab',{name:'Labels',exact:true}).tap();
          await viewer.getByRole('tab',{name:'Image',exact:true}).tap();
          await viewer.getByRole('button',{name:'UPLOAD: image',exact:true}).tap();
          await viewer.getByRole('dialog',{name:'Add image',exact:true}).waitFor({timeout:3000});
          await snapshot(page,'se-image-upload');
          await viewer.locator('#imagePlacementRole').selectOption('layer');
          await viewer.locator('#imageFile').setInputFiles(path.join(root,'apps/rist-world/wwwroot/assets/cards/fronts/card_front_06_minimal.png'));
          await viewer.getByRole('button',{name:/SIZE −:/}).waitFor();
          await viewer.getByRole('button',{name:/SIZE −:/}).tap();
          await snapshot(page,'se-image-edited');
          await page.getByRole('button',{name:'Open Start menu',exact:true}).tap();
          await page.locator('[data-start-action=save]').tap();
          await page.waitForTimeout(1500);await snapshot(page,'se-image-save');
          await page.locator('[data-start-exit]').tap();
        });
        await page.setViewportSize({width:320,height:568});await snapshot(page,'se-320-builder');
        await check('320px toolbar can scroll to its final control',async()=>{
          const undo=page.getByRole('button',{name:'Undo',exact:true});await undo.scrollIntoViewIfNeeded();
          assert(await undo.evaluate(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44&&r.left>=0&&r.right<=innerWidth;}));
          await snapshot(page,'se-320-toolbar-scrolled');
        });
        await page.setViewportSize({width:375,height:667});
        await page.reload();await page.getByRole('button',{name:'PRESS START',exact:true}).waitFor({timeout:45000});await snapshot(page,'se-reloaded');
        await page.getByRole('button',{name:'PRESS START',exact:true}).click();await clickDisplay(page,'right');await clickDisplay(page,'right');
        report.states.push({name:'se-after-reload-owned-world',text:await page.locator('body').innerText()});
        const {context:desktopContext}=await authenticatedContext(browser,'gm',{viewport:{width:1280,height:800}});
        const desktop=await desktopContext.newPage();attach(desktop,'desktop');
        await launch(desktop,origin);await clickDisplay(desktop,'right');await clickDisplay(desktop,'right');
        await snapshot(desktop,'desktop-owned-world');await clickDisplay(desktop,'right');await clickDisplay(desktop,'left');
        await snapshot(desktop,'desktop-builder-entry');
        await check('Region title and image placement persist after reload',async()=>{
          const frame=desktop.frames().find(f=>f.url().includes('/prototype/index.html'));
          assert(frame,'World Builder iframe missing');
          await frame.waitForFunction(()=>window.ShaelvienPrototype?.getViewerState().userLayers.some(item=>item.kind==='image'&&item.committed),{},{timeout:15000});
          const layers=await frame.evaluate(()=>window.ShaelvienPrototype.getViewerState().userLayers);
          assert(layers.some(item=>item.kind==='label'&&item.text==='AINPC E2E Region'));
          report.states.push({name:'persisted-viewer-layers',layers});
        });
        await check('Saved region exists in the authoritative region catalog',async()=>{
          const result=await desktop.evaluate(async()=>{
            const worldId=document.querySelector('.universal-shell').dataset.worldId;
            const response=await fetch('/api/authority/world/regions?worldId='+encodeURIComponent(worldId),{headers:{Authorization:'Bearer '+sessionStorage.getItem('rist.session')}});
            const data=await response.json();return {status:response.status,found:Array.isArray(data)&&data.some(region=>region.name==='AINPC E2E Region')};
          });
          assert.equal(result.status,200);assert(result.found,'Named region missing from authoritative catalog');
        });
        await desktopContext.close();
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
    report.expectedNetworkErrors=report.networkErrors.filter(e=>e.error==='net::ERR_ABORTED'||(e.status===404&&(e.url.endsWith('/translation-config.json')||(e.url.endsWith('/objects/[redacted]')&&e.method==='GET'&&e.resourceType==='fetch'))));
    report.unexpectedNetworkErrors=report.networkErrors.filter(e=>!report.expectedNetworkErrors.includes(e));
    report.completedAt=new Date().toISOString();fs.writeFileSync(path.join(evidence,audit?'report.json':'authentication-report.json'),JSON.stringify(report,null,2));
    const failed=report.checks.filter(c=>!c.pass).length;
    console.log(JSON.stringify({checks:report.checks,findings:report.findings,networkErrors:report.networkErrors.length,exceptions:report.exceptions.length,evidence:'.e2e-runtime/evidence-public'}));
    if(failed||(audit&&(report.findings.length||report.unexpectedNetworkErrors.length||report.exceptions.length)))process.exitCode=1;
  }
})();
