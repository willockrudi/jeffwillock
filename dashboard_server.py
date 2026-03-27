"""
dashboard_server.py — JC Custom shop dashboard server
Serves the dashboard UI and handles all actions.

Run:
    .venv/bin/python dashboard_server.py

Opens at:
    http://127.0.0.1:8082        (TV / desktop)
    http://[local-ip]:8082       (iPad over WiFi)

Find your local IP with: hostname -I | awk '{print $1}'
"""

import json
import os
import sys
import shutil
import threading
import time
import subprocess
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlencode

ROOT         = Path(__file__).parent.resolve()
INCOMING_DIR = ROOT / "_Incoming"
GUITARS_PATH = ROOT / "guitars.json"
SITE_PATH    = ROOT / "site.json"

UNDO_DIR     = ROOT / ".undo_pending"
UNDO_SECONDS = 30

HOST = "0.0.0.0"   # listen on all interfaces so iPad can connect
PORT = 8082

MEDIA_EXTENSIONS = {
    # Photos
    ".jpg", ".jpeg", ".png", ".heic", ".heif",
    ".gif", ".webp", ".tiff", ".tif", ".raw", ".dng",
    # Videos
    ".mp4", ".mov", ".m4v", ".avi", ".mkv", ".wmv", ".3gp",
}
PHOTO_EXTENSIONS = MEDIA_EXTENSIONS  # alias — covers photos and videos

# ── Pending undos: {token: {src, dest, expires}} ─────────────────────────────
_pending_undos: dict = {}
_undo_lock = threading.Lock()


def _undo_reaper():
    """Background thread — commits moves once undo window expires."""
    while True:
        time.sleep(2)
        now = time.time()
        with _undo_lock:
            expired = [t for t, u in _pending_undos.items() if now >= u["expires"]]
            for token in expired:
                entry = _pending_undos.pop(token)
                # Move is already done — just clean up the undo record
                tmp = Path(entry.get("tmp", ""))
                if tmp.exists():
                    tmp.unlink(missing_ok=True)


threading.Thread(target=_undo_reaper, daemon=True).start()


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_json(path: Path) -> list | dict:
    if not path.exists():
        return [] if "guitars" in path.name or "repairs" in path.name else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def load_guitars() -> list:
    data = load_json(GUITARS_PATH)
    return data if isinstance(data, list) else []


def load_site() -> dict:
    data = load_json(SITE_PATH)
    return data if isinstance(data, dict) else {}


def incoming_photos() -> list[str]:
    if not INCOMING_DIR.exists():
        return []
    files = sorted(
        [f.name for f in INCOMING_DIR.iterdir()
         if f.is_file() and f.suffix.lower() in PHOTO_EXTENSIONS],
        key=lambda n: (INCOMING_DIR / n).stat().st_mtime,
        reverse=True,
    )
    return files


# ── Rebuild / publish helpers ─────────────────────────────────────────────────

