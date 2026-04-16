# QUICK START GUIDE - Nexus Downloader v5.0
**Get Started in 5 Minutes - No Experience Needed**  
**Last Updated**: April 16, 2026

---

## ⚡ 30-SECOND SETUP

### For Complete Beginners
```bash
1. Install Python 3.9+ from python.org
2. Download Nexus Downloader
3. Run: python nexus_downloader.py
4. Done! 🎉
```

### For Developers
```bash
# Clone repo
git clone https://github.com/yourorg/nexus-downloader.git

# Setup
cd nexus-downloader
python -m venv env
source env/bin/activate  # or env\Scripts\activate on Windows
pip install -r requirements.txt

# Run
python nexus_downloader.py
```

---

## 📖 SIMPLE MODE - 3 EASY STEPS

### Step 1: Launch Application
```bash
# From project folder:
python nexus_downloader.py

# Window opens with "Nexus Downloader" title
```

### Step 2: Paste Your URL
```
┌─────────────────────────────────────┐
│  Nexus Downloader | Mode: Simple ▼  │
├─────────────────────────────────────┤
│                                     │
│  Download Media                     │
│  Media URL: [paste_your_url_here]  │
│  Save to:   [/Users/Downloads]     │
│  Quality:   [Auto ▼]               │
│                                     │
│  [Start Download] [Pause] [Cancel]  │
└─────────────────────────────────────┘

Example URLs:
✓ https://youtube.com/watch?v=abc123
✓ https://example.com/video.mp4
✓ https://cdn.example.com/file.zip
```

### Step 3: Click Start & Wait
```
Progress shows:
┌─────────────────────────────────────┐
│ video.mp4                           │
│ ████████████░░░░░░░░░░░░░░░░░░ 45% │
│ Speed: 2.5 MB/s  |  Time left: 3min│
└─────────────────────────────────────┘

When done: File saved to Download folder ✓
```

---

## 🎯 QUICK TASKS

### Download a Video
```
1. Paste video URL
2. Click "Start Download"
3. Wait for completion
4. File appears in Downloads folder
```

### Pause a Download
```
1. Click "Pause" button
2. Download stops
3. Click "Resume" to continue
```

### Cancel a Download
```
1. Click "Cancel" button
2. Download stops & file removed
3. Start a new download
```

### Change Save Location
```
1. Click folder path in "Save to:"
2. Select different folder
3. Click OK
4. Downloads go to new folder
```

### Check Download Speed
```
While downloading, look at status bar:
Speed: 2.5 MB/s  ← megabytes per second
Time: 3:45       ← time remaining
Progress: 45%    ← percentage complete
```

---

## ⚙️ SWITCHING TO ADVANCED MODE

### What's Different?
```
SIMPLE MODE              ADVANCED MODE
─────────────────────────────────────
1 page                  5 tabs
3 buttons               Full controls
Auto settings           Custom config
Basic info              Real-time metrics
                        Engine selection
                        Performance stats
                        Log viewer
```

### How to Switch
```
1. Click dropdown: "Mode: Simple ▼"
2. Select: "Advanced (Power User)"
3. BOOM! All tabs appear
4. Click to switch back anytime
```

### Advanced Mode Tabs
1. **Dashboard** - Real-time stats
2. **Tasks** - Manage downloads
3. **Metrics** - Performance graphs
4. **Logs** - Detailed events
5. **Settings** - Configuration

---

## ❓ FREQUENTLY ASKED QUESTIONS

### Q: Where does it save files?
**A**: By default: `C:\Users\YourName\Downloads` (Windows) or `~/Downloads` (Mac/Linux)
- You can change this in Settings
- Click "Save to:" and pick different folder

### Q: Can I pause and resume?
**A**: Yes! Click "Pause" to stop, click again to resume. 
- Your partial file is kept
- Resume starts from where it stopped

### Q: How do I know if it's working?
**A**: You'll see:
- Progress bar moving
- Speed showing (e.g., "2.5 MB/s")
- Time remaining (e.g., "5 min")

### Q: What if download fails?
**A**: App automatically retries:
1. First fail → waits 2 seconds, retries
2. Second fail → waits 5 seconds, retries  
3. Third fail → shows error message

You can manually retry by clicking "Start" again.

### Q: Can I download multiple files?
**A**: Yes! 
- **Simple Mode**: After one finishes, start another
- **Advanced Mode**: Use "Tasks" tab for queue

### Q: How do I see download history?
**A**: In Simple Mode, scroll down to "Recent Downloads"
- **Advanced Mode**: Click "Tasks" tab to see all

### Q: Does it work without internet?
**A**: No, it needs internet to download. But you can:
- Prepare URLs while offline
- Configure settings offline
- View logs & history offline

### Q: Can I run it on my server?
**A**: Yes (future version):
- **Today**: Works on Windows/Mac/Linux desktop
- **Soon**: Headless mode for servers (Phase E)
- **Future**: Docker container available

### Q: What's the difference between Simple & Advanced?
**A**: 
- **Simple**: For just downloading (80% of users)
- **Advanced**: For power users who want full control (developers/testers)

### Q: Is my data private?
**A**: Yes:
- All processing local (no cloud)
- No tracking/telemetry
- Logs only on your computer
- Full source code available

---

## 🚀 POWER USER TIPS

