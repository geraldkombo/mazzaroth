#!/usr/bin/env python3
"""
Mazzaroth CLI - Real-time transit scoring, alerts, and T-Rex 2 integration.

Usage:
    python mazz.py now          Current transit score + active aspects
    python mazz.py today        Full day briefing
    python mazz.py week         7-day forecast from today
    python mazz.py watch        Daemon mode (checks every 30 min)
    python mazz.py search DATE  Look up date in 10-year database (YYYY-MM-DD)
    python mazz.py thresholds   Compute and cache score thresholds
    python mazz.py relationship Relationship & sex transits
    python mazz.py areas        All 13 life areas by intensity
    python mazz.py transits     All active transits mapped to life areas
    python mazz.py month        30-day transit outlook scan
    python mazz.py brief        Strategic Daily Brief (transit synthesis)
    python mazz.py wealth       Wealth Optimizer - financial astrology briefing
    python mazz.py wealth calendar  Financial calendar for next 60 days
    python mazz.py wealth pattern   Your billionaire wealth blueprint
    python mazz.py wealth invest    Investment timing analysis
    python mazz.py audit        Ground Truth audit status
    python mazz.py audit rate N tag  Rate today's outcome (1-5)
    python mazz.py audit history     Audit log
    python mazz.py audit regression  Hit-rate regression analysis
    python mazz.py ics generate      Regenerate ICS calendar file
    python mazz.py ics status        ICS deployment status
    python mazz.py ics deploy FOLDER Copy ICS to sync folder
    python mazz.py zepp status       Zepp import history
    python mazz.py zepp run FILE     Import Zepp CSV manually
"""

import sys, os, time, json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
import mazzaroth_life_areas as la

THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")
COLOR = True

# --- Multi-Subject Dispatch ---
CURRENT_USER = None
CURRENT_USER_DIR = None

def get_data_path(user):
    base = "subjects"
    os.makedirs(base, exist_ok=True)
    user_path = os.path.join(base, user)
    os.makedirs(user_path, exist_ok=True)
    return user_path

if os.name == "nt":
    os.system("color")

def c(code, text):
    if not COLOR: return text
    return f"\033[{code}m{text}\033[0m"

def bold(t): return c("1", t)
def red(t): return c("91", t)
def green(t): return c("92", t)
def yellow(t): return c("93", t)
def blue(t): return c("94", t)
def magenta(t): return c("95", t)
def cyan(t): return c("96", t)

DEFAULT_THRESHOLDS = {"peak": 3100, "vhigh": 2800, "high": 2400, "n": 3950}

def load_thresholds():
    if os.path.exists(THRESH_CACHE):
        with open(THRESH_CACHE) as f:
            return json.load(f)
    return DEFAULT_THRESHOLDS

