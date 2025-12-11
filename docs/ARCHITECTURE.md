# ContextDiff - Architecture Documentation

## System Architecture

### High-Level Overview

```
┌─────────────┐
│   Client    │
│ Application │
└──────┬──────┘
       │ HTTP/JSON
       ▼
┌─────────────────────────────────────┐
│         FastAPI Application         │
│  ┌───────────────────────────────┐  │
│  │   Rate Limit Middleware       │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │     CORS Middleware           │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │   /v1/compare Endpoint        │  │
│  └───────────┬───────────────────┘  │
│              ▼                       │
│  ┌───────────────────────────────┐  │
│  │      DiffEngine Service       │  │
│  │  - Prompt Construction        │  │
│  │  - LLM API Call               │  │
│  │  - Response Validation        │  │
│  │  - Span Correction            │  │
│  └───────────┬───────────────────┘  │
└──────────────┼─────────────────────┘
               │
               ▼
       ┌──────────────┐
       │  OpenAI API  │
       │  (GPT-4o)    │
       └──────────────┘
```

### Component Breakdown

#### 1. Entry Point (`main.py`)
- FastAPI application initialization
- Middleware configuration
- Route registration
- Lifespan management (startup/shutdown)

#### 2. Middleware Layer

**RateLimitMiddleware** (`app/middleware/rate_limiter.py`)
- Token bucket algorithm
- Per-IP rate limiting
- Configurable limits
- Burst capacity handling
- Automatic cleanup of inactive buckets

**CORSMiddleware** (FastAPI built-in)
- Cross-origin request handling
- Configurable allowed origins
- Credential support

#### 3. API Endpoints (`main.py`)

**POST /v1/compare**
- Primary analysis endpoint
- Input validation via Pydantic
- Error handling and transformation
- Response formatting

**GET /health**
- Health check endpoint
- LLM service availability check
- Version information

#### 4. Core Services

**DiffEngine** (`app/services/diff_engine.py`)
- Main business logic coordinator
- Prompt construction
- OpenAI API interaction
- Response parsing and validation
- Span correction and hallucination removal

**Monitoring** (`app/monitoring.py`)
- Sentry SDK integration
- Error tracking
- Performance monitoring
- Breadcrumb logging
- User context management

#### 5. Data Models (`app/models.py`)

**Request Models:**
- `CompareRequest`: Input validation
- `SensitivityLevel`: Enum for filter levels

**Response Models:**
- `DiffResponse`: Complete analysis result
- `DiffSummary`: High-level overview
- `ChangeItem`: Individual change details
- `TextSpan`: Text location information

**System Models:**
- `HealthResponse`: Health check format

#### 6. Configuration (`app/config.py`)
- Environment variable loading
- Pydantic Settings validation
- Type-safe configuration access
- Default value management

#### 7. Utilities (`app/utils/prompts.py`)
- System prompt templates
- User prompt formatting
- Sensitivity-based prompt adaptation

## Data Flow

### Successful Request Flow

```
1. Client sends POST /v1/compare with JSON body
   ↓
2. Rate limit middleware checks IP bucket
   ↓
3. FastAPI validates request against CompareRequest schema
   ↓
4. DiffEngine.analyze_diff() called
   ↓
5. System and user prompts constructed
   ↓
6. OpenAI API called with JSON mode
   ↓
7. Raw JSON response received
   ↓
8. _validate_and_fix_spans() corrects/removes invalid spans
   ↓
9. _validate_and_build_response() creates Pydantic models
   ↓
10. Response serialized to JSON and returned
```

### Error Handling Flow

```
                  Request
                     ↓
         ┌──────────────────────┐
         │  Rate Limit Check    │
         └──────┬───────────────┘
                │ Exceeded?
                ├─→ Yes → 429 Too Many Requests
                ↓ No
         ┌──────────────────────┐
         │  Pydantic Validation │
         └──────┬───────────────┘
                │ Invalid?
                ├─→ Yes → 422 Unprocessable Entity
                ↓ No
         ┌──────────────────────┐
         │  DiffEngine Analysis │
         └──────┬───────────────┘
                │
        ┌───────┴────────┐
        │                │
   LLMAPIError    LLMResponseError
        │                │
        ↓                ↓
  500 Internal    500 Internal
     Error            Error
        │                │
        └────────┬───────┘
                 ↓
        Logged to Sentry
```

## Algorithm Details

### Rate Limiting - Token Bucket

**Parameters:**
- `capacity`: Maximum tokens (requests_per_minute + burst_size)
- `refill_rate`: tokens_per_second = requests_per_minute / 60
- `tokens`: Current available tokens

**Algorithm:**
```python
def consume(tokens_needed):
    current_time = now()
    elapsed = current_time - last_refill_time
    
    # Refill tokens based on time
    new_tokens = elapsed * refill_rate
    tokens = min(capacity, tokens + new_tokens)
    last_refill_time = current_time
    
    # Try to consume
    if tokens >= tokens_needed:
        tokens -= tokens_needed
        return True  # Success
    else:
        return False  # Rate limited
```

