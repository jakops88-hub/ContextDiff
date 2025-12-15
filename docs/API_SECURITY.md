# API Security Configuration

## Overview

The ContextDiff API now includes security middleware to protect endpoints for RapidAPI deployment while allowing trusted frontend access.

## Authentication Methods

The API supports **two authentication methods** (either one grants access):

### 1. API Secret Header (RapidAPI)
- **Header**: `X-API-SECRET`
- **Value**: Matches `API_SECRET` environment variable
- **Use case**: RapidAPI marketplace authentication

### 2. Trusted Origin (Your Frontend)
- **Header**: `Origin` or `Referer`
- **Value**: Matches domains in `ALLOW_ORIGINS`
- **Use case**: Your Vercel frontend calling the API

## Configuration

### Backend Environment Variables

Add to `backend/.env` (or Koyeb environment):

```bash
# Generate a secure random secret:
# openssl rand -hex 32
API_SECRET=your_secure_random_secret_here

# Configure allowed origins (comma-separated)
ALLOW_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

### RapidAPI Configuration

When listing on RapidAPI:

1. **Set API Secret** in Koyeb:
   ```bash
   API_SECRET=your_secure_random_secret_here
   ```

2. **Configure RapidAPI** to send header:
   - Header Name: `X-API-SECRET`
   - Header Value: `your_secure_random_secret_here`

3. **Test endpoint**:
   ```bash
   curl -X POST https://your-api.koyeb.app/v1/compare \
     -H "Content-Type: application/json" \
     -H "X-API-SECRET: your_secure_random_secret_here" \
     -d '{
       "original_text": "Test",
       "generated_text": "Test modified",
       "sensitivity": "medium"
     }'
   ```

## Security Logic

```
IF X-API-SECRET header matches API_SECRET:
  ✅ ALLOW ACCESS
ELSE IF Origin matches ALLOW_ORIGINS:
  ✅ ALLOW ACCESS
ELSE:
  ❌ 403 FORBIDDEN
```

## Local Development

For local development, you can:

1. **Disable security** (leave `API_SECRET` empty):
   ```bash
   # No API_SECRET in .env
   ```

2. **Use wildcard origins**:
   ```bash
   ALLOW_ORIGINS=*
   ```

## Frontend Configuration

Your Vercel frontend needs no changes! It will authenticate via the `Origin` header automatically.

Just ensure `ALLOW_ORIGINS` includes your Vercel domain:

```bash
ALLOW_ORIGINS=https://contextdiff-playground.vercel.app
```

## Error Responses

### 403 Forbidden

```json
{
  "detail": "Access denied. Valid X-API-SECRET header or trusted origin required."
}
```

**Causes:**
- Missing or invalid `X-API-SECRET` header
- Request origin not in `ALLOW_ORIGINS`
- Both authentication methods failed

**Solution:**
- Check `X-API-SECRET` header value
- Verify `ALLOW_ORIGINS` includes your domain
- Check Koyeb logs for detailed error info

## Testing

### Test with API Secret

```bash
curl -X POST https://your-api.koyeb.app/v1/compare \
  -H "Content-Type: application/json" \
  -H "X-API-SECRET: your_secret_here" \
  -d '{"original_text":"A","generated_text":"B","sensitivity":"medium"}'
```

### Test with Origin (Frontend)

```bash
curl -X POST https://your-api.koyeb.app/v1/compare \
  -H "Content-Type: application/json" \
  -H "Origin: https://contextdiff-playground.vercel.app" \
  -d '{"original_text":"A","generated_text":"B","sensitivity":"medium"}'
```

### Test Failure (No Auth)

```bash
curl -X POST https://your-api.koyeb.app/v1/compare \
  -H "Content-Type: application/json" \
  -d '{"original_text":"A","generated_text":"B","sensitivity":"medium"}'

# Expected: 403 Forbidden
```

## Monitoring

Check Koyeb logs for authentication events:

```
Access granted via X-API-SECRET header
Access granted via allowed origin: https://your-app.vercel.app
Access denied - No valid authentication. API Secret: Missing, Origin: https://unknown.com
```

## Security Best Practices

1. **Generate strong secrets**:
   ```bash
   openssl rand -hex 32
   ```

2. **Never commit secrets** to git (use `.env`, not `.env.example`)

3. **Rotate secrets periodically** (update Koyeb + RapidAPI)

4. **Use HTTPS only** (Koyeb and Vercel provide this by default)

5. **Monitor logs** for unauthorized access attempts

6. **Limit ALLOW_ORIGINS** to specific domains (avoid `*` in production)

## Deployment Checklist

- [ ] Generate secure `API_SECRET`
- [ ] Add `API_SECRET` to Koyeb environment
- [ ] Configure `ALLOW_ORIGINS` with Vercel domain
- [ ] Push backend changes to GitHub
- [ ] Verify Koyeb auto-deploys
- [ ] Test with RapidAPI credentials
- [ ] Test with frontend (Vercel)
- [ ] Monitor logs for auth events
- [ ] Update RapidAPI documentation

## Troubleshooting

### Frontend can't call API

**Problem**: 403 Forbidden from Vercel frontend

**Solution**:
1. Check `ALLOW_ORIGINS` includes exact Vercel URL
2. Verify CORS is configured correctly
3. Check browser console for CORS errors

### RapidAPI integration fails

**Problem**: 403 Forbidden from RapidAPI

**Solution**:
1. Verify `X-API-SECRET` header is being sent
2. Check secret matches Koyeb environment variable
3. Test with curl first to isolate issue

### Security disabled in production

**Problem**: API is open without authentication

**Solution**:
1. Set `API_SECRET` in Koyeb (non-empty value)
2. Redeploy or restart service
3. Test authentication is enforced

---

**Security implemented! 🔒** Your API is now protected for RapidAPI launch while maintaining seamless access for your Vercel frontend.
