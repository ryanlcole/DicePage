const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('Browser Back authority is not a visible or grid-flow control',()=>{
  const razor=read('Components/ExperimentsWorkspace.razor');
  const css=read('wwwroot/css/experiments-universal-suite.css');

  assert.match(
    razor,
    /class="experiments-browser-back"[\s\S]{0,220}?data-browser-back="experiments"[\s\S]{0,220}?hidden/
  );
  assert.match(
    css,
    /\.experiments-browser-back\s*\{[\s\S]*?display:none!important;[\s\S]*?\}/
  );
});

test('Browser Back authority remains connected to the experiments shell',()=>{
  const bridge=read('wwwroot/browser-back-authority.js');
  assert.match(bridge,/\.experiments-shell \[data-browser-back="experiments"\]/);
  assert.match(bridge,/target\.click\(\)/);
});


test('landscape mode prioritizes viewer visibility with a compact control deck',()=>{
  const css=read('wwwroot/css/experiments-universal-suite.css');
  assert.match(css,/Compact landscape visibility authority/);
  assert.match(css,/@media \(orientation:landscape\) and \(max-height:620px\)/);
  assert.match(css,/grid-template-rows:minmax\(0,1fr\) clamp\(92px,26dvh,112px\)!important/);
  assert.match(css,/grid-template-columns:minmax\(0,1fr\) clamp\(76px,14vw,96px\) minmax\(0,1fr\)!important/);
  assert.match(css,/\.single-analog-deck \.analog-pad\{[\s\S]*?width:min\(100%,76px\)!important/);
  assert.match(css,/\.single-analog-deck button\.control-display-button>span\{[\s\S]*?display:none!important/);
});
