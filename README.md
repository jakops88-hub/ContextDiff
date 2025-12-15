# ContextDiff - Semantic Text Analysis Platform

**AI-Powered Semantic Text Difference Analysis**

A production-ready monorepo featuring a FastAPI backend and Next.js playground frontend that compares texts for semantic differences using LLM-powered analysis. Goes beyond simple string comparison to detect changes in meaning, tone, facts, and intent.

## 📁 Monorepo Structure

```
ContextDiff/
├── backend/          # FastAPI Python backend
│   ├── app/          # Application modules
│   ├── main.py       # API entry point
│   ├── requirements.txt
│   ├── Dockerfile    # Production Docker image
│   └── .env.example
├── frontend/         # Next.js playground (moved from /playground)
│   ├── app/          # Next.js App Router pages
│   ├── components/   # React components
│   ├── lib/          # API clients and utilities
│   ├── package.json
│   └── next.config.mjs
└── docs/            # Documentation
```

## 🚀 Features

### Backend API
- **Semantic Analysis**: Detect factual changes, tone shifts, omissions, and additions
- **Configurable Sensitivity**: Low, Medium, or High analysis modes
- **Risk Scoring**: 0-100 risk assessment with safety determination
- **Detailed Change Detection**: Precise character-level spans with reasoning
- **Performance Optimized**: Chunking (800 char), parallel processing, caching (1hr TTL)
- **Production Ready**: Strict typing, robust error handling, async operations
- **OpenAPI Documentation**: Auto-generated interactive API docs at `/docs`

### Frontend Playground
- **Interactive UI**: Modern Next.js 14 with Tailwind CSS and Shadcn UI
- **Real-time Analysis**: Progress tracking with live streaming effects
- **Context-Aware Highlighting**: 3-strategy matching with overlap detection
- **Inspector Panel**: Click-to-inspect detailed change analysis
- **Enterprise Features**: Copy JSON, Export MD, confidence badges, severity breakdown
- **Responsive Layout**: Dynamic 4-4-4 grid with toast notifications

## 📋 Requirements

- **Backend**: Python 3.11+, OpenAI API key
- **Frontend**: Node.js 18+, npm/pnpm
- **Deployment**: Docker (Koyeb), Vercel

## 🛠️ Backend Setup

1. **Navigate to backend:**
   ```powershell
   cd c:\Dev\ContextDiff\backend
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```powershell
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

## 🚀 Running Backend Locally

**Start the FastAPI server:**
```powershell
cd backend
python main.py
```

Or using uvicorn directly:
```powershell
uvicorn main:app --reload
```

The API will be available at:
- **API Endpoint**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎨 Frontend Setup

1. **Navigate to frontend:**
   ```powershell
   cd c:\Dev\ContextDiff\frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.local.example .env.local
   ```
   Edit `.env.local`:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## 🚀 Running Frontend Locally

**Start the Next.js development server:**
```bash
npm run dev
# or
pnpm dev
```

The playground will be available at: **http://localhost:3000**

## 🐳 Docker Deployment (Backend)

### Build the Docker image:
```bash
cd backend
docker build -t contextdiff-api .
```

### Run the container:
```bash
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key contextdiff-api
```

### Deploy to Koyeb:
1. Push backend code to GitHub
2. Create new app on Koyeb
3. Connect GitHub repository
4. Set Docker build context to `/backend`
5. Add environment variable: `OPENAI_API_KEY`
6. Deploy

## ☁️ Vercel Deployment (Frontend)

### Deploy frontend to Vercel:
```bash
cd frontend
vercel
```

Or via Vercel dashboard:
1. Import repository
2. Set root directory to `frontend`
3. Framework preset: Next.js
4. Add environment variable: `NEXT_PUBLIC_API_URL`
5. Deploy

## 📖 API Usage

### Compare Texts

**Endpoint:** `POST /v1/compare`

**Request Body:**
```json
{
  "original_text": "The product will be available in Q1 2024.",
  "generated_text": "The product might be available in early 2024.",
  "sensitivity": "medium"
}
```