def cmd_now():
    th = load_thresholds()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transit = mz.get_transit_data(now)
    score, hits = mz.score_transit(transit)
    level = mz.get_level(score, th)

    print(f"\n{bold('MAZZAROTH')} - {now.strftime('%Y-%m-%d %H:%M UTC')}  |  Profection: H{mz.PROF_HOUSE}")
    print("=" * 56)

    level_str = level if level else "NORMAL"
    if level == "PEAK": level_str = red(level_str)
    elif level == "VERY HIGH": level_str = yellow(level_str)
    elif level == "HIGH": level_str = green(level_str)
    print(f"  {bold('Score:')} {score:.0f}  |  {bold('Level:')} {level_str}  |  {bold('Thresholds:')} PEAK>{th['peak']:.0f} VH>{th['vhigh']:.0f} H>{th['high']:.0f}")
    print()

    if hits:
        print(f"  {bold('Active Aspects:')}")
        for s, desc, aname in hits[:8]:
            print(f"    {desc:<45} {s:>8.1f}")
        print()

        top = hits[0]
        tname = top[1].split(" ")[0]
        nname = "chart"
        if "natal " in top[1]:
            nname = top[1].split("natal ")[1].split(" ")[0]
        nd = mz.NATAL.get(nname, mz.NATAL["Sun"])
        h = mz._house_num(nd["lon"])
        interp, actions = mz.get_interpretation(tname, h)

        print(f"  {bold('Top Transit:')} {top[1]}")
        print(f"  {bold('House:')} H{h}")
        print(f"  {bold('Strategy:')} {interp}")
        print(f"  {bold('Actions:')}")
        for a in actions:
            print(f"    -> {a}")
        print()
        dt = now.strftime("%Y-%m-%d")
        print(f"  {bold('T-Rex 2 Memo:')}")
        print(f'  "{mz.t_rex_memo(tname, nname, h, interp, dt)}"')
    else:
        print(f"  No active aspects within orb.\n")

    # Check database for today
    db = mz.load_event_db()
    if db:
        today_events = mz.today_from_db(db, now.strftime("%Y-%m-%d"))
        if today_events:
            print(f"  {bold('Database Events Today:')}")
            for e in today_events:
                print(f"    [{e['Level']}] {e['Transit']} H{e['House']}  Score: {e['Score']}")
            print()
    else:
        print(f"  (No database CSV found — run 'python mazz.py build' first)")
        print()

def cmd_today():
    th = load_thresholds()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_str = now.strftime("%Y-%m-%d")

    print(f"\n{bold('MAZZAROTH TODAY')} — {today_str}")
    print("=" * 56)

    db = mz.load_event_db()
    if db:
        events = mz.today_from_db(db, today_str)
        if events:
            events.sort(key=lambda x: float(x["Score"]), reverse=True)
            for e in events:
                lvl = e["Level"]
                disp = lvl
                if lvl == "PEAK": disp = red(lvl)
                elif lvl == "VERY HIGH": disp = yellow(lvl)
                elif lvl == "HIGH": disp = green(lvl)
                print(f"\n  {bold(f'[{disp}]')} {e['Transit']}  |  House H{e['House']}  |  Score: {e['Score']}")
                print(f"  Aspect: {e['Aspect']}")
                print(f"  Strategy: {e['Meaning']}")
                print(f"  Actions: {e['Actions'][:100]}")
                print(f"  {bold('T-Rex 2:')}")
                print(f'  "{mz.t_rex_memo(e["Transit"].split("->")[0].strip() if "->" in e["Transit"] else "Planet", e["Transit"].split("->")[1].strip() if "->" in e["Transit"] else "chart", e["House"], e["Meaning"], e["Date"])}"')
        else:
            print(f"\n  No high-impact events in database for today.\n")

    # Also show real-time
    print(f"\n  {bold('Real-time Check:')}")
    cmd_now()

def cmd_week():
    th = load_thresholds()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    today_str = now.strftime("%Y-%m-%d")

    db = mz.load_event_db()
    if not db:
        print("No database found. Run this from the project directory.")
        return

    print(f"\n{bold('MAZZAROTH 7-DAY FORECAST')} — {today_str}")
    print("=" * 56)

    week_events = mz.week_from_db(db, today_str)
    if not week_events:
        print("\n  No high-impact events in the next 7 days.\n")
        return

    week_events.sort(key=lambda x: (x["Date"], -float(x["Score"])))
    current_date = ""
    for e in week_events:
        if e["Date"] != current_date:
            current_date = e["Date"]
            dt = datetime.strptime(current_date, "%Y-%m-%d")
            day_name = dt.strftime("%A")
            print(f"\n  {bold(day_name)} — {current_date}")
        lvl = e["Level"]
        disp = lvl
        if lvl == "PEAK": disp = red(lvl)
        elif lvl == "VERY HIGH": disp = yellow(lvl)
        elif lvl == "HIGH": disp = green(lvl)
        tname = e["Transit"].split("->")[0].strip() if "->" in e["Transit"] else ""
        print(f"    [{disp}] {e['Transit']:25} H{e['House']:2}  Score: {e['Score']:>7}  |  {e['Meaning'][:45]}")
    print()

