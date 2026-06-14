#!/usr/bin/env python3
"""
T-Rex 2 Watch Sync - Formats Mazzaroth data for the T-Rex 2 via Zepp app.

Usage:
    python trex2_sync.py today      Daily briefing (copy to Zepp Memo)
    python trex2_sync.py week       Next 7 days summary
    python trex2_sync.py ics        Instructions to sync ICS to watch calendar
    python trex2_sync.py alarms     Generate phone calendar alerts for PEAK days
"""

import sys, os, csv, json
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))
DATA_DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")

def load_db():
    path = os.path.join(DATA_DIR, "mazzaroth_master_log.csv")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "mazzaroth_master_log.csv")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def fmt_t2(text, max_len=80):
    return text[:max_len] + "..." if len(text) > max_len else text

def cmd_today():
    db = load_db()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    print("=" * 42)
    print("  T-REX 2 DAILY BRIEFING")
    print(f"  {today}")
    print("=" * 42)
    
    # From database
    if db:
        todays = [e for e in db if e["Date"] == today]
        if todays:
            todays.sort(key=lambda x: float(x["Score"]), reverse=True)
            for e in todays:
                print(f"\n  [{e['Level']}] {e['Transit']} H{e['House']}")
                print(f"  {e['Meaning'][:65]}")
    
    print(f"\n  {'-' * 42}")
    print(f"  Copy this to Zepp App -> Agenda:")
    print(f"  {'-' * 42}")
    
    if db and todays:
        e = todays[0]
        lines = [
            f"MAZZAROTH | {e['Level']}",
            f"{e['Transit']} H{e['House']} Score:{e['Score']}",
            f"{e['Meaning'][:60]}",
        ]
    else:
        try:
            import mazzaroth as mz
            transit = mz.get_transit_data(now)
            score, hits = mz.score_transit(transit)
            top = hits[0][1] if hits else "No major aspects"
            tname = top.split(" ")[0] if hits else ""
            nd = mz.NATAL.get("Sun")
            h = mz._house_num(nd["lon"]) if nd else 11
            interp, _ = mz.get_interpretation(tname if tname else "Sun", h)
            lines = [
                f"MAZZAROTH | {'PEAK' if score > 3100 else 'ACTIVE'}",
                f"Score:{score:.0f} H{h} | {top[:35] if hits else 'No aspects'}",
                f"{interp[:60]}",
            ]
        except:
            lines = ["MAZZAROTH", "Run: python mazz.py now", "For live transit data"]

    for l in lines:
        print(f"  {l}")
    print()

def cmd_week():
    db = load_db()
    if not db:
        print("No database found.")
        return
    
    now = datetime.now()
    print("=" * 42)
    print("  T-REX 2 | WEEK AHEAD")
    print(f"  {now.strftime('%Y-%m-%d')} +7 days")
    print("=" * 42)
    
    week_events = []
    for i in range(7):
        d = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_events = [e for e in db if e["Date"] == d]
        week_events.extend(day_events)
    
    if not week_events:
        print("\n  No high-impact events this week.\n")
        return
    
    week_events.sort(key=lambda x: (x["Date"], -float(x["Score"])))
    cur_date = ""
    for e in week_events:
        if e["Date"] != cur_date:
            cur_date = e["Date"]
            dt = datetime.strptime(cur_date, "%Y-%m-%d")
            print(f"\n  {dt.strftime('%a %b %d')}")
        print(f"  [{e['Level'][0]}] {fmt_t2(e['Transit'], 30):30} H{e['House']} {e['Score']:>5}")

    print(f"\n  To add to watch: Zepp App > Profile > Agenda > +")

def cmd_ics():
    print("=" * 42)
    print("  SYNC ICS TO T-REX 2")
    print("=" * 42)
    print("""
  1. Transfer mazzaroth_exact.ics to your phone

  2a. iPhone (Apple Calendar):
      AirDrop or email the .ics to yourself.
      Open -> "Add to Calendar" -> Save.

  2b. Android (Google Calendar):
      Upload .ics to Google Drive.
      Open in Drive -> "Open with" -> Calendar.

  3. Open Zepp App on your phone.

  4. Go to Profile -> App permissions ->
     Enable "Calendar" sync.

  5. The T-Rex 2 will sync events automatically
     when connected via Bluetooth.

  6. To see events on watch:
     Swipe up -> Agenda app.
     Or set watch face with calendar complications.

  NOTE: Sync can take 1-5 minutes. Force sync
  by pulling down in Zepp App > Home > sync icon.
""")

def cmd_alarms():
    db = load_db()
    if not db:
        print("No database found.")
        return

    peaks = [e for e in db if e["Level"] == "PEAK"]
    highs = [e for e in db if e["Level"] in ("VERY HIGH", "HIGH")]
    
    print("=" * 42)
    print("  PEAK DAYS - Add to Zepp Reminders")
    print("=" * 42)
    print(f"\n  {len(peaks)} PEAK days in database.")
    print(f"  {len(highs)} HIGH/VERY HIGH days.\n")
    print("  To add a reminder in Zepp App:")
    print("  1. Profile > Reminders")
    print("  2. Add reminder > Select date & time")
    print("  3. Paste memo from below\n")
    
    # Show next 10 PEAK days
    today = datetime.now().strftime("%Y-%m-%d")
    upcoming = sorted([e for e in peaks if e["Date"] >= today], key=lambda x: x["Date"])[:10]
    
    if upcoming:
        for e in upcoming:
            memo = f"PEAK {e['Transit']} H{e['House']} | {e['Meaning'][:50]}"
            print(f"  {e['Date']}")
            print(f"    {memo}")
            print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "today": cmd_today()
    elif cmd == "week": cmd_week()
    elif cmd == "ics": cmd_ics()
    elif cmd == "alarms": cmd_alarms()
    else: print(f"Unknown: {cmd}\n{__doc__}")

