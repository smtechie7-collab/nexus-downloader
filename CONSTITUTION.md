📜 NEXUS MEDIA DOWNLOADER — CONSTITUTION v5.0 (THE ZENITH EDITION)

Status: Mandatory, Non-Negotiable
System Type: Fully Distributed, Self-Learning Extraction Framework
Execution Model: Async + Orchestrated + Priority-Driven + Adaptive + Distributed-Ready

🎯 1. Core Philosophy (The Zenith Standards)

1.1 Deterministic & Self-Optimizing

Har function ka output predictable hona chahiye. 

Same input → Same output. No hidden global state.

Self-Optimization: System must learn from failures and automatically adjust strategies over time without human intervention.

1.2 Engine Isolation & Schema Enforcement

Har engine ek sandboxed unit hai.

Plugin Isolation: Engine crashes cannot corrupt the pipeline (Strict try/catch wrapper at Router level).

Schema Validation Layer: Blind trust is eradicated. Output MUST pass strict schema enforcement (e.g., Pydantic) before entering the queue. Malformed data is instantly rejected.

1.3 Backpressure & Fail-Safe Execution

Link fail → Skip + Log + Classify Error

Engine fail → Catch in Sandbox + Trigger Fallback Chain + Update Metrics

Queue fail → Retry with Exponential Backoff

Backpressure Rule: If the queue grows faster than the download rate, intake (scraping) MUST automatically throttle to prevent memory exhaustion.

1.4 Distributed First & Scalability

Designed for 1 URL or 1 Million URLs.

WorkerNode Abstraction: The system must be able to decouple scraping from downloading. Capable of running the Queue on Redis/RabbitMQ for multi-machine scaling in the future.

1.5 Zero Trust & Advanced Security

SSRF Protection: Scraper must NEVER resolve local/private IP ranges (127.0.0.0/8, 10.0.0.0/8) to prevent Server-Side Request Forgery.

Malicious Redirect Handling: Max redirect limits enforced; suspicious redirect chains dropped.

File Injection Prevention: File extensions must be validated against actual MIME types/magic bytes, not just URL strings.

🧠 2. System Architecture (The 5 Planes)

2.1 Task Orchestration & Control Plane (The Brain)

TaskController: Total control over system state (cancel(), pause(), resume()).

PriorityQueue: Strict scheduling (HIGH: User, MEDIUM: Playlist, LOW: Background Crawl).

AdaptiveEngineSelector (NEW): Tracks success_rate per domain. Auto-promotes the best engine and auto-deprecates failing engines. Replaces static DomainStrategy.

BackpressureController (NEW): Slows intake when Queue > Threshold. Prioritizes HIGH tasks, throttles LOW tasks.

RateLimiter: Per-domain limits, global concurrency limits, adaptive slowdowns.

2.2 Execution Plane (The Muscles)

Engines: Sandboxed extractors (Fast, Spider, Stealth, Headless, Media).

SchemaValidator (NEW): Strictly enforces the JSON/Pydantic output contract.

Content Validator: Validates engine output sanity (File size, Content-Type headers) before final queuing.

SessionManager: Centralized cookie store, header rotation, and auth handling.

2.3 Distributed Output Plane (The Hands)

WorkerNode Abstraction (NEW): Downloads execute as independent workers capable of remote queue consumption.

Download Manager: Chunking, resuming, networking.

BandwidthManager: Enforces max_kbps per download and a global_bandwidth_cap to prevent network starvation.

File Writer: Safe disk IO with collision prevention.

2.4 Data Plane (The Memory)

StateManager: Checkpoints queues and partial downloads to disk/DB.

Deduplicator: Hash-based and URL-normalization checks.

CacheLayer: URL → Response mapping with TTL.

🔄 3. Strict Data Flow Contract

Input → Deduplicator → Cache Check → Adaptive Selector → RateLimiter → Engine (Sandboxed) → SchemaValidator → Content Validator → PriorityQueue (Monitored by BackpressureController) → WorkerNode (Downloader w/ BandwidthManager) → Storage

👉 Rule: Bypass of this exact chain is strictly forbidden under any circumstances.

3.1 Standard Data Contract (STRICT ENFORCEMENT)

