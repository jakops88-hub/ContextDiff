# Monorepo Quick Reference

Quick reference guide for working with the ContextDiff monorepo.

## 📁 Directory Structure

```
ContextDiff/
├── backend/              # Python FastAPI backend
│   ├── app/
│   │   ├── middleware/   # Rate limiting
│   │   ├── services/     # Core logic (diff_engine, cache)
│   │   └── utils/        # Helpers (prompts, text processing)
│   ├── main.py           # FastAPI app entry point
│   ├── requirements.txt  # Python dependencies
│   ├── Dockerfile        # Docker config for Koyeb
│   ├── .dockerignore
│   ├── .env              # Local environment (not in git)
│   └── .env.example      # Environment template
│
├── frontend/             # Next.js playground
│   ├── app/              # Next.js App Router
│   │   ├── page.tsx      # Main playground page
│   │   └── layout.tsx
│   ├── components/       # React components
│   │   ├── DiffViewer.tsx         # 3-column diff view
│   │   ├── ChangeDetailCard.tsx   # Inspector panel
│   │   ├── ResultsSummary.tsx     # Enterprise dashboard
│   │   └── AnalysisProgress.tsx   # Progress bar
│   ├── lib/              # API client and utilities
│   ├── hooks/            # React hooks
│   ├── package.json
│   ├── next.config.mjs
│   └── .env.local        # Frontend environment (not in git)
│
├── docs/                 # Documentation
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── MONOREPO_DEPLOYMENT.md
│   └── PERFORMANCE.md
│
├── .git/                 # Git repository
├── .gitignore            # Git ignore (root level)
└── README.md             # Main documentation
```

## 🚀 Quick Start Commands

### Backend Development

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your OPENAI_API_KEY

# Run server
python main.py
# or
uvicorn main:app --reload

# API docs: http://localhost:8000/docs
```

### Frontend Development

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.local.example .env.local
# Edit .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000

# Run dev server
npm run dev

# Open: http://localhost:3000
```

## 🐳 Docker Commands

### Backend

```bash
# Build image
cd backend
docker build -t contextdiff-api .

# Run container
docker run -p 8000:8000 -e OPENAI_API_KEY=your-key contextdiff-api

# Test
curl http://localhost:8000/health
```

## 📦 Deployment

### Backend → Koyeb

```bash
# 1. Push to GitHub
git add backend/
git commit -m "Update backend"
git push origin main

# 2. Koyeb auto-deploys (if configured)
# Or manually trigger from dashboard
```

### Frontend → Vercel

```bash
# Method 1: CLI
cd frontend
vercel --prod

# Method 2: Git push (auto-deploy)
git add frontend/
git commit -m "Update frontend"
git push origin main
```

## 🔧 Common Tasks

### Update Dependencies

**Backend:**
```bash
cd backend
pip install --upgrade package-name
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
npm update package-name
# or
npm install package-name@latest
```

### Add New Route (Backend)

1. Edit `backend/main.py`:
   ```python
   @app.get("/v1/new-endpoint")
   async def new_endpoint():
       return {"message": "Hello"}
   ```

2. Test locally:
   ```bash
   curl http://localhost:8000/v1/new-endpoint
   ```

3. Commit and deploy:
   ```bash
   git add backend/main.py
   git commit -m "Add new endpoint"
   git push
   ```

### Add New Component (Frontend)

1. Create component:
   ```bash
   cd frontend/components
   touch NewComponent.tsx
   ```

2. Implement component:
   ```typescript
   export function NewComponent() {
     return <div>Hello</div>;
   }
   ```

3. Import in page:
   ```typescript
   import { NewComponent } from '@/components/NewComponent';
   ```

### Update Environment Variables

**Backend (Koyeb):**
1. Go to Koyeb dashboard
2. Select app → Settings → Environment
3. Add/update variables
4. Redeploy

**Frontend (Vercel):**
1. Go to Vercel dashboard
2. Select project → Settings → Environment Variables
3. Add/update variables
4. Redeploy

## 🧪 Testing

### Backend

```bash
cd backend

# Health check
curl http://localhost:8000/health

# Compare texts
curl -X POST http://localhost:8000/v1/compare \
  -H "Content-Type: application/json" \
  -d @test-payload.json
```

### Frontend

