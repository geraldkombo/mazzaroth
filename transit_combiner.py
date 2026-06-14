#!/usr/bin/env python3
"""
Transit Combiner - Multi-transit synthesis engine.
Reads all active aspects for a given date and produces a single
"Strategic Daily Brief" that synthesizes the full transit picture
into actionable language.

Usage:
    python transit_combiner.py now          # Today's strategic brief
    python transit_combiner.py date YYYY-MM-DD  # Specific date
    python transit_combiner.py tomorrow     # Tomorrow's brief
    python transit_combiner.py week         # 7-day narrative
"""

import sys, os, json
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")

# Narrative archetypes per planet combination
ARCHETYPES = {
    "Sun": "identity, vitality, will",
    "Moon": "emotions, intuition, habit",
    "Mercury": "communication, data, decisions",
    "Venus": "relationships, values, pleasure",
    "Mars": "action, drive, ambition",
    "Jupiter": "expansion, luck, growth",
    "Saturn": "structure, discipline, karma",
    "Uranus": "innovation, disruption, awakening",
    "Neptune": "vision, illusion, spirituality",
    "Pluto": "transformation, power, depth",
    "N.Node": "destiny, soul path, trajectory",
    "Chiron": "healing, wound, vulnerability",
}
ASPECT_STYLES = {
    "Conj": ("fusion", "fuses"),
    "Sxt": ("opportunity", "opens"),
    "Tri": ("flow", "supports"),
    "Sq": ("tension", "challenges"),
    "Opp": ("polarity", "polarizes"),
    "Qnx": ("catalyst", "catalyzes"),
    "Qnt": ("spur", "spurs"),
    "BQnt": ("persistent", "nags"),
    "SSq": ("subtle friction", "frays"),
    "SqSq": ("building pressure", "pressures"),
    "PAR": ("declination", "aligns"),
    "ANTI": ("antiscion", "mirrors"),
}

def _get_style(aname):
    return ASPECT_STYLES.get(aname, (aname, aname.lower()+"s"))

def _archetype(name):
    return ARCHETYPES.get(name, name)

def _assess_tone(hits):
    supportive = 0; challenging = 0
    for _, desc, aname in hits:
        key = aname if aname else ""
        if key in ASPECT_STYLES:
            label, _ = ASPECT_STYLES[key]
            if label in ("fusion","opportunity","flow","declination","antiscion"):
                supportive += 1
            elif label in ("tension","polarity"):
                challenging += 1
    net = supportive - challenging
    if net >= 2: return "supportive"
    if net <= -2: return "challenging"
    if challenging > supportive: return "mixed-tension"
    return "neutral"

def synthesize_brief(transit_data=None, date_label=None):
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)

    thresh = {"peak":3100,"vhigh":2800,"high":2400}
    if os.path.exists(THRESH_CACHE):
        with open(THRESH_CACHE) as f: thresh = json.load(f)

    score, hits = mz.score_transit(transit_data)
    level = mz.get_level(score, thresh) or "NORMAL"
    tone = _assess_tone(hits)
    top = hits[0] if hits else (0, "No significant aspects", "")
    tname = top[1].split(" ")[0] if hits else ""

    nname = "chart"
    if "natal " in top[1]:
        nname = top[1].split("natal ")[1].split(" ")[0]
    nd = mz.NATAL.get(nname, mz.NATAL["Sun"])
    h = mz._house_num(nd["lon"])
    interp, actions = mz.get_interpretation(tname if tname else "Sun", h)

    # Build narrative lines
    lines = []
    tone_words = {"supportive":"Harmonious", "challenging":"Intense", "mixed-tension":"Mixed", "neutral":"Neutral"}
    lines.append(f"Overview: {tone_words.get(tone, tone.capitalize())} {level} day (score {score:.0f}).")

    # Planet-specific briefs
    planets_used = set()
    for s, desc, aname in hits[:5]:
        parts = desc.split(" ")
        if len(parts) < 2: continue
        tp = parts[0]
        if tp in planets_used: continue
        planets_used.add(tp)
        label, verb = _get_style(aname)
        # Find natal planet name (word after "natal")
        np = ""
        for i, p in enumerate(parts):
            if p == "natal" and i + 1 < len(parts):
                np = parts[i + 1]
                break
        if not np and "//" in desc:
            np = "chart"  # declination aspect
        t_arch = _archetype(tp)
        n_arch = _archetype(np) if np else "chart"
        angle = desc.split("(")[-1].rstrip(")") if "(" in desc else ""
        lines.append(f"  {tp} ({t_arch}) {verb} your {n_arch} ({label}, {angle}).")

    # Top strategy
    lines.append(f"\n  Focus: {interp}")
    if actions:
        lines.append(f"  Action: {actions[0]}")

    return {
        "date": date_label or datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M UTC"),
        "score": round(score, 1),
        "level": level,
        "tone": tone,
        "top_transit": top[1] if hits else "",
        "brief": "\n".join(lines),
        "strategy": interp,
        "actions": actions,
    }

def cmd_now():
    brief = synthesize_brief()
    print(f"\n{'='*56}")
    print(f"  STRATEGIC DAILY BRIEF")
    print(f"{'='*56}")
    print(f"\n  {brief['date']}  |  Score: {brief['score']}  |  {brief['level']}  |  Tone: {brief['tone'].upper()}")
    print(f"\n{brief['brief']}")
    print()

def cmd_date(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc).replace(tzinfo=None)
    except ValueError:
        print(f"  Invalid date: {date_str} (use YYYY-MM-DD)")
        return
    midday = datetime.combine(dt.date(), datetime.min.time(), tzinfo=timezone.utc).replace(tzinfo=None) + timedelta(hours=12)
    transit = mz.get_transit_data(midday)
    brief = synthesize_brief(transit, date_str)
    print(f"\n{'='*56}")
    print(f"  STRATEGIC BRIEF - {brief['date']}")
    print(f"{'='*56}")
    print(f"  Score: {brief['score']}  |  {brief['level']}  |  Tone: {brief['tone'].upper()}")
    print(f"\n{brief['brief']}")
    print()

def cmd_tomorrow():
    dt = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=1)
    cmd_date(dt.strftime("%Y-%m-%d"))

def cmd_week():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    print(f"\n{'='*56}")
    print(f"  7-DAY STRATEGIC NARRATIVE")
    print(f"{'='*56}")
    for i in range(7):
        dt = now + timedelta(days=i)
        midday = datetime.combine(dt.date(), datetime.min.time(), tzinfo=timezone.utc).replace(tzinfo=None) + timedelta(hours=12)
        transit = mz.get_transit_data(midday)
        brief = synthesize_brief(transit, dt.strftime("%Y-%m-%d"))
        tone_mark = {"supportive":"+", "challenging":"-", "mixed-tension":"~", "neutral":"="}.get(brief["tone"], "?")
        print(f"\n  {dt.strftime('%a %m/%d')} [{tone_mark}] {brief['level']:10} {brief['score']:>6}")
        print(f"  {brief['top_transit'][:60]}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_now()
    elif sys.argv[1] == "now":
        cmd_now()
    elif sys.argv[1] == "date":
        if len(sys.argv) < 3:
            print("Usage: python transit_combiner.py date YYYY-MM-DD")
        else:
            cmd_date(sys.argv[2])
    elif sys.argv[1] == "tomorrow":
        cmd_tomorrow()
    elif sys.argv[1] == "week":
        cmd_week()
    else:
        print(__doc__)
