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
  assert.match(info,/cdn\.simpleicons\.org\/openai/);
  assert.match(info,/cdn\.simpleicons\.org\/amazonwebservices/);
  assert.match(info,/trademarks and logos remain the property of their respective owners/);
});