**Benefits:**
- Allows burst traffic within limits
- Smooth token refill over time
- Per-IP isolation
- Memory efficient with periodic cleanup

### Span Validation and Correction

**Problem:** LLMs sometimes return incorrect text span indices or hallucinate text that doesn't exist.

**Solution:** Three-phase validation

**Phase 1: Exact Match Check**
```python
actual = original_text[start:end]
expected = change.original_span.text

if actual != expected:
    # Proceed to Phase 2
```

**Phase 2: Auto-Correction**
```python
found_index = original_text.find(expected_text)

if found_index != -1:
    # Fix indices
    change.original_span.start = found_index
    change.original_span.end = found_index + len(expected_text)
else:
    # Proceed to Phase 3
```

**Phase 3: Hallucination Removal**
```python
if text_not_found:
    # Remove this change entirely
    valid_changes.remove(change)
    log_warning("Hallucinated change removed")
```

**Result:** Clients never receive invalid span indices.

## Scalability Considerations

### Current Limitations

1. **In-Memory Rate Limiting**
   - Issue: Doesn't work across multiple instances
   - Solution: Implement Redis-backed rate limiter

2. **No Request Queue**
   - Issue: All requests hit LLM API directly
   - Solution: Add Celery/RQ for async processing

3. **No Caching**
   - Issue: Identical requests processed multiple times
   - Solution: Add Redis cache with hash-based keys

### Scaling Strategy

**Vertical Scaling (Single Instance):**
- Increase uvicorn workers: `--workers 4`
- Tune OpenAI timeout and concurrency
- Optimize prompt token usage

**Horizontal Scaling (Multiple Instances):**
```
        Load Balancer
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
  API-1    API-2    API-3
    │        │        │
    └────────┼────────┘
             ▼
      Shared Redis
    (Rate Limits + Cache)
```

**Required Changes:**
1. Replace `RateLimitMiddleware` with Redis-backed version
2. Add Redis for distributed caching
3. Implement sticky sessions or stateless design
4. Share Sentry across instances (already stateless)

### Performance Benchmarks

**Expected Performance (gpt-4o-mini):**
- Response time: 2-5 seconds (typical)
- Throughput: ~12 requests/minute per instance (5s avg)
- Token usage: ~500-2000 tokens per request

**Optimization Targets:**
- Cache hit rate: >30%
- P95 latency: <10 seconds
- Error rate: <1%
- Rate limit hit rate: <5%

## Security Considerations

### Current Implementation

**Implemented:**
- Rate limiting per IP
- Input validation (Pydantic)
- CORS configuration
- No PII sent to Sentry
- Secure environment variable handling

**Not Implemented (Production Required):**
- API key authentication
- Request signing
- IP allowlisting
- SQL injection protection (no database yet)
- DDoS protection (use Cloudflare)

### Authentication Pattern (Future)

```python
# middleware/auth.py
async def verify_api_key(request: Request):
    api_key = request.headers.get("Authorization")
    
    if not api_key or not api_key.startswith("Bearer "):
        raise HTTPException(401, "Missing API key")
    
    key = api_key.replace("Bearer ", "")
    
    # Verify against database or cache
    if not is_valid_key(key):
        raise HTTPException(401, "Invalid API key")
    
    # Attach user context
    request.state.user_id = get_user_from_key(key)
```

### Data Privacy

