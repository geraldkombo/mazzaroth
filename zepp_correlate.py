#!/usr/bin/env python3
"""
Zepp <-> Mazzaroth Correlation
Merges your T-Rex 2 health export with transit scores to find alignment.

Usage:
    python zepp_correlate.py <zepp_csv_path>
"""

import sys, os, csv
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
PROJECT = os.path.dirname(__file__)
DATA_DIR = os.path.join(PROJECT, "Mazzaroth_Engine_Data")

HEADER_HELP = """
Expected Zepp CSV columns:
  - Date column (any format like 2026-06-12, 06/12/2026, etc.)
  - Recovery or readiness score column (0-100)
  - Stress score column (0-100)

If your columns have different names, edit the COLUMN_MAP dict below.
"""

COLUMN_MAP = {
    "date": ["Date", "date", "Day", "day", "Datetime", "timestamp", "Time"],
    "recovery": ["Recovery", "recovery", "Readiness", "readiness", "HRV", "hrv"],
    "stress": ["Stress", "stress", "Stress Level", "stress_level", "PAI", "pai"],
}

def find_column(headers, aliases):
    for h in headers:
        hs = h.strip().lower()
        for alias in aliases:
            if alias.lower() == hs:
                return h
    return None

def parse_date(val):
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y%m%d"]:
        try: return datetime.strptime(val.strip(), fmt)
        except: pass
    return None

def load_mazzaroth_data():
    path = os.path.join(DATA_DIR, "mazzaroth_master_log.csv")
    if not os.path.exists(path):
        path = os.path.join(PROJECT, "mazzaroth_master_log.csv")
    if not os.path.exists(path):
        print(f"  Warning: No master log found at {path}")
        return {}
    data = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data[row["Date"].strip()] = {
                "level": row.get("Level", ""),
                "score": float(row.get("Score", 0)),
                "transit": row.get("Transit", ""),
                "aspect": row.get("Aspect", ""),
            }
    print(f"  Loaded {len(data)} Mazzaroth transit days.")
    return data

def correlate(zepp_path):
    print(f"\n{'='*56}")
    print(f"  ZEPP ↔ MAZZAROTH CORRELATION")
    print(f"{'='*56}\n")

    # Load Mazzaroth data
    mazz_data = load_mazzaroth_data()

    # Read Zepp CSV
    with open(zepp_path, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
    
    date_col = find_column(headers, COLUMN_MAP["date"])
    rec_col = find_column(headers, COLUMN_MAP["recovery"])
    stress_col = find_column(headers, COLUMN_MAP["stress"])

    print(f"  Detected columns:")
    print(f"    Date:    {date_col or 'NOT FOUND'}")
    print(f"    Recovery:{rec_col or 'NOT FOUND'}")
    print(f"    Stress:  {stress_col or 'NOT FOUND'}")
    if not date_col:
        print(f"\n  {HEADER_HELP}")
        print(f"  Headers found: {headers}")
        return
    print()

    # Output
    out_path = os.path.join(DATA_DIR, "zepp_correlated.csv")
    rows = []
    matched = 0
    with open(zepp_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            dt = parse_date(row[date_col])
            if not dt: continue
            dstr = dt.strftime("%Y-%m-%d")
            rec = row.get(rec_col, "").strip() if rec_col else ""
            stress = row.get(stress_col, "").strip() if stress_col else ""
            mazz = mazz_data.get(dstr, {})
            rows.append({
                "Date": dstr,
                "Zepp_Recovery": rec,
                "Zepp_Stress": stress,
                "Mazz_Score": mazz.get("score", ""),
                "Mazz_Level": mazz.get("level", ""),
                "Mazz_Transit": mazz.get("transit", ""),
                "Alignment_Note": "",
            })
            if mazz: matched += 1

    # Score alignment
    float_rows = []
    for r in rows:
        try:
            sc = float(r["Mazz_Score"]) if r["Mazz_Score"] else 0
            rec = float(r["Zepp_Recovery"]) if r["Zepp_Recovery"] else 50
        except: sc, rec = 0, 50
        r["Score_Normalized"] = sc
        r["Recovery_Normalized"] = rec
        float_rows.append(r)

    # Correlation
    if len(float_rows) > 5:
        scores_n = [r["Score_Normalized"] for r in float_rows]
        rec_n = [r["Recovery_Normalized"] for r in float_rows]
        n = len(scores_n)
        mean_s = sum(scores_n) / n
        mean_r = sum(rec_n) / n
        var_s = sum((x - mean_s)**2 for x in scores_n) / n
        var_r = sum((x - mean_r)**2 for x in rec_n) / n
        if var_s > 0 and var_r > 0:
            cov = sum((scores_n[i] - mean_s) * (rec_n[i] - mean_r) for i in range(n)) / n
            corr = cov / ((var_s * var_r)**0.5)
        else:
            corr = 0
    else:
        corr = 0

    # Write output
    os.makedirs(DATA_DIR, exist_ok=True)
    out_cols = ["Date","Zepp_Recovery","Zepp_Stress","Mazz_Score","Mazz_Level","Mazz_Transit","Alignment_Note"]
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=out_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"  Written: {out_path} ({len(rows)} rows, {matched} matched to transit data)")
    print(f"  Correlation (Recovery vs Transit Score): {corr:+.3f}")
    if abs(corr) > 0.3:
        print(f"  {'STRONG' if abs(corr) > 0.6 else 'MODERATE'} alignment detected.")
    else:
        print(f"  Weak or no linear alignment. Check the CSV for specific date matches.")
    print()

    # Quick stats: average recovery on PEAK vs non-PEAK days
    peak_recs = [r["Recovery_Normalized"] for r in float_rows if r["Mazz_Level"] == "PEAK" and r["Recovery_Normalized"] > 0]
    non_peak_recs = [r["Recovery_Normalized"] for r in float_rows if r["Mazz_Level"] != "PEAK" and r["Recovery_Normalized"] > 0]
    if peak_recs and non_peak_recs:
        avg_peak = sum(peak_recs) / len(peak_recs)
        avg_non = sum(non_peak_recs) / len(non_peak_recs)
        print(f"  Avg Recovery on PEAK days:     {avg_peak:.1f}")
        print(f"  Avg Recovery on non-PEAK days: {avg_non:.1f}")
        print(f"  Difference: {avg_peak - avg_non:+.1f} points")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    correlate(sys.argv[1])
