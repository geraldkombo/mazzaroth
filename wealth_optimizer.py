#!/usr/bin/env python3
"""
Wealth Optimizer - Financial Astrology Engine.
Billionaire-grade transit analysis for wealth timing, investments, and financial decisions.

Usage:
    python wealth_optimizer.py now           # Current wealth transit briefing
    python wealth_optimizer.py calendar      # Best financial days this month
    python wealth_optimizer.py pattern       # Your billionaire wealth pattern
    python wealth_optimizer.py invest        # Investment timing analysis
"""

import sys, os, json, math
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")

# Wealth houses
WEALTH_HOUSES = [2, 8, 10]  # H2=money, H8=shared resources, H10=career
BUSINESS_HOUSES = [6, 10, 11]  # H6=work, H10=reputation, H11=network

# Financial planet archetypes
FINANCE_PLANETS = {
    "Jupiter": {"role":"expansion", "action":"Invest, expand, seek opportunities", "weight":2.0},
    "Saturn":  {"role":"structure", "action":"Budget, consolidate, build systems", "weight":1.5},
    "Pluto":   {"role":"transformation", "action":"Restructure debt, transform revenue model", "weight":2.5},
    "Venus":   {"role":"revenue", "action":"Monetize relationships, beauty, art", "weight":1.5},
    "Mars":    {"role":"drive", "action":"Execute aggressively, launch, compete", "weight":1.2},
    "Sun":     {"role":"recognition", "action":"Lead publicly, build personal brand", "weight":1.3},
    "Mercury": {"role":"communication", "action":"Negotiate, pitch, write proposals", "weight":1.0},
    "Neptune": {"role":"vision", "action":"Brand storytelling, creative monetization", "weight":1.5},
    "Uranus":  {"role":"innovation", "action":"Disrupt market, adopt new revenue channels", "weight":2.0},
    "N.Node":  {"role":"destiny", "action":"Follow long-term financial vision", "weight":1.8},
    "Chiron":  {"role":"healing", "action":"Heal money wounds, price your worth", "weight":1.0},
}

# Billionaire patterns: planetary configurations statistically overrepresented in high-net-worth charts
BILLIONAIRE_PATTERNS = [
    {"name":"Jupiter-Saturn Bridge", "description":"Discipline meets expansion. Build wealth systematically over decades. Patient capital.", "planets":["Jupiter","Saturn"],"aspects":["Conj","Tri","Sxt"]},
    {"name":"Pluto Wealth Transformer", "description":"Phoenix money story. Multiple fortunes made and lost. Deep financial transformation.", "planets":["Pluto"],"aspects":["Conj","Sq","Opp"]},
    {"name":"Venus-Jupiter Amplifier", "description":"Money flows through relationships, beauty, and generosity. Social capital = financial capital.", "planets":["Venus","Jupiter"],"aspects":["Conj","Tri","Sxt"]},
    {"name":"Saturn H10 Career Emperor", "description":"Authority, legacy, and institutional power. Build a monopoly or market-dominating position.", "planets":["Saturn"],"aspects":["Conj","Tri"]},
    {"name":"Uranus H11 Network Disruptor", "description":"Fortune through networks, community, and tech platforms. First-mover advantage.", "planets":["Uranus","N.Node"],"aspects":["Conj","Sxt"]},
    {"name":"Mars-H2 Money Warrior", "description":"Aggressive wealth building. High risk tolerance. Multiple revenue streams.", "planets":["Mars","Pluto"],"aspects":["Conj","Sxt"]},
    {"name":"Neptune Brand Visionary", "description":"Fortune through storytelling, brand, and vision. Sell the dream, not the product.", "planets":["Neptune","Sun"],"aspects":["Conj","Tri","Sxt"]},
    {"name":"Mercury-H3 Deal Maker", "description":"Negotiation, trading, and information arbitrage. Mind is the money machine.", "planets":["Mercury","Jupiter"],"aspects":["Conj","Tri","Sxt"]},
]

def _house_num_for(name):
    nd = mz.NATAL.get(name, mz.NATAL["Sun"])
    return mz._house_num(nd["lon"])

def _finance_role(planet):
    info = FINANCE_PLANETS.get(planet, {})
    return info.get("role", "influence"), info.get("action", "")

