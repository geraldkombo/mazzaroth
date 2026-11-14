# MAZZAROTH - COMPLETE HANDOVER & INVENTORY (2026-11-14)

Everything Mazzaroth on this PC, how it deploys, and every access path. Verified live on 2026-11-14: nothing is locked out.

## 1. Live systems

| System | URL | Status |
|---|---|---|
| Production app (auth-gated) | https://mazzaroth-660.pages.dev | LIVE, data 2026-11-14, AI working |
| Today's deployment | https://a41d9d60.mazzaroth-660.pages.dev | Current production deployment |
| GitHub repo | https://github.com/geraldkombo/mazzaroth | Pushed, commit 36191da |
| Lovable rebuild (skyguard) | https://skyguard-ai-alerts.lovable.app | Sign-in wall; editing needs Lovable login (project lovp_41f1bf1v4e84ybafsm4k5r8963). Not needed for the Pages site. |

Note: `mazzaroth.pages.dev` (no -660) is someone else's Jekyll blog. Our project is named `mazzaroth`; Cloudflare appended -660.

## 2. Access paths (all verified 2026-11-14)

- Cloudflare: OAuth token for kombo@pm.me, Account "Kombo@pm.me's Account", Account ID fdff06ddff4a96e9709519f406fa7e36. Credentials: `C:\Users\HP\AppData\Roaming\xdg.config\.wrangler\config\default.toml`. `npx wrangler@4 pages deploy` works from this machine.
- GitHub: push credentials work (Git Credential Manager). Remote: origin = https://github.com/geraldkombo/mazzaroth.git. `gh` CLI is logged out but plain git push/pull works.
- App login (production): email + password in `.dev.vars` (AUTH_EMAIL / AUTH_PASS). Same values are set as Cloudflare Pages secrets. Verified: POST /api/login returns 200 on production.
- Cloudflare Pages secrets currently set on project `mazzaroth`: AUTH_EMAIL, AUTH_PASS, SESSION_SECRET. (CEREBRAS_API_KEY deleted 2026-11-14 - all Cerebras keys are account-blocked 402.)

## 3. Architecture

```
Python engine (this PC)                 Cloudflare Pages "mazzaroth"
--------------------------------        --------------------------------------
mazzaroth.py  core engine               docs/            static site (index.html)
mazz.py       CLI                       docs/data/*      precomputed engine data
quinarian_engine.py  72 quinaries       functions/       Pages Functions:
generate_daily_data.py -> docs/data/      _middleware.js   auth gate (HMAC session cookie)
refresh_data.py (wrapper)                 _lib.js          sessions, login page, thresholds
Skyfield + ephe/de421.bsp (JPL, 16MB)     _plain.js        plain-language layer
                                          _quinaries.js    72-quinary table
                                          _ai.js           AI backend (NEW 2026-11-14)
                                          api/login|logout|session  auth
                                          api/ask|brief|week        AI endpoints
```

- AI backend: Cloudflare Workers AI, free allowance, keyless (env.AI binding in wrangler.jsonc). Model chain: `@cf/meta/llama-3.3-70b-instruct-fp8-fast` -> `@cf/meta/llama-3.1-8b-instruct-fp8`. Responses carry `source:"workers-ai"`.
- Auth: single-user gate. HMAC-signed cookie `mazz_auth`, 30-day TTL, SESSION_SECRET signs.

## 4. Data pipeline & automation

