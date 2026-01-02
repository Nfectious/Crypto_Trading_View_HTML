@echo off
setlocal enabledelayedexpansion
set "SRC_DIR=%~dp0\..\"
set "BASE=%USERPROFILE%\crypto-playbook"

echo Deploying playbook to %BASE%
mkdir "%BASE%" 2>nul
mkdir "%BASE%\clips" 2>nul
mkdir "%BASE%\pdf" 2>nul
mkdir "%BASE%\deploy" 2>nul

echo Copying files...
xcopy "%SRC_DIR%index.html" "%BASE%\" /Y >nul
xcopy "%SRC_DIR%style.css" "%BASE%\" /Y >nul
xcopy "%SRC_DIR%script.js" "%BASE%\" /Y >nul
xcopy "%SRC_DIR%clips\*" "%BASE%\clips\" /E /I /Y >nul
xcopy "%SRC_DIR%pdf\*" "%BASE%\pdf\" /E /I /Y >nul
xcopy "%SRC_DIR%deploy\*" "%BASE%\deploy\" /E /I /Y >nul

echo Done. Opening playbook...
start "" "%BASE%\index.html"

pause
