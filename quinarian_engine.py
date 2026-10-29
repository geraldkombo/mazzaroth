#!/usr/bin/env python3
"""
Quinarian Engine v1 — The Astrological Goetia Calendar & Alert System
Generates ICS for ALL 72 quinaries with smart watch notifications,
preparation alerts, and email-ready briefings.

Usage:
    python quinarian_engine.py ics              Generate full ICS calendar
    python quinarian_engine.py now              Current quinary status
    python quinarian_engine.py daemon           Watch & alert daemon
    python quinarian_engine.py deploy FOLDER    Copy ICS to sync folder
"""

import sys, os, json, csv, math, time, shutil
from datetime import datetime, timedelta, timezone
from collections import OrderedDict

# === PATH SETUP ===
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "Mazzaroth_Engine_Data")
ICS_PATH = os.path.join(ROOT, "quinarian_calendar.ics")
os.makedirs(DATA_DIR, exist_ok=True)

# === THE 72 QUINARIES — COMPLETE DATA ===
# Each entry: (quinary#, start_deg, end_deg, sign, angel, demon, attributes, psalm, psalm_ref)
QUINARIES = [
    (1,0,4.99,"Aries","VEHUIAH","BAEL","Enlightenment, expanded consciousness, arts and sciences, skillful, wise","But thou, O Lord, art a shield for me; my glory, and the lifter up of mine head.","Psalm 3:3"),
    (2,5,9.99,"Aries","IELIEL (JELIEL)","AGARES","Repress revolutions, fidelity, marital harmony, generation, passionate, courteous, cheerful","But be not thou far from me, O Lord: O my strength, haste thee to help me.","Psalm 22:19"),
    (3,10,14.99,"Aries","SITAEL","VASSAGO","Magnanimity, nobility, against adversity, truth, helpful","I will say of the Lord, He is my refuge and my fortress: my God; in him will I trust.","Psalm 91:2"),
    (4,15,19.99,"Aries","ELEMIAH","GAMIGIN (SAMIGINA)","Spiritual peace, sea voyages, discovery, industrious, travel","Return, O Lord, deliver my soul: oh save me for thy mercies' sake.","Psalm 6:4"),
    (5,20,24.99,"Aries","MAHASIAH","MARBAS","Peace, magic, occultism, theology, agreeable, honest, science","I sought the Lord, and he heard me, and delivered me from all my fears.","Psalm 34:4"),
    (6,25,29.99,"Aries","LEHAHEL","VALEFOR (VALEFAR)","Cures disease, love, ambition, fame, arts and sciences, fortune","Sing praises to the Lord, which dwelleth in Zion: declare among the people his doings.","Psalm 9:11"),
    (7,0,4.99,"Taurus","ACHAIAH","AMON (AAMON)","Useful knowledge, secrets, patience, temperance, skillful","The Lord is merciful and gracious, slow to anger, and plenteous in mercy.","Psalm 103:8"),
    (8,5,9.99,"Taurus","CAHETEL (CAHETHEL)","BARBATOS","Blessings, theology, protection, rural, agriculture, business acumen, hunting","O come, let us worship and bow down: let us kneel before the Lord our maker.","Psalm 95:6"),
    (9,10,14.99,"Taurus","HAZIEL (AZIEL)","PAIMON","Promises, friendship, faith, sincerity, forgiving","Remember, O Lord, thy tender mercies and thy lovingkindnesses; for they have been ever of old.","Psalm 25:6"),
    (10,15,19.99,"Taurus","ALADIAH","BUER","Secrets, diseases, health, healing, sophisticated, success","Let thy mercy, O Lord, be upon us, according as we hope in thee.","Psalm 33:22"),
    (11,20,24.99,"Taurus","LAUVIA (LAVIAH)","GUSION","Protection from lightning, victory, fame, talented","The Lord liveth; and blessed be my rock; and let the God of my salvation be exalted.","Psalm 18:46"),
    (12,25,29.99,"Taurus","HAHAIAH","SITRI","Against adversity, charity, dreams, mysteries, gentle, agreeable","Why standest thou afar off, O Lord? why hidest thou thyself in times of trouble?","Psalm 10:1"),
    (13,0,4.99,"Gemini","IAZALEL (IEZALEL)","BELETH (BILETH)","Reconciliation, marital fidelity, memory, learning, eloquent, rhetoric","Make a joyful noise unto the Lord, all the earth: make a loud noise, and rejoice, and sing praise.","Psalm 98:4"),
    (14,5,9.99,"Gemini","MEBAHEL","LERAIKHA (LERAJE)","Against greed, justice, truth, liberty, law, protection, prisoners, influence","The Lord also will be a refuge for the oppressed, a refuge in times of trouble.","Psalm 9:9"),
    (15,10,14.99,"Gemini","HARIEL","ELIGOS (ELIGOR)","Religion, arts and sciences, pure, morality, discoveries","But the Lord is my defense; and my God is the rock of my refuge.","Psalm 94:22"),
    (16,15,19.99,"Gemini","HAKAMIAH","ZEPAR","Against traitors, dignitaries, war, loyal, brave, passionate, victory, honor","O Lord God of my salvation, I have cried day and night before thee.","Psalm 88:1"),
    (17,20,24.99,"Gemini","LAUVIAH (LOVIAH)","BOTIS","Rest, sciences, music, poetry, philosophy, discoveries, dreams","O Lord our Lord, how excellent is thy name in all the earth!","Psalm 8:9"),
    (18,25,29.99,"Gemini","CALIEL","BATHIN","Truth, innocence, integrity, just, trials, witnesses","Judge me, O Lord my God, according to thy righteousness; and let them not rejoice over me.","Psalm 35:24"),
    (19,0,4.99,"Cancer","LEUVIAH (LEVUIAH)","SALLOS (SALEOS)","Obtaining grace, memory, joviality, intelligence, amiable, stoic","I waited patiently for the Lord; and he inclined unto me, and heard my cry.","Psalm 40:1"),
    (20,5,9.99,"Cancer","PAHALIAH","PURSON","Conversions, theology, chastity, morals, purity","In my distress I cried unto the Lord, and he heard me. Deliver my soul, O Lord, from lying lips, and from a deceitful tongue.","Psalm 120:1-2"),
    (21,10,14.99,"Cancer","NELCHAEL","MARAX (MORAX)","Against slander, astronomy, mathematics, geography, poetry, studious","But I trusted in thee, O Lord: I said, Thou art my God.","Psalm 31:14"),
    (22,15,19.99,"Cancer","IEIAIEL","IPOS","Protection, storms, philanthropy, business acumen, voyages","The Lord is thy keeper: the Lord is thy shade upon thy right hand.","Psalm 121:5"),
    (23,20,24.99,"Cancer","MELAHEL","AIM","Against weapons and perils, medicinal herbs, disease, safety, travels, honor","The Lord shall preserve thy going out and thy coming in from this time forth, and even for evermore.","Psalm 121:8"),
    (24,25,29.99,"Cancer","HAHUIAH (HAIVIAH)","NABERIUS (NABERUS)","Grace, exile, against thieves and murderers, protection, truth, sincerity","Behold, the eye of the Lord is upon them that fear him, upon them that hope in his mercy.","Psalm 33:18"),
    (25,0,4.99,"Leo","NITHHAIAH","GLASYA-LABOLAS","Wisdom, dreams, occult sciences, revelations, peace, solitude","I will praise thee, O Lord, with my whole heart; I will shew forth all thy marvellous works.","Psalm 9:1"),
    (26,5,9.99,"Leo","HAAIAH","BIM (BUNE)","Truth, peace treaties, judgment, divine contemplation, politics, communication","I cried with my whole heart; hear me, O Lord: I will keep thy statutes.","Psalm 119:145"),
    (27,10,14.99,"Leo","IERATHEL (JERATHEL)","RONOVE","Protection from attacks, confounds enemies, liberty, peace, literature","Deliver me, O Lord, from the evil man: preserve me from the violent man.","Psalm 140:1"),
    (28,15,19.99,"Leo","SEEHIAH (SEEIAH)","BERITH (BEALE)","Protection from fire and storms, health, longevity, circumscript, simplicity","O God, be not far from me: O my God, make haste for my help.","Psalm 71:12"),
    (29,20,24.99,"Leo","REIIEL (REIAIEL)","ASTAROTH","Against atheists, theology, truth, mysticism, philosophy","Behold, God is mine helper: the Lord is with them that uphold my soul.","Psalm 54:4"),
    (30,25,29.99,"Leo","OMAEL","FORNEUS","Against depression, generation, anatomy and medicine, animals, patience","For thou art my hope, O Lord God: thou art my trust from my youth.","Psalm 71:5"),
    (31,0,4.99,"Virgo","LECABEL","FORAS","Problem-solving, agriculture, astronomy, talents, insight","I will go in the strength of the Lord God: I will make mention of thy righteousness, even of thine only.","Psalm 71:16"),
    (32,5,9.99,"Virgo","VASARIAH","ASMODAY (ASMODAI)","Against false accusations, justice, memory, eloquence, amiable","For the word of the Lord is right; and all his works are done in truth.","Psalm 33:4"),
    (33,10,14.99,"Virgo","IEUIAH (IEHUIAH)","GAAPH (GAAP)","Uncovers plots, protection, loyalty, fidelity","The Lord knoweth the thoughts of man, that they are vanity.","Psalm 94:11"),
    (34,15,19.99,"Virgo","LEHAHAIAH (LEHAHIAH)","FURFUR","International peace, faith, respect, talents, confidence","Let Israel hope in the Lord from henceforth and forever.","Psalm 131:3"),
    (35,20,24.99,"Virgo","CHAVAKIAH (CHEVAKIAH)","MARCHOSIAS","Restores friendship, peace, harmony, selfless, finances, service","I love the Lord, because he hath heard my voice and my supplications.","Psalm 116:1"),
    (36,25,29.99,"Virgo","MENADEL (MANADEL)","STOLAS (STOLOS)","Against slander, releases prisoners, reparations, livelihood","Lord, I have loved the habitation of thy house, and the place where thine honour dwelleth.","Psalm 26:8"),
    (37,0,4.99,"Libra","ANIEL","PHENEX (PHEYNIX)","Victory, release from siege, arts and sciences, wisdom, inspirational, fame","Turn us again, O God, and cause thy face to shine; and we shall be saved.","Psalm 80:3"),
    (38,5,9.99,"Libra","HAAMIAH","MALTHOUS (HALPHAS)","Theology, protection, treasures, against fraud, sects","Because thou hast made the Lord, which is my refuge, even the most High, thy habitation.","Psalm 91:9"),
    (39,10,14.99,"Libra","REHAEL","MALPHAS","Protection, cures disease, health, longevity, familial","Hear, O Lord, and have mercy upon me: Lord, be thou my helper.","Psalm 30:10"),
    (40,15,19.99,"Libra","IEIAZEL","RAUM","Releases prisoners, literature, the arts, design, eloquence","Lord, why castest thou off my soul? why hidest thou thy face from me?","Psalm 88:14"),
    (41,20,24.99,"Libra","HAHAHEL (HAHAEL)","FURCALOR (FOCALOR)","Against atheists and slander, Christianity, priests, missionaries","Deliver my soul, O Lord, from lying lips, and from a deceitful tongue.","Psalm 120:2"),
    (42,25,29.99,"Libra","MIKAEL (MICHAEL)","VEPAR (VEPHAR)","Safe journeys, curiosity, politics, conspiracies, foreign news","The Lord shall preserve thee from all evil: he shall preserve thy soul.","Psalm 121:7"),
    (43,0,4.99,"Scorpio","VEUALIAH","SABNOCK (SAVNOK)","Destroys enemies, prosperity, bellicose, glory, liberty","But unto thee have I cried, O Lord; and in the morning shall my prayer prevent thee.","Psalm 88:13"),
    (44,5,9.99,"Scorpio","IELAHIAH","SHAZ (SHAX)","Victory in lawsuits, courage, travels, learning","Accept, I beseech thee, the freewill offerings of my mouth, O Lord, and teach me thy judgments.","Psalm 119:108"),
    (45,10,14.99,"Scorpio","SEALIAH","VINE (VINEA)","Confounds evil, vegetation, education, health, learning, resources","When I said, My foot slippeth; thy mercy, O Lord, held me up.","Psalm 94:18"),
    (46,15,19.99,"Scorpio","ARIEL","BIFRONS (BIFROVS)","Hidden treasures, dreams, imagination, resourceful, circumspect","The Lord is good to all: and his tender mercies are over all his works.","Psalm 145:9"),
    (47,20,24.99,"Scorpio","ASALIAH","UVALL (VUAL)","Spirituality, justice, contemplation, agreeable, occult learning","O Lord, how great are thy works! and thy thoughts are very deep.","Psalm 92:5"),
    (48,25,29.99,"Scorpio","MIHAEL","HAAGENTI","Marital harmony, generation, love, protection, fidelity, passionate, pleasure","The Lord hath made known his salvation: his righteousness hath he openly shewed in the sight of the heathen.","Psalm 98:2"),
    (49,0,4.99,"Sagittarius","VEHUEL","CROCELL (CROKEL)","Religious, humble, sorrow, contrary, literature, generous, sensitive","Great is the Lord, and greatly to be praised; and his greatness is unsearchable.","Psalm 145:3"),
    (50,5,9.99,"Sagittarius","DANIEL","FURCAS","Consolation, decisions, justice, merciful, industrious, literature, eloquent","The Lord is gracious, and full of compassion; slow to anger, and of great mercy.","Psalm 145:8"),
    (51,10,14.99,"Sagittarius","HAHASIAH","BALAM (BALAAM)","Occultism, physics, natural philosophy, medicine, alchemy","The glory of the Lord shall endure forever: the Lord shall rejoice in his works.","Psalm 104:31"),
    (52,15,19.99,"Sagittarius","IMAMIAH","ALLOCES (ALOCAS)","Destroys enemies, vigor, research, voyages, protection, liberty, stoic","I will praise the Lord according to his righteousness: and will sing praise to the name of the Lord most high.","Psalm 7:17"),
    (53,20,24.99,"Sagittarius","NANAEL","CAMIO (CAIM)","Enlightenment, higher sciences, law, melancholy humor, private, retired","I know, O Lord, that thy judgments are right, and that thou in faithfulness hast afflicted me.","Psalm 119:75"),
    (54,25,29.99,"Sagittarius","NITHAEL","MURMUS (MURMUR)","Mercy, longevity, stability, writer, eloquent, learned","The Lord hath prepared his throne in the heavens; and his kingdom ruleth over all.","Psalm 103:19"),
    (55,0,4.99,"Capricorn","MABAIAH (MEBAHAIAH)","OROBAS","Consolation, fertility, religion, piety, morality","But thou, O Lord, shall endure forever; and thy remembrance unto all generations.","Psalm 102:12"),
    (56,5,9.99,"Capricorn","POIEL","GREMORY (GAMORI)","Wishes, fame, fortune, modest, agreeable, talented","The Lord upholdeth all that fall, and raiseth up all those that be bowed down.","Psalm 145:14"),
    (57,10,14.99,"Capricorn","NEMAMIAH","OSO (OSE)","Prosperity, warfare, delivers prisoners, active, brave, stoic","Ye that fear the Lord, trust in the Lord: he is their help and their shield.","Psalm 115:11"),
    (58,15,19.99,"Capricorn","IEIALEL","AVNAS (AMY)","Against troubles, eyesight, iron, locksmiths, bravery, bold, commerce","My soul is also sore vexed: but thou, O Lord, how long?","Psalm 6:3"),
    (59,20,24.99,"Capricorn","HARAEL (HARAHEL)","ORIAS (ORIAX)","Fertility, helps with problem children, treasures, business acumen, talented","From the rising of the sun unto the going down of the same the Lord's name is to be praised.","Psalm 113:3"),
    (60,25,29.99,"Capricorn","MITZRAEL (MIZRAEL)","NAPHULA (VAPULA)","Spiritual and mental health, against persecution, virtue, talents, humor, longevity","The Lord is righteous in all his ways, and holy in all his works.","Psalm 145:17"),
    (61,0,4.99,"Aquarius","UMABEL (VMABEL)","ZAGAN","Friendship, astronomy, physics, sensitive heart in love, travels, pleasures","Blessed be the name of the Lord from this time forth and for evermore.","Psalm 113:2"),
    (62,5,9.99,"Aquarius","IAHHEL (IAHHAEL)","VALU (VOLAC)","Wisdom, knowledge, philosophy, tranquility, solitude, modest, virtuous","Consider how I love thy precepts: quicken me, O Lord, according to thy lovingkindness.","Psalm 119:159"),
    (63,10,14.99,"Aquarius","ANAVEL","ANDRAS","Against accidents, health, trade and business, banks, ingenious, industrious","Serve the Lord with gladness: come before his presence with singing.","Psalm 100:2"),
    (64,15,19.99,"Aquarius","MEHIEL","HAURES (FLAUROS)","Against rabies and dangerous animals, oration, teacher, author, literature","Behold, the eye of the Lord is upon them that fear him, upon them that hope in his mercy.","Psalm 33:18"),
    (65,20,24.99,"Aquarius","DAMABIAH","ANDREALPHUS","Against sorcery, wisdom, sailors, water, expeditions, wealth","Return, O Lord, how long? and let it repent thee concerning thy servants.","Psalm 90:13"),
    (66,25,29.99,"Aquarius","MANAKEL","KIMARIS (CIMERIES)","Against leprosy and anger, vegetation, dreams, sweet, pleasant","Forsake me not, O Lord: O my God, be not far from me.","Psalm 38:21"),
    (67,0,4.99,"Pisces","EIAEL","AMDUKIAS (AMDUSIAS)","Against adversity, wisdom, change, occultism, solitude, mysticism","Delight thyself also in the Lord: and he shall give thee the desires of thine heart.","Psalm 37:4"),
    (68,5,9.99,"Pisces","CHABUIAH (HABUIAH)","BELIAL","Cures disease, health, fertility, agriculture, rural","Praise ye the Lord. O give thanks unto the Lord; for he is good: for his mercy endureth forever.","Psalm 106:1"),
    (69,10,14.99,"Pisces","ROEHEL","DECARABIA","Finds stolen goods, law, fame, morality, customs","The Lord is the portion of mine inheritance and of my cup: thou maintainest my lot.","Psalm 16:5"),
    (70,15,19.99,"Pisces","IABAMIAH (JABAMIAH)","SEERE (SEIR)","Regeneration, inner harmony, philosophy, genius, spiritual protection","In the beginning God created the heaven and the earth.","Genesis 1:1"),
    (71,20,24.99,"Pisces","HAIAIEL (HAIEL)","DANTALION","Confounds evil, victory, weapons, iron, bravery, protection, fire","I will greatly praise the Lord with my mouth; yea, I will praise him among the multitude.","Psalm 109:30"),
    (72,25,29.99,"Pisces","MUMIAH","ANDROMALIUS","Happy conclusions, medicine, longevity, success, helps the poor and infirm","Return unto thy rest, O my soul; for the Lord hath dealt bountifully with thee.","Psalm 116:7"),
]