1. GitHub Actions `deploy.yml`: daily 00:00 UTC regenerates docs/data + Mazzaroth_Engine_Data on ubuntu, commits as "Auto-deploy: Daily data refresh YYYY-MM-DD" (MazzarothBot). Commits to the repo only - does NOT deploy to Cloudflare (deliberate, commit 5822a5f).
2. `deploy-pages.yml`: manual-only Cloudflare deploy (needs repo secrets CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID).
3. NEW 2026-11-14: Task Scheduler job "Mazzaroth daily deploy" (06:30 daily, this PC, runs on battery, StartWhenAvailable) executes `scripts\daily_deploy.cmd` -> `scripts\daily_deploy.ps1`: git pull --rebase --autostash (picks up the bot's fresh data) then `wrangler pages deploy docs --project-name mazzaroth --branch main`. Log: `Mazzaroth_Engine_Data\daily_deploy.log`. This closes the gap that left production stale at 2026-10-07. Verified end-to-end 2026-11-14 (deploy c109c301).
   - GOTCHA: Task Scheduler silently fails (Result 0, nothing runs) when Execute is a path containing spaces ("Default Project"). The task must use Execute=`cmd.exe` + Argument=`/c "<full path to .cmd>"`. The .cmd wrapper exists for this reason.
   - GOTCHA: npm cache was corrupted/empty (Nov 1 disk cleanup aftermath) causing `npx wrangler` ENOENT failures; fixed with `npm cache verify` on 2026-11-14. If deploys ever fail with npm enoent again, rerun that.

Manual commands:
```powershell
cd "C:\Users\HP\Documents\Default Project\mazzaroth_v3"
# regenerate data locally (Python 3.13 + skyfield on this PC):
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" refresh_data.py
# deploy:
& "C:\Program Files\nodejs\npx.cmd" -y wrangler@4 pages deploy docs --project-name mazzaroth --branch main
# local dev (reads wrangler.jsonc + .dev.vars):
& "C:\Program Files\nodejs\npx.cmd" -y wrangler@4 pages dev --port 8788
```

Gotchas learned:
- wrangler 4.148 workerd only supports compatibility_date <= 2026-10-13 (wrangler.jsonc is pinned to that).
- If workerd dies with SQLITE_NOTADB, delete the project's `.wrangler\` folder (regenerable cache).
- Python is not on PATH in fresh shells; use the full path above.

## 5. Changes made 2026-11-14 (commit 36191da, pushed + deployed)

- Migrated api/ask.js, api/brief.js, api/week.js off dead Cerebras (all keys 402) onto shared `functions/_ai.js` (Workers AI primary, Cerebras fallback if ever re-keyed). Verified: ask 2.5s, brief 5.2s, week 3.6s, all 200, source workers-ai, on local dev AND production.
- Refreshed docs/data to 2026-11-14 (was 2026-10-07).
- wrangler.jsonc: added AI binding + nodejs_compat.
- Deleted dead CEREBRAS_API_KEY Pages secret; removed key from .dev.vars. Project is now keyless for AI.
- Registered Task Scheduler daily deploy (section 4).
- Kept the working-copy change that removed the three personal "YOUR PLACES" shortcuts from the city picker in docs/index.html.

## 6. Everything Mazzaroth on this PC

### Primary project (the engine + the site)
`C:\Users\HP\Documents\Default Project\mazzaroth_v3\`
- Engine: mazzaroth.py, mazz.py, quinarian_engine.py, mazzaroth_personal.py, mazzaroth_life_areas.py, mazzaroth_lunar.py, mazzaroth_noretro.py, transit_combiner.py, wealth_optimizer.py, execution_audit.py, optimizer.py, hourly_monitor.py, compare.py, mazzaroth_web.py
- Data pipeline: generate_daily_data.py, generate_master_log.py, refresh_data.py, build_csvs_from_master.py, build_thresholds.py, build_organized_package.py
- Sync/daemons: ics_auto_deploy.py, trex2_sync.py, zepp_auto_sync.py, zepp_correlate.py, watchdog.ps1, setup_quinarian.ps1, scripts\daily_deploy.ps1 (new)
- Site: docs/index.html, docs/data/*, functions/* (see section 3), wrangler.jsonc, .github/workflows/*
- Ephemeris: ephe/de421.bsp (JPL DE421, 16MB), ephe/weights.json, ephe/thresholds.json
- Engine data: Mazzaroth_Engine_Data/ (master log 3944 events 2026-2036, audit, predictions, high-leverage windows, Zepp correlation)
- Calendars: mazzaroth_exact.ics (986 events), quinarian_calendar.ics
- Readings: dad_quinarian_reading.md, gerald_quinarian_reading.md, MAZZAROTH_DAILY_READINGS.md, docs/data/gerald_reading.md
- Context/specs: README.md, README_DEPLOY.md, MAZZAROTH_CONTEXT.md, LOVABLE_BUILD_PROMPT.md (spec that built the skyguard Lovable app), .cursorrules, 254-GEO-AEO-MASTER-PROMPT-FINAL.md, 254-AEO-GEO-MASTER-PROMPT-v3.md, 254-X-ENGINE-v1.md, 254-LINKEDIN-ENGINE-v1.md
- Secrets: .dev.vars (gitignored; app login + session secret)

### Build/design history (threads)
- opencode: `Default Project\opencode-threads\sessions\` - main build sessions: 2026-09-21 ses_f3b91c57dffe (1914 hits), 2026-09-21 ses_f3b76839cffe, 2026-09-23 ses_f330ad65, 2026-09-28 ses_f183aa915ffe (has the Pages project table), plus ~55 sessions with mentions. Live sessions also in `~\.local\share\opencode\opencode.db`.
- Gemini: `Desktop\Gemini-Threads-komboshikunyi\091/092/095` (roadmap, perfection code, Engine v3 reading), `Desktop\Gemini-Threads-geraldshikunyi\150` + `Desktop\Gemini-Threads-ngeshuishikunyi\150` (Vault spiritual core)
- Mistral: `Desktop\Mistral-Threads\010 - Gerald Mazzaroth Data Review`
- Perplexity: `Documents\Perplexity-Archive\` (incl. Frances Rolleston "Mazzaroth, or The Constellations")
- Prompt inventory: `Default Project\254-Prompts\254-article-prompts-inventory.md` (items 3-5), `thread-ideas\mined-ideas.md`

### Full package
`C:\Users\HP\Documents\Default Project\MAZZAROTH_FULL_CODEBASE_ENGINE_2026-11-14.zip` - entire project incl. engine, ephemeris, data, site, functions (excludes only .git/__pycache__/.wrangler; GitHub holds history).

## 7. What skyguard (Lovable) is

`skyguard-ai-alerts.lovable.app` is the Lovable-hosted rebuild specified by `LOVABLE_BUILD_PROMPT.md` (same engine concept, TypeScript, Supabase sign-in). It is separate from the Pages site and behind its own login: Google sign-in with gearldshikunyi@gmail.com ONLY (user-confirmed 2026-11-14; note this is a different spelling from the Pages app email geraldsikunyi@gmail.com). Lovable project id: lovp_41f1bf1v4e84ybafsm4k5r8963 (edit at lovable.dev while signed in with that Google account). The Pages site (mazzaroth-660) is the one with the real engine data and the working AI, and it is fully under this PC's control - nothing needed from Lovable to keep it running.
