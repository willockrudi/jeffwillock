#!/usr/bin/env python3
"""
JC Custom Guitars - Bulletproof Admin System
=============================================
Crash-proof, auto-recovering, zero-friction guitar build documentation.

Features:
- Catches ALL errors gracefully
- Auto-creates missing folders
- Never crashes on bad data
- Friendly error messages
- Works offline
"""

import json
import os
import re
import shutil
import html
import subprocess
import sys
import mimetypes
import webbrowser
import traceback
import signal
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlencode, urlparse, unquote
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

# Where to look for Google Drive
DRIVE_SEARCH_PATHS = [
    "~/Google Drive/My Drive/JC Custom Guitars",
    "~/Google Drive/JC Custom Guitars", 
    "~/Library/CloudStorage/GoogleDrive-*/My Drive/JC Custom Guitars",
    "~/JC Custom Guitars",  # Local fallback
]

# Website folder (your GitHub repo)
WEBSITE_FOLDER = "~/Documents/dev/my_websites/jeffwillock"

# =============================================================================
# SAFE HELPERS - Never crash
# =============================================================================

def safe_read_json(path: str, default=None):
    """Read JSON file, return default if anything fails."""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure we return the expected type
                if default is not None:
                    if isinstance(default, list) and not isinstance(data, list):
                        log(f"Warning: Expected list in {path}, got {type(data)}")
                        return default
                    if isinstance(default, dict) and not isinstance(data, dict):
                        log(f"Warning: Expected dict in {path}, got {type(data)}")
                        return default
                return data
    except Exception as e:
        log(f"Warning: Could not read {path}: {e}")
    # Return a copy of default to avoid mutation issues
    if default is None:
        return {}
    if isinstance(default, list):
        return []
    if isinstance(default, dict):
        return {}
    return default


def safe_write_json(path: str, data):
    """Write JSON file safely with backup."""
    try:
        # Ensure directory exists
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # Write to temp file first
        temp_path = path + '.tmp'
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Then rename (atomic on most systems)
        shutil.move(temp_path, path)
        return True
    except Exception as e:
        log(f"Warning: Could not write {path}: {e}")
        traceback.print_exc()
        return False


def safe_listdir(path: str) -> list:
    """List directory, return empty list if fails."""
    try:
        if os.path.isdir(path):
            return os.listdir(path)
    except Exception as e:
        log(f"Warning: Could not list {path}: {e}")
    return []


def safe_stat(path: str):
    """Get file stats, return None if fails."""
    try:
        return os.stat(path)
    except:
        return None


def log(message: str):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def expand_path(path: str) -> str:
    """Expand ~ and environment variables in path."""
    return os.path.expandvars(os.path.expanduser(path))


# =============================================================================
# FIND FOLDERS
# =============================================================================

def find_drive_folder() -> str:
    """Find Google Drive folder, create fallback if needed."""
    import glob
    
    for pattern in DRIVE_SEARCH_PATHS:
        expanded = expand_path(pattern)
        # Handle glob patterns
        if '*' in expanded:
            matches = glob.glob(expanded)
            for match in matches:
                if os.path.isdir(match):
                    log(f"Found Drive folder: {match}")
                    return match
        elif os.path.isdir(expanded):
            log(f"Found Drive folder: {expanded}")
            return expanded
    
    # Create local fallback
    fallback = expand_path("~/JC Custom Guitars")
    os.makedirs(fallback, exist_ok=True)
    log(f"Created local folder: {fallback}")
    return fallback


def get_website_folder() -> str:
    """Get website folder path."""
    return expand_path(WEBSITE_FOLDER)


# =============================================================================
# GLOBAL STATE
# =============================================================================

