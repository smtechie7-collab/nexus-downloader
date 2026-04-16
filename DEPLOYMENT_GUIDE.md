# DEPLOYMENT GUIDE - Nexus Downloader v5.0
**Production Deployment Instructions**  
**Last Updated**: April 16, 2026  
**Status**: Production Ready

---

## 📋 TABLE OF CONTENTS
1. System Requirements
2. Pre-Deployment Checklist
3. Installation Steps
4. Configuration
5. Running the Application
6. Monitoring & Logs
7. Performance Tuning
8. Security Best Practices
9. Backup & Recovery
10. Troubleshooting

---

## 1. SYSTEM REQUIREMENTS

### Minimum Specifications
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18.04+, CentOS 7+)
- **Python**: 3.9 or higher
- **RAM**: 512 MB minimum (1+ GB recommended)
- **Disk**: 250 MB for application + download space
- **Network**: Internet connection (up to 100 Mbps recommended)

### Recommended Specifications
- **OS**: Windows Server 2019+, Ubuntu 20.04 LTS
- **Python**: 3.10 or higher
- **RAM**: 2+ GB
- **Disk**: SSD with 1+ GB free space
- **CPU**: 2+ cores
- **Network**: 100+ Mbps

### Dependencies
```
Python Packages:
- PyQt6>=6.0.0          # GUI framework
- requests>=2.28.0       # HTTP client
- aiohttp>=3.9.0        # Async HTTP
- pydantic>=2.0.0       # Schema validation
- pyyaml>=6.0           # Config parsing
- pytest>=8.0.0         # Testing
- pytest-asyncio>=0.21  # Async testing
- psutil>=5.0.0         # System monitoring
```

---

## 2. PRE-DEPLOYMENT CHECKLIST

### Environment Setup
- [ ] Python 3.9+ installed and in PATH
- [ ] Git installed (for cloning repository)
- [ ] Administrative/sudo access available when needed
- [ ] Outbound internet access available
- [ ] 1+ GB free disk space confirmed

### Firewall & Network
- [ ] Port 8080+ available (if using API in future)
- [ ] No proxy interference with downloads
- [ ] DNS resolution working correctly
- [ ] VPN/corporate firewall configured if needed

### Pre-Deployment Validation
- [ ] Clone repository: `git clone ...`
- [ ] Run tests: `pytest tests/ -v`
- [ ] Expected result: 46/46 tests passing
- [ ] Check Python version: `python --version`

---

## 3. INSTALLATION STEPS

### Step 1: Clone Repository
```bash
# Clone the repository
git clone https://github.com/yourorg/nexus-downloader.git
cd nexus-downloader

# Verify directory
ls -la  # Linux/Mac
dir     # Windows
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep PyQt6
```

### Step 4: Verify Installation
```bash
# Test imports
python -c "from gui.app import NexusDownloaderApp; print('OK')"

# Run test suite
pytest tests/ -q

# Expected output:
# ====== 46 passed in X.XXs ======
```

### Step 5: Initial Configuration
```bash
# Copy default config (if needed)
cp config.yaml.example config.yaml  # or create from template

# Edit config with your settings
# See Configuration section below
```

---

## 4. CONFIGURATION

### Configuration File: `config.yaml`

```yaml
# Download Settings
download:
  max_workers: 10              # Concurrent downloads
  timeout: 30                  # Request timeout (seconds)
  retry_attempts: 3            # Retry failed downloads
  resume_enabled: true         # Resume partial files
  output_dir: ~/Downloads      # Default save location

# Rate Limiting
rate_limit:
  enabled: true
  per_domain: 5                # Requests per second
  burst_size: 20               # Max burst requests
  sliding_window: 60           # Window size (seconds)

# Resource Guards
resource_guard:
  enabled: true
  max_memory_mb: 1000          # Max memory usage
  max_cpu_percent: 80          # Max CPU usage
  check_interval: 5            # Check interval (seconds)

# Network
network:
  proxy_enabled: false
  proxy_list: []               # List of proxies
  dns_timeout: 5              # DNS lookup timeout
  connection_pool: 50-100     # Connection pool size

# Logging
logging:
  level: INFO                  # DEBUG/INFO/WARNING/ERROR
  format: json                 # json or text
  file: nexus.log             # Log file location
  max_size_mb: 100            # Log rotation size
  backup_count: 5             # Number of backups

# Monitoring
monitoring:
  metrics_enabled: true
  metrics_interval: 60         # Metrics collection (seconds)
  dashboard_port: 8080        # Dashboard port (future)

# Cache
cache:
  enabled: true
  ttl_hours: 24               # Cache TTL
  max_size_mb: 100            # Max cache size
```

