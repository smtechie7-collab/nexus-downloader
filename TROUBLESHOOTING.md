# TROUBLESHOOTING GUIDE - Nexus Downloader v5.0
**Common Issues & Solutions**  
**Last Updated**: April 16, 2026

---

## 🔍 QUICK DIAGNOSIS

### Step 1: Check Logs
```bash
# View recent errors (last 20 lines)
tail -20 ~/.nexus/logs/nexus.log

# Search for ERROR level
grep '"level": "ERROR"' ~/.nexus/logs/nexus.log

# Check specific module
grep "DownloadManager" ~/.nexus/logs/nexus.log | tail -10
```

### Step 2: Verify Environment
```bash
# Check Python version
python --version
# Expected: Python 3.9+

# Check dependencies
pip list | grep -E "PyQt6|requests|aiohttp"

# Check internet
ping 8.8.8.8
# Expected: replies within 100ms
```

### Step 3: Test Components
```bash
# Test imports
python -c "from gui.app import NexusDownloaderApp; print('GUI: OK')"
python -c "from pipeline.parser import URLParser; print('Parser: OK')"
python -c "from downloader.download_manager import DownloadManager; print('DL: OK')"
```

---

## 🚨 CRITICAL ISSUES

### Issue: Application Won't Start

#### Error: `ModuleNotFoundError: No module named 'PyQt6'`
```
DIAGNOSIS:
→ PyQt6 not installed
→ Wrong Python environment
→ Virtual environment not activated

SOLUTION 1: Reinstall PyQt6
  pip install --upgrade PyQt6

SOLUTION 2: Check environment
  which python  # Should show env path
  python -c "import sys; print(sys.prefix)"

SOLUTION 3: Reactivate virtual environment
  source env/bin/activate  # Linux/Mac
  env\Scripts\activate      # Windows
```

#### Error: `RuntimeError: Event loop is closed`
```
DIAGNOSIS:
→ PyQt6 asyncio integration issue
→ Previous process not cleaned up
→ Windows-specific (proactor event loop)

SOLUTION 1: Restart application
  pkill -f nexus_downloader
  python nexus_downloader.py

SOLUTION 2: Check running processes
  ps aux | grep python  # Linux/Mac
  tasklist | findstr python  # Windows

SOLUTION 3: Force kill stray processes
  pkill -9 -f nexus  # Linux/Mac
  taskkill /F /IM python.exe  # Windows
```

#### Error: `Python not found / python: command not found`
```
DIAGNOSIS:
→ Python not in PATH
→ Wrong installation
→ Using wrong shell/terminal

SOLUTION 1: Add Python to PATH (Windows)
  → Settings → Environment Variables
  → Add: C:\Python39\Scripts
  → Add: C:\Python39
  → Restart terminal

SOLUTION 2: Use full path
  /usr/local/bin/python3.9 nexus_downloader.py

SOLUTION 3: Reinstall Python with PATH option
  → python.org download
  → Check "Add Python to PATH"
  → Reinstall
```

---

## 🌐 NETWORK ISSUES

### Issue: Cannot Connect to Internet

#### Error: `Connection timeout` / `Connection refused`
```
DIAGNOSIS:
→ No internet connection
→ Firewall blocking
→ Wrong proxy settings
→ Server down

TEST 1: Ping test
  ping 8.8.8.8  or  ping google.com
  Expected: replies

TEST 2: DNS test
  nslookup example.com  (Windows)
  dig example.com      (Linux/Mac)
  Expected: IP address returned

TEST 3: Download test
  curl -I https://example.com
  Expected: HTTP 200/301/302

SOLUTIONS:
1. Check firewall:
   → Allow python through firewall
   → Windows: Firewall→Allow app→Add python
   → Mac: System Preferences→Security

2. Check proxy:
   → If behind proxy, configure in settings
   → Test proxy: curl -x proxy.host:8080 https://example.com

3. Check ISP/DNS:
   → Change DNS to 8.8.8.8 or 1.1.1.1
   → Check with ISP about restrictions

4. Retry download:
   → Most issues resolve with retry
   → Check logs for specific error
```

#### Error: `DNS resolution failed` / `Name or service not known`
```
DIAGNOSIS:
→ DNS server not responding
→ Invalid domain name
→ Network connectivity issue

SOLUTION 1: Test DNS
  nslookup example.com
  → Should show IP address
  
SOLUTION 2: Change DNS (Windows)
  ipconfig /flushdns
  → Restart application

SOLUTION 3: Change DNS (Linux/Mac)
  sudo dscacheutil -flushcache  (Mac)
  sudo systemctl restart systemd-resolved  (Linux)
  
SOLUTION 4: Use static DNS
  Edit /etc/resolv.conf
  Add: nameserver 8.8.8.8
```