class AppState:
    """Global application state - initialized once at startup."""
    drive_folder: str = ""
    website_folder: str = ""
    config: dict = {}
    
    @classmethod
    def init(cls):
        """Initialize app state."""
        cls.drive_folder = find_drive_folder()
        cls.website_folder = get_website_folder()
        cls.config = cls.load_config()
        
        # Ensure folders exist
        os.makedirs(cls.drive_folder, exist_ok=True)
        os.makedirs(os.path.join(cls.drive_folder, "_site_data"), exist_ok=True)
        
        log(f"Drive folder: {cls.drive_folder}")
        log(f"Website folder: {cls.website_folder}")
    
    @classmethod
    def load_config(cls) -> dict:
        """Load or create config."""
        config_path = os.path.join(cls.drive_folder, "_config.json")
        default = {
            "owner_name": "Jeff Willock",
            "site_name": "JC Custom Guitars",
            "created": datetime.now().isoformat(),
        }
        config = safe_read_json(config_path, default)
        # Ensure defaults
        for k, v in default.items():
            config.setdefault(k, v)
        safe_write_json(config_path, config)
        return config


# =============================================================================
# BUILD MANAGEMENT
# =============================================================================

def list_builds() -> list:
    """List all build folders with their media."""
    builds = []
    base = AppState.drive_folder
    
    for name in safe_listdir(base):
        # Skip hidden and system folders
        if name.startswith('.') or name.startswith('_'):
            continue
            
        folder = os.path.join(base, name)
        if not os.path.isdir(folder):
            continue
        
        photos = []
        videos = []
        photo_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'}
        video_exts = {'.mov', '.mp4', '.m4v', '.avi', '.mkv', '.webm'}
        
        for fname in safe_listdir(folder):
            fpath = os.path.join(folder, fname)
            if not os.path.isfile(fpath):
                continue
            
            ext = os.path.splitext(fname)[1].lower()
            stat = safe_stat(fpath)
            if not stat:
                continue
            
            info = {
                "name": fname,
                "path": fpath,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "date": datetime.fromtimestamp(stat.st_mtime).strftime("%b %d, %H:%M"),
            }
            
            if ext in photo_exts:
                photos.append(info)
            elif ext in video_exts:
                videos.append(info)
        
        # Sort newest first
        photos.sort(key=lambda x: x["mtime"], reverse=True)
        videos.sort(key=lambda x: x["mtime"], reverse=True)
        
        folder_stat = safe_stat(folder)
        mtime = folder_stat.st_mtime if folder_stat else 0
        
        builds.append({
            "name": name,
            "path": folder,
            "photos": photos,
            "videos": videos,
            "photo_count": len(photos),
            "video_count": len(videos),
            "mtime": mtime,
            "last_updated": datetime.fromtimestamp(mtime).strftime("%b %d") if mtime else "Unknown",
        })
    
    # Sort by most recent
    builds.sort(key=lambda x: x["mtime"], reverse=True)
    return builds


def create_build(name: str) -> bool:
    """Create a new build folder."""
    try:
        name = name.strip()
        if not name:
            return False
        # Sanitize name
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        folder = os.path.join(AppState.drive_folder, name)
        os.makedirs(folder, exist_ok=True)
        log(f"Created build: {name}")
        return True
    except Exception as e:
        log(f"Error creating build: {e}")
        return False


def get_builds_data() -> list:
    """Get saved build data for website."""
    path = os.path.join(AppState.drive_folder, "_site_data", "builds.json")
    return safe_read_json(path, [])


def save_builds_data(data: list):
    """Save build data for website."""
    path = os.path.join(AppState.drive_folder, "_site_data", "builds.json")
    safe_write_json(path, data)


# =============================================================================
# WEBSITE GENERATION
# =============================================================================

def rebuild_website() -> tuple:
    """Rebuild the website."""
    try:
        website = AppState.website_folder
        if not os.path.isdir(website):
            return False, f"Website folder not found: {website}"
        
        manage = os.path.join(website, "manage.py")
        if os.path.exists(manage):
            result = subprocess.run(
                [sys.executable, manage, "rebuild"],
                cwd=website,
                capture_output=True,
                timeout=60
            )
            if result.returncode == 0:
                return True, "Website rebuilt!"
            return False, f"Rebuild error: {result.stderr.decode()[:200]}"
        
        return True, "No rebuild script found"
    except subprocess.TimeoutExpired:
        return False, "Rebuild timed out"
    except Exception as e:
        return False, f"Rebuild error: {str(e)[:200]}"


