# REST API SPECIFICATION - Nexus Downloader v5.0
**API Design for Future Implementation (Phase E)**  
**Status**: Design Document (Not Yet Implemented)  
**Last Updated**: April 16, 2026

---

## 📋 TABLE OF CONTENTS
1. Overview
2. Authentication
3. API Endpoints
4. Request/Response Models
5. Error Codes
6. Rate Limiting
7. Webhooks (Future)
8. Implementation Guide

---

## 1. OVERVIEW

### Purpose
The REST API provides programmatic access to Nexus Downloader functionality for:
- Automation & scripting
- Third-party integrations
- Remote management
- Headless server deployments

### Base URL
```
Local Development:  http://localhost:8000/api/v1
Production:         https://nexus.example.com/api/v1
```

### API Version
- Current: `v1`
- Versioning strategy: URL-based (`/api/v1`, `/api/v2`)

### Content Types
- Request:  `application/json`
- Response: `application/json`

---

## 2. AUTHENTICATION

### Method: API Key (Bearer Token)
```
Authorization: Bearer YOUR_API_KEY_HERE
```

### Getting an API Key
```bash
# Endpoint (future)
POST /api/v1/auth/keys

# Request
{
  "name": "My App",
  "expires_in_days": 365
}

# Response
{
  "key": "nxd_abc123xyz789...",
  "created_at": "2026-04-16T14:30:00Z",
  "expires_at": "2027-04-16T14:30:00Z"
}
```

### Security
- Keys should be kept secret (like passwords)
- Use environment variables: `export NEXUS_API_KEY="..."`
- Rotate keys periodically
- Revoke compromised keys immediately
- HTTPS required in production

---

## 3. API ENDPOINTS

### 3.1 Downloads

#### Start Download
```http
POST /api/v1/downloads
Content-Type: application/json
Authorization: Bearer {token}

{
  "url": "https://example.com/video.mp4",
  "output_path": "/home/user/downloads",
  "quality": "720p",
  "resume": true,
  "metadata": {
    "title": "My Video",
    "tags": ["video", "tutorial"]
  }
}

Response (201 Created):
{
  "id": "dl_abc123",
  "url": "https://example.com/video.mp4",
  "status": "pending",
  "created_at": "2026-04-16T14:30:00Z",
  "estimated_time_sec": 120
}
```

#### Get Download Status
```http
GET /api/v1/downloads/{id}
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "dl_abc123",
  "url": "https://example.com/video.mp4",
  "status": "downloading",
  "progress": 45,
  "speed_mbps": 2.5,
  "time_elapsed_sec": 60,
  "time_remaining_sec": 60,
  "size_bytes": 1073741824,
  "downloaded_bytes": 483183820,
  "filename": "video.mp4",
  "output_path": "/home/user/downloads",
  "created_at": "2026-04-16T14:30:00Z",
  "started_at": "2026-04-16T14:31:00Z",
  "completed_at": null,
  "error": null
}
```

Status Values: `pending`, `downloading`, `paused`, `completed`, `failed`, `cancelled`

#### List Downloads
```http
GET /api/v1/downloads?status=all&limit=50&offset=0
Authorization: Bearer {token}

Response (200 OK):
{
  "items": [
    { ... download object ... },
    { ... download object ... }
  ],
  "total": 150,
  "limit": 50,
  "offset": 0
}
```

Query Parameters:
- `status`: `all`, `completed`, `failed`, `downloading`
- `limit`: 1-100 (default: 50)
- `offset`: pagination offset
- `domain`: filter by domain
- `sort_by`: `created_at`, `status`, `speed`

#### Pause Download
```http
PATCH /api/v1/downloads/{id}/pause
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "dl_abc123",
  "status": "paused",
  "progress": 45
}
```

#### Resume Download
```http
PATCH /api/v1/downloads/{id}/resume
Authorization: Bearer {token}

Response (200 OK):
{
  "id": "dl_abc123",
  "status": "downloading",
  "progress": 45
}
```

#### Cancel Download
```http
DELETE /api/v1/downloads/{id}
Authorization: Bearer {token}

Response (204 No Content)
```

#### Batch Download
```http
POST /api/v1/downloads/batch
Authorization: Bearer {token}

{
  "urls": [
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4"
  ],
  "output_path": "/home/user/downloads",
  "concurrent": 2,
  "resume_failed": true
}

Response (201 Created):
{
  "batch_id": "batch_abc123",
  "status": "queued",
  "total_items": 2,
  "download_ids": [
    "dl_abc123",
    "dl_def456"
  ]
}
```

---

### 3.2 Metrics

#### Get Metrics Summary
```http
GET /api/v1/metrics/summary
Authorization: Bearer {token}

Response (200 OK):
{
  "total_requests": 1245,
  "total_successes": 1200,
  "total_failures": 45,
  "success_rate": 0.965,
  "total_downloaded_bytes": 107374182400,
  "total_downloaded_gb": 100,
  "uptime_seconds": 86400,
  "average_speed_mbps": 2.5,
  "current_memory_mb": 485,
  "current_cpu_percent": 12
}
```

