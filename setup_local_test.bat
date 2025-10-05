@echo off
setlocal ENABLEDELAYEDEXPANSION

:: ================================================================
::  Shaelvien / ReLiC_GameMaster  —  Local Test & GitHub Sync
:: ================================================================
set DEST=C:\Users\Local User\source\repos\DicePage
set BRANCH=main

echo ------------------------------------------------
echo   Rebuilding local DicePage and syncing GitHub
echo ------------------------------------------------
cd /d "%DEST%"

:: ---- 0. Verify Git repo  ----
if not exist ".git" (
    echo Initializing new git repository...
    git init
    echo Please set your remote manually after this run if not done.
)

:: ---- 1. Create/refresh Node project ----
if not exist "package.json" (
    echo Creating package.json...
    >package.json echo {
    >>package.json echo   "name": "shaelvien-dicepage",
    >>package.json echo   "version": "1.0.0",
    >>package.json echo   "description": "Shaelvien Dice Mall test site",
    >>package.json echo   "type": "module",
    >>package.json echo   "main": "server.js",
    >>package.json echo   "scripts": { "start": "node server.js" },
    >>package.json echo   "engines": { "node": ">=18" },
    >>package.json echo   "dependencies": {
    >>package.json echo     "express": "^4.19.2",
    >>package.json echo     "compression": "^1.7.4",
    >>package.json echo     "helmet": "^7.1.0",
    >>package.json echo     "morgan": "^1.10.0"
    >>package.json echo   }
    >>package.json echo }
)

:: ---- 2. Basic server.js ----
if not exist "server.js" (
    echo Writing server.js...
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
)

:: ---- 3. Public folder ----
if not exist "Public" mkdir Public
if not exist "Public\index.html" (
    echo Creating index.html...
    >Public\index.html echo ^<!DOCTYPE html^>
    >>Public\index.html echo ^<html lang="en"^>^<head^>^<meta charset="UTF-8" /^>
    >>Public\index.html echo ^<title^>Shaelvien DicePage Test^</title^>^</head^>^<body style="background:black;color:white;text-align:center;padding-top:20%%;"^>
    >>Public\index.html echo ^<h1^>Shaelvien DicePage - Local Test^</h1^>
    >>Public\index.html echo ^<p^>Server running correctly on localhost.^</p^>
    >>Public\index.html echo ^</body^>^</html^>
)

:: ---- 4. Install dependencies ----
echo Installing npm dependencies...
call npm install --silent

:: ---- 5. Start local server ----
echo.
echo ------------------------------------------------
echo   Starting local server on http://localhost:3000
echo ------------------------------------------------
start cmd /k "cd /d "%DEST%" && npm start"

:: ---- 6. Optional Git commit/push ----
echo.
set /p PUSHQ="Commit and push to GitHub now (Y/N)? "
if /I "%PUSHQ%"=="Y" (
    git add -A
    git commit -m "Local test rebuild"
    git push origin %BRANCH%
)

echo.
echo Done.  Site available locally at http://localhost:3000
pause
endlocal
