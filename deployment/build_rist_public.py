from pathlib import Path
import base64, json, re, shutil, subprocess
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
DIST=ROOT/'dist'; SITE=ROOT/'site'; TACTICAL=ROOT/'apps'/'tactical'; RIST=ROOT/'apps'/'rist-world'
def main():
    www=RIST/'wwwroot'; (www/'assets').mkdir(parents=True,exist_ok=True); (www/'data').mkdir(parents=True,exist_ok=True)
    text=(TACTICAL/'js'/'naeja_world_asset.js').read_text(encoding='utf-8')
    m=re.search(r'data:image/jpeg;base64,([^\"]+)',text)
    if not m: raise RuntimeError('Naeja image missing')
    (www/'assets'/'naeja.jpg').write_bytes(base64.b64decode(m.group(1)))
    (www/'data'/'atlas-public.json').write_text('[]',encoding='utf-8')
    (www/'data'/'cards-public.json').write_text('[]',encoding='utf-8')
    out=ROOT/'publish-rist'; shutil.rmtree(out,ignore_errors=True)
    subprocess.run(['dotnet','publish',str(RIST/'RistWorld.csproj'),'-c','Release','-o',str(out)],check=True)
    shutil.rmtree(DIST,ignore_errors=True); DIST.mkdir()
    shutil.copy2(SITE/'landing'/'index.html',DIST/'index.html'); shutil.copy2(SITE/'site-shell.css',DIST/'site-shell.css')
    for route in ('store','docs','lab'): shutil.copytree(SITE/route,DIST/route)
    shutil.copytree(out/'wwwroot',DIST/'app')
    p=DIST/'app'/'index.html'; p.write_text(p.read_text().replace('<base href="/">','<base href="/DicePage/app/">'))
    info={'applicationVersion':'rist-world-net10','buildId':'rist-'+datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S'),'deploymentEnvironment':'repository-predeploy'}
    (DIST/'build-info.json').write_text(json.dumps(info,indent=2)+'\n')
    return 0
if __name__=='__main__': raise SystemExit(main())