def wealth_score(transit_data=None):
    """Compute a wealth-specific score (0-1000) from current transits to financial houses."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)
    score = 0
    factors = []
    for tname, td in transit_data.items():
        tw = FINANCE_PLANETS.get(tname, {}).get("weight", 1.0)
        tmm = td["motion_mult"]
        for nname, nd in mz.NATAL.items():
            h = mz._house_num(nd["lon"])
            if h not in WEALTH_HOUSES:
                continue
            nw = mz.WEIGHTS.get(nname, 1.0)
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in mz.ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    prec = 3.0 if delta < 0.1 else (2.0 if delta < 0.5 else 1.0)
                    s = base * tw * nw * tmm * prec
                    score += s
                    factors.append({
                        "transit": tname, "natal": nname, "aspect": aname,
                        "house": h, "contrib": round(s, 1), "delta": round(delta, 3)
                    })
    factors.sort(key=lambda x: x["contrib"], reverse=True)
    return round(score, 1), factors

def billionaire_patterns(transit_data=None):
    """Check which billionaire wealth patterns are currently activated."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)
    active = []
    for pattern in BILLIONAIRE_PATTERNS:
        found = False
        for tname, td in transit_data.items():
            for ptarget in pattern["planets"]:
                nd = mz.NATAL.get(ptarget)
                if not nd: continue
                diff = abs(td["lon"] - nd["lon"]) % 360
                if diff > 180: diff = 360 - diff
                for angle, orb, _, aname in mz.ASPECTS:
                    if aname not in pattern["aspects"]: continue
                    if abs(diff - angle) <= orb:
                        if not found:
                            active.append({
                                "pattern": pattern["name"],
                                "description": pattern["description"],
                                "trigger": f"{tname} {aname} natal {ptarget}",
                                "orb": round(diff - angle, 3),
                            })
                            found = True
                        break
                if found: break
    return active

def investment_window(transit_data=None):
    """Determine if today is favorable for investment decisions."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)

    verdicts = []
    mercury = transit_data.get("Mercury", {})
    mercury_lon = mercury.get("lon", 0)
    mercury_spd = mercury.get("spd", 0)

    # Mercury retrograde check
    if mercury_spd < 0:
        verdicts.append(("AVOID", "Mercury retrograde - defer major financial decisions, signings, launches"))

    # Mercury in financial houses (use house cusps from life areas module)
    try:
        from mazzaroth_life_areas import HOUSE_CUSPS as WC
    except ImportError:
        WC = {}
    for h in [2, 8]:
        cusp_lon = WC.get(h, {}).get("lon") if WC else None
        if cusp_lon is not None:
            diff = abs(mercury_lon - cusp_lon) % 360
            if diff < 8:
                verdicts.append(("FAVORABLE", "Mercury in financial house - good for negotiations, proposals, analysis"))

    # Jupiter favorable days
    jupiter = transit_data.get("Jupiter", {})
    jup_lon = jupiter.get("lon", 0)
    for nname, nd in mz.NATAL.items():
        h = mz._house_num(nd["lon"])
        if h in WEALTH_HOUSES:
            diff = abs(jup_lon - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            if abs(diff - 120) <= 7:
                verdicts.append(("FAVORABLE", f"Jupiter trine natal {nname} H{h} - expansion window, invest"))
            elif abs(diff - 60) <= 5:
                verdicts.append(("FAVORABLE", f"Jupiter sextile natal {nname} H{h} - opportunity window, act"))
            elif abs(diff - 0) <= 8:
                verdicts.append(("HIGH IMPACT", f"Jupiter conjunct natal {nname} H{h} - major financial cycle begins"))

    # Saturn discipline check
    saturn = transit_data.get("Saturn", {})
    sat_lon = saturn.get("lon", 0)
    for nname, nd in mz.NATAL.items():
        h = mz._house_num(nd["lon"])
        if h in WEALTH_HOUSES:
            diff = abs(sat_lon - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            if abs(diff - 0) <= 8:
                verdicts.append(("WARNING", f"Saturn conjunct natal {nname} H{h} - financial pressure, restructure, do not over-leverage"))

    if not verdicts:
        verdicts.append(("NEUTRAL", "No strong financial signals today. Focus on execution and systems."))
    return verdicts

def financial_forecast(days=30):
    """Generate a financial forecast for the next N days."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    forecast = []
    for i in range(days):
        dt = now + timedelta(days=i)
        midday = datetime.combine(dt.date(), datetime.min.time(), tzinfo=timezone.utc).replace(tzinfo=None) + timedelta(hours=12)
        transit = mz.get_transit_data(midday)
        ws, factors = wealth_score(transit)
        patterns = billionaire_patterns(transit)
        invest = investment_window(transit)
        if ws > 500 or patterns or any(v[0] in ("FAVORABLE","HIGH IMPACT","WARNING") for v in invest):
            forecast.append({
                "date": dt.strftime("%Y-%m-%d"),
                "day": dt.strftime("%a"),
                "wealth_score": ws,
                "top_factor": factors[0] if factors else None,
                "patterns": [p["pattern"] for p in patterns],
                "verdicts": invest,
            })
    return forecast

