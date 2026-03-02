import json
import os
import re
import shutil
from datetime import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(ROOT, "index.html")
TEMPLATE_PATH = os.path.join(ROOT, "template.html")
DATA_PATH = os.path.join(ROOT, "projects.json")
SITE_PATH = os.path.join(ROOT, "site.json")
IMAGES_DIR = os.path.join(ROOT, "images")

PROJECTS_START = "<!-- PROJECTS_START -->"
PROJECTS_END = "<!-- PROJECTS_END -->"
TAGS_START = "<!-- TAGS_START -->"
TAGS_END = "<!-- TAGS_END -->"


# ---------- Data IO ----------
def load_projects():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_projects(projects):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(projects, f, indent=2, ensure_ascii=False)


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
    with open(SITE_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_site(site):
    with open(SITE_PATH, "w", encoding="utf-8") as f:
        json.dump(site, f, indent=2, ensure_ascii=False)


# ---------- Helpers ----------
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "project"


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


def normalize_status(value: str) -> str:
    """
    Keeps status consistent even if user types short versions.
    """
    v = (value or "").strip().lower()
    if v in ["in progress", "progress", "in-progress", "inprogress", "ip"]:
        return "In Progress"
    if v in ["complete", "completed", "done", "finished", "c"]:
        return "Complete"
    if v in ["archived", "archive", "old", "a"]:
        return "Archived"
    # fallback: Title Case whatever they typed
    return (value or "Complete").strip().title()


def status_badge(status: str) -> tuple[str, str]:
    """
    Returns (css_class, display_text)
    """
    s = (status or "Complete").strip().lower()
    if s.startswith("in"):
        return ("status-progress", "🛠 In Progress")
    if s.startswith("arch"):
        return ("status-archived", "🗃 Archived")
    return ("status-complete", "✅ Complete")


def copy_image_into_site(image_path: str, title: str) -> str:
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # PowerShell drag/drop often includes quotes
    image_path = image_path.strip().strip('"')

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
def project_card_html(p: dict) -> str:
    desc = (p.get("description") or "").strip()
    desc_html = "<br>".join([line.strip() for line in desc.splitlines() if line.strip()])

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
            label = link.get("label", "Link")
            url = (link.get("url") or "").strip()
            if url:
                link_tags.append(
                    f'            <a href="{url}" target="_blank" rel="noopener">{label}</a>'
                )
        if link_tags:
            links_html = f"""
          <div class="links">
{os.linesep.join(link_tags)}
          </div>"""

    title = p.get("title", "Untitled")
    img = p.get("image", "")
    alt = p.get("alt", title)

    status = normalize_status(p.get("status", "Complete"))
    badge_class, badge_text = status_badge(status)

    return f"""
      <div class="project-card">
        <img src="{img}" alt="{alt}">
        <div class="project-info">
          <h3>{title} <span class="status-badge {badge_class}">{badge_text}</span></h3>
          <p>{desc_html}</p>{bullets_html}{links_html}
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
    if TAGS_START not in html or TAGS_END not in html:
        return html

    tag_html = "\n".join([f"        <span>{t}</span>" for t in tags])

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


# ---------- Commands ----------
def list_projects(projects):
    if not projects:
        print("No projects yet.")
        return
    print("\nProjects:")
    for i, p in enumerate(projects, start=1):
        status = normalize_status(p.get("status", "Complete"))
        print(f"  {i}. {p.get('title','Untitled')}  [{status}]")


def input_project():
    projects = load_projects()

    print("\n=== New Project ===")
    title = prompt("Title")
    status = normalize_status(prompt("Status (Complete / In Progress / Archived)", default="Complete"))
    alt = prompt("Image alt text (what’s in the photo)", default=title, optional=True)

    image_path = prompt("Path to image file (drag/drop the file here)")
    image_rel = copy_image_into_site(image_path, title)

    description = prompt_multiline("Description (you can type multiple lines)")
    bullets = prompt_bullets()

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
        "image": image_rel,
        "alt": alt,
        "description": description,
        "bullets": bullets,
        "links": links,
        "created": datetime.now().isoformat(timespec="seconds"),
    }

    projects.insert(0, project)
    save_projects(projects)
    rebuild_index_from_projects(projects)
    print("\nAdded project and updated index.html ✅")


def edit_project():
    projects = load_projects()
    if not projects:
        print("No projects to edit.")
        return

    list_projects(projects)
    choice = prompt("\nWhich project number to edit")
    if not choice.isdigit():
        print("Please enter a number.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(projects):
        print("Invalid project number.")
        return

    p = projects[idx]
    print(f"\n=== Editing: {p.get('title','Untitled')} ===")

    p["title"] = prompt("Title", default=p.get("title", ""))
    p["status"] = normalize_status(
        prompt("Status (Complete / In Progress / Archived)", default=p.get("status", "Complete"))
    )
    p["alt"] = prompt("Image alt text", default=p.get("alt", p["title"]), optional=True)

    replace = prompt("Replace image? (y/n)", default="n", optional=True).lower()
    if replace == "y":
        image_path = prompt("Path to new image (drag/drop)")
        p["image"] = copy_image_into_site(image_path, p["title"])

    p["description"] = prompt_multiline("Description", default=p.get("description", ""))
    p["bullets"] = prompt_bullets(default_list=p.get("bullets", []))

    print("\nLinks (leave blank to remove).")
    links = []
    l1_label = prompt("Link 1 label", default="Photos", optional=True)
    l1_url = prompt("Link 1 url", default="", optional=True)
    if l1_url.strip():
        links.append({"label": l1_label or "Link", "url": l1_url.strip()})

    l2_label = prompt("Link 2 label", default="Video", optional=True)
    l2_url = prompt("Link 2 url", default="", optional=True)
    if l2_url.strip():
        links.append({"label": l2_label or "Link", "url": l2_url.strip()})

    p["links"] = links
    p["updated"] = datetime.now().isoformat(timespec="seconds")

    save_projects(projects)
    rebuild_index_from_projects(projects)
    print("\nSaved changes and updated index.html ✅")


def delete_project():
    projects = load_projects()
    if not projects:
        print("No projects to delete.")
        return

    list_projects(projects)
    choice = prompt("\nWhich project number to DELETE")
    if not choice.isdigit():
        print("Please enter a number.")
        return
    idx = int(choice) - 1
    if idx < 0 or idx >= len(projects):
        print("Invalid project number.")
        return

    title = projects[idx].get("title", "Untitled")
    confirm = prompt(f"Type DELETE to confirm deleting '{title}'")
    if confirm != "DELETE":
        print("Cancelled.")
        return

    projects.pop(idx)
    save_projects(projects)
    rebuild_index_from_projects(projects)
    print("\nDeleted project and updated index.html ✅")


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

    print("\nTags (press Enter on blank line to finish).")
    if site.get("tags"):
        print("Current tags:")
        for t in site["tags"]:
            print(f"  - {t}")

    new_tags = []
    while True:
        t = input("  - ").strip()
        if t == "":
            break
        new_tags.append(t)
    if new_tags:
        site["tags"] = new_tags

    save_site(site)

    projects = load_projects()
    rebuild_index_from_projects(projects)
    print("\nSaved site settings and updated index.html ✅")


def main():
    print("\nCommands:")
    print("  1) input-project   (add new)")
    print("  2) edit-project    (edit existing)")
    print("  3) delete-project  (remove)")
    print("  4) list-projects   (show list)")
    print("  5) rebuild         (regenerate index.html)")
    print("  6) edit-site       (name, about, contact, tags)")

    cmd = prompt("\nEnter command").lower().strip()
    projects = load_projects()

    if cmd in ["1", "input-project", "add", "new"]:
        input_project()
    elif cmd in ["2", "edit-project", "edit"]:
        edit_project()
    elif cmd in ["3", "delete-project", "delete", "remove"]:
        delete_project()
    elif cmd in ["4", "list-projects", "list"]:
        list_projects(projects)
    elif cmd in ["5", "rebuild", "build"]:
        rebuild_index_from_projects(projects)
        print("\nRebuilt index.html ✅")
    elif cmd in ["6", "edit-site", "site"]:
        edit_site()
    else:
        print("Unknown command.")


if __name__ == "__main__":
    main()
