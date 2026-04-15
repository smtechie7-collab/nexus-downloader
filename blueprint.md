📘 NEXUS MEDIA DOWNLOADER — MASTER BLUEPRINT (IMPLEMENTATION SPEC)

Purpose:
This document converts the Constitution v4.0 into strict, executable engineering instructions.
No ambiguity. No interpretation required.

🧱 1. PROJECT ROOT STRUCTURE (STRICT)
nexus_downloader/
│
├── main.py
├── config.yaml
├── requirements.txt
│
├── core/                  # Control Plane
│   ├── router.py
│   ├── domain_strategy.py
│   ├── task_controller.py
│   ├── priority_queue.py
│   ├── rate_limiter.py
│   ├── resource_guard.py
│   └── backpressure.py
│
├── engines/               # Execution Plane
│   ├── base_engine.py
│   ├── fast_engine_v1.py
│   ├── spider_engine_v1.py
│   ├── stealth_engine_v1.py
│   ├── headless_engine_v1.py
│   └── media_engine_v1.py
│
├── pipeline/              # Data Flow Control
│   ├── validator.py
│   ├── schema_validator.py
│   ├── parser.py
│
├── network/
│   ├── session_manager.py
│   ├── proxy_manager.py
│
├── downloader/            # Output Plane
│   ├── download_manager.py
│   ├── bandwidth_manager.py
│   ├── file_writer.py
│
├── storage/               # Data Plane
│   ├── state_manager.py
│   ├── cache.py
│   ├── deduplicator.py
│
├── monitoring/
│   ├── logger.py
│   ├── metrics.py
│
├── utils/
│   ├── helpers.py
│   ├── constants.py
│
└── tests/
    ├── test_router.py
    ├── test_engine.py
    ├── test_download.py

👉 Rule: Is structure ko break karna = architecture violation

🔄 2. EXECUTION FLOW (NON-NEGOTIABLE)
User Input
 → Deduplicator
 → CacheLayer
 → DomainStrategy
 → Router
 → RateLimiter
 → Engine (Sandboxed)
 → SchemaValidator
 → ContentValidator
 → Parser
 → PriorityQueue
 → TaskController
 → Downloader (BandwidthManager)
 → FileWriter
 → Storage

👉 Any bypass = critical violation

🧠 3. CORE COMPONENT CONTRACTS
3.1 Router (core/router.py)

Responsibility:

Select engine
Apply fallback chain
Wrap engine in sandbox
class Router:
    def route(self, url: str) -> dict:
        """Returns standardized engine output"""
3.2 Base Engine (engines/base_engine.py)
class BaseEngine:
    def extract(self, url: str) -> dict:
        """Must return STANDARD DATA FORMAT only"""

👉 No download logic here

3.3 Standard Data Format (ENFORCED)
{
    "status": "success" | "fail",
    "source": "engine_name_vX",
    "media": [
        {
            "url": str,
            "type": str,
            "quality": str,
            "metadata": dict
        }
    ],
    "error_type": str,
    "error_msg": str | None
}
3.4 Priority Queue (core/priority_queue.py)
class PriorityQueue:
    def add(task, priority: str): pass
    def get(): pass

Priority:

HIGH
MEDIUM
LOW
3.5 Task Controller (core/task_controller.py)
class TaskController:
    def cancel(task_id): pass
    def pause(): pass
    def resume(): pass
3.6 Rate Limiter (core/rate_limiter.py)
class RateLimiter:
    def allow(domain: str) -> bool: pass
3.7 Resource Guard (core/resource_guard.py)
class ResourceGuard:
    def check() -> bool:
        """Block tasks if system overloaded"""
3.8 Schema Validator (pipeline/schema_validator.py)
def validate(data: dict) -> bool:
    """Reject invalid engine output"""
3.9 Content Validator (pipeline/validator.py)
def validate_media(url: str) -> bool:
    """Check headers, type, size"""
3.10 Download Manager (downloader/download_manager.py)
class DownloadManager:
    def download(url: str, path: str): pass
3.11 Bandwidth Manager
class BandwidthManager:
    def throttle(): pass
3.12 State Manager (storage/state_manager.py)
class StateManager:
    def save(): pass
    def load(): pass
3.13 Deduplicator (storage/deduplicator.py)
def is_duplicate(url: str) -> bool: pass
3.14 Cache Layer (storage/cache.py)
def get(url: str): pass
def set(url: str, data): pass
⚙️ 4. CONFIG SYSTEM (MANDATORY)

config.yaml example:

rate_limit:
  per_domain: 5
  global: 50

resources:
  max_threads: 8
  memory_limit_percent: 85
  disk_min_gb: 2

download:
  path: "./downloads"
  chunk_size: 1048576

bandwidth:
  max_kbps: 1024

retry:
  max_attempts: 3

👉 No hardcoding allowed

🧵 5. CONCURRENCY MODEL
Task	Tool
Engine calls	asyncio
Downloads	ThreadPoolExecutor
Queue	thread-safe
🧪 6. TESTING RULES

Minimum:

Router fallback test
Engine output format test
Download resume test
Rate limit simulation
Crash recovery test
🛡️ 7. ERROR HANDLING (STRICT)

Every error MUST be categorized:

NetworkError
ParseError
AccessDenied
RateLimited

👉 No generic exceptions allowed

📊 8. LOGGING FORMAT
{
  "timestamp": "",
  "level": "",
  "module": "",
  "message": "",
  "context": {}
}
🚫 9. FORBIDDEN ACTIONS
❌ Direct download inside engine
❌ GUI logic in core
❌ Blocking calls
❌ Skipping validators
❌ Hardcoded configs
🚀 10. PHASE-WISE BUILD ORDER (IMPORTANT)
Phase 1 (Minimum Working System)
Router
BaseEngine
One Engine (FastEngine)
Queue
DownloadManager
Phase 2
RateLimiter
Cache
Deduplicator
Phase 3
SessionManager
Validator
Metrics
Phase 4
Stealth + Headless engines
Bandwidth manager
Full orchestration
🧭 FINAL DIRECTIVE

"No module should assume anything. Everything must be validated, controlled, and observable."

🧠 Reality Check (Important)

This blueprint is:

✅ AI-executable
✅ Developer-safe
✅ Scalable
✅ Clean

🚀 Next Step

Now you are ready to move to:

👉 Code Generation Phase

If you want, I’ll generate:

✅ Phase 1 full code (copy-paste ready)
✅ Gemini prompt for Android Studio agent
✅ Base working CLI version