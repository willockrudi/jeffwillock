JC Custom Guitars Site

Simple static site + Python editor script for:

custom guitar build logs
repair and restoration logs
site profile content (about/contact)
Files
index.html – main builds page (generated)
repairs.html – repairs and restoration page (generated)
projects/*.html – per-build detail pages (generated)
template.html – template used to rebuild index.html
repairs_template.html – template used to rebuild repairs.html
project_template.html – template used to rebuild per-build pages
projects.json – build entries
repairs.json – repair entries
site.json – profile, contact, and about content
manage.py – editor/admin script
Run

From this folder:

python3 manage.py

Then choose a command:

input-project – add a new guitar build
edit-project – edit build details (title, status, cover, gallery, tags, links, text)
edit-story – edit build story sections (photos + text)
input-repair – add a new repair or restoration log
edit-repair – edit an existing repair entry
delete-project – remove a build and its generated page
delete-repair – remove a repair entry
undo-last – restore the latest JSON backup
list-backups – show available backups
restore-backup – restore a specific backup
publish-github – commit and push changes to GitHub
web-ui – launch a local browser-based admin menu
edit-site – update name, about text, contact info, tags
list-projects – list builds
list-repairs – list repairs
rebuild – regenerate the site pages from JSON + templates
Typical workflow
Add or edit builds and repairs using manage.py.
Run rebuild (or use commands that rebuild automatically).
Open index.html in a browser and verify changes.
Run publish-github to update the live site.

manage.py runs in a loop until you choose q to quit.

Web Admin UI

From manage.py, choose web-ui.

Default URL:

http://127.0.0.1:8081

The web UI lets you:

rebuild and publish
edit site settings
add/delete builds and repairs
manage build story sections
Notes
Images are copied into the images/ folder when you add entries with photos.
Backups are stored in .backups/ before content-editing commands.
The site is generated from JSON files using templates, so you don’t need to edit HTML directly for new builds or repairs.
publish-github uses your local git credentials and pushes the current branch to GitHub.