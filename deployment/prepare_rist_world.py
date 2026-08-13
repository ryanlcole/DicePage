import base64,json,re,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'apps'/'tactical';W=R/'apps'/'rist-world'/'wwwroot'
(W/'assets'/'atlas').mkdir(parents=True,exist_ok=True);(W/'data').mkdir(parents=True,exist_ok=True)
s=(T/'js'/'naeja_world_asset.js').read_text();m=re.search(r'data:image/jpeg;base64,([^\"]+)',s)
if not m: raise RuntimeError('Naeja JPEG missing')
(W/'assets'/'naeja.jpg').write_bytes(base64.b64decode(re.sub(r'\s+','',m.group(1))))
r=json.loads((T/'data'/'atlas'/'atlas_asset_registry.json').read_text());o=[]
for a in r.get('assets',[]):
 p=T/a.get('derivedPath','')
 if a.get('enabled') is False or not p.exists(): continue
 d=W/'assets'/'atlas'/p.name;shutil.copy2(p,d);o.append({'id':a['assetId'],'name':a.get('name',a['assetId']),'image':f'assets/atlas/{p.name}'})
(W/'data'/'atlas-public.json').write_text(json.dumps(o))
c=json.loads((T/'data'/'tabletop'/'card_definitions.json').read_text()).get('cards',[])
(W/'data'/'cards-public.json').write_text(json.dumps([{'id':x['cardId'],'name':x.get('name',x['cardId']),'type':x.get('cardType','card'),'text':x.get('text','')} for x in c]))
print({'naeja':True,'atlas':len(o),'cards':len(c)})
