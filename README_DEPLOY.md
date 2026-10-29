# MAZZAROTH — Personal Web App (Cloudflare Pages)

Private daily-reading dashboard + **Ask Mazzi** AI coach, deployed for free on Cloudflare Pages.

**Production URL: https://mazzaroth-660.pages.dev** (login required).

> Note: `mazzaroth.pages.dev` (no `-660`) is an unrelated Jekyll blog owned by another Cloudflare
> account — it is **not** this app. Our project is named `mazzaroth`; Cloudflare appended the `-660`
> suffix because the plain subdomain was already taken.
The engine data (`docs/data/*`) is precomputed by the Python engine; Cloudflare serves it with
server-side auth (your email) and proxies AI questions to Cerebras — your API key never reaches the browser.

---

## What got added

| Piece | Location |
|---|---|
| Auth gate (login with your email) | `functions/_middleware.js` + `functions/api/login.js` / `session.js` / `logout.js` |
| AI assistant endpoint (Cerebras `gpt-oss-120b`) | `functions/api/ask.js` |
| `Ask Mazzi` tab in the dashboard | `docs/index.html` |
| Threshold recalibration to `PEAK>11675 / VH>10806 / HIGH>9480` | `docs/index.html` |
| Daily refresh helper | `refresh_data.py` |
| Deploy config | `wrangler.jsonc`, `package.json`, `.github/workflows/deploy-pages.yml` |

---

## 1. Local run (free, instant preview)

```powershell
cd "C:\Users\HP\Documents\Default Project\mazzaroth_v3"
& "C:\Program Files\nodejs\npx.cmd" -y wrangler@4 pages dev docs --port 8788
```

Local secrets live in `.dev.vars` (gitignored):
`AUTH_EMAIL=geraldsikunyi@gmail.com` · `AUTH_PASS=<in .dev.vars>` · `SESSION_SECRET=<in .dev.vars>` · `CEREBRAS_API_KEY=<in .dev.vars>`

Open http://localhost:8788 → you'll get the sign-in page. (The default password is in `.dev.vars`.)

## 2. Deploy to production

First-time Authentication (one of):

- `& "C:\Program Files\nodejs\npx.cmd" -y wrangler@4 login`  → opens browser, approve
- or set `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ACCOUNT_ID` env vars (Scoped token: Account > Cloudflare Pages > Read/Write)

Then create the project (auto-created on first deploy if it doesn't exist) and set secrets:

```powershell
npx.cmd wrangler pages project create mazzaroth --production-branch main
npx.cmd wrangler pages secret put AUTH_EMAIL         --project-name mazzaroth   # geraldsikunyi@gmail.com
npx.cmd wrangler pages secret put AUTH_PASS          --project-name mazzaroth   # YOUR password (type it)
npx.cmd wrangler pages secret put SESSION_SECRET     --project-name mazzaroth   # a long random string
npx.cmd wrangler pages secret put CEREBRAS_API_KEY   --project-name mazzaroth   # your Cerebras key
```

Deploy:

```powershell
npx.cmd wrangler pages deploy docs --project-name mazzaroth
```

Done → **https://mazzaroth-660.pages.dev** (login required).

## 3. Keep the data fresh

The engine computes transits statically. To update the site to a new date (e.g. after it regenerates):

```powershell
python refresh_data.py      # rewrites docs/data/*
npx.cmd wrangler pages deploy docs --project-name mazzaroth
```

You can also let GitHub auto-deploy: commit the repo to
`github.com/geraldkombo/mazzaroth`, add repo secrets `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID`, and the included `.github/workflows/deploy-pages.yml` deploys on every push.

## 4. Locking it down more (optional)

- **Cloudflare Access** (Zero Trust): add `mazzaroth*.pages.dev` as an Access application with a
  policy for `geraldsikunyi@gmail.com`. That becomes a second, even stronger login layer.
- Change `AUTH_PASS` any time with a fresh `wrangler pages secret put AUTH_PASS`.

## Cost

Free tier: unlimited static assets, 100k Function requests/day (your usage is a handful), and
Cerebras/GPT-OSS-120b is fast and (for this volume) effectively free.

## Files to keep private

- `.dev.vars` — contains SESSION_SECRET + API key. Never commit. (Already gitignored.)
- Your Cloudflare secrets live only in Cloudflare, never in the repo.