#### Error: `HTTPError 403 Forbidden` / `401 Unauthorized`
```
DIAGNOSIS:
→ Website blocking requests
→ Authentication required
→ Geo-blocking
→ Rate limit exceeded

SOLUTIONS:
1. Change User-Agent:
   → Already done (Mozilla/5.0 in code)

2. Use proxy:
   → Enable proxy rotation in Settings
   → Try different proxy

3. Reduce rate:
   → Lower rate_limit in config.yaml
   → Add delays between requests

4. Check URL:
   → Verify link is correct
   → Try in browser first

5. Wait and retry:
   → Some sites block after many requests
   → Wait 30+ minutes or use VPN
```

---

## 💾 FILE & STORAGE ISSUES

### Issue: Download Fails to Save

#### Error: `Permission denied` / `Access is denied`
```
DIAGNOSIS:
→ Output folder not writable
→ File locked by another process
→ Insufficient permissions

SOLUTION 1: Check permissions (Linux/Mac)
  ls -ld ~/Downloads
  → Should show: drwxr-xr-x (755)
  
  If wrong: chmod 755 ~/Downloads

SOLUTION 2: Check file locks
  lsof | grep filename  # Linux/Mac
  → If locked, close the process

SOLUTION 3: Change save location
  Settings → Save to → [Choose different folder]
  → Must be writeable by user

SOLUTION 4: Disable antivirus temporarily
  → Some antivirus blocks file operations
  → Create whitelist for nexus-downloader
```

#### Error: `No space left on device` / `Disk full`
```
DIAGNOSIS:
→ Not enough disk space
→ Partition is full
→ Quota exceeded

SOLUTIONS:
1. Free disk space:
   → Delete old downloads
   → Clear cache: rm ~/.nexus/cache/*
   → Empty trash/recycle bin

2. Use different partition:
   → Settings → Save to → [Different drive]

3. Check disk usage:
   df -h   # Linux/Mac
   diskpart  # Windows
   → Find largest files
   → Delete unnecessary ones

4. Compression:
   → Compress old downloads
   → Archive to external drive
```

#### Error: `Corrupted file` / `File format not recognized`
```
DIAGNOSIS:
→ Download incomplete
→ File partially written
→ Network interruption
→ Server sent incorrect file

SOLUTIONS:
1. Delete and retry:
   → Remove corrupted file
   → Start download again
   → App will resume if interrupted

2. Verify with hash (if available):
   sha256sum filename
   → Compare with source

3. Try different quality:
   → Settings → Quality → [Lower quality]

4. Try different engine:
   → Advanced Mode → Dashboard
   → See which engine used
   → May retry with different engine

5. Check source:
   → Try URL in browser
   → Verify file is downloadable
```

---

## ⚡ PERFORMANCE ISSUES

### Issue: Download Too Slow

#### Diagnosis
```bash
# Check actual speed
tail -f ~/.nexus/logs/nexus.log | grep "Speed:"

# Monitor network
# Windows: Task Manager → Performance → Network
# Mac: Activity Monitor → Network  
# Linux: iftop or nethogs
```

#### Solutions
```
SOLUTION 1: Check internet speed
  → Go to speedtest.net
  → Compare expected vs actual
  → If much slower, ISP issue

SOLUTION 2: Reduce workers (for stability)
  config.yaml:
    download:
      max_workers: 5  # Was 10

SOLUTION 3: Reduce rate limit
  config.yaml:
    rate_limit:
      per_domain: 2   # Was 5

SOLUTION 4: Use proxy (bypass throttling)
  Settings → Network → Enable Proxy Rotation

SOLUTION 5: Change server/CDN
  → Try different domain if available
  → Some CDNs faster than others

SOLUTION 6: Download during off-peak
  → Nighttime usually faster
  → Weekday off-hours
```

### Issue: High Memory Usage

#### Diagnosis
```bash
# Check memory
ps aux | grep python
→ Look at RSS column (memory in KB)

# In app
→ Advanced Mode → Dashboard
→ Look at "Memory:" in status bar
```

#### Solutions
```
SOLUTION 1: Reduce workers
  config.yaml:
    download:
      max_workers: 3  # Lower concurrency

SOLUTION 2: Clear cache
  rm -rf ~/.nexus/cache/*
  → Restart app

SOLUTION 3: Reduce cache size
  config.yaml:
    cache:
      max_size_mb: 50  # Was 100

SOLUTION 4: Monitor in Activity Monitor
  macOS: Activity Monitor
  Windows: Task Manager
  Linux: top or htop
  
  If still high, restart app:
  pkill -f nexus_downloader
```