def cmd_watch():
    th = load_thresholds()
    interval = 1800  # 30 min
    print(f"\n{bold('MAZZAROTH WATCH')} — Monitoring every {interval//60} min")
    print("=" * 56)
    print("  Press Ctrl+C to stop.\n")

    try:
        while True:
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            transit = mz.get_transit_data(now)
            score, hits = mz.score_transit(transit)
            level = mz.get_level(score, th)
            ts = now.strftime("%H:%M")

            if level == "PEAK":
                top = hits[0] if hits else ("", 0, "")
                mz.alert_peak(f"Score: {score:.0f} | {top[1]}")
            elif level == "VERY HIGH":
                print(f"  [{ts}] {yellow('VERY HIGH')} — Score: {score:.0f}")
            elif level == "HIGH":
                print(f"  [{ts}] {green('HIGH')} — Score: {score:.0f}")
            else:
                print(f"  [{ts}] Score: {score:.0f}", end="\r")

            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n  Watch stopped.\n")

def cmd_search(date_str):
    db = mz.load_event_db()
    if not db:
        print("No database found.")
        return
    events = mz.today_from_db(db, date_str)
    if not events:
        print(f"No events found for {date_str}.")
        return
    events.sort(key=lambda x: float(x["Score"]), reverse=True)
    print(f"\n{bold('Events for')} {date_str}:")
    print("=" * 56)
    for e in events:
        lvl = e["Level"]
        disp = lvl
        if lvl == "PEAK": disp = red(lvl)
        elif lvl == "VERY HIGH": disp = yellow(lvl)
        elif lvl == "HIGH": disp = green(lvl)
        print(f"  [{disp}] {e['Transit']:25} H{e['House']:2}  Score: {e['Score']:>7}")
        print(f"         {e['Aspect']}")
        print(f"         {e['Meaning'][:70]}")
        print()

def cmd_thresholds():
    th = load_thresholds()
    print(f"\n{bold('Thresholds')} (based on {th['n']} days):")
    print(f"  PEAK:      > {th['peak']:.0f}")
    print(f"  VERY HIGH: > {th['vhigh']:.0f}")
    print(f"  HIGH:      > {th['high']:.0f}")
    print()

def cmd_relationship():
    report = la.relationship_report()
    print(f"\n{'='*56}")
    print(f"  RELATIONSHIP & SEX TRANSITS")
    print(f"{'='*56}")
    for r in report:
        print(f"\n  [{r['area']}] H{r['house']}")
        print(f"  {r['transit']}  (orb {r['delta']:+})")
        print(f"  {r['interpretation']}")
    print()

def cmd_areas():
    report = la.life_areas_report()
    print(la.format_report(report, "ALL LIFE AREAS (sorted by intensity)"))
    for r in report:
        if r["level"] in ("PEAK", "VERY HIGH"):
            intel_map = {
                2: la.WEALTH_INTEL, 4: la.HOME_INTEL, 5: la.ROMANCE_INTEL,
                6: la.HEALTH_INTEL, 10: la.WEALTH_INTEL, 12: la.SPIRIT_INTEL
            }
            im = intel_map.get(r["house"])
            if im:
                first_aspect = r["aspects"][0].split(" ")[0] if r["aspects"] else ""
                key = (first_aspect, str(r["house"]))
                if key in im:
                    print(f"  >> {im[key]}")
    print()

def cmd_all_transits():
    rows = la.all_area_transits()
    print(f"\n{'='*56}")
    print(f"  ALL ACTIVE TRANSITS BY LIFE AREA")
    print(f"{'='*56}")
    cur_h = 0
    for r in rows:
        if r["house"] != cur_h:
            cur_h = r["house"]
            print(f"\n  H{cur_h}: {r['life_area']}")
        print(f"    {r['transit_planet']:10} {r['aspect']:4} {r['natal_planet']:10} (orb {r['orb']:+})")
    print()

