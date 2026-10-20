/* Open Reality — isolated deterministic genesis proof.
   Reality is current state. Knowledge is observer-derived. History stores reversible deltas. */
(() => {
  'use strict';

  const clone = value => JSON.parse(JSON.stringify(value));
  const seed = {
    id: 'OR-0001',
    revision: 0,
    tick: 0,
    runes: {
      p1:{id:'p1',kind:'proton',charge:1,mass:1},
      e1:{id:'e1',kind:'electron',charge:-1,mass:0.0005446},
      p2:{id:'p2',kind:'proton',charge:1,mass:1},
      e2:{id:'e2',kind:'electron',charge:-1,mass:0.0005446},
      p3:{id:'p3',kind:'proton',charge:1,mass:1},
      p4:{id:'p4',kind:'proton',charge:1,mass:1},
      p5:{id:'p5',kind:'proton',charge:1,mass:1},
      p6:{id:'p6',kind:'proton',charge:1,mass:1},
      p7:{id:'p7',kind:'proton',charge:1,mass:1},
      p8:{id:'p8',kind:'proton',charge:1,mass:1},
      p9:{id:'p9',kind:'proton',charge:1,mass:1},
      p10:{id:'p10',kind:'proton',charge:1,mass:1},
      n1:{id:'n1',kind:'neutron',charge:0,mass:1},n2:{id:'n2',kind:'neutron',charge:0,mass:1},
      n3:{id:'n3',kind:'neutron',charge:0,mass:1},n4:{id:'n4',kind:'neutron',charge:0,mass:1},
      n5:{id:'n5',kind:'neutron',charge:0,mass:1},n6:{id:'n6',kind:'neutron',charge:0,mass:1},
      n7:{id:'n7',kind:'neutron',charge:0,mass:1},n8:{id:'n8',kind:'neutron',charge:0,mass:1},
      oE1:{id:'oE1',kind:'electron',charge:-1,mass:0.0005446},oE2:{id:'oE2',kind:'electron',charge:-1,mass:0.0005446},
      oE3:{id:'oE3',kind:'electron',charge:-1,mass:0.0005446},oE4:{id:'oE4',kind:'electron',charge:-1,mass:0.0005446},
      oE5:{id:'oE5',kind:'electron',charge:-1,mass:0.0005446},oE6:{id:'oE6',kind:'electron',charge:-1,mass:0.0005446},
      oE7:{id:'oE7',kind:'electron',charge:-1,mass:0.0005446},oE8:{id:'oE8',kind:'electron',charge:-1,mass:0.0005446}
    },
    glyphs:{}, shaeps:{}, knowledge:{}, history:[]
  };

  let world = clone(seed);
  const $ = id => document.getElementById(id);
  const log = text => { const el=$('log'); if(el) el.textContent=`${new Date().toISOString()} — ${text}\n`+(el.textContent==='No local observations yet.'?'':el.textContent); };
  const shaep = (id,kind,members,metadata={}) => ({id,kind,members:[...members],metadata:{...metadata}});

  function commit(label, mutate){
    const before={glyphs:clone(world.glyphs),shaeps:clone(world.shaeps)};
    mutate(world);
    world.revision++; world.tick++;
    world.history.push({revision:world.revision,tick:world.tick,label,before});
    render(); log(`reality changed: ${label}`);
  }

  function genesis(){
    if(world.revision!==0) return;
    commit('bind primitives into atoms', w=>{
      w.shaeps.H1=shaep('H1','hydrogen atom',['p1','e1'],{atomicNumber:1});
      w.shaeps.H2=shaep('H2','hydrogen atom',['p2','e2'],{atomicNumber:1});
      w.shaeps.O1=shaep('O1','oxygen atom',['p3','p4','p5','p6','p7','p8','p9','p10','n1','n2','n3','n4','n5','n6','n7','n8','oE1','oE2','oE3','oE4','oE5','oE6','oE7','oE8'],{atomicNumber:8});
      w.glyphs['nucleus:H1']={kind:'contains',from:'H1',to:['p1']};
      w.glyphs['nucleus:H2']={kind:'contains',from:'H2',to:['p2']};
      w.glyphs['nucleus:O1']={kind:'contains',from:'O1',to:['p3','p4','p5','p6','p7','p8','p9','p10','n1','n2','n3','n4','n5','n6','n7','n8']};
    });
  }

  function buildWater(){
    if(world.shaeps.W1) return;
    if(!world.shaeps.H1) genesis();
    commit('form H₂O relationship', w=>{
      w.glyphs['bond:H1-O1']={kind:'covalent-bond',from:'H1',to:'O1'};
      w.glyphs['bond:H2-O1']={kind:'covalent-bond',from:'H2',to:'O1'};
      w.shaeps.W1=shaep('W1','H₂O molecule',['H1','H2','O1'],{formula:'H₂O',derived:true});
    });
  }

  function research(){
    const target=world.shaeps.W1||world.shaeps.O1||world.shaeps.H1;
    if(!target){ log('nothing structured to research yet'); return; }
    const key=`observation:${target.id}`;
    world.knowledge[key]={target:target.id,observedAtRevision:world.revision,claim:`Observed ${target.kind}`,status:'observation-not-authority'};
    render(); log(`knowledge added about ${target.id}; reality unchanged`);
  }

  function rewind(){
    const event=world.history.pop();
    if(!event){ log('genesis boundary reached'); return; }
    world.glyphs=event.before.glyphs; world.shaeps=event.before.shaeps;
    world.revision=Math.max(0,world.revision-1); world.tick=Math.max(0,world.tick-1);
    render(); log(`rewound: ${event.label}`);
  }

  function observe(){
    const r=Object.keys(world.runes).length,g=Object.keys(world.glyphs).length,s=Object.keys(world.shaeps).length,k=Object.keys(world.knowledge).length;
    log(`observation: ${r} runes · ${g} glyphs · ${s} shaeps · ${k} knowledge records · revision ${world.revision}`);
  }

  function render(){
    if($('revision')) $('revision').textContent=String(world.revision).padStart(6,'0');
    if($('state')) $('state').textContent=world.shaeps.W1?'H₂O':world.revision?'ATOMS':'GENESIS';
    if($('runeCount')) $('runeCount').textContent=Object.keys(world.runes).length;
    if($('glyphCount')) $('glyphCount').textContent=Object.keys(world.glyphs).length;
    if($('shaepCount')) $('shaepCount').textContent=Object.keys(world.shaeps).length;
    if($('knowledgeCount')) $('knowledgeCount').textContent=Object.keys(world.knowledge).length;
    if($('historyCount')) $('historyCount').textContent=world.history.length;
    try{ localStorage.setItem('shaelvien.openReality.prototype.v1',JSON.stringify(world)); }catch{}
  }

  try{
    const saved=localStorage.getItem('shaelvien.openReality.prototype.v1');
    if(saved) world=JSON.parse(saved);
  }catch{}

  window.OpenReality={observe,research,genesis,buildWater,rewind,reset(){world=clone(seed);render();log('local prototype reset to genesis');},snapshot(){return clone(world);}};
  addEventListener('DOMContentLoaded',render);
})();
