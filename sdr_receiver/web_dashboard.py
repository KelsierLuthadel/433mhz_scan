"""Live web dashboard for decoded packets.

Requires: pip install flask

Endpoints:
  GET /            HTML dashboard page
  GET /stream      SSE stream of packets (text/event-stream)
  GET /api/state   JSON snapshot {packets, model_stats}
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from .packet import DecodedPacket

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dashboard state (thread-safe)
# ---------------------------------------------------------------------------

@dataclass
class _ModelStat:
    count: int = 0
    last_seen: str = ""


class DashboardState:
    def __init__(self, max_packets: int = 100) -> None:
        self._packets: deque[dict] = deque(maxlen=max_packets)
        self._model_stats: dict[str, _ModelStat] = {}
        self._subscribers: list[queue.SimpleQueue] = []
        self._lock = threading.Lock()

    def push(self, pkt: DecodedPacket) -> None:
        record = {
            "time":     pkt.time.strftime("%H:%M:%S.%f")[:-3],
            "model":    pkt.model,
            "freq_mhz": pkt.freq_mhz,
            "fields":   pkt.summary_fields(),
        }
        payload = json.dumps(record, default=str)

        with self._lock:
            self._packets.append(record)
            stat = self._model_stats.setdefault(pkt.model, _ModelStat())
            stat.count    += 1
            stat.last_seen = record["time"]
            dead: list[queue.SimpleQueue] = []
            for sub in self._subscribers:
                try:
                    sub.put_nowait(payload)
                except Exception:
                    dead.append(sub)
            for d in dead:
                self._subscribers.remove(d)

    def subscribe(self) -> queue.SimpleQueue:
        q: queue.SimpleQueue = queue.SimpleQueue()
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: queue.SimpleQueue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    @property
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "packets": list(self._packets),
                "model_stats": {
                    k: {"count": v.count, "last_seen": v.last_seen}
                    for k, v in sorted(
                        self._model_stats.items(), key=lambda x: -x[1].count
                    )
                },
            }


# ---------------------------------------------------------------------------
# HTML dashboard (inlined  no templates dir needed)
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>RTL-SDR Live Decoder</title>
<style>
:root{
  --bg:#0d1117;--bg2:#161b22;--bg3:#1c2128;
  --border:#30363d;--text:#c9d1d9;--dim:#8b949e;
  --green:#3fb950;--cyan:#79c0ff;--yellow:#e3b341;
  --red:#f85149;--purple:#bc8cff;--orange:#ffa657;
  --font:'Cascadia Code','Fira Code','Consolas',monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font:13px/1.5 var(--font);height:100vh;display:flex;flex-direction:column}
a{color:var(--cyan)}

/* ── Header ── */
header{background:var(--bg2);border-bottom:1px solid var(--border);
  padding:10px 18px;display:flex;align-items:center;gap:18px;flex-shrink:0}
header h1{font-size:14px;color:var(--cyan);letter-spacing:.05em}
.badge{background:var(--bg3);border:1px solid var(--border);border-radius:4px;
  padding:2px 8px;font-size:11px;color:var(--dim)}
#status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;
  background:var(--red);margin-right:5px;transition:background .3s}
#status-dot.live{background:var(--green);box-shadow:0 0 6px var(--green)}
.header-right{margin-left:auto;display:flex;gap:12px;align-items:center}
#pkt-rate{color:var(--green);font-size:12px}

/* ── Layout ── */
.layout{display:grid;grid-template-columns:260px 1fr;gap:0;flex:1;overflow:hidden}

/* ── Sidebar ── */
aside{background:var(--bg2);border-right:1px solid var(--border);
  overflow-y:auto;padding:12px}
aside h2{font-size:11px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--dim);margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid var(--border)}
.model-card{background:var(--bg3);border:1px solid var(--border);border-radius:6px;
  padding:8px 10px;margin-bottom:6px;cursor:default;transition:border-color .2s}
.model-card:hover{border-color:var(--cyan)}
.model-name{color:var(--cyan);font-size:12px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.model-meta{display:flex;justify-content:space-between;margin-top:4px}
.model-count{color:var(--green);font-size:11px}
.model-time{color:var(--dim);font-size:10px}

/* ── Feed ── */
main{display:flex;flex-direction:column;overflow:hidden}
.feed-header{background:var(--bg2);border-bottom:1px solid var(--border);
  padding:8px 14px;font-size:11px;color:var(--dim);display:flex;gap:20px;flex-shrink:0}
.feed-wrap{flex:1;overflow-y:auto}
table{width:100%;border-collapse:collapse;table-layout:fixed}
thead th{position:sticky;top:0;background:var(--bg2);border-bottom:1px solid var(--border);
  padding:6px 10px;font-size:11px;text-align:left;color:var(--dim);
  text-transform:uppercase;letter-spacing:.06em;font-weight:500}
th:nth-child(1){width:90px}
th:nth-child(2){width:160px}
th:nth-child(3){width:100px}
th:nth-child(4){width:auto}
tbody tr{border-bottom:1px solid #21262d;transition:background .1s}
tbody tr:hover{background:var(--bg2)}
tbody tr.new-row{animation:fadeIn .4s ease}
@keyframes fadeIn{from{background:rgba(63,185,80,.12)}to{background:transparent}}
td{padding:5px 10px;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;vertical-align:middle}
.td-time{color:var(--dim);font-size:11px}
.td-model{color:var(--cyan);font-weight:600}
.td-freq{color:var(--yellow);font-size:11px}
.td-fields{color:var(--text)}
.field-kv{display:inline-block;margin-right:12px}
.field-key{color:var(--purple)}
.field-val{color:var(--orange)}
</style>
</head>
<body>
<header>
  <h1>&#9671; RTL-SDR Live Decoder</h1>
  <span class="badge"><span id="status-dot"></span><span id="status-txt">Connecting…</span></span>
  <span class="badge" id="pkt-total">0 packets</span>
  <div class="header-right">
    <span id="pkt-rate" style="color:var(--dim)"></span>
  </div>
</header>
<div class="layout">
  <aside>
    <h2>Device Models</h2>
    <div id="model-list"></div>
  </aside>
  <main>
    <div class="feed-header">
      <span>TIME</span><span>MODEL</span><span>FREQ</span><span>FIELDS</span>
    </div>
    <div class="feed-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th><th>Model</th><th>Freq</th><th>Fields</th>
          </tr>
        </thead>
        <tbody id="feed-body"></tbody>
      </table>
    </div>
  </main>
</div>
<script>
const MAX_ROWS = 150;
let totalPkts = 0, recentCount = 0, rateTimer = null;
const modelStats = {};

function fmtFields(fields){
  return Object.entries(fields).map(([k,v])=>
    `<span class="field-kv"><span class="field-key">${k}</span>=<span class="field-val">${v}</span></span>`
  ).join('');
}

function prependRow(d){
  const tbody = document.getElementById('feed-body');
  const tr = document.createElement('tr');
  tr.className = 'new-row';
  tr.innerHTML = `
    <td class="td-time">${d.time}</td>
    <td class="td-model">${d.model}</td>
    <td class="td-freq">${d.freq_mhz}</td>
    <td class="td-fields">${fmtFields(d.fields)}</td>`;
  tbody.prepend(tr);
  while(tbody.rows.length > MAX_ROWS) tbody.deleteRow(-1);
}

function updateModelCard(model, count, lastSeen){
  modelStats[model] = {count, lastSeen};
  const list = document.getElementById('model-list');
  let card = document.getElementById('mc-'+btoa(model).replace(/=/g,''));
  if(!card){
    card = document.createElement('div');
    card.className = 'model-card';
    card.id = 'mc-'+btoa(model).replace(/=/g,'');
    list.appendChild(card);
  }
  card.innerHTML = `<div class="model-name">${model}</div>
    <div class="model-meta">
      <span class="model-count">&#9632; ${count}</span>
      <span class="model-time">${lastSeen}</span>
    </div>`;
  // Sort cards by count
  [...list.children]
    .sort((a,b)=> (modelStats[atob(b.id.slice(3)+'==')||'']?.count||0) - (modelStats[atob(a.id.slice(3)+'==')||'']?.count||0))
    .forEach(c=>list.appendChild(c));
}

function setStatus(live){
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-txt');
  dot.className = live ? 'live' : '';
  txt.textContent = live ? 'Live' : 'Reconnecting…';
}

function updateCounter(){
  document.getElementById('pkt-total').textContent = `${totalPkts.toLocaleString()} packets`;
}

function startRateTimer(){
  rateTimer = setInterval(()=>{
    const rate = recentCount;
    recentCount = 0;
    const el = document.getElementById('pkt-rate');
    el.textContent = `${rate}/s`;
    el.style.color = rate > 0 ? 'var(--green)' : 'var(--dim)';
  }, 1000);
}

// Load initial state
fetch('/api/state').then(r=>r.json()).then(data=>{
  (data.packets||[]).slice().reverse().forEach(pkt=>{
    prependRow(pkt);
    totalPkts++;
  });
  Object.entries(data.model_stats||{}).forEach(([m,s])=>
    updateModelCard(m, s.count, s.last_seen));
  updateCounter();
});

// SSE with reconnect
let sse, sseBackoff = 1000;
function connectSSE(){
  sse = new EventSource('/stream');
  sse.onopen = ()=>{ setStatus(true); sseBackoff = 1000; };
  sse.onmessage = e=>{
    const d = JSON.parse(e.data);
    prependRow(d);
    totalPkts++; recentCount++;
    updateCounter();
    const ms = modelStats[d.model] || {count:0};
    updateModelCard(d.model, ms.count+1, d.time);
    modelStats[d.model] = {count:ms.count+1, lastSeen:d.time};
  };
  sse.onerror = ()=>{
    setStatus(false);
    sse.close();
    setTimeout(()=>{ sseBackoff=Math.min(sseBackoff*2,30000); connectSSE(); }, sseBackoff);
  };
}

startRateTimer();
connectSSE();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------

class Dashboard:
    def __init__(
        self,
        state: DashboardState,
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        try:
            from flask import Flask, Response, jsonify, request  # type: ignore
            self._flask_available = True
        except ImportError:
            raise ImportError("Flask is required for the web dashboard:\n  pip install flask")

        self.state = state
        self.host  = host
        self.port  = port
        self._app  = self._build_app()

    def _build_app(self):
        from flask import Flask, Response, jsonify  # type: ignore

        app = Flask(__name__)
        app.logger.setLevel(logging.WARNING)

        state = self.state

        @app.route("/")
        def index():
            return _HTML, 200, {"Content-Type": "text/html; charset=utf-8"}

        @app.route("/api/state")
        def api_state():
            return jsonify(state.snapshot)

        @app.route("/stream")
        def stream():
            sub = state.subscribe()

            def generate():
                try:
                    while True:
                        try:
                            payload = sub.get(timeout=30)
                            yield f"data: {payload}\n\n"
                        except Exception:
                            yield ": keepalive\n\n"  # SSE comment keeps connection alive
                except GeneratorExit:
                    pass
                finally:
                    state.unsubscribe(sub)

            return Response(generate(), mimetype="text/event-stream",
                            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

        return app

    def start(self) -> None:
        from werkzeug.serving import make_server  # type: ignore

        srv = make_server(self.host, self.port, self._app, threaded=True)
        t = threading.Thread(target=srv.serve_forever, name="web-dashboard", daemon=True)
        t.start()
        logger.info("Dashboard: http://%s:%d", self.host if self.host != "0.0.0.0" else "localhost", self.port)
        print(f"  Dashboard : http://localhost:{self.port}")
