"""Fiorenza-style lunar layers for the Mazzaroth engine.

Adds two ideas from Nick Anthony Fiorenza's "Lunar Planner" (sidereal / star-level
astrology) on top of the tropical transit engine, without disturbing it:

1. The sidereal lunar mansions (nakshatras) — the 27 star-mansions the Moon
   travels through (each 13d20m of sidereal longitude). Fiorenza's technique
   anchors timing in the *stars the Moon is actually passing*, not the tropical
   signs. We compute the Moon's sidereal longitude (tropical - ayanamsa) and map
   it to the mansion + its deity/meaning.

2. The eight lunar phases as a developmental "action spiral" — each phase has a
   specific task (begin / commit / act / refine / illuminate / share / release /
   surrender). This is Fiorenza's core "live in attunement to the lunar cycles"
   teaching, kept distinct from the existing agriculture advice.

Ayanamsa: Lahiri (the standard sidereal offset). ~24.2 deg in 2026.
"""

import math

# Lahiri ayanamsa in degrees, valid around the given decimal year.
# Base 23d51'11.24" at J2000.0, precessing ~50.29" per year.
_AYANAMSA_BASE = 23.853122  # 23d51'11.24"
_AYANAMSA_RATE = 50.29 / 3600.0  # deg per year


def ayanamsa(year=2026.0):
    """Lahiri ayanamsa (degrees) for a decimal year."""
    return _AYANAMSA_BASE + (year - 2000.0) * _AYANAMSA_RATE


# 27 sidereal lunar mansions. Each spans 13d20m (13.333... deg).
# `end` is the inclusive upper edge of the mansion in sidereal longitude.
NAKSHATRAS = [
    (0.0,   'Ashwini',          'Ashwini Kumaras', 'Horse head',      'Swift healing and fresh starts. Move quickly, initiate.'),
    (13.333, 'Bharani',         'Yama',            'Yoni',            'Bearing and discipline. Finish what you started, honour limits.'),
    (26.667, 'Krittika',        'Agni',            'Razor / flame',   'Cutting and purification. Cut through clutter, refine.'),
    (40.0,   'Rohini',          'Prajapati',       'Cart / ox',       'Growth and abundance. Nourish, build, beautify.'),
    (53.333, 'Mrigashira',      'Soma',            'Deer head',       'Gentle seeking. Research, wander, follow curiosity.'),
    (66.667, 'Ardra',           'Rudra',           'Teardrop',        'The storm. Breakthrough through release; cleanse and clear.'),
    (80.0,   'Punarvasu',       'Aditi',           'Quiver / return', 'Renewal and return. Restore, reunite, come back home.'),
    (93.333, 'Pushya',          'Brihaspati',      'Cow udder',       'Nourishing and auspicious. Feed, support, bless.'),
    (106.667, 'Ashlesha',       'Nagas',           'Serpent',         'Depth and intuition. Read beneath the surface.'),
    (120.0,  'Magha',           'Pitris',          'Throne',          'Ancestry and authority. Claim your legacy, lead.'),
    (133.333, 'Purva Phalguni', 'Bhaga',           'Hammock',         'Pleasure and creative rest. Enjoy, romance, restore.'),
    (146.667, 'Uttara Phalguni','Aryaman',         'Bed',             'Alliance and commitment. Sign, partner, make it real.'),
    (160.0,  'Hasta',           'Savitar',         'Hand',            'Skill and craft. Work with your hands, fix, heal.'),
    (173.333, 'Chitra',         'Tvashtar',        'Jewel',           'Design and beauty. Architect, refine, adorn.'),
    (186.667, 'Swati',          'Vayu',            'Young shoot',     'Independence and movement. Go your own way, breathe.'),
    (200.0,  'Vishakha',        'Indra / Agni',    'Triumphal arch',  'Determination and victory. Push to the finish, celebrate.'),
    (213.333, 'Anuradha',       'Mitra',           'Lotus / staff',   'Friendship and devotion. Cooperate, stay loyal.'),
    (226.667, 'Jyeshtha',       'Indra',           'Earring / umbrella','Seniority and protection. Take charge, shield the weak.'),
    (240.0,  'Mula',            'Nirriti',         'Bundle of roots', 'Uprooting and foundations. Dig deep, remove, reset.'),
    (253.333, 'Purva Ashadha',  'Apas',            'Fan / tusk',      'Invigoration and early victory. Declare, energise.'),
    (266.667, 'Uttara Ashadha', 'Vishvadevas',     'Elephant tusk',   'Enduring victory. Hold the line, finish the long task.'),
    (280.0,  'Shravana',        'Vishnu',          'Three footprints','Listening and learning. Study, hear, connect the dots.'),
    (293.333, 'Dhanishta',      'Vasus',           'Drum',            'Rhythm and wealth. Drum the beat, gather resources.'),
    (306.667, 'Shatabhisha',    'Varuna',          'Empty circle',    'Healing and mystery. Close the loop, restore wholeness.'),
    (320.0,  'Purva Bhadrapada','Aja Ekapada',     'Sword / two faces','Fire and transformation. Cut the old, transmute.'),
    (333.333, 'Uttara Bhadrapada','Ahir Budhnya',  'Serpent of depth','Depth and stability. Settle into the deep, endure.'),
    (346.667, 'Revati',         'Pushan',          'Fish / drum',     'Safe passage and completion. Wrap up, guide, rest.'),
]