def run_rebuild() -> tuple[bool, str]:
    try:
        result = subprocess.run(
            [str(ROOT / ".venv" / "bin" / "python"), str(ROOT / "manage.py"), "rebuild"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            input="5\nq\n",
        )
        # manage.py rebuild via CLI needs stdin — use python import instead
        sys.path.insert(0, str(ROOT))
        from manage import rebuild_all
        rebuild_all()
        return True, "Site rebuilt."
    except Exception as e:
        try:
            sys.path.insert(0, str(ROOT))
            from manage import rebuild_all
            rebuild_all()
            return True, "Site rebuilt."
        except Exception as e2:
            return False, f"Rebuild failed: {e2}"


def run_publish(message: str = "") -> tuple[bool, str]:
    try:
        sys.path.insert(0, str(ROOT))
        from manage import publish_to_github_noninteractive
        ok, msg = publish_to_github_noninteractive(message or None)
        return ok, msg
    except Exception as e:
        return False, f"Publish failed: {e}"


# ── Photo assignment ──────────────────────────────────────────────────────────

def assign_photo(filename: str, guitar_slug: str) -> tuple[bool, str, str]:
    """
    Move filename from _Incoming/ into guitars/[slug]/build/.
    Returns (ok, message, undo_token).
    """
    src = INCOMING_DIR / filename
    if not src.exists():
        return False, f"{filename} not found in _Incoming/", ""

    guitars = load_guitars()
    guitar = next((g for g in guitars if g.get("slug") == guitar_slug), None)
    if not guitar:
        return False, f"Guitar '{guitar_slug}' not found.", ""

    dest_dir = ROOT / "guitars" / guitar_slug / "build"
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest = dest_dir / filename
    i = 2
    while dest.exists():
        dest = dest_dir / f"{src.stem}_{i}{src.suffix}"
        i += 1

    shutil.move(str(src), str(dest))

    token = f"{guitar_slug}-{filename}-{int(time.time())}"
    with _undo_lock:
        _pending_undos[token] = {
            "src":     str(src),
            "dest":    str(dest),
            "expires": time.time() + UNDO_SECONDS,
            "label":   f"{filename} → {guitar.get('title', guitar_slug)}",
        }

    return True, f"Assigned {filename} to {guitar.get('title', guitar_slug)}", token


def undo_assign(token: str) -> tuple[bool, str]:
    with _undo_lock:
        entry = _pending_undos.pop(token, None)
    if not entry:
        return False, "Undo window has expired."
    dest = Path(entry["dest"])
    src  = Path(entry["src"])
    if dest.exists():
        shutil.move(str(dest), str(src))
        return True, f"Undone — {dest.name} moved back to _Incoming/"
    return False, "File no longer exists at destination."


# ── HTML builders ─────────────────────────────────────────────────────────────

STATUS_COLOR = {
    "in progress": "#ffb57d",
    "complete":    "#7ad88c",
    "available":   "#7ad8d8",
    "sold":        "#c2b6aa",
    "archived":    "#c2b6aa",
}

STATUS_DOT = {
    "in progress": "🟠",
    "complete":    "🟢",
    "available":   "🔵",
    "sold":        "⚪",
    "archived":    "⚪",
}


def _guitar_cards_html(guitars: list) -> str:
    if not guitars:
        return "<p class='empty'>No guitars yet. Add one via manage.py or the web UI.</p>"

    cards = []
    for g in guitars:
        title   = g.get("title", "Untitled")
        number  = g.get("number", "")
        status  = (g.get("status") or "in progress").lower()
        color   = STATUS_COLOR.get(status, "#c2b6aa")
        dot     = STATUS_DOT.get(status, "⚪")
        specs   = " · ".join(filter(None, [
            g.get("body_wood"), g.get("fretboard"), g.get("pickups")
        ]))
        customer = g.get("customer_name", "")
        est      = g.get("estimated_completion", "")
        price    = g.get("price")
        steps    = g.get("steps") or []
        last_step = steps[-1].get("title", "") if steps else ""

        price_html    = f'<span class="price">${price:,.0f}</span>' if price else ""
        customer_html = f'<div class="customer">For: {customer}</div>' if customer else ""
        est_html      = f'<div class="est">Due: {est}</div>' if est else ""
        step_html     = f'<div class="last-step">Last: {last_step}</div>' if last_step else ""
        specs_html    = f'<div class="specs">{specs}</div>' if specs else ""

        cards.append(f"""
<div class="guitar-card">
  <div class="card-header">
    <span class="guitar-number">#{number}</span>
    <span class="status-dot" style="color:{color}">{dot} {status.title()}</span>
  </div>
  <h2 class="guitar-name">{title}</h2>
  {specs_html}
  {customer_html}
  {est_html}
  {step_html}
  {price_html}
</div>""")

    return "\n".join(cards)


def _incoming_html(photos: list[str], guitars: list) -> str:
    if not photos:
        return "<p class='empty'>No photos in _Incoming/</p>"

    guitar_opts = "\n".join([
        f'<option value="{g.get("slug","")}">'
        f'#{g.get("number","")} {g.get("title","Untitled")}'
        f'</option>'
        for g in guitars
    ])

    items = []
    for filename in photos:
        items.append(f"""
<div class="photo-item" id="photo-{filename.replace('.','_')}">
  {'<video src="/incoming/' + filename + '" controls style="width:100%;height:160px;object-fit:cover;background:#000;display:block;"></video>' if filename.lower().rsplit('.',1)[-1] in ('mp4','mov','m4v','avi','mkv','wmv','3gp') else '<img src="/incoming/' + filename + '" alt="' + filename + '" loading="lazy">'}
  <div class="photo-controls">
    <p class="photo-name">{filename}</p>
    <select class="guitar-select" data-file="{filename}">
      <option value="">— assign to guitar —</option>
      {guitar_opts}
    </select>
    <button class="assign-btn" data-file="{filename}">Assign</button>
  </div>
</div>""")

    return "\n".join(items)


def build_page(is_ipad: bool = False, message: str = "", undo_token: str = "") -> str:
    guitars = load_guitars()
    site    = load_site()
    photos  = incoming_photos()
    name    = site.get("name", "JC Custom Guitars")
    now     = datetime.now().strftime("%A %d %b  %H:%M")

    guitar_cards = _guitar_cards_html(guitars)
    incoming_html = _incoming_html(photos, guitars)

    undo_bar = ""
    if undo_token and undo_token in _pending_undos:
        label = _pending_undos[undo_token].get("label", "last action")
        undo_bar = f"""
<div class="undo-bar" id="undoBar">
  <span>✅ {label}</span>
  <button onclick="undoAction('{undo_token}')">↩ Undo ({UNDO_SECONDS}s)</button>
</div>"""

    msg_bar = ""
    if message:
        msg_bar = f'<div class="msg-bar">{message}</div>'

    layout_class = "ipad" if is_ipad else "tv"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Custom — Shop Dashboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:       #1a1510;
    --bg-alt:   #221c17;
    --surface:  #2c2420;
    --surface2: #362e28;
    --text:     #f0ebe4;
    --muted:    #b8a898;
    --accent:   #c96a2b;
    --accent2:  #e8813a;
    --green:    #7ad88c;
    --border:   #453830;
    --radius:   18px;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'DM Sans', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    overflow-x: hidden;
  }}

  /* ── Header ── */
  .header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 18px 32px;
    background: var(--bg-alt);
    border-bottom: 2px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
  }}

  .logo {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.2rem;
    letter-spacing: 0.06em;
    color: var(--text);
  }}

  .logo span {{ color: var(--accent); }}

  .clock {{
    font-size: 1.1rem;
    color: var(--muted);
    font-variant-numeric: tabular-nums;
  }}

  .header-actions {{
    display: flex;
    gap: 12px;
  }}

  /* ── Buttons ── */
  .btn {{
    font-family: 'DM Sans', sans-serif;
    font-weight: 600;
    font-size: 1rem;
    border: none;
    border-radius: 999px;
    cursor: pointer;
    padding: 12px 22px;
    min-height: 52px;
    transition: transform 0.15s, background 0.15s;
  }}

  .btn:active {{ transform: scale(0.97); }}

  .btn-primary {{ background: var(--accent); color: #fff; }}
  .btn-primary:hover {{ background: var(--accent2); }}
  .btn-ghost {{
    background: var(--surface2);
    color: var(--text);
    border: 1px solid var(--border);
  }}
  .btn-ghost:hover {{ border-color: var(--accent); color: var(--accent); }}
  .btn-danger {{ background: #8b2020; color: #fff; }}

  /* ── Layout ── */
  .main {{
    display: grid;
    gap: 0;
    height: calc(100vh - 74px);
  }}

  .tv .main {{
    grid-template-columns: 1fr 340px;
  }}

  .ipad .main {{
    grid-template-columns: 1fr;
    height: auto;
  }}

  /* ── Guitars panel ── */
  .guitars-panel {{
    padding: 28px 32px;
    overflow-y: auto;
  }}

  .panel-title {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.1em;
    color: var(--muted);
    text-transform: uppercase;
    margin-bottom: 20px;
  }}

  .guitars-grid {{
    display: grid;
    gap: 18px;
  }}

  .tv .guitars-grid {{
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  }}

  /* ── Guitar card ── */
  .guitar-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 26px;
    position: relative;
    transition: border-color 0.2s;
  }}

  .guitar-card:hover {{ border-color: var(--accent); }}

  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }}

  .guitar-number {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    color: var(--muted);
    letter-spacing: 0.08em;
  }}

  .status-dot {{
    font-size: 0.9rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }}

  .guitar-name {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2.4rem;
    line-height: 1;
    letter-spacing: 0.02em;
    margin-bottom: 10px;
    color: var(--text);
  }}

  .tv .guitar-name {{ font-size: 2.8rem; }}

  .specs, .customer, .est, .last-step {{
    font-size: 0.95rem;
    color: var(--muted);
    margin-top: 5px;
  }}

  .price {{
    display: inline-block;
    margin-top: 12px;
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--accent);
  }}

  /* ── Incoming panel ── */
  .incoming-panel {{
    background: var(--bg-alt);
    border-left: 2px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }}

  .ipad .incoming-panel {{
    border-left: none;
    border-top: 2px solid var(--border);
  }}

  .incoming-header {{
    padding: 20px 24px 14px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }}

  .incoming-count {{
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.08em;
    color: var(--muted);
  }}

  .incoming-count span {{
    font-size: 2rem;
    color: var(--accent);
    margin-right: 6px;
  }}

  .photo-list {{
    overflow-y: auto;
    flex: 1;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }}

  .photo-item {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    transition: border-color 0.2s;
  }}

  .photo-item:hover {{ border-color: var(--accent); }}

  .photo-item img {{
    width: 100%;
    height: 160px;
    object-fit: cover;
    display: block;
  }}

  .photo-controls {{
    padding: 12px 14px;
  }}

  .photo-name {{
    font-size: 0.8rem;
    color: var(--muted);
    margin-bottom: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}

  .guitar-select {{
    width: 100%;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid var(--border);
    background: var(--surface2);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    margin-bottom: 8px;
    min-height: 44px;
  }}

  .assign-btn {{
    width: 100%;
    min-height: 48px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 10px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
  }}

  .assign-btn:active {{ transform: scale(0.98); }}
  .assign-btn:hover {{ background: var(--accent2); }}

  /* ── Undo bar ── */
  .undo-bar {{
    position: fixed;
    bottom: 24px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--surface2);
    border: 1px solid var(--accent);
    border-radius: 999px;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
    z-index: 200;
    box-shadow: 0 8px 32px rgba(0,0,0,0.4);
    animation: slideUp 0.3s ease;
  }}

  @keyframes slideUp {{
    from {{ opacity: 0; transform: translateX(-50%) translateY(20px); }}
    to   {{ opacity: 1; transform: translateX(-50%) translateY(0); }}
  }}

  .undo-bar button {{
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 999px;
    padding: 8px 18px;
    font-family: 'DM Sans', sans-serif;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.95rem;
    min-height: 40px;
  }}

  /* ── Message bar ── */
  .msg-bar {{
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
    padding: 10px 32px;
    font-size: 0.95rem;
    color: var(--green);
  }}

  /* ── Empty states ── */
  .empty {{
    color: var(--muted);
    font-size: 1rem;
    padding: 24px 0;
  }}

  /* ── Scrollbar ── */
  ::-webkit-scrollbar {{ width: 6px; }}
  ::-webkit-scrollbar-track {{ background: transparent; }}
  ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 3px; }}