{
    "status": "success" | "fail",
    "source": "engine_name_vX",
    "media": [
        {
            "url": "string",
            "type": "video" | "audio" | "image" | "document" | "other",
            "quality": "string",
            "metadata": {}
        }
    ],
    "error_type": "NetworkError|ParseError|AccessDenied|RateLimited|None",
    "error_msg": "string" | null
}


⚙️ 4. Resource & Concurrency Control (CRITICAL)

4.1 ResourceGuard & Backpressure

System unlimited hai, par hardware nahi.

MAX_THREADS: Bound to CPU cores (e.g., os.cpu_count() * 2).

MEMORY_CAP: Pause/Throttle intake if RAM > 85%.

DISK_SPACE_LIMIT: Hard pause system if free disk < 2GB.

4.2 RateLimiter Protocols

PER_DOMAIN_LIMIT: Max N requests/sec.

GLOBAL_LIMIT: Total outbound connection cap.

ADAPTIVE_SLOWDOWN: Automatically inject delays on HTTP 429.

🛡️ 5. Advanced Security & Session Layer

5.1 Hardened SessionManager

Cookie Store & Header Rotation: Dynamic User-Agent, Accept, Referer.

Anti-Ban: Delay jitter (Randomized intervals) and Proxy support.

SSRF Shield: Strict domain validation before executing any HTTP request. Private IPs are blacklisted.

💾 6. State & Download System

6.1 StateManager & Distributed Readiness

Queues are periodically written to persistent storage (DB/Redis/JSON).

Partial downloads use .part extension with byte-tracking.

6.2 Chunk-Based Download

Large files must be downloaded in chunks. Resume support is mandatory.

🧾 7. Observability & Self-Learning

7.1 Error Classification (Crucial for Fallbacks)

NetworkError: Timeout, DNS failure → Retry.

ParseError: CSS changed → Escalate to deep engine.

AccessDenied: 403 Forbidden → Change Proxy/Headers.

RateLimited: 429 → Trigger Backoff.

7.2 Telemetry & Adaptive Metrics

success_rate: Adjusts engine priority dynamically.

avg_extraction_time: Identifies degraded performance.

engine_fail_rate: Soft-deprecates broken engines.

7.3 Structured Logging

{
    "timestamp": "ISO-8601",
    "level": "INFO|ERROR|DEBUG|CRITICAL",
    "module": "module_name",
    "error_type": "Categorized_Error",
    "message": "event_description",
    "context": {"url": "...", "task_id": "...", "retries": 1}
}


🧩 8. Plugin & Versioning System

8.1 Engine Versioning

Engines must be version-tagged: youtube_engine_v1.py

Router maintains mapping to the latest stable version and rolls back on high failure rates.

🎛️ 9. Configuration System

Single source of truth: config.yaml
Contains:

Rate limits, Timeouts, Backpressure thresholds.

Resource limits (RAM, Disk bounds, Global Bandwidth Caps).

Worker configurations (Local vs Remote).
👉 Rule: Hardcoded logic thresholds inside .py files are strictly prohibited.

🧪 10. Testing Protocol

10.1 Minimum Coverage

Schema enforcement tests (Reject invalid JSON).

Task cancellation, Backpressure, and RateLimiter tests.

SSRF and malicious payload rejection tests.

🎨 11. UI Contract

GUI = Viewer only

Allowed: Start/Stop/Pause/Cancel via TaskController, Progress, Logs, Metrics Dashboard.

Not Allowed: Parsing, Queuing, Rate limiting logic.

🤖 12. AI Execution Rules (STRICT HARD MODE)

AI must:

Never bypass the SchemaValidator, RateLimiter, or Content Validator.

Always write code compatible with WorkerNode distribution (no local memory hacks).

Always wrap engine executions in isolated try/except sandboxes.

Enforce Pydantic/Typing strictly.

🔒 13. Forbidden Practices (CRITICAL)

❌ God functions & Spagetti logic.

❌ In-memory queues without disk/DB checkpoints.

❌ Blindly trusting scraped URLs (Validation is mandatory).

❌ Hardcoded secrets, headers, or timeouts.

❌ Resolving localhost/private IPs via scraper.

🧭 Final Directive

"The system is a self-regulating, self-learning, and fully orchestrated organism. It honors task priority, 
limits its own resources to prevent starvation, dynamically promotes the best tools, validates everything it touches, 
and isolates its core from the chaos of volatile external networks and malicious actors."