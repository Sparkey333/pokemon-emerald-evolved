@echo off
rem Pokemon Evolved - one launcher for everything in this repo (Windows).
rem
rem   Play.bat                 open the hub (tabbed launcher) in your browser
rem   Play.bat hub             same
rem   Play.bat gen1            play Gen 1 (Red/Blue/Yellow) via engines\gen1recomp
rem   Play.bat emerald         open the Emerald evolution showcase
rem   Play.bat build-hub       regenerate apps\hub\index.html from source data
rem
rem No ROMs ship with this repository. Gen 1 asks for your own legally obtained
rem .gb/.gbc on first run; the Emerald build needs your own Emerald .gba.

setlocal
cd /d "%~dp0"

set "CMD=%~1"
if "%CMD%"=="" set "CMD=hub"

if /i "%CMD%"=="hub"       goto hub
if /i "%CMD%"=="gen1"      goto gen1
if /i "%CMD%"=="rby"       goto gen1
if /i "%CMD%"=="emerald"   goto emerald
if /i "%CMD%"=="gen3"      goto emerald
if /i "%CMD%"=="showcase"  goto emerald
if /i "%CMD%"=="realms"    goto realms
if /i "%CMD%"=="original"  goto realms
if /i "%CMD%"=="build-hub" goto buildhub
if /i "%CMD%"=="help"      goto usage
if /i "%CMD%"=="-h"        goto usage
if /i "%CMD%"=="--help"    goto usage

echo error: unknown command: %CMD%
echo.
goto usage

:hub
if not exist "apps\hub\index.html" (
  where python >nul 2>&1 && (
    echo ==^> generating the hub page
    python "apps\hub\build_hub.py"
  )
)
if not exist "apps\hub\index.html" (
  echo error: apps\hub\index.html not found and could not be generated
  exit /b 1
)
echo ==^> opening the hub
start "" "apps\hub\index.html"
goto end

:gen1
if not exist "engines\gen1recomp\main.lua" (
  echo error: engines\gen1recomp is missing - see engines\VENDOR.md
  exit /b 1
)
echo ==^> starting Gen 1 ^(gen1recomp^)
echo ==^> first run decodes a ROM you supply; later runs launch straight away
rem bootstrap.ps1 installs Python/LOVE if needed, builds game data, then launches.
powershell -NoProfile -ExecutionPolicy Bypass -File "engines\gen1recomp\scripts\bootstrap.ps1"
if errorlevel 1 (
  echo.
  echo Something went wrong - see the messages above.
  pause
)
goto end

:emerald
echo ==^> opening the Emerald evolution showcase
start "" "hack\showcase\pokemon-evolved-official-vs-diy.html"
goto end

:realms
if not exist "apps\realms\index.html" (
  where python >nul 2>&1 && python "apps\realms\build.py"
)
echo ==^> opening Emerald Realms
start "" "apps\realms\index.html"
goto end

:buildhub
where python >nul 2>&1 || (
  echo error: python is required
  exit /b 1
)
python "apps\hub\build_hub.py"
goto end

:usage
echo Usage: Play.bat [hub^|gen1^|emerald^|build-hub]
echo.
echo   hub         open the tabbed launcher in your browser (default)
echo   gen1        play Gen 1 Red/Blue/Yellow (asks for your own ROM)
echo   emerald     open the Emerald evolution showcase
echo   build-hub   regenerate apps\hub\index.html
exit /b 2

:end
endlocal
