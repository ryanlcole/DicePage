@echo off
echo ============================================
echo   Deploying to Azure: relicgamemaster2
echo ============================================
echo.

REM Navigate to project directory
cd /d %~dp0

REM Commit latest local changes
git add .
git commit -m "Auto-deploy DiceMall update"
git push

REM Deploy to Azure
az webapp up --name relicgamemaster2 --resource-group ryancole_rg_7000 --runtime "node|20-lts" --sku F1 --location eastus

echo.
echo ============================================
echo   Deployment Complete!
echo ============================================
pause
