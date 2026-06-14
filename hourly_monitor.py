from skyfield.api import load
from datetime import datetime, timedelta

ts = load.timescale(builtin=True)
planets = load("ephe/de421.bsp")
earth = planets["earth"]

BODIES = {"Moon": planets["moon"], "Mercury": planets["mercury"], "Sun": planets["sun"]}

now = datetime.now(datetime.UTC).replace(tzinfo=None)
print(f"{'Time (UTC)':<12} | {'Body':<10} | {'Longitude':<10} | {'Declination':<10} | {'Speed °/h':<10}")
print("-" * 60)

for hour in range(25):
    dt = now + timedelta(hours=hour)
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    t_next = ts.utc(dt.year, dt.month, dt.day, dt.hour + 1, dt.minute, dt.second)

    for name, body in BODIES.items():
        app = earth.at(t).observe(body).apparent()
        lat, lon, dist = app.ecliptic_latlon()
        _, dec, _ = app.radec()
        lon_deg = lon.degrees % 360

        app_next = earth.at(t_next).observe(body).apparent()
        lon_next = app_next.ecliptic_latlon()[1].degrees % 360
        spd = (lon_next - lon_deg)
        if spd > 180: spd -= 360
        if spd < -180: spd += 360

        print(f"{dt.strftime('%H:%M'):<12} | {name:<10} | {lon_deg:<10.2f} | {dec.degrees:<+9.2f}  | {spd:<+9.4f}")

print()

# === PEAK ASPECT WATCH (next 4 hours) ===
print("=== PEAK WINDOW ALERT (next 4 hours) ===")
NATAL_SUN_LON = 159.11  # Natal Sun ~ 9° Virgo (Gerald Kombo)
for hour in range(4):
    dt = now + timedelta(hours=hour)
    t = ts.utc(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

    for name, body in BODIES.items():
        app = earth.at(t).observe(body).apparent()
        lat, lon, dist = app.ecliptic_latlon()
        lon_deg = lon.degrees % 360

        diff = abs(lon_deg - NATAL_SUN_LON) % 360
        if diff > 180: diff = 360 - diff

        aspects = [(0, 8, "Conj"), (180, 8, "Opp"), (90, 7, "Sq"), (120, 7, "Tri"), (60, 5, "Sxt")]
        for angle, orb, name_asp in aspects:
            delta = abs(diff - angle)
            if delta <= orb:
                print(f"  [{dt.strftime('%H:%M')}] {name} {name_asp} Natal Sun ({delta:.2f}°)")

print()
print("T-Rex 2 Memo: 'H11 Network Sync | Check master_log for action'")
