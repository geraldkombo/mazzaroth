"""
mazzaroth_personal.py — Gerald Kombo's personal blueprint, derived deterministically
from his computed natal chart + profection (time-lord) technique. No invented transits.

Every output is keyed to real computed facts: house occupancy, natal aspects,
current profection house, today's top transit (via mazzaroth/life-areas/wealth).
"""
import sys, os
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
import mazzaroth_life_areas as la
import wealth_optimizer as wo

HOUSE_NAME = {
    1: "Identity, Self-Image, Personal Brand", 2: "Finances, Values, Self-Worth",
    3: "Communication, Siblings, Writing", 4: "Home, Family, Roots",
    5: "Creativity, Romance, Pleasure, Risk", 6: "Health, Daily Work, Routines, Service",
    7: "Partnerships, Marriage, Contracts", 8: "Intimacy, Shared Resources, Transformation",
    9: "Philosophy, Travel, Publishing", 10: "Career, Reputation, Legacy",
    11: "Friends, Networks, Community, Hopes", 12: "Solitude, Spirituality, Retreat, Subconscious",
    13: "Ophiuchus — Healing, Higher Service, Synthesis",
}


def _occupancy():
    houses = {}
    for name, nd in mz.NATAL.items():
        houses.setdefault(mz._house_num(nd["lon"]), []).append(name)
    return houses


def _has_natal_aspect(a_name, b_name, want):
    """True if a->b has an aspect whose name matches `want`."""
    diff = abs(mz.NATAL[a_name]["lon"] - mz.NATAL[b_name]["lon"]) % 360
    if diff > 180:
        diff = 360 - diff
    for angle, orb, _base, aname in mz.ASPECTS:
        if abs(diff - angle) <= orb and aname == want:
            return True
    return False


def natal_constitution(occ):
    """Read the dominant shape of Gerald's fixed chart."""
    h2 = occ.get(2, [])
    h6 = occ.get(6, [])
    h7 = occ.get(7, [])
    h11 = occ.get(11, [])
    h12 = occ.get(12, [])
    moon_pluto = _has_natal_aspect("Moon", "Pluto", "Sq")
    merc_struggle = (_has_natal_aspect("Mercury", "Saturn", "Sq")
                     or _has_natal_aspect("Mercury", "Neptune", "Sq"))
    sun_mars = _has_natal_aspect("Sun", "Mars", "Conj")
    venus_uranus = _has_natal_aspect("Venus", "Uranus", "Sxt")
    jup_sat = _has_natal_aspect("Jupiter", "Saturn", "Opp")

    out = {
        "dominant_house": 2 if len(h2) >= 2 else 7,
        "headline": (
            f"Money house H2 stacked with {', '.join(h2)} — earning, valuing and selling "
            f"are wired into you. Your soul-growth axis is H7 partnerships "
            f"(Moon + North Node): contracts and one-to-one connections are where life happens."
        ),
        "money_wiring": {
            "planets": h2,
            "read": (
                f"You earn through {', '.join(h2) or 'H2'}: fast communication of value (Mercury), "
                "pricing and likability (Venus), bold action (Mars). Wealth comes from PEOPLE — "
                "closing deals, raising prices, negotiating contracts — not from passive bets."
            ),
            "tension": (
                "Mercury squares Saturn/Neptune: you over-plan and under-close, second-guess your "
                "own numbers, and let perfect plans replace sold work." if merc_struggle else
                "Clear Mercury wiring: your hands agree with your head. Keep the cadence."
            ),
            "technique": (
                "Set ONE external deadline this week and ship something small. Show the working "
                "product at 70% — the deal is a conversation, not a document you finish alone."
            ),
            "natal_patterns": [p["pattern"] for p in wo.natal_wealth_profile() if p["pattern"]],
        },
        "relationship_wiring": {
            "axis": h7,
            "read": (
                "Moon + North Node in H7: your growth comes THROUGH partnerships and contracts. "
                f"{'Moon square Pluto' if moon_pluto else 'Moon'}: intensity runs deep — you feel "
                "everything in alliances and may grip too hard when threatened."
            ),
            "technique": (
                "Keep the single most important partnership moving weekly. Name your feelings to "
                "yourself before negotiating them with others (Moon-Pluto regulation)."
            ),
        },
        "work_wiring": {
            "planets": h6,
            "read": (
                f"H6 carries {', '.join(h6)}: your daily-work and health engine. "
                "Saturn = discipline, Uranus = innovation, Neptune = risk of fuzzy burnout. "
                "Systems are your superpower; formless grind is your enemy."
            ),
            "technique": (
                "Protect recovery like a delivery date: sleep, single-focus blocks, one work theme "
                "per day. Guard against over-committing — Mars conjoined Sun wants to sprint every day."
            ),
        },
        "network": {
            "axis": h11,
            "read": (
                "Chiron sits in H11: the wound is belonging — fear of rejection inside communities, "
                "hopes that feel fragile. The cure is the same house: heal others in networks and "
                "your own place in them resolves."
            ),
            "technique": "Help one person publicly this week (answer, share, teach). Healing through service.",
        },
        "decision_tension": "Moon square Pluto" if moon_pluto else "none",
        "visualizer_hint": (
            f"Venus trine Jupiter + sextile Uranus: social magnetism and lucky timing in "
            "partnerships — soften hard asks with charm, move fast when Venus windows open." if venus_uranus else ""
        ),
        "expansion_tension": (
            "Jupiter opposite Saturn/Uranus/Neptune: the eternal pull between quiet expansion "
            "(research, vision) and rigid structure. In a completion year this is a feature: "
            "build systems in silence; let the structure mature before the public reveal." if jup_sat else ""
        ),
    }
    return out


