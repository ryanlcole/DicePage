const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

const root=path.resolve(__dirname,'..');
const read=relative=>fs.readFileSync(path.join(root,relative),'utf8');

test('environment offers Shaelvien RIST and Legacy as the three user-facing paths',()=>{
 const auth=read('Components/AuthenticatedWorld.razor');
 const gate=read('Components/LegacyWorldGate.razor');
 assert.match(auth,/Choose Shaelvien, RIST, or Legacy/);
 assert.match(auth,/<strong>SHAELVIEN<\/strong>/);
 assert.match(auth,/<strong>RIST<\/strong>/);
 assert.match(auth,/<strong>LEGACY<\/strong>/);
 assert.match(auth,/<LegacyWorldGate/);
 assert.match(auth,/@if\(Auth\.IsOwnerDiscordAccount\)[\s\S]*?class="rist-environment-dev"[\s\S]*?EXPERIMENTS/);
 assert.doesNotMatch(auth,/class="rist-environment-option experiments"/);
 assert.doesNotMatch(auth,/>MERGED</);
 assert.doesNotMatch(gate,/RIST LEGACY/);
 assert.match(gate,/<small>LEGACY<\/small>/);
});

test('Legacy accepts a ZIP and preserves provenance with safety limits',()=>{
 const gate=read('Components/LegacyWorldGate.razor');
 const importer=read('LegacyArchiveImport.cs');
 assert.match(gate,/IMPORT ZIP/);
 assert.match(gate,/accept="\.zip,application\/zip,application\/x-zip-compressed"/);
 assert.match(gate,/LegacyArchiveImport\.Validate\(bytes\)/);
 assert.match(gate,/Session\.CreateWorldAsync/);
 assert.match(importer,/MaxEntryCount=4000/);
 assert.match(importer,/MaxExpandedBytes=500L\*1024\*1024/);
 assert.match(importer,/Archive contains an unsafe relative path/);
 assert.match(importer,/SHA256\.HashData/);
 assert.match(importer,/OriginalKey/);
 assert.match(importer,/Runecore compatibility ladder/);
});

test('Legacy converts every entry to HTML and images into My Assets storage',()=>{
 const importer=read('LegacyArchiveImport.cs');
 assert.match(importer,/htmlKey=\$"\{root\}\/html\/\{id\}\.html"/);
 assert.match(importer,/assets\/images\/world\/legacy/);
 assert.match(importer,/DOCX text normalized to HTML/);
 assert.match(importer,/Legacy binary document: printable text recovered/);
 assert.match(importer,/SuggestedLocation/);
 assert.match(importer,/MY ASSETS/);
});

test('Legacy creates a linked PDF binder and dock resolves its links privately',()=>{
 const importer=read('LegacyArchiveImport.cs');
 const dock=read('Components/LegacyArchiveDock.razor');
 const bridge=read('wwwroot/legacy-archive-dock.js');
 const helper=read('wwwroot/legacy/index.html');
 const shell=read('Components/PublicAlphaShell.razor');
 assert.match(importer,/BinderPdf\(manifest,appBaseUri\)/);
 assert.match(importer,/legacy\/index\.html\?world=/);
 assert.match(dock,/BINDER PDF/);
 assert.match(dock,/OpenLegacyEntryFromBinderAsync/);
 assert.match(bridge,/rist-legacy-binder/);
 assert.match(helper,/postMessage\(\{source:'rist-legacy-binder'/);
 assert.match(shell,/<LegacyArchiveDock \/>/);
});

test('Legacy program handling is quarantine-first and does not execute imported code',()=>{
 const importer=read('LegacyArchiveImport.cs');
 assert.match(importer,/Quarantined binary\. Not executed/);
 assert.match(importer,/Quarantined source\. Not executed/);
 assert.doesNotMatch(importer,/Process\.Start|Assembly\.Load|eval\(|exec\(/);
});


test('Runecore accepts unknown file types without discarding them',()=>{
 const gate=read('Components/LegacyWorldGate.razor');
 const importer=read('LegacyArchiveImport.cs');
 assert.match(gate,/any file type inside it is preserved privately/);
 assert.match(importer,/return "FILE";/);
 assert.match(importer,/origin-unresolved/);
 assert.match(importer,/Opaque binary/);
 assert.match(importer,/The file is preserved intact and remains eligible for a future adapter or capsule/);
 assert.match(importer,/originalKey=\$"\{root\}\/originals/);
 assert.match(importer,/htmlKey=\$"\{root\}\/html/);
});

test('Runecore identifies origin signatures including Neverwinter Nights Aurora data',()=>{
 const importer=read('LegacyArchiveImport.cs');
 assert.match(importer,/NeverwinterExtensions/);
 assert.match(importer,/Neverwinter Nights \/ Aurora Toolset/);
 assert.match(importer,/BioWare Aurora resource container/);
 assert.match(importer,/win32-x86-no-network/);
 assert.match(importer,/OLE Compound Document/);
 assert.match(importer,/DOS\/Windows executable/);
 assert.match(importer,/ELF executable/);
});

test('Runecore capsule requests enforce isolation boundaries and do not execute imports',()=>{
 const importer=read('LegacyArchiveImport.cs');
 const dock=read('Components/LegacyArchiveDock.razor');
 assert.match(importer,/RunecoreCapsuleRequest/);
 assert.match(importer,/false,false,true,"ephemeral",120,512/);
 assert.match(importer,/awaiting-user-license-or-media/);
 assert.match(importer,/ready-for-isolated-executor/);
 assert.match(dock,/PREPARE ORIGIN CAPSULE/);
 assert.match(dock,/NO NETWORK · NO HOST CREDENTIALS · READ-ONLY SOURCE · EPHEMERAL WRITABLE SCRATCH/);
 assert.match(dock,/LICENSE \/ ORIGIN MEDIA/);
 assert.match(dock,/will not be auto-executed/);
 assert.doesNotMatch(importer,/Process\.Start|Assembly\.Load|VirtualBox|QEMU|eval\(|exec\(/);
 assert.doesNotMatch(dock,/Process\.Start|Assembly\.Load|eval\(|exec\(/);
});
