"""
Mazzaroth Life Areas - Relationships, Sex, Wealth, Career, Health, and all 13 houses.
Expands the base engine with comprehensive interpretations for every domain.

Usage:
    from mazzaroth_life_areas import life_areas_report, relationship_report
"""

import sys, os
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz

# === LIFE AREAS BY HOUSE ===
LIFE_AREAS = {
    1:  "Identity, Self-Image, Personal Brand",
    2:  "Finances, Values, Self-Worth",
    3:  "Communication, Siblings, Short Trips, Writing",
    4:  "Home, Family, Roots, Emotional Foundation",
    5:  "Creativity, Romance, Children, Pleasure, Risk",
    6:  "Health, Daily Work, Routines, Service",
    7:  "Partnerships, Marriage, Contracts, Open Enemies",
    8:  "Sex, Intimacy, Shared Resources, Inheritance, Transformation",
    9:  "Philosophy, Travel, Higher Education, Publishing",
    10: "Career, Reputation, Public Life, Legacy",
    11: "Friends, Networks, Community, Hopes, Wishes",
    12: "Solitude, Spirituality, Retreat, Subconscious",
    13: "Ophiuchus - Healing, Higher Service, Synthesis",
}

# === RELATIONSHIP-SPECIFIC INTERPRETATIONS (H7) ===
RELATIONSHIP_INTEL = {
    "Venus":   "Relationships are harmonious and magnetic. Attract partnerships naturally. Focus on shared beauty and values.",
    "Mars":    "Passion and conflict in relationships. Attraction is strong but egos may clash. Channel into shared goals.",
    "Jupiter": "Relationships expand your world. A partner may bring growth, travel, or new opportunities. Watch for over-idealization.",
    "Saturn":  "Commitment and responsibility in relationships. A karmic partnership. May feel heavy or restrictive at first.",
    "Pluto":   "Deep transformation through relationships. Power dynamics are intense. The connection is fated and irreversible.",
    "Neptune": "Spiritual or illusionary relationships. Tendency to idealize partners. Need for clear boundaries.",
    "Uranus":  "Unexpected relationships or sudden changes. Need for freedom within partnership. Electric connections.",
    "Mercury": "Communication is the foundation. Intellectual chemistry. Talk through everything.",
    "Sun":     "Self-expression through partnership. The relationship reflects your identity. Creative collaboration.",
    "Moon":    "Emotional bonding and nurturing. Partnerships feel like home. High emotional attunement.",
    "N.Node":  "Karmic partnership. This relationship advances your soul's path. Do not run from it.",
    "Chiron":  "Healing through relationships. Old wounds surface to be seen and held. Deep vulnerability required.",
}

# === SEX/INTIMACY INTERPRETATIONS (H8) ===
SEX_INTEL = {
    "Venus":   "Sensual and affectionate intimacy. Touch, presence, and beauty heighten the experience. Deep bonding.",
    "Mars":    "Raw passion and sexual drive. High libido. Assertive in the bedroom. Intense chemistry.",
    "Jupiter": "Expansive sexuality. Adventurous, open-minded. May explore new territories of intimacy.",
    "Saturn":  "Sexual discipline or restraint. May take time to open up. Once committed, deeply loyal.",
    "Pluto":   "Sexual transformation. The most intense, primal connections. Merging of souls and bodies.",
    "Neptune": "Spiritual sexuality. Merging without boundaries. Ecstatic but need grounding.",
    "Uranus":  "Experimental and unconventional sexuality. Open to non-traditional dynamics. Electric bedroom energy.",
    "Mercury": "Sexual communication. Talking about desires is essential. Erotic intelligence.",
    "Sun":     "Sexual confidence and self-expression. Generous lover. Identity affirmed through intimacy.",
    "Moon":    "Emotional sexuality. Intimacy requires feeling safe. Nurturing through physical connection.",
    "N.Node":  "Fated sexual connections. Past-life resonance with certain partners.",
    "Chiron":  "Healing sexual wounds. Vulnerability in intimacy leads to deep restoration.",
}

