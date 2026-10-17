@echo off
rem Kullanim: calistir.bat baslangic.json komutlar.jsonl > sonuclar.jsonl
rem Hangi klasorden cagrilirsa cagrilsin proje klasoru PYTHONPATH'e eklenir.
setlocal
set "PYTHONPATH=%~dp0."

where python >nul 2>nul
if %errorlevel%==0 (
    python -m komut_satiri.isleyici %*
) else (
    py -3 -m komut_satiri.isleyici %*
)
exit /b %errorlevel%