#### Get Domain Statistics
```http
GET /api/v1/metrics/domains
Authorization: Bearer {token}

Response (200 OK):
{
  "domains": [
    {
      "domain": "youtube.com",
      "requests": 542,
      "success_rate": 0.96,
      "avg_latency_ms": 245,
      "min_latency_ms": 120,
      "max_latency_ms": 1250
    },
    {
      "domain": "example.com",
      "requests": 245,
      "success_rate": 0.99,
      "avg_latency_ms": 150,
      "min_latency_ms": 50,
      "max_latency_ms": 450
    }
  ]
}
```

#### Get Engine Statistics
```http
GET /api/v1/metrics/engines
Authorization: Bearer {token}

Response (200 OK):
{
  "engines": [
    {
      "name": "media_engine",
      "usage_count": 450,
      "success_rate": 0.98,
      "avg_execution_ms": 500,
      "total_data_processed_gb": 50
    },
    {
      "name": "headless_engine",
      "usage_count": 245,
      "success_rate": 0.90,
      "avg_execution_ms": 2500,
      "total_data_processed_gb": 30
    }
  ]
}
```

---

### 3.3 Configuration

#### Get Current Configuration
```http
GET /api/v1/config
Authorization: Bearer {token}

Response (200 OK):
{
  "download": {
    "max_workers": 10,
    "timeout": 30,
    "retry_attempts": 3,
    "resume_enabled": true
  },
  "rate_limit": {
    "enabled": true,
    "per_domain": 5,
    "burst_size": 20
  },
  "logging": {
    "level": "INFO",
    "format": "json"
  }
}
```

#### Update Configuration
```http
PATCH /api/v1/config
Authorization: Bearer {token}

{
  "download": {
    "max_workers": 20
  },
  "rate_limit": {
    "per_domain": 10
  }
}

Response (200 OK):
{ ... updated config ... }
```

---

### 3.4 System

#### Health Check
```http
GET /api/v1/health
(No auth required)

Response (200 OK):
{
  "status": "healthy",
  "version": "5.0",
  "uptime_seconds": 86400,
  "api_version": "v1"
}
```

Status Values: `healthy`, `degraded`, `unhealthy`

#### System Status
```http
GET /api/v1/system/status
Authorization: Bearer {token}

Response (200 OK):
{
  "status": "running",
  "memory_mb": 485,
  "memory_limit_mb": 1000,
  "cpu_percent": 12,
  "disk_free_gb": 150,
  "network_active": true,
  "last_error": null,
  "error_count_24h": 3
}
```

#### Get Logs
```http
GET /api/v1/logs?level=ERROR&limit=100
Authorization: Bearer {token}

Response (200 OK):
{
  "logs": [
    {
      "timestamp": "2026-04-16T14:30:00Z",
      "level": "ERROR",
      "module": "DownloadManager",
      "message": "Download failed",
      "context": {
        "url": "https://...",
        "error": "Connection timeout"
      }
    }
  ],
  "total": 3,
  "limit": 100
}
```

Query Parameters:
- `level`: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- `limit`: 1-1000 (default: 100)
- `offset`: pagination
- `module`: filter by module name

---

## 4. REQUEST/RESPONSE MODELS

### Download Object
```json
{
  "id": "dl_abc123xxx",
  "url": "https://example.com/video.mp4",
  "filename": "video.mp4",
  "output_path": "/home/user/downloads",
  "status": "completed",
  "progress": 100,
  "speed_mbps": 2.5,
  "time_elapsed_sec": 120,
  "time_remaining_sec": 0,
  "size_bytes": 1073741824,
  "downloaded_bytes": 1073741824,
  "quality": "720p",
  "engine_used": "media_engine",
  "retries": 0,
  "created_at": "2026-04-16T14:30:00Z",
  "started_at": "2026-04-16T14:31:00Z",
  "completed_at": "2026-04-16T14:33:00Z",
  "error": null,
  "metadata": {
    "title": "Video Title",
    "tags": ["video"]
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "NETWORK_ERROR",
    "message": "Connection timeout after 30 seconds",
    "details": {
      "url": "https://...",
      "timeout": 30
    },
    "request_id": "req_abc123"
  }
}
```

---

## 5. ERROR CODES

### HTTP Status Codes
```
200 OK              - Request successful
201 Created         - Resource created
204 No Content      - Success, no response body
400 Bad Request     - Invalid input/parameters
401 Unauthorized    - Authentication failed
403 Forbidden       - Permission denied
404 Not Found       - Resource not found
409 Conflict        - Resource state conflict
429 Too Many Requests - Rate limit exceeded
500 Internal Error  - Server error
503 Unavailable     - Service temporarily unavailable
```

### API Error Codes
```
INVALID_URL         - URL format invalid or blocked
NETWORK_ERROR       - Network/connection problem
TIMEOUT             - Request timeout
DOWNLOAD_FAILED     - Download execution failed
AUTHENTICATION_FAILED - Invalid API key
RATE_LIMIT_EXCEEDED - Too many requests
RESOURCE_NOT_FOUND  - Download ID not found
INVALID_CONFIG      - Configuration invalid
INSUFFICIENT_SPACE  - Not enough disk space
ENGINE_FAILED       - Extraction engine error
```

