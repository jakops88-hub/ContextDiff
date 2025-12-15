# Monorepo Deployment Guide

Complete guide for deploying the ContextDiff monorepo (backend + frontend) to production.

## 🏗️ Architecture

**Deployment Stack:**
```
Backend (Python/FastAPI)  → Koyeb (Docker Container)
Frontend (Next.js)        → Vercel (Serverless)
```

**Communication:**
- Frontend calls backend via `NEXT_PUBLIC_API_URL`
- CORS configured for cross-origin requests
- Backend uses OpenAI GPT-4o-mini API

---

## 🐳 Backend Deployment (Koyeb)

### Prerequisites
- GitHub account with repository
- Koyeb account (free tier available)
- OpenAI API key

### Step-by-Step Guide

#### 1. Verify Dockerfile
```bash
cd backend
cat Dockerfile  # Should exist with proper configuration
```

#### 2. Push to GitHub
```bash
git add .
git commit -m "Prepare backend for Koyeb deployment"
git push origin main
```

#### 3. Create Koyeb App

1. **Sign in** to https://app.koyeb.com
2. **Click** "Create App"
3. **Select** GitHub as source
4. **Authorize** Koyeb to access your repository

#### 4. Configure Build

| Setting | Value |
|---------|-------|
| Repository | `your-username/ContextDiff` |
| Branch | `main` |
| Build method | Docker |
| Dockerfile path | `backend/Dockerfile` |
| Build context | `/backend` |

#### 5. Configure Runtime

| Setting | Value |
|---------|-------|
| Port | `8000` |
| Health check path | `/health` |
| Instance type | Free (512 MB RAM) |
| Region | `fra` (Europe) or `was` (US East) |

#### 6. Add Environment Variables

**Required:**
```
OPENAI_API_KEY=sk-your-actual-api-key
```

**Optional:**
```
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=1500
OPENAI_TEMPERATURE=0.0
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=60
```

#### 7. Deploy

1. Click **"Deploy"**
2. Wait 2-5 minutes for build completion
3. Note your public URL: `https://your-app-name.koyeb.app`

#### 8. Verify Deployment

```bash
# Health check
curl https://your-app-name.koyeb.app/health

# Expected response:
{"status":"healthy","version":"1.0.0"}

# Test API
curl -X POST https://your-app-name.koyeb.app/v1/compare \
  -H "Content-Type: application/json" \
  -d '{
    "original_text": "Test text",
    "generated_text": "Modified text",
    "sensitivity": "medium"
  }'
```

---

## ☁️ Frontend Deployment (Vercel)

### Prerequisites
- Vercel account (free tier available)
- Backend deployed and URL obtained

### Method 1: CLI Deployment (Recommended)

#### 1. Install Vercel CLI
```bash
npm install -g vercel
```

#### 2. Login to Vercel
```bash
vercel login
```

#### 3. Deploy
```bash
cd frontend
vercel
```