# === GERALD KOMBO'S NATAL QUINARIES ===
NATAL_QUINARIES = {
    "Ascendant": 63,   # Anavel/Andras - Angel of the Nativity
    "Sun": 35,         # Chavakiah/Marchosias
    "Moon": 64,        # Mehiel/Haures
    "Mercury": 39,     # Rehael/Malphas
    "Venus": 43,       # Veualiah/Sabnock
    "Mars": 36,        # Menadel/Stolas
    "Jupiter": 20,     # Pahaliah/Purson
    "Saturn": 56,      # Poiel/Gremory
    "Uranus": 55,      # Mabaiah/Orobas
    "Neptune": 56,     # Poiel/Gremory
    "Pluto": 45,       # Sealiah/Vine
    "N.Node": 65,      # Damabiah/Andrealphus
    "Chiron": 12,      # Hahaiah/Sitri
}

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

def get_quinary(ecliptic_lon):
    """Return quinary number (1-72) for a given ecliptic longitude (0-360)."""
    lon = ecliptic_lon % 360
    return int(lon / 5) + 1

def get_quinary_data(qnum):
    """Return the quinary entry for a given number (1-72)."""
    for q in QUINARIES:
        if q[0] == qnum:
            return q
    return None

def _load_ephe():
    from skyfield.api import load
    ts = load.timescale(builtin=True)
    bsp_path = os.path.join(ROOT, "ephe", "de421.bsp")
    if os.path.exists(bsp_path):
        planets = load(bsp_path)
    else:
        print("  Ephemeris not found. Downloading...")
        os.makedirs(os.path.join(ROOT, "ephe"), exist_ok=True)
        planets = load("de421.bsp")
    earth = planets["earth"]
    return ts, planets, earth

