# ARCHITECTURE DOCUMENTATION - Nexus Downloader v5.0
**System Design & Component Overview**  
**Last Updated**: April 16, 2026

---

## 📐 SYSTEM OVERVIEW

### Nine Planes Architecture
```
                    ┌─────────────────────────────────┐
                    │   USER INTERFACE PLANE          │   ← PyQt6 GUI
                    │  (Simple & Advanced Modes)      │
                    └────────────┬────────────────────┘
                                 │
        ┌────────────────────────┴───────────────────────────────┐
        │                                                        │
   ┌────▼──────────────────┐                    ┌──────────────▼─────┐
   │  ORCHESTRATION PLANE  │◄───────────────────┤  PIPELINE PLANE    │
   │ (Router, Controller)  │                    │ (Validation, Parse)│
   ├───────────────────────┤                    ├────────────────────┤
   │ • Smart Engine Route  │                    │ • Schema Validator │
   │ • Task Management     │                    │ • Media Validator  │
   │ • Domain Strategy     │                    │ • URL Parser       │
   └────┬──────────────────┘                    └──────────────────┘
        │
    ┌───┴──────────────┬──────────────┬──────────────┬────────────┐
    │                  │              │              │            │
┌───▼────────────┐ ┌───▼───────┐ ┌───▼──────────┐ ┌─▼──────────┐ │
│ ENGINES PLANE  │ │NETWORK    │ │DOWNLOAD      │ │STORAGE    │ │
│ (5 Engines)    │ │PLANE      │ │PLANE         │ │PLANE      │ │
├────────────────┤ ├───────────┤ ├──────────────┤ ├──────────────┤
│ • Fast Engine  │ │Session Mgr│ │Download Mgr  │ │Cache Layer   │
│ • Spider       │ │Proxy Mgr  │ │Bandwidth Mgr │ │Deduplicator  │
│ • Stealth      │ │SSRF Guard │ │File Writer   │ │State Mgr     │
│ • Headless     │ │           │ │              │ │              │
│ • Media        │ └───────────┘ └──────────────┘ └──────────────┘
└────────────────┘
        │
    ┌───┴────────────────┐
    │                    │
┌───▼──────────────┐ ┌──▼────────────┐
│ MONITORING PLANE │ │ CORE UTILITIES│
│                  │ │               │
├─────────────────┤ ├─────────────────┤
│ • Logger        │ │ • Constants    │
│ • Metrics       │ │ • Retry Logic  │
│ • Health Checks │ │ • Helpers      │
└──────────────────┘ └──────────────────┘
```

---

## 🔄 DATA FLOW DIAGRAM

### Request Journey (Simplified)
```
User URL Input
     │
     ▼
[SSRF Guard] ──► Blocked? ──Yes──► Error Response
     │                                    │
     No                                   ▼
     │                           (Log, Display Error)
     ▼
[URL Parser] ──► Normalize & Extract Metadata
     │
     ▼
[Deduplicator] ──► Already Downloaded? ──Yes──► Skip
     │                                            │
     No                                          ▼
     │                                    (Return Cached)
     ▼
[Cache Layer] ──► In Cache & Valid? ──Yes──► Return
     │                                        │
     No                                      ▼
     │                                  (Skip Engine)
     ▼
[Router] ──► Select Best Engine
     │       Based on Domain/Type/Performance
     ▼
[Selected Engine]
     │
     ├─► Extract Media URLs
     │
     ▼
[Validator] ──► Verify Media (HEAD request)
     │
     ├─► Valid? ──Yes─┐
     │            	  │
     ├─► No ────► Error
     │            	
     ▼
[Download Manager] ──► Multi-threaded Download
     │
     ├─► Progress Updates
     ├─► Resume Support
     ├─► Bandwidth Throttling
     │
     ▼
[File Writer] ──► Atomic Write to Disk
     │
     ├─► Success ──► Log + Metrics
     │
     ├─► Fail ───► Retry with Backoff
     │
     ▼
[Complete] ──► Update Cache + State
```

---

## 🎯 CORE COMPONENTS

### 1. ORCHESTRATION PLANE

#### Router (core/router.py)
```python
class Router:
    - route(url) → Selects optimal engine
    - register_engine(name, engine)
    - get_engine_stats() → Performance data
```

