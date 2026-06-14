#!/usr/bin/env python3
"""
Zepp Auto Sync - Automated Data Ingestion Bridge.
Watches a Zepp-Exports folder and triggers correlation when new CSVs arrive.

Usage:
    python zepp_auto_sync.py                    # Start watcher (daemon mode)
    python zepp_auto_sync.py run path/to.csv    # One-shot import
    python zepp_auto_sync.py status             # Show import history
"""

import sys, os, csv, json, time, hashlib
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))

DATA_DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")
IMPORT_LOG = os.path.join(DATA_DIR, "zepp_imports.csv")
CORRELATION_OUT = os.path.join(DATA_DIR, "zepp_mazzaroth_correlation_results.csv")
WATCH_FOLDER = os.path.join(os.path.dirname(__file__), "Zepp_Exports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(WATCH_FOLDER, exist_ok=True)

def _ensure_import_log():
    if not os.path.exists(IMPORT_LOG):
        with open(IMPORT_LOG, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["imported_at","filename","rows","hash"])

def _file_hash(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _is_already_imported(fhash):
    if not os.path.exists(IMPORT_LOG):
        return False
    with open(IMPORT_LOG, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row.get("hash") == fhash:
                return True
    return False

def _log_import(filename, rows, fhash):
    _ensure_import_log()
    with open(IMPORT_LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"), filename, rows, fhash])

def correlate(zepp_path):
    print(f"  Correlating: {zepp_path}")
    try:
        import zepp_correlate
        result = zepp_correlate.main(zepp_path)
        if result:
            print(f"  Correlation complete. Results in {CORRELATION_OUT}")
        return result
    except Exception as e:
        print(f"  Correlation error: {e}")
        return None

def run_import(zepp_path):
    if not os.path.exists(zepp_path):
        print(f"  File not found: {zepp_path}")
        return
    fhash = _file_hash(zepp_path)
    if _is_already_imported(fhash):
        print(f"  Already imported (skip): {os.path.basename(zepp_path)}")
        return
    # Count rows
    with open(zepp_path, "r", encoding="utf-8-sig") as f:
        rows = sum(1 for _ in f) - 1  # minus header
    _log_import(os.path.basename(zepp_path), rows, fhash)
    print(f"  Imported: {os.path.basename(zepp_path)} ({rows} rows)")
    correlate(zepp_path)

def cmd_status():
    _ensure_import_log()
    print(f"\n{'='*56}")
    print(f"  ZEPP AUTO SYNC - STATUS")
    print(f"{'='*56}")
    if os.path.exists(IMPORT_LOG):
        with open(IMPORT_LOG, "r", encoding="utf-8-sig") as f:
            imported = list(csv.DictReader(f))
        print(f"  Imports: {len(imported)}")
        for i in imported[-10:]:
            print(f"    {i['imported_at']} | {i['filename']:40} | {i['rows']:>5} rows")
    else:
        print(f"  No imports recorded yet.")
    # Watch folder
    files = [f for f in os.listdir(WATCH_FOLDER) if f.endswith(".csv")]
    print(f"  Files in watch folder ({WATCH_FOLDER}): {len(files)}")
    for f in files[-5:]:
        print(f"    {f}")
    print(f"\n  Watching: {WATCH_FOLDER} (run daemon mode to auto-import)")
    print()

def cmd_watch():
    print(f"\n  Zepp Auto Sync - Watching: {WATCH_FOLDER}")
    print(f"  Drop CSV files here to auto-import and correlate.")
    print(f"  Press Ctrl+C to stop.\n")
    seen = set()
    while True:
        try:
            files = [f for f in os.listdir(WATCH_FOLDER) if f.endswith(".csv")]
            for fname in files:
                fpath = os.path.join(WATCH_FOLDER, fname)
                fhash = _file_hash(fpath)
                if fhash not in seen and not _is_already_imported(fhash):
                    seen.add(fhash)
                    print(f"\n  [New file detected] {fname}")
                    run_import(fpath)
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n  Stopped.\n")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_watch()
    elif sys.argv[1] == "run":
        if len(sys.argv) < 3:
            print("Usage: python zepp_auto_sync.py run path/to/zepp.csv")
        else:
            run_import(sys.argv[2])
    elif sys.argv[1] == "status":
        cmd_status()
    else:
        print(__doc__)