```bash
cd frontend

# Build test
npm run build

# Type check
npm run lint

# Manual test
npm run dev
# Open http://localhost:3000 and test UI
```

## 📊 Monitoring

### Backend Logs (Koyeb)

```bash
# Via dashboard: Logs tab
# Via CLI: koyeb logs your-app-name
```

### Frontend Logs (Vercel)

```bash
# Via CLI
vercel logs contextdiff-playground

# Via dashboard: Deployments → Select → Logs
```

### API Health

```bash
# Backend
curl https://your-app.koyeb.app/health

# Frontend
curl https://your-app.vercel.app
```

## 🐛 Debugging

### Backend Not Starting

1. **Check environment:**
   ```bash
   cd backend
   cat .env | grep OPENAI_API_KEY
   ```

2. **Test imports:**
   ```bash
   python -c "import fastapi; print('OK')"
   ```

3. **Check logs:**
   ```bash
   python main.py
   # Read error messages
   ```

### Frontend Not Building

1. **Check Node version:**
   ```bash
   node --version  # Should be 18+
   ```

2. **Clear cache:**
   ```bash
   cd frontend
   rm -rf .next node_modules
   npm install
   npm run build
   ```

3. **Check TypeScript:**
   ```bash
   npm run lint
   ```

### API Calls Failing

1. **Check CORS:**
   - Verify frontend URL in `backend/main.py` CORS config
   - Check browser console for CORS errors

2. **Check environment variables:**
   - Backend: `OPENAI_API_KEY` set in Koyeb
   - Frontend: `NEXT_PUBLIC_API_URL` set in Vercel

3. **Test backend directly:**
   ```bash
   curl -X POST https://your-backend.koyeb.app/v1/compare \
     -H "Content-Type: application/json" \
     -d '{"original_text":"test","generated_text":"test2","sensitivity":"medium"}'
   ```

## 📝 Git Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes in backend or frontend
cd backend  # or cd frontend
# ... make changes ...

# Commit changes
git add .
git commit -m "feat: Add new feature"

# Push branch
git push origin feature/new-feature

# Create PR on GitHub
```

### Hotfix

```bash
# Create hotfix branch
git checkout -b hotfix/critical-bug

# Fix bug
# ... make changes ...

# Commit and push
git add .
git commit -m "fix: Critical bug fix"
git push origin hotfix/critical-bug

# Merge to main ASAP
```

## 🔐 Security

### Environment Variables

**Never commit:**
- `.env` (backend)
- `.env.local` (frontend)
- API keys
- Secrets

**Always use:**
- `.env.example` templates
- Platform-specific env vars (Koyeb, Vercel)
- Git-ignored local configs

### CORS

**Update `backend/main.py` when deploying:**
```python
allow_origins=[
    "https://your-production-domain.com",
    "http://localhost:3000",  # Dev only
]
```

## 📚 Documentation

- **API Docs**: http://localhost:8000/docs (Swagger)
- **Architecture**: `docs/ARCHITECTURE.md`
- **Deployment**: `docs/MONOREPO_DEPLOYMENT.md`
- **Performance**: `docs/PERFORMANCE.md`

## 🆘 Getting Help

1. **Check logs** (Koyeb/Vercel dashboards)
2. **Read error messages** carefully
3. **Test components** in isolation
4. **Check documentation** in `/docs`
5. **GitHub Issues** for bug reports

---

## 🎯 Cheat Sheet

| Task | Command |
|------|---------|
| Start backend | `cd backend && python main.py` |
| Start frontend | `cd frontend && npm run dev` |
| Build backend Docker | `cd backend && docker build -t api .` |
| Deploy frontend | `cd frontend && vercel --prod` |
| Check backend health | `curl http://localhost:8000/health` |
| View backend logs | Koyeb dashboard → Logs |
| View frontend logs | `vercel logs` or Vercel dashboard |
| Update backend deps | `cd backend && pip freeze > requirements.txt` |
| Update frontend deps | `cd frontend && npm update` |
| Test API endpoint | `curl -X POST http://localhost:8000/v1/compare -H "Content-Type: application/json" -d '...'` |

---

**Quick Links:**
- [Main README](../README.md)
- [Deployment Guide](./MONOREPO_DEPLOYMENT.md)
- [Backend README](../backend/README.md)
- [Frontend README](../frontend/README.md)
