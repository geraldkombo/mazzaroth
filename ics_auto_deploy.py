#!/usr/bin/env python3
"""
ICS Auto Deploy - Automated ICS regeneration and watch-push.
Generates mazzaroth_exact.ics from the 10-year database and provides
options for deploying to calendar sync folders.

Usage:
    python ics_auto_deploy.py generate        # Regenerate ICS from DB
    python ics_auto_deploy.py deploy FOLDER   # Copy ICS to a sync folder
    python ics_auto_deploy.py status          # Show ICS file info
    python ics_auto_deploy.py watch           # Watch DB for changes, auto-regenerate
"""

import sys, os, csv, json, time, shutil
from datetime import datetime, timedelta, timezone

DATA_DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")
ICS_PATH = os.path.join(os.path.dirname(__file__), "mazzaroth_exact.ics")
DB_PATH = os.path.join(DATA_DIR, "mazzaroth_master_log.csv")

os.makedirs(DATA_DIR, exist_ok=True)

def generate_ics():
    if not os.path.exists(DB_PATH):
        print(f"  Database not found: {DB_PATH}")
        return False
    with open(DB_PATH, "r", encoding="utf-8-sig") as f:
        events = list(csv.DictReader(f))
    if not events:
        print("  Empty database.")
        return False

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Mazzaroth//v3//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Mazzaroth Transits",
        "X-WR-TIMEZONE:UTC",
    ]
    uid = 0
    for e in events:
        uid += 1
        dt = e.get("Date", "")
        level = e.get("Level", "NORMAL")
        transit = e.get("Transit", "")
        house = e.get("House", "")
        score = e.get("Score", "0")
        meaning = e.get("Meaning", "")

        # Color mapping
        color = "FF4444" if level == "PEAK" else "FF8800" if level == "VERY HIGH" else "44CC44" if level == "HIGH" else "888888"
        alarm_minutes = 60 if level == "PEAK" else 120 if level == "VERY HIGH" else 240

        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:mazzaroth-{uid:04d}@mazzaroth")
        lines.append(f"DTSTART;VALUE=DATE:{dt.replace('-','')}")
        lines.append(f"DTEND;VALUE=DATE:{(datetime.strptime(dt,'%Y-%m-%d')+timedelta(days=1)).strftime('%Y%m%d')}")
        lines.append(f"SUMMARY:[{level}] {transit}")
        lines.append(f"DESCRIPTION:Score: {score}\\nHouse: H{house}\\n{meaning[:200]}")
        lines.append(f"X-APPLE-CALENDAR-COLOR:#{color}")
        lines.append("BEGIN:VALARM")
        lines.append(f"TRIGGER:-PT{alarm_minutes}M")
        lines.append("ACTION:DISPLAY")
        lines.append(f"DESCRIPTION:Mazzaroth {level} alert")
        lines.append("END:VALARM")
        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")

    with open(ICS_PATH, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")

    print(f"  Generated: {ICS_PATH}")
    print(f"  Events: {len(events)}")
    return True

def deploy(folder):
    if not os.path.exists(ICS_PATH):
        print(f"  ICS not found. Run 'generate' first.")
        return
    if not os.path.exists(folder):
        print(f"  Target folder not found: {folder}")
        return
    dest = os.path.join(folder, "mazzaroth_exact.ics")
    shutil.copy2(ICS_PATH, dest)
    print(f"  Deployed to: {dest}")
    print(f"  Size: {os.path.getsize(dest)} bytes")

def cmd_status():
    print(f"\n{'='*56}")
    print(f"  ICS AUTO DEPLOY - STATUS")
    print(f"{'='*56}")
    if os.path.exists(ICS_PATH):
        size_kb = os.path.getsize(ICS_PATH) / 1024
        modified = datetime.fromtimestamp(os.path.getmtime(ICS_PATH))
        with open(ICS_PATH, "r", encoding="utf-8") as f:
            event_count = f.read().count("BEGIN:VEVENT")
        print(f"  ICS file:       {ICS_PATH}")
        print(f"  Size:           {size_kb:.1f} KB")
        print(f"  Events:         {event_count}")
        print(f"  Last modified:  {modified.strftime('%Y-%m-%d %H:%M')}")
    else:
        print(f"  No ICS file found.")
    if os.path.exists(DB_PATH):
        db_mtime = os.path.getmtime(DB_PATH)
        db_modified = datetime.fromtimestamp(db_mtime)
        print(f"  Database:       {DB_PATH}")
        print(f"  DB modified:    {db_modified.strftime('%Y-%m-%d %H:%M')}")
        ics_older = not os.path.exists(ICS_PATH) or os.path.getmtime(ICS_PATH) < db_mtime
        print(f"  ICS out of date: {'YES - regenerate needed' if ics_older else 'No'}")
    else:
        print(f"  No database found.")
    print()

def cmd_watch():
    print(f"\n  Watching DB for changes (Ctrl+C to stop)...")
    last_mtime = os.path.getmtime(DB_PATH) if os.path.exists(DB_PATH) else 0
    while True:
        try:
            time.sleep(30)
            if os.path.exists(DB_PATH):
                mtime = os.path.getmtime(DB_PATH)
                if mtime > last_mtime:
                    print(f"\n  [DB changed] Regenerating ICS...")
                    generate_ics()
                    last_mtime = mtime
        except KeyboardInterrupt:
            print("\n  Stopped.\n")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "generate":
        generate_ics()
    elif cmd == "deploy":
        if len(sys.argv) < 3:
            print("Usage: python ics_auto_deploy.py deploy /path/to/sync/folder")
        else:
            deploy(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    elif cmd == "watch":
        cmd_watch()
    else:
        print(__doc__)
