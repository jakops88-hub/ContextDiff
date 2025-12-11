# ContextDiff Deployment Guide

## Prerequisites

- Python 3.10 or higher
- OpenAI API key
- Sentry account (optional, for monitoring)
- Redis instance (optional, for distributed rate limiting)

## Local Development

### 1. Clone Repository

```bash
git clone https://github.com/your-org/contextdiff.git
cd contextdiff
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 5. Run Development Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server available at: http://localhost:8000

API documentation: http://localhost:8000/docs

## Production Deployment

### Option 1: Docker

#### Build Image

```bash
docker build -t contextdiff-api:latest .
```

#### Run Container

```bash
docker run -d \
  --name contextdiff-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e SENTRY_DSN=your-sentry-dsn \
  -e RATE_LIMIT_PER_MINUTE=120 \
  contextdiff-api:latest
```

#### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SENTRY_DSN=${SENTRY_DSN}
      - RATE_LIMIT_PER_MINUTE=120
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped
```

Run: `docker-compose up -d`

### Option 2: Railway

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and initialize:
```bash
railway login
railway init
```

3. Add environment variables:
```bash
railway variables set OPENAI_API_KEY=sk-your-key
railway variables set SENTRY_DSN=your-dsn
```

4. Deploy:
```bash
railway up
```

### Option 3: Render

1. Create `render.yaml`:

```yaml
services:
  - type: web
    name: contextdiff-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: OPENAI_API_KEY
        sync: false
      - key: PYTHON_VERSION
        value: 3.11.0
      - key: RATE_LIMIT_PER_MINUTE
        value: 120
```

2. Connect repository to Render
3. Add environment variables in dashboard
4. Deploy

### Option 4: AWS EC2

#### 1. Launch EC2 Instance

- AMI: Ubuntu 22.04 LTS
- Instance type: t3.medium (2 vCPU, 4GB RAM)
- Security group: Allow port 8000 (or 80/443 with reverse proxy)

#### 2. SSH and Setup

```bash
ssh ubuntu@your-ec2-ip

# Install Python
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# Clone repository
git clone https://github.com/your-org/contextdiff.git
cd contextdiff

# Setup virtual environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Configure Systemd Service

Create `/etc/systemd/system/contextdiff.service`:

```ini
[Unit]
Description=ContextDiff API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/contextdiff
Environment="PATH=/home/ubuntu/contextdiff/.venv/bin"
EnvironmentFile=/home/ubuntu/contextdiff/.env
ExecStart=/home/ubuntu/contextdiff/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable contextdiff
sudo systemctl start contextdiff
sudo systemctl status contextdiff
```

#### 4. Setup Nginx Reverse Proxy

Install:
```bash
sudo apt install nginx -y
```

Create `/etc/nginx/sites-available/contextdiff`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and reload:
```bash
sudo ln -s /etc/nginx/sites-available/contextdiff /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Setup SSL with Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

### Option 5: Kubernetes

#### 1. Create Kubernetes Manifests

**deployment.yaml:**
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
        image: your-registry/contextdiff-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: openai-key
        - name: SENTRY_DSN
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: sentry-dsn
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

**service.yaml:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: contextdiff-api
spec:
  selector:
    app: contextdiff-api
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
type: Opaque
stringData:
  openai-key: sk-your-key
  sentry-dsn: your-dsn
```

#### 2. Deploy

```bash
kubectl apply -f secrets.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

#### 3. Check Status

```bash
kubectl get pods
kubectl get services
kubectl logs -f deployment/contextdiff-api
```

## Configuration

### Environment Variables

All configuration via environment variables. See `.env.example` for complete list.

**Critical:**
- `OPENAI_API_KEY` - Required for LLM functionality

**Performance:**
- `OPENAI_MODEL` - Choose model (gpt-4o-mini, gpt-4o)
- `OPENAI_TIMEOUT` - Adjust for slow connections
- `RATE_LIMIT_PER_MINUTE` - Control throughput

**Monitoring:**
- `SENTRY_DSN` - Enable error tracking
- `SENTRY_TRACES_SAMPLE_RATE` - Adjust performance monitoring

### Scaling Configuration