# === WEALTH/CAREER INTEL ===
WEALTH_INTEL = {
    ("Jupiter","2"):  "Financial expansion. Money flows in. Invest in growth. Generosity pays back.",
    ("Saturn","2"):   "Financial discipline. Budget and structure. Delayed but solid gains.",
    ("Pluto","2"):    "Financial transformation. Debt payoff, inheritance, or rebounding from loss.",
    ("Venus","2"):    "Money through beauty, art, or social connections. Pleasant financial period.",
    ("Saturn","10"):  "Career structure. Promotion, recognition, authority. Building legacy.",
    ("Jupiter","10"): "Career breakthrough. Visibility, awards, public success. Step into leadership.",
    ("Pluto","10"):   "Career transformation. Power shift. Old role dies, new authority rises.",
    ("Sun","10"):     "Recognition and acclaim. Your talents are seen. Lead publicly.",
    ("Mercury","3"):  "Communication superpowers. Pitch, write, teach. Ideas gain traction.",
    ("Jupiter","9"):  "Expansion through publishing, travel, or education. Big-picture thinking.",
}

# === HEALTH/WELLNESS INTEL ===
HEALTH_INTEL = {
    ("Saturn","6"): "Build health discipline. Routine is everything. Slow, consistent gains.",
    ("Mars","6"):   "High energy for physical work. Channel into exercise. Watch for burnout.",
    ("Pluto","6"):  "Deep health transformation. Heal the root cause. Regenerative period.",
    ("Neptune","6"):"Sensitive to environment. Need for rest. Watch for immune system.",
    ("Jupiter","6"):"Vitality expansion. Good time for detox, retreat, or health optimization.",
    ("Moon","6"):   "Emotional health linked to daily routines. Nurture yourself through habits.",
    ("Sun","6"):    "Vitality peaks when work aligns with purpose. Health follows meaning.",
}

# === HOME/FAMILY INTEL ===
HOME_INTEL = {
    ("Moon","4"):  "Family and home are emotionally central. Nurturing your domestic space heals.",
    ("Venus","4"): "Harmony in the home. Decorate, host, beautify your living space.",
    ("Mars","4"):  "Tension or renovation at home. Channel into construction or reorganization.",
    ("Saturn","4"):"Family responsibility or structural foundation work. Building stability.",
    ("Pluto","4"): "Deep family transformation. Old patterns unearthed. Rebuilding the roots.",
    ("Uranus","4"):"Unexpected changes in home or family. Relocation or restructuring.",
    ("Jupiter","4"):"Home expansion. Moving to bigger space. Family growth or hosting.",
}

# === CREATIVITY/ROMANCE INTEL ===
ROMANCE_INTEL = {
    ("Venus","5"): "Romance and pleasure are heightened. Dating, creative projects, and joy.",
    ("Sun","5"):   "Self-expression through creativity. Perform, create, show your work.",
    ("Mars","5"):  "Passionate romance. Pursuing what you desire. Creative breakthroughs.",
    ("Jupiter","5"):"Creative expansion. Luck in romance. Children or artistic projects thrive.",
    ("Pluto","5"): "Creative transformation. Your art goes deep. Romance is all-consuming.",
    ("Neptune","5"):"Artistic inspiration at its peak. Romantic fantasy. Creative flow.",
    ("Uranus","5"):"Creative breakthroughs. Unexpected romance. Unconventional pleasure.",
}

# === SPIRITUALITY/SOLITUDE INTEL ===
SPIRIT_INTEL = {
    ("Neptune","12"):"Spiritual awakening. Dreams are vivid. Meditation deepens. Boundaries dissolve.",
    ("Moon","12"):   "Emotional retreat needed. Solitude restores. Work with dreams and subconscious.",
    ("Pluto","12"):  "Deep psychological work. Shadow integration. Past-life material surfaces.",
    ("Jupiter","12"):"Spiritual expansion. Study esoteric subjects. Retreat leads to growth.",
    ("Saturn","12"): "Spiritual discipline. Solitude practice. Karmic accounting and release.",
    ("Sun","12"):    "Period of introspection. Identity reforms in solitude. Hidden creativity.",
    ("Mercury","12"):"Deep communication with the unseen. Journaling, therapy, dreamwork.",
    ("Venus","12"):  "Spiritual love. Compassion practice. Artistic solitude.",
    ("Mars","12"):   "Spiritual warrior. Confront shadows. Energy work and purification.",
}