**Logic**:
```
If domain in youtube_domains:
    → Use media_engine
Elif has_javascript:
    → Use headless_engine
Elif is_html_page:
    → Use spider_engine
Else:
    → Use fast_engine
```

**Timeout Handling**:
- Wraps execution with asyncio.wait_for()
- 30-second timeout per engine
- Falls back to next engine on timeout
- Classifications: SUCCESS, TIMEOUT, NETWORK_ERROR

#### Task Controller (core/task_controller.py)
```python
class TaskController:
    - create_task(url) → Task ID
    - update_status(task_id, status)
    - get_all_tasks() → List
    - cancel_task(task_id)
```

**States**: PENDING → RUNNING → COMPLETED/FAILED

---

### 2. EXTRACTION ENGINES

#### Base Engine (engines/base_engine.py)
```python
class BaseEngine:
    async def extract(url) → {media_items}
    async def validate(url) → bool
    get_name() → str
    get_priority() → int
```

#### Engine Types
```
Fast Engine       → Direct links (like URLs)
                 → Speed: 100ms-300ms
                 → Reliability: 95%

Spider Engine     → HTML scraping
                 → Speed: 500ms-2s
                 → Reliability: 85%

Headless Engine   → JavaScript rendering
                 → Speed: 2s-5s
                 → Reliability: 90%

Stealth Engine    → Anti-detection
                 → Speed: 1s-3s
                 → Reliability: 80%

Media Engine      → Platform-specific
                 → Speed: 300ms-1s
                 → Reliability: 98%
```

---

### 3. PIPELINE PROCESSING

#### Schema Validator (pipeline/schema_validator.py)
```python
class SchemaValidator:
    - validate(data) → bool
    - get_errors() → List[str]
```

**Validates**:
- URL format
- Media metadata
- Download config
- Engine output

#### Content Validator (pipeline/validator.py)
```python
async def validate_media(media_item) → bool
    - HEAD request to verify file
    - Check Content-Type
    - Verify file size
```

#### URL Parser (pipeline/parser.py) **[NEW]**
```python
class URLParser:
    - normalize_url(url) → str (clean)
    - extract_media_info(url) → Dict
    - validate_url_format(url) → bool
```

**Removes**:
- Tracking parameters (utm_*, fbclid, etc.)
- Session IDs
- Timestamp params
- Normalizes domain to lowercase

**Detects**:
- Media type from extension
- Shortened URLs
- Domain info

---

### 4. NETWORK LAYER

#### Session Manager (network/session_manager.py)
```python
class SessionManager:
    - get_session() → ClientSession
    - set_headers(headers)
    - configure_pool(min, max) → Connection pooling
```

**Features**:
- User-Agent rotation
- Connection pooling (50-500 connections)
- Timeout configuration
- SSL verification

#### Proxy Manager (network/proxy_manager.py)
```python
class ProxyManager:
    - add_proxy(proxy_url)
    - get_next_proxy() → URL
    - rotate_proxies() → bool
```

**Supports**:
- HTTP proxies
- SOCKS5 proxies
- Proxy failover
- Automatic retry

#### SSRF Guard (network/ssrf_guard.py)
```python
class SSRFGuard:
    - validate_request(url) → bool
    - is_private_ip(ip) → bool
```

**Blocks**:
- Private IPs (10.*, 192.168.*, 127.*)
- Local network access
- Metadata services
- File protocols

---

### 5. DOWNLOAD LAYER

#### Download Manager (downloader/download_manager.py)
```python
class DownloadManager:
    async def download(url, filename) → Future
    async def shutdown()
    update_bandwidth_limit(mbps)
```

**Features**:
- Multi-threaded execution (ThreadPoolExecutor)
- Resume support (Range headers)
- Partial file detection
- Atomic file writes
- Bandwidth throttling

**Process**:
```
1. Check if file exists
2. If partial → Calculate resume offset
3. Add resume headers to request
4. Download in chunks
5. Write atomically (temp → final)
6. Verify file
7. Cleanup temp files
```

#### Bandwidth Manager (downloader/bandwidth_manager.py)
```python
class BandwidthManager:
    - set_limit(mbps) → Throttle to rate
    - get_current_speed() → mbps
    - calculate_sleep_time(chunk_size) → seconds
```

