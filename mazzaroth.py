"""
Mazzaroth Engine v3 — Core Module
JPL DE421 ephemeris via Skyfield. No compilation required.
"""

from skyfield.api import load
from datetime import datetime, timedelta, timezone
import math, json, os, csv

# === BOOTSTRAP ===
_ts = None
_planets = None
_earth = None
_ephe_path = os.path.join(os.path.dirname(__file__), "ephe", "de421.bsp")

def _ensure_loaded():
    global _ts, _planets, _earth
    if _ts is None:
        _ts = load.timescale(builtin=True)
        _planets = load(_ephe_path)
        _earth = _planets["earth"]

# === NATAL CHART (Gerald Kombo, 1989-09-13 03:50 UTC, Nairobi) ===
NATAL = {
    "Sun":    {"lon": 170.4843, "lat":  0.0000, "decl":  3.7704},
    "Moon":   {"lon": 318.5855, "lat": -0.6646, "decl":-15.8878},
    "Mercury":{"lon": 190.6142, "lat": -4.0613, "decl": -7.9358},
    "Venus":  {"lon": 210.8920, "lat": -0.7001, "decl":-12.4403},
    "Mars":   {"lon": 175.9804, "lat":  0.8870, "decl":  2.4119},
    "Jupiter":{"lon":  97.7781, "lat": -0.2931, "decl": 22.9183},
    "Saturn": {"lon": 277.4451, "lat":  0.4797, "decl":-22.7511},
    "Uranus": {"lon": 271.4826, "lat": -0.2721, "decl":-23.7031},
    "Neptune":{"lon": 279.7679, "lat":  0.9015, "decl":-22.1805},
    "Pluto":  {"lon": 223.2569, "lat": 15.3646, "decl": -1.1315},
    "N.Node": {"lon": 324.4188, "lat":  0.0000, "decl":  0.0000},
    "Chiron": {"lon":  57.2745, "lat": -2.9884, "decl":  0.0000},
}

# === CONSTANTS ===
WEIGHTS = {"Pluto":4.0,"Neptune":3.5,"Uranus":3.0,"Saturn":2.5,"Jupiter":2.0,
           "N.Node":1.8,"Chiron":1.5,"Mars":1.5,"Sun":1.5,"Mercury":1.2,
           "Venus":1.2,"Moon":1.0}
MEAN_SPD = {"Sun":0.9856,"Moon":13.176,"Mercury":1.383,"Venus":1.200,
            "Mars":0.524,"Jupiter":0.083,"Saturn":0.034,"Uranus":0.012,
            "Neptune":0.006,"Pluto":0.004,"N.Node":0.053,"Chiron":0.019}
ASPECTS = [(0,8,10,"Conj"),(180,8,8,"Opp"),(90,7,7,"Sq"),(120,7,6,"Tri"),
           (60,5,4,"Sxt"),(150,3,3,"Qnx"),(45,2,2,"SSq"),(135,2,2,"SqSq"),
           (72,2,2,"Qnt"),(144,2,2,"BQnt")]
HOUSE_WT = {1:2.0,4:2.0,7:2.0,10:2.0,2:1.5,5:1.5,8:1.5,11:1.5,
            3:1.0,6:1.0,9:1.0,12:1.0,13:1.0}
PROF_HOUSE = ((36 % 13) + 1)  # Age 36 => H11

IAU = [(0.0,27.0,"Pisces"),(27.0,53.5,"Aries"),(53.5,90.4,"Taurus"),
       (90.4,118.1,"Gemini"),(118.1,138.2,"Cancer"),(138.2,174.0,"Leo"),
       (174.0,218.0,"Virgo"),(218.0,241.0,"Libra"),(241.0,248.0,"Scorpius"),
       (248.0,266.5,"Ophiuchus"),(266.5,300.0,"Sagittarius"),
       (300.0,327.5,"Capricornus"),(327.5,360.0,"Aquarius")]