def _get_sun_lon(t, earth, planets):
    astro = earth.at(t).observe(planets["sun"])
    _, lon, _ = astro.ecliptic_latlon()
    return float(lon.degrees)

def get_current_quinary():
    try:
        ts, planets, earth = _load_ephe()
        now = datetime.now(timezone.utc)
        t = ts.utc(now.year, now.month, now.day, now.hour, now.minute)
        lon = _get_sun_lon(t, earth, planets)
        return get_quinary(lon)
    except Exception as e:
        print(f"  Skyfield error: {e}")
        now = datetime.now(timezone.utc)
        doy = now.timetuple().tm_yday
        approx_lon = (doy - 79) * 0.9856
        if approx_lon < 0: approx_lon += 360
        return get_quinary(approx_lon)

def equinoctial_hour_range(qnum):
    """Return the equinoctial hour range for a quinary (1-72)."""
    start_min = (qnum - 1) * 20
    start_h = start_min // 60
    start_m = start_min % 60
    end_min = qnum * 20
    end_h = end_min // 60
    end_m = end_min % 60
    return (start_h, start_m), (end_h, end_m)

def format_hour(h, m):
    ampm = "AM" if h < 12 or h == 24 else "PM"
    h12 = h % 12
    if h12 == 0: h12 = 12
    return f"{h12}:{m:02d} {ampm}"

