# ContextDiff API - Developer Documentation

## Overview

ContextDiff is a REST API for semantic text difference analysis. It compares two text versions and identifies meaningful changes beyond simple string diffs, using LLM-powered analysis to detect factual changes, tone shifts, omissions, and additions.

## Base URL

```
Production: https://api.contextdiff.com
Development: http://localhost:8000
```

## Authentication

Currently not implemented. For production deployment, add API key authentication via headers:

```http
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Default:** 60 requests per minute per IP address
- **Burst:** Additional 10 requests allowed for short spikes
- **Headers returned:**
  - `X-RateLimit-Limit`: Maximum requests allowed
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Unix timestamp when limit resets

**Rate limit exceeded response:**
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

## Endpoints

### POST /v1/compare

Analyze semantic differences between original and generated text.

**Request Body:**

```json
{
  "original_text": "string",
  "generated_text": "string",
  "sensitivity": "low" | "medium" | "high"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `original_text` | string | Yes | The original/reference text |
| `generated_text` | string | Yes | The generated/modified text to compare |
| `sensitivity` | enum | No | Filter level for detected changes (default: "medium") |

**Sensitivity Levels:**

- `low`: Only critical factual changes (numbers, dates, names)
- `medium`: Factual changes plus significant tone shifts
- `high`: All changes including minor formatting and phrasing

**Response (200 OK):**

```json
{
  "summary": {
    "is_safe": false,
    "risk_score": 75,
    "semantic_change_level": "CRITICAL"
  },
  "changes": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "FACTUAL",
      "severity": "critical",
      "description": "Dosage amount changed from 5mg to 50mg",
      "original_span": {
        "text": "5mg",
        "start": 45,
        "end": 48
      },
      "generated_span": {
        "text": "50mg",
        "start": 45,
        "end": 49
      },
      "reasoning": "Critical medication dosage modification that could lead to overdose"
    }
  ]
}
```

**Response Fields:**

**Summary:**
| Field | Type | Description |
|-------|------|-------------|
| `is_safe` | boolean | Whether changes are safe/acceptable |
| `risk_score` | integer | Risk level 0-100 (higher = more dangerous) |
| `semantic_change_level` | enum | Overall change severity: NONE, MINOR, MODERATE, CRITICAL, FATAL |

**Change Item:**
| Field | Type | Description |
|-------|------|-------------|
| `id` | uuid | Unique identifier for this change |
| `type` | enum | Change category: FACTUAL, TONE, OMISSION, ADDITION, FORMATTING |
| `severity` | enum | Change severity: info, warning, critical |
| `description` | string | Human-readable explanation |
| `original_span` | object | Location in original text |
| `generated_span` | object | Location in generated text |
| `reasoning` | string | Detailed analysis reasoning |

**Span Object:**
| Field | Type | Description |
|-------|------|-------------|
| `text` | string | The actual text content |
| `start` | integer | Start index in source text |
| `end` | integer | End index in source text (exclusive) |

**Error Responses:**

**422 Unprocessable Entity** - Validation error:
```json
{
  "detail": [
    {
      "loc": ["body", "sensitivity"],
      "msg": "value is not a valid enumeration member",
      "type": "type_error.enum"
    }
  ]
}
```

**429 Too Many Requests** - Rate limit exceeded:
```json
{
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again later.",
  "retry_after": 60
}
```

**500 Internal Server Error** - LLM API failure:
```json
{
  "detail": "OpenAI API error: Rate limit exceeded"
}
```

**503 Service Unavailable** - Service health check failed:
```json
{
  "detail": "LLM service unavailable"
}
```

### GET /health

Check API health and availability.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-11T10:30:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "unhealthy",
  "version": "1.0.0",
  "timestamp": "2025-12-11T10:30:00Z"
}
```

### GET /docs

Interactive Swagger UI documentation.

### GET /redoc

Alternative ReDoc documentation interface.

## Usage Examples

### Python

```python
import requests

url = "http://localhost:8000/v1/compare"
payload = {
    "original_text": "The medication dosage is 5mg daily.",
    "generated_text": "The medication dosage is 50mg daily.",
    "sensitivity": "high"
}

response = requests.post(url, json=payload)
result = response.json()

if not result["summary"]["is_safe"]:
    print(f"Warning: Risk score {result['summary']['risk_score']}")
    for change in result["changes"]:
        print(f"- {change['description']} (severity: {change['severity']})")
```

### cURL

```bash
curl -X POST "http://localhost:8000/v1/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "Meeting scheduled for Monday 3pm",
    "generated_text": "Meeting scheduled for Tuesday 3pm",
    "sensitivity": "medium"
  }'
