/* Reference server-side authority logic for Open Reality.
   This file documents executable state-transition semantics; do not serve it as browser authority. */

export class OpenRealityAuthority {
  constructor(seed) {
    this.world = structuredClone(seed);
    this.queue = Promise.resolve();
  }

  publicState() {
    const w = this.world;
    return structuredClone({
      worldId: w.worldId,
      revision: w.revision,
      tick: w.tick,
      reality: w.reality,
      knowledge: w.knowledge,
      capabilities: ['observe', 'research', 'propose']
    });
  }

  submit(proposal) {
    const job = this.queue.then(() => this.#apply(proposal));
    this.queue = job.catch(() => {});
    return job;
  }

  #apply(proposal) {
    if (!proposal || proposal.expectedRevision !== this.world.revision) {
      return { ok:false, status:409, error:'STALE_REALITY', state:this.publicState() };
    }

    switch (proposal.action) {
      case 'form-atoms': return this.#formAtoms();
      case 'form-water': return this.#formWater();
      default: return { ok:false, status:400, error:'UNKNOWN_ACTION', state:this.publicState() };
    }
  }

  #commit(label, mutate) {
    const before = structuredClone(this.world.reality);
    mutate(this.world.reality);
    this.world.revision += 1;
    this.world.tick += 1;
    this.world.history.push({
      revision:this.world.revision,
      tick:this.world.tick,
      label,
      inverse:{ replaceReality:before }
    });
    return { ok:true, status:200, event:{label,revision:this.world.revision}, state:this.publicState() };
  }

  #formAtoms() {
    if (this.world.reality.shaeps.H1) return {ok:false,status:409,error:'ALREADY_FORMED',state:this.publicState()};
    return this.#commit('bind primitives into atoms', reality => {
      reality.shaeps.H1={id:'H1',kind:'hydrogen atom',members:['p1','e1'],metadata:{atomicNumber:1}};
      reality.shaeps.H2={id:'H2',kind:'hydrogen atom',members:['p2','e2'],metadata:{atomicNumber:1}};
      reality.shaeps.O1={id:'O1',kind:'oxygen atom',members:['oxygen-nucleus','oxygen-electrons'],metadata:{atomicNumber:8}};
      reality.glyphs['contains:H1']={kind:'contains',from:'H1',to:['p1','e1']};
      reality.glyphs['contains:H2']={kind:'contains',from:'H2',to:['p2','e2']};
    });
  }

  #formWater() {
    if (!this.world.reality.shaeps.H1 || !this.world.reality.shaeps.O1) return {ok:false,status:409,error:'PREREQUISITE_MISSING',state:this.publicState()};
    if (this.world.reality.shaeps.W1) return {ok:false,status:409,error:'ALREADY_FORMED',state:this.publicState()};
    return this.#commit('form H2O relationship', reality => {
      reality.glyphs['bond:H1-O1']={kind:'covalent-bond',from:'H1',to:'O1'};
      reality.glyphs['bond:H2-O1']={kind:'covalent-bond',from:'H2',to:'O1'};
      reality.shaeps.W1={id:'W1',kind:'H2O molecule',members:['H1','H2','O1'],metadata:{formula:'H2O',derived:true}};
    });
  }

  research(observation) {
    const id=`K${Object.keys(this.world.knowledge).length+1}`;
    this.world.knowledge[id]={...structuredClone(observation),observedAtRevision:this.world.revision,status:'observation-not-authority'};
    return {ok:true,status:200,knowledgeId:id,state:this.publicState()};
  }

  rewindOwner() {
    const event=this.world.history.pop();
    if(!event) return {ok:false,status:409,error:'GENESIS_BOUNDARY',state:this.publicState()};
    this.world.reality=structuredClone(event.inverse.replaceReality);
    this.world.revision=Math.max(0,this.world.revision-1);
    this.world.tick=Math.max(0,this.world.tick-1);
    return {ok:true,status:200,rewound:event.label,state:this.publicState()};
  }
}

export function createGenesisWorld(runes={}) {
  return {
    worldId:'OR-0001',
    revision:0,
    tick:0,
    reality:{runes:structuredClone(runes),glyphs:{},shaeps:{}},
    knowledge:{},
    history:[]
  };
}
