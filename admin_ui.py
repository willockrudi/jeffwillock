"""
admin_ui.py — JC Custom full admin UI
Beautiful file-manager-style interface replacing the manage.py CLI menu.
Served by dashboard_server.py at /admin

Sections:
  /admin                — home (quick stats + actions)
  /admin/guitars        — guitar portfolio manager
  /admin/builds         — builds manager
  /admin/repairs        — repairs manager
  /admin/site           — site settings
  /admin/publish        — rebuild + publish + status
  /admin/backups        — backup list + restore
"""

import html
import os
from datetime import datetime
from pathlib import Path

# ── Shared CSS + shell ────────────────────────────────────────────────────────

ADMIN_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');

:root {
  --bg:       #1a1510;
  --bg-alt:   #221c17;
  --surface:  #2c2420;
  --surface2: #362e28;
  --surface3: #3f3530;
  --text:     #f0ebe4;
  --muted:    #b8a898;
  --accent:   #c96a2b;
  --accent2:  #e8813a;
  --green:    #7ad88c;
  --red:      #e05555;
  --blue:     #7ab8d8;
  --border:   #453830;
  --radius:   14px;
  --sidebar:  240px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body {
  font-family: 'DM Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  font-size: 16px;
  line-height: 1.5;
}

a { color: inherit; text-decoration: none; }

/* ── Layout ── */
.shell { display: flex; min-height: 100vh; }

/* ── Sidebar ── */
.sidebar {
  width: var(--sidebar);
  background: var(--bg-alt);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0; left: 0; bottom: 0;
  z-index: 50;
  overflow-y: auto;
}

.sidebar-logo {
  padding: 22px 20px 18px;
  border-bottom: 1px solid var(--border);
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.5rem;
  letter-spacing: 0.05em;
  color: var(--text);
}
.sidebar-logo span { color: var(--accent); }

.nav-section {
  padding: 14px 12px 6px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  margin: 1px 8px;
  border-radius: 10px;
  color: var(--muted);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  text-decoration: none;
}
.nav-item:hover { background: var(--surface); color: var(--text); }
.nav-item.active { background: var(--surface2); color: var(--accent); font-weight: 600; }
.nav-item .icon { font-size: 1.1rem; width: 22px; text-align: center; }

.sidebar-bottom {
  margin-top: auto;
  padding: 16px 12px;
  border-top: 1px solid var(--border);
}

/* ── Main content ── */
.main {
  margin-left: var(--sidebar);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.topbar {
  background: var(--bg-alt);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: sticky;
  top: 0;
  z-index: 40;
}

.page-title {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.6rem;
  letter-spacing: 0.05em;
}

.topbar-actions { display: flex; gap: 10px; align-items: center; }

.content { padding: 32px; flex: 1; }

/* ── Buttons ── */
.btn {
  font-family: 'DM Sans', sans-serif;
  font-weight: 600;
  font-size: 0.95rem;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  padding: 10px 20px;
  min-height: 42px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: transform 0.12s, background 0.15s, opacity 0.15s;
  white-space: nowrap;
}
.btn:active { transform: scale(0.97); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-primary  { background: var(--accent);  color: #fff; }
.btn-primary:hover  { background: var(--accent2); }
.btn-success  { background: #2d6e3e; color: #fff; }
.btn-success:hover  { background: #378a4d; }
.btn-ghost    { background: var(--surface2); color: var(--text); border: 1px solid var(--border); }
.btn-ghost:hover    { border-color: var(--accent); color: var(--accent); }
.btn-danger   { background: transparent; color: var(--red); border: 1px solid var(--red); }
.btn-danger:hover   { background: var(--red); color: #fff; }
.btn-sm { padding: 6px 14px; min-height: 32px; font-size: 0.85rem; }

/* ── Cards ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px;
  margin-bottom: 20px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border);
}
.card-title {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.2rem;
  letter-spacing: 0.05em;
}

/* ── File list (the "file manager" rows) ── */
.file-list { display: flex; flex-direction: column; gap: 2px; }

.file-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: background 0.12s, border-color 0.12s;
  cursor: pointer;
}
.file-row:hover { background: var(--surface2); border-color: var(--border); }

.file-icon {
  font-size: 1.4rem;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--surface2);
  border-radius: 8px;
  flex-shrink: 0;
}

.file-info { flex: 1; min-width: 0; }
.file-name {
  font-weight: 600;
  font-size: 1rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.file-meta { font-size: 0.82rem; color: var(--muted); margin-top: 1px; }

.file-actions { display: flex; gap: 6px; flex-shrink: 0; }

.status-pill {
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 999px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}
.pill-progress { background: rgba(201,106,43,0.18); color: #ffb57d; border: 1px solid rgba(255,181,125,0.3); }
.pill-complete { background: rgba(70,150,90,0.18); color: #7ad88c; border: 1px solid rgba(122,216,140,0.3); }
.pill-available { background: rgba(122,184,216,0.15); color: #7ab8d8; border: 1px solid rgba(122,184,216,0.3); }
.pill-sold { background: rgba(180,180,180,0.1); color: var(--muted); border: 1px solid var(--border); }
.pill-archived { background: rgba(180,180,180,0.1); color: var(--muted); border: 1px solid var(--border); }
.pill-fixed { background: rgba(70,150,90,0.18); color: #7ad88c; border: 1px solid rgba(122,216,140,0.3); }

/* ── Forms ── */
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18px;
}
.form-grid.single { grid-template-columns: 1fr; }
.form-grid.thirds { grid-template-columns: 1fr 1fr 1fr; }

.field { display: flex; flex-direction: column; gap: 6px; }
.field.span2 { grid-column: span 2; }
.field.span3 { grid-column: span 3; }

label {
  font-size: 0.82rem;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

input, textarea, select {
  width: 100%;
  background: var(--surface2);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  font-family: 'DM Sans', sans-serif;
  font-size: 0.97rem;
  padding: 10px 14px;
  transition: border-color 0.15s;
  outline: none;
}
input:focus, textarea:focus, select:focus { border-color: var(--accent); }
textarea { min-height: 90px; resize: vertical; }
select option { background: var(--surface2); }

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}

/* ── Stats row ── */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}
.stat-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 22px;
}
.stat-number {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 2.8rem;
  line-height: 1;
  color: var(--accent);
}
.stat-label {
  font-size: 0.82rem;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-top: 4px;
}

/* ── Alerts / messages ── */
.alert {
  padding: 12px 18px;
  border-radius: 10px;
  margin-bottom: 20px;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 10px;
}
.alert-success { background: rgba(70,150,90,0.15); border: 1px solid rgba(122,216,140,0.3); color: var(--green); }
.alert-error   { background: rgba(200,60,60,0.15); border: 1px solid rgba(200,60,60,0.3); color: #f08080; }
.alert-info    { background: rgba(122,184,216,0.12); border: 1px solid rgba(122,184,216,0.3); color: var(--blue); }

/* ── Confirm modal ── */
.modal-overlay {
  display: none;
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.7);
  z-index: 200;
  align-items: center;
  justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 32px;
  max-width: 420px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.modal h3 { font-family: 'Bebas Neue', sans-serif; font-size: 1.5rem; margin-bottom: 12px; }
.modal p { color: var(--muted); margin-bottom: 24px; }
.modal-actions { display: flex; gap: 10px; justify-content: flex-end; }

/* ── Section divider ── */
.section-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 24px 0 10px;
}

/* ── Story steps ── */
.step-row {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  background: var(--surface2);
  border-radius: 10px;
  margin-bottom: 8px;
  border: 1px solid var(--border);
}
.step-number {
  font-family: 'Bebas Neue', sans-serif;
  font-size: 1.4rem;
  color: var(--accent);
  width: 30px;
  flex-shrink: 0;
}
.step-info { flex: 1; }
.step-title { font-weight: 600; margin-bottom: 2px; }
.step-text { font-size: 0.88rem; color: var(--muted); }

/* ── Empty state ── */
.empty-state {
  text-align: center;
  padding: 48px 24px;
  color: var(--muted);
}
.empty-state .empty-icon { font-size: 3rem; margin-bottom: 14px; }
.empty-state p { font-size: 1rem; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

/* ── Mobile (iPad) ── */
@media (max-width: 768px) {
  :root { --sidebar: 0px; }
  .sidebar { display: none; }
  .main { margin-left: 0; }
  .content { padding: 20px 16px; }
  .form-grid { grid-template-columns: 1fr; }
  .form-grid.thirds { grid-template-columns: 1fr; }
  .field.span2, .field.span3 { grid-column: span 1; }
  .topbar { padding: 14px 16px; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
"""


def _pill(status: str) -> str:
    s = (status or "").lower()
    cls = {
        "in progress": "pill-progress",
        "complete":    "pill-complete",
        "available":   "pill-available",
        "sold":        "pill-sold",
        "archived":    "pill-archived",
        "fixed":       "pill-fixed",
        "monitoring":  "pill-progress",
    }.get(s, "pill-archived")
    return f'<span class="status-pill {cls}">{html.escape(status)}</span>'


def _shell(page: str, content: str, message: str = "", msg_type: str = "success") -> str:
    alert = ""
    if message:
        alert = f'<div class="alert alert-{msg_type}">{"✅" if msg_type=="success" else "❌" if msg_type=="error" else "ℹ"} {html.escape(message)}</div>'

    nav_items = [
        ("/admin",          "🏠", "Home",          "home"),
        ("/admin/guitars",  "🎸", "Guitars",        "guitars"),
        ("/admin/builds",   "🔨", "Builds",         "builds"),
        ("/admin/repairs",  "🔧", "Repairs",        "repairs"),
        ("/admin/site",     "⚙️",  "Site Settings",  "site"),
        ("/admin/publish",  "🚀", "Publish",        "publish"),
        ("/admin/backups",  "🗂",  "Backups",        "backups"),
    ]

    nav_html = ""
    for href, icon, label, key in nav_items:
        active = "active" if page == key else ""
        nav_html += f'<a href="{href}" class="nav-item {active}"><span class="icon">{icon}</span>{label}</a>\n'

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>JC Custom — Admin</title>
<style>{ADMIN_CSS}</style>
</head>
<body>
<div class="shell">

  <nav class="sidebar">
    <div class="sidebar-logo">JC <span>Custom</span></div>
    <div class="nav-section">Content</div>
    {nav_html}
    <div class="sidebar-bottom">
      <a href="/" class="nav-item"><span class="icon">📺</span>Dashboard</a>
    </div>
  </nav>

  <div class="main">
    <div class="topbar">
      <div class="page-title" id="pageTitle"></div>
      <div class="topbar-actions" id="topbarActions"></div>
    </div>
    <div class="content">
      {alert}
      {content}
    </div>
  </div>

</div>

<!-- Confirm modal -->
<div class="modal-overlay" id="confirmModal">
  <div class="modal">
    <h3 id="modalTitle">Are you sure?</h3>
    <p id="modalBody">This cannot be undone.</p>
    <div class="modal-actions">
      <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
      <button class="btn btn-danger" id="modalConfirm">Delete</button>
    </div>
  </div>
</div>

<script>
// ── Modal helpers ──
function openModal(title, body, onConfirm) {{
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').textContent = body;
  document.getElementById('modalConfirm').onclick = () => {{ closeModal(); onConfirm(); }};
  document.getElementById('confirmModal').classList.add('open');
}}
function closeModal() {{
  document.getElementById('confirmModal').classList.remove('open');
}}

// ── Form submit helper ──
function submitForm(formId, successMsg) {{
  const form = document.getElementById(formId);
  if (!form) return;
  const btn = form.querySelector('button[type=submit]');
  if (btn) {{ btn.disabled = true; btn.textContent = 'Saving...'; }}
  form.submit();
}}

// ── Auto-dismiss alerts ──
setTimeout(() => {{
  const a = document.querySelector('.alert');
  if (a) a.style.transition = 'opacity 0.5s', a.style.opacity = '0',
    setTimeout(() => a.remove(), 500);
}}, 4000);
</script>
</body>
</html>"""


# ── Page builders ─────────────────────────────────────────────────────────────

def page_home(guitars, builds, repairs, site) -> str:
    n_guitars   = len(guitars)
    n_builds    = len(builds)
    n_repairs   = len(repairs)
    n_progress  = sum(1 for g in guitars if (g.get("status") or "").lower() == "in progress")

    recent_guitars = guitars[:3]
    recent_html = ""
    for g in recent_guitars:
        recent_html += f"""
<div class="file-row">
  <div class="file-icon">🎸</div>
  <div class="file-info">
    <div class="file-name">#{g.get('number','')} {html.escape(g.get('title','Untitled'))}</div>
    <div class="file-meta">{html.escape(g.get('body_wood','') or '')} {('· ' + html.escape(g.get('customer_name',''))) if g.get('customer_name') else ''}</div>
  </div>
  {_pill(g.get('status','In Progress'))}
  <div class="file-actions">
    <a href="/admin/guitars/edit?idx={guitars.index(g)}" class="btn btn-ghost btn-sm">Edit</a>
  </div>
</div>"""

    if not recent_html:
        recent_html = '<div class="empty-state"><div class="empty-icon">🎸</div><p>No guitars yet — add one to get started.</p></div>'

    return f"""
<script>
  document.getElementById('pageTitle').textContent = 'Home';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/guitars/new" class="btn btn-primary">+ Add Guitar</a>';
</script>

<div class="stats-row">
  <div class="stat-card">
    <div class="stat-number">{n_guitars}</div>
    <div class="stat-label">Guitars</div>
  </div>
  <div class="stat-card">
    <div class="stat-number">{n_progress}</div>
    <div class="stat-label">In Progress</div>
  </div>
  <div class="stat-card">
    <div class="stat-number">{n_builds}</div>
    <div class="stat-label">Builds</div>
  </div>
  <div class="stat-card">
    <div class="stat-number">{n_repairs}</div>
    <div class="stat-label">Repairs</div>
  </div>
</div>

<div class="card">
  <div class="card-header">
    <span class="card-title">Recent Guitars</span>
    <a href="/admin/guitars" class="btn btn-ghost btn-sm">View all</a>
  </div>
  <div class="file-list">{recent_html}</div>
</div>

<div class="card">
  <div class="card-header"><span class="card-title">Quick Actions</span></div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;">
    <a href="/admin/guitars/new"  class="btn btn-primary">🎸 Add Guitar</a>
    <a href="/admin/builds/new"   class="btn btn-ghost">🔨 Add Build</a>
    <a href="/admin/repairs/new"  class="btn btn-ghost">🔧 Add Repair</a>
    <a href="/admin/publish"      class="btn btn-ghost">🚀 Publish Site</a>
  </div>
</div>"""


def page_guitars_list(guitars) -> str:
    rows = ""
    for i, g in enumerate(guitars):
        specs = " · ".join(filter(None, [g.get("body_wood"), g.get("fretboard")]))
        customer = g.get("customer_name", "")
        meta = " · ".join(filter(None, [specs, f"For: {customer}" if customer else ""]))
        rows += f"""
<div class="file-row">
  <div class="file-icon">🎸</div>
  <div class="file-info">
    <div class="file-name">#{g.get('number','')} {html.escape(g.get('title','Untitled'))}</div>
    <div class="file-meta">{html.escape(meta)}</div>
  </div>
  {_pill(g.get('status','In Progress'))}
  <div class="file-actions">
    <a href="/admin/guitars/story?idx={i}" class="btn btn-ghost btn-sm">Story</a>
    <a href="/admin/guitars/edit?idx={i}"  class="btn btn-ghost btn-sm">Edit</a>
    <button class="btn btn-danger btn-sm"
      onclick="openModal('Delete Guitar','Delete #{g.get("number","")} {html.escape(g.get("title","Untitled")).replace("'","\\'")}? This cannot be undone.',
        ()=>window.location='/admin/guitars/delete?idx={i}')">Delete</button>
  </div>
</div>"""

    if not rows:
        rows = '<div class="empty-state"><div class="empty-icon">🎸</div><p>No guitars yet.</p></div>'

    return f"""
<script>
  document.getElementById('pageTitle').textContent = 'Guitars';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/guitars/new" class="btn btn-primary">+ New Guitar</a>';
</script>
<div class="card">
  <div class="file-list">{rows}</div>
</div>"""


def _guitar_form(g: dict = None, action: str = "/admin/guitars/save", idx: int = -1) -> str:
    g = g or {}
    v = lambda k, d="": html.escape(str(g.get(k, d) or ""), quote=True)
    status_opts = ""
    for s in ["In Progress", "Complete", "Available", "Sold", "Archived"]:
        sel = "selected" if (g.get("status") or "In Progress") == s else ""
        status_opts += f'<option {sel}>{s}</option>'
    idx_field = f'<input type="hidden" name="idx" value="{idx}">' if idx >= 0 else ""
    return f"""
<form method="post" action="{action}" id="guitarForm">
  {idx_field}
  <div class="form-grid">
    <div class="field">
      <label>Guitar Name / Title</label>
      <input name="title" value="{v('title')}" required placeholder="e.g. The Tele" />
    </div>
    <div class="field">
      <label>Status</label>
      <select name="status">{status_opts}</select>
    </div>
    <div class="field span2">
      <label>Description</label>
      <textarea name="description">{html.escape(g.get('description','') or '')}</textarea>
    </div>
  </div>

  <div class="section-label">Specs</div>
  <div class="form-grid thirds">
    <div class="field"><label>Body Wood</label><input name="body_wood" value="{v('body_wood')}" /></div>
    <div class="field"><label>Neck Wood</label><input name="neck_wood" value="{v('neck_wood')}" /></div>
    <div class="field"><label>Fretboard</label><input name="fretboard" value="{v('fretboard')}" /></div>
    <div class="field"><label>Hardware</label><input name="hardware" value="{v('hardware')}" /></div>
    <div class="field"><label>Pickups</label><input name="pickups" value="{v('pickups')}" /></div>
    <div class="field"><label>Finish</label><input name="finish" value="{v('finish')}" /></div>
    <div class="field"><label>Scale Length</label><input name="scale_length" value="{v('scale_length')}" /></div>
    <div class="field"><label>Est. Completion</label><input name="estimated_completion" value="{v('estimated_completion')}" placeholder="e.g. June 2026" /></div>
    <div class="field"><label>Cover Image Path</label><input name="cover_image" value="{v('cover_image')}" placeholder="images/photo.jpg" /></div>
  </div>

  <div class="section-label">Order</div>
  <div class="form-grid thirds">
    <div class="field"><label>Price ($)</label><input name="price" type="number" step="0.01" value="{v('price')}" /></div>
    <div class="field"><label>Customer Name</label><input name="customer_name" value="{v('customer_name')}" /></div>
    <div class="field"><label>Deposit Paid ($)</label><input name="deposit_paid" type="number" step="0.01" value="{v('deposit_paid')}" /></div>
    <div class="field"><label>Balance Due ($)</label><input name="balance_due" type="number" step="0.01" value="{v('balance_due')}" /></div>
    <div class="field span2"><label>Customer Notes</label><textarea name="customer_notes">{html.escape(g.get('customer_notes','') or '')}</textarea></div>
  </div>

  <div class="section-label">Tags & Notes</div>
  <div class="form-grid">
    <div class="field"><label>Tags (comma-separated)</label><input name="tags" value="{html.escape(','.join(g.get('tags') or []), quote=True)}" /></div>
    <div class="field"><label>Bullets (one per line)</label><textarea name="bullets">{html.escape(chr(10).join(g.get('bullets') or []))}</textarea></div>
  </div>

  <div class="form-actions">
    <button type="submit" class="btn btn-primary">💾 Save Guitar</button>
    <a href="/admin/guitars" class="btn btn-ghost">Cancel</a>
  </div>
</form>"""


def page_guitar_new() -> str:
    return f"""
<script>document.getElementById('pageTitle').textContent = 'New Guitar';</script>
<div class="card">{_guitar_form(action="/admin/guitars/save")}</div>"""


def page_guitar_edit(g: dict, idx: int) -> str:
    title = f"#{g.get('number','')} {g.get('title','Untitled')}"
    return f"""
<script>document.getElementById('pageTitle').textContent = '{html.escape(title)}';</script>
<div class="card">{_guitar_form(g=g, action="/admin/guitars/save", idx=idx)}</div>"""


def page_guitar_story(g: dict, idx: int) -> str:
    steps = g.get("steps") or []
    steps_html = ""
    for i, s in enumerate(steps):
        img_hint = f" 📷" if s.get("image") else ""
        steps_html += f"""
<div class="step-row">
  <div class="step-number">{i+1}</div>
  <div class="step-info">
    <div class="step-title">{html.escape(s.get('title',''))}{img_hint}</div>
    <div class="step-text">{html.escape((s.get('text','') or '')[:120])}{'…' if len(s.get('text','') or '') > 120 else ''}</div>
  </div>
  <div class="file-actions">
    <a href="/admin/guitars/story/edit?idx={idx}&step={i}" class="btn btn-ghost btn-sm">Edit</a>
    <button class="btn btn-danger btn-sm"
      onclick="openModal('Delete Section','Delete section {i+1}?',
        ()=>window.location='/admin/guitars/story/delete?idx={idx}&step={i}')">Delete</button>
  </div>
</div>"""

    if not steps_html:
        steps_html = '<div class="empty-state"><div class="empty-icon">📖</div><p>No story sections yet.</p></div>'

    title = f"#{g.get('number','')} {g.get('title','Untitled')} — Story"
    return f"""
<script>
  document.getElementById('pageTitle').textContent = '{html.escape(title)}';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/guitars" class="btn btn-ghost btn-sm">← Guitars</a>';
</script>
<div class="card">
  <div class="card-header">
    <span class="card-title">Build Story Sections</span>
  </div>
  {steps_html}
</div>

<div class="card">
  <div class="card-header"><span class="card-title">Add Section</span></div>
  <form method="post" action="/admin/guitars/story/add">
    <input type="hidden" name="idx" value="{idx}">
    <div class="form-grid">
      <div class="field"><label>Section Title</label><input name="title" placeholder="Part {len(steps)+1}" /></div>
      <div class="field"><label>Image Path</label><input name="image_path" placeholder="images/photo.jpg" /></div>
      <div class="field span2"><label>Text</label><textarea name="text"></textarea></div>
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">+ Add Section</button>
    </div>
  </form>
</div>"""


def _build_form(p: dict = None, action: str = "/admin/builds/save", idx: int = -1) -> str:
    p = p or {}
    v = lambda k, d="": html.escape(str(p.get(k, d) or ""), quote=True)
    status_opts = ""
    for s in ["Complete", "In Progress", "Archived"]:
        sel = "selected" if (p.get("status") or "Complete") == s else ""
        status_opts += f'<option {sel}>{s}</option>'
    idx_field = f'<input type="hidden" name="idx" value="{idx}">' if idx >= 0 else ""
    return f"""
<form method="post" action="{action}">
  {idx_field}
  <div class="form-grid">
    <div class="field"><label>Title</label><input name="title" value="{v('title')}" required /></div>
    <div class="field"><label>Status</label><select name="status">{status_opts}</select></div>
    <div class="field span2"><label>Description</label><textarea name="description">{html.escape(p.get('description','') or '')}</textarea></div>
    <div class="field"><label>Tags (comma-separated)</label><input name="tags" value="{html.escape(','.join(p.get('tags') or []), quote=True)}" /></div>
    <div class="field"><label>Cover Image Path</label><input name="cover_image" value="{v('cover_image') or v('image')}" /></div>
    <div class="field span2"><label>Bullets (one per line)</label><textarea name="bullets">{html.escape(chr(10).join(p.get('bullets') or []))}</textarea></div>
  </div>
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">💾 Save Build</button>
    <a href="/admin/builds" class="btn btn-ghost">Cancel</a>
  </div>
</form>"""


def page_builds_list(builds) -> str:
    rows = ""
    for i, p in enumerate(builds):
        rows += f"""
<div class="file-row">
  <div class="file-icon">🔨</div>
  <div class="file-info">
    <div class="file-name">{html.escape(p.get('title','Untitled'))}</div>
    <div class="file-meta">{html.escape(','.join(p.get('tags') or []))}</div>
  </div>
  {_pill(p.get('status','Complete'))}
  <div class="file-actions">
    <a href="/admin/builds/story?idx={i}" class="btn btn-ghost btn-sm">Story</a>
    <a href="/admin/builds/edit?idx={i}"  class="btn btn-ghost btn-sm">Edit</a>
    <button class="btn btn-danger btn-sm"
      onclick="openModal('Delete Build','Delete \\'{html.escape(p.get("title","")).replace("'","\\'")}\\' permanently?',
        ()=>window.location='/admin/builds/delete?idx={i}')">Delete</button>
  </div>
</div>"""
    if not rows:
        rows = '<div class="empty-state"><div class="empty-icon">🔨</div><p>No builds yet.</p></div>'
    return f"""
<script>
  document.getElementById('pageTitle').textContent = 'Builds';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/builds/new" class="btn btn-primary">+ New Build</a>';
</script>
<div class="card"><div class="file-list">{rows}</div></div>"""


def page_builds_new() -> str:
    return """<script>document.getElementById('pageTitle').textContent = 'New Build';</script>
<div class="card">""" + _build_form() + "</div>"


def page_builds_edit(p: dict, idx: int) -> str:
    return f"""<script>document.getElementById('pageTitle').textContent = 'Edit Build';</script>
<div class="card">{_build_form(p=p, action="/admin/builds/save", idx=idx)}</div>"""


def page_builds_story(p: dict, idx: int) -> str:
    steps = p.get("steps") or []
    steps_html = ""
    for i, s in enumerate(steps):
        img_hint = " 📷" if s.get("image") else ""
        steps_html += f"""
<div class="step-row">
  <div class="step-number">{i+1}</div>
  <div class="step-info">
    <div class="step-title">{html.escape(s.get('title',''))}{img_hint}</div>
    <div class="step-text">{html.escape((s.get('text','') or '')[:120])}</div>
  </div>
  <div class="file-actions">
    <a href="/admin/builds/story/edit?idx={idx}&step={i}" class="btn btn-ghost btn-sm">Edit</a>
    <button class="btn btn-danger btn-sm"
      onclick="openModal('Delete Section','Delete section {i+1}?',
        ()=>window.location='/admin/builds/story/delete?idx={idx}&step={i}')">Delete</button>
  </div>
</div>"""
    if not steps_html:
        steps_html = '<div class="empty-state"><div class="empty-icon">📖</div><p>No sections yet.</p></div>'
    return f"""
<script>
  document.getElementById('pageTitle').textContent = '{html.escape(p.get("title","Build"))} — Story';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/builds" class="btn btn-ghost btn-sm">← Builds</a>';
</script>
<div class="card">
  <div class="card-header"><span class="card-title">Story Sections</span></div>
  {steps_html}
</div>
<div class="card">
  <div class="card-header"><span class="card-title">Add Section</span></div>
  <form method="post" action="/admin/builds/story/add">
    <input type="hidden" name="idx" value="{idx}">
    <div class="form-grid">
      <div class="field"><label>Section Title</label><input name="title" placeholder="Part {len(steps)+1}" /></div>
      <div class="field"><label>Image Path</label><input name="image_path" placeholder="images/photo.jpg" /></div>
      <div class="field span2"><label>Text</label><textarea name="text"></textarea></div>
    </div>
    <div class="form-actions"><button type="submit" class="btn btn-primary">+ Add Section</button></div>
  </form>
</div>"""


def _repair_form(r: dict = None, action: str = "/admin/repairs/save", idx: int = -1) -> str:
    r = r or {}
    v = lambda k, d="": html.escape(str(r.get(k, d) or ""), quote=True)
    idx_field = f'<input type="hidden" name="idx" value="{idx}">' if idx >= 0 else ""
    today = datetime.now().strftime("%Y-%m-%d")
    return f"""
<form method="post" action="{action}">
  {idx_field}
  <div class="form-grid">
    <div class="field"><label>Title</label><input name="title" value="{v('title')}" required /></div>
    <div class="field"><label>Date</label><input name="date" value="{v('date', today)}" /></div>
    <div class="field"><label>Status</label><input name="status" value="{v('status','Fixed')}" /></div>
    <div class="field"><label>Instrument / Device</label><input name="device" value="{v('device')}" /></div>
    <div class="field span2"><label>Symptom</label><textarea name="symptom">{html.escape(r.get('symptom','') or '')}</textarea></div>
    <div class="field span2"><label>Diagnosis</label><textarea name="diagnosis">{html.escape(r.get('diagnosis','') or '')}</textarea></div>
    <div class="field span2"><label>Fix / What Worked</label><textarea name="fix">{html.escape(r.get('fix','') or '')}</textarea></div>
    <div class="field"><label>Tags (comma-separated)</label><input name="tags" value="{html.escape(','.join(r.get('tags') or []), quote=True)}" /></div>
    <div class="field"><label>Photo Path</label><input name="image" value="{v('image')}" /></div>
    <div class="field span2"><label>Notes</label><textarea name="notes">{html.escape(r.get('notes','') or '')}</textarea></div>
  </div>
  <div class="form-actions">
    <button type="submit" class="btn btn-primary">💾 Save Repair</button>
    <a href="/admin/repairs" class="btn btn-ghost">Cancel</a>
  </div>
</form>"""


def page_repairs_list(repairs) -> str:
    rows = ""
    for i, r in enumerate(repairs):
        rows += f"""
<div class="file-row">
  <div class="file-icon">🔧</div>
  <div class="file-info">
    <div class="file-name">{html.escape(r.get('title','Untitled Repair'))}</div>
    <div class="file-meta">{html.escape(r.get('device','') or '')} {('· ' + r.get('date','')) if r.get('date') else ''}</div>
  </div>
  {_pill(r.get('status','Fixed'))}
  <div class="file-actions">
    <a href="/admin/repairs/edit?idx={i}" class="btn btn-ghost btn-sm">Edit</a>
    <button class="btn btn-danger btn-sm"
      onclick="openModal('Delete Repair','Delete this repair entry permanently?',
        ()=>window.location='/admin/repairs/delete?idx={i}')">Delete</button>
  </div>
</div>"""
    if not rows:
        rows = '<div class="empty-state"><div class="empty-icon">🔧</div><p>No repairs yet.</p></div>'
    return f"""
<script>
  document.getElementById('pageTitle').textContent = 'Repairs';
  document.getElementById('topbarActions').innerHTML =
    '<a href="/admin/repairs/new" class="btn btn-primary">+ New Repair</a>';
</script>
<div class="card"><div class="file-list">{rows}</div></div>"""


def page_repairs_new() -> str:
    return """<script>document.getElementById('pageTitle').textContent = 'New Repair';</script>
<div class="card">""" + _repair_form() + "</div>"


def page_repairs_edit(r: dict, idx: int) -> str:
    return f"""<script>document.getElementById('pageTitle').textContent = 'Edit Repair';</script>
<div class="card">{_repair_form(r=r, action="/admin/repairs/save", idx=idx)}</div>"""


def page_site(site: dict) -> str:
    v = lambda k, d="": html.escape(str(site.get(k, d) or ""), quote=True)
    return f"""
<script>document.getElementById('pageTitle').textContent = 'Site Settings';</script>
<div class="card">
  <form method="post" action="/admin/site/save">
    <div class="form-grid">
      <div class="field"><label>Name</label><input name="name" value="{v('name')}" /></div>
      <div class="field"><label>Tagline</label><input name="tagline" value="{v('tagline')}" /></div>
      <div class="field span2"><label>About Text</label><textarea name="about_text">{html.escape(site.get('about_text','') or '')}</textarea></div>
      <div class="field"><label>Email</label><input name="email" type="email" value="{v('email')}" /></div>
      <div class="field"><label>Instagram URL</label><input name="instagram_url" value="{v('instagram_url')}" /></div>
      <div class="field"><label>YouTube URL</label><input name="youtube_url" value="{v('youtube_url')}" /></div>
      <div class="field"><label>Build Log Note</label><input name="build_log_note" value="{v('build_log_note')}" /></div>
      <div class="field"><label>About Tags (comma-separated)</label><input name="tags" value="{html.escape(','.join(site.get('tags') or []), quote=True)}" /></div>
    </div>
    <div class="form-actions">
      <button type="submit" class="btn btn-primary">💾 Save Settings</button>
    </div>
  </form>
</div>"""


def page_publish() -> str:
    return """
<script>document.getElementById('pageTitle').textContent = 'Publish';</script>
<div class="card">
  <div class="card-header"><span class="card-title">Rebuild Site</span></div>
  <p style="color:var(--muted);margin-bottom:18px;">
    Regenerates all HTML pages from JSON data. Run this after editing content.
  </p>
  <button class="btn btn-ghost" id="rebuildBtn" onclick="doRebuild()">⟳ Rebuild Now</button>
  <div id="rebuildStatus" style="margin-top:14px;"></div>
</div>

<div class="card">
  <div class="card-header"><span class="card-title">Publish to GitHub</span></div>
  <p style="color:var(--muted);margin-bottom:18px;">
    Commits all changes and pushes to GitHub Pages. Site goes live within ~30 seconds.
  </p>
  <div class="form-grid single" style="max-width:480px;">
    <div class="field">
      <label>Commit Message (optional)</label>
      <input id="commitMsg" placeholder="site update" />
    </div>
  </div>
  <div style="margin-top:14px;">
    <button class="btn btn-primary" id="publishBtn" onclick="doPublish()">🚀 Publish to GitHub</button>
  </div>
  <div id="publishStatus" style="margin-top:14px;"></div>
</div>

<script>
function doRebuild() {
  const btn = document.getElementById('rebuildBtn');
  const status = document.getElementById('rebuildStatus');
  btn.disabled = true; btn.textContent = '⟳ Rebuilding...';
  fetch('/rebuild', {method:'POST'})
    .then(r=>r.json())
    .then(d=>{
      btn.disabled = false; btn.textContent = '⟳ Rebuild Now';
      status.innerHTML = d.ok
        ? '<div class="alert alert-success">✅ ' + d.message + '</div>'
        : '<div class="alert alert-error">❌ ' + d.message + '</div>';
    });
}
function doPublish() {
  const btn = document.getElementById('publishBtn');
  const status = document.getElementById('publishStatus');
  const msg = document.getElementById('commitMsg').value;
  btn.disabled = true; btn.textContent = '🚀 Publishing...';
  fetch('/publish', {
    method:'POST',
    headers:{'Content-Type':'application/x-www-form-urlencoded'},
    body:'message='+encodeURIComponent(msg)
  })
    .then(r=>r.json())
    .then(d=>{
      btn.disabled = false; btn.textContent = '🚀 Publish to GitHub';
      status.innerHTML = d.ok
        ? '<div class="alert alert-success">✅ ' + d.message + '</div>'
        : '<div class="alert alert-error">❌ ' + d.message + '</div>';
    });
}
</script>"""


def page_backups(backups: list) -> str:
    rows = ""
    for i, name in enumerate(backups):
        parts = name.split("-")
        date_str = "-".join(parts[:3]) if len(parts) >= 3 else name
        label = "-".join(parts[3:]) if len(parts) > 3 else ""
        rows += f"""
<div class="file-row">
  <div class="file-icon">🗂</div>
  <div class="file-info">
    <div class="file-name">{html.escape(label or name)}</div>
    <div class="file-meta">{html.escape(date_str)}</div>
  </div>
  <div class="file-actions">
    <button class="btn btn-ghost btn-sm"
      onclick="openModal('Restore Backup','Restore \\'{html.escape(name)}\\' and rebuild the site?',
        ()=>window.location='/admin/backups/restore?name={html.escape(name, quote=True)}')">Restore</button>
  </div>
</div>"""
    if not rows:
        rows = '<div class="empty-state"><div class="empty-icon">🗂</div><p>No backups yet.</p></div>'

    return f"""
<script>
  document.getElementById('pageTitle').textContent = 'Backups';
  document.getElementById('topbarActions').innerHTML =
    '<button class="btn btn-ghost btn-sm" onclick="undoLast()">↩ Undo Last Change</button>';
</script>
<div class="card">
  <div class="card-header">
    <span class="card-title">Saved Backups</span>
    <span style="color:var(--muted);font-size:0.88rem;">{len(backups)} backups</span>
  </div>
  <div class="file-list">{rows}</div>
</div>
<script>
function undoLast() {{
  if (!confirm('Restore the most recent backup and rebuild?')) return;
  window.location = '/admin/backups/undo';
}}
</script>"""
