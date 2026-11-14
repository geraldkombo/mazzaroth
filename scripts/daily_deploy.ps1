# Mazzaroth daily deploy
# Pulls the GitHub bot's daily data refresh (committed ~00:05 UTC by deploy.yml),
# then deploys docs/ to Cloudflare Pages production (mazzaroth-660.pages.dev).
# Registered as Task Scheduler job "Mazzaroth daily deploy" at 06:30 local.
# Log: Mazzaroth_Engine_Data\daily_deploy.log

$ErrorActionPreference = 'Continue'
$root = 'C:\Users\HP\Documents\Default Project\mazzaroth_v3'
$log  = Join-Path $root 'Mazzaroth_Engine_Data\daily_deploy.log'
$npx  = 'C:\Program Files\nodejs\npx.cmd'

"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') start ===" | Out-File $log -Append -Encoding utf8
Set-Location $root

git pull --rebase --autostash origin main 2>&1 | Out-File $log -Append -Encoding utf8

& $npx -y wrangler@4 pages deploy docs --project-name mazzaroth --branch main 2>&1 |
    Select-Object -Last 4 | Out-File $log -Append -Encoding utf8

"=== $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') done ===" | Out-File $log -Append -Encoding utf8
