"""Build leverage + zepp CSVs from master_log.csv (does not require ICS parsing)."""
import csv, os
DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")
master = os.path.join(DIR, "mazzaroth_master_log.csv")
leverage = os.path.join(DIR, "high_leverage_windows.csv")
zepp = os.path.join(DIR, "zepp_mazzaroth_correlation_template.csv")
with open(master, encoding="utf-8-sig") as f:
    events = list(csv.DictReader(f))
print(f"Loaded {len(events)} events")
scores = sorted(float(e["Score"]) for e in events)
thr = scores[int(len(scores)*0.95)]
peaks = [e for e in events if float(e["Score"]) >= thr]
peaks.sort(key=lambda e: float(e["Score"]), reverse=True)
with open(leverage, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Score","Date","Level","Transit","House","Profection","Aspect","Meaning","Actions","Status","T-Rex2_Memo"])
    for e in peaks:
        memo = f"PEAK {e['Date'][5:]} | {e['Transit']} H{e['House']} | {e['Meaning'][:55]}"
        w.writerow([e["Score"],e["Date"],e["Level"],e["Transit"],e["House"],e["Profection"],
                    e["Aspect"],e["Meaning"],e["Actions"],e["Status"],memo])
with open(zepp, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Date","Zepp_Recovery_Score_(0-100)","Zepp_Stress_Score_(0-100)","Mazzaroth_Transit_Intensity_(Score)","Mazzaroth_Level","Mazzaroth_Transit_Pair","Notes"])
    for e in events:
        w.writerow([e["Date"],"","",e["Score"],e["Level"],e["Transit"],""])
print(f"Wrote {len(peaks)} leverage windows, {len(events)} zepp rows.")
