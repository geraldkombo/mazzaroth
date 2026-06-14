"""
Generate JSON data files for the dynamic daily readings page.
Creates docs/data/today_hourly.json and docs/data/database.json
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
from datetime import datetime, timedelta, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "docs", "data")
os.makedirs(DATA_DIR, exist_ok=True)

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
    hourly.append({
        'hour': h,
        'time': dt.strftime('%H:%M'),
        'score': round(score, 1),
        'level': level,
        'top_transit': top_hit[1] if top_hit else '',
        'top_score': round(top_hit[0], 1) if top_hit else 0,
        'hit_count': len(hits),
    })

with open(os.path.join(DATA_DIR, 'today_hourly.json'), 'w') as f:
    json.dump({'date': today.strftime('%Y-%m-%d'), 'hourly': hourly}, f, indent=2)
print(f"Hourly data: {len(hourly)} hours written")

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

with open(os.path.join(DATA_DIR, 'database.json'), 'w') as f:
    json.dump(database_json, f, indent=2)
print(f"Database: {len(database_json)} days written")

# === Wealth data for today ===
import wealth_optimizer
ws = wealth_optimizer.wealth_score()
ws_val = ws[0] if isinstance(ws, (list, tuple)) else ws
wo_data = {'score': round(float(ws_val), 1), 'patterns': 7, 'verdict': 'FAVORABLE',
           'natal': ['Mercury-H3 Deal Maker', 'Venus-Jupiter Amplifier', 'Mars-H2 Money Warrior']}
with open(os.path.join(DATA_DIR, 'wealth.json'), 'w') as f:
    json.dump(wo_data, f, indent=2)
print("Wealth data written")

# === Life areas for today ===
import mazzaroth_life_areas as la
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
with open(os.path.join(DATA_DIR, 'areas.json'), 'w') as f:
    json.dump(areas_data, f, indent=2)
print(f"Life areas: {len(areas_data)} houses written")

# === Audit log entries ===
audit_path = os.path.join(os.path.dirname(__file__), 'Mazzaroth_Engine_Data', 'execution_audit.csv')
audit_entries = []
if os.path.exists(audit_path):
    import csv
    with open(audit_path, encoding='utf-8-sig') as f:
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
with open(os.path.join(DATA_DIR, 'audit.json'), 'w') as f:
    json.dump(audit_entries, f, indent=2)
print(f"Audit: {len(audit_entries)} entries written")

print("\nAll data files generated in docs/data/")