def natal_wealth_profile():
    """Analyze the natal chart for innate wealth potential (billionaire blueprint)."""
    profile = []
    for name, nd in mz.NATAL.items():
        h = mz._house_num(nd["lon"])
        house_label = {2:"Finances",8:"Shared Resources",10:"Career"}.get(h, f"H{h}")
        if h in WEALTH_HOUSES:
            pattern = ""
            for p in BILLIONAIRE_PATTERNS:
                if name in p["planets"]:
                    pattern = p["name"]
                    break
            profile.append({
                "planet": name, "house": h, "house_label": house_label,
                "lon": round(nd["lon"], 1), "pattern": pattern,
            })
    return profile

def cmd_now():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transit = mz.get_transit_data(now)
    ws, factors = wealth_score(transit)
    patterns = billionaire_patterns(transit)
    invest = investment_window(transit)
    natal = natal_wealth_profile()

    print(f"\n{'='*56}")
    print(f"  WEALTH OPTIMIZER - {now.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{'='*56}")
    print(f"  Wealth Score: {ws}/1000")
    print(f"  Active Patterns: {len(patterns)}")

    if patterns:
        print(f"\n  {'='*56}")
        print(f"  BILLIONAIRE PATTERNS ACTIVE")
        print(f"  {'='*56}")
        for p in patterns:
            print(f"    [{p['pattern']}]")
            print(f"    {p['description']}")
            print(f"    Trigger: {p['trigger']} (orb {p['orb']:+})")
            print()

    if factors:
        print(f"  ACTIVE WEALTH ASPECTS:")
        for f in factors[:8]:
            hname = {2:"Fin",8:"Shared",10:"Career"}.get(f['house'], f'House {f["house"]}')
            role, action = _finance_role(f["transit"])
            print(f"    {f['transit']:10} {f['aspect']:4} natal {f['natal']:10} H{f['house']} ({hname}) +{f['contrib']:>6}")
        print()

    print(f"  INVESTMENT VERDICT:")
    for v in invest:
        print(f"    [{v[0]}] {v[1]}")
    print()

    print(f"  NATAL WEALTH BLUEPRINT:")
    for p in natal:
        tag = f" << {p['pattern']}" if p['pattern'] else ""
        print(f"    {p['planet']:12} in {p['house_label']:18} ({p['lon']}deg){tag}")
    print()

def cmd_calendar():
    forecast = financial_forecast(60)
    print(f"\n{'='*56}")
    print(f"  FINANCIAL CALENDAR - Next {len(forecast)} key days")
    print(f"{'='*56}")
    for f in forecast:
        tags = []
        for v in f["verdicts"]:
            icon = {"FAVORABLE":"+", "HIGH IMPACT":"++", "WARNING":"!", "AVOID":"X", "NEUTRAL":"~"}.get(v[0], "?")
            tags.append(f"{icon}{v[0][0]}")
        ptag = " ".join(p[:3] for p in f["patterns"]) if f["patterns"] else ""
        print(f"  {f['date']} {f['day']:4} | WS:{f['wealth_score']:>5} | {' '.join(tags):20} {ptag}")
    print()

def cmd_pattern():
    natal = natal_wealth_profile()
    print(f"\n{'='*56}")
    print(f"  YOUR BILLIONAIRE WEALTH BLUEPRINT")
    print(f"{'='*56}")
    print(f"  Based on your natal chart, here are the wealth patterns hard-coded in your birth chart:")
    for p in natal:
        if p["pattern"]:
            print(f"\n  [{p['pattern']}]")
            for bp in BILLIONAIRE_PATTERNS:
                if bp["name"] == p["pattern"]:
                    print(f"    {bp['description']}")
    print(f"\n  Natal planets in wealth houses:")
    for p in natal:
        print(f"    {p['planet']:12} H{p['house']} {p['house_label']:20} {p['lon']}deg")
    print()

def cmd_invest():
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transit = mz.get_transit_data(now)
    invest = investment_window(transit)
    ws, factors = wealth_score(transit)
    mercury = transit.get("Mercury", {})
    mercury_spd = mercury.get("spd", 0)

    print(f"\n{'='*56}")
    print(f"  INVESTMENT TIMING ANALYSIS")
    print(f"{'='*56}")
    print(f"  Mercury {'RETROGRADE - Defer major decisions' if mercury_spd < 0 else 'Direct - Good for new commitments'}")
    print(f"  Wealth Score: {ws}/1000")
    print()
    for v in invest:
        icon = {"FAVORABLE":"+", "HIGH IMPACT":"++", "WARNING":"!", "AVOID":"X", "NEUTRAL":"~"}.get(v[0], "?")
        print(f"  [{icon}] {v[1]}")
    print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        cmd_now()
    elif sys.argv[1] == "now":
        cmd_now()
    elif sys.argv[1] == "calendar":
        cmd_calendar()
    elif sys.argv[1] == "pattern":
        cmd_pattern()
    elif sys.argv[1] == "invest":
        cmd_invest()
    else:
        print(__doc__)