### Environment Variables (Optional)
```bash
# Override config with environment variables
export NEXUS_MAX_WORKERS=20
export NEXUS_LOG_LEVEL=DEBUG
export NEXUS_RATE_LIMIT=10
export NEXUS_OUTPUT_DIR=/custom/path
```

### First-Time Setup
```bash
# Create data directories
mkdir -p ~/nexus-downloads     # Downloads directory
mkdir -p ~/.nexus/logs         # Logs directory
mkdir -p ~/.nexus/cache        # Cache directory

# Set permissions (Linux/Mac)
chmod 755 ~/nexus-downloads
chmod 700 ~/.nexus
```

---

## 5. RUNNING THE APPLICATION

### Method 1: GUI Application (Recommended)
```bash
# From project root
python nexus_downloader.py

# Or direct import
python -c "from gui.app import main; main()"

# Expected output:
# Application initialized
# [GUI window opens]
```

### Method 2: Command-Line Script
```bash
# For automation/scripting (future feature)
python nexus_downloader.py --url "https://example.com/video.mp4"
python nexus_downloader.py --batch urls.txt --quality 720p
```

### Method 3: Background Service (Linux/Mac)
```bash
# Create systemd service (Linux)
sudo nano /etc/systemd/system/nexus-downloader.service

[Unit]
Description=Nexus Downloader Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/path/to/nexus-downloader
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 /path/to/nexus-downloader/nexus_downloader.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable nexus-downloader
sudo systemctl start nexus-downloader
sudo systemctl status nexus-downloader
```

### Method 4: Docker Container (Optional, Phase E)
```bash
# Build image
docker build -t nexus-downloader:5.0 .

# Run container
docker run -v ~/Downloads:/app/downloads nexus-downloader:5.0

# See Docker section in this guide for details
```

---

## 6. MONITORING & LOGS

### Log Locations
```
Windows:
  Main Log:     C:\Users\{username}\nexus-downloader\logs\nexus.log
  Config:       C:\Users\{username}\.nexus\config.yaml

Linux/Mac:
  Main Log:     ~/.nexus/logs/nexus.log
  Config:       ~/.nexus/config.yaml
  Application:  /opt/nexus-downloader/
```

### Log Format
```
JSON Format (Structured):
{
  "timestamp": "2026-04-16T14:30:45.123Z",
  "level": "INFO",
  "module": "DownloadManager",
  "message": "Download started",
  "context": {
    "url": "https://example.com/file.mp4",
    "size": 1073741824
  }
}

Plain Text Format:
[2026-04-16 14:30:45] INFO - DownloadManager: Download started
  URL: https://example.com/file.mp4
  Size: 1.0 GB
```

### View Logs in Real-Time
```bash
# Linux/Mac
tail -f ~/.nexus/logs/nexus.log

# Windows PowerShell
Get-Content nexus.log -Wait

# JSON parsing (Linux)
tail -f nexus.log | jq '.level, .message'

# Filter by level
grep '"level": "ERROR"' nexus.log

# From GUI (Advanced Mode)
→ Click "Logs" tab → See real-time streaming logs
```

### Log Analysis
```bash
# Count downloads by domain
grep "Download started" nexus.log | jq '.context.domain' | sort | uniq -c

# Find errors with timestamps
grep '"level": "ERROR"' nexus.log | jq '{timestamp, message}'

# Get success rate
total=$(grep "Download" nexus.log | wc -l)
success=$(grep "Download completed" nexus.log | wc -l)
echo "Success rate: $((success * 100 / total))%"
```

---

## 7. PERFORMANCE TUNING

### Optimize for Speed
```yaml
# High-performance config
download:
  max_workers: 20          # Increase concurrency
  timeout: 60              # Longer timeout

rate_limit:
  per_domain: 20           # Higher rate
  burst_size: 50

cache:
  enabled: true            # Enable caching
  ttl_hours: 48
```

### Optimize for Stability
```yaml
# Stable, conservative config
download:
  max_workers: 5
  timeout: 30
  retry_attempts: 5

rate_limit:
  per_domain: 2            # Lower rate
  burst_size: 5

resource_guard:
  max_memory_mb: 500       # Strict limit
```

### Memory Optimization
```bash
# Monitor memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# If high memory:
# 1. Reduce max_workers in config
# 2. Clear cache: rm ~/.nexus/cache/*
# 3. Check running processes: ps aux | grep python
```

### Network Optimization
```bash
# Test connection speed
python -c "
import requests, time
url = 'https://cdn.example.com/test-file'
start = time.time()
r = requests.get(url, stream=True)
speed = len(r.content) / (time.time() - start) / 1024 / 1024
print(f'Download speed: {speed:.2f} MB/s')
"

# If slow:
# 1. Check bandwidth: speedtest-cli
# 2. Try proxy: Enable in config
# 3. Check ISP limits
```

