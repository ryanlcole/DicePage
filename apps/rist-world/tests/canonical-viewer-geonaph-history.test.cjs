const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const repoRoot=path.resolve(root,'..','..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');
const readRepo=relative=>fs.readFileSync(path.join(repoRoot,relative),'utf8');

test('GameMaster deed map remains isolated from stale Geonaph prototype state',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');
  assert.match(razor,/Stage\.MmoMap[\s\S]{0,100}?Stage\.HistoryCampaign[\s\S]{0,100}?Stage\.ContextSelect[\s\S]{0,100}?return "about:blank";/);
  assert.match(razor,/RequestHomeFromPrototypeAsync\(\)[\s\S]{0,520}?background child must never eject the player[\s\S]{0,300}?Stage\.MmoMap[\s\S]{0,140}?Stage\.HistoryCampaign/);
  assert.ok((mmo.match(/Session\.SetActiveRegion\(""\);/g)||[]).length>=2);
  assert.match(mmo,/The deed map is the Shaelvien root, not the previously opened zone/);
});

test('Geonaph allows Mature presentation while keeping historical provenance independent',()=>{
  const data=JSON.parse(read('wwwroot/data/geonaph/history/campaign-v1.json'));
  const instance=data.zone.region.local.instance;
  const allowed=new Set(['FACT','RECONSTRUCTION','FICTION']);
  assert.equal(data.world,'Geonaph');
  assert.equal(data.contentProfile.ratingStatus,'UNRATED');
  assert.equal(data.contentProfile.matureContent,'ALLOWED');
  assert.equal(data.contentProfile.presentation,'HISTORICAL_CONTEXT');
  assert.equal(data.contentProfile.provenanceIndependent,true);
  assert.match(data.contentProfile.principle,/Mature-rated presentation is allowed in Shaelvien/i);
  for(const value of [
    data.zone.classification,data.zone.region.classification,data.zone.region.local.classification,
    instance.classification,instance.playableReconstruction.classification,
    instance.languageContext.classification,instance.bridge.classification,
    ...instance.tasks.map(task=>task.classification),
    ...data.sources.map(source=>source.classification)
  ]) assert.ok(allowed.has(value),`invalid historical provenance: ${value}`);
  assert.ok(instance.tasks.every(task=>task.classification==='RECONSTRUCTION'));
  assert.ok(data.sources.every(source=>source.classification==='FACT'));
});

test('Lomekwi language and uncertainty stay explicit and reconstruction stays non-evidentiary',()=>{
  const data=JSON.parse(read('wwwroot/data/geonaph/history/campaign-v1.json'));
  const instance=data.zone.region.local.instance;
  const joined=JSON.stringify(instance).toLowerCase();
  assert.equal(instance.languageContext.originalLanguageStatus,'UNATTESTED');
  assert.equal(instance.languageContext.original,'No written or recorded language survives.');
  assert.equal(instance.languageContext.transliteration,'NOT AVAILABLE');
  assert.equal(instance.languageContext.translation,'No historical translation exists.');
  assert.match(joined,/taxonomic identity unresolved/);
  assert.match(instance.playableReconstruction.rule,/never promoted into a historical claim/i);
  assert.equal(instance.bridge.status,'LOCKED_UNTIL_NEXT_FACT_NODE_VERIFIED');
});

test('database seed migrates canonical display name and verifies provenance plus content policy',()=>{
  const seed=readRepo('infra/aws/rist-platform-geanaph-seed/app.py');
  const template=readRepo('infra/aws/rist-platform.yml');
  assert.match(seed,/ZONE_NAME = "Geonaph"/);
  assert.match(seed,/return normalized_name\(value\) in \{"geonaph", "geanaph"\}/);
  assert.ok((seed.match(/"provenance": "FACT"/g)||[]).length>=3);
  assert.match(seed,/"matureContent": "ALLOWED"/);
  assert.match(seed,/"provenanceIndependent": True/);
  assert.match(seed,/"historyProvenanceVerified": True/);
  assert.match(seed,/"historyContentPolicyVerified": True/);
  assert.match(seed,/"matureContentAllowed": True/);
  assert.match(template,/Revision: geonaph-east-v6-free-origin/);
});

test('first evidence-safe sprite package is reconstruction-only and taxonomically unresolved',()=>{
  const manifest=JSON.parse(read('wwwroot/assets/geonaph/history/lomekwi3/sprites/sprite-set.json'));
  const assets=JSON.parse(read('wwwroot/data/geonaph/history/assets-v1.json'));
  const svg=read('wwwroot/assets/geonaph/history/lomekwi3/sprites/lom3-toolmaker-actions.svg');
  assert.equal(manifest.provenance,'RECONSTRUCTION');
  assert.equal(manifest.taxonomicIdentity,'UNRESOLVED');
  assert.equal(manifest.matureContent,'ALLOWED');
  assert.deepEqual(manifest.frames.map(frame=>frame.action),[
    'neutral-locomotion-a','neutral-locomotion-b','observe-stone',
    'carry-stone','battering-percussion','core-working'
  ]);
  assert.equal(assets.region.id,'west-turkana');
  assert.equal(assets.local.id,'lomekwi-3');
  assert.equal(assets.instance.id,'lom3-toolmaking-locality');
  assert.equal(assets.spriteSets[0].provenance,'RECONSTRUCTION');
  assert.doesNotMatch(svg,/clothing|metal|spear|fire|species/i);
});


