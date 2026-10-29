# MAZZAROTH v3 — LOVABLE BUILD PROMPT

> **Author:** Gerald Kombo  
> **Purpose:** Rebuild the complete Mazzaroth astrological transit engine in Lovable  
> **Constraint:** Lovable only — no external APIs, no external AI, no external astrology services  
> **Data input:** This folder contains all source code, CSV databases, ICS calendars, and context files

---

## 1. PERSONAL DATA — Gerald Kombo

```
Name:       Gerald Kombo
Born:       September 13, 1989, 03:50 UTC
Location:   Aga Khan Parklands Hospital, Nairobi, Kenya
Coordinates: 1°16'S, 36°49'E
```

### Natal Chart (Hardcoded Longitudes)

| Body      | Longitude | Latitude  | Declination |
|-----------|-----------|-----------|-------------|
| Sun       | 170.4843° | 0.0000°   | 3.7704°     |
| Moon      | 318.5855° | -0.6646°  | -15.8878°   |
| Mercury   | 190.6142° | -4.0613°  | -7.9358°    |
| Venus     | 210.8920° | -0.7001°  | -12.4403°   |
| Mars      | 175.9804° | 0.8870°   | 2.4119°     |
| Jupiter   | 97.7781°  | -0.2931°  | 22.9183°    |
| Saturn    | 277.4451° | 0.4797°   | -22.7511°   |
| Uranus    | 271.4826° | -0.2721°  | -23.7031°   |
| Neptune   | 279.7679° | 0.9015°   | -22.1805°   |
| Pluto     | 223.2569° | 15.3646°  | -1.1315°    |
| N.Node    | 324.4188° | 0.0000°   | 0.0000°     |
| Chiron    | 57.2745°  | -2.9884°  | 0.0000°     |

### Profection House
Age 36 → Profection House = ((36 % 13) + 1) = **H11**

---

## 2. FATHER'S PASSING — For Quinarian / Grief Context

```
Name:       [Father of Gerald Kombo]
Born:       July 5, 1955 — Nairobi, Kenya
Passed:     July 13, 2026, 11:30 PM — Nairobi West Hospital, Nairobi, Kenya
Funeral:    July 23, 2026
Burial:     July 24, 2026
```

