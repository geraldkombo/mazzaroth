"""Regenerate docs/data from the engine's master log (today + hourly + db + wealth + areas).

Run whenever you want the deployed site to reflect a new date:
    python refresh_data.py
Then push / redeploy via wrangler.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    os.chdir(ROOT)
    target = sys.executable
    if not os.path.exists(os.path.join(ROOT, "generate_daily_data.py")):
        raise SystemExit("generate_daily_data.py not found; run this from mazzaroth_v3/")
    subprocess.check_call([target, "generate_daily_data.py"], cwd=ROOT)
    print("docs/data refreshed for", os.path.join(ROOT, "docs", "data"))
    print("Redeploy with:  cd mazzaroth_v3 && npx wrangler pages deploy docs --project-name mazzaroth")
    print("Chromium headless note: open the data/**/*.js files are JS globals — no build step needed.")


if __name__ == "__main__":
    main()