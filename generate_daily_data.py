"""
Generate JSON data files for the dynamic daily readings page.
Creates docs/data/today_hourly.json and docs/data/database.json
"""
import sys, os, json, logging
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
from datetime import datetime, timedelta, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "docs" / "data"
EPHE_PATH = BASE_DIR / "ephe" / "de421.bsp"
DATA_DIR.mkdir(parents=True, exist_ok=True)

if not EPHE_PATH.exists():
    logging.error("Ephemeris file not found at %s", EPHE_PATH)
    logging.info("Downloading...")
    from skyfield.api import load
    load(str(EPHE_PATH))
    logging.info("Downloaded.")

# === Natal chart data for all pages ===
def compute_natal_chart():
    planets = []
    for name, nd in mz.NATAL.items():
        lon = nd["lon"]
        const = mz._constellation(lon)
        house = mz._house_num(lon)
        planets.append({
            "name": name,
            "lon": round(lon, 2),
            "lat": round(nd.get("lat", 0), 2),
            "decl": round(nd.get("decl", 0), 2),
            "constellation": const,
            "house": house,
            "speed": round(mz.MEAN_SPD.get(name, 0), 4),
        })
    aspects = []
    for i, p1 in enumerate(planets):
        for j, p2 in enumerate(planets):
            if j <= i: continue
            diff = abs(p1["lon"] - p2["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in mz.ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    aspects.append({
                        "p1": p1["name"], "p2": p2["name"],
                        "aspect": aname, "orb": round(delta, 2),
                    })
                    break
    houses = {}
    for p in planets:
        hk = str(p["house"])
        if hk not in houses: houses[hk] = []
        houses[hk].append(p["name"])
    sorted_houses = {}
    for k in sorted(houses.keys(), key=int):
        sorted_houses[k] = houses[k]
    return {"planets": planets, "aspects": aspects, "houses": sorted_houses}

natal_chart = compute_natal_chart()
logging.info("Natal chart: %d planets, %d aspects, %d houses occupied",
             len(natal_chart["planets"]), len(natal_chart["aspects"]), len(natal_chart["houses"]))

# === Hourly data for today ===
now = datetime.now(timezone.utc).replace(tzinfo=None)
today = now.replace(hour=0, minute=0, second=0, microsecond=0)
thresh = {'peak': 3100, 'vhigh': 2800, 'high': 2400}

hourly = []
for h in range(24):
    dt = today + timedelta(hours=h)
    transit = mz.get_transit_data(dt)
    score, hits = mz.score_transit(transit)
    level = mz.get_level(score, thresh) or 'NORMAL'
    top_hit = hits[0] if hits else None
    retro_planets = [name for name, td in transit.items() if td.get('retrograde')]
    hourly.append({
        'hour': h,
        'time': dt.strftime('%H:%M'),
        'score': round(score, 1),
        'level': level,
        'top_transit': top_hit[1] if top_hit else '',
        'top_score': round(top_hit[0], 1) if top_hit else 0,
        'hit_count': len(hits),
        'retrograde_planets': retro_planets,
    })

with open(DATA_DIR / 'today_hourly.json', 'w') as f:
    json.dump({'date': today.strftime('%Y-%m-%d'), 'hourly': hourly}, f, indent=2)
logging.info("Hourly data: %d hours written (retrogrades included)", len(hourly))

# === Daily database ===
db = mz.load_event_db()
daily = {}
for e in db:
    d = e['Date']
    if d not in daily:
        daily[d] = []
    daily[d].append({
        'transit': e['Transit'],
        'house': e['House'],
        'score': round(float(e['Score']), 1),
        'level': e['Level'],
        'aspect': e.get('Aspect', ''),
        'meaning': e.get('Meaning', '')[:80],
    })

# Also add all dates from hourly data
for h in hourly:
    d = today.strftime('%Y-%m-%d')
    if d not in daily:
        daily[d] = []

database_json = []
for date in sorted(daily.keys(), reverse=True):
    events = sorted(daily[date], key=lambda x: -x['score'])
    max_score = max(e['score'] for e in events) if events else 0
    levels = set(e['level'] for e in events)
    database_json.append({
        'date': date,
        'max_score': max_score,
        'max_level': max(levels, key=lambda l: ['NORMAL','HIGH','VERY HIGH','PEAK'].index(l)) if levels else 'NORMAL',
        'event_count': len(events),
        'events': events[:5],
    })

with open(DATA_DIR / 'database.json', 'w') as f:
    json.dump(database_json, f, indent=2)
logging.info("Database: %d days written", len(database_json))

# === Wealth data for today ===
import wealth_optimizer
try:
    ws = wealth_optimizer.wealth_score()
    ws_val = ws[0] if isinstance(ws, (list, tuple)) else ws
    wo_data = {'score': round(float(ws_val), 1), 'patterns': 7, 'verdict': 'FAVORABLE',
               'natal': ['Mercury-H3 Deal Maker', 'Venus-Jupiter Amplifier', 'Mars-H2 Money Warrior']}
except Exception as e:
    logging.error("Wealth score failed: %s", e)
    wo_data = {'score': 0, 'patterns': 0, 'verdict': 'UNAVAILABLE', 'natal': []}
with open(DATA_DIR / 'wealth.json', 'w') as f:
    json.dump(wo_data, f, indent=2)
logging.info("Wealth data written")

# === Life areas for today ===
import mazzaroth_life_areas as la
try:
    report = la.life_areas_report()
    areas_data = []
    for r in report:
        areas_data.append({
            'house': r['house'],
            'name': r['name'],
            'score': r['score'],
            'level': r['level'],
            'aspects': r['aspects'],
        })
except Exception as e:
    logging.error("Life areas failed: %s", e)
    areas_data = []
with open(DATA_DIR / 'areas.json', 'w') as f:
    json.dump(areas_data, f, indent=2)
logging.info("Life areas: %d houses written", len(areas_data))

# === Audit log entries ===
audit_path = BASE_DIR / 'Mazzaroth_Engine_Data' / 'execution_audit.csv'
audit_entries = []
if audit_path.exists():
    import csv
    with open(str(audit_path), encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get('outcome_score'):
                audit_entries.append({
                    'date': r['date'],
                    'score': r['predicted_score'],
                    'level': r['predicted_level'],
                    'transit': r['top_transit'],
                    'outcome': r['outcome_score'],
                    'tag': r.get('outcome_tag', ''),
                })
with open(DATA_DIR / 'audit.json', 'w') as f:
    json.dump(audit_entries, f, indent=2)
logging.info("Audit: %d entries written", len(audit_entries))

# === Combine all data into daily.js (single-line for fast loading) ===
combined = {
    "today_hourly": {
        "date": today.strftime('%Y-%m-%d'),
        "hourly": hourly,
    },
    "database": database_json,
    "wealth": wo_data,
    "areas": areas_data,
    "audit": audit_entries,
    "natal": natal_chart,
}
js_path = DATA_DIR / 'daily.js'
with open(js_path, 'w') as f:
    f.write("window.MD=" + json.dumps(combined, separators=(',',':')))
logging.info("daily.js written (%.1f KB) with natal data", os.path.getsize(js_path) / 1024)

logging.info("All data files generated in docs/data/")
