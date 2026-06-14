#!/usr/bin/env python3
"""
Mazzaroth Web Dashboard — Live transit browser at http://localhost:8080
Plus terminal-based push notifications for PEAK windows.

Usage:
    python mazzaroth_web.py           Start dashboard server
    python mazzaroth_web.py --port 9090  Custom port
    python mazzaroth_web.py --notify    One-time push notification test
"""

import sys, os, json, http.server, socketserver, threading, webbrowser
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(__file__))
import mazzaroth as mz
import mazzaroth_life_areas as la

PORT = 8080
DATA_DIR = os.path.join(os.path.dirname(__file__), "Mazzaroth_Engine_Data")
THRESH_CACHE = os.path.join(os.path.dirname(__file__), "ephe", "thresholds.json")
DEFAULT_THRESH = {"peak": 3100, "vhigh": 2800, "high": 2400}

def load_thresh():
    if os.path.exists(THRESH_CACHE):
        with open(THRESH_CACHE) as f: return json.load(f)
    return DEFAULT_THRESH

db_cache = None
db_ts = 0

def load_db():
    global db_cache, db_ts
    path = os.path.join(DATA_DIR, "mazzaroth_master_log.csv")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(__file__), "mazzaroth_master_log.csv")
    if os.path.exists(path):
        mt = os.path.getmtime(path)
        if mt > db_ts:
            import csv
            with open(path, "r", encoding="utf-8-sig") as f:
                db_cache = list(csv.DictReader(f))
            db_ts = mt
    return db_cache or []