test('registered Pangea sprites retain asset bucket authority without frontend mirror dependence',()=>{
  const workflow=readRepo('.github/workflows/sync-rist-assets-aws.yml');
  assert.match(workflow,/Verify registered Pangea sprite authority/);
  assert.match(workflow,/authority[\s\S]{0,160}?lives in the asset bucket/);
  assert.match(workflow,/aws s3api head-object --bucket "\$ASSET_BUCKET" --key "\$target_key"/);
  assert.doesNotMatch(
    workflow,
    /FRONTEND_BUCKET[\s\S]{0,700}?sprites\/pangea\/registered|sprites\/pangea\/registered[\s\S]{0,700}?FRONTEND_BUCKET/
  );
});


test('Shaelvien content policy allows Mature ratings without changing provenance',()=>{
  const policy=JSON.parse(read('wwwroot/data/shaelvien/content-policy.json'));
  assert.equal(policy.world,'Shaelvien');
  assert.equal(policy.contentRating.matureContent,'ALLOWED');
  assert.equal(policy.contentRating.provenanceIndependent,true);
  assert.ok(policy.law.includes('Mature-rated content is allowed in Shaelvien.'));
  assert.ok(policy.law.includes('Content rating and historical provenance are separate systems.'));
});


test('World Builder shows the full Geonaph tier-layer stack while MMO stays flattened',()=>{
  const prototype=read('wwwroot/prototype/prototype.js');
  const interfaceRazor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');
  const seed=readRepo('infra/aws/rist-platform-geanaph-seed/app.py');

  const visualBlock=(seed.match(/VISUAL_LAYERS = \([\s\S]*?\n\)/)||[''])[0];
  const addresses=[...visualBlock.matchAll(/\("[^"]+",\s*"[^"]+",\s*(?:"[^"]+"|[A-Z_]+),\s*(\d+),\s*(\d+),/g)]
    .map(match=>[Number(match[1]),Number(match[2])]);
  assert.equal(addresses.length,9);
  assert.deepEqual([...new Set(addresses.map(address=>address[0]))],[0,1,2]);

  assert.match(prototype,/function allParallaxRestOffset\(item\)/);
  assert.match(prototype,/viewerTier!=='all'\|\|!isFullDeedFrameItem\(item\)/);
  assert.match(prototype,/const rest=allParallaxRestOffset\(item\);/);
  assert.match(prototype,/viewerTier='all';\s*viewerLayer=9;/);
  assert.match(interfaceRazor,/entryView=\{entryView\}.*renderer=20261001-zone-depth-1/);

  assert.match(mmo,/if \(tier != 0\) continue;/);
  assert.match(mmo,/JsonBool\(item, "mmoSurface", false\)/);
});


test('World Builder full stack remains independent from MMO Tier 0 optimization',()=>{
  const razor=read('Components/UniversalInterface.razor');
  const mmo=read('Components/UniversalInterface.MmoMap.cs');
  const seed=readRepo('infra/aws/rist-platform-geanaph-seed/app.py');

  assert.match(razor,/var entryView=access=="edit"\?"all-parallax":"saved";/);
  assert.doesNotMatch(razor,/entryView=access=="edit"&&[^\n]+selectedDeedName/);
  assert.match(
    razor,
    /if\(_stage==Stage\.WorldBuilderTier&&CurrentBuilderScope=="WORLD"\)[\s\S]{0,120}?await ShowAllWorldLayersAsync\(\);[\s\S]{0,100}?else[\s\S]{0,100}?await SyncWorldBuilderDepthAsync\(\);/
  );

  assert.match(mmo,/var tier = JsonInt\(item, "tier", 0\);[\s\S]{0,80}?if \(tier != 0\) continue;/);
  assert.match(mmo,/JsonBool\(item, "mmoSurface", false\)/);

  const tuples=[...seed.matchAll(/\("[^"]+",\s*"[^"]+",\s*(?:"[^"]+"|[A-Z_]+),\s*(\d),\s*(\d),\s*-?\d+,\s*(?:True|False)\)/g)]
    .map(match=>({tier:Number(match[1]),layer:Number(match[2])}));
  assert.equal(tuples.length,9);
  assert.deepEqual([...new Set(tuples.map(item=>item.tier))],[0,1,2]);
});
