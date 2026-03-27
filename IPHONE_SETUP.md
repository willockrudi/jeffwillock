# 📱 iPhone Shortcut Setup Guide
## For JC Custom Guitars Photo/Video Capture

This guide shows how to create iPhone shortcuts that let dad:
1. **Tap one button** to take a photo or video
2. **Pick which build** it goes to (or create a new one)
3. **Automatically upload** to Google Drive

---

## Prerequisites

1. **Google Drive app** installed and signed in on iPhone
2. **Shortcuts app** (comes with iOS, free)

---

## SHORTCUT 1: Quick Photo Capture

### Step-by-Step Creation:

1. **Open Shortcuts app** on iPhone
2. **Tap "+" button** (top right) to create new shortcut
3. **Tap "Add Action"**

### Add these actions in order:

#### Action 1: Take Photo
- Search for "Take Photo"
- Add it
- Options: Turn OFF "Show Camera Preview" for faster capture

#### Action 2: Show Menu (Choose Build)
- Search for "Choose from Menu"
- Add it
- Set Prompt: "Which Build?"
- Add these options:
  - "➕ New Build"
  - (Leave room - we'll add existing builds)

#### Action 3: Handle "New Build" option
- In the "New Build" section of the menu:
- Add "Ask for Input"
  - Prompt: "Build Name?"
  - Input Type: Text
- Add "Create Folder"
  - Service: Google Drive (iCloud Drive)
  - Path: "JC Custom Guitars/[Asked Input]"
- Add "Save File"
  - Save: Photo (from step 1)
  - Service: Google Drive
  - Destination Path: "JC Custom Guitars/[Asked Input]/"

#### Action 4: Handle existing builds
- For each existing build folder, create a menu option
- Each option should:
  - Save File to that folder in Google Drive

### Finishing Up:
1. Tap the shortcut name at top
2. Rename to "📷 Guitar Photo"
3. Tap "Add to Home Screen"
4. Choose a guitar emoji icon 🎸

---

## SHORTCUT 2: Quick Video Capture

Same as above but:
- Use "Record Video" instead of "Take Photo"
- Name it "🎬 Guitar Video"

---

## SIMPLER ALTERNATIVE: Manual Google Drive Upload

If shortcuts are too complex, here's an easier method:

### Setup Google Drive App:
1. Open Google Drive app
2. Tap "+" button
3. Choose "Upload"
4. Select "Photos and Videos"
5. Navigate to the correct build folder
6. Upload!

### Create Home Screen Shortcut to Google Drive:
1. Open Google Drive app
2. Navigate to "JC Custom Guitars" folder
3. Tap the "..." menu
4. Choose "Add to Home Screen"

Now dad can:
1. Take photo normally in Camera
2. Tap the Google Drive icon
3. Upload to the right folder

---

## THE EASIEST METHOD: Auto-Upload Everything

If organization isn't critical, set up automatic upload:

### In Google Drive App:
1. Open Google Drive
2. Tap menu (☰)
3. Settings
4. Backup
5. Turn ON "Photos & Videos"
6. Set folder to "JC Custom Guitars"

Now EVERY photo/video automatically uploads!
Dad just takes photos normally and they all go to Google Drive.
He can organize them into build folders using the computer admin.

---

## Testing

1. Take a test photo with your new shortcut
2. Wait 30 seconds for sync
3. Open the admin on the computer
4. The photo should appear!

---

## Troubleshooting

**Photos not appearing?**
- Check Google Drive app is syncing (open app, pull down to refresh)
- Make sure you're signed into the same Google account on both devices

**Shortcut not working?**
- Make sure Google Drive app has permission to access photos
- Settings → Privacy → Photos → Google Drive → Full Access

**Slow uploads?**
- Enable "Use Cellular Data" in Google Drive settings
- Or wait for WiFi connection

---

## Quick Reference Card (Print this for Dad)

```
📷 TO TAKE A GUITAR PHOTO:
   1. Tap "Guitar Photo" icon
   2. Take the photo
   3. Pick which build
   4. Done! ✅

🎬 TO TAKE A VIDEO:
   1. Tap "Guitar Video" icon  
   2. Record your video
   3. Pick which build
   4. Done! ✅

🖥️ TO SEE YOUR PHOTOS:
   1. Double-click "JC Custom Admin" on desktop
   2. Your builds and photos are all there!

📤 TO PUT ON WEBSITE:
   1. Open admin
   2. Click "Edit for Site" on a build
   3. Pick cover photo
   4. Click "Save to Website"
   5. Click "Publish Online"
```
