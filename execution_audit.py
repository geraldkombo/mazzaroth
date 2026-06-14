#!/usr/bin/env python3
"""
Execution Audit - Ground Truth Logging Layer.
Records user-reported outcomes for PEAK/VH/HIGH transit days and computes
hit-rate regression per planet, house, and aspect type.

Usage:
    python execution_audit.py status       # Show pending audits + stats
    python execution_audit.py rate 1-5 tag  # Rate a past PEAK day
    python execution_audit.py history      # Full audit log
    python execution_audit.py regression   # Hit-rate analysis
"""

import sys, os, csv, json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

AUDIT_DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")
AUDIT_LOG = os.path.join(AUDIT_DIR, "execution_audit.csv")
PREDICTIONS_LOG = os.path.join(AUDIT_DIR, "predictions_log.csv")
THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")

os.makedirs(AUDIT_DIR, exist_ok=True)

def _ensure_logs():
    if not os.path.exists(AUDIT_LOG):
        with open(AUDIT_LOG, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date","predicted_score","predicted_level","top_transit","house",
                        "outcome_score","outcome_tag","rated_at"])
    if not os.path.exists(PREDICTIONS_LOG):
        with open(PREDICTIONS_LOG, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date","predicted_score","predicted_level","top_transit","house","aspect"])

def _load_audit():
    _ensure_logs()
    rows = []
    with open(AUDIT_LOG, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def _load_predictions():
    _ensure_logs()
    rows = []
    with open(PREDICTIONS_LOG, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

def _save_predictions(rows):
    _ensure_logs()
    with open(PREDICTIONS_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","predicted_score","predicted_level","top_transit","house","aspect"])
        w.writeheader()
        w.writerows(rows)

def _save_audit(rows):
    _ensure_logs()
    with open(AUDIT_LOG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date","predicted_score","predicted_level","top_transit","house",
                                          "outcome_score","outcome_tag","rated_at"])
        w.writeheader()
        w.writerows(rows)

def record_todays_prediction():
    today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    predictions = _load_predictions()
    if any(r["date"] == today for r in predictions):
        return
    thresh = {"peak":3100,"vhigh":2800,"high":2400}
    if os.path.exists(THRESH_CACHE):
        with open(THRESH_CACHE) as f: thresh = json.load(f)
    transit = mz.get_transit_data(datetime.now(timezone.utc).replace(tzinfo=None))
    score, hits = mz.score_transit(transit)
    level = mz.get_level(score, thresh) or "NORMAL"
    top = hits[0][1] if hits else "None"
    top_split = top.split(" natal ")
    aspect = top_split[1] if len(top_split) > 1 else top
    predictions.append({
        "date": today, "predicted_score": str(round(score, 1)),
        "predicted_level": level, "top_transit": top,
        "house": str(mz._house_num(mz.NATAL.get("Sun", mz.NATAL["Sun"])["lon"])),
        "aspect": aspect,
    })
    _save_predictions(predictions)

def cmd_status():
    _ensure_logs()
    audit = _load_audit()
    predictions = _load_predictions()
    today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    rated_dates = {r["date"] for r in audit if r["outcome_score"]}
    pending = [p for p in predictions if p["date"] not in rated_dates and p["date"] <= today]
    hist = [a for a in audit if a["outcome_score"]]
    rated_count = len(hist)
    avg_score = sum(int(a["outcome_score"]) for a in hist) / rated_count if rated_count else 0
    hits = sum(1 for a in hist if int(a["outcome_score"]) >= 4)
    hit_rate = hits / rated_count * 100 if rated_count else 0

    print(f"\n{'='*56}")
    print(f"  EXECUTION AUDIT - STATUS")
    print(f"{'='*56}")
    print(f"  Total predictions logged:   {len(predictions)}")
    print(f"  Days rated:                 {rated_count}")
    print(f"  Pending review:             {len(pending)}")
    print(f"  Average outcome:            {avg_score:.2f}/5")
    print(f"  Hit rate (4-5):             {hit_rate:.1f}%")
    print(f"\n  Pending dates:")
    for p in pending[-10:]:
        print(f"    {p['date']} | {p['top_transit']:40} | Score: {p['predicted_score']}")
    if not pending:
        print(f"    (none - all rated)")
    print()

def cmd_rate(outcome, tag):
    today = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d")
    audit = _load_audit()
    existing = next((r for r in audit if r["date"] == today), None)
    if existing:
        if existing["outcome_score"]:
            print(f"  Today already rated: {existing['outcome_score']}/5 - {existing['outcome_tag']}")
            return
        existing["outcome_score"] = str(outcome)
        existing["outcome_tag"] = tag
        existing["rated_at"] = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M")
    else:
        predictions = _load_predictions()
        pred = next((p for p in predictions if p["date"] == today), {})
        audit.append({
            "date": today,
            "predicted_score": pred.get("predicted_score", ""),
            "predicted_level": pred.get("predicted_level", ""),
            "top_transit": pred.get("top_transit", ""),
            "house": pred.get("house", ""),
            "outcome_score": str(outcome),
            "outcome_tag": tag,
            "rated_at": datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M"),
        })
    _save_audit(audit)
    print(f"  Recorded: {today} -> {outcome}/5 ({tag})")

def cmd_history():
    audit = _load_audit()
    rated = [a for a in audit if a["outcome_score"]]
    print(f"\n{'='*56}")
    print(f"  AUDIT HISTORY ({len(rated)} rated)")
    print(f"{'='*56}")
    for r in sorted(rated, key=lambda x: x["date"], reverse=True)[:30]:
        c = ""
        s = int(r["outcome_score"])
        if s >= 4: c = "green"
        elif s <= 2: c = "red"
        print(f"  {r['date']} | {r['top_transit']:40} | {r['predicted_level']:10} | {r['outcome_score']}/5 {r['outcome_tag']}")
    print()

def cmd_regression():
    audit = _load_audit()
    rated = [a for a in audit if a["outcome_score"]]
    if not rated:
        print("\n  No audit data yet. Use 'python execution_audit.py rate 1-5 tag' after PEAK days.\n")
        return

    print(f"\n{'='*56}")
    print(f"  HIT RATE REGRESSION ANALYSIS")
    print(f"{'='*56}")

    # By planet
    planet_stats = {}
    for r in rated:
        transit = r.get("top_transit", "").split(" ")[0]
        s = int(r["outcome_score"])
        if transit not in planet_stats:
            planet_stats[transit] = {"n":0, "total":0, "hits":0}
        planet_stats[transit]["n"] += 1
        planet_stats[transit]["total"] += s
        if s >= 4:
            planet_stats[transit]["hits"] += 1

    print(f"\n  By Transit Planet:")
    print(f"  {'Planet':12} {'N':>4} {'Avg':>6} {'Hit%':>6}")
    print(f"  {'-'*30}")
    for p in sorted(planet_stats, key=lambda x: planet_stats[x]["n"], reverse=True):
        s = planet_stats[p]
        avg = s["total"]/s["n"]
        hr = s["hits"]/s["n"]*100
        print(f"  {p:12} {s['n']:4} {avg:6.2f} {hr:5.0f}%")

    # Overall
    n = len(rated)
    total = sum(int(r["outcome_score"]) for r in rated)
    hits = sum(1 for r in rated if int(r["outcome_score"]) >= 4)
    misses = sum(1 for r in rated if int(r["outcome_score"]) <= 2)
    print(f"\n  Overall: {hits}/{n} hits ({hits/n*100:.0f}%), {misses} misses")
    print(f"  Mean outcome: {total/n:.2f}/5")

    # Threshold recommendation
    high_pred = [r for r in rated if r["predicted_level"] == "PEAK"]
    vh_pred = [r for r in rated if r["predicted_level"] == "VERY HIGH"]
    h_pred = [r for r in rated if r["predicted_level"] == "HIGH"]
    print(f"\n  By Predicted Level:")
    for label, group in [("PEAK", high_pred), ("VERY HIGH", vh_pred), ("HIGH", h_pred)]:
        if group:
            g_hits = sum(1 for r in group if int(r["outcome_score"]) >= 4)
            g_avg = sum(int(r["outcome_score"]) for r in group) / len(group)
            print(f"    {label:12} n={len(group):3} hits={g_hits:3} avg={g_avg:.2f}")
    print()

if __name__ == "__main__":
    record_todays_prediction()

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "rate":
        if len(sys.argv) < 4:
            print("Usage: python execution_audit.py rate 1-5 outcome_tag")
            sys.exit(1)
        try:
            outcome = int(sys.argv[2])
            if outcome < 1 or outcome > 5:
                raise ValueError
        except ValueError:
            print("Outcome must be 1-5")
            sys.exit(1)
        tag = " ".join(sys.argv[3:])
        cmd_rate(outcome, tag)
    elif cmd == "history":
        cmd_history()
    elif cmd == "regression":
        cmd_regression()
    else:
        print(__doc__)
