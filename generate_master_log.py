"""Sweep transits over a date range and write master_log.csv (HIGH+)."""
import sys, os, csv
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

OUT = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data", "mazzaroth_master_log.csv")
START = datetime(2026, 3, 17)
END   = datetime(2036, 12, 31)
TH = mz.load_thresholds()

mz._ensure_loaded()
rows = []
d = START
today_s = datetime.utcnow().strftime("%Y-%m-%d")
n_total = (END-START).days + 1
i = 0
while d <= END:
    td = mz.get_transit_data(d.replace(hour=12))
    score, hits = mz.score_transit(td)
    level = mz.get_level(score, TH)
    if level and hits:
        top = hits[0]
        # top = (score, "Tname Asp natal Nname (delta)", aspect_code)
        label = top[1]
        # Extract Tname, Nname
        try:
            tname = label.split()[0]
            nname = label.split("natal ")[1].split()[0].rstrip(",")
        except Exception:
            tname, nname = "?", "?"
        # House of natal target
        try:
            house = mz._house_num(mz.NATAL[nname]["lon"])
        except Exception:
            house = ""
        transit_pair = f"{tname}->{nname}"
        date_s = d.strftime("%Y-%m-%d")
        meaning = mz.get_interpretation(tname, house)
        rows.append({
            "Date": date_s, "Level": level, "Transit": transit_pair,
            "House": house, "Profection": str(mz.PROF_HOUSE),
            "Score": f"{score:.1f}", "Aspect": top[2],
            "Meaning": meaning, "Actions": "",
            "Status": "Upcoming" if date_s >= today_s else "Passed",
        })
    i += 1
    if i % 365 == 0:
        print(f"  {i}/{n_total} days processed, {len(rows)} events kept")
    d += timedelta(days=1)

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["Date","Level","Transit","House","Profection","Score","Aspect","Meaning","Actions","Status"])
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"Wrote {len(rows)} events to {OUT}")