CONST_ORDER = ["Pisces","Aries","Taurus","Gemini","Cancer","Leo","Virgo",
               "Libra","Scorpius","Ophiuchus","Sagittarius","Capricornus","Aquarius"]

INTEL_MAP = {
    ("Pluto","11"):("Network restructuring. Power connections.",["Cut shallow connections","Reach out to 5 key people","Join mission-aligned community"]),
    ("Saturn","11"):("Network pruning. Quality over quantity.",["Cut shallow connections","Invest in 3 key relationships","Build tight inner circle"]),
    ("Mercury","11"):("Ideas spread through network. Publish.",["Write something bold","Send the pitch deck","Start community conversation"]),
    ("Pluto","1"):("Identity rebuilt. Step into new version.",["Rebrand yourself","Make bold public declaration","Cut what no longer fits"]),
    ("Pluto","12"):("Build in silence. Strategy retreat.",["Deep strategy work","Research major project","Rest and integrate"]),
    ("Neptune","1"):("Visionary identity. Lead with story.",["Articulate long-term vision","Lead with story not data","Explore new creative identity"]),
    ("Uranus","4"):("Home base restructuring.",["Restructure workspace","Make bold operational change","Resolve foundational issues"]),
    ("Saturn","6"):("Work discipline crystallising.",["Build non-negotiable routine","Document processes","Create accountability"]),
    ("Jupiter","10"):("Career explosion window.",["Apply for big opportunity","Step into public leadership","Make bold career announcement"]),
    ("Pluto","8"):("Deep pivot. Transformational decisions.",["Apply for funding","Major investment decision","Pursue merger"]),
    ("Pluto","4"):("Foundation-building for decades.",["Secure base systems","Build infrastructure","Address instability"]),
}
FALLBACK_INTEL = ("Bold decisions now.", ["Make the major move","Act on what you delayed","Build something that lasts"])

def _constellation(lon):
    lon = lon % 360
    for s, e, n in IAU:
        if s <= lon < e: return n
    return "Pisces"

def _house_num(planet_lon):
    natal_sun_lon = NATAL["Sun"]["lon"]
    pc = _constellation(planet_lon)
    sc = _constellation(natal_sun_lon)
    return ((CONST_ORDER.index(pc) - CONST_ORDER.index(sc)) % 13) + 1

def _antiscion(lon):
    return (180 - lon) % 360 if lon <= 180 else (540 - lon) % 360

# === TRANSIT COMPUTATION ===
SKY_BODIES = {
    "Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
    "Mars": "mars", "Jupiter": "jupiter barycenter", "Saturn": "saturn barycenter",
    "Uranus": "uranus barycenter", "Neptune": "neptune barycenter", "Pluto": "pluto barycenter",
}

def _lunar_node_lon(t_date):
    j2000 = datetime(2000, 1, 1, 12, 0)
    d = (t_date - j2000).total_seconds() / 86400.0
    return (125.0445550 - 0.052992095 * d) % 360.0

