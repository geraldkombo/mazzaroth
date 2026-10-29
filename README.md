# Mazzaroth v3

Self-tuning astrological transit engine. Pure Python on Windows/PowerShell — Skyfield + JPL DE421 ephemeris, no C compiler required. Closed-loop: it predicts transits, logs real-world outcomes, and self-tunes scoring weights via Bayesian update.

## What's inside

| Component | File(s) | Purpose |
|---|---|---|
| Core engine | `mazzaroth.py` | Ephemeris (12 bodies incl. Chiron via Kepler orbit + mean lunar node), aspect detection (longitude, declination, antiscia), weighted transit scoring, constellation-based 13-house system (incl. Ophiuchus) |
| Personal blueprint | `mazzaroth_personal.py` | Derives wiring (money/partnerships/work/network), profection year theme + 3-year arc, daily helps/avoids |
| CLI | `mazz.py` | `now`, `today`, `week`, `month`, `watch` (daemon), `search`, `thresholds`, `relationship`, `areas`, `transits`, `brief`, `audit`, `ics`, `zepp`, `wealth` |
| Web dashboard | `mazzaroth_web.py` | Local live dashboard (auto-refresh 30s): score gauge, active aspects, 7-day forecast, PEAK calendar, planet positions, life areas |
| Self-tuning | `optimizer.py`, `execution_audit.py` | Bayesian weight updates from logged outcomes; audit loop |
| Calendar sync | `ics_auto_deploy.py`, `zepp_auto_sync.py`, `zepp_correlate.py` | ICS generation/deploy and Zepp (Amazfit) watch sync + outcome correlation |
| Quinarian calendar | `quinarian_engine.py`, `mazzaroth_lunar.py`, `mazzaroth_life_areas.py` | Alternative calendar system + lunar/life-area overlays |
| Data pipeline | `refresh_data.py`, `generate_daily_data.py`, `transit_combiner.py`, `build_csvs_from_master.py` | Daily data generation for the dashboard and exports |

## Requirements

- Python 3.12+, Windows/PowerShell
- JPL DE421 ephemeris `.bsp` file in `ephe/` (Skyfield downloads it on first run if absent)
- `pip install -r requirements.txt` (see `package.json`/`wrangler.jsonc` only for the optional web deploy pieces)

## Quickstart

```powershell
python mazz.py now        # current sky + top transits
python mazz.py today      # daily brief
python mazz.py week       # 7-day forecast
python mazzaroth_web.py   # local dashboard at http://localhost:8080
```

## Notes

- Personal research tool: the natal chart is hard-coded to the author's birth data; scoring thresholds are cached in `ephe/thresholds.json`.
- `MAZZAROTH_CONTEXT.md` is the authoritative system-context document for the engine internals.

## License

MIT — see [LICENSE](LICENSE).
