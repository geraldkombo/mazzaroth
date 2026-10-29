"""
Generate JSON data files for the dynamic daily readings page.
Creates docs/data/today_hourly.json and docs/data/database.json
"""
import sys, os, json, logging
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
import mazzaroth_personal as pers
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
thresh = mz.load_thresholds()

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
        'personal': pers.personal_for_hour(top_hit[1] if top_hit else '', level, score),
    })

reading = pers.build_reading(hourly) or {}
logging.info("Personal reading built: %s", reading.get('headline', '')[:60])

with open(DATA_DIR / 'today_hourly.json', 'w') as f:
    json.dump({'date': today.strftime('%Y-%m-%d'), 'hourly': hourly}, f, indent=2)
logging.info("Hourly data: %d hours written (retrogrades included)", len(hourly))

# === Moon phase & agriculture timing ===
moon_phase = {}
try:
    mz._ensure_loaded()
    t = mz._ts.utc(now.year, now.month, now.day, 12)
    sun_lon = mz._earth.at(t).observe(mz._planets['sun']).apparent().ecliptic_latlon()[1].degrees % 360
    moon_lon = mz._earth.at(t).observe(mz._planets['moon']).apparent().ecliptic_latlon()[1].degrees % 360
    phase_angle = (moon_lon - sun_lon) % 360
    phases = [
        (22.5, 'New Moon', 'Plant leafy greens, start seeds. Prep soil.'),
        (67.5, 'Waxing Crescent', 'Plant above-ground crops. Good for transplanting.'),
        (112.5, 'First Quarter', 'Plant fruiting crops. Strong growth energy. Fertilize.'),
        (157.5, 'Waxing Gibbous', 'Prune, train vines. Good for grafting.'),
        (202.5, 'Full Moon', 'Harvest. Ripeness peaks. Good for picking and selling.'),
        (247.5, 'Waning Gibbous', 'Plant root crops. Good for weeding, composting.'),
        (292.5, 'Last Quarter', 'Prune, clear land. Build fences, infrastructure.'),
        (337.5, 'Waning Crescent', 'Rest soil. Weed, pest control. Avoid planting.'),
    ]
    for deg, name, advice in phases:
        if phase_angle <= deg:
            moon_phase = {'name': name, 'advice': advice, 'angle': round(phase_angle, 1)}
            break
    if not moon_phase:
        moon_phase = {'name': 'New Moon', 'advice': 'Plant leafy greens, start seeds. Prep soil.', 'angle': round(phase_angle, 1)}
    # Fiorenza lunar layers: sidereal mansion (nakshatra) + phase action guide.
    try:
        import mazzaroth_lunar as ml
        ay = ml.ayanamsa(now.year + (now.timetuple().tm_yday / 366.0))
        mansion = ml.lunar_mansion(moon_lon, ay=ay)
        guide = ml.phase_guide(phase_angle)
        moon_phase['sidereal'] = mansion['sidereal']
        moon_phase['ayanamsa'] = round(ay, 2)
        moon_phase['mansion'] = mansion
        moon_phase['guide'] = guide['guide']
        moon_phase['illumination'] = round(ml.illumination(phase_angle), 1)
    except Exception as le:
        logging.warning("Lunar mansion failed: %s", le)
    logging.info("Moon phase: %s (%.1f°)", moon_phase['name'], phase_angle)
except Exception as e:
    logging.warning("Moon phase failed: %s", e)
    moon_phase = {'name': '—', 'advice': 'Moon data unavailable.', 'angle': 0}

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

# === Wealth data for today (real engine output, personalized) ===
import wealth_optimizer
try:
    ws = wealth_optimizer.wealth_score()
    ws_val = ws[0] if isinstance(ws, (list, tuple)) else ws
    ws_factors = ws[1] if isinstance(ws, (list, tuple)) and len(ws) > 1 else []
    pat_names = [p['pattern'] for p in wealth_optimizer.billionaire_patterns()]
    verdicts = wealth_optimizer.investment_window()
    prio = {'AVOID': 0, 'WARNING': 1, 'HIGH IMPACT': 2, 'FAVORABLE': 3, 'NEUTRAL': 4}
    verdicts.sort(key=lambda v: prio.get(v[0], 5))
    verdict_txt = (verdicts[0][1] if verdicts and verdicts[0][0] != 'NEUTRAL'
                   else 'Neutral financial day. Build systems and execute.')
    natal_wp = wealth_optimizer.natal_wealth_profile()
    wo_data = {'score': round(float(ws_val), 1),
               'patterns': len(pat_names),
               'pattern_names': pat_names,
               'verdict': verdict_txt,
               'verdicts': [{'tag': v[0], 'note': v[1]} for v in verdicts[:3]],
               'factors': ws_factors[:6],
               'natal': natal_wp}
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

# === Personal blueprint (deterministic from natal + profection + today) ===
import mazzaroth_personal as pers
try:
    blueprint = pers.build_blueprint()
except Exception as e:
    logging.error("Blueprint failed: %s", e)
    blueprint = None
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
    "moon_phase": moon_phase,
    "database": database_json,
    "wealth": wo_data,
    "areas": areas_data,
    "audit": audit_entries,
    "natal": natal_chart,
    "thresholds": thresh,
    "reading": reading,
    "profection": {
        "house": mz.PROF_HOUSE,
        "age": mz._age_now(),
        "name": natal_chart["houses"].get(str(mz.PROF_HOUSE), []),
    },
    "blueprint": blueprint,
}
js_path = DATA_DIR / 'daily.js'
with open(js_path, 'w') as f:
    f.write("window.MD=" + json.dumps(combined, separators=(',',':')))
logging.info("daily.js written (%.1f KB) with natal data", os.path.getsize(js_path) / 1024)

logging.info("All data files generated in docs/data/")