**Algorithm**:
```
time_slot = chunk_size / (limit_mbps * 1024 * 1024)
actual_speed = chunk_size / (time_elapsed)
if actual_speed > limit:
    sleep(calculated_time)
```

---

### 6. STORAGE LAYER

#### Cache Layer (storage/cache.py)
```python
class CacheLayer:
    - set(url, result, ttl_hours=24)
    - get(url) → Result|None
    - invalidate(url)
    - clear_expired()
```

**Features**:
- TTL-based expiration (default 24h)
- LRU eviction
- JSON serialization
- Config-based limits

#### Deduplicator (storage/deduplicator.py)
```python
class Deduplicator:
    - add(url) → bool
    - is_duplicate(url) → bool
    - get_duplicates() → List[str]
```

**Method**: MD5 hash of normalized URL

#### State Manager (storage/state_manager.py)
```python
class StateManager:
    - save_state(state_dict)
    - load_state() → Dict
    - get_last_status() → str
```

**Persists**:
- Download history
- Task queue state
- Configuration
- Metrics snapshots

---

### 7. MONITORING PLANE

#### Logger (monitoring/logger.py)
```python
def get_logger(module_name) → Logger
    - info(msg, extra={})
    - warning(msg, extra={})
    - error(msg, extra={})
```

**Format**: JSON (structured logging)
```json
{
  "timestamp": "2026-04-16T14:30:45Z",
  "level": "INFO",
  "module": "DownloadManager",
  "message": "Download complete",
  "context": {
    "url": "https://...",
    "size_mb": 1024,
    "duration_sec": 45
  }
}
```

#### Metrics (monitoring/metrics.py)
```python
class Metrics:
    - get_summary() → Dict
    - get_domain_stats() → Dict
    - get_engine_stats() → Dict
    - record_request(domain, engine, status)
```

**Tracked**:
- Total requests
- Success rate
- Domain performance
- Engine usage
- Error rates
- Latency percentiles

---

## 📊 DATA FLOW: DETAILED EXECUTION

### Download Execution Timeline
```
T0: User clicks "Start"
    └─► URL input validation

T1: SSRF check (10ms)
    └─► Validates URL safety
    
T2: URL Parsing (5ms)
    └─► Normalize, extract metadata

T3: Dedup check (5ms)
    └─► Already downloaded?

T4: Cache check (5ms)
    └─► Recently cached?

T5: Router selection (50ms)
    └─► Choose best engine

T6: Engine execution (500ms-5s)
    ├─► Extract media URLs
    ├─► Format: List[MediaItem]
    
T7: Content validation (100ms-1s)
    ├─► HEAD request per media
    ├─► Check Content-Type
    └─► Verify availability

T8: Download manager (Seconds-Hours)
    ├─► Multi-threaded download
    ├─► Progress updates (1Hz)
    ├─► Resume if interrupted
    
T9: File write (100ms-1s)
    ├─► Atomic write
    ├─► Create temp file
    ├─► Rename to final
    
T10: Completion (10ms)
    ├─► Update cache
    ├─► Record metrics
    └─► ✓ Done

Total: 1-10 seconds (fast path)
       + Download time (variable)
```

---

## 🔀 CONCURRENCY MODEL

### Async/Await
```python
# Engine extraction (async)
async def extract_urls(url):
    async with aiohttp.ClientSession as session:
        async with session.get(url) as response:
            return parse_response(response)

# Concurrent execution
tasks = [extract(url) for url in urls]
results = await asyncio.gather(*tasks)
```

### Multi-threading
```python
# Download execution (threaded)
executor = ThreadPoolExecutor(max_workers=10)
future = executor.submit(download_file, url)
result = future.result()  # Block until done

# Allows GUI to remain responsive
```

### Mixed Model
```
Main Thread (PyQt GUI)
    ↓
Orchestration (asyncio event loop)
    ↓
Engine extraction (async/await)
    ↓
Download threads (ThreadPoolExecutor)
    ↓
File I/O (atomic writes)
```

---

## 🔐 SECURITY ARCHITECTURE

```
Input → [SSRF Guard] → [URL Validator] → [Schema Validator]
                           ↓
                      Sanitized & Safe
                           ↓
         [Execution] → [Logging] → [No Sensitive Data]
```