def year_theme(occ):
    """Profection technique: current year's house, time-lord, and the 3-year arc."""
    h = mz.PROF_HOUSE
    age = mz._age_now()
    nxt = ((age + 1) % 13) + 1
    nxt2 = ((age + 2) % 13) + 1
    occupants = occ.get(h, [])
    time_lords = {12: "Jupiter", 13: "—", 1: "Sun", 2: "Venus", 3: "Mercury",
                  4: "Moon", 5: "Sun", 6: "Mercury", 7: "Venus", 8: "Pluto",
                  9: "Jupiter", 10: "Saturn", 11: "Saturn"}
    tl = time_lords.get(h, "—")
    meaning = {
        12: "COMPLETION YEAR — quiet power. Study, finish, archive, heal. Favor arrives "
            "behind the scenes and through faith/mentors. Do the deep work now; the reveal comes later.",
        13: "SYNTHESIS YEAR — Ophiuchus. Weave everything you learned into a method you can teach. "
            "Serve, heal, integrate body and work.",
        1: "IDENTITY YEAR — public relaunch. Rebrand the body of work you built in the quiet years.",
    }.get(h, "Focus the time-lord house this year.")
    means = {12: "Finish quietly: retire old projects, deepen your one craft, study and heal.",
             13: "Synthesise: turn the year's research into a teachable framework.",
             1: "Relaunch: take the rebuilt identity public."}
    arc = [
        {"year": str(datetime.now(timezone.utc).year), "house": h,
         "title": HOUSE_NAME[h].split(",")[0], "action": means.get(h, "Run this house")},
        {"year": str(datetime.now(timezone.utc).year + 1), "house": nxt,
         "title": HOUSE_NAME[nxt].split(",")[0],
         "action": means.get(nxt, "Run this house")},
        {"year": str(datetime.now(timezone.utc).year + 2), "house": nxt2,
         "title": HOUSE_NAME[nxt2].split(",")[0],
         "action": means.get(nxt2, "Run this house")},
    ]
    return {
        "age": age,
        "house": h,
        "name": HOUSE_NAME[h].split(",")[0],
        "time_lord": tl,
        "occupants": occupants,
        "meaning": meaning,
        "arc": arc,
        "weekly": (
            "Block 3 protected deep-work sessions in silence. No announcements, no launches. "
            "Research, write, finish. Answer the mentor's message. Rest without guilt." if h == 12
            else "Teach the framework you built. Serve one community you fear. Integrate body + work."
        ),
    }