**Single Instance:**
```bash
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

**Multiple Instances:**
- Deploy behind load balancer
- Use Redis for distributed rate limiting (requires code modification)
- Share Sentry configuration

## Monitoring Setup

### Sentry Configuration

1. Create account at https://sentry.io
2. Create new project (Python/FastAPI)
3. Copy DSN from project settings
4. Add to environment:
```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
SENTRY_ENVIRONMENT=production
```

### Metrics Dashboard

Recommended metrics to track:

- Request rate (requests/second)
- Response latency (p50, p95, p99)
- Error rate (percentage)
- Rate limit hits (percentage)
- OpenAI API latency
- OpenAI API errors

Tools:
- Sentry Performance Monitoring
- Prometheus + Grafana
- CloudWatch (AWS)
- Datadog

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Find process
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>
```

**OpenAI API timeout:**
```bash
# Increase timeout
OPENAI_TIMEOUT=120
```

**Memory issues:**
```bash
# Reduce workers
uvicorn main:app --workers 2

# Or increase instance memory
```

**Rate limiting too aggressive:**
```bash
# Increase limits
RATE_LIMIT_PER_MINUTE=120
RATE_LIMIT_BURST=30
```

### Logs

**View logs:**
```bash
# Systemd
sudo journalctl -u contextdiff -f

# Docker
docker logs -f contextdiff-api

# Kubernetes
kubectl logs -f deployment/contextdiff-api
```

**Log levels:**
```bash
# Debug mode
uvicorn main:app --log-level debug
```

## Health Checks

**Endpoint:** `GET /health`

**Successful response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-11T10:30:00Z"
}
```

**Load balancer configuration:**
- Health check path: `/health`
- Expected status code: 200
- Check interval: 10 seconds
- Timeout: 5 seconds
- Unhealthy threshold: 3 failures

## Performance Optimization

### Recommendations

1. **Use connection pooling** for Redis (future)
2. **Enable caching** for identical requests
3. **Tune worker count** based on CPU cores
4. **Use CDN** for static documentation
5. **Implement request queuing** for high load

### Benchmarking

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test throughput
ab -n 100 -c 10 -T 'application/json' \
  -p request.json \
  http://localhost:8000/v1/compare
```

Where `request.json`:
```json
{
  "original_text": "Test text",
  "generated_text": "Modified text",
  "sensitivity": "medium"
}
```

## Security Hardening

### Production Checklist

- [ ] Change `ALLOW_ORIGINS` from `*` to specific domains
- [ ] Implement API key authentication
- [ ] Enable HTTPS (SSL/TLS)
- [ ] Set up firewall rules
- [ ] Regular security updates
- [ ] Enable request logging
- [ ] Implement rate limiting per user (not just IP)
- [ ] Add input sanitization
- [ ] Regular dependency audits (`pip-audit`)

### Firewall Setup (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup environment
cp .env .env.backup

# Backup with timestamp
cp .env .env.$(date +%Y%m%d_%H%M%S)
```

### Database Backup (Future)

When adding database:
```bash
# PostgreSQL
pg_dump contextdiff > backup.sql

# Restore
psql contextdiff < backup.sql
```

## Cost Optimization

### OpenAI API Costs

**gpt-4o-mini pricing (as of Dec 2024):**
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

**Estimated cost per request:**
- Average: ~1000 tokens total
- Cost: ~$0.0004 per request
- 1M requests: ~$400

**Optimization strategies:**
1. Use gpt-4o-mini instead of gpt-4o (10x cheaper)
2. Implement caching for identical requests
3. Optimize prompt length
4. Set appropriate `max_tokens` limit

### Infrastructure Costs

**Minimal deployment:**
- Railway/Render: $7-20/month
- AWS t3.small: ~$15/month
- DigitalOcean Droplet: $6-12/month

**Production deployment:**
- Load balancer: $10-30/month
- 2-3 app instances: $30-90/month
- Redis: $10-30/month
- Monitoring (Sentry): $26-80/month

## Support

For deployment issues:
- Check documentation: `/docs`
- Review logs for errors
- Test health endpoint: `/health`
- Verify environment variables
- Confirm OpenAI API key validity

For production support, contact your DevOps team or create issue in repository.
