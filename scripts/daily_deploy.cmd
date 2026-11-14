@echo off
REM Wrapper so the Scheduled Task Execute path (reliably persisted) does the work
REM without depending on the fragile -Argument field. See daily_deploy.ps1.
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\HP\Documents\Default Project\mazzaroth_v3\scripts\daily_deploy.ps1"