</style>
</head>
<body class="{layout_class}">

<header class="header">
  <div class="logo">JC <span>Custom Guitars</span></div>
  <div class="clock" id="clock">{now}</div>
  <div class="header-actions">
    <a href="/admin" class="btn btn-ghost" style="text-decoration:none;">⚙ Manage</a>
    <button class="btn btn-ghost" onclick="doRebuild()">⟳ Rebuild</button>
    <button class="btn btn-primary" onclick="doPublish()">↑ Publish</button>
  </div>
</header>

{msg_bar}
{undo_bar}

<div class="main">

  <section class="guitars-panel">
    <p class="panel-title">Active Builds — {len(guitars)} guitar{"s" if len(guitars) != 1 else ""}</p>
    <div class="guitars-grid">
      {guitar_cards}
    </div>
  </section>

  <aside class="incoming-panel">
    <div class="incoming-header">
      <div class="incoming-count"><span>{len(photos)}</span>Incoming</div>
      <button class="btn btn-ghost" style="padding:8px 14px;min-height:38px;font-size:0.85rem;"
              onclick="location.reload()">↺ Refresh</button>
    </div>
    <div class="photo-list">
      {incoming_html}
    </div>
  </aside>

</div>

<script>
  // ── Live clock ──
  function tick() {{
    const now = new Date();
    const days = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
    const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    const d = days[now.getDay()];
    const dt = String(now.getDate()).padStart(2,' ');
    const m = months[now.getMonth()];
    const h = String(now.getHours()).padStart(2,'0');
    const min = String(now.getMinutes()).padStart(2,'0');
    document.getElementById('clock').textContent = `${{d}} ${{dt}} ${{m}}  ${{h}}:${{min}}`;
  }}
  tick();
  setInterval(tick, 10000);

  // ── Assign photo ──
  document.querySelectorAll('.assign-btn').forEach(btn => {{
    btn.addEventListener('click', () => {{
      const file   = btn.dataset.file;
      const select = document.querySelector(`.guitar-select[data-file="${{file}}"]`);
      const slug   = select ? select.value : '';
      if (!slug) {{ alert('Please select a guitar first.'); return; }}
      btn.disabled = true;
      btn.textContent = 'Assigning...';
      fetch('/assign', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
        body: `file=${{encodeURIComponent(file)}}&slug=${{encodeURIComponent(slug)}}`
      }})
      .then(r => r.json())
      .then(data => {{
        if (data.ok) {{
          const item = document.getElementById('photo-' + file.replace('.','_'));
          if (item) item.remove();
          showUndo(data.token, data.message);
          const countEl = document.querySelector('.incoming-count span');
          if (countEl) countEl.textContent = Math.max(0, parseInt(countEl.textContent) - 1);
        }} else {{
          alert('Error: ' + data.message);
          btn.disabled = false;
          btn.textContent = 'Assign';
        }}
      }})
      .catch(() => {{
        alert('Request failed.');
        btn.disabled = false;
        btn.textContent = 'Assign';
      }});
    }});
  }});

  // ── Undo ──
  function showUndo(token, message) {{
    let bar = document.getElementById('undoBar');
    if (!bar) {{
      bar = document.createElement('div');
      bar.className = 'undo-bar';
      bar.id = 'undoBar';
      document.body.appendChild(bar);
    }}
    bar.innerHTML = `<span>✅ ${{message}}</span>
      <button onclick="undoAction('${{token}}')">↩ Undo (30s)</button>`;
    setTimeout(() => {{ if (bar) bar.remove(); }}, 31000);
  }}

  function undoAction(token) {{
    fetch('/undo', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
      body: 'token=' + encodeURIComponent(token)
    }})
    .then(r => r.json())
    .then(data => {{
      const bar = document.getElementById('undoBar');
      if (bar) bar.remove();
      if (data.ok) {{ location.reload(); }}
      else {{ alert('Undo failed: ' + data.message); }}
    }});
  }}

  // ── Rebuild ──
  function doRebuild() {{
    const btn = document.querySelector('.btn-ghost');
    btn.textContent = '⟳ Rebuilding...';
    btn.disabled = true;
    fetch('/rebuild', {{ method: 'POST' }})
      .then(r => r.json())
      .then(data => {{
        btn.textContent = data.ok ? '✅ Done' : '❌ Failed';
        btn.disabled = false;
        setTimeout(() => {{ btn.textContent = '⟳ Rebuild'; }}, 3000);
      }});
  }}

  // ── Publish ──
  function doPublish() {{
    const btn = document.querySelector('.btn-primary');
    btn.textContent = '↑ Publishing...';
    btn.disabled = true;
    fetch('/publish', {{ method: 'POST' }})
      .then(r => r.json())
      .then(data => {{
        btn.textContent = data.ok ? '✅ Published' : '❌ Failed';
        btn.disabled = false;
        setTimeout(() => {{ btn.textContent = '↑ Publish'; }}, 4000);
      }});
  }}
