# Copilot Workspace Instructions for Rudi Makes Site

## Overview
This workspace is a static site generator and content manager for project build logs, repair logs, and site profile content. It uses Python scripts to manage content and generate HTML pages from templates and JSON data.

## Build & Run
- **Edit content:** Run `python3 manage.py` and follow the menu to add/edit projects, repairs, or site info.
- **Rebuild site:** Use the `rebuild` command in `manage.py` to regenerate HTML pages from templates and JSON.
- **Web admin:** Use the `web-ui` command to launch a local admin interface at http://127.0.0.1:8081.
- **Publish:** Use `publish-github` to commit and push changes to your GitHub repo.

## Key Files & Structure
- `index.html`, `repairs.html`, `projects/*.html`: Generated site pages
- `template.html`, `repairs_template.html`, `project_template.html`: Jinja2-style templates
- `projects.json`, `repairs.json`, `site.json`: Content data
- `manage.py`: Main interactive script for all content operations
- `images/`: Uploaded images for projects/repairs
- `.backups/`: Automatic JSON backups before edits

## Conventions & Pitfalls
- **Always use `manage.py`** for edits to ensure backups and correct HTML escaping.
- **Do not edit generated HTML directly.** Changes will be overwritten on rebuild.
- **Backups:** Use `undo-last`, `list-backups`, or `restore-backup` in `manage.py` to recover data.
- **Image handling:** Images are copied to `images/` automatically when added via the script.
- **GitHub publishing:** Requires local git config and credentials (SSH key or token).

## Example Prompts
- "Add a new project build log."
- "Edit the about section of the site."
- "Restore the last backup."
- "Publish the latest changes to GitHub."
- "Launch the web admin UI."

## Related Customizations
- To further automate or customize workflows, consider creating agent hooks for backup management, HTML validation, or deployment.
- For frontend or backend-specific instructions, use `applyTo` patterns to target relevant files or directories.

---
For more details, see the README.md in the project root.
