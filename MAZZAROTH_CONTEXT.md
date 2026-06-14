# Mazzaroth v3 — System Context for AI Assistants

## Overview
Production-grade astrological transit engine using Skyfield + JPL DE421 ephemeris. Pure Python, no C compiler needed. Runs on Windows/PowerShell. Closed-loop: predicts transits, logs real-world outcomes, self-tunes weights via Bayesian update.

## Architecture

### Core Engine (`mazzaroth.py`)
- Ephemeris: Skyfield + JPL DE421 (16MB .bsp file)
- Natal chart: Gerald Kombo, 1989-09-13 03:50 UTC, Nairobi
- 12 bodies: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, N.Node, Chiron
- Chiron via Kepler orbit (heliocentric->geocentric), mean lunar node formula
- Aspect detection: longitude (10 aspects) + declination (parallel) + antiscia
- Scoring: base weight * planet_weight * natal_weight * house_weight * motion_mult * precision
- Thresholds: PEAK>3100, VERY HIGH>2800, HIGH>2400 (cached in ephe/thresholds.json)
- Constellation-based house system: 13 houses including Ophiuchus

### CLI (`mazz.py`)
Commands: now, today, week, watch (daemon), search, thresholds, relationship, areas, transits, month, brief, audit, ics, zepp, wealth

### Web Dashboard (`mazzaroth_web.py`)
- Live at localhost:8080, auto-refresh 30s
- Score gauge, active aspects, 7-day forecast, PEAK calendar, planet positions, life areas

### Life Areas (`mazzaroth_life_areas.py`)
- All 13 houses with interpretations: relationship, sex, wealth, health, home, romance, spirituality
- House cusp activation ensures all areas score even without natal planets

### Wealth Optimizer (`wealth_optimizer.py`)
- Financial astrology: wealth score, billionaire pattern detection (8 patterns)
- Natal blueprint: Mercury/Venus/Mars in H2 (Deal Maker + Amplifier + Money Warrior)
- Investment timing, 60-day financial calendar
- Commands: python mazz.py wealth [calendar|pattern|invest]

### Ground Truth (`execution_audit.py`)
- Auto-logs predictions for PEAK/VH/HIGH days to predictions_log.csv
- Rate: python mazz.py audit rate 1-5 "tag"
- Regression: python mazz.py audit regression (hit-rate by planet, house, aspect)
- First entry: 2026-06-12, PEAK 6158, Neptune Sq Neptune, 4/5 "productive day"

### Transit Combiner (`transit_combiner.py`)
- Synthesizes multiple transits into single Strategic Daily Brief
- Tone classification: supportive / challenging / mixed-tension / neutral
- Commands: python mazz.py brief, python transit_combiner.py [date|tomorrow|week]

### T-Rex 2 Sync (`trex2_sync.py`)
- ICS calendar, Zepp Agenda memos, watch alarms
- Preloaded 986 events (2026-2036) in mazzaroth_exact.ics

### Zepp Correlation (`zepp_auto_sync.py`, `zepp_correlate.py`)
- Watches Zepp_Exports/ folder, auto-imports CSVs
- Merges health data with transit scores for correlation analysis

### Self-Healing (`watchdog.ps1`)
- PowerShell watchdog, 60s cycle, auto-restarts daemon + dashboard
- Memory leak detection at 200MB threshold

### CI/CD (`.github/workflows/deploy.yml`)
- Weekly ICS regeneration + threshold update
- Runs Sunday 06:00 UTC, or manual trigger

### GitHub Pages (`docs/index.html`)
- Private static dashboard at geraldkombo.github.io/mazzaroth/
- Stats, upcoming PEAK days, download links

## Key Design Decisions
- Skyfield+DE421 instead of pyswisseph (no MSVC on Windows)
- Hardcoded natal chart for instant startup
- deg instead of ° in output (cp1252 encoding safety)
- All Unicode-stripped for PowerShell compatibility
- House cusps enable scoring for ALL 13 life areas

## Data Files
- Mazzaroth_Engine_Data/mazzaroth_master_log.csv — 986 events
- Mazzaroth_Engine_Data/execution_audit.csv — outcome ratings
- Mazzaroth_Engine_Data/predictions_log.csv — auto-logged predictions
- Mazzaroth_Engine_Data/high_leverage_windows.csv — top 50 days
- mazzaroth_exact.ics — calendar for watch sync
- ephe/thresholds.json — cached scoring thresholds

## Git Repo
- github.com/geraldkombo/mazzaroth (private)
- Pages: geraldkombo.github.io/mazzaroth (private)
- Contains: Mazzaroth v3 + majiwatch gateway + other projects

## Next Technical Frontiers
1. Bayesian optimizer.py — Beta-Bernoulli weight update after 10+ audit entries
2. Multi-subject scaling — subjects/{name}/natal.json, --user flag
3. Auto-generated static HTML in CI/CD for fresher Pages data