</script>
</body>
</html>"""


# ── Request handler ───────────────────────────────────────────────────────────

class DashboardHandler(BaseHTTPRequestHandler):

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, content: str, status: int = 200):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _parse_form(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length).decode("utf-8") if length else ""
        parsed = parse_qs(raw, keep_blank_values=True)
        return {k: v[0] for k, v in parsed.items()}

    def do_GET(self):
        parsed = urlparse(self.path)
        ua = self.headers.get("User-Agent", "")
        is_ipad = "iPad" in ua or "iPhone" in ua or "Mobile" in ua

        msg   = parse_qs(parsed.query).get("msg", [""])[0]
        token = parse_qs(parsed.query).get("token", [""])[0]

        if parsed.path in ("/", "/index.html"):
            self._html(build_page(is_ipad=is_ipad, message=msg, undo_token=token))
            return

        # Serve incoming photos
        if parsed.path.startswith("/incoming/"):
            filename = parsed.path[len("/incoming/"):]
            fpath = INCOMING_DIR / filename
            if fpath.exists() and fpath.suffix.lower() in PHOTO_EXTENSIONS:
                data = fpath.read_bytes()
                ext = fpath.suffix.lower()
                mime = {
                    "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "png": "image/png",  "heic": "image/heic",
                    "gif": "image/gif",  "webp": "image/webp",
                    "mp4": "video/mp4",  "mov": "video/quicktime",
                    "m4v": "video/mp4",  "avi": "video/x-msvideo",
                    "mkv": "video/x-matroska", "wmv": "video/x-ms-wmv",
                    "3gp": "video/3gpp",
                }.get(ext.lstrip("."), "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            self.send_response(404)
            self.end_headers()
            return

        # Fall through to admin handler (patched in below)
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/assign":
            form = self._parse_form()
            filename = form.get("file", "").strip()
            slug     = form.get("slug", "").strip()
            if not filename or not slug:
                self._json({"ok": False, "message": "Missing file or guitar."})
                return
            ok, msg, token = assign_photo(filename, slug)
            self._json({"ok": ok, "message": msg, "token": token})
            return

        if parsed.path == "/undo":
            form  = self._parse_form()
            token = form.get("token", "").strip()
            ok, msg = undo_assign(token)
            self._json({"ok": ok, "message": msg})
            return

        if parsed.path == "/rebuild":
            ok, msg = run_rebuild()
            self._json({"ok": ok, "message": msg})
            return

        if parsed.path == "/publish":
            ok, msg = run_publish()
            self._json({"ok": ok, "message": msg})
            return

        self._json({"ok": False, "message": "Unknown action."}, 404)

    def log_message(self, fmt, *args):
        return  # suppress default access log noise


# ── Entry point ───────────────────────────────────────────────────────────────

def get_local_ip() -> str:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "unknown"


def main():
    INCOMING_DIR.mkdir(parents=True, exist_ok=True)
    local_ip = get_local_ip()

    server = ThreadingHTTPServer((HOST, PORT), DashboardHandler)

    print(f"""