---

## 6. RATE LIMITING

### Limits
- **Free tier**: 100 requests/hour, 10 concurrent downloads
- **Pro tier**: 1000 requests/hour, 50 concurrent downloads
- **Enterprise**: Unlimited

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1713268200
X-RateLimit-Retry-After: 300
```

### When Rate Limited (429)
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded: 100/hour",
    "retry_after": 300
  }
}
```

**Wait time**: See `Retry-After` header or `retry_after` field

---

## 7. WEBHOOKS (Future Enhancement)

### Webhook Events
```
download.started      - Download began
download.progress     - Progress update (5%, 10%, etc.)
download.completed    - Download finished
download.failed       - Download failed
download.paused       - Download paused
download.resumed      - Download resumed
download.cancelled    - Download cancelled
```

### Webhook Payload
```json
{
  "event": "download.completed",
  "timestamp": "2026-04-16T14:33:00Z",
  "data": {
    "id": "dl_abc123",
    "url": "https://...",
    "filename": "video.mp4",
    "size_bytes": 1073741824,
    "duration_sec": 120
  }
}
```

### Register Webhook
```http
POST /api/v1/webhooks
Authorization: Bearer {token}

{
  "url": "https://myapp.com/webhooks/nexus",
  "events": ["download.completed", "download.failed"],
  "active": true
}

Response:
{
  "id": "webhook_abc123",
  "url": "https://myapp.com/webhooks/nexus",
  "created_at": "2026-04-16T14:30:00Z"
}
```

---

## 8. IMPLEMENTATION GUIDE

### Phase E Timeline
```
Week 1:
  - Set up FastAPI/Flask project
  - Implement authentication
  - Build download endpoints
  
Week 2:
  - Build metrics endpoints
  - Add configuration endpoints
  - Add tests (>90% coverage)
  
Week 3:
  - System endpoints
  - Documentation (OpenAPI/Swagger)
  - Docker containerization
  - Performance optimization
```

### Technology Stack (Proposed)
```
Framework:      FastAPI (modern, fast, auto-docs)
Server:         Uvicorn (production-ready ASGI)
Auth:           JWT or API keys (simple approach)
Rate Limiting:  slowapi (FastAPI middleware)
Docs:           Swagger/OpenAPI (auto-generated)
Testing:        pytest + httpx
Deployment:     Docker + Kubernetes
```

### Sample Implementation
```python
# app/main.py
from fastapi import FastAPI, HTTPException, Header
from typing import Optional

app = FastAPI(title="Nexus Downloader API", version="1.0")

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "version": "5.0"}

@app.post("/api/v1/downloads")
async def start_download(url: str, authorization: str = Header(None)):
    if not verify_token(authorization):
        raise HTTPException(status_code=401)
    # ... implementation
    return {"id": "dl_abc123", "status": "pending"}

@app.get("/api/v1/downloads/{download_id}")
async def get_download_status(download_id: str):
    # ... implementation
    return download_object
```

### Swagger UI
```
API Documentation available at:
http://localhost:8000/docs          (Interactive Swagger UI)
http://localhost:8000/redoc         (ReDoc documentation)
http://localhost:8000/openapi.json  (OpenAPI schema)
```

---

## EXAMPLE USAGE

### Using cURL
```bash
# Start download
curl -X POST http://localhost:8000/api/v1/downloads \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/video.mp4"}'

# Check status
curl -X GET http://localhost:8000/api/v1/downloads/dl_abc123 \
  -H "Authorization: Bearer YOUR_KEY"

# Pause
curl -X PATCH http://localhost:8000/api/v1/downloads/dl_abc123/pause \
  -H "Authorization: Bearer YOUR_KEY"
```

### Using Python
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# Start download
response = requests.post(
    f"{BASE_URL}/downloads",
    json={"url": "https://example.com/video.mp4"},
    headers=HEADERS
)
download_id = response.json()["id"]

# Check status
response = requests.get(
    f"{BASE_URL}/downloads/{download_id}",
    headers=HEADERS
)
print(response.json())
```

### Using JavaScript
```javascript
const apiKey = "your_api_key";
const baseUrl = "http://localhost:8000/api/v1";

// Start download
fetch(`${baseUrl}/downloads`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${apiKey}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    url: "https://example.com/video.mp4"
  })
})
.then(r => r.json())
.then(data => console.log("Download ID:", data.id))
```

---

## NOTES FOR IMPLEMENTATION

- **Security**: HTTPS required in production
- **CORS**: Will need to configure for browser access
- **Caching**: Some endpoints can be cached (e.g., domain stats)
- **Pagination**: Large result sets use limit/offset
- **Versioning**: URL-based versioning (`/api/v1`, `/api/v2`)
- **Monitoring**: All API calls logged and metered

---

**Status**: Design Document | **Phase**: E (Future)  
**Ready to implement when requested**  
**Estimated effort**: 1-2 weeks development