```

### JavaScript (Node.js)

```javascript
const fetch = require('node-fetch');

async function compareTexts() {
  const response = await fetch('http://localhost:8000/v1/compare', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      original_text: "The contract expires on December 31, 2024.",
      generated_text: "The contract expires on December 31, 2025.",
      sensitivity: "high"
    })
  });
  
  const result = await response.json();
  
  if (result.summary.risk_score > 50) {
    console.log('High-risk changes detected!');
    result.changes.forEach(change => {
      console.log(`${change.type}: ${change.description}`);
    });
  }
}

compareTexts();
```

### TypeScript Types

```typescript
enum Sensitivity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high"
}

enum ChangeType {
  FACTUAL = "FACTUAL",
  TONE = "TONE",
  OMISSION = "OMISSION",
  ADDITION = "ADDITION",
  FORMATTING = "FORMATTING"
}

enum Severity {
  INFO = "info",
  WARNING = "warning",
  CRITICAL = "critical"
}

enum SemanticChangeLevel {
  NONE = "NONE",
  MINOR = "MINOR",
  MODERATE = "MODERATE",
  CRITICAL = "CRITICAL",
  FATAL = "FATAL"
}

interface TextSpan {
  text: string;
  start: number;
  end: number;
}

interface ChangeItem {
  id: string;
  type: ChangeType;
  severity: Severity;
  description: string;
  original_span: TextSpan;
  generated_span: TextSpan;
  reasoning: string;
}

interface DiffSummary {
  is_safe: boolean;
  risk_score: number;
  semantic_change_level: SemanticChangeLevel;
}

interface DiffResponse {
  summary: DiffSummary;
  changes: ChangeItem[];
}

interface CompareRequest {
  original_text: string;
  generated_text: string;
  sensitivity?: Sensitivity;
}
```

## Best Practices

### Input Validation

- Text length: API handles up to ~100K characters per request
- Empty texts will return minimal/no changes
- Unicode and special characters are supported

### Error Handling

Always implement retry logic with exponential backoff:

```python
import time

def compare_with_retry(original, generated, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, json={
                "original_text": original,
                "generated_text": generated,
                "sensitivity": "high"
            })
            
            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get('Retry-After', 60))
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### Performance

- **Response time:** Typically 2-5 seconds for standard texts
- **Timeout:** Default 60 seconds
- **Concurrency:** Rate limited per IP, use multiple IPs for higher throughput
- **Caching:** Consider caching results for identical text pairs

### Sensitivity Selection

Choose sensitivity based on use case:

**Use LOW when:**
- Validating AI-generated medical/legal content
- Only critical factual accuracy matters
- Performance is priority (fewer changes = faster analysis)

**Use MEDIUM when:**
- General content validation
- Balanced between thoroughness and performance
- Tone matters but minor formatting doesn't

**Use HIGH when:**
- Complete audit trail needed
- Legal/compliance requirements
- Debugging AI output behavior

## Monitoring and Observability

### Sentry Integration

The API integrates with Sentry for error tracking. Configure via environment:

```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Metrics

Monitor these key metrics:

- Request latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Rate limit hit rate
- LLM API failures
- Token usage

### Logs

Structured JSON logs include:

```json
{
  "timestamp": "2025-12-11T10:30:00Z",
  "level": "INFO",
  "message": "Analysis complete",
  "context": {
    "risk_score": 75,
    "change_level": "CRITICAL",
    "changes_detected": 3,
    "original_len": 150,
    "generated_len": 152
  }
}
```

## Deployment

### Environment Variables

Required:
```bash
OPENAI_API_KEY=sk-...
```

Optional:
```bash
# API Configuration
API_TITLE="ContextDiff API"
API_VERSION="1.0.0"
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_BURST=10

# Monitoring
SENTRY_DSN=https://...
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t contextdiff-api .
docker run -p 8000:8000 --env-file .env contextdiff-api
```

### Production Considerations

1. **Use Redis for rate limiting** - Replace in-memory storage
2. **Add API key authentication** - Implement in middleware
3. **Enable HTTPS** - Use reverse proxy (nginx, Caddy)
4. **Scale horizontally** - Run multiple instances behind load balancer
5. **Database for audit logs** - Store all comparisons for compliance
6. **CDN for static docs** - Serve documentation via CDN

## Support

For issues, questions, or feature requests:
- GitHub Issues: [repository-url]
- Email: support@contextdiff.com
- Documentation: https://docs.contextdiff.com

## Changelog

### v1.0.0 (2025-12-11)
- Initial release
- Core semantic diff analysis
- Rate limiting
- Sentry monitoring
- Comprehensive documentation