╔══════════════════════════════════════════════╗
║       JC Custom — Shop Dashboard             ║
╠══════════════════════════════════════════════╣
║  TV / Desktop : http://127.0.0.1:{PORT}        ║
║  iPad (WiFi)  : http://{local_ip}:{PORT}   ║
╚══════════════════════════════════════════════╝

Press Ctrl+C to stop.
""")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


# =============================================================================
#  ADMIN UI — wired in from admin_ui.py
# =============================================================================

import importlib.util as _ilu
import sys as _sys

def _load_admin_ui():
    spec = _ilu.spec_from_file_location("admin_ui", ROOT / "admin_ui.py")
    mod  = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def _load_manage():
    if str(ROOT) not in _sys.path:
        _sys.path.insert(0, str(ROOT))
    import manage as m
    return m


def _admin_response(handler, page_key: str, content: str,
                    message: str = "", msg_type: str = "success"):
    ui = _load_admin_ui()
    body = ui._shell(page_key, content, message, msg_type)
    b = body.encode("utf-8")
    handler.send_response(200)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Content-Length", str(len(b)))
    handler.end_headers()
    handler.wfile.write(b)


def _admin_redirect(handler, path: str, msg: str = "", msg_type: str = "success"):
    from urllib.parse import urlencode
    target = path
    if msg:
        sep = "&" if "?" in target else "?"
        target += sep + urlencode({"msg": msg, "mt": msg_type})
    handler.send_response(303)
    handler.send_header("Location", target)
    handler.end_headers()


def _safe_idx(val, lst):
    try:
        i = int(val)
        return i if 0 <= i < len(lst) else -1
    except (TypeError, ValueError):
        return -1


def _parse_qs_simple(qs: str) -> dict:
    from urllib.parse import parse_qs
    parsed = parse_qs(qs, keep_blank_values=True)
    return {k: v[0] for k, v in parsed.items()}


# ── Monkey-patch DashboardHandler with admin routes ───────────────────────────

_orig_do_GET  = DashboardHandler.do_GET
_orig_do_POST = DashboardHandler.do_POST


def _admin_do_GET(self):
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(self.path)
    path   = parsed.path
    qs     = _parse_qs_simple(parsed.query)
    msg    = qs.get("msg", "")
    mt     = qs.get("mt", "success")

    # Non-admin paths go to original handler
    if not path.startswith("/admin"):
        _orig_do_GET(self)
        return

    ui = _load_admin_ui()
    m  = _load_manage()

    guitars = m.load_guitars()
    builds  = m.load_projects()
    repairs = m.load_repairs()
    site    = m.load_site()
    backups = m.list_backups()

    # ── Home ──
    if path == "/admin" or path == "/admin/":
        content = ui.page_home(guitars, builds, repairs, site)
        _admin_response(self, "home", content, msg, mt); return

    # ── Guitars ──
    if path == "/admin/guitars":
        _admin_response(self, "guitars", ui.page_guitars_list(guitars), msg, mt); return

    if path == "/admin/guitars/new":
        _admin_response(self, "guitars", ui.page_guitar_new(), msg, mt); return

    if path == "/admin/guitars/edit":
        idx = _safe_idx(qs.get("idx"), guitars)
        if idx < 0: _admin_redirect(self, "/admin/guitars", "Guitar not found.", "error"); return
        _admin_response(self, "guitars", ui.page_guitar_edit(guitars[idx], idx), msg, mt); return

    if path == "/admin/guitars/story":
        idx = _safe_idx(qs.get("idx"), guitars)
        if idx < 0: _admin_redirect(self, "/admin/guitars", "Guitar not found.", "error"); return
        _admin_response(self, "guitars", ui.page_guitar_story(guitars[idx], idx), msg, mt); return

    if path == "/admin/guitars/story/edit":
        idx  = _safe_idx(qs.get("idx"), guitars)
        step = _safe_idx(qs.get("step"), guitars[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/guitars", "Not found.", "error"); return
        g = guitars[idx]
        s = (g.get("steps") or [])[step]
        ui2 = _load_admin_ui()
        import html as _html
        v = lambda k: _html.escape(str(s.get(k,"") or ""), quote=True)
        content = f"""
