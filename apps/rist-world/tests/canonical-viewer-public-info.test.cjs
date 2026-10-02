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
  assert.match(home,/class="meet-team-link" href="\/Game\/info\.html">Meet the team/);
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
  assert.match(info,/creatorUrl='assets\/profile\/ryan-cole-portrait\.png'/);
  assert.match(info,/assets\/branding\/relic_gamemaster_wordmark\.jpg/);
  assert.match(info,/alt="ReLiCGameMaster logo"/);
  assert.match(info,/class="logo-orb"/);
  assert.match(info,/async function makeLogoTransparent\(\)/);
  assert.match(info,/nearWhite\|\|nearBlack/);
  assert.match(info,/portrait-stage:not\(\.creator\) img\{[^}]*filter:brightness\(1\.2\) contrast\(1\.06\) saturate\(1\.05\) drop-shadow/);
  assert.match(info,/Press the ReLiCGameMaster logo to reveal Ryan's portrait/);
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


test('profile frame fits creator portrait and removes only the GameMaster outer background',()=>{
  const info=readApp('wwwroot/info.html');
  assert.match(info,/\.portrait-stage\{[^}]*aspect-ratio:4\/5/);
  assert.match(info,/\.portrait-stage\.creator img\{[^}]*width:calc\(100% - 22px\)[^}]*height:calc\(100% - 22px\)/);
  assert.match(info,/async function makeDarkOuterBackgroundTransparent\(url\)/);
  assert.match(info,/const visited=new Uint8Array\(width\*height\)/);
  assert.match(info,/return distance<78 && luminance<105/);
  assert.match(info,/gmUrl=await makeDarkOuterBackgroundTransparent\(rawGmUrl\)/);
});