def publish_website() -> tuple:
    """Publish website to GitHub."""
    try:
        website = AppState.website_folder
        if not os.path.isdir(os.path.join(website, ".git")):
            return False, "Not a git repository"
        
        # Add all
        subprocess.run(["git", "add", "-A"], cwd=website, check=True, capture_output=True)
        
        # Commit
        msg = f"Update {datetime.now().strftime('%b %d %H:%M')}"
        subprocess.run(["git", "commit", "-m", msg], cwd=website, capture_output=True)
        
        # Push
        result = subprocess.run(["git", "push"], cwd=website, capture_output=True, timeout=120)
        if result.returncode == 0:
            return True, "Published to GitHub!"
        
        stderr = result.stderr.decode()
        if "nothing to commit" in stderr.lower() or "up to date" in stderr.lower():
            return True, "Already up to date!"
        
        return False, f"Push failed: {stderr[:200]}"
        
    except subprocess.TimeoutExpired:
        return False, "Push timed out - check internet connection"
    except Exception as e:
        return False, f"Publish error: {str(e)[:200]}"


# =============================================================================
# CSS STYLES
# =============================================================================

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    min-height: 100vh;
    color: #e4e4e7;
}

.container { max-width: 1200px; margin: 0 auto; padding: 20px; }

.header {
    background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 25px;
    text-align: center;
    box-shadow: 0 10px 40px rgba(233, 69, 96, 0.3);
}

.header h1 { font-size: 2.2em; margin-bottom: 8px; }
.header p { opacity: 0.9; }

.actions {
    display: flex;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    margin-bottom: 30px;
}

.btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 16px 28px;
    border: none;
    border-radius: 12px;
    font-size: 1.1em;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
    text-decoration: none;
    color: white;
}