<script>document.getElementById('pageTitle').textContent = 'Edit Story Section';</script>
<div class="card">
  <form method="post" action="/admin/guitars/story/save">
    <input type="hidden" name="idx" value="{idx}">
    <input type="hidden" name="step" value="{step}">
    <div class="form-grid">
      <div class="field"><label>Title</label><input name="title" value="{v('title')}" /></div>
      <div class="field"><label>Image Path</label><input name="image" value="{v('image')}" /></div>
      <div class="field span2"><label>Text</label><textarea name="text">{_html.escape(s.get('text','') or '')}</textarea></div>
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">💾 Save Section</button>
      <a href="/admin/guitars/story?idx={idx}" class="btn btn-ghost">Cancel</a>
    </div>
  </form>
</div>"""
        _admin_response(self, "guitars", content, msg, mt); return

    if path == "/admin/guitars/delete":
        idx = _safe_idx(qs.get("idx"), guitars)
        if idx < 0: _admin_redirect(self, "/admin/guitars", "Guitar not found.", "error"); return
        m.create_backup_note("admin-guitar-delete")
        guitars.pop(idx)
        m.save_guitars(guitars)
        m.rebuild_guitars_page(guitars)
        m.rebuild_guitar_pages(guitars)
        _admin_redirect(self, "/admin/guitars", "Guitar deleted.", "success"); return

    if path == "/admin/guitars/story/delete":
        idx  = _safe_idx(qs.get("idx"), guitars)
        step = _safe_idx(qs.get("step"), guitars[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/guitars", "Not found.", "error"); return
        m.create_backup_note("admin-guitar-story-delete")
        steps = guitars[idx].get("steps") or []
        steps.pop(step)
        guitars[idx]["steps"] = steps
        m.save_guitars(guitars)
        m.rebuild_guitar_pages(guitars)
        _admin_redirect(self, f"/admin/guitars/story?idx={idx}", "Section deleted.", "success"); return

    # ── Builds ──
    if path == "/admin/builds":
        _admin_response(self, "builds", ui.page_builds_list(builds), msg, mt); return
    if path == "/admin/builds/new":
        _admin_response(self, "builds", ui.page_builds_new(), msg, mt); return
    if path == "/admin/builds/edit":
        idx = _safe_idx(qs.get("idx"), builds)
        if idx < 0: _admin_redirect(self, "/admin/builds", "Build not found.", "error"); return
        _admin_response(self, "builds", ui.page_builds_edit(builds[idx], idx), msg, mt); return
    if path == "/admin/builds/story":
        idx = _safe_idx(qs.get("idx"), builds)
        if idx < 0: _admin_redirect(self, "/admin/builds", "Build not found.", "error"); return
        _admin_response(self, "builds", ui.page_builds_story(builds[idx], idx), msg, mt); return
    if path == "/admin/builds/delete":
        idx = _safe_idx(qs.get("idx"), builds)
        if idx < 0: _admin_redirect(self, "/admin/builds", "Not found.", "error"); return
        m.create_backup_note("admin-build-delete")
        builds.pop(idx)
        m.save_projects(builds)
        m.rebuild_all(builds)
        _admin_redirect(self, "/admin/builds", "Build deleted.", "success"); return
    if path == "/admin/builds/story/delete":
        idx  = _safe_idx(qs.get("idx"), builds)
        step = _safe_idx(qs.get("step"), builds[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/builds", "Not found.", "error"); return
        m.create_backup_note("admin-build-story-delete")
        steps = builds[idx].get("steps") or []
        steps.pop(step)
        builds[idx]["steps"] = steps
        m.save_projects(builds)
        m.rebuild_project_pages(builds)
        _admin_redirect(self, f"/admin/builds/story?idx={idx}", "Section deleted.", "success"); return
    if path == "/admin/builds/story/edit":
        idx  = _safe_idx(qs.get("idx"), builds)
        step = _safe_idx(qs.get("step"), builds[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/builds", "Not found.", "error"); return
        p = builds[idx]; s = (p.get("steps") or [])[step]
        import html as _html
        v = lambda k: _html.escape(str(s.get(k,"") or ""), quote=True)
        content = f"""<script>document.getElementById('pageTitle').textContent='Edit Story Section';</script>
<div class="card"><form method="post" action="/admin/builds/story/save">
  <input type="hidden" name="idx" value="{idx}"><input type="hidden" name="step" value="{step}">
  <div class="form-grid">
    <div class="field"><label>Title</label><input name="title" value="{v('title')}" /></div>
    <div class="field"><label>Image Path</label><input name="image" value="{v('image')}" /></div>
    <div class="field span2"><label>Text</label><textarea name="text">{_html.escape(s.get('text','') or '')}</textarea></div>
  </div>
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">💾 Save</button>
    <a href="/admin/builds/story?idx={idx}" class="btn btn-ghost">Cancel</a>
  </div>