def _scan_day(dt):
    """Compute transit events for a single day."""
    from datetime import time
    midday = datetime.combine(dt.date(), time(12, 0), tzinfo=timezone.utc).replace(tzinfo=None)
    transit = mz.get_transit_data(midday)
    thresh = load_thresholds() if os.path.exists(THRESH_CACHE) else {"peak": 3100, "vhigh": 2800, "high": 2400}
    events = []
    for tname, td in transit.items():
        tw = mz.WEIGHTS.get(tname, 1.0)
        tmm = td["motion_mult"]
        for nname, nd in mz.NATAL.items():
            h = mz._house_num(nd["lon"])
            nw = mz.WEIGHTS.get(nname, 1.0)
            hw = mz.HOUSE_WT.get(h, 1.0)
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in mz.ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    prec = 3.0 if delta < 0.1 else (2.0 if delta < 0.5 else 1.0)
                    s = base * tw * nw * hw * tmm * prec
                    interp, actions = mz.get_interpretation(tname, h)
                    lvl = mz.get_level(s, thresh)
                    events.append({
                        "Date": dt.strftime("%Y-%m-%d"),
                        "Transit": f"{tname} {aname} {nname}",
                        "House": str(h),
                        "Score": str(round(s, 1)),
                        "Level": lvl or "NORMAL",
                        "Meaning": interp,
                        "Aspect": f"{tname} {aname} {nname} H{h}",
                    })
    events.sort(key=lambda x: float(x["Score"]), reverse=True)
    return events