# === ICS GENERATION ===
def generate_ics(years=10):
    """
    Generate comprehensive ICS calendar with:
    - Annual quinarian weeks (~5-day periods when sun is in each quinary)
    - Natal quinary daily hours (the 20-min windows for Gerald's key quinaries)
    - All events with VALARM notifications
    """
    ts, planets, earth = _load_ephe()
    
    now = datetime.now(timezone.utc)
    start_year = now.year
    end_year = start_year + years
    
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Quinarian Engine//v1//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Quinarian Astrology - The 72 Keys",
        "X-WR-TIMEZONE:UTC",
        "X-APPLE-CALENDAR-COLOR:#1E88E5",
    ]
    
    uid = 0
    event_count = 0
    
    # Compute solar position every 5 days to find quinary transitions
    print("  Computing solar quinaries across years...")
    
    for year in range(start_year, end_year + 1):
        # Find when sun enters each quinary (approximate)
        for qnum in range(1, 73):
            q = get_quinary_data(qnum)
            if not q: continue
            _, start_deg, end_deg, sign, angel, demon, attrs, psalm, psalm_ref = q
            
            # Approximate mid-point of quinary
            mid_deg = (start_deg + end_deg) / 2 + SIGNS.index(sign) * 30
            
            # Approximate date when sun is at this longitude
            # Sun moves ~0.9856 deg/day from vernal equinox
            # Vernal equinox ~ March 20 (~day 79)
            day_of_year = 79 + mid_deg / 0.9856
            if day_of_year > 365: day_of_year -= 365
            
            # Create date
            from datetime import date
            d = date(year, 1, 1) + timedelta(days=int(day_of_year) - 1)
            
            # Duration: ~5 days per quinary
            start_dt = datetime(d.year, d.month, d.day, 0, 0, tzinfo=timezone.utc)
            end_dt = start_dt + timedelta(days=5)
            
            uid += 1
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:quinary-week-{uid:04d}@quinarian")
            lines.append(f"DTSTART;VALUE=DATE:{start_dt.strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{end_dt.strftime('%Y%m%d')}")
            lines.append(f"SUMMARY:Q{qnum} {sign} {angel}/{demon}")
            lines.append(f"DESCRIPTION:Quinary {qnum} ({start_deg}-{end_deg} {sign})\\nAngel: {angel}\\nDemon: {demon}\\nAttributes: {attrs}\\nPsalm: {psalm_ref} - {psalm}")
            lines.append(f"X-APPLE-CALENDAR-COLOR:#1E88E5")
            # 1 day before alert
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-PT1440M")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:Tomorrow: Q{qnum} {angel} begins")
            lines.append("END:VALARM")
            lines.append("END:VEVENT")
            event_count += 1
            
            # Also create preparation alert 3 hours into the quinary
            uid += 1
            prep_dt = start_dt + timedelta(hours=3)
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:quinary-prep-{uid:04d}@quinarian")
            lines.append(f"DTSTART:{prep_dt.strftime('%Y%m%dT%H%M%S')}Z")
            lines.append(f"DTEND:{(prep_dt+timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')}Z")
            lines.append(f"SUMMARY:[PREP] Q{qnum} {angel} - recite Psalm")
            lines.append(f"DESCRIPTION:Quinary {qnum} is active. Angel: {angel}. Demon: {demon}. Recite: {psalm_ref}")
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-PT15M")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:15 min until Q{qnum} {angel} prep window")
            lines.append("END:VALARM")
            lines.append("END:VEVENT")
            event_count += 1
    
    # === DAILY QUINARIAN HOURS FOR KEY NATAL QUINARIES ===
    print(f"  Adding daily quinarian hours for natal placements...")
    
    natal_labels = {
        63: "Ascendant (Anavel/Andras) - ANGEL OF THE NATIVITY",
        35: "Sun (Chavakiah/Marchosias)",
        64: "Moon (Mehiel/Haures)",
        39: "Mercury (Rehael/Malphas)",
        43: "Venus (Veualiah/Sabnock)",
        36: "Mars (Menadel/Stolas)",
        56: "Saturn+Neptune (Poiel/Gremory)",
        20: "Jupiter (Pahaliah/Purson)",
        55: "Uranus (Mabaiah/Orobas)",
        45: "Pluto (Sealiah/Vine)",
        65: "N.Node (Damabiah/Andrealphus)",
    }
    
    for days_ahead in range(0, 365 * years, 1):
        check_date = now + timedelta(days=days_ahead)
        
        # Only add events for today through next 90 days (to keep file manageable)
        if days_ahead > 90:
            # Add weekly batches for the rest
            if days_ahead % 7 != 0:
                continue
        
        for qnum, label in natal_labels.items():
            (s_h, s_m), (e_h, e_m) = equinoctial_hour_range(qnum)
            
            start_dt = datetime(check_date.year, check_date.month, check_date.day, 
                               s_h, s_m, 0, tzinfo=timezone.utc)
            end_dt = datetime(check_date.year, check_date.month, check_date.day,
                             e_h, e_m, 0, tzinfo=timezone.utc)
            
            # Quinary 72 ends at midnight next day
            if qnum == 72:
                end_dt = end_dt + timedelta(days=1)
            
            q = get_quinary_data(qnum)
            if not q: continue
            _, sd, ed, sign, angel, demon, attrs, psalm, psalm_ref = q
            
            uid += 1
            lines.append("BEGIN:VEVENT")
            lines.append(f"UID:quinary-hour-{uid:04d}@quinarian")
            lines.append(f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}Z")
            lines.append(f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}Z")
            lines.append(f"SUMMARY:NATAL {label}")
            lines.append(f"DESCRIPTION:Q{qnum} ({sd}-{ed} {sign}) - {angel} ({demon})\\nAttributes: {attrs}\\nPsalm: {psalm_ref}")
            lines.append(f"X-APPLE-CALENDAR-COLOR:#FF6F00")
            # Alert 30 min before
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-PT30M")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:30 min until {angel} hour - prepare")
            lines.append("END:VALARM")
            # Alert 5 min before
            lines.append("BEGIN:VALARM")
            lines.append("TRIGGER:-PT5M")
            lines.append("ACTION:DISPLAY")
            lines.append(f"DESCRIPTION:{angel} hour now! Recite {psalm_ref}")
            lines.append("END:VALARM")
            lines.append("END:VEVENT")
            event_count += 1
    
    lines.append("END:VCALENDAR")
    
    with open(ICS_PATH, "w", encoding="utf-8") as f:
        f.write("\r\n".join(lines) + "\r\n")
    
    size_kb = os.path.getsize(ICS_PATH) / 1024
    print(f"\n  Generated: {ICS_PATH}")
    print(f"  Events: {event_count}")
    print(f"  Size: {size_kb:.0f} KB")
    return True

