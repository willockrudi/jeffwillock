
import json
import os
import re
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))

# Main Builds page
INDEX_PATH = os.path.join(ROOT, "index.html")
TEMPLATE_PATH = os.path.join(ROOT, "template.html")

# Troubleshooting page
REPAIRS_INDEX_PATH = os.path.join(ROOT, "repairs.html")
REPAIRS_TEMPLATE_PATH = os.path.join(ROOT, "repairs_template.html")

# Data files
DATA_PATH = os.path.join(ROOT, "projects.json")
REPAIRS_PATH = os.path.join(ROOT, "repairs.json")
SITE_PATH = os.path.join(ROOT, "site.json")

# Assets
IMAGES_DIR = os.path.join(ROOT, "images")

# Markers
PROJECTS_START = "<!-- PROJECTS_START -->"
PROJECTS_END = "<!-- PROJECTS_END -->"
REPAIRS_START = "<!-- REPAIRS_START -->"
REPAIRS_END = "<!-- REPAIRS_END -->"
TAGS_START = "<!-- TAGS_START -->"
TAGS_END = "<!-- TAGS_END -->"


# ---------- Data IO ----------
def _load_json_list(path: str) -> list:
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        print(f"⚠️  JSON parse error in {os.path.basename(path)}. Using empty list.")
        return []


