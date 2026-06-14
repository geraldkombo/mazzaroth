import csv, os, re
from datetime import datetime

dir_name = "Mazzaroth_Engine_Data"
os.makedirs(dir_name, exist_ok=True)

ics_path = "mazzaroth_exact.ics"
master_path = os.path.join(dir_name, "mazzaroth_master_log.csv")
leverage_path = os.path.join(dir_name, "high_leverage_windows.csv")
correlation_path = os.path.join(dir_name, "zepp_mazzaroth_correlation_template.csv")

print("Parsing mazzaroth_exact.ics...")
with open(ics_path, "r", encoding="utf-8") as f:
    content = f.read()

events = []
blocks = content.split("BEGIN:VEVENT")[1:]
for block in blocks:
    if "END:VEVENT" not in block:
        continue
    block = block.split("END:VEVENT")[0]

    dtstart = re.search(r"DTSTART;TZID=Africa/Nairobi:(\d{4})(\d{2})(\d{2})T", block)
    summary = re.search(r"SUMMARY:(.+)", block)
    desc = re.search(r"DESCRIPTION:(.+)", block)
    if not (dtstart and summary and desc):
        continue

    date_str = f"{dtstart.group(1)}-{dtstart.group(2)}-{dtstart.group(3)}"
    summary_text = summary.group(1).strip()
    desc_text = desc.group(1).strip().replace("\\n", "\n")

    level_match = re.search(r"\[(PEAK|VERY HIGH|HIGH)\]", summary_text)
    level = level_match.group(1) if level_match else ""

    transit_match = re.search(r"\| (.+?) H(\d+)", summary_text)
    transit = transit_match.group(1) if transit_match else ""
    house = transit_match.group(2) if transit_match else ""

    score_match = re.search(r"Score: ([\d.]+)", desc_text)
    score = float(score_match.group(1)) if score_match else 0

    prof_match = re.search(r"Profection: H(\d+)", desc_text)
    prof = prof_match.group(1) if prof_match else ""

    aspect_match = re.search(r"Aspect: (.+)", desc_text)
    aspect = aspect_match.group(1).strip() if aspect_match else ""

    lines = desc_text.split("\n")
    meaning = ""
    actions = ""
    in_actions = False
    action_lines = []
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith("WHAT THIS MEANS:"):
            if i + 1 < len(lines):
                meaning = lines[i + 1].strip()
        elif s.startswith("ACTIONS:"):
            in_actions = True
        elif in_actions:
            if s and "Mazzaroth" not in s:
                action_lines.append(s.replace("-> ", "").strip())
            elif "Mazzaroth" in s:
                break
    actions = "\n".join(action_lines)
    status = "Upcoming" if date_str >= datetime.now().strftime("%Y-%m-%d") else "Passed"

    events.append({
        "Date": date_str, "Level": level, "Transit": transit,
        "House": house, "Profection": prof, "Score": score,
        "Aspect": aspect, "Meaning": meaning, "Actions": actions,
        "Status": status
    })

events.sort(key=lambda x: x["Date"])

# 1. Master CSV
print(f"Writing {master_path}...")
with open(master_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Date","Level","Transit","House","Profection","Score","Aspect","Meaning","Actions","Status"])
    for e in events:
        w.writerow([e["Date"],e["Level"],e["Transit"],e["House"],e["Profection"],
                    f'{e["Score"]:.1f}',e["Aspect"],e["Meaning"],e["Actions"],e["Status"]])

# 2. High-Leverage Windows (top 5% PEAK days sorted by score)
print(f"Writing {leverage_path}...")
scores = sorted([e["Score"] for e in events])
threshold = scores[int(len(scores) * 0.95)]
peaks = [e for e in events if e["Score"] >= threshold]
peaks.sort(key=lambda x: x["Score"], reverse=True)

with open(leverage_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Score","Date","Level","Transit","House","Profection","Aspect","Meaning","Actions","Status","T-Rex2_Memo"])
    for e in peaks:
        memo = f"PEAK {e['Date'][5:]} | {e['Transit']} H{e['House']} | {e['Meaning'][:55]}"
        w.writerow([f'{e["Score"]:.1f}', e["Date"], e["Level"], e["Transit"],
                    e["House"], e["Profection"], e["Aspect"], e["Meaning"],
                    e["Actions"], e["Status"], memo])

# 3. Zepp Correlation Template
print(f"Writing {correlation_path}...")
with open(correlation_path, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Date","Zepp_Recovery_Score_(0-100)","Zepp_Stress_Score_(0-100)","Mazzaroth_Transit_Intensity_(Score)","Mazzaroth_Level","Mazzaroth_Transit_Pair","Notes"])
    for e in events:
        w.writerow([e["Date"],"","",f'{e["Score"]:.1f}',e["Level"],e["Transit"],""])

print(f"\n  Mazzaroth_Engine_Data/")
print(f"  +-- mazzaroth_master_log.csv              ({len(events)} events)")
print(f"  +-- high_leverage_windows.csv             ({len(peaks)} top-5% windows)")
print(f"  +-- zepp_mazzaroth_correlation_template.csv  (ready for Zepp merge)")
print(f"\nInstructions:")
print(f"  1. Open mazzaroth_master_log.csv in Excel, use Conditional Formatting on Score (color scale).")
print(f"  2. high_leverage_windows.csv = your strategy sheet. Print this.")
print(f"  3. zepp_mazzaroth_correlation_template.csv: paste your Zepp Recovery/Stress columns next to dates.")