def cmd_now():
    """Show current quinary status."""
    try:
        current_q = get_current_quinary()
    except Exception as e:
        print(f"  Skyfield error: {e}")
        print("  Using approximate calculation instead.")
        now = datetime.now(timezone.utc)
        # Approximate: March 20 = day 79, sun moves 0.9856 deg/day
        doy = now.timetuple().tm_yday
        approx_lon = (doy - 79) * 0.9856
        if approx_lon < 0: approx_lon += 360
        current_q = get_quinary(approx_lon)
    
    q = get_quinary_data(current_q)
    if not q:
        print("  Error: quinary not found")
        return
    
    _, sd, ed, sign, angel, demon, attrs, psalm, psalm_ref = q
    (sh, sm), (eh, em) = equinoctial_hour_range(current_q)
    
    print(f"\n{'='*56}")
    print(f"  CURRENT QUINARY STATUS")
    print(f"{'='*56}")
    print(f"  Quinary:    #{current_q}")
    print(f"  Degrees:    {sd}-{ed} {sign}")
    print(f"  Angel:      {angel}")
    print(f"  Demon:      {demon}")
    print(f"  Attributes: {attrs}")
    print(f"  Hour:       {format_hour(sh, sm)} - {format_hour(eh, em)} (equinoctial)")
    print(f"  Psalm:      {psalm_ref}")
    print(f"  \"{psalm}\"")
    print()
    
    # Show natal connections
    print(f"  NATAL CONNECTIONS:")
    for planet, qnum in NATAL_QUINARIES.items():
        if qnum == current_q:
            nq = get_quinary_data(qnum)
            print(f"    >>> {planet}: Q{qnum} {nq[3]} - {nq[4]}/{nq[5]}")
    print()
    
    # Show if this quinary is for a natal planet
    print(f"  PREPARATION:")
    print(f"    - Recite {psalm_ref} during this quinary")
    print(f"    - Light a candle for {angel}")
    print(f"    - Focus on: {attrs}")
    print()