def helps_and_avoids(occ, year, today_top):
    """Today-anchored actions, derived from today's real top transit + wiring."""
    helps, avoids = [], []
    # Chiron-in-H11 network healing (Uranus grid on Chiron is today's theme)
    if "Chiron" in occ.get(11, []):
        helps.append("Reconnect the network wound: send ONE value message to a group you avoid.")
        helps.append("Publish one piece to a small community — belonging heals by doing, not waiting.")
    if today_top and "Chiron" in today_top:
        helps.append("Uranus/Chiron activation today: break one fear about community. Reach out now.")
    # H2 money orders
    if occ.get(2, []):
        helps.append("Do one money conversation today: pitch, price raise, or chase the invoice.")
    # profection-specific
    if year["house"] == 12:
        helps.append("Protect quiet: 3 deep-work blocks, vendor noise off, finish one old project.")
        avoids.append("No public relaunches this year — that's H1's job (year +2).")
    if today_top:
        avoids.append(f"Don't over-commit to the {today_top} energy — do ONE bold move, not five.")
    # Moon-Pluto discipline
    if _has_natal_aspect("Moon", "Pluto", "Sq"):
        helps.append("Journal 5 minutes before money decisions: notice if mood is driving the number.")
    if _has_natal_aspect("Mercury", "Saturn", "Sq") or _has_natal_aspect("Mercury", "Neptune", "Sq"):
        helps.append("Cut the plan 3x smaller and put it out today — imperfect shipped beats perfect shelved.")
    if _has_natal_aspect("Sun", "Mars", "Conj"):
        avoids.append("Do not sprint in all directions — Mars/Sun demands single-target execution.")
    return helps[:6], avoids[:4]


def build_blueprint():
    occ = _occupancy()
    const = natal_constitution(occ)
    year = year_theme(occ)
    try:
        areas = la.life_areas_report()
        top_area = sorted(areas, key=lambda r: -r["score"])[0] if areas else None
    except Exception:
        top_area = None
    try:
        top = None
        td = mz.get_transit_data(datetime.now(timezone.utc).replace(tzinfo=None))
        _, hits = mz.score_transit(td)
        if hits:
            hits.sort(key=lambda x: -x[0])
            top = hits[0][1]
    except Exception:
        top = None
    helps, avoids = helps_and_avoids(occ, year, top)
    return {
        "generated": datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d %H:%M UTC"),
        "constitution": const,
        "year": year,
        "today_top": top,
        "top_life_area": {"house": top_area["house"], "name": top_area["name"]} if top_area else None,
        "helps_now": helps,
        "avoid_now": avoids,
    }


# ==== DEEP DAILY & HOURLY LAYER ====
# Maps any natal target -> Gerald's wiring axis, then builds an autonomous
# today reading from the real hourly engine rows + the profection technique.