</form></div>"""
        _admin_response(self, "builds", content, msg, mt); return

    # ── Repairs ──
    if path == "/admin/repairs":
        _admin_response(self, "repairs", ui.page_repairs_list(repairs), msg, mt); return
    if path == "/admin/repairs/new":
        _admin_response(self, "repairs", ui.page_repairs_new(), msg, mt); return
    if path == "/admin/repairs/edit":
        idx = _safe_idx(qs.get("idx"), repairs)
        if idx < 0: _admin_redirect(self, "/admin/repairs", "Not found.", "error"); return
        _admin_response(self, "repairs", ui.page_repairs_edit(repairs[idx], idx), msg, mt); return
    if path == "/admin/repairs/delete":
        idx = _safe_idx(qs.get("idx"), repairs)
        if idx < 0: _admin_redirect(self, "/admin/repairs", "Not found.", "error"); return
        m.create_backup_note("admin-repair-delete")
        repairs.pop(idx)
        m.save_repairs(repairs)
        m.rebuild_repairs_page()
        _admin_redirect(self, "/admin/repairs", "Repair deleted.", "success"); return

    # ── Site settings ──
    if path == "/admin/site":
        _admin_response(self, "site", ui.page_site(site), msg, mt); return

    # ── Publish ──
    if path == "/admin/publish":
        _admin_response(self, "publish", ui.page_publish(), msg, mt); return

    # ── Backups ──
    if path == "/admin/backups":
        _admin_response(self, "backups", ui.page_backups(backups), msg, mt); return
    if path == "/admin/backups/undo":
        if not backups: _admin_redirect(self, "/admin/backups", "No backups.", "error"); return
        m.restore_backup(backups[0])
        m.rebuild_all()
        _admin_redirect(self, "/admin/backups", f"Restored: {backups[0]}", "success"); return
    if path == "/admin/backups/restore":
        name = qs.get("name", "")
        if not name: _admin_redirect(self, "/admin/backups", "No backup specified.", "error"); return
        m.restore_backup(name)
        m.rebuild_all()
        _admin_redirect(self, "/admin/backups", f"Restored: {name}", "success"); return

    # Fallback
    _admin_redirect(self, "/admin", "Page not found.", "error")


def _admin_do_POST(self):
    from urllib.parse import urlparse
    parsed = urlparse(self.path)
    path   = parsed.path

    if not path.startswith("/admin"):
        _orig_do_POST(self)
        return

    m   = _load_manage()
    form = self._parse_form()

    def _num(k):
        v = form.get(k,"").strip()
        try: return float(v) if v else None
        except ValueError: return None

    def _csv(k): return m._split_csv(form.get(k,""))
    def _lines(k): return m._split_lines(form.get(k,""))

    # ── Save guitar ──
    if path == "/admin/guitars/save":
        guitars = m.load_guitars()
        idx     = _safe_idx(form.get("idx","-1"), guitars)
        title   = (form.get("title") or "").strip()
        if not title: _admin_redirect(self, "/admin/guitars", "Title is required.", "error"); return
        m.create_backup_note("admin-guitar-save")
        if idx < 0:
            g = {"number": m._next_guitar_number(guitars),
                 "slug": m.slugify(title), "steps": [],
                 "created": datetime.now().isoformat(timespec="seconds")}
            guitars.insert(0, g); idx = 0
        else:
            g = guitars[idx]
        g["title"]  = title
        g["status"] = m.normalize_status(form.get("status","In Progress"))
        g["description"] = form.get("description","")
        for k in ("body_wood","neck_wood","fretboard","hardware","pickups","finish",
                  "scale_length","estimated_completion","customer_name","customer_notes"):
            g[k] = form.get(k,"")
        g["price"] = _num("price"); g["deposit_paid"] = _num("deposit_paid"); g["balance_due"] = _num("balance_due")
        g["tags"]    = _csv("tags"); g["bullets"] = _lines("bullets")
        cover = m.resolve_image_input(form.get("cover_image",""), title)
        g["cover_image"] = cover; g["image"] = cover
        g.setdefault("images", []); g.setdefault("links", [])
        g["updated"] = datetime.now().isoformat(timespec="seconds")
        if not g.get("slug"): g["slug"] = m.slugify(title)
        m.save_guitars(guitars)
        m.rebuild_guitars_page(guitars); m.rebuild_guitar_pages(guitars)
        _admin_redirect(self, "/admin/guitars", f"Saved: {title}", "success"); return

    # ── Save build ──
    if path == "/admin/builds/save":
        builds = m.load_projects()
        idx    = _safe_idx(form.get("idx","-1"), builds)
        title  = (form.get("title") or "").strip()
        if not title: _admin_redirect(self, "/admin/builds", "Title is required.", "error"); return
        m.create_backup_note("admin-build-save")
        if idx < 0:
            p = {"slug": m.slugify(title), "steps": [],
                 "created": datetime.now().isoformat(timespec="seconds")}
            builds.insert(0, p); idx = 0
        else:
            p = builds[idx]
        p["title"]  = title
        p["status"] = m.normalize_status(form.get("status","Complete"))
        p["description"] = form.get("description","")
        p["tags"]    = _csv("tags"); p["bullets"] = _lines("bullets")
        cover = m.resolve_image_input(form.get("cover_image",""), title)
        p["cover_image"] = cover; p["image"] = cover
        p.setdefault("images",[]); p.setdefault("links",[])
        p["updated"] = datetime.now().isoformat(timespec="seconds")
        if not p.get("slug"): p["slug"] = m.slugify(title)
        m.save_projects(builds); m.rebuild_all(builds)
        _admin_redirect(self, "/admin/builds", f"Saved: {title}", "success"); return

    # ── Add build story section ──
    if path == "/admin/builds/story/add":
        builds = m.load_projects()
        idx    = _safe_idx(form.get("idx","-1"), builds)
        if idx < 0: _admin_redirect(self, "/admin/builds", "Not found.", "error"); return
        m.create_backup_note("admin-build-story-add")
        steps = builds[idx].get("steps") or []
        step_no = len(steps)+1
        title_s = (form.get("title") or f"Part {step_no}").strip()
        img = m.resolve_image_input(form.get("image_path",""), f"{builds[idx].get('title','build')}-step-{step_no}")
        steps.append({"title": title_s, "text": form.get("text",""), "image": img, "alt": title_s})
        builds[idx]["steps"] = steps
        builds[idx]["updated"] = datetime.now().isoformat(timespec="seconds")
        m.save_projects(builds); m.rebuild_project_pages(builds)
        _admin_redirect(self, f"/admin/builds/story?idx={idx}", "Section added.", "success"); return

    # ── Save build story section ──
    if path == "/admin/builds/story/save":
        builds = m.load_projects()
        idx    = _safe_idx(form.get("idx","-1"), builds)
        step   = _safe_idx(form.get("step","-1"), builds[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/builds", "Not found.", "error"); return
        m.create_backup_note("admin-build-story-save")
        steps = builds[idx].get("steps") or []
        title_s = (form.get("title") or steps[step].get("title") or "Part").strip()
        steps[step]["title"] = title_s
        steps[step]["text"]  = form.get("text","")
        steps[step]["image"] = m.resolve_image_input(form.get("image",""), f"build-step-{step+1}")
        builds[idx]["steps"] = steps
        builds[idx]["updated"] = datetime.now().isoformat(timespec="seconds")
        m.save_projects(builds); m.rebuild_project_pages(builds)
        _admin_redirect(self, f"/admin/builds/story?idx={idx}", "Section saved.", "success"); return

    # ── Save repair ──
    if path == "/admin/repairs/save":
        repairs = m.load_repairs()
        idx     = _safe_idx(form.get("idx","-1"), repairs)
        title   = (form.get("title") or "").strip()
        if not title: _admin_redirect(self, "/admin/repairs", "Title is required.", "error"); return
        m.create_backup_note("admin-repair-save")
        if idx < 0:
            r = {"created": datetime.now().isoformat(timespec="seconds")}
            repairs.insert(0, r); idx = 0
        else:
            r = repairs[idx]
        r["title"] = title
        for k in ("date","status","device","symptom","diagnosis","fix","notes"):
            r[k] = form.get(k,"")
        r["tags"]  = _csv("tags")
        r["image"] = m.resolve_image_input(form.get("image",""), title)
        r["alt"]   = form.get("alt","") or title
        r["updated"] = datetime.now().isoformat(timespec="seconds")
        m.save_repairs(repairs); m.rebuild_repairs_page()
        _admin_redirect(self, "/admin/repairs", f"Saved: {title}", "success"); return

    # ── Add guitar story section ──
    if path == "/admin/guitars/story/add":
        guitars = m.load_guitars()
        idx     = _safe_idx(form.get("idx","-1"), guitars)
        if idx < 0: _admin_redirect(self, "/admin/guitars", "Not found.", "error"); return
        m.create_backup_note("admin-guitar-story-add")
        steps   = guitars[idx].get("steps") or []
        step_no = len(steps)+1
        title_s = (form.get("title") or f"Part {step_no}").strip()
        img = m.resolve_image_input(form.get("image_path",""), f"{guitars[idx].get('title','guitar')}-step-{step_no}")
        steps.append({"title": title_s, "text": form.get("text",""), "image": img, "alt": title_s})
        guitars[idx]["steps"] = steps
        guitars[idx]["updated"] = datetime.now().isoformat(timespec="seconds")
        m.save_guitars(guitars); m.rebuild_guitar_pages(guitars)
        _admin_redirect(self, f"/admin/guitars/story?idx={idx}", "Section added.", "success"); return

    # ── Save guitar story section ──
    if path == "/admin/guitars/story/save":
        guitars = m.load_guitars()
        idx     = _safe_idx(form.get("idx","-1"), guitars)
        step    = _safe_idx(form.get("step","-1"), guitars[idx].get("steps") or [] if idx >= 0 else [])
        if idx < 0 or step < 0: _admin_redirect(self, "/admin/guitars", "Not found.", "error"); return
        m.create_backup_note("admin-guitar-story-save")
        steps = guitars[idx].get("steps") or []
        title_s = (form.get("title") or steps[step].get("title") or "Part").strip()
        steps[step]["title"] = title_s
        steps[step]["text"]  = form.get("text","")
        steps[step]["image"] = m.resolve_image_input(form.get("image",""), f"guitar-step-{step+1}")
        guitars[idx]["steps"] = steps
        guitars[idx]["updated"] = datetime.now().isoformat(timespec="seconds")
        m.save_guitars(guitars); m.rebuild_guitar_pages(guitars)
        _admin_redirect(self, f"/admin/guitars/story?idx={idx}", "Section saved.", "success"); return

    # ── Site settings ──
    if path == "/admin/site/save":
        m.create_backup_note("admin-site-save")
        site = m.load_site()
        for k in ("name","tagline","build_log_note","about_text","email","instagram_url","youtube_url"):
            site[k] = form.get(k,"")
        site["tags"] = _csv("tags")
        m.save_site(site); m.rebuild_all()
        _admin_redirect(self, "/admin/site", "Site settings saved.", "success"); return

    # Publish POST (commit message)
    if path == "/admin/publish/go":
        ok, msg = run_publish(form.get("message",""))
        mt = "success" if ok else "error"
        _admin_redirect(self, "/admin/publish", msg, mt); return

    _admin_redirect(self, "/admin", "Unknown action.", "error")


# Patch the handler
DashboardHandler.do_GET  = lambda self: _admin_do_GET(self)
DashboardHandler.do_POST = lambda self: _admin_do_POST(self)