def _chiron_geocentric(t, jd):
    CHIRON_EPOCH_JD = 2460800.5
    CHIRON_A = 13.6660147; CHIRON_E = 0.3815424
    CHIRON_I = math.radians(6.93688); CHIRON_OMEGA = math.radians(209.26032)
    CHIRON_W = math.radians(339.51752); CHIRON_M0 = math.radians(157.64918)
    CHIRON_N = 0.01951712
    d = jd - CHIRON_EPOCH_JD
    M = (CHIRON_M0 + math.radians(CHIRON_N * d)) % (2 * math.pi)
    E = M
    for _ in range(100):
        dE = (M - E + CHIRON_E * math.sin(E)) / (1 - CHIRON_E * math.cos(E))
        E += dE
        if abs(dE) < 1e-10: break
    xp = CHIRON_A * (math.cos(E) - CHIRON_E)
    yp = CHIRON_A * math.sqrt(1 - CHIRON_E**2) * math.sin(E)
    cw, sw = math.cos(CHIRON_W), math.sin(CHIRON_W)
    cO, sO = math.cos(CHIRON_OMEGA), math.sin(CHIRON_OMEGA)
    ci, si = math.cos(CHIRON_I), math.sin(CHIRON_I)
    x_ecl = xp*(cw*cO - sw*sO*ci) + yp*(-sw*cO - cw*sO*ci)
    y_ecl = xp*(cw*sO + sw*cO*ci) + yp*(-sw*sO + cw*cO*ci)
    z_ecl = xp*sw*si + yp*cw*si
    earth_bary = _planets["earth"].at(t).position.au
    sun_bary = _planets["sun"].at(t).position.au
    eh = earth_bary - sun_bary
    eps = math.radians(23.4392911)
    ex, ey = eh[0], eh[1]*math.cos(eps)+eh[2]*math.sin(eps)
    ez = -eh[1]*math.sin(eps)+eh[2]*math.cos(eps)
    gx, gy, gz = x_ecl-ex, y_ecl-ey, z_ecl-ez
    lon = math.degrees(math.atan2(gy, gx)) % 360
    lat = math.degrees(math.atan2(gz, math.sqrt(gx*gx+gy*gy)))
    return lon, lat

def get_transit_data(dt_utc):
    _ensure_loaded()
    t = _ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second)
    data = {}
    for name, sky_name in SKY_BODIES.items():
        try:
            app = _earth.at(t).observe(_planets[sky_name]).apparent()
            lat, lon, _ = app.ecliptic_latlon()
            _, dec, _ = app.radec()
            lon_deg = lon.degrees % 360
            t_next = _ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour+1, dt_utc.minute, dt_utc.second)
            lon_next = _earth.at(t_next).observe(_planets[sky_name]).apparent().ecliptic_latlon()[1].degrees % 360
            spd = lon_next - lon_deg
            if spd > 180: spd -= 360
            elif spd < -180: spd += 360
            spd_pct = abs(spd) / MEAN_SPD.get(name, 1)
            if spd_pct < 0.05: mm = 5.0
            elif spd_pct < 0.25: mm = 2.0
            else: mm = 1.0
            data[name] = {"lon":lon_deg, "lat":lat.degrees, "decl":dec.degrees, "spd":spd, "motion_mult":mm, "antiscion":_antiscion(lon_deg)}
        except: pass
    data["N.Node"] = {"lon":_lunar_node_lon(dt_utc), "lat":0.0, "decl":0.0, "spd":-0.053, "motion_mult":1.0, "antiscion":_antiscion(_lunar_node_lon(dt_utc))}
    try:
        jd = 2451545.0 + (dt_utc - datetime(2000,1,1,12,0)).total_seconds()/86400.0
        clon, clat = _chiron_geocentric(t, jd)
        data["Chiron"] = {"lon":clon, "lat":clat, "decl":0.0, "spd":MEAN_SPD["Chiron"], "motion_mult":1.0, "antiscion":_antiscion(clon)}
    except: pass
    return data

# === SCORING ===
def score_transit(transit_data):
    total = 0
    hits = []
    for tname, td in transit_data.items():
        tw = WEIGHTS.get(tname, 1.0)
        tmm = td["motion_mult"]
        for nname, nd in NATAL.items():
            nw = WEIGHTS.get(nname, 1.0)
            h = _house_num(nd["lon"])
            hw = HOUSE_WT.get(h, 1.0)
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    prec = 3.0 if delta<0.1 else (2.0 if delta<0.5 else 1.0)
                    s = base * tw * nw * hw * tmm * prec
                    total += s
                    hits.append((s, f"{tname} {aname} natal {nname} ({delta:.3f}deg)", aname))
            ddiff = abs(td["decl"] - nd["decl"])
            if ddiff <= 1.0:
                s = 6 * tw * nw * hw * tmm * (2.0 if ddiff<0.1 else 1.0)
                total += s
                hits.append((s, f"{tname} // natal {nname} decl ({ddiff:.3f}deg)", "PAR"))
            anti_diff = abs(td["lon"] - _antiscion(nd["lon"])) % 360
            if anti_diff > 180: anti_diff = 360 - anti_diff
            if anti_diff <= 1.5:
                s = 5 * tw * nw * hw * tmm
                total += s
                hits.append((s, f"{tname} anti-{nname} ({anti_diff:.3f}deg)", "ANTI"))
    hits.sort(reverse=True)
    return total, hits