SIGNAL_MAP = {
    "Sun":    ("Identity", "identity", "your H1 identity & personal brand — own the ambition, lead with who you are",
               "Make one visible move as yourself: post, pitch, or claim the role.",
               "Decide how you want to be seen tomorrow; draft the launch note.",
               "Separate your self-worth from today's output — rest and refill identity energy."),
    "Mercury":("Money: Deals", "money", "your money house H2 — a deal/communication trigger; your words create value",
               "Send the proposal, negotiate the price, set the deal meeting.",
               "Draft the pitch and the pricing options; prepare the numbers.",
               "Don't renegotiate in a tired mind — write the version you'll send fresh."),
    "Venus":  ("Money: Value", "money", "your money house H2 — values, pricing and likability in play",
               "Raise a price, pitch your value, or convert a contact into a client.",
               "List what you offer and what it's worth — before you ask.",
               "Receive compliments and money gracefully; invest in what you love."),
    "Mars":   ("Money: Action", "money", "your money house H2 — aggressive earning, bold action on income",
               "Chase the invoice, close the deal, launch the income move.",
               "Queue today's one bold earning action; armour up for pushback.",
               "Burn the adrenaline down with movement before you spend."),
    "Pluto":  ("Communication", "comms", "H3 — deep, persuasive communication and research power",
               "Write the transformative piece; have the hard, honest conversation.",
               "Outline the argument, gather the evidence, plan the message.",
               "Journal it out — Pluto words land best after reflection."),
    "Saturn": ("Work: Systems", "work", "H6 — work discipline and structure; your systems superpower",
               "Execute the routine with military precision; cement one system.",
               "Blueprint the system you'll build; set the non-negotiable routine.",
               "Rest on schedule — recovery is part of the discipline."),
    "Uranus": ("Work: Breakthrough", "work", "H6 — innovation and disruption in daily work",
               "Try the unconventional method; disrupt your own boring process.",
               "Prototype the new approach; expect the sudden insight.",
               "Step back so the flash of insight can arrive; change scenery."),
    "Neptune":("Work: Vision", "work", "H6 — vision vs. fog in daily work; verify facts, dream big",
               "Dream-shape the deliverable, then check every number twice.",
               "Write the vision, add the verification steps.",
               "Guard against burnout-illusion: boundaries, not endless grind."),
    "Moon":   ("Partnerships", "people", "H7 — partnerships & contracts, Moon-soft and emotional",
               "Have the key 1-on-1, smooth the alliance, sign the contract.",
               "Prepare the partnership talk; name your feelings first.",
               "Recover from people-drain; emotional rest before decisions."),
    "N.Node": ("Partnership Growth", "people", "H7 — your North Node: growth THROUGH people and contracts",
               "Take the partnership step your shyness avoids — it's your growth lane.",
               "Line up the growth conversation; commit to who you'll involve.",
               "Rest is fine — but keep the single key relationship warmed."),
    "Chiron": ("Community & Brand", "network", "H11 — the network wound heals by serving; your brand solves by helping",
               "Help one person publicly; publish the piece to a small community.",
               "Draft the share-ready value post; pick the community.",
               "Don't spiral over rejection-sensitivity — belonging comes from giving."),
    "Jupiter":("Year Priority", "year", "H12 — your time-lord house: quiet power, study, completion, faith",
               "Do the protected deep-work block; study, finish, archive one old project.",
               "Plan the quiet arc: research list, mentor call, finishing tasks.",
               "Rest without guilt — hidden work still counts this year."),
}

TARGET_BY_HOUSE = {}
for _nam, _nd in mz.NATAL.items():
    TARGET_BY_HOUSE.setdefault(mz._house_num(_nd["lon"]), []).append(_nam)

AXIS_BY_TARGET = {}
for _hk, _names in TARGET_BY_HOUSE.items():
    for _nm in _names:
        AXIS_BY_TARGET[_nm] = SIGNAL_MAP.get(_nm, (_nm, "natal", f"your natal {_nm}",
                                              "Act on this signal in your usual focused way.",
                                              "Prepare the move with clear notes.",
                                              "Rest and integrate the signal."))


def _category(level, score):
    if level in ("PEAK", "VERY HIGH"):
        return "ACT"
    if level == "HIGH":
        return "PLAN"
    return "REST"


def parse_transit(label):
    """Extract (transit, target) from engine hit labels in every format."""
    if not label:
        return None, None
    m = __import__("re").search(r"(\w[\w.]*)\s+\w+\s+natal\s+(\w[\w.]*)", label)
    if m:
        return m.group(1), m.group(2)
    m = __import__("re").search(r"(\w[\w.]*)\s+//\s+natal\s+(\w[\w.]*)", label)
    if m:
        return m.group(1), m.group(2)
    m = __import__("re").search(r"(\w[\w.]*)\s+anti-?(\w[\w.]*)", label)
    if m:
        return m.group(1), m.group(2)
    # transit-only fallback via WHICH_KEY map below
    m = __import__("re").search(r"^\s*([A-Z][\w.]*)", label)
    if m:
        return m.group(1), None
    return None, None


def signal_for(top_transit):
    transit, target = parse_transit(top_transit) if top_transit else (None, None)
    axis, tag, why, act, plan, rest = AXIS_BY_TARGET.get(target, SIGNAL_MAP.get(transit,
        (None, None, None, None, None, None)) or (None, None, None, None, None, None))
    if axis is None:
        return {"axis": "Natal", "tag": "natal", "text": "",
                "why": "personal natal activation", "act": "Act on the engine's top signal.",
                "plan": "Prepare for the active signal with clear notes.",
                "rest": "Rest and integrate the signal."}
    return {"axis": axis, "tag": tag, "why": why, "act": act, "plan": plan, "rest": rest}