---

## 8. SECURITY BEST PRACTICES

### File Permissions
```bash
# Linux/Mac - Restrict access
chmod 700 ~/.nexus              # Only user can access
chmod 600 ~/.nexus/config.yaml  # Only user can read config

# Windows - Administrator only
icacls "%USERPROFILE%\.nexus" /inheritance:r /grant:r "%USERNAME%":F
```

### Config Security
```yaml
# NEVER commit these to git:
# - API keys
# - Proxy credentials
# - Passwords

# Use environment variables instead:
export NEXUS_PROXY_USER="$PROXY_USER"
export NEXUS_PROXY_PASS="$PROXY_PASS"
```

### Network Security
```bash
# Verify HTTPS connections
curl -I https://example.com

# Check certificate validity
openssl s_client -connect example.com:443

# Enable SSRF protection (built-in)
# Configured in: core/ssrf_guard.py
```

### Logging Security
```yaml
# In config.yaml - Don't log sensitive data
logging:
  level: INFO
  # Passwords/tokens are automatically redacted
```

---

## 9. BACKUP & RECOVERY

### Backup Procedure
```bash
# Linux/Mac - Full backup
tar -czf nexus-backup-$(date +%Y%m%d).tar.gz \
  ~/.nexus/logs \
  ~/.nexus/config.yaml \
  ~/nexus-downloads

# Windows - Using robocopy
robocopy "%USERPROFILE%\.nexus" D:\backups\nexus /E /Z
```

### Automated Backup (Cron)
```bash
# Linux/Mac - Daily backup at 2 AM
0 2 * * * tar -czf /mnt/backup/nexus-$(date +\%Y\%m\%d).tar.gz ~/.nexus ~/nexus-downloads

# Windows - Task Scheduler (see Troubleshooting for setup)
```

### Recovery Procedure
```bash
# 1. Stop application
pkill -f nexus_downloader

# 2. Restore backup
tar -xzf nexus-backup-20260416.tar.gz -C ~

# 3. Restart application
python nexus_downloader.py

# 4. Verify restore
tail -20 ~/.nexus/logs/nexus.log
```

---

## 10. TROUBLESHOOTING

### Application Won't Start

**Error**: `ModuleNotFoundError: No module named 'PyQt6'`
```bash
# Solution: Reinstall dependencies
pip install --upgrade PyQt6
pip install -r requirements.txt
```

**Error**: `Port already in use`
```bash
# Solution: Change port in config or kill process
# Find process using port 8080
lsof -i :8080  # Linux/Mac
netstat -ano | findstr :8080  # Windows

# Kill process
kill -9 <PID>  # Linux/Mac
taskkill /PID <PID> /F  # Windows
```

### Network Issues

**Error**: `Connection timeout`
```bash
# Solutions:
# 1. Check internet: ping 8.8.8.8
# 2. Check proxy: verify proxy settings
# 3. Increase timeout in config: timeout: 60
# 4. Check firewall: netstat -an | grep LISTENING
```

**Error**: `DNS resolution failed`
```bash
# Solution: Test DNS
nslookup example.com  # Windows
dig example.com      # Linux/Mac
```

### Performance Issues

**Problem**: High memory usage
```bash
# Check memory
ps aux | grep python

# Solutions:
# 1. Reduce workers: max_workers: 5
# 2. Clear cache: rm ~/.nexus/cache/*
# 3. Restart app: pkill -f nexus_downloader
```

**Problem**: Slow downloads
```bash
# Check connection speed
speedtest-cli

# Solutions:
# 1. Check ISP bandwidth
# 2. Enable proxy rotation
# 3. Check server response times
```

### Log Analysis for Errors
```bash
# Find last error
grep "ERROR" ~/.nexus/logs/nexus.log | tail -5

# Get full context
tail -100 ~/.nexus/logs/nexus.log

# Search specific module
grep "DownloadManager" ~/.nexus/logs/nexus.log | tail -20
```

---

## SUPPORT & HELP

### Getting Help
1. Check logs: `tail -50 ~/.nexus/logs/nexus.log`
2. Read guide: Review this DEPLOYMENT_GUIDE.md
3. Check FAQ: See QUICK_START.md
4. Report issue: GitHub issues (if applicable)

### Quick Commands Reference
```bash
# Start app
python nexus_downloader.py

# Run tests
pytest tests/ -v

# View logs
tail -f ~/.nexus/logs/nexus.log

# Check version
grep version setup.py

# Clear cache
rm -rf ~/.nexus/cache/*

# Reset config
cp config.yaml.example config.yaml
```

---

**Version**: 5.0  
**Last Updated**: April 16, 2026  
**Status**: Production Ready  
**Support**: See README.md for contact information