**Current:**
- Text data passed to OpenAI (subject to OpenAI's data policy)
- No persistent storage of user data
- Logs contain request metadata only

**Recommendations:**
- Implement data retention policy
- Allow opt-out of logging
- Anonymize logs after 30 days
- Add GDPR-compliant data deletion endpoint

## Monitoring Strategy

### Key Metrics

**Application Metrics:**
- Request count (by endpoint, status code)
- Response latency (p50, p95, p99)
- Error rate (4xx, 5xx)
- Rate limit hit rate

**Business Metrics:**
- Analyses performed
- Average risk score
- Change type distribution
- Sensitivity level usage

**Infrastructure Metrics:**
- CPU usage
- Memory usage
- Network I/O
- OpenAI API latency

### Sentry Integration

**Automatic Tracking:**
- All unhandled exceptions
- HTTP 500 errors
- Performance transactions (10% sample)
- Request breadcrumbs

**Manual Tracking:**
```python
from app.monitoring import capture_exception, add_breadcrumb

add_breadcrumb(
    "Text comparison started",
    category="api",
    data={"sensitivity": "high"}
)

try:
    result = await analyze()
except Exception as e:
    capture_exception(e, context={
        "text_length": len(text),
        "sensitivity": sensitivity
    })
```

### Alerting Strategy

**Critical Alerts (PagerDuty):**
- Error rate > 5% for 5 minutes
- P95 latency > 30 seconds
- Health check failures
- OpenAI API quota exhausted

**Warning Alerts (Slack):**
- Error rate > 2% for 10 minutes
- Rate limit hit rate > 10%
- Memory usage > 80%

## Testing Strategy

### Unit Tests

**Models:**
```python
def test_compare_request_validation():
    # Valid request
    req = CompareRequest(
        original_text="test",
        generated_text="test2",
        sensitivity="high"
    )
    assert req.sensitivity == SensitivityLevel.HIGH
    
    # Invalid sensitivity
    with pytest.raises(ValidationError):
        CompareRequest(
            original_text="test",
            generated_text="test2",
            sensitivity="invalid"
        )
```

**DiffEngine:**
```python
@pytest.mark.asyncio
async def test_span_validation():
    engine = DiffEngine()
    response_data = {
        "summary": {...},
        "changes": [{
            "original_span": {
                "text": "wrong",
                "start": 0,
                "end": 5
            }
        }]
    }
    
    corrected = engine._validate_and_fix_spans(
        response_data,
        "correct text",
        "generated"
    )
    
    # Should auto-correct or remove
    assert corrected["changes"][0]["original_span"]["start"] == correct_index
```

### Integration Tests

**API Endpoint:**
```python
def test_compare_endpoint(client):
    response = client.post("/v1/compare", json={
        "original_text": "Test",
        "generated_text": "Test modified",
        "sensitivity": "medium"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "changes" in data
```

**Rate Limiting:**
```python
def test_rate_limiting(client):
    # Send requests beyond limit
    for i in range(70):
        response = client.post("/v1/compare", json=valid_request)
        if i < 60:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
```

### Load Testing

```python
# locust_test.py
from locust import HttpUser, task, between

class DiffAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def compare_texts(self):
        self.client.post("/v1/compare", json={
            "original_text": "Sample text",
            "generated_text": "Modified text",
            "sensitivity": "medium"
        })
```

Run: `locust -f locust_test.py --host=http://localhost:8000`

## Deployment Guide

### Local Development

```bash
# Install dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run server
uvicorn main:app --reload
```

### Production Deployment

**Option 1: Docker on Cloud Platform**

```bash
# Build
docker build -t contextdiff-api:v1.0.0 .

# Push to registry
docker tag contextdiff-api:v1.0.0 registry.com/contextdiff-api:v1.0.0
docker push registry.com/contextdiff-api:v1.0.0

# Deploy (example: Railway, Render, Fly.io)
# Configure environment variables via platform UI
```

**Option 2: Kubernetes**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contextdiff-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contextdiff-api
  template:
    metadata:
      labels:
        app: contextdiff-api
    spec:
      containers:
      - name: api
        image: registry.com/contextdiff-api:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

**Option 3: Serverless (AWS Lambda)**

Requires adaptation:
- Use Mangum adapter for AWS Lambda
- Add cold start optimization
- Implement connection pooling
- Consider Lambda pricing for LLM calls

### Infrastructure Requirements

**Minimum:**
- 512MB RAM
- 1 vCPU
- 10GB disk

**Recommended (Production):**
- 2GB RAM
- 2 vCPU
- 20GB disk
- Redis instance for rate limiting

## Future Enhancements

### Short Term
1. API key authentication
2. Redis-backed rate limiting
3. Request/response caching
4. Comprehensive test suite
5. CI/CD pipeline

### Medium Term
1. Async job processing (Celery)
2. Batch comparison endpoint
3. Webhook notifications
4. Custom model fine-tuning
5. Multi-language support

### Long Term
1. On-premise deployment option
2. Plugin system for custom analyzers
3. Machine learning model training on user feedback
4. GraphQL API alternative
5. Real-time streaming analysis

## Troubleshooting

### Common Issues

**Issue: Rate limit too aggressive**
```bash
# Increase in .env
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_BURST=20
```

**Issue: OpenAI timeout**
```bash
# Increase timeout
OPENAI_TIMEOUT=120
```

**Issue: Memory usage growing**
- Check rate limiter bucket cleanup
- Verify no request data is cached unintentionally
- Monitor Sentry for memory leaks

**Issue: Inconsistent span indices**
- Already handled by `_validate_and_fix_spans()`
- Check logs for "Auto-corrected" or "Removed hallucinated" messages
- May indicate prompt engineering needed

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
uvicorn main:app --log-level debug
```

## Conclusion

This architecture provides a solid foundation for a production-ready semantic diff API. Key strengths:

- Clean separation of concerns
- Robust error handling
- Built-in monitoring
- Scalable design
- Comprehensive validation

For production deployment, prioritize:
1. Redis integration for distributed rate limiting
2. API key authentication
3. Comprehensive monitoring dashboard
4. Load testing and optimization
5. Documentation and client SDKs
