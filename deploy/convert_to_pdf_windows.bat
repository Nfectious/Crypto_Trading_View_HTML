@echo off
setlocal
set "ROOT_DIR=%~dp0\.."
set "HTML=%ROOT_DIR%\pdf\pullback-playbook-sol-ltc.html"
set "OUT=%ROOT_DIR%\pdf\pullback-playbook-sol-ltc.pdf"

rem Try wkhtmltopdf
where wkhtmltopdf >nul 2>nul
if %errorlevel%==0 (
  wkhtmltopdf --enable-local-file-access "%HTML%" "%OUT%"
  echo PDF created with wkhtmltopdf
  goto :done
)

rem Try Chrome/Edge (expecting chrome/chromium in PATH)
where chrome >nul 2>nul || where msedge >nul 2>nul
if %errorlevel%==0 (
  for %%C in (chrome msedge) do (
    where %%C >nul 2>nul || continue
    "%%~$PATH:C%%" --headless --disable-gpu --print-to-pdf="%OUT%" "file:///%HTML%"
    if %errorlevel%==0 (
      echo PDF created with %%C
      goto :done
    )
  )
)

echo No supported PDF renderer found. Install wkhtmltopdf or Chrome/Edge and add to PATH.
exit /b 2

:done
echo Done: %OUT%
pause
