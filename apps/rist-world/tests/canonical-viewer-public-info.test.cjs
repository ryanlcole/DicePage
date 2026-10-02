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
  assert.match(info,/\.signature-card::before\{[^}]*rgba\(214,223,231,\.16\)[^}]*opacity:\.44/);
  assert.match(info,/\.signature-card::before\{[^}]*translate3d\(calc\(var\(--px\) \* 5px\),calc\(var\(--py\) \* 5px\),32px\)/);
  assert.match(info,/\.signature-card-shine\{position:absolute;z-index:5/);
  assert.match(info,/\.signature-card::after\{content:"";position:absolute;z-index:6/);
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
});
