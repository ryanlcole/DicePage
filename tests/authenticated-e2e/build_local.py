"""Builds an isolated Debug publication, never a production authentication variant."""
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
from local_harness import require_test_environment, RUNTIME, ROOT

require_test_environment()
RUNTIME.mkdir(exist_ok=True)
marker = RUNTIME / 'build.json'
marker.unlink(missing_ok=True)
dotnet = sys.argv[1] if len(sys.argv) > 1 else 'dotnet'
project = ROOT / 'apps/rist-world/RistWorld.csproj'
properties = []
# Optional compiler compatibility for sandboxes that cannot start MSBuild's
# Unix-socket task host. Use exactly the restored SDK tasks in-process; never
# change application compilation, auth, source files or production targets.
if os.environ.get('SHAELVIEN_E2E_WASM_IN_PROCESS') == '1':
    subprocess.run([dotnet, 'restore', str(project), '--nologo'], cwd=ROOT, check=True)
    assets = json.loads((project.parent / 'obj/project.assets.json').read_text())
    package = next(key for key in assets['libraries'] if key.lower().startswith('microsoft.net.sdk.webassembly.pack/'))
    assembly = next(path for folder in assets['packageFolders']
        if (path := Path(folder) / package.lower() / 'tools/net10.0/Microsoft.NET.Sdk.WebAssembly.Pack.Tasks.dll').is_file())
    target = ET.Element('Project')
    for name in ('ComputeWasmBuildAssets', 'ComputeWasmPublishAssets', 'ConvertDllsToWebCil', 'GenerateWasmBootJson'):
        ET.SubElement(target, 'UsingTask', TaskName='Microsoft.NET.Sdk.WebAssembly.' + name,
            AssemblyFile=str(assembly), Override='true')
    targets = RUNTIME / 'in-process-wasm.targets'
    ET.ElementTree(target).write(targets)
    properties = ['-m:1', '-nr:false', '-p:CustomBeforeMicrosoftCommonTargets=' + str(targets)]
subprocess.run([dotnet, 'publish',
    str(ROOT / 'apps/rist-world/RistWorld.csproj'), '-c', 'Debug',
    '-o', str(RUNTIME / 'publish'), '--nologo', '-p:PublishTrimmed=false', *properties], cwd=ROOT, check=True)
marker.write_text(json.dumps({'environment': 'test', 'configuration': 'Debug'}))