.btn:hover { transform: translateY(-2px); }
.btn-primary { background: linear-gradient(135deg, #e94560, #ff6b6b); }
.btn-secondary { background: linear-gradient(135deg, #0f3460, #1a1a4e); }
.btn-success { background: linear-gradient(135deg, #00b894, #00cec9); }
.btn-small { padding: 10px 18px; font-size: 0.95em; }

.section-title {
    font-size: 1.5em;
    margin: 30px 0 15px;
    padding-left: 12px;
    border-left: 4px solid #e94560;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 20px;
}

.card {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 16px;
    overflow: hidden;
    transition: all 0.2s;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.card:hover {
    transform: translateY(-3px);
    border-color: #e94560;
}

.card-thumb {
    width: 100%;
    height: 200px;
    object-fit: cover;
    background: #2a2a4a;
}

.card-body { padding: 18px; }
.card-title { font-size: 1.3em; font-weight: 700; margin-bottom: 8px; }

.card-meta {
    display: flex;
    gap: 15px;
    color: #a0a0b0;
    font-size: 0.9em;
    margin-bottom: 12px;
}

.card-actions { display: flex; gap: 8px; }
.card-actions .btn { flex: 1; justify-content: center; }

.empty {
    text-align: center;
    padding: 60px 20px;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 16px;
    border: 2px dashed rgba(255, 255, 255, 0.1);
}

.empty-icon { font-size: 60px; margin-bottom: 15px; opacity: 0.5; }
.empty h2 { color: #e94560; margin-bottom: 10px; }
.empty p { color: #a0a0b0; margin-bottom: 20px; }

.modal-bg {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.8);
    z-index: 1000;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(4px);
}

.modal-bg.show { display: flex; }

.modal {
    background: #1a1a2e;
    border-radius: 20px;
    padding: 35px;
    max-width: 500px;
    width: 90%;
    border: 1px solid rgba(255,255,255,0.1);
}

.modal h2 { color: #e94560; margin-bottom: 20px; }
.modal label { display: block; margin: 15px 0 6px; color: #a0a0b0; font-weight: 600; }

.modal input, .modal textarea, .modal select {
    width: 100%;
    padding: 14px;
    border: 2px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    background: rgba(255,255,255,0.05);
    color: white;
    font-size: 1.05em;
}

.modal input:focus, .modal textarea:focus {
    outline: none;
    border-color: #e94560;
}

.modal-actions { display: flex; gap: 12px; margin-top: 25px; }
.modal-actions .btn { flex: 1; justify-content: center; }

.photo-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
    gap: 8px;
    margin: 12px 0;
    max-height: 250px;
    overflow-y: auto;
    padding: 8px;
    background: rgba(0,0,0,0.2);
    border-radius: 10px;
}

.photo-item {
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    border: 3px solid transparent;
    transition: all 0.15s;
}

.photo-item:hover { transform: scale(1.05); }
.photo-item.selected { border-color: #00b894; }
.photo-item img { width: 100%; height: 100%; object-fit: cover; }

.toast {
    position: fixed;
    bottom: 25px;
    left: 50%;
    transform: translateX(-50%);
    padding: 14px 28px;
    border-radius: 50px;
    font-weight: 600;
    z-index: 2000;
    animation: slideUp 0.3s;
}

.toast.success { background: linear-gradient(135deg, #00b894, #00cec9); }
.toast.error { background: linear-gradient(135deg, #e94560, #ff6b6b); }

@keyframes slideUp {
    from { transform: translateX(-50%) translateY(50px); opacity: 0; }
    to { transform: translateX(-50%) translateY(0); opacity: 1; }
}

.info-bar {
    background: rgba(255,255,255,0.05);
    padding: 15px 20px;
    border-radius: 12px;
    margin-top: 30px;
    font-size: 0.9em;
    color: #a0a0b0;
}

.info-bar code {
    background: rgba(0,0,0,0.3);
    padding: 3px 8px;
    border-radius: 4px;
    font-family: monospace;
}

@media (max-width: 600px) {
    .header h1 { font-size: 1.6em; }
    .actions { flex-direction: column; }
    .btn { width: 100%; justify-content: center; }
    .grid { grid-template-columns: 1fr; }
}
"""

# =============================================================================
# HTML TEMPLATES
# =============================================================================

def render_page(title: str, body: str, message: str = "", msg_type: str = "success") -> str:
    """Render a complete HTML page."""
    toast = ""
    if message:
        toast = f'<div class="toast {msg_type}">{html.escape(message)}</div>'
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>{CSS}</style>
</head>
<body>
    <div class="container">
        {body}
    </div>
    {toast}
    <script>
        // Auto-hide toast
        setTimeout(() => document.querySelectorAll('.toast').forEach(t => t.remove()), 4000);
        
        // Modal handling
        function openModal(id) {{
            document.getElementById(id).classList.add('show');
            const input = document.querySelector('#' + id + ' input');
            if (input) setTimeout(() => input.focus(), 100);
        }}
        function closeModal() {{
            document.querySelectorAll('.modal-bg').forEach(m => m.classList.remove('show'));
        }}
        document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});
        document.querySelectorAll('.modal-bg').forEach(m => {{
            m.addEventListener('click', e => {{ if (e.target === m) closeModal(); }});
        }});
        
        // Photo selection
        function selectPhoto(el, inputId) {{
            document.querySelectorAll('.photo-item').forEach(p => p.classList.remove('selected'));
            el.classList.add('selected');
            document.getElementById(inputId).value = el.dataset.path;
        }}
    </script>
</body>
</html>"""


def render_home(message: str = "", msg_type: str = "success") -> str:
    """Render the home page."""
    builds = list_builds()
    
    # Build cards
    cards = ""
    for b in builds:
        thumb = ""
        if b["photos"]:
            thumb = f'<img class="card-thumb" src="/media?p={html.escape(b["photos"][0]["path"])}" alt="">'
        else:
            thumb = '<div class="card-thumb" style="display:flex;align-items:center;justify-content:center;font-size:50px;">🎸</div>'
        
        cards += f"""
        <div class="card">
            {thumb}
            <div class="card-body">
                <div class="card-title">{html.escape(b["name"])}</div>
                <div class="card-meta">
                    <span>📷 {b["photo_count"]}</span>
                    <span>🎬 {b["video_count"]}</span>
                    <span>📅 {b["last_updated"]}</span>
                </div>
                <div class="card-actions">
                    <a href="/build?n={html.escape(b['name'])}" class="btn btn-primary btn-small">Open</a>
                    <a href="/edit?n={html.escape(b['name'])}" class="btn btn-secondary btn-small">Edit</a>
                </div>
            </div>
        </div>
        """
    
    if not builds:
        cards = """
        <div class="empty" style="grid-column: 1/-1;">
            <div class="empty-icon">📸</div>
            <h2>No builds yet</h2>
            <p>Create your first build, then take photos with your iPhone!</p>
            <button class="btn btn-primary" onclick="openModal('newBuildModal')">➕ Create first build</button>
        </div>
        """
    
    body = f"""
    <div class="header">
        <h1>🎸 JC Custom Guitars</h1>
        <p>Your guitar builds, photos & videos</p>
    </div>
    
    <div class="actions">
        <button class="btn btn-primary" onclick="openModal('newBuildModal')">➕ New Build</button>
        <form method="post" action="/rebuild" style="display:inline">
            <button type="submit" class="btn btn-secondary">🔄 Rebuild Site</button>
        </form>
        <form method="post" action="/publish" style="display:inline">
            <button type="submit" class="btn btn-success">🚀 Publish</button>
        </form>
    </div>
    
    <h2 class="section-title">Your Builds</h2>
    <div class="grid">{cards}</div>
    
    <div class="info-bar">
        📁 Photos sync from: <code>{html.escape(AppState.drive_folder)}</code>
    </div>
    
    <!-- New Build Modal -->
    <div class="modal-bg" id="newBuildModal">
        <div class="modal">
            <h2>➕ New Build</h2>
            <form method="post" action="/new-build">
                <label>Build name</label>
                <input type="text" name="name" placeholder="e.g. Telecaster Refinish" required>
                <p style="color:#888;margin-top:8px;font-size:0.9em">Creates a folder for your photos & videos</p>
                <div class="modal-actions">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create</button>
                </div>
            </form>
        </div>
    </div>
    """
    
    return render_page("JC Custom Guitars", body, message, msg_type)


def render_build(name: str, message: str = "") -> str:
    """Render a single build page."""
    builds = list_builds()
    build = next((b for b in builds if b["name"] == name), None)
    
    if not build:
        return render_home("Build not found", "error")
    
    # Photos grid
    photos = ""
    for p in build["photos"]:
        photos += f"""
        <div class="photo-item" onclick="window.open('/media?p={html.escape(p["path"])}')">
            <img src="/media?p={html.escape(p["path"])}" loading="lazy" alt="">
        </div>
        """
    if not photos:
        photos = '<p style="color:#888;text-align:center;padding:30px;">No photos yet</p>'
    
    # Videos list
    videos = ""
    for v in build["videos"]:
        size_mb = v["size"] / (1024*1024)
        videos += f"""
        <div style="display:flex;align-items:center;gap:12px;padding:12px;background:rgba(0,0,0,0.2);border-radius:10px;margin-bottom:8px;">
            <span style="font-size:28px;">🎬</span>
            <div style="flex:1;">
                <div style="font-weight:600;">{html.escape(v["name"])}</div>
                <div style="color:#888;font-size:0.85em;">{size_mb:.1f} MB • {v["date"]}</div>
            </div>
            <a href="/media?p={html.escape(v["path"])}&dl=1" class="btn btn-secondary btn-small">Download</a>
        </div>
        """
    if not videos:
        videos = '<p style="color:#888;text-align:center;padding:30px;">No videos yet</p>'
    
    body = f"""
    <p style="margin-bottom:15px;"><a href="/" style="color:#e94560;">← Back to all builds</a></p>
    
    <div class="header" style="text-align:left;">
        <h1>📁 {html.escape(name)}</h1>
        <p>{build["photo_count"]} photos • {build["video_count"]} videos</p>
    </div>
    
    <div class="actions" style="justify-content:flex-start;">
        <a href="/edit?n={html.escape(name)}" class="btn btn-primary">✏️ Edit for Website</a>
    </div>
    
    <h2 class="section-title">📷 Photos</h2>
    <div class="photo-grid" style="max-height:none;">{photos}</div>
    
    <h2 class="section-title">🎬 Videos</h2>
    {videos}
    """
    
    return render_page(name, body, message)


def render_edit(name: str, message: str = "") -> str:
    """Render the edit page for website configuration."""
    builds = list_builds()
    build = next((b for b in builds if b["name"] == name), None)
    
    if not build:
        return render_home("Build not found", "error")
    
    # Load existing data
    builds_data = get_builds_data()
    existing = next((b for b in builds_data if b.get("folder_name") == name), {})
    
    title = existing.get("title", name)
    description = existing.get("description", "")
    status = existing.get("status", "In Progress")
    cover = existing.get("cover_image", "")
    
    # Photo picker
    photos = ""
    for p in build["photos"]:
        selected = "selected" if cover and p["name"] in cover else ""
        photos += f"""
        <div class="photo-item {selected}" data-path="{html.escape(p["path"])}" onclick="selectPhoto(this, 'coverInput')">
            <img src="/media?p={html.escape(p["path"])}" loading="lazy" alt="">
        </div>
        """
    if not photos:
        photos = '<p style="color:#888;">No photos yet - take some first!</p>'
    
    body = f"""
    <p style="margin-bottom:15px;"><a href="/" style="color:#e94560;">← Back to all builds</a></p>
    
    <div class="header" style="text-align:left;">
        <h1>✏️ Edit for Website</h1>
        <p>Configure how "{html.escape(name)}" appears on your site</p>
    </div>
    
    <form method="post" action="/save-build" class="modal" style="display:block;max-width:700px;margin:0;">
        <input type="hidden" name="folder_name" value="{html.escape(name)}">
        
        <label>Title</label>
        <input type="text" name="title" value="{html.escape(title)}" placeholder="{html.escape(name)}">
        
        <label>Status</label>
        <select name="status">
            <option value="In Progress" {"selected" if status == "In Progress" else ""}>🛠 In Progress</option>
            <option value="Complete" {"selected" if status == "Complete" else ""}>✅ Complete</option>
        </select>
        
        <label>Description</label>
        <textarea name="description" rows="4" placeholder="Describe this build...">{html.escape(description)}</textarea>
        
        <label>Cover photo (tap to select)</label>
        <div class="photo-grid">{photos}</div>
        <input type="hidden" name="cover_image" id="coverInput" value="{html.escape(cover)}">
        
        <div class="modal-actions">
            <a href="/" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-success">💾 Save</button>
        </div>
    </form>
    """
    
    return render_page(f"Edit {name}", body, message)


# =============================================================================
# HTTP SERVER
# =============================================================================

class Handler(BaseHTTPRequestHandler):
    """HTTP request handler with comprehensive error catching."""
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def safe_respond(self, func):
        """Wrap handler in try-catch."""
        try:
            func()
        except Exception as e:
            log(f"Error handling request: {e}")
            traceback.print_exc()
            self.send_error(500, f"Server error: {str(e)[:100]}")
    
    def send_html(self, content: str, status: int = 200):
        """Send HTML response."""
        data = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def send_json(self, obj: dict, status: int = 200):
        """Send JSON response."""
        data = json.dumps(obj).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    
    def redirect(self, path: str, msg: str = "", msg_type: str = "success"):
        """Redirect with optional message."""
        target = path
        if msg:
            sep = "&" if "?" in path else "?"
            encoded_msg = urlencode({'msg': msg, 't': msg_type})
            target = f"{path}{sep}{encoded_msg}"
        self.send_response(303)
        self.send_header('Location', target)
        self.end_headers()
    
    def send_media(self, path: str, download: bool = False):
        """Send media file."""
        try:
            if not os.path.isfile(path):
                self.send_error(404)
                return
            
            mime, _ = mimetypes.guess_type(path)
            mime = mime or 'application/octet-stream'
            
            with open(path, 'rb') as f:
                data = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            
            if download:
                fname = os.path.basename(path)
                self.send_header('Content-Disposition', f'attachment; filename="{fname}"')
            else:
                self.send_header('Cache-Control', 'max-age=3600')
            
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            log(f"Error sending media: {e}")
            self.send_error(500)
    
    def parse_form(self) -> dict:
        """Parse POST form data."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            data = self.rfile.read(length).decode('utf-8') if length else ""
            return {k: v[0] for k, v in parse_qs(data, keep_blank_values=True).items()}
        except:
            return {}
    
    def do_GET(self):
        """Handle GET requests."""
        self.safe_respond(self._handle_get)
    
    def do_POST(self):
        """Handle POST requests."""
        self.safe_respond(self._handle_post)
    
    def _handle_get(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        
        msg = query.get('msg', [''])[0]
        msg_type = query.get('t', ['success'])[0]
        
        if path == '/':
            self.send_html(render_home(msg, msg_type))
        
        elif path == '/media':
            media_path = query.get('p', [''])[0]
            download = query.get('dl', ['0'])[0] == '1'
            if media_path:
                self.send_media(unquote(media_path), download)
            else:
                self.send_error(400)
        
        elif path == '/build':
            name = query.get('n', [''])[0]
            self.send_html(render_build(name, msg))
        
        elif path == '/edit':
            name = query.get('n', [''])[0]
            self.send_html(render_edit(name, msg))
        
        else:
            self.send_html(render_home("Page not found", "error"), 404)
    
    def _handle_post(self):
        path = urlparse(self.path).path
        form = self.parse_form()
        
        try:
            if path == '/new-build':
                name = form.get('name', '').strip()
                if name and create_build(name):
                    self.redirect('/', f"Created: {name}")
                else:
                    self.redirect('/', "Please enter a valid name", "error")
            
            elif path == '/save-build':
                folder = form.get('folder_name', '')
                if not folder:
                    self.redirect('/', "Invalid build", "error")
                    return
                
                builds_data = get_builds_data()
                
                # Ensure builds_data is a list
                if not isinstance(builds_data, list):
                    builds_data = []
                
                # Find or create entry
                idx = next((i for i, b in enumerate(builds_data) if isinstance(b, dict) and b.get("folder_name") == folder), -1)
                
                entry = {
                    "folder_name": folder,
                    "title": form.get("title", folder).strip() or folder,
                    "slug": re.sub(r'[^a-z0-9]+', '-', form.get("title", folder).lower()).strip('-'),
                    "status": form.get("status", "In Progress"),
                    "description": form.get("description", ""),
                    "cover_image": form.get("cover_image", ""),
                    "updated": datetime.now().isoformat(),
                }
                
                if idx >= 0:
                    entry["created"] = builds_data[idx].get("created", entry["updated"])
                    builds_data[idx] = entry
                else:
                    entry["created"] = entry["updated"]
                    builds_data.insert(0, entry)
                
                save_builds_data(builds_data)
                self.redirect('/', f"Saved: {entry['title']}")
            
            elif path == '/rebuild':
                ok, msg = rebuild_website()
                self.redirect('/', msg, "success" if ok else "error")
            
            elif path == '/publish':
                ok, msg = publish_website()
                self.redirect('/', msg, "success" if ok else "error")
            
            else:
                self.redirect('/', "Unknown action", "error")
        
        except Exception as e:
            log(f"POST error: {e}")
            traceback.print_exc()
            self.redirect('/', f"Error: {str(e)[:100]}", "error")


# =============================================================================
# MAIN
# =============================================================================

def main():
    port = 8080
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    
    # Initialize app state
    AppState.init()
    
    # Setup signal handlers for clean shutdown
    def shutdown(sig, frame):
        log("Shutting down...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Start server
    server = ThreadingHTTPServer(('', port), Handler)
    
    log("=" * 50)
    log("🎸 JC CUSTOM GUITARS")
    log("=" * 50)
    log(f"Server running at: http://localhost:{port}")
    log("Press Ctrl+C to stop")
    log("")
    
    # Open browser
    try:
        webbrowser.open(f"http://localhost:{port}")
    except:
        pass
    
    # Run forever
    try:
        server.serve_forever()
    except Exception as e:
        log(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