def _house_num_for(name):
    nd = mz.NATAL.get(name, mz.NATAL["Sun"])
    return mz._house_num(nd["lon"])

def relationship_report(transit_data=None):
    """Analyze transits affecting relationships (H7) and sex (H8)."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)

    results = []
    for tname, td in transit_data.items():
        for nname, nd in mz.NATAL.items():
            h = mz._house_num(nd["lon"])
            if h not in (7, 8):
                continue
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, _, aname in mz.ASPECTS:
                if abs(diff - angle) <= orb:
                    intel = RELATIONSHIP_INTEL.get(tname, SEX_INTEL.get(tname, ""))
                    area = "Partnership" if h == 7 else "Intimacy/Sex"
                    results.append({
                        "area": area, "house": h,
                        "transit": f"{tname} {aname} natal {nname}",
                        "delta": round(diff - angle, 3),
                        "interpretation": intel or f"{tname} activating H{h}",
                    })
    results.sort(key=lambda x: abs(x["delta"]))
    return results

# House cusps: each house corresponds to a constellation zone.
# Cusp = starting longitude of that constellation.
# This ensures transits can activate ALL 13 life areas, even without natal planets.
def _build_house_cusps():
    sun_idx = next(i for i, (_, _, n) in enumerate(mz.IAU) if n == mz._constellation(mz.NATAL["Sun"]["lon"]))
    cusps = {}
    for h in range(1, 14):
        const_idx = (h - 1 + sun_idx) % len(mz.CONST_ORDER)
        const_name = mz.CONST_ORDER[const_idx]
        start_lon = next(s for s, e, n in mz.IAU if n == const_name)
        cusps[h] = {"lon": start_lon, "name": const_name}
    return cusps

HOUSE_CUSPS = _build_house_cusps()

def life_areas_report(transit_data=None, level_filter=None):
    """Score every life area based on current transits. Uses house cusps so ALL 13 areas are scored."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)

    thresh = {"peak": 3100, "vhigh": 2800, "high": 2400}
    cache_path = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")
    if os.path.exists(cache_path):
        import json
        with open(cache_path) as f: thresh = json.load(f)

    area_scores = {h: 0 for h in LIFE_AREAS}
    area_hits = {h: [] for h in LIFE_AREAS}

    # Score transits against natal planets (existing logic)
    for tname, td in transit_data.items():
        tw = mz.WEIGHTS.get(tname, 1.0)
        tmm = td["motion_mult"]
        for nname, nd in mz.NATAL.items():
            h = mz._house_num(nd["lon"])
            nw = mz.WEIGHTS.get(nname, 1.0)
            hw = mz.HOUSE_WT.get(h, 1.0)
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in mz.ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    prec = 3.0 if delta < 0.1 else (2.0 if delta < 0.5 else 1.0)
                    s = base * tw * nw * hw * tmm * prec
                    area_scores[h] += s
                    area_hits[h].append(f"{tname} {aname} {nname} ({delta:.2f}deg)")

    # Also score transits against all 13 house cusps (ensures ALL life areas activate)
    weights_by_name = {"Sun":1.5,"Moon":1.0,"Mercury":1.2,"Venus":1.2,"Mars":1.5,"Jupiter":2.0,
        "Saturn":2.5,"Uranus":3.0,"Neptune":3.5,"Pluto":4.0,"N.Node":1.8,"Chiron":1.5}
    for tname, td in transit_data.items():
        tw = weights_by_name.get(tname, 1.0)
        tmm = td["motion_mult"]
        for h, cusp in HOUSE_CUSPS.items():
            hw = mz.HOUSE_WT.get(h, 1.0)
            diff = abs(td["lon"] - cusp["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, base, aname in mz.ASPECTS:
                delta = abs(diff - angle)
                if delta <= orb:
                    prec = 3.0 if delta < 0.1 else (2.0 if delta < 0.5 else 1.0)
                    s = base * tw * hw * tmm * prec
                    area_scores[h] += s
                    area_hits[h].append(f"{tname} {aname} H{h} cusp ({delta:.2f}deg)")

    report = []
    for h in sorted(area_scores.keys()):
        sc = area_scores[h]
        lvl = mz.get_level(sc, thresh)
        if level_filter and lvl != level_filter:
            continue
        hits = area_hits[h][:5]
        report.append({
            "house": h, "name": LIFE_AREAS[h],
            "score": round(sc, 1), "level": lvl or "NORMAL",
            "aspects": hits,
        })
    report.sort(key=lambda x: x["score"], reverse=True)
    return report

def all_area_transits(transit_data=None):
    """Get all active transits mapped to life areas."""
    if transit_data is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit_data = mz.get_transit_data(now)

    rows = []
    for tname, td in transit_data.items():
        for nname, nd in mz.NATAL.items():
            h = mz._house_num(nd["lon"])
            diff = abs(td["lon"] - nd["lon"]) % 360
            if diff > 180: diff = 360 - diff
            for angle, orb, _, aname in mz.ASPECTS:
                if abs(diff - angle) <= orb:
                    delta = round(diff - angle, 3)
                    rows.append({
                        "transit_planet": tname,
                        "natal_planet": nname,
                        "aspect": aname,
                        "house": h,
                        "life_area": LIFE_AREAS.get(h, f"House {h}"),
                        "orb": delta,
                    })
    rows.sort(key=lambda x: x["house"])
    return rows

def format_report(report, title="LIFE AREAS REPORT"):
    lines = [f"\n{'='*56}", f"  {title}", f"{'='*56}"]
    for r in report:
        lvl_disp = r["level"]
        lines.append(f"\n  H{r['house']:2} {r['name']}")
        lines.append(f"  Score: {r['score']:<8} Level: {lvl_disp}")
        for a in r["aspects"][:3]:
            lines.append(f"    -> {a}")
    lines.append("")
    return "\n".join(lines)

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "relationship":
        report = relationship_report()
        print(f"\n{'='*56}")
        print(f"  RELATIONSHIP & SEX TRANSITS")
        print(f"{'='*56}")
        for r in report:
            print(f"\n  [{r['area']}] H{r['house']}")
            print(f"  {r['transit']}  (orb {r['delta']:+})")
            print(f"  {r['interpretation']}")
        print()

    elif len(sys.argv) > 1 and sys.argv[1] == "areas":
        report = life_areas_report()
        print(format_report(report, "ALL LIFE AREAS (sorted by intensity)"))
        for r in report:
            if r["level"] in ("PEAK", "VERY HIGH"):
                intel_map = {
                    2: WEALTH_INTEL, 3: None, 4: HOME_INTEL, 5: ROMANCE_INTEL,
                    6: HEALTH_INTEL, 7: None, 8: None, 10: WEALTH_INTEL, 12: SPIRIT_INTEL
                }
                im = intel_map.get(r["house"])
                if im:
                    first_aspect = r["aspects"][0].split(" ")[0] if r["aspects"] else ""
                    key = (first_aspect, str(r["house"]))
                    if key in im:
                        print(f"  >> {im[key]}")
        print()

    elif len(sys.argv) > 1 and sys.argv[1] == "all":
        rows = all_area_transits()
        print(f"\n{'='*56}")
        print(f"  ALL ACTIVE TRANSITS BY LIFE AREA")
        print(f"{'='*56}")
        cur_h = 0
        for r in rows:
            if r["house"] != cur_h:
                cur_h = r["house"]
                print(f"\n  H{cur_h}: {r['life_area']}")
            print(f"    {r['transit_planet']:10} {r['aspect']:4} {r['natal_planet']:10} (orb {r['orb']:+})")
        print()

    else:
        print(__doc__)
        print("Commands:")
        print("  python mazzaroth_life_areas.py relationship   # Relationship & sex transits")
        print("  python mazzaroth_life_areas.py areas          # All life areas by intensity")
        print("  python mazzaroth_life_areas.py all            # All active transits mapped to life areas")