def _save_json(path: str, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def load_projects():
    return _load_json_list(DATA_PATH)


def save_projects(projects):
    _save_json(DATA_PATH, projects)


def load_repairs():
    return _load_json_list(REPAIRS_PATH)


def save_repairs(repairs):
    _save_json(REPAIRS_PATH, repairs)


def load_site():
    if not os.path.exists(SITE_PATH):
        return {
            "name": "Your Name",
            "tagline": "",
            "build_log_note": "",
            "about_text": "",
            "email": "",
            "instagram_url": "",
            "youtube_url": "",
            "tags": [],
        }
    try:
        with open(SITE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {
                "name": "Your Name",
                "tagline": "",
                "build_log_note": "",
                "about_text": "",
                "email": "",
                "instagram_url": "",
                "youtube_url": "",
                "tags": [],
            }
        # Ensure keys exist
        data.setdefault("tags", [])
        return data
    except json.JSONDecodeError:
        print("⚠️  JSON parse error in site.json. Using defaults.")
        return {
            "name": "Your Name",
            "tagline": "",
            "build_log_note": "",
            "about_text": "",
            "email": "",
            "instagram_url": "",
            "youtube_url": "",
            "tags": [],
        }


def save_site(site):
    _save_json(SITE_PATH, site)


# ---------- Helpers ----------
def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "item"


def prompt(msg: str, default: str | None = None, optional: bool = False) -> str:
    while True:
        if default is not None and default != "":
            val = input(f"{msg} [{default}]: ").strip()
            if val == "":
                return default
        else:
            val = input(f"{msg}: ").strip()

        if val or optional:
            return val
        print("Please enter a value (or Ctrl+C to cancel).")


def prompt_multiline(label: str, default: str | None = None) -> str:
    print(f"\n{label} (finish with a blank line):")
    if default:
        print("---- current ----")
        print(default)
        print("-----------------")

    lines = []
    while True:
        line = input()
        if line.strip() == "":
            break
        lines.append(line)

    if not lines and default is not None:
        return default
    return "\n".join(lines).strip()


def prompt_bullets(default_list=None):
    if default_list is None:
        default_list = []

    print("\nBullets (press Enter on blank line to finish).")
    if default_list:
        print("Current bullets:")
        for b in default_list:
            print(f"  - {b}")

    bullets = []
    while True:
        line = input("  - ").strip()
        if line == "":
            break
        bullets.append(line)

    return bullets if bullets else default_list


def prompt_tags(default_list=None):
    if default_list is None:
        default_list = []

    print("\nTags (optional). Enter tags one per line. Blank line to finish.")
    if default_list:
        print("Current tags:")
        for t in default_list:
            print(f"  - {t}")

    tags = []
    while True:
        t = input("  - ").strip()
        if t == "":
            break
        tags.append(t)

    return tags if tags else default_list


def normalize_status(value: str) -> str:
    v = (value or "").strip().lower()
    if v in ["in progress", "progress", "in-progress", "inprogress", "ip"]:
        return "In Progress"
    if v in ["complete", "completed", "done", "finished", "c"]:
        return "Complete"
    if v in ["archived", "archive", "old", "a"]:
        return "Archived"
    return (value or "Complete").strip().title()


def status_badge(status: str) -> tuple[str, str]:
    s = (status or "Complete").strip().lower()
    if s.startswith("in"):
        return ("status-progress", "🛠 In Progress")
    if s.startswith("arch"):
        return ("status-archived", "🗃 Archived")
    return ("status-complete", "✅ Complete")


def copy_image_into_site(image_path: str, title: str) -> str:
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # PowerShell drag/drop often includes quotes
    image_path = (image_path or "").strip().strip('"')

    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    ext = os.path.splitext(image_path)[1].lower()
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    base = slugify(title)
    dest_name = f"{date_prefix}-{base}{ext}"
    dest_path = os.path.join(IMAGES_DIR, dest_name)

    i = 2
    while os.path.exists(dest_path):
        dest_name = f"{date_prefix}-{base}-{i}{ext}"
        dest_path = os.path.join(IMAGES_DIR, dest_name)
        i += 1

    shutil.copy2(image_path, dest_path)
    return f"images/{dest_name}"


# ---------- HTML generation ----------
def _lines_to_br(text: str) -> str:
    text = (text or "").strip()
    return "<br>".join([line.strip() for line in text.splitlines() if line.strip()])


def _card_tags_block(tags: list[str]) -> tuple[str, str]:
    """
    Returns:
      - data-tags string (slugified) for JS filtering
      - HTML chips block (original strings) for display
    """
    tags = tags or []
    clean = [t for t in tags if str(t).strip()]
    data_tags = ",".join([slugify(t) for t in clean])
    if not clean:
        return data_tags, ""

    chips = "\n".join([f'            <span class="tag-chip">{t}</span>' for t in clean])
    tags_html = f"""
          <div class="card-tags">
{chips}
          </div>"""
    return data_tags, tags_html


def repair_card_html(r: dict) -> str:
    title = r.get("title", "Untitled Repair")
    alt = r.get("alt", title)

    date = (r.get("date") or "").strip()
    status = (r.get("status") or "").strip()
    device = (r.get("device") or "").strip()

    symptom = _lines_to_br(r.get("symptom", ""))
    diagnosis = _lines_to_br(r.get("diagnosis", ""))
    fix = _lines_to_br(r.get("fix", ""))
    notes = _lines_to_br(r.get("notes", ""))

    img = (r.get("image") or "").strip()
    img_html = f'<img src="{img}" alt="{alt}">' if img else ""

    meta_bits = [b for b in [date, status] if b]
    meta_html = f'<p class="muted">{" • ".join(meta_bits)}</p>' if meta_bits else ""

    data_tags, tags_html = _card_tags_block(r.get("tags") or [])

    def line(label: str, value_html: str) -> str:
        value_html = (value_html or "").strip()
        if not value_html:
            return ""
        return f"<p><strong>{label}:</strong> {value_html}</p>"

    return f"""
      <div class="project-card" data-tags="{data_tags}">
        {img_html}
        <div class="project-info">
          <h3>{title}</h3>
          {meta_html}
          {tags_html}
          {line("Device", device)}
          {line("Symptom", symptom)}
          {line("Diagnosis", diagnosis)}
          {line("Fix", fix)}
          {f"<p>{notes}</p>" if notes else ""}
        </div>
      </div>
""".rstrip() + "\n"


def project_card_html(p: dict) -> str:
    desc_html = _lines_to_br(p.get("description", ""))

    bullets = p.get("bullets") or []
    bullets_html = ""
    if bullets:
        items = "\n".join([f"            <li>{b}</li>" for b in bullets])
        bullets_html = f"""
          <ul class="bullets">
{items}
          </ul>"""

    links = p.get("links") or []
    links_html = ""
    if links:
        link_tags = []
        for link in links:
            label = (link.get("label") or "Link").strip()
            url = (link.get("url") or "").strip()
            if url:
                link_tags.append(f'            <a href="{url}" target="_blank" rel="noopener">{label}</a>')
        if link_tags:
            links_html = f"""
          <div class="links">
{os.linesep.join(link_tags)}
          </div>"""

    title = p.get("title", "Untitled")
    alt = p.get("alt", title)

    status = normalize_status(p.get("status", "Complete"))
    badge_class, badge_text = status_badge(status)

    cover = (p.get("cover_image") or p.get("image") or "").strip()

    images = p.get("images") or []
    images = [img for img in images if isinstance(img, str) and img.strip()]

    gallery_html = ""
    if images:
        gallery_id = f"gallery-{slugify(title)}-{abs(hash(cover)) % 100000}"
        thumbs = "\n".join([f'            <img src="{img}" alt="{alt}">' for img in images])
        gallery_html = f"""
          <button class="gallery-toggle" type="button" data-gallery-toggle="{gallery_id}">More photos</button>
          <div class="gallery" id="{gallery_id}">
{thumbs}
          </div>"""

    data_tags, tags_html = _card_tags_block(p.get("tags") or [])

    return f"""
      <div class="project-card" data-tags="{data_tags}">
        <img src="{cover}" alt="{alt}">
        <div class="project-info">
          <h3>{title} <span class="status-badge {badge_class}">{badge_text}</span></h3>
          <p>{desc_html}</p>{tags_html}{bullets_html}{links_html}{gallery_html}
        </div>
      </div>
""".rstrip() + "\n"


def replace_placeholders(html: str, site: dict) -> str:
    mapping = {
        "{{NAME}}": site.get("name", ""),
        "{{TAGLINE}}": site.get("tagline", ""),
        "{{BUILD_LOG_NOTE}}": site.get("build_log_note", ""),
        "{{ABOUT_TEXT}}": site.get("about_text", ""),
        "{{EMAIL}}": site.get("email", ""),
        "{{INSTAGRAM_URL}}": site.get("instagram_url", ""),
        "{{YOUTUBE_URL}}": site.get("youtube_url", ""),
    }
    for k, v in mapping.items():
        html = html.replace(k, v)
    return html


def inject_tags(html: str, tags: list[str]) -> str:
    # This injects the ABOUT section tags, not per-card tags
    if TAGS_START not in html or TAGS_END not in html:
        return html

    tag_html = "\n".join([f"        <span>{t}</span>" for t in (tags or [])])

    s = html.index(TAGS_START) + len(TAGS_START)
    e = html.index(TAGS_END)
    return html[:s] + "\n" + tag_html + "\n      " + html[e:]


def rebuild_index_from_projects(projects):
    if not os.path.isfile(TEMPLATE_PATH):
        raise FileNotFoundError(
            f"template.html not found at {TEMPLATE_PATH}\n"
            "Create it by copying index.html -> template.html"
        )

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    if PROJECTS_START not in template or PROJECTS_END not in template:
        raise ValueError(
            "Markers not found in template.html.\n"
            "Add:\n"
            "<!-- PROJECTS_START -->\n"
            "<!-- PROJECTS_END -->"
        )

    start_i = template.index(PROJECTS_START) + len(PROJECTS_START)
    end_i = template.index(PROJECTS_END)
    cards = "".join(project_card_html(p) for p in projects)
    new_content = template[:start_i] + "\n" + cards + template[end_i:]

    if os.path.exists(SITE_PATH):
        site = load_site()
        new_content = replace_placeholders(new_content, site)
        new_content = inject_tags(new_content, site.get("tags", []))

    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


def rebuild_repairs_page():
    if not os.path.isfile(REPAIRS_TEMPLATE_PATH):
        raise FileNotFoundError(
            f"repairs_template.html not found at {REPAIRS_TEMPLATE_PATH}\n"
            "Create it by creating repairs_template.html"
        )

    with open(REPAIRS_TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    if REPAIRS_START not in template or REPAIRS_END not in template:
        raise ValueError(
            "Markers not found in repairs_template.html.\n"
            "Add:\n"
            "<!-- REPAIRS_START -->\n"
            "<!-- REPAIRS_END -->"
        )

    repairs = load_repairs()
    rs = template.index(REPAIRS_START) + len(REPAIRS_START)
    re_ = template.index(REPAIRS_END)
    repair_cards = "".join(repair_card_html(r) for r in repairs)
    new_content = template[:rs] + "\n" + repair_cards + template[re_:]

    if os.path.exists(SITE_PATH):
        site = load_site()
        new_content = replace_placeholders(new_content, site)
        new_content = inject_tags(new_content, site.get("tags", []))

    with open(REPAIRS_INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)


# ---------- Commands ----------
def list_projects(projects):
    if not projects:
        print("No projects yet.")
        return
    print("\nBuilds:")
    for i, p in enumerate(projects, start=1):
        status = normalize_status(p.get("status", "Complete"))
        tags = p.get("tags") or []
        tag_str = ", ".join(tags) if tags else ""
        print(f"  {i}. {p.get('title','Untitled')}  [{status}]" + (f"  ({tag_str})" if tag_str else ""))


def list_repairs(repairs):
    if not repairs:
        print("No repair logs yet.")
        return
    print("\nTroubleshooting:")
    for i, r in enumerate(repairs, start=1):
        title = r.get("title", "Untitled Repair")
        date = (r.get("date") or "").strip()
        status = (r.get("status") or "").strip()
        tags = r.get("tags") or []
        extra = " • ".join([x for x in [date, status] if x])
        tag_str = ", ".join(tags) if tags else ""
        line = f"  {i}. {title}"
        if extra:
            line += f"  [{extra}]"
        if tag_str:
            line += f"  ({tag_str})"
        print(line)


def input_project():
    projects = load_projects()

    print("\n=== New Build ===")
    title = prompt("Title")
    status = normalize_status(prompt("Status (Complete / In Progress / Archived)", default="Complete"))
    alt = prompt("Image alt text (what’s in the photo)", default=title, optional=True)

    image_path = prompt("Path to image file (drag/drop the file here)")
    image_rel = copy_image_into_site(image_path, title)

    description = prompt_multiline("Description (you can type multiple lines)")
    bullets = prompt_bullets()
    tags = prompt_tags()

    links = []
    add_link = prompt("Add a link? (y/n)", default="n", optional=True).lower()
    if add_link == "y":
        label = prompt("Link label (e.g., Photos, Video, Notes)", default="Photos", optional=True)
        url = prompt("Link URL")
        links.append({"label": label, "url": url})

        add_link2 = prompt("Add another link? (y/n)", default="n", optional=True).lower()
        if add_link2 == "y":
            label2 = prompt("Link label", default="Video", optional=True)
            url2 = prompt("Link URL")
            links.append({"label": label2, "url": url2})

    project = {
        "title": title,
        "status": status,
        "cover_image": image_rel,
        "image": image_rel,      # legacy/backwards compat
        "images": [],            # extra images optional later
        "alt": alt,
        "description": description,
        "bullets": bullets,
        "tags": tags,            # <-- NEW: per-card tags for filtering
        "links": links,
        "created": datetime.now().isoformat(timespec="seconds"),
    }

    projects.insert(0, project)
    save_projects(projects)

    # rebuild both pages
    rebuild_index_from_projects(projects)
    rebuild_repairs_page()
    print("\nAdded build and updated index.html + repairs.html ✅")


def input_repair():
    repairs = load_repairs()

    print("\n=== New Circuit Troubleshooting Entry ===")
    title = prompt("Title (short)", default="Circuit Troubleshooting", optional=True)
    date = prompt("Date (YYYY-MM-DD)", default=datetime.now().strftime("%Y-%m-%d"), optional=True)
    status = prompt("Status (In Progress / Fixed / Monitoring)", default="Fixed", optional=True)

    device = prompt("Device / Board", optional=True)
    symptom = prompt_multiline("Symptom (multi-line)", default="")
    diagnosis = prompt_multiline("Diagnosis (multi-line)", default="")
    fix = prompt_multiline("Fix / What worked (multi-line)", default="")

    add_photo = prompt("Add a photo? (y/n)", default="y", optional=True).lower()
    image_rel = ""
    alt = ""
    if add_photo == "y":
        image_path = prompt("Path to image file (drag/drop)")
        image_rel = copy_image_into_site(image_path, title)
        alt = prompt("Image alt text", default=title, optional=True)

    notes = prompt_multiline("Extra notes (optional)", default="")
    tags = prompt_tags()

    entry = {
        "title": title,
        "date": date,
        "status": status,
        "device": device,
        "symptom": symptom,
        "diagnosis": diagnosis,
        "fix": fix,
        "image": image_rel,
        "alt": alt,
        "notes": notes,
        "tags": tags,  # <-- NEW: per-card tags for filtering
        "created": datetime.now().isoformat(timespec="seconds"),
    }

    repairs.insert(0, entry)
    save_repairs(repairs)

    # rebuild both pages
    projects = load_projects()
    rebuild_index_from_projects(projects)
    rebuild_repairs_page()
    print("\nAdded troubleshooting entry and updated repairs.html ✅")


def edit_site():
    site = load_site()

    print("\n=== Edit Site Settings ===")
    site["name"] = prompt("Name", default=site.get("name", "Your Name"))
    site["tagline"] = prompt("Tagline", default=site.get("tagline", ""))
    site["build_log_note"] = prompt("Build log note", default=site.get("build_log_note", ""))
    site["about_text"] = prompt_multiline("About text (multi-line)", default=site.get("about_text", ""))
    site["email"] = prompt("Email", default=site.get("email", ""))
    site["instagram_url"] = prompt("Instagram URL", default=site.get("instagram_url", ""))
    site["youtube_url"] = prompt("YouTube URL", default=site.get("youtube_url", ""))

    print("\nAbout tags (these show in the About section).")
    site["tags"] = prompt_tags(default_list=site.get("tags", []))

    save_site(site)

    # Rebuild both pages to apply placeholders/tags
    projects = load_projects()
    rebuild_index_from_projects(projects)
    rebuild_repairs_page()
    print("\nSaved site settings and updated index.html + repairs.html ✅")


def main():
    print("\nCommands:")
    print("  1) input-project   (add new build)")
    print("  4) list-projects   (show builds list)")
    print("  5) rebuild         (regenerate index.html + repairs.html)")
    print("  6) edit-site       (name, about, contact, tags)")
    print("  7) input-repair    (add troubleshooting entry)")
    print("  8) list-repairs    (show troubleshooting list)")

    cmd = prompt("\nEnter command").lower().strip()
    projects = load_projects()
    repairs = load_repairs()

    if cmd in ["1", "input-project", "add", "new"]:
        input_project()
    elif cmd in ["4", "list-projects", "list"]:
        list_projects(projects)
    elif cmd in ["5", "rebuild", "build"]:
        rebuild_index_from_projects(projects)
        rebuild_repairs_page()
        print("\nRebuilt index.html + repairs.html ✅")
    elif cmd in ["6", "edit-site", "site"]:
        edit_site()
    elif cmd in ["7", "input-repair", "repair", "new-repair"]:
        input_repair()
    elif cmd in ["8", "list-repairs", "repairs", "list-repair"]:
        list_repairs(repairs)
    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