### Issue: High CPU Usage

#### Solutions
```
SOLUTION 1: Reduce workers
  max_workers: 5  # Lower parallelism

SOLUTION 2: Add delays
  config.yaml:
    rate_limit:
      per_domain: 1  # Slower rate

SOLUTION 3: Check for stuck process
  ps aux | grep python
  → Kill if command is old

SOLUTION 4: Restart
  pkill -f nexus_downloader
  sleep 5
  python nexus_downloader.py
```

---

## 🎨 GUI ISSUES

### Issue: GUI Won't Display / Blank Window

#### Solutions
```
SOLUTION 1: Check X11 (Linux)
  export DISPLAY=:0
  python nexus_downloader.py

SOLUTION 2: Disable hardware acceleration
  export QT_XCB_GL_INTEGRATION=none
  python nexus_downloader.py

SOLUTION 3: Check screen resolution
  xrandr  # Linux
  → May help if DPI scaling issue

SOLUTION 4: Use different backend (Qt6)
  export QT_QPA_PLATFORM=linux
  python nexus_downloader.py
```

### Issue: Buttons Not Responding

#### Solutions
```
SOLUTION 1: Wait for response
  → App may be processing
  → Watch logs: tail -f nexus.log

SOLUTION 2: Restart GUI
  pkill -f nexus_downloader
  python nexus_downloader.py

SOLUTION 3: Check if stuck
  ps aux | grep python
  → If old process running, kill it

SOLUTION 4: Reduce workers
  → May be unresponsive due to heavy load
```

---

## 📊 CONFIGURATION ISSUES

### Issue: Settings Not Saving

#### Solutions
```
SOLUTION 1: Check file permissions
  ls -la ~/.nexus/config.yaml
  → Must be writable (644 or 664)

SOLUTION 2: Verify syntax
  python -c "import yaml; yaml.safe_load(open('config.yaml'))"
  → Should not give error

SOLUTION 3: Restart app
  Changes take effect on restart

SOLUTION 4: Manually edit
  nano ~/.nexus/config.yaml  # Linux/Mac
  notepad %USERPROFILE%\.nexus\config.yaml  # Windows
```

### Issue: Default Config Not Loading

#### Solutions
```
SOLUTION 1: Check file exists
  ls ~/.nexus/config.yaml  # Linux/Mac
  dir %USERPROFILE%\.nexus\config.yaml  # Windows

SOLUTION 2: Reset config
  rm ~/.nexus/config.yaml
  → Restart app (recreates default)

SOLUTION 3: Copy from template
  cp config.yaml.example config.yaml
```

---

## 🧪 TESTING & DEBUGGING

### Enable Debug Logging
```bash
# Option 1: Environment variable
export NEXUS_LOG_LEVEL=DEBUG
python nexus_downloader.py

# Option 2: Edit config
config.yaml:
  logging:
    level: DEBUG

# Then check logs
tail -50 ~/.nexus/logs/nexus.log | jq .
```

### Run Tests
```bash
# Full test suite
pytest tests/ -v

# Specific test
pytest tests/test_download.py::test_atomic_write_success -v

# With logging
pytest tests/ -v -s --capture=no

# Coverage report
pytest tests/ --cov=. --cov-report=html
```

### Debug Specific Component
```bash
# Test URL parsing
python -c "
from pipeline.parser import URLParser
p = URLParser()
url = 'https://example.com/video.mp4?utm_source=test'
print(p.normalize_url(url))
"

# Test download
python -c "
import asyncio
from downloader.download_manager import DownloadManager
dm = DownloadManager()
# Test code here
asyncio.run(dm.download(...))
"
```

---

## 📞 SUPPORT & ESCALATION

### When to Contact Support
1. After trying all solutions above
2. With log excerpts (last 50 lines)
3. With system info (OS, Python version, etc.)
4. With reproducible steps

### Gather Information for Support
```bash
# Copy this block for bug reports:
echo "=== System Info ==="
python --version
uname -a  # Linux/Mac
wmic os get caption  # Windows
echo "=== App Info ==="
grep version nexus_downloader.py
echo "=== Recent Errors ==="
tail -50 ~/.nexus/logs/nexus.log
echo "=== Config ==="
cat ~/.nexus/config.yaml
```

### Get Help
- `QUICK_START.md` - Getting started
- `DEPLOYMENT_GUIDE.md` - Deployment help
- `ARCHITECTURE.md` - Technical deep dive
- GitHub Issues - Report bugs
- Email: support@example.com

---

**Version**: 5.0 | **Status**: Production Ready  
**Last Updated**: April 16, 2026  
**Found an issue? Report it with full logs please!**