def cmd_daemon():
    """Daemon mode - watches current quinary and alerts."""
    print(f"\n  Quinarian Watch Daemon starting...")
    print(f"  Checking every 10 minutes.")
    print(f"  Press Ctrl+C to stop.\n")
    
    last_q = None
    
    while True:
        try:
            current_q = get_current_quinary()
        except:
            time.sleep(60)
            continue
        
        if current_q != last_q:
            q = get_quinary_data(current_q)
            if q:
                _, sd, ed, sign, angel, demon, attrs, psalm, psalm_ref = q
                (sh, sm), (eh, em) = equinoctial_hour_range(current_q)
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
                
                print(f"\n[{now}] QUINARY CHANGE")
                print(f"  Now in Q{current_q} ({sd}-{ed} {sign})")
                print(f"  Angel: {angel} | Demon: {demon}")
                print(f"  Hour: {format_hour(sh, sm)} - {format_hour(eh, em)}")
                print(f"  Recite: {psalm_ref}")
                
                # Check natal connections
                for planet, qnum in NATAL_QUINARIES.items():
                    if qnum == current_q:
                        print(f"  *** {planet} NATAL QUINARY ACTIVE ***")
                
                print()
            last_q = current_q
        
        time.sleep(600)  # 10 min

def cmd_deploy(folder):
    """Copy ICS to a sync folder for Google Calendar / watch."""
    if not os.path.exists(ICS_PATH):
        print(f"  ICS not found. Run 'python quinarian_engine.py ics' first.")
        return
    if not os.path.exists(folder):
        print(f"  Target folder not found: {folder}")
        return
    dest = os.path.join(folder, "quinarian_calendar.ics")
    shutil.copy2(ICS_PATH, dest)
    print(f"  Deployed to: {dest}")
    print(f"  Size: {os.path.getsize(dest)} bytes")
    print(f"\n  To sync to Google Calendar:")
    print(f"    1. Open https://calendar.google.com")
    print(f"    2. Settings -> Import & Export -> Import")
    print(f"    3. Select: {dest}")
    print(f"    4. For smart watch: install Google Calendar app")
    print(f"       and enable notifications for imported calendar.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "ics":
        generate_ics()
    elif cmd == "now":
        cmd_now()
    elif cmd == "daemon":
        cmd_daemon()
    elif cmd == "deploy":
        if len(sys.argv) < 3:
            print("Usage: python quinarian_engine.py deploy /path/to/sync/folder")
        else:
            cmd_deploy(sys.argv[2])
    else:
        print(__doc__)