### Father's Natal Sun
- **12.7° Cancer → 21st Quinary** (10°–14°59' Cancer)
- **Angel:** NELCHAEL ("against slander, astronomy, mathematics, geography, poetry")
- **Demon:** MARAX (Morax) ("astronomy, herbs, stones, arts and sciences")
- **Psalm 31:14:** *"But I trusted in thee, O Lord: I said, Thou art my God."*

### Father's Passing Moment (July 13, 2026, 11:30 PM EAT = 20:30 UTC)
- **Ascendant:** 6.0° Capricorn → **56th Quinary** — Angel POIEL, Demon GREMORY
- **Sun:** 21.5° Cancer → **23rd Quinary** — Angel MELAHEL, Demon AIM
- **Moon:** 13.7° Capricorn → **57th Quinary** — Angel NEMAMIAH, Demon OSO

### Father-Daughter Synastry Link
- Gerald's **Saturn + Neptune** are both in the **56th Quinary** (Poiel/Gremory)
- Father passed with **56th Quinary on Ascendant**
- This is the ancestral link — father's soul completion echoes Gerald's life foundation

---

## 3. SYSTEM ARCHITECTURE

### 3.1 Core Engine (`mazzaroth.py`)
- **Ephemeris:** JPL DE421 (provided as `ephe/de421.bsp` — 16MB, excluded from zip)
- **Library:** Skyfield (pure Python, no compilation)
- **Bootstrap:** Load `de421.bsp` once, cache planetary positions
- **12 bodies:** Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, N.Node, Chiron
- **Chiron:** Compute via Kepler orbit (heliocentric → geocentric) — code provided in original
- **North Node:** Mean lunar node formula — code provided in original

### 3.2 Aspect Detection
- **10 major aspects:** Conj (0°), Opp (180°), Sq (90°), Tri (120°), Sxt (60°), Qnx (150°), SSq (45°), SqSq (135°), Qnt (72°), BQnt (144°)
- **Declination parallels** (orb 1.0°)
- **Antiscia** (orb 1.5°)
- Each aspect has: angle, orb, base_score, name

### 3.3 Scoring Formula
```
score = base_weight * transit_planet_weight * natal_planet_weight 
        * house_weight * motion_multiplier * precision_multiplier * retrograde_multiplier
```

**Weights:**
| Planet   | Weight |
|----------|--------|
| Pluto    | 4.0    |
| Neptune  | 3.5    |
| Uranus   | 3.0    |
| Saturn   | 2.5    |
| Jupiter  | 2.0    |
| N.Node   | 1.8    |
| Chiron   | 1.5    |
| Mars     | 1.5    |
| Sun      | 1.5    |
| Mercury  | 1.2    |
| Venus    | 1.2    |
| Moon     | 1.0    |

**House weights:** H1=2.0, H4=2.0, H7=2.0, H10=2.0, H2=1.5, H5=1.5, H8=1.5, H11=1.5, rest=1.0

**Motion multiplier:** <5% mean speed = 5.0, <25% = 2.0, else 1.0

**Precision:** delta < 0.1° = 3.0, < 0.5° = 2.0, else 1.0

**Retrograde multiplier:** 1.5 if retrograde

### 3.4 Thresholds (for classifying transit intensity)
- Computed by scanning 2026-03-17 to 2036-12-31
- **PEAK**      > 95th percentile (>11675)
- **VERY HIGH**  > 90th percentile (>10806)
- **HIGH**       > 75th percentile (>9480)

### 3.5 Constellation-Based House System (13 Houses)
Using IAU constellation boundaries:
```
Pisces (0-27°), Aries (27-53.5°), Taurus (53.5-90.4°), Gemini (90.4-118.1°),
Cancer (118.1-138.2°), Leo (138.2-174°), Virgo (174-218°), Libra (218-241°),
Scorpius (241-248°), Ophiuchus (248-266.5°), Sagittarius (266.5-300°),
Capricornus (300-327.5°), Aquarius (327.5-360°)
```

**House number:** `(constellation_index_of_planet - constellation_index_of_natal_sun) % 13 + 1`

### 3.6 13 Life Areas
| H   | Area |
|-----|------|
| 1   | Identity, Self-Image, Personal Brand |
| 2   | Finances, Values, Self-Worth |
| 3   | Communication, Siblings, Writing |
| 4   | Home, Family, Roots, Emotional Foundation |
| 5   | Creativity, Romance, Children, Pleasure |
| 6   | Health, Daily Work, Routines, Service |
| 7   | Partnerships, Marriage, Contracts |
| 8   | Sex, Intimacy, Shared Resources, Transformation |
| 9   | Philosophy, Travel, Higher Education, Publishing |
| 10  | Career, Reputation, Public Life, Legacy |
| 11  | Friends, Networks, Community, Hopes |
| 12  | Solitude, Spirituality, Retreat, Subconscious |
| 13  | Ophiuchus — Healing, Higher Service, Synthesis |

House cusps computed from constellation boundaries so ALL 13 areas score even without natal planets.

---

## 4. COMMAND-LINE INTERFACE — `mazz.py`

| Command | Description |
|---------|-------------|
| `python mazz.py now` | Current transit score + active aspects |
| `python mazz.py today` | Full day briefing |
| `python mazz.py week` | 7-day forecast |
| `python mazz.py watch` | Daemon mode (checks every 30 min) |
| `python mazz.py search YYYY-MM-DD` | Look up date in 10-year CSV database |
| `python mazz.py thresholds` | Compute and cache score thresholds |
| `python mazz.py relationship` | Relationship & sex transits |
| `python mazz.py areas` | All 13 life areas by intensity |
| `python mazz.py transits` | All active transits mapped to life areas |
| `python mazz.py month` | 30-day transit outlook |
| `python mazz.py brief` | Strategic Daily Brief (transit synthesis) |
| `python mazz.py wealth` | Wealth Optimizer — financial astrology briefing |
| `python mazz.py wealth calendar` | 60-day financial calendar |
| `python mazz.py wealth pattern` | Billionaire wealth blueprint |
| `python mazz.py wealth invest` | Investment timing analysis |
| `python mazz.py audit` | Ground Truth audit status |
| `python mazz.py audit rate 1-5 tag` | Rate today's outcome (1-5) |
| `python mazz.py audit history` | Audit log |
| `python mazz.py audit regression` | Hit-rate regression analysis |
| `python mazz.py ics generate` | Regenerate ICS calendar |
| `python mazz.py ics deploy FOLDER` | Deploy ICS to sync folder |
| `python mazz.py quinarian` | Current quinarian status |
| `python mazz.py quinarian daemon` | Quinarian watch daemon (10-min checks) |
| `python mazz.py quinarian ics` | Generate quinarian ICS calendar |
| `python mazz.py quinarian deploy FOLDER` | Deploy quinarian ICS |
| `python mazz.py optimize` | Bayesian weight optimization from audit log |
| `python mazz.py --user NAME ...` | Multi-subject routing |

---

## 5. MODULES

### 5.1 `mazzaroth.py` — Core Engine
- Ephemeris loading & caching
- Transit computation for all 12 bodies
- Scoring engine with full aspect detection
- Threshold computation (scan 10 years)
- CSV database lookup (master log)
- T-Rex 2 memo formatting
- PEAK alert sound on Windows

### 5.2 `mazzaroth_life_areas.py` — Life Areas & Interpretations
- 13 life areas mapped to houses
- Relationship (H7) and Sex (H8) interpretations per planet
- Wealth/career (H2, H10) interpretations
- Health (H6), Home (H4), Romance (H5), Spirituality (H12) interpretations
- House cusp computation
- Area scoring with transit-to-cusp activation

### 5.3 `transit_combiner.py` — Strategic Daily Brief
- Multi-transit narrative synthesis
- Tone classification: supportive / challenging / mixed-tension / neutral
- Planet archetypes and aspect styles for natural language

### 5.4 `wealth_optimizer.py` — Financial Astrology
- Wealth score (0-1000) focusing on H2, H8, H10
- 8 billionaire wealth patterns
- Investment timing with Mercury retrograde checks
- 60-day financial forecast

### 5.5 `execution_audit.py` — Ground Truth
- Auto-logs PEAK/VH/HIGH predictions to CSV
- Rate outcomes (1-5) with tags
- Hit-rate regression by planet, house, level
- CSV files: `execution_audit.csv`, `predictions_log.csv`

### 5.6 `optimizer.py` — Bayesian Weight Optimization
- Reads audit log
- Beta-Bernoulli update on planet weights
- Requires 10+ audit entries
- Outputs to `ephe/weights_optimized.json`

### 5.7 `quinarian_engine.py` — Shem Angel / Goetia Calendar
- Complete table of 72 quinaries (quinary#, degrees, sign, angel, demon, attributes, psalm)
- Gerald's natal quinaries for all 12 planets + Ascendant
- Current quinary computation (solar position → quinary number)
- Equinoctial hour range per quinary (20-min windows, 72 × 20 = 1440 min)
- ICS generation with VALARM notifications
- Daemon mode for quinary change alerts

### 5.8 `ics_auto_deploy.py` — ICS Management
- Regenerate `mazzaroth_exact.ics` from CSV database
- Deploy to sync folder for mobile calendar

### 5.9 `mazzaroth_web.py` — Web Dashboard
- HTTP server on port 8080
- JSON API at `/api/data` and `/api/areas`
- Auto-refresh every 30 seconds
- Score gauge, active aspects, planet positions, 7-day forecast, PEAK calendar
- Push notifications via Windows Toast

### 5.10 `zepp_auto_sync.py` / `zepp_correlate.py` — Health Data Integration
- Watches `Zepp_Exports/` folder for new CSV files
- Merges Zepp health data with transit scores
- Correlation analysis

### 5.11 `trex2_sync.py` — Calendar & Watch Sync
- ICS sync for Amazfit T-Rex 2 watch
- 986 events (2026-2036) in `mazzaroth_exact.ics`

### 5.12 `generate_daily_data.py` / `generate_master_log.py` / `build_csvs_from_master.py` / `build_organized_package.py`
- Data generation and packaging utilities

### 5.13 `hourly_monitor.py` — Real-time PEAK Alert
- Checks transit score every hour
- Sends Windows Toast notification for PEAK events

### 5.14 `watchdog.ps1` — Self-Healing
- PowerShell watchdog with 60s cycle
- Auto-restarts daemon + dashboard
- Memory leak detection at 200MB

---

## 6. DATA FILES

### 6.1 Calendar Files (Include in Build)
- `mazzaroth_exact.ics` — 986 transit events (2026-2036)
- `quinarian_calendar.ics` — Full 72 quinaries with VALARM alerts

### 6.2 CSV Databases
- `Mazzaroth_Engine_Data/mazzaroth_master_log.csv` — 3944 events (2026-2036)
- `Mazzaroth_Engine_Data/execution_audit.csv` — Outcome ratings
- `Mazzaroth_Engine_Data/predictions_log.csv` — Auto-logged predictions
- `Mazzaroth_Engine_Data/high_leverage_windows.csv` — Top 50 days

### 6.3 Ephemeris (External / Excluded from Zip)
- `ephe/de421.bsp` — JPL DE421 (16MB) — user must download separately or use included
- `ephe/weights.json` — Planet weights

### 6.4 Reading Files (Include)
- `dad_quinarian_reading.md` — Quinarian reading for Gerald's father
- `gerald_quinarian_reading.md` — Quinarian reading for Gerald Kombo

---

## 7. KEY DESIGN RULES

1. **PURE PYTHON** — No C compiler needed. No `pyswisseph`. Use `skyfield` + DE421.
2. **WINDOWS COMPATIBLE** — cp1252 safe (no `°` symbol, use `deg`). US English.
3. **HARDCODED NATAL** — Gerald Kombo's chart hardcoded for instant startup.
4. **NO NETWORK DEPENDENCY** — Once DE421 is downloaded, everything runs offline.
5. **13 CONSTELLATIONS** — Include Ophiuchus in the house system.
6. **CHIRON** — Compute via Kepler orbit (heliocentric → geocentric), not from ephemeris.
7. **N. NODE** — Mean lunar node formula, not from ephemeris.
8. **HOUSE CUSPS** — Enable scoring ALL 13 life areas even without natal planets.
9. **AUDIT LOOP** — Predict → Rate → Optimize cycle for self-improvement.
10. **ICS GENERATION** — Calendar files must have VALARM notifications for watch sync.

---

## 8. BUILD INSTRUCTIONS FOR LOVABLE

1. Install Python 3.9+
2. `pip install skyfield`
3. Download `de421.bsp` from JPL or use included file in `ephe/`
4. Run `python mazz.py thresholds` to compute initial thresholds (~2 min for 10 years)
5. Run `python mazz.py now` to test

### Files to Generate (if missing):
- `python mazz.py ics generate` — Regenerate `mazzaroth_exact.ics`
- `python quinarian_engine.py ics` — Regenerate `quinarian_calendar.ics`

### To Run Daemon:
```
python mazz.py watch                    # Transit watch (30-min cycle)
python mazz.py quinarian daemon         # Quinarian watch (10-min cycle)
python mazzaroth_web.py                 # Web dashboard on :8080
```

---

## 9. EXAMPLE OUTPUT

```
MAZZAROTH — 2026-07-23 12:00 UTC  |  Profection: H11
========================================================
  Score: 2845  |  Level: NORMAL  |  Thresholds: PEAK>11675 VH>10806 H>9480

  Active Aspects:
    Pluto Opp natal Sun (0.023deg)                                      3845.0
    Saturn Sq natal Moon (0.112deg)                                     2120.0
    Jupiter Tri natal Venus (0.456deg)                                   980.0

  Top Transit: Pluto Opp natal Sun
  House: H6
  Strategy: Network restructuring. Power connections.
  Actions:
    -> Cut shallow connections
    -> Reach out to 5 key people
    -> Join mission-aligned community

  T-Rex 2 Memo:
  "PEAK 07-23 | Pluto->Sun H6 | Network restructuring. Power connections."
```

---

## 10. DELIVERABLES CHECKLIST

- [ ] `mazzaroth.py` — Core engine with all 12 bodies, aspects, scoring
- [ ] `mazz.py` — Full CLI with all commands
- [ ] `mazzaroth_life_areas.py` — 13 life areas with interpretations
- [ ] `transit_combiner.py` — Strategic Daily Brief synthesis
- [ ] `wealth_optimizer.py` — Financial astrology engine
- [ ] `execution_audit.py` — Ground Truth audit layer
- [ ] `optimizer.py` — Bayesian weight optimization
- [ ] `quinarian_engine.py` — 72 quinaries with ICS generation
- [ ] `ics_auto_deploy.py` — ICS calendar management
- [ ] `mazzaroth_web.py` — Web dashboard
- [ ] `trex2_sync.py` — Watch sync
- [ ] `zepp_auto_sync.py` / `zepp_correlate.py` — Health data integration
- [ ] `generate_daily_data.py` — Daily data generation
- [ ] `generate_master_log.py` — Master log builder
- [ ] `hourly_monitor.py` — Hourly PEAK alerts
- [ ] `watchdog.ps1` — Self-healing script
- [ ] `dad_quinarian_reading.md` — Father's quinarian reading
- [ ] `gerald_quinarian_reading.md` — Gerald's quinarian reading
- [ ] `MAZZAROTH_CONTEXT.md` — System context documentation
- [ ] `MAZZAROTH_DAILY_READINGS.md` — Daily readings documentation
- [ ] `mazzaroth_exact.ics` — 986 transit events calendar
- [ ] `quinarian_calendar.ics` — 72 quinaries calendar
- [ ] `Mazzaroth_Engine_Data/mazzaroth_master_log.csv` — 3944 master events
- [ ] `Mazzaroth_Engine_Data/execution_audit.csv` — Audit log
- [ ] `Mazzaroth_Engine_Data/predictions_log.csv` — Predictions log
- [ ] `Mazzaroth_Engine_Data/high_leverage_windows.csv` — Top 50 windows
- [ ] `ephe/weights.json` — Planet weights

---

## 11. FOR LOVABLE — CRITICAL NOTES

- **This is for Gerald Kombo ONLY.** Personalized natal chart, life areas, wealth patterns, and quinarian readings are tied to this specific birth data.
- **Daily readings must be exact and accurate.** Use the provided CSV database for pre-computed events; real-time computation for current positions.
- **Include all ICS calendar files.** These drive the smart watch notifications (Amazfit T-Rex 2).
- **Father's quinarian reading is included** as a record of his passing — this can be displayed during funeral/burial periods.
- **No external dependencies** beyond Skyfield + DE421. Lovable must generate all interpretations, strategies, and intelligence internally.
- **Do not modify the natal chart data.** This is Gerald's chart and must remain exactly as specified.
- **The 72 quinaries table** in `quinarian_engine.py` must remain complete and unmodified — it is sourced from *The Astrological Goetia* by Jaime Paul Lamb.

---

*Build complete. May the stars guide the work.*
