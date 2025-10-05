@echo off
setlocal ENABLEDELAYEDEXPANSION

:: =======================================================
::  Shaelvien / ReLiC_GameMaster — Fix Node ESM + Run Site
:: =======================================================
set DEST=C:\Users\Local User\source\repos\DicePage
cd /d "%DEST%"

echo ------------------------------------------------------
echo  Checking package.json for ESM configuration
echo ------------------------------------------------------

:: Ensure package.json exists
if not exist "package.json" (
  echo package.json not found. Creating a new one...
  >package.json echo {
  >>package.json echo   "name": "shaelvien-dicepage",
  >>package.json echo   "version": "1.0.0",
  >>package.json echo   "description": "Shaelvien Dice Mall test site",
  >>package.json echo   "type": "module",
  >>package.json echo   "main": "server.js",
  >>package.json echo   "scripts": { "start": "node server.js" },
  >>package.json echo   "dependencies": {
  >>package.json echo     "express": "^4.19.2",
  >>package.json echo     "compression": "^1.7.4",
  >>package.json echo     "helmet": "^7.1.0",
  >>package.json echo     "morgan": "^1.10.0"
  >>package.json echo   }
  >>package.json echo }
) else (
  echo Updating "type":"module" if missing...
  powershell -NoLogo -NoProfile -Command ^
  "(Get-Content package.json -Raw) -replace '\"type\":\\s*\"[^\"]*\"', '\"type\": \"module\"' | Set-Content package.json"
)

echo ------------------------------------------------------
echo  Rewriting server.js to modern ESM format
echo ------------------------------------------------------

>server.js echo import express from "express";
>>server.js echo import compression from "compression";
>>server.js echo import helmet from "helmet";
>>server.js echo import morgan from "morgan";
>>server.js echo const app = express();
>>server.js echo const PORT = process.env.PORT ^|^| 3000;
>>server.js echo app.use(helmet());
>>server.js echo app.use(compression());
>>server.js echo app.use(morgan("dev"));
>>server.js echo app.use(express.static("Public"));
>>server.js echo app.get("/", (req,res)=>res.sendFile("index.html", {root:"Public"}));
>>server.js echo app.listen(PORT, ()=>console.log(`DicePage running on http://localhost:${PORT}`));

echo ------------------------------------------------------
echo  Installing dependencies
echo ------------------------------------------------------
call npm install --silent

echo ------------------------------------------------------
echo  Launching local server
echo ------------------------------------------------------
start "" http://localhost:3000
start cmd /k "cd /d "%DEST%" && npm start"

echo ------------------------------------------------------
echo  If you see 'DicePage running on http://localhost:3000'
echo  then your Node ESM configuration is fixed.
echo ------------------------------------------------------
pause
endlocal
