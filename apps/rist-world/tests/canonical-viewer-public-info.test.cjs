const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const appRoot=path.resolve(__dirname,'..');
const repoRoot=path.resolve(appRoot,'..','..');
const readApp=relative=>fs.readFileSync(path.join(appRoot,relative),'utf8');
const readRepo=relative=>fs.readFileSync(path.join(repoRoot,relative),'utf8');

test('public About section links to Meet the team rather than putting creator biography in the hero',()=>{
  const home=readRepo('site/relic-home/index.html');
  assert.match(home,/<section class="overview" id="about">[\s\S]*?ReLiCGameMaster[\s\S]*?Meet the team/);
  assert.match(home,/class="meet-team-link" href="\/Game\/info\.html\?signature=jeyrusal">Meet the team/);
  assert.doesNotMatch(home,/class="hero-actions"[\s\S]{0,700}?About Ryan Cole/);
});

test('Game info credits directly used software contributors after legal links',()=>{
  const info=readApp('wwwroot/info.html');
  const legal=info.indexOf('<h2>Legal, Privacy & Safety</h2>');
  const contributors=info.indexOf('id="software-contributors"');
  assert.ok(legal>=0&&contributors>legal);
  for(const label of [
    'OpenAI / ChatGPT','GitHub','GitHub Actions','Amazon Web Services',
    'Microsoft .NET','Blazor WebAssembly','Python','JavaScript',
    'Node.js','npm','Discord','Git'
  ]) assert.ok(info.includes(label),'missing software contributor: '+label);
  assert.match(info,/assets\/software\/openai-chatgpt\.svg/);
  assert.match(info,/assets\/software\/aws\.svg/);
  assert.match(info,/trademarks and logos remain the property of their respective owners/);

  assert.match(info,/assets\/branding\/relic_gamemaster_wordmark\.jpg/);
  assert.match(info,/alt="ReLiCGameMaster logo"/);
  assert.match(info,/class="logo-orb"/);
  assert.match(info,/async function makeLogoTransparent\(\)/);
  assert.match(info,/const lowSaturation=\(max-min\)<24/);
  assert.match(info,/\(lowSaturation&&min>214\)\|\|\(lowSaturation&&max<54\)/);
  assert.doesNotMatch(info,/Press the ReLiCGameMaster logo to reveal Ryan's portrait/);
  assert.doesNotMatch(info,/class="die-body"/);
});



test('Game info has only a bottom Return Home control',()=>{
  const info=readApp('wwwroot/info.html');
  assert.doesNotMatch(info,/Return to RIST WORLD/);
  assert.match(info,/class="return-home-button" href="\/">Return Home<\/a>/);
  const button=info.indexOf('class="return-home-button"');
  const contributors=info.indexOf('id="software-contributors"');
  assert.ok(button>contributors);
});





test('Meet the team opens the live Jeyrusal Signature Card parallax stack',()=>{
  const info=readApp('wwwroot/info.html');
  assert.match(info,/id="signature-card" class="signature-card"/);
  assert.match(info,/01_jeyrusal_card_frame\.png/);
  assert.match(info,/02_jeyrusal_character_cutout\.png/);
  assert.match(info,/03_jeyrusal_holographic_overlay\.png/);
  assert.match(info,/class="signature-card-shine"/);
  assert.match(info,/class="signature-card-chrome"/);
  assert.match(info,/filter:brightness\(\.58\) saturate\(\.42\) contrast\(1\.22\)/);
  assert.match(info,/class="signature-card-foil"/);
  assert.match(info,/\.signature-card-foil\{[^}]*background-color:rgba\(102,111,120,\.10\)[^}]*opacity:\.70/);
  assert.match(info,/\.signature-card-shine\{[^}]*rgba\(0,0,0,\.72\)[^}]*mix-blend-mode:multiply[^}]*opacity:\.78/);
  assert.doesNotMatch(info,/\.signature-card-shine\{[^}]*rgba\(255,255,255,\.55\)/);
  assert.match(info,/\.signature-card-foil\{[^}]*translate3d\(calc\(var\(--px\) \* 6px\),calc\(var\(--py\) \* 6px\),62px\)/);
  assert.match(info,/\.signature-card-shine\{position:absolute;z-index:6/);
  assert.match(info,/\.signature-card::after\{content:"";position:absolute;z-index:7/);
  assert.match(info,/function setParallax\(x,y,tilt=7\)/);
  assert.match(info,/requestAnimationFrame\(idleTilt\)/);
  assert.match(info,/DeviceOrientationEvent\.requestPermission/);
  assert.match(info,/function orientationAxes\(event\)/);
  assert.match(info,/orientationBaseline=\{x:axes\.x,y:axes\.y\}/);
  assert.match(info,/const dx=axes\.x-orientationBaseline\.x/);
  assert.match(info,/const dy=axes\.y-orientationBaseline\.y/);
  assert.match(info,/dx\/18/);
  assert.match(info,/dy\/18/);
  assert.match(info,/function runOrientationParallax\(\)/);
  assert.match(info,/setParallax\(orientationCurrent\.x,orientationCurrent\.y,11\)/);
  assert.match(info,/addEventListener\('deviceorientation',orientationTilt/);
  assert.match(info,/event\.pointerType==='touch'\)return/);
  assert.match(info,/if\(event\.pointerType==='touch'\)\{[\s\S]*?void enableDeviceTilt\(\);[\s\S]*?return;/);
  assert.match(info,/signatureCard\.addEventListener\('pointermove',pointerTilt/);
  assert.doesNotMatch(info,/addEventListener\('touchend',enableDeviceTilt/);
  assert.doesNotMatch(info,/signature-caption/);
  assert.doesNotMatch(info,/Move or tilt/);
  assert.match(info,/aria-label="Signature Card"/);
  assert.doesNotMatch(info,/aria-label="Jeyrusal/);
  assert.doesNotMatch(info,/Show Jeyrusal Signature Card/);
  assert.doesNotMatch(info,/Press the ReLiCGameMaster logo/);
  assert.doesNotMatch(info,/Press it again to return to Jeyrusal/);
  assert.match(info,/creatorUrl='assets\/profile\/ryan-cole-portrait\.png'/);
  assert.doesNotMatch(info,/makeDarkOuterBackgroundTransparent/);
  for(const die of ['d4','d5-bonus','d5-penalty','d6','d8','d10','d10-inverse','d12','d20']){
    assert.ok(info.includes('data-die="'+die+'"'),'missing logo die '+die);
    assert.ok(info.includes("assets/dice/"+die+".png"),'missing app die asset '+die);
  }
  assert.match(info,/function animateLogoDieLikeGame\(element,spec,value\)/);
  assert.match(info,/const steps=13\+randomInt\(10\)/);
  assert.match(info,/frame=\(frame\+1\)%spec\.frames/);
  assert.match(info,/await wait\(52\+Math\.min\(n\*3,34\)\)/);
  assert.match(info,/const finalFrame=frameForLogoDie\(spec,value\)/);
  assert.match(info,/function rollLogoDice\(animate=true\)/);
  assert.match(info,/function motionShake\(event\)/);
  assert.match(info,/addEventListener\('devicemotion',motionShake/);
  assert.match(info,/DeviceMotionEvent\.requestPermission/);
  assert.match(info,/Promise\.allSettled\(\[orientationRequest,motionRequest\]\)/);
  assert.match(info,/dataset\.orientationAccess/);
  assert.match(info,/dataset\.motionAccess/);
  assert.match(info,/document\.addEventListener\('touchstart',unlockSensors/);
  assert.match(info,/document\.addEventListener\('click',unlockSensors/);
  assert.match(info,/stage\.addEventListener\('click',unlockSensors/);
  assert.match(info,/motionTiltBaseline/);
  assert.match(info,/now-lastOrientationAt>300/);
  assert.doesNotMatch(info,/if\(!orientationActive\|\|reducedMotion\)/);
  assert.match(info,/strength<13\|\|now-lastShakeAt<650/);
  assert.match(info,/rollLogoDice\(true\)/);
  assert.match(info,/toggle\.addEventListener\('click',\(\)=>\{[\s\S]*?rollLogoDice\(true\);[\s\S]*?showingCreator=!showingCreator;[\s\S]*?draw\(\);/);
  assert.match(info,/--logo-tx/);
  assert.match(info,/--logo-ry/);
  assert.match(info,/toggle\.style\.setProperty\('--logo-tx'/);
});