### Keyboard Shortcuts (Advanced Mode)
```
Ctrl+D    → Download selected
Ctrl+P    → Pause selected
Ctrl+E    → Resume selected
Ctrl+Q    → Quit app
Ctrl+,    → Open settings
```

### Command Line Usage (Future)
```bash
# Quick download
nexus download "https://example.com/video.mp4"

# Download to specific folder
nexus download "https://example.com/video.mp4" --output ~/MyVideos

# Batch download
nexus batch urls.txt

# Show stats
nexus status
```

### Quality Settings
```
AUTO      → App chooses best based on connection
480p      → Standard quality (faster)
720p      → HD quality
1080p     → Full HD quality
4K        → Ultra HD quality (if available)
```

### Configuration File (Advanced)
```bash
# Edit advanced settings
nano ~/.nexus/config.yaml  # Linux/Mac
notepad "%USERPROFILE%\.nexus\config.yaml"  # Windows

# Common settings:
download:
  max_workers: 10          # Number of concurrent downloads
  timeout: 30              # Connection timeout (seconds)
```

---

## 🆘 TROUBLESHOOTING QUICK FIXES

### Problem: Application won't start
```
Solution:
1. Install Python 3.9+
2. Run: pip install -r requirements.txt
3. Try again
```

### Problem: Download won't start
```
Solution:
1. Check internet connection: ping google.com
2. Try different URL
3. Check firewall isn't blocking
4. Restart application
```

### Problem: Download too slow
```
Solution:
1. Check internet speed (speedtest.net)
2. Try different quality setting
3. Wait during peak hours
4. Restart application
```

### Problem: File corrupted
```
Solution:
1. Resume download (if incomplete)
2. Delete file and redownload
3. Try different quality
```

### Problem: Out of disk space
```
Solution:
1. Delete old downloads
2. Change save folder to another drive
3. Free up space on computer
```

### Problem: Still stuck?
```
Check the full guide:
→ Read: DEPLOYMENT_GUIDE.md (section: Troubleshooting)
→ Check: ~/.nexus/logs/nexus.log
→ See: README.md for support
```

---

## 📊 METRICS & MONITORING (Advanced Users)

### Understanding the Dashboard
```
┌─────────────────────────────────────┐
│ Total Requests: 1,245               │
│ Success Rate: 96.5%                 │
│ Memory: 485 MB                      │
│ CPU: 12%                            │
└─────────────────────────────────────┘

What it means:
- Requests = Total files processed
- Success = Percentage without errors
- Memory = RAM used by app
- CPU = Processor usage %
```

### Real-Time Metrics Graph
```
Performance Over Time:
│                      ╱╲
│            ╱╲       ╱  ╲
│           ╱  ╲     ╱    ╲
│          ╱    ╲   ╱      ╲
└──────────────────────────── Time
  Green = Good | Yellow = Caution | Red = Warning
```

### Domain Performance (Advanced Mode)
```
youtube.com       542 requests  ✓ 96% success
example.com       245 requests  ✓ 99% success
cdn.example.com   458 requests  ⚠ 87% success
```

---

## 💡 TIPS & TRICKS

### Tip 1: Use Quality Settings
```
Fast: Set to "Auto" - app optimizes automatically
Good: Select "720p" - good balance
Best: Select "1080p" - highest quality (slower)
```

### Tip 2: Batch Downloads
```
Advanced Mode → Tasks tab → Add multiple URLs
All download automatically (one after another)
```

### Tip 3: Monitor in Background
```
Minimize to system tray (when supported)
App continues downloading
Notification when done
```

### Tip 4: Use Proxy (If Needed)
```
Settings → Network → Enable Proxy Rotation
Useful if blocked by ISP/region
```

### Tip 5: Check Logs When Issues Occur
```
Advanced Mode → Logs tab → See detailed info
Or: tail -f ~/.nexus/logs/nexus.log
```

---

## 🎓 LEARNING PATH

### Beginner (Week 1)
- [x] Install application
- [x] Download single file
- [x] Pause & resume
- [ ] Read README.md

### Intermediate (Week 2)
- [ ] Switch to Advanced Mode
- [ ] Download multiple files
- [ ] Configure settings
- [ ] Check metrics/logs
- [ ] Read DEPLOYMENT_GUIDE.md

### Advanced (Week 3+)
- [ ] Command-line interface (when available)
- [ ] API integration (future)
- [ ] Performance tuning
- [ ] Custom configuration
- [ ] Contribute to project

---

## 🎉 YOU'RE READY!

**Your Checklist**:
- [x] Installed application
- [x] Understand Simple Mode
- [x] Know how to pause/resume
- [x] Know how to switch modes
- [x] Understood FAQ

**Next Steps**:
1. Download your first file 📥
2. Join community (if applicable)
3. Provide feedback 💬
4. Read full deployment guide when ready

---

## 📞 NEED HELP?

### Quick Help
1. Check FAQ section above
2. Read DEPLOYMENT_GUIDE.md (Troubleshooting)
3. Check app logs (Advanced Mode → Logs)

### Detailed Help
- 📖 Full guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 🏗️ Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- 🐛 Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Contact
- GitHub Issues: Create a new issue
- Email: support@example.com (when available)
- Documentation: Check README.md

---

**Version**: 5.0 | **Status**: Production Ready  
**Last Updated**: April 16, 2026  
**Made With ❤️ for Easy Downloading**