def personal_for_hour(top_transit, level, score):
    sig = signal_for(top_transit)
    cat = _category(level, score)
    text = sig.get({"ACT": "act", "PLAN": "plan", "REST": "rest"}[cat], sig["rest"])
    if cat == "REST" and level not in ("HIGH", "VERY HIGH", "PEAK") and score == 0:
        text = "Quiet hour — use for rest or deep work."
    return {"axis": sig["axis"], "tag": sig["tag"], "cat": cat, "text": text}


def build_reading(hourly):
    """Autonomous today reading from real hourly rows + blueprint + technique."""
    if not hourly:
        return None
    acts = [x for x in hourly if x.get("personal", {}).get("cat") == "ACT"]
    plans = [x for x in hourly if x.get("personal", {}).get("cat") == "PLAN"]
    active = acts or plans
    top = max(hourly, key=lambda x: x.get("score", 0) or 0)
    top_sig = signal_for(top.get("top_transit", ""))
    # dominant axis across the day's engaged hours
    from collections import Counter
    cnt = Counter(x.get("personal", {}).get("axis", "Natal") for x in active)
    dom_axis, dom_n = cnt.most_common(1)[0] if cnt else ("—", 0)
    # year anchor
    y = {
        "age": mz._age_now(), "house": mz.PROF_HOUSE,
        "name": HOUSE_NAME[mz.PROF_HOUSE].split(",")[0],
        "time_lord": {12: "Jupiter"}.get(mz.PROF_HOUSE, "—"),
    }
    occ = _occupancy()
    mode = "ACT" if acts else ("PLAN" if plans else "REST")
    headline = (
        f"Today turns on {top_sig['axis'].lower()}: {top.get('top_transit') or 'your top transit'}. "
        f"{top_sig['why']}. Peak energy {top.get('time', '')} — {len(acts)} ACT hour(s) / {len(plans)} PLAN, "
        f"axis most loaded: {dom_axis}."
        if top_sig.get("axis") != "Natal" else
        f"{top.get('top_transit') or 'a steady signal'} — {top_sig['why']}. Peak energy {top.get('time', '')}."
    )
    story = (
        f"Your H{y['house']} {y['name']} year (time-lord {y['time_lord']}) frames the day: "
        f"{len(acts)} ACT hour(s) / {len(plans)} PLAN hour(s), dominated by {dom_axis}. "
        + ("Run the day like a protected work block: act in the ACT windows, prep in the PLAN gaps, "
           "guard recovery in REST." if y["house"] == 12 else
           "Lean into the loaded axis today — act in the ACT windows, prepare in the PLAN gaps, rest the rest.")
    )
    moves = []
    top_sigs = signal_for(acts[0]["top_transit"]) if acts else None
    if occ.get(2, []):
        moves.append("MONEY MOVE — one conversation with a price on it: pitch, raise, or chase the invoice.")
    if occ.get(7, []):
        moves.append("PEOPLE MOVE — keep the one key partnership moving; warm the contract.")
    if occ.get(6, []):
        moves.append("WORK MOVE — one system, one focused block; protect recovery like a delivery date.")
    if moves == [] and top_sigs:
        moves.append(top_sigs["act"])
    watch = [{"time": a["time"], "axis": a.get("personal", {}).get("axis"), "score": round(a.get("score", 0))}
             for a in sorted(active, key=lambda x: -(x.get("score", 0) or 0))[:4]]
    return {
        "headline": headline, "story": story,
        "moves": moves[:3], "watch": watch,
        "axis_focus": dom_axis, "year_house": y["house"], "year_name": y["name"],
        "top_time": top.get("time", ""), "act_count": len(acts), "plan_count": len(plans), "mode": mode,
    }


if __name__ == "__main__":
    import json
    b = build_blueprint()
    print(json.dumps(b, indent=2))