**Follow prompts:**
- Set up and deploy? → **Yes**
- Which scope? → **Your account**
- Link to existing project? → **No**
- Project name? → **contextdiff-playground**
- Directory? → **./** (already in frontend/)
- Override settings? → **No**

#### 4. Add Environment Variable
```bash
vercel env add NEXT_PUBLIC_API_URL production
# Enter: https://your-app-name.koyeb.app
```

#### 5. Redeploy with Environment Variable
```bash
vercel --prod
```

### Method 2: Dashboard Deployment

#### 1. Import Project

1. Go to https://vercel.com/new
2. Click **"Import Git Repository"**
3. Select **your ContextDiff repository**
4. Click **"Import"**

#### 2. Configure Project

**Framework Settings:**
- Framework Preset: **Next.js** (auto-detected)
- Root Directory: **frontend**
- Build Command: `npm run build` (auto-detected)
- Output Directory: `.next` (auto-detected)
- Install Command: `npm install` (auto-detected)

**Environment Variables:**
- Name: `NEXT_PUBLIC_API_URL`
- Value: `https://your-app-name.koyeb.app`
- Environment: **Production, Preview, Development**

#### 3. Deploy

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. Note your URL: `https://contextdiff-playground.vercel.app`

#### 4. Verify Deployment

1. **Open** `https://contextdiff-playground.vercel.app` in browser
2. **Test functionality:**
   - Enter sample texts
   - Select sensitivity
   - Click "Analyze"
   - Verify results display
   - Test inspector panel
   - Try copy/export buttons

---

## 🔧 Environment Variables Reference

### Backend (Koyeb)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key | - | ✅ Yes |
| `OPENAI_MODEL` | GPT model | `gpt-4o-mini` | ❌ No |
| `OPENAI_MAX_TOKENS` | Max response tokens | `1500` | ❌ No |
| `OPENAI_TEMPERATURE` | Model temperature | `0.0` | ❌ No |
| `API_VERSION` | API version | `1.0.0` | ❌ No |
| `RATE_LIMIT_REQUESTS` | Requests per minute | `60` | ❌ No |
| `SENTRY_DSN` | Error tracking | - | ❌ No |
| `LOG_LEVEL` | Logging level | `INFO` | ❌ No |

### Frontend (Vercel)

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | ✅ Yes |

**Important:** `NEXT_PUBLIC_API_URL` should:
- Include protocol: `https://`
- NOT have trailing slash: ❌ `https://api.example.com/`
- Correct: ✅ `https://api.example.com`

---

## 🔒 CORS Configuration

The backend must allow requests from your frontend domain.

**Update `backend/main.py`:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://contextdiff-playground.vercel.app",  # Production
        "http://localhost:3000",                      # Local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**For multiple Vercel preview deployments:**
```python
allow_origins=["https://*.vercel.app"]  # Wildcard support
```

---

## 📊 Monitoring & Logs

### Backend Monitoring (Koyeb)

**Access logs:**
1. Go to Koyeb dashboard
2. Select your app
3. Click **"Logs"** tab

**View metrics:**
1. Click **"Metrics"** tab
2. Monitor:
   - CPU usage
   - Memory usage
   - Request rate
   - Response time

### Frontend Monitoring (Vercel)

**Access logs:**
```bash
vercel logs contextdiff-playground
```

**Analytics:**
1. Go to Vercel dashboard
2. Select project
3. Click **"Analytics"** tab
4. View:
   - Page views
   - Load time
   - Web Vitals

---

## 🚨 Troubleshooting

### Backend Issues

**Problem: Deployment fails**
```bash
# Check build logs in Koyeb dashboard
# Common causes:
- Missing Dockerfile
- Incorrect build context path
- Syntax errors in code
```

**Solution:**
1. Verify `backend/Dockerfile` exists
2. Check build context is `/backend`
3. Test Docker build locally:
   ```bash
   cd backend
   docker build -t test .
   ```

**Problem: Health check fails**
```bash
# Check environment variables
# Verify OPENAI_API_KEY is set
```

**Solution:**
1. Go to Koyeb dashboard
2. Select app → Settings → Environment variables
3. Add/verify `OPENAI_API_KEY`
4. Redeploy

**Problem: CORS errors**
```
Access to fetch at 'https://backend.koyeb.app' from origin 'https://frontend.vercel.app' 
has been blocked by CORS policy
```

**Solution:**
1. Add frontend URL to `allow_origins` in `main.py`
2. Commit and push to trigger redeploy

### Frontend Issues

**Problem: API calls fail (404)**
```javascript
// Check browser console
// Error: Failed to fetch
```

**Solution:**
1. Verify `NEXT_PUBLIC_API_URL` in Vercel dashboard
2. Ensure no trailing slash
3. Test backend URL directly:
   ```bash
   curl https://your-backend.koyeb.app/health
   ```

**Problem: Environment variable not working**
```javascript
// NEXT_PUBLIC_API_URL is undefined
```

**Solution:**
1. Environment variables starting with `NEXT_PUBLIC_` are exposed to browser
2. Must be set in Vercel dashboard
3. Redeploy after adding env vars:
   ```bash
   vercel --prod
   ```

---

## 💰 Cost Estimation

### Free Tier Usage

**Koyeb (Backend):**
- ✅ 1 free web service
- ✅ 512 MB RAM, 0.1 vCPU
- ⚠️ Sleeps after 30min inactivity
- 💡 Use keep-alive pings for production

**Vercel (Frontend):**
- ✅ Unlimited deployments
- ✅ 100 GB bandwidth/month
- ✅ Serverless functions
- ✅ Automatic HTTPS

**OpenAI API:**
- Model: gpt-4o-mini
- Cost: ~$0.15 per 1M tokens
- Avg request: ~$0.002-0.005
- 1000 requests ≈ $2-5

**Total monthly cost (low usage):**
- Backend: $0 (free tier)
- Frontend: $0 (free tier)
- OpenAI: ~$10-50 (usage-based)

---

## 🔄 CI/CD Auto-Deploy

Both platforms support automatic deployment on git push.

**How it works:**
1. Push code to `main` branch
2. **Koyeb** detects changes in `/backend` → Rebuilds Docker image
3. **Vercel** detects changes in `/frontend` → Rebuilds Next.js app
4. Both deploy automatically

**To disable:**
- Koyeb: Pause auto-deploy in settings
- Vercel: Remove GitHub integration

---

## ✅ Deployment Checklist

### Pre-Deployment
- [ ] Backend tests pass locally
- [ ] Frontend builds successfully
- [ ] Environment variables documented
- [ ] CORS configured correctly
- [ ] API endpoints tested

### Backend Deployment
- [ ] Dockerfile verified
- [ ] Pushed to GitHub
- [ ] Koyeb app created
- [ ] Environment variables set
- [ ] Deployed successfully
- [ ] Health check passes
- [ ] API endpoints accessible

### Frontend Deployment
- [ ] Backend URL obtained
- [ ] Vercel project created
- [ ] Root directory set to `frontend`
- [ ] Environment variable added
- [ ] Deployed successfully
- [ ] Site loads correctly
- [ ] API calls work

### Post-Deployment
- [ ] End-to-end test completed
- [ ] Monitoring dashboards configured
- [ ] Error tracking setup (optional)
- [ ] Documentation updated with URLs
- [ ] Team notified

---

## 📚 Next Steps

1. **Custom Domains**
   - Koyeb: Add custom domain in settings
   - Vercel: Add custom domain in project settings

2. **Enhanced Monitoring**
   - Set up Sentry for error tracking
   - Configure uptime monitoring (UptimeRobot, etc.)

3. **Performance Optimization**
   - Enable Redis caching for backend
   - Configure CDN for frontend assets

4. **Security Hardening**
   - Add API authentication
   - Implement rate limiting per user
   - Set up WAF rules

5. **Scaling**
   - Upgrade Koyeb plan for no sleep mode
   - Add load balancing if needed
   - Consider serverless functions for backend

---

## 🆘 Support Resources

- **Koyeb Docs**: https://www.koyeb.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **OpenAI Status**: https://status.openai.com
- **Project Issues**: GitHub repository issues tab

---

**Deployment Complete! 🎉**

Your ContextDiff platform should now be live:
- Backend: `https://your-app-name.koyeb.app`
- Frontend: `https://contextdiff-playground.vercel.app`