**Security Layers**:
1. Input validation (URL format)
2. SSRF protection (no private IPs)
3. Schema validation (type checking)
4. Logging scrubbing (no credentials)
5. File permissions (restricted access)

---

## 📈 SCALABILITY CONSIDERATIONS

### Current Design (Single Machine)
```
┌─────────────────────┐
│  Single Instance    │
├─────────────────────┤
│ Max Workers: 10     │
│ Max Memory: 1 GB    │
│ Throughput: 5-100 req/s
└─────────────────────┘
```

### Future: Distributed (Phase E+)
```
┌─────────────────────────────────────┐
│         Load Balancer               │
├────────┬────────────┬────────────┤
│        │            │            │
▼        ▼            ▼            ▼
Instance 1  Instance 2  Instance 3  ...
│        │            │            │
└────────┴────────────┴────────────┘
         │
    ┌────▼─────┐
    │ Database  │ (PostgreSQL)
    │ Cache     │ (Redis)
    │ Queue     │ (RabbitMQ)
    └──────────┘
```

---

## 🔄 DESIGN PATTERNS

### Pattern 1: Strategy Pattern (Engines)
```python
# Different strategies for extraction
class Engine(ABC):
    @abstractmethod
    async def extract(url): pass

# Runtime selection based on URL
router.select_engine(url)
```

### Pattern 2: Observer Pattern (Metrics)
```python
# Events trigger metric recording
@on_event("download_complete")
def record_metrics(event):
    metrics.record_success()
```

### Pattern 3: Factory Pattern (Logger)
```python
# Create logger instances
logger = get_logger("ModuleName")
# All loggers use same config
```

### Pattern 4: Chain of Responsibility (Pipeline)
```python
# Each layer does its job
input → validator → parser → router → engines
        ↓
     if fails, stop
     if passes, continue
```

---

## 📝 CODE ORGANIZATION

```
nexus-downloader/
│
├── core/                 # Orchestration
│  ├── router.py         # Engine selection
│  ├── task_controller   # Task management
│  └── ...
│
├── engines/             # Extraction strategies
│  ├── base_engine.py
│  ├── fast_engine_v1...
│  └── ...
│
├── pipeline/            # Data processing
│  ├── schema_validator
│  ├── validator
│  └── parser            # ⭐ NEW
│
├── network/             # Network access
│  ├── session_manager
│  └── proxy_manager
│
├── downloader/          # Download execution
│  ├── download_manager
│  └── bandwidth_manager
│
├── storage/             # Data persistence
│  ├── cache
│  ├── deduplicator
│  └── state_manager
│
├── monitoring/          # Observability
│  ├── logger
│  └── metrics
│
├── gui/                 # User interface
│  ├── app.py           # Dual-mode app
│  └── widgets/         # UI components
│
├── utils/               # Utilities
│  ├── constants
│  ├── retry
│  └── helpers
│
└── tests/               # Test suite
   ├── test_download
   ├── test_router
   └── test_engine
```

---

## 📊 DEPLOYMENT ARCHITECTURE

```
┌──────────────────────────────────────────┐
│         Development Environment          │
│  └─ SQLite cache, local file storage     │
├──────────────────────────────────────────┤
│         Staging Environment              │
│  └─ PostgreSQL cache, NFS storage        │
├──────────────────────────────────────────┤
│         Production Environment           │
│  ├─ Docker container                     │
│  ├─ Kubernetes orchestration             │
│  ├─ Redis cache cluster                  │
│  └─ S3 storage backend                   │
└──────────────────────────────────────────┘
```

---

## 🎯 KEY METRICS

### Performance Targets
- **Avg Latency**: <200ms (router + validation)
- **Engine Speed**: 200ms-5s  
- **Download**: 5-100 Mbps (configurable)
- **Memory**: <500 MB typical
- **Throughput**: 10-50 files/min

### Quality Targets
- **Success Rate**: >95%
- **Error Recovery**: 3 retries with backoff
- **Test Coverage**: >95%
- **Uptime**: 99.9%

---

**Version**: 5.0 | **Status**: Production Ready  
**Last Updated**: April 16, 2026  
**Architecture**: Modular, Scalable, Secure