**Response:**
```json
{
  "summary": {
    "is_safe": false,
    "risk_score": 45,
    "semantic_change_level": "MODERATE"
  },
  "changes": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "type": "FACTUAL",
      "severity": "warning",
      "description": "Certainty level changed from definite to uncertain",
      "original_span": {
        "text": "will be available",
        "start": 12,
        "end": 28
      },
      "generated_span": {
        "text": "might be available",
        "start": 12,
        "end": 30
      },
      "reasoning": "The modal verb changed from 'will' (definite) to 'might' (uncertain), weakening the commitment."
    }
  ]
}
```

### Sensitivity Levels

- **`low`**: Only flag critical issues (factual errors, major contradictions)
- **`medium`**: Balanced analysis (default, recommended for most cases)
- **`high`**: Maximum scrutiny (catch all semantic variations)

### Change Types

- **`FACTUAL`**: Changes to facts, data, claims, or certainty levels
- **`TONE`**: Changes in sentiment, formality, or emotional coloring
- **`OMISSION`**: Missing information from original
- **`ADDITION`**: New information in generated text
- **`FORMATTING`**: Structural changes affecting interpretation

### Severity Levels

- **`info`**: Minor change with negligible impact
- **`warning`**: Notable change that might matter in some contexts
- **`critical`**: Significant change that alters meaning

## 🏗️ Project Structure

```
contextdiff/
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
├── main.py               # FastAPI application entry point
└── app/
    ├── config.py         # Configuration management
    ├── models.py         # Pydantic data models
    ├── services/
    │   └── diff_engine.py # Core LLM analysis engine
    └── utils/
        └── prompts.py    # System prompts for LLM
```

## 🧪 Testing with cURL

```powershell
curl -X POST "http://localhost:8000/v1/compare" `
  -H "Content-Type: application/json" `
  -d '{
    "original_text": "The meeting is scheduled for 3 PM.",
    "generated_text": "The meeting might be around 3 PM.",
    "sensitivity": "medium"
  }'
```

## 🔧 Configuration

All configuration is managed through environment variables in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | Model to use | `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | Response temperature | `0.1` |
| `OPENAI_MAX_TOKENS` | Max response tokens | `4000` |
| `OPENAI_TIMEOUT` | API timeout (seconds) | `60` |

## 🛡️ Error Handling

The API includes comprehensive error handling:

- **400**: Invalid request parameters
- **500**: Internal server error
- **502**: LLM API error
- **503**: Service unavailable (rate limit)
- **504**: Gateway timeout

All errors return structured JSON responses with error type and message.

## 📊 Response Structure

### Summary Fields

- **`is_safe`**: Boolean indicating if generated text is safe to use
- **`risk_score`**: Integer 0-100 indicating overall risk level
- **`semantic_change_level`**: Categorical assessment (NONE, MINOR, MODERATE, CRITICAL, FATAL)

### Change Item Fields

- **`id`**: Unique UUID for the change
- **`type`**: Category of change (FACTUAL, TONE, OMISSION, ADDITION, FORMATTING)
- **`severity`**: Impact level (info, warning, critical)
- **`description`**: Brief explanation
- **`original_span`**: Location and text in original
- **`generated_span`**: Location and text in generated
- **`reasoning`**: Detailed explanation of the classification

## 🎯 Use Cases

- **Content Verification**: Ensure AI-generated content preserves original meaning
- **Translation QA**: Verify translations maintain semantic accuracy
- **Summarization Review**: Check if summaries capture key information
- **Legal/Medical**: High-stakes content validation with `high` sensitivity
- **Marketing Copy**: Verify brand voice consistency

## 🔐 Security Notes

- Never commit `.env` file with actual API keys
- Use proper CORS configuration in production
- Consider rate limiting for public deployments
- Monitor OpenAI API usage and costs

## 📝 License

MIT License - Feel free to use in your projects!

## 🤝 Contributing

This is an MVP. Potential enhancements:
- Support for multiple LLM providers
- Batch processing endpoint
- Caching layer for repeated comparisons
- WebSocket support for streaming analysis
- PDF/document comparison support

---

**Built with ❤️ using FastAPI and OpenAI**