def build_api():
    thresh = load_thresh()
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    transit = mz.get_transit_data(now)
    score, hits = mz.score_transit(transit)
    level = mz.get_level(score, thresh)

    top = hits[0] if hits else (0, "No aspects", "")
    tname = top[1].split(" ")[0] if hits else ""
    nname = "chart"
    if "natal " in top[1]:
        nname = top[1].split("natal ")[1].split(" ")[0]
    nd = mz.NATAL.get(nname, mz.NATAL["Sun"])
    h = mz._house_num(nd["lon"])
    interp, actions = mz.get_interpretation(tname if tname else "Sun", h)

    db = load_db()
    today_str = now.strftime("%Y-%m-%d")
    today_events = [e for e in db if e["Date"] == today_str]
    today_events.sort(key=lambda x: float(x["Score"]), reverse=True)

    week_events = []
    for i in range(7):
        d = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        week_events.extend([e for e in db if e["Date"] == d])
    week_events.sort(key=lambda x: (x["Date"], -float(x["Score"])))

    peak_upcoming = sorted([e for e in db if e["Level"] == "PEAK" and e["Date"] >= today_str], key=lambda x: x["Date"])[:20]

    body_data = {}
    for name, td in transit.items():
        nd = mz.NATAL.get(name)
        if nd:
            body_data[name] = {
                "transit_lon": round(td["lon"], 2),
                "natal_lon": round(nd["lon"], 2),
                "spd": round(td["spd"], 4),
            }

    return {
        "now": now.strftime("%Y-%m-%d %H:%M UTC"),
        "score": round(score, 1),
        "level": level or "NORMAL",
        "thresholds": thresh,
        "profection": mz.PROF_HOUSE,
        "top_transit": top[1] if hits else "",
        "top_score": round(top[0], 1) if hits else 0,
        "house": h,
        "strategy": interp,
        "actions": actions,
        "hits": [{"desc": h[1], "score": round(h[0], 1)} for h in hits[:12]],
        "today": today_events,
        "week": week_events,
        "peak_upcoming": peak_upcoming,
        "bodies": body_data,
    }

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mazzaroth Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
body{background:#0a0a0f;color:#e0e0e0;padding:20px}
h1{font-size:1.4em;margin-bottom:4px;color:#fff}
.sub{color:#888;font-size:.85em;margin-bottom:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;margin-bottom:20px}
.card{background:#12121a;border:1px solid #222;border-radius:12px;padding:16px}
.card h2{font-size:.85em;text-transform:uppercase;letter-spacing:1px;color:#666;margin-bottom:12px}
.score-big{font-size:3em;font-weight:700;line-height:1}
.score-big.peak{color:#ff4444}.score-big.vhigh{color:#ff8800}.score-big.high{color:#44cc44}.score-big.normal{color:#666}
.level-badge{display:inline-block;padding:4px 12px;border-radius:20px;font-size:.8em;font-weight:600}
.level-badge.peak{background:#ff444422;color:#ff4444;border:1px solid #ff4444}
.level-badge.vhigh{background:#ff880022;color:#ff8800;border:1px solid #ff8800}
.level-badge.high{background:#44cc4422;color:#44cc44;border:1px solid #44cc44}
.meta{color:#888;font-size:.85em;margin-top:8px}
.aspect{display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #1a1a24;font-size:.9em}
.aspect:last-child{border:0}
.aspect .desc{color:#ccc}.aspect .scr{color:#888;font-family:monospace}
.today-event{margin:8px 0;padding:8px;border-radius:8px;background:#0e0e18}
.today-event.peak{border-left:3px solid #ff4444}
.today-event.vhigh{border-left:3px solid #ff8800}
.today-event.high{border-left:3px solid #44cc44}
.today-event .lvl{font-size:.75em;font-weight:600}
.today-event .lvl.p{color:#ff4444}.today-event .lvl.v{color:#ff8800}.today-event .lvl.h{color:#44cc44}
.today-event .tr{font-size:.9em;margin:4px 0}
.today-event .sc{color:#888;font-size:.8em}
.action-item{padding:4px 0;color:#aaa;font-size:.9em}
.action-item:before{content:"→ ";color:#666}
.week-day{margin:4px 0;padding:6px;border-radius:6px;background:#0e0e18;display:flex;justify-content:space-between;font-size:.85em}
.week-day .dt{color:#888;min-width:90px}
.week-day .ev{flex:1}.week-day .sc{color:#666;font-family:monospace}
.bar-widget{height:6px;background:#1a1a24;border-radius:3px;margin-top:8px;overflow:hidden}
.bar-fill{height:100%;border-radius:3px;transition:width 1s}
.body-item{display:flex;justify-content:space-between;padding:4px 0;font-size:.85em;border-bottom:1px solid #1a1a24}
.body-item:last-child{border:0}.body-item .nm{color:#aaa}.body-item .lo{color:#666;font-family:monospace}
@media(max-width:600px){.grid{grid-template-columns:1fr}}
</style>
</head><body>
<h1>Mazzaroth</h1>
<div class="sub" id="sub">Loading...</div>
<div class="grid" id="grid"></div>
<div class="grid"><div class="card" id="areas-card" style="grid-column:1/-1"><h2>Life Areas</h2><div style="color:#666">Loading...</div></div></div>
<script>
const THRESH = {thresh_json};
function load(){fetch('/api/data').then(r=>r.json()).then(d=>render(d)).catch(()=>setTimeout(load,2000))}
function lvlClass(l){return (l||'').toLowerCase().replace(' ','')}
function render(d){
  const g=document.getElementById('grid');
  document.getElementById('sub').textContent=d.now+' | Profection H'+d.profection;

  g.innerHTML=`
<div class="card">
  <h2>Live Score</h2>
  <div class="score-big ${lvlClass(d.level)}">${d.score}</div>
  <div style="margin-top:8px"><span class="level-badge ${lvlClass(d.level)}">${d.level}</span></div>
  <div class="meta">Threshold: PEAK >${d.thresholds.peak} &middot; VH >${d.thresholds.vhigh} &middot; H >${d.thresholds.high}</div>
  <div class="bar-widget"><div class="bar-fill" style="width:${Math.min(100,d.score/d.thresholds.peak*100)}%;background:${d.level==='PEAK'?'#ff4444':d.level==='VERY HIGH'?'#ff8800':d.level==='HIGH'?'#44cc44':'#666'}"></div></div>
</div>

<div class="card">
  <h2>Top Transit</h2>
  <div style="font-size:1.1em;margin-bottom:8px">${d.top_transit}</div>
  <div class="meta">House H${d.house} &middot; Score ${d.top_score}</div>
  <div style="margin-top:8px;color:#aaa;font-size:.9em">${d.strategy}</div>
  ${d.actions.map(a=>'<div class="action-item">'+a+'</div>').join('')}
</div>

<div class="card">
  <h2>Active Aspects</h2>
  ${d.hits.map(h=>'<div class="aspect"><span class="desc">'+h.desc+'</span><span class="scr">'+h.score+'</span></div>').join('')||'<div style="color:#666">None within orb</div>'}
</div>

<div class="card">
  <h2>Planet Positions</h2>
  ${Object.entries(d.bodies).map(([k,v])=>'<div class="body-item"><span class="nm">'+k+'</span><span class="lo">T:'+v.transit_lon+'&deg; N:'+v.natal_lon+'&deg; &Delta;'+(Math.round(Math.abs(v.transit_lon-v.natal_lon)*100)/100)+'&deg;</span></div>').join('')}
</div>

<div class="card" style="grid-column:1/-1">
  <h2>Today's Events</h2>
  ${d.today.length?d.today.map(e=>'<div class="today-event '+lvlClass(e.Level)+'"><div class="lvl '+lvlClass(e.Level)[0]+'">'+e.Level+'</div><div class="tr">'+e.Transit+' H'+e.House+'</div><div class="sc">'+e.Score+' &middot; '+e.Meaning.substr(0,60)+'</div></div>').join(''):'<div style="color:#666">No high-impact events in database for today</div>'}
</div>

<div class="card" style="grid-column:1/-1">
  <h2>7-Day Forecast</h2>
  ${d.week.length?d.week.map(e=>'<div class="week-day"><span class="dt">'+e.Date.substr(5)+'</span><span class="ev"><span class="level-badge '+lvlClass(e.Level)+'" style="font-size:.75em;padding:2px 8px;margin-right:6px">'+e.Level[0]+'</span>'+e.Transit+' H'+e.House+'</span><span class="sc">'+e.Score+'</span></div>').join(''):'<div style="color:#666">No events in next 7 days</div>'}
</div>

<div class="card" style="grid-column:1/-1">
  <h2>Upcoming PEAK Days</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px">
  ${d.peak_upcoming.map(e=>'<div style="background:#1a1a24;padding:8px;border-radius:6px;font-size:.85em"><div style="color:#ff4444;font-weight:600">'+e.Date+'</div><div style="color:#ccc;margin:4px 0">'+e.Transit+' H'+e.House+'</div><div style="color:#888;font-size:.8em">'+e.Meaning.substr(0,50)+'</div></div>').join('')}
  </div>
</div>
`;
}
function loadAreas(){fetch('/api/areas').then(r=>r.json()).then(areas=>{const c=document.getElementById('areas-card');if(!c)return;c.innerHTML='<h2>Life Areas</h2>'+areas.map(a=>'<div class="aspect"><span class="desc">H'+a.house+' '+a.name+'</span><span class="scr"><span class="level-badge '+(a.level||'normal').toLowerCase().replace(' ','')+'" style="font-size:.7em;padding:1px 6px;margin-right:6px">'+(a.level||'NORMAL')[0]+'</span>'+a.score+'</span></div>').join('')}).catch(()=>{});
}
load();setInterval(load,30000);loadAreas();setInterval(loadAreas,30000);
</script></body></html>"""

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/data":
            data = build_api()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif parsed.path == "/api/areas":
            report = la.life_areas_report()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(report).encode())
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html = HTML.replace("{thresh_json}", json.dumps(load_thresh()))
            self.wfile.write(html.encode())

def notify_peak(message=None):
    if message is None:
        thresh = load_thresh()
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        transit = mz.get_transit_data(now)
        score, hits = mz.score_transit(transit)
        level = mz.get_level(score, thresh)
        if level == "PEAK":
            top = hits[0][1] if hits else ""
            message = f"MAZZAROTH PEAK | Score: {score:.0f} | {top}"
        else:
            message = f"MAZZAROTH {level or 'NORMAL'} | Score: {score:.0f}"
    import subprocess, platform
    if platform.system() == "Windows":
        subprocess.run(["powershell", "-Command", f'''
            $t=[Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime];
            $tmpl=[Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
            $txt=$tmpl.GetElementsByTagName("text");$txt.Item(0).AppendChild($tmpl.CreateTextNode("Mazzaroth")).Value;
            $txt.Item(1).AppendChild($tmpl.CreateTextNode("{message}")).Value;
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Mazzaroth").Show($tmpl)
        '''], capture_output=True)
    print(f"\n  [PUSH] {message}\n")

if __name__ == "__main__":
    if "--notify" in sys.argv:
        notify_peak()
        sys.exit(0)
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            PORT = int(sys.argv[idx + 1])

    print(f"\n  Mazzaroth Dashboard: http://localhost:{PORT}")
    print(f"  Share on network:    http://{os.popen('hostname').read().strip()}:{PORT}")
    print(f"  Press Ctrl+C to stop.\n")

    webbrowser.open(f"http://localhost:{PORT}")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.\n")
