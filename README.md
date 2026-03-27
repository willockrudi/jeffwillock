# 🎸 JC Custom Guitars - Complete Admin System

## Zero-Friction Workflow for Documenting Guitar Builds

This system lets your dad document his guitar work with **zero technical knowledge needed**.

### The Workflow:

```
📱 IPHONE                    ☁️ GOOGLE DRIVE                   🖥️ COMPUTER
─────────                    ──────────────                    ──────────
Take photo/video  ──────►  Auto-syncs to cloud  ──────►  Shows in admin
Pick which build            Organized by build               One-click publish
Done!                       You can also access              Website updated!
```

---

## 📦 What's Included

| File | Purpose |
|------|---------|
| `manage.py` | The admin dashboard server |
| `setup.sh` | One-time setup script |
| `Start JC Custom.command` | Double-click to start admin |
| `IPHONE_SETUP.md` | Guide for setting up iPhone shortcuts |

---

## 🚀 Quick Setup (5 minutes)

### On Dad's Mac:

1. **Install Google Drive for Desktop**
   - Download from: https://www.google.com/drive/download/
   - Sign in with Google account

2. **Run the setup script**
   ```bash
   cd /path/to/jccustom_complete
   bash setup.sh
   ```

3. **Done!** A "🎸 JC Custom Admin" shortcut appears on Desktop

### On Dad's iPhone:

1. **Install Google Drive app** from App Store
2. **Sign in** with the SAME Google account
3. **Set up auto-upload** (see IPHONE_SETUP.md)

---

## 🎯 How Dad Uses It

### Taking Photos/Videos:

**Easiest method:** Just use the normal Camera app. Photos auto-upload to Google Drive.

**Organized method:** Use the shortcut that asks "Which build?" after each photo.

### Managing the Website:

1. **Double-click** "🎸 JC Custom Admin" on Desktop
2. Browser opens with all builds and photos
3. Click **"Edit for Site"** on a build
4. Pick cover photo, add description
5. Click **"Publish Online"**

That's it! Website is updated.

---

## 📁 Folder Structure

Everything lives in Google Drive, so both dad and you can access it:

```
Google Drive/
└── JC Custom Guitars/
    ├── _site_data/          ← Website data (JSON files)
    ├── _config.json         ← Settings
    ├── Telecaster Build/    ← Build folder
    │   ├── photo1.jpg
    │   ├── video1.mov
    │   └── ...
    ├── Stratocaster/        ← Another build
    │   └── ...
    └── manage.py            ← Admin server
```

---

## 🔧 Configuration

Edit `_config.json` in the Google Drive folder:

```json
{
  "drive_folder": "/path/to/Google Drive/JC Custom Guitars",
  "website_folder": "/path/to/github/repo",
  "owner_name": "Jeff Willock",
  "site_name": "JC Custom Guitars"
}
```

---

## ❓ Troubleshooting

### "Photos not showing up"
- Open Google Drive app on iPhone, pull down to refresh
- Wait 1-2 minutes for sync
- Check both devices use the same Google account

### "Can't start admin"
- Make sure Python 3 is installed: `python3 --version`
- Check the log: `cat /tmp/jccustom.log`

### "Website not updating"
- Make sure the website folder is a git repository
- Check git credentials are set up

---

## 🆘 Help for Dad

Print this card and put it by the computer:

```
┌─────────────────────────────────────────┐
│  🎸 JC CUSTOM GUITARS - QUICK GUIDE    │
├─────────────────────────────────────────┤
│                                         │
│  📷 TAKE PHOTOS:                        │
│     Just use your iPhone camera!        │
│     Photos sync automatically.          │
│                                         │
│  🖥️ MANAGE WEBSITE:                     │
│     1. Double-click guitar icon         │
│     2. Pick a build                     │
│     3. Click "Edit for Site"            │
│     4. Click "Publish Online"           │
│                                         │
│  ❓ PROBLEMS?                           │
│     Call [Your Name]: [Your Phone]      │
│                                         │
└─────────────────────────────────────────┘
```

---

## 👨‍👦 Remote Help

Since everything is in Google Drive, you can help remotely:

1. **View photos**: Access the shared Google Drive folder
2. **Edit website**: Make changes to the builds.json file
3. **Debug**: Check /tmp/jccustom.log on his computer via screen share

---

## License

MIT - Do whatever you want with it!
