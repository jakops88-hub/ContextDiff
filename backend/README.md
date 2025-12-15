# ContextDiff Backend API

**FastAPI + OpenAI Semantic Text Analysis Engine**

Production-ready Python backend for semantic text difference analysis using GPT-4o-mini.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your OPENAI_API_KEY
   ```

3. **Run the server:**
   ```bash
   python main.py
   # or
   uvicorn main:app --reload
   ```

4. **Access API docs:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📁 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration & settings
│   ├── models.py          # Pydantic schemas
│   ├── monitoring.py      # Sentry integration
│   ├── middleware/
│   │   └── rate_limiter.py
│   ├── services/
│   │   ├── cache.py       # In-memory caching (SHA-256, 1hr TTL)
│   │   └── diff_engine.py # Core analysis engine
│   └── utils/
│       ├── prompts.py     # LLM system prompts
│       └── text_processing.py
├── main.py               # FastAPI application
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ |
| `OPENAI_MODEL` | GPT model to use | `gpt-4o-mini` | ❌ |
| `OPENAI_MAX_TOKENS` | Max response tokens | `1500` | ❌ |
| `OPENAI_TEMPERATURE` | Model temperature | `0.0` | ❌ |
| `API_VERSION` | API version | `1.0.0` | ❌ |
| `RATE_LIMIT_REQUESTS` | Requests per minute | `60` | ❌ |
| `SENTRY_DSN` | Sentry error tracking | - | ❌ |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ |

### Model Configuration

The engine uses **gpt-4o-mini** by default for optimal cost/performance:
- **Temperature**: 0.0 (deterministic)
- **Max Tokens**: 1500 (sufficient for change detection)
- **Context Window**: 30 characters before/after spans

## ⚡ Performance Features

- **Chunking**: Splits texts >800 chars for parallel processing
- **Parallel Processing**: `asyncio.gather()` for concurrent chunk analysis
- **Caching**: SHA-256 cache with 1-hour TTL (prevents duplicate API calls)
- **Smart Filtering**: Skips identical chunks (difflib short-circuit)
- **Span Validation**: 3-phase validation with context-aware matching
- **Rate Limiting**: Token bucket algorithm (60 req/min default)

## 🐳 Docker

### Build:
```bash
docker build -t contextdiff-api .
```

### Run:
```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  contextdiff-api
```

### Health Check:
```bash
curl http://localhost:8000/health
```

## 📊 API Performance

- **Small texts (<800 chars)**: ~3-5 seconds
- **Medium texts (800-3000 chars)**: ~8-12 seconds
- **Large texts (>3000 chars)**: ~15-25 seconds

Performance optimized through:
- Parallel chunk processing
- Compressed prompts (30 char context)
- Response caching
- Efficient span validation

## 🔐 Security

- **Rate Limiting**: Token bucket middleware
- **CORS**: Configured for frontend origins
- **Input Sanitization**: Strips sensitive data from logs
- **Type Safety**: Full Pydantic V2 validation
- **Error Handling**: Graceful degradation with proper status codes

## 📈 Monitoring

Optional Sentry integration for error tracking:
```bash
export SENTRY_DSN=https://your-sentry-dsn
```

Logs include:
- Request metadata (sensitivity, text lengths)
- Performance metrics (processing time, chunk count)
- Cache hit rates
- API costs (estimated)

## 🚀 Deployment

### Koyeb (Recommended)
1. Push code to GitHub
2. Create new app on Koyeb
3. Select Docker deployment
4. Set build context: `/backend`
5. Add `OPENAI_API_KEY` env var
6. Deploy

### Railway/Render
1. Connect repository
2. Set root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add `OPENAI_API_KEY` env var

## 🧪 Testing

```bash
# Health check
curl http://localhost:8000/health

# Compare texts
curl -X POST http://localhost:8000/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "The product launches in Q1.",
    "generated_text": "The product might launch in Q1.",
    "sensitivity": "medium"
  }'
```

## 📝 License

MIT

## 🤝 Contributing

See main repository README for contribution guidelines.
