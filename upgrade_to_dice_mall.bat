@echo off
setlocal ENABLEDELAYEDEXPANSION

:: ======================================================
::   Shaelvien / ReLiC_GameMaster — Dice Mall Upgrade
:: ======================================================
set DEST=C:\Users\Local User\source\repos\DicePage
set BRANCH=main

echo ------------------------------------------------------
echo  Syncing latest build from GitHub...
echo ------------------------------------------------------
cd /d "%DEST%"
git pull origin %BRANCH%

:: ---- Create Mall structure ----
if not exist "Public\js" mkdir "Public\js"
if not exist "Public\assets" mkdir "Public\assets"

echo ------------------------------------------------------
echo  Writing mall.json...
echo ------------------------------------------------------
>Public\mall.json echo {
>>Public\mall.json echo   "categories": [
>>Public\mall.json echo     { "id": 1, "name": "TTRPG", "banner": "assets/ttrpg_banner.png", "products": ["dice","maps","miniatures"] },
>>Public\mall.json echo     { "id": 2, "name": "Anime", "banner": "assets/anime_banner.png", "products": ["figures","tees","stickers"] },
>>Public\mall.json echo     { "id": 3, "name": "Cosplay", "banner": "assets/cosplay_banner.png", "products": ["armor","wigs","props"] }
>>Public\mall.json echo   ]
>>Public\mall.json echo }

echo ------------------------------------------------------
echo  Writing dice.js...
echo ------------------------------------------------------
>Public\js\dice.js echo // Shaelvien Dice Mall - D20 Interactive Gateway
>>Public\js\dice.js echo import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
>>Public\js\dice.js echo import { OrbitControls } from 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';
>>Public\js\dice.js echo let scene=new THREE.Scene(),camera,newRenderer,die;
>>Public\js\dice.js echo const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();
>>Public\js\dice.js echo init();animate();
>>Public\js\dice.js echo function init(){
>>Public\js\dice.js echo   newRenderer=new THREE.WebGLRenderer({antialias:true});
>>Public\js\dice.js echo   newRenderer.setSize(window.innerWidth,window.innerHeight);
>>Public\js\dice.js echo   document.body.appendChild(newRenderer.domElement);
>>Public\js\dice.js echo   camera=new THREE.PerspectiveCamera(50,window.innerWidth/window.innerHeight,0.1,1000);
>>Public\js\dice.js echo   camera.position.z=3;
>>Public\js\dice.js echo   const geo=new THREE.IcosahedronGeometry(1,0);
>>Public\js\dice.js echo   const mat=new THREE.MeshStandardMaterial({color:0x6688ff,metalness:0.8,roughness:0.3});
>>Public\js\dice.js echo   die=new THREE.Mesh(geo,mat);scene.add(die);
>>Public\js\dice.js echo   scene.add(new THREE.AmbientLight(0xffffff,0.8));
>>Public\js\dice.js echo   const light=new THREE.PointLight(0xffffff,1);light.position.set(5,5,5);scene.add(light);
>>Public\js\dice.js echo   const controls=new OrbitControls(camera,newRenderer.domElement);
>>Public\js\dice.js echo   document.addEventListener('click',onClick);
>>Public\js\dice.js echo }
>>Public\js\dice.js echo function onClick(event){
>>Public\js\dice.js echo   mouse.x=(event.clientX/window.innerWidth)*2-1;
>>Public\js\dice.js echo   mouse.y=-(event.clientY/window.innerHeight)*2+1;
>>Public\js\dice.js echo   raycaster.setFromCamera(mouse,camera);
>>Public\js\dice.js echo   const hits=raycaster.intersectObject(die);
>>Public\js\dice.js echo   if(hits.length>0){window.location.href="category.html?cat="+Math.ceil(Math.random()*3);}
>>Public\js\dice.js echo }
>>Public\js\dice.js echo function animate(){
>>Public\js\dice.js echo   requestAnimationFrame(animate);
>>Public\js\dice.js echo   die.rotation.x+=0.005;die.rotation.y+=0.005;
>>Public\js\dice.js echo   newRenderer.render(scene,camera);
>>Public\js\dice.js echo }

echo ------------------------------------------------------
echo  Writing mall.js...
echo ------------------------------------------------------
>Public\js\mall.js echo // Shaelvien Dice Mall - Category Renderer
>>Public\js\mall.js echo async function loadMall(){
>>Public\js\mall.js echo   const res=await fetch("mall.json");const data=await res.json();
>>Public\js\mall.js echo   const url=new URLSearchParams(window.location.search);
>>Public\js\mall.js echo   const id=parseInt(url.get("cat"))||1;
>>Public\js\mall.js echo   const cat=data.categories.find(c=>c.id===id);
>>Public\js\mall.js echo   document.body.style.background="black";document.body.style.color="white";
>>Public\js\mall.js echo   document.body.innerHTML=\`<h1>\${cat.name} Mall</h1><img src='\${cat.banner}' style='width:80%%;border-radius:10px;'><p>Products: \${cat.products.join(", ")}</p>\`;
>>Public\js\mall.js echo }
>>Public\js\mall.js echo loadMall();

echo ------------------------------------------------------
echo  Writing new index.html and category.html
echo ------------------------------------------------------
>Public\index.html echo ^<!DOCTYPE html^>
>>Public\index.html echo ^<html lang="en"^>^<head^>^<meta charset="UTF-8" /^>
>>Public\index.html echo ^<title^>Shaelvien Dice Mall^</title^>^</head^>
>>Public\index.html echo ^<body style="margin:0;overflow:hidden;background:black;"^>^<script type="module" src="js/dice.js"^>^</script^>^</body^>^</html^>

>Public\category.html echo ^<!DOCTYPE html^>
>>Public\category.html echo ^<html lang="en"^>^<head^>^<meta charset="UTF-8" /^>
>>Public\category.html echo ^<title^>Shaelvien Dice Mall - Category^</title^>^</head^>
>>Public\category.html echo ^<body^>^<script src="js/mall.js"^>^</script^>^</body^>^</html^>

echo ------------------------------------------------------
echo  Installing dependencies...
echo ------------------------------------------------------
call npm install --silent

echo ------------------------------------------------------
echo  Starting Dice Mall at http://localhost:3000
echo ------------------------------------------------------
start cmd /k "cd /d "%DEST%" && npm start"
pause
endlocal
