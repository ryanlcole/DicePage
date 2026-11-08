'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const script = fs.readFileSync(path.join(__dirname, '..', 'worker.js'), 'utf8');
const handlers = [];
const attrs = {};
const sectionIDs = {gear:[],spells:[]};
const writes = [];
let passed = 0;
function expect(label, cb){try{ cb(); passed++; console.log('PASS',label);}catch(e){console.error('FAIL',label,e);process.exitCode=1;}}
function trigger(event, attr) {
  const eventInfo={sourceAttribute:attr||'',triggerName:event,sourceType:'player'};
  handlers.filter(h=>h.events.includes(event)).forEach(h=>h.fn(eventInfo));
}
const sandbox={
  on:function(events,fn){handlers.push({events:events.split(/\s+/),fn});},
  getAttrs:function(names,fn){let v={};names.forEach(n=>{if(Object.prototype.hasOwnProperty.call(attrs,n))v[n]=attrs[n];});fn(v);},
  setAttrs:function(obj,opts,cb){Object.assign(attrs,obj);writes.push({obj,opts});if(typeof cb==='function')cb();},
  getSectionIDs:function(section,fn){fn(sectionIDs[section.replace(/^repeating_/, '')]||[]);},
  console
};
vm.createContext(sandbox); vm.runInContext(script,sandbox,{filename:'worker.js'});
function recipe(values,id='-Recipe1') {
  let pre='repeating_dicebag_'+id+'_'; Object.keys(attrs).filter(k=>k.startsWith(pre)).forEach(k=>delete attrs[k]); Object.keys(values).forEach(k=>attrs[pre+k]=String(values[k]));
  trigger('change:repeating_dicebag:recipe_sides',pre+'recipe_sides');
  return {command:attrs[pre+'recipe_command'],status:attrs[pre+'recipe_status']};
}
expect('registers recipe events',()=>assert.ok(handlers.some(x=>x.events.includes('change:repeating_dicebag:recipe_count'))));
expect('1d20 base recipe',()=>assert.equal(recipe({recipe_name:'Perception',recipe_count:'1',recipe_sides:'20'}).command,'&{template:default} {{name=Perception}} {{Roll=[[1d20]]}}'));
expect('advantage + flat bonus',()=>assert.match(recipe({recipe_name:'Attack',recipe_count:'2',recipe_sides:'20',recipe_keep:'kh',recipe_keepcount:'1',recipe_bonus:'3'}).command,/2d20kh1\+3/));
expect('keep lowest',()=>assert.match(recipe({recipe_count:'3',recipe_sides:'6',recipe_keep:'kl',recipe_keepcount:'2'}).command,/3d6kl2/));
expect('drop highest',()=>assert.match(recipe({recipe_count:'4',recipe_sides:'6',recipe_keep:'dh',recipe_keepcount:'1'}).command,/4d6dh1/));
expect('negative bonus',()=>assert.match(recipe({recipe_count:'1',recipe_sides:'20',recipe_bonus:'-2'}).command,/1d20-2/));
expect('success threshold',()=>assert.match(recipe({recipe_count:'6',recipe_sides:'6',recipe_target:'5'}).command,/6d6>5/));
expect('exploding and reroll',()=>assert.match(recipe({recipe_count:'3',recipe_sides:'6',recipe_explode:'1',recipe_reroll:'ro1'}).command,/3d6!ro1/));
expect('custom d30',()=>assert.match(recipe({recipe_count:'1',recipe_sides:'custom',recipe_customsides:'30'}).command,/1d30/));
expect('Fate dice',()=>assert.match(recipe({recipe_count:'4',recipe_sides:'F'}).command,/4dF/));
expect('Fate restriction handled',()=>assert.match(recipe({recipe_count:'4',recipe_sides:'F',recipe_explode:'1'}).status,/Manual mode/));
expect('whisper GM',()=>assert.ok(recipe({recipe_count:'3',recipe_sides:'6',recipe_visibility:'gm'}).command.startsWith('/w gm ')));
expect('manual macro preserved',()=>assert.equal(recipe({recipe_mode:'manual',recipe_manual:'/roll 1d20 + @{strength_mod}'}).command,'/roll 1d20 + @{strength_mod}'));
expect('manual character ability call',()=>assert.equal(recipe({recipe_mode:'manual',recipe_manual:'%{selected|repeating_actions_$0_action}'}).command,'%{selected|repeating_actions_$0_action}'));
expect('manual shared macro reference',()=>assert.equal(recipe({recipe_mode:'manual',recipe_manual:'#initiative'}).command,'#initiative'));
expect('manual Mod is opt in',()=>assert.equal(recipe({recipe_mode:'manual',recipe_manual:'!rollinit'}).command,'!rollinit'));
expect('manual no newline',()=>assert.match(recipe({recipe_mode:'manual',recipe_manual:'/roll 1d20\n!other'}).status,/Fix manual command/));
expect('manual rejects unqualified raw text',()=>assert.match(recipe({recipe_mode:'manual',recipe_manual:'hello'}).status,/Use \/roll/));
expect('invalid keep/drop',()=>assert.match(recipe({recipe_count:'1',recipe_sides:'20',recipe_keep:'kh',recipe_keepcount:'1'}).status,/Check keep/));
expect('invalid custom sides',()=>assert.match(recipe({recipe_count:'1',recipe_sides:'custom',recipe_customsides:'1'}).status,/Check number/));
expect('name sanitization',()=>assert.ok(!recipe({recipe_name:'Test }} {{evil=BAD',recipe_count:'1',recipe_sides:'20'}).command.includes('{{evil=')));
expect('independent recipe rows',()=>{
  const a=recipe({recipe_name:'Alpha',recipe_count:'1',recipe_sides:'4'},'-A');
  const b=recipe({recipe_name:'Beta',recipe_count:'3',recipe_sides:'8'},'-B');
  assert.match(a.command,/1d4/);assert.match(b.command,/3d8/);
  assert.match(attrs['repeating_dicebag_-A_recipe_command'],/1d4/);
});
expect('initial gear sum',()=>{sectionIDs.gear=[];trigger('sheet:opened','');assert.equal(attrs.carried_weight,0);});
expect('carried gear quantity weight',()=>{
 sectionIDs.gear=['-A','-B','-C'];
 Object.assign(attrs,{
   'repeating_gear_-A_gear_carried':'1','repeating_gear_-A_gear_qty':'2','repeating_gear_-A_gear_weight':'1.5',
   'repeating_gear_-B_gear_carried':'0','repeating_gear_-B_gear_qty':'1','repeating_gear_-B_gear_weight':'50',
   'repeating_gear_-C_gear_carried':'1','repeating_gear_-C_gear_qty':'3','repeating_gear_-C_gear_weight':'0.2'
 });
 trigger('change:repeating_gear:gear_qty','repeating_gear_-A_gear_qty');assert.equal(attrs.carried_weight,3.6);
});
expect('gear rows removed trigger recompute',()=>{sectionIDs.gear=['-C'];trigger('remove:repeating_gear','');assert.equal(attrs.carried_weight,0.6);});
expect('prepared spell counter',()=>{
 sectionIDs.spells=['-X','-Y'];
 attrs['repeating_spells_-X_spell_prepared']='2';attrs['repeating_spells_-Y_spell_prepared']='3';
 trigger('change:repeating_spells:spell_prepared','repeating_spells_-X_spell_prepared');
 assert.equal(attrs.prepared_total,5);
});
expect('prepared negative ignored',()=>{
 attrs['repeating_spells_-X_spell_prepared']='-4';
 trigger('change:repeating_spells:spell_prepared','repeating_spells_-X_spell_prepared');
 assert.equal(attrs.prepared_total,3);
});
console.log(`\n${passed} worker tests passed; ${handlers.length} handlers registered; ${writes.length} setAttrs calls.`);