def get_thresholds():
    _ensure_loaded()
    start = datetime(2026, 3, 17)
    end = datetime(2036, 12, 31)
    scores = []
    d = start
    while d <= end:
        td = get_transit_data(d.replace(hour=12))
        sc, _ = score_transit(td)
        scores.append(sc)
        d += timedelta(days=1)
    scores.sort()
    n = len(scores)
    return {
        "peak": scores[int(n*0.95)],
        "vhigh": scores[int(n*0.90)],
        "high": scores[int(n*0.75)],
        "n": n,
    }

def get_level(score, thresholds=None):
    if thresholds is None:
        thresholds = {"peak": 3100, "vhigh": 2800, "high": 2400}
    if score >= thresholds["peak"]: return "PEAK"
    if score >= thresholds["vhigh"]: return "VERY HIGH"
    if score >= thresholds["high"]: return "HIGH"
    return None

def get_interpretation(tname, house):
    key = (tname, str(house))
    if key in INTEL_MAP: return INTEL_MAP[key]
    for k, v in INTEL_MAP.items():
        if k[0] == tname: return v
    return FALLBACK_INTEL

def t_rex_memo(tname, nname, house, meaning, date_str):
    short = meaning[:55] if meaning else "Execute the move"
    return f"PEAK {date_str[5:]} | {tname}->{nname} H{house} | {short}"

# === ALERT ===
def alert_peak(event_summary):
    try:
        import subprocess, platform
        if platform.system() == "Windows":
            subprocess.run(["powershell", "-Command", "[System.Media.SystemSounds]::Exclamation.Play()"], capture_output=True)
        else:
            print("\a", end="", flush=True)
    except: pass
    bar = "!" * 50
    print(f"\n{bar}")
    print(f"  MAZZAROTH PEAK WINDOW ACTIVE")
    print(f"  {event_summary}")
    print(f"{bar}\n")

# === CSV DATABASE LOOKUP ===
def load_event_db(csv_path=None):
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data", "mazzaroth_master_log.csv")
    if not os.path.exists(csv_path):
        return None
    events = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)
    return events

def today_from_db(events, date_str):
    return [e for e in events if e["Date"] == date_str]

def week_from_db(events, start_date_str):
    results = []
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    for i in range(7):
        d = (start + timedelta(days=i)).strftime("%Y-%m-%d")
        results.extend([e for e in events if e["Date"] == d])
    return results
#!/usr/bin/env python3
"""
Mazzaroth CLI — Real-time transit scoring, alerts, and T-Rex 2 integration.

Usage:
    python mazz.py now          Current transit score + active aspects
    python mazz.py today        Full day briefing
    python mazz.py week         7-day forecast from today
    python mazz.py watch        Daemon mode (checks every 30 min)
    python mazz.py search DATE  Look up date in 10-year database (YYYY-MM-DD)
    python mazz.py thresholds   Compute and cache score thresholds
"""

import sys, os, time, json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")
COLOR = True
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

    print(f"\n{bold('MAZZAROTH')} — {now.strftime('%Y-%m-%d %H:%M UTC')}  |  Profection: H{mz.PROF_HOUSE}")
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

def help():
    print(__doc__)

if __name__ == "__main__":
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
    elif cmd in ("help", "--help", "-h"): help()
    else:
        print(f"Unknown command: {cmd}")
        help()