def lunar_mansion(moon_tropical_lon, ay=None, year=2026.0):
    """Return the nakshatra dict for a Moon tropical longitude (degrees).

    moon_tropical_lon: ecliptic longitude 0..360 (tropical, what Skyfield gives).
    """
    if ay is None:
        ay = ayanamsa(year)
    sid = (moon_tropical_lon - ay) % 360.0
    idx = int(sid // 13.33333333)  # 13d20m
    if idx >= 27:
        idx = 26
    end, name, deity, symbol, meaning = NAKSHATRAS[idx]
    # pada: which quarter of the mansion (1-4)
    pada = int((sid - idx * 13.33333333) // (13.33333333 / 4.0)) + 1
    return {
        'index': idx + 1,
        'name': name,
        'deity': deity,
        'symbol': symbol,
        'meaning': meaning,
        'pada': pada,
        'sidereal': round(sid, 2),
    }


# Fiorenza-style developmental guidance for the eight lunar phases.
# Matches the angle thresholds used in generate_daily_data.py.
PHASE_GUIDE = [
    (22.5,  'New Moon',         'Begin. Set intention — plant the seed of what you will grow this cycle.'),
    (67.5,  'Waxing Crescent',  'Commit. Gather resources and take the first small, concrete steps.'),
    (112.5, 'First Quarter',    'Act. Overcome resistance — build and push through the obstacle.'),
    (157.5, 'Waxing Gibbous',   'Refine. Adjust and perfect what is taking shape before it culminates.'),
    (202.5, 'Full Moon',        'Illuminate. Culminate and reveal — harvest the awareness and express it.'),
    (247.5, 'Waning Gibbous',   'Share. Give away, teach, and communicate what this cycle taught you.'),
    (292.5, 'Last Quarter',     'Release. Let go of what no longer serves; restructure and clear.'),
    (337.5, 'Waning Crescent',  'Surrender. Rest, integrate, and dream the shape of the next cycle.'),
]


def phase_guide(phase_angle):
    """Return {name, guide} for a Moon-Sun elongation in degrees (0..360)."""
    for deg, name, guide in PHASE_GUIDE:
        if phase_angle <= deg:
            return {'name': name, 'guide': guide}
    return {'name': 'New Moon', 'guide': PHASE_GUIDE[0][2]}


def illumination(phase_angle):
    """Approximate % of the Moon's disc lit, from elongation (0..360)."""
    return (1.0 - math.cos(math.radians(phase_angle))) / 2.0 * 100.0