def cmd_month():
    """Scan next 30 days for significant transits."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    db = mz.load_event_db()
    print(f"\n{'='*56}")
    print(f"  30-DAY OUTLOOK: {now.strftime('%Y-%m-%d')} to {(now+timedelta(days=30)).strftime('%Y-%m-%d')}")
    print(f"{'='*56}")
    total_peak = 0
    total_vh = 0
    total_h = 0
    for i in range(31):
        d = (now + timedelta(days=i))
        ds = d.strftime("%Y-%m-%d")
        events = mz.today_from_db(db, ds) if db else []
        if not events:
            events = _scan_day(d)
        peak = [e for e in events if e.get("Level") == "PEAK"]
        vh = [e for e in events if e.get("Level") == "VERY HIGH"]
        if peak or vh:
            total_peak += len(peak)
            total_vh += len(vh)
            total_h += len([e for e in events if e.get("Level") == "HIGH"])
            print(f"\n  {ds}")
            if peak:
                parts = [f"{e['Transit']} H{e['House']} ({e['Score']})" for e in peak]
                print(f"    [PEAK] {' | '.join(parts)}")
            if vh:
                parts = [f"{e['Transit']} H{e['House']} ({e['Score']})" for e in vh]
                print(f"    [VERY HIGH] {' | '.join(parts)}")
    print(f"\n{'='*56}")
    print(f"  30-day summary: {total_peak} PEAK, {total_vh} VERY HIGH, {total_h} HIGH windows")
    print(f"{'='*56}\n")

def help():
    print(__doc__)
    print("  Life Areas:")
    print("    python mazz.py relationship  # Relationship & sex transits")
    print("    python mazz.py areas         # All life areas by intensity")
    print("    python mazz.py transits      # All transits mapped to life areas")
    print("    python mazz.py month         # 30-day transit outlook scan")
    print("  Production:")
    print("    python mazz.py brief         # Strategic Daily Brief (transit synthesis)")
    print("    python mazz.py wealth        # Wealth Optimizer - financial astrology")
    print("    python mazz.py wealth calendar  # Financial calendar 60 days")
    print("    python mazz.py wealth pattern   # Billionaire wealth blueprint")
    print("    python mazz.py wealth invest    # Investment timing analysis")
    print("    python mazz.py audit         # Ground Truth audit status")
    print("    python mazz.py audit rate N tag  # Rate today outcome (1-5)")
    print("    python mazz.py audit history     # Audit log")
    print("    python mazz.py audit regression  # Hit-rate regression analysis")
    print("    python mazz.py ics generate      # Regenerate ICS calendar")
    print("    python mazz.py ics deploy FOLDER # Deploy ICS to sync folder")
    print("    python mazz.py zepp status       # Zepp import history")
    print("    python mazz.py zepp run FILE     # Import Zepp CSV manually")
    print("  Optimization:")
    print("    python mazz.py optimize          # Bayesian weight optimization from audit log")
    print("  Flags:")
    print("    python mazz.py --user NAME ...   # Multi-subject routing (default: geraldkombo)")
    print()

if __name__ == "__main__":
    # Parse --user flag before command dispatch
    user_arg = "geraldkombo"
    filtered = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--user" and i + 1 < len(sys.argv):
            user_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i].startswith("--user="):
            user_arg = sys.argv[i].split("=", 1)[1]
            i += 1
        else:
            filtered.append(sys.argv[i])
            i += 1
    CURRENT_USER = user_arg
    CURRENT_USER_DIR = get_data_path(user_arg)

    # Rebuild sys.argv without the user flag for downstream dispatch
    sys.argv = [sys.argv[0]] + filtered

    if len(sys.argv) < 2:
        help()
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "now": cmd_now()
    elif cmd == "today": cmd_today()
    elif cmd == "week": cmd_week()
    elif cmd == "watch": cmd_watch()
    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python mazz.py search YYYY-MM-DD")
        else:
            cmd_search(sys.argv[2])
    elif cmd == "thresholds": cmd_thresholds()
    elif cmd == "relationship": cmd_relationship()
    elif cmd == "areas": cmd_areas()
    elif cmd == "transits": cmd_all_transits()
    elif cmd == "month": cmd_month()
    elif cmd == "brief":
        import transit_combiner
        transit_combiner.cmd_now()
    elif cmd == "wealth":
        import wealth_optimizer
        if len(sys.argv) < 3:
            wealth_optimizer.cmd_now()
        elif sys.argv[2] == "calendar":
            wealth_optimizer.cmd_calendar()
        elif sys.argv[2] == "pattern":
            wealth_optimizer.cmd_pattern()
        elif sys.argv[2] == "invest":
            wealth_optimizer.cmd_invest()
    elif cmd == "audit":
        import execution_audit
        execution_audit.record_todays_prediction()
        if len(sys.argv) < 3:
            execution_audit.cmd_status()
        elif sys.argv[2] == "rate":
            if len(sys.argv) < 5:
                print("Usage: python mazz.py audit rate 1-5 outcome_tag")
            else:
                execution_audit.cmd_rate(int(sys.argv[3]), " ".join(sys.argv[4:]))
        elif sys.argv[2] == "history":
            execution_audit.cmd_history()
        elif sys.argv[2] == "regression":
            execution_audit.cmd_regression()
    elif cmd == "ics":
        import ics_auto_deploy
        if len(sys.argv) < 3:
            ics_auto_deploy.cmd_status()
        elif sys.argv[2] == "generate":
            ics_auto_deploy.generate_ics()
        elif sys.argv[2] == "status":
            ics_auto_deploy.cmd_status()
        elif sys.argv[2] == "deploy" and len(sys.argv) >= 4:
            ics_auto_deploy.deploy(sys.argv[3])
    elif cmd == "zepp":
        import zepp_auto_sync
        if len(sys.argv) < 3:
            zepp_auto_sync.cmd_status()
        elif sys.argv[2] == "status":
            zepp_auto_sync.cmd_status()
        elif sys.argv[2] == "run" and len(sys.argv) >= 4:
            zepp_auto_sync.run_import(sys.argv[3])
    elif cmd == "optimize":
        import optimizer
        optimizer.run_optimization()
    elif cmd in ("help", "--help", "-h"): help()
    else:
        print(f"Unknown command: {cmd}")
        help()
