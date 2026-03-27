# Google Cloud Setup — JC Custom Watcher
## One-time browser setup (~10 minutes)

This only needs to be done once. After this, `watcher.py` runs
automatically with no browser needed.

---

## Step 1 — Create a Google Cloud project

1. Go to **https://console.cloud.google.com/**
2. Sign in with the **same Google account** your iPhone backs up to
3. Click the project dropdown at the top → **New Project**
4. Name it `JC Custom` → click **Create**
5. Wait a few seconds, then make sure `JC Custom` is selected in the dropdown

---

## Step 2 — Enable the Photos Library API

1. In the left sidebar → **APIs & Services** → **Library**
2. Search for `Photos Library API`
3. Click it → click **Enable**

---

## Step 3 — Create OAuth credentials

1. In the left sidebar → **APIs & Services** → **Credentials**
2. Click **+ Create Credentials** → **OAuth client ID**
3. If prompted to configure a consent screen first:
   - Click **Configure Consent Screen**
   - Choose **External** → **Create**
   - Fill in App name: `JC Custom Watcher`
   - Fill in your email for support and developer contact
   - Click **Save and Continue** through all the screens
   - On the **Test users** screen, click **+ Add users**, add your Gmail address → **Save**
   - Go back to **Credentials**
4. Click **+ Create Credentials** → **OAuth client ID** again
5. Application type: **Desktop app**
6. Name: `JC Custom Watcher`
7. Click **Create**Client ID
    404655407179-c5gn7qd7m3pieb4f85oq592cjkadgqct.apps.googleusercontent.com 
8. Click **Download JSON** on the confirmation dialog

---

## Step 4 — Save the credentials file

Move the downloaded JSON file into your `jeffwillock` repo folder and
rename it exactly:

```
.gphoto_credentials.json
```

So the full path should be:
```
~/Documents/jeffwillock/.gphoto_credentials.json
```

> The dot at the start makes it a hidden file — it won't show in Finder
> by default, but it will be there. Use `ls -a` in terminal to confirm.

---

## Step 5 — Install Python dependencies

Run this once in Terminal:

```bash
cd ~/Documents/jeffwillock
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client requests
```

---

## Step 6 — First run (authorise)

```bash
cd ~/Documents/jeffwillock
python3 watcher.py
```

A browser window will open. Sign in with the same Google account,
click **Allow**. The window will close and the watcher will start.

You'll see output like:
```
2026-03-27 10:00:00  INFO     Authorised. Watching for new photos...
2026-03-27 10:00:00  INFO     Poll complete — 3 new photo(s) downloaded to _Incoming/
```

Photos from your iPhone will appear in:
```
~/Google Drive/JC Custom/_Incoming/
```

---

## After first run — automatic startup

The token is saved to `.gphoto_token.json` in the repo folder.
Every subsequent run of `watcher.py` uses this token automatically —
no browser needed.

To have it start on login, we'll wire it into `launch.sh` in Phase 4.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Missing dependencies` error | Run the `pip install` command in Step 5 |
| `OAuth credentials file not found` | Check `.gphoto_credentials.json` is in the repo root |
| Browser says "App not verified" | Click **Advanced** → **Go to JC Custom Watcher (unsafe)** — this is expected for a personal app |
| Photos not appearing | Check iPhone is connected to WiFi and Google Photos has finished backing up |
| `ConnectionError` in logs | Mac is offline — watcher will retry automatically |

---

## What gets downloaded

- Only **new** photos since watcher last ran
- Full resolution originals
- Saved as the original filename from your iPhone (e.g. `IMG_1234.JPG`)
- The watcher remembers which photos it has already downloaded — no duplicates

---

*Phase 3 will add the iPad assignment UI where you drag photos from
_Incoming/ into the right guitar folder.*
