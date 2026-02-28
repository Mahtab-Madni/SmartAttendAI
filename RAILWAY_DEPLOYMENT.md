# SmartAttendAI - Railway Deployment Guide

## Prerequisites

1. **Railway Account**: Create one at [https://railway.app](https://railway.app)
2. **Git Repository**: Push your project to GitHub/GitLab
3. **Railway CLI** (optional): Install from [https://docs.railway.app/](https://docs.railway.app/)

---

## Step 1: Prepare Your Project

### 1.1 Update `.env` File

```bash
cp .env.example .env
```

Fill in your environment variables:

- `TELEGRAM_BOT_TOKEN`: Get from BotFather on Telegram
- `SECRET_KEY`: Generate a secure random key
- Other configuration values as needed

### 1.2 Verify Files Are in Place

Ensure these files exist in your project root:

- `Procfile` ✓
- `Dockerfile` ✓
- `requirements.txt` ✓
- `.env.example` ✓
- `railway.json` ✓

---

## Step 2: Deploy via Railway Dashboard

### Option A: GitHub Integration (Recommended)

1. **Push to GitHub**

   ```bash
   git add .
   git commit -m "Add Railway deployment configuration"
   git push origin main
   ```

2. **Connect Railway to GitHub**
   - Go to [https://railway.app/dashboard](https://railway.app/dashboard)
   - Click "New Project" → "Deploy from GitHub"
   - Authorize Railway and select your repository
   - Select the SmartAttendAI repo

3. **Configure Environment Variables**
   - In Railway dashboard, go to "Variables"
   - Add all variables from your `.env` file:
     ```
     TELEGRAM_BOT_TOKEN=your_token
     SECRET_KEY=your_secret_key
     DATABASE_TYPE=sqlite
     DEBUG=False
     ENVIRONMENT=production
     ```

4. **Deploy**
   - Railway auto-deploys on every GitHub push
   - Or manually trigger deployment from dashboard

### Option B: Using Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Create new project
railway init

# Link to GitHub repository
railway link

# Set environment variables
railway variables

# Deploy
railway up
```

---

## Step 3: Database Setup (Important!)

### For SQLite (Default - Works on Railway)

The app uses SQLite by default. No additional setup needed.

### For PostgreSQL (Recommended for Production)

If you want to use PostgreSQL:

1. **Add PostgreSQL Plugin**
   - In Railway dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will auto-generate `DATABASE_URL`

2. **Update Environment Variable**

   ```
   DATABASE_TYPE=postgresql
   DATABASE_URL=postgresql://user:password@host:port/db
   ```

3. **Update `app.py`** (Optional - if using different DB):
   Connect to PostgreSQL using SQLAlchemy instead of SQLite

---

## Step 4: Configure Memory & Resources

Since SmartAttendAI uses ML models, allocate sufficient resources:

1. **In Railway Dashboard**
   - Go to your deployment settings
   - Set **Memory**: Minimum 2GB (for ML models)
   - Set **CPU**: At least 1 CPU core

2. **Alternative**: Scale resources if you get memory errors
   - Railway allows dynamic scaling based on demand

---

## Step 5: Set Up Persistent Storage (For Face Encodings)

Your app stores face encodings in `config/data/faces/`. You have two options:

### Option A: SQLite in Ephemeral Storage

- Current setup uses SQLite in the container
- Data persists within the deployment but resets on redeploy
- **Good for**: Testing, development

### Option B: Use Railway PostgreSQL (Recommended)

- Use PostgreSQL for permanent data storage
- Update database connection string
- Data survives redeployment

---

## Step 6: Verify Deployment

```bash
# Check deployment status
railway logs

# Test your application
curl https://your-railway-url.railway.app/

# View real-time logs
railway logs -f
```

---

## Step 7: Configure Domain (Optional)

1. **Add Custom Domain**
   - In Railway dashboard → Settings → Domains
   - Add your custom domain (e.g., attendance.yourdomain.com)
   - Configure DNS with Railway's provided CNAME record

2. **HTTPS is Automatic**
   - Railway provides free SSL/TLS certificates

---

## Troubleshooting

### Build Fails: Memory Issues

**Solution**: This is common with ML models

- Reduce model loading in optimization
- Use `python:3.10-slim` (already specified in Dockerfile)
- Increase Railway plan resources

### Port Binding Error

**Solution**: Ensure `$PORT` environment variable is used

- Verify `Procfile` uses `$PORT`
- Railway automatically sets this

### Module Not Found Errors

**Solution**: Ensure all dependencies are in `requirements.txt`

```bash
pip freeze > requirements.txt
```

### Models Not Loading

**Solution**: Update model paths in config

```python
# In config/settings.py
MODELS_DIR = Path("/app/models")  # Absolute path for Railway
```

### Face Encoding Database Issues

**Solution**:

- Use PostgreSQL instead of SQLite for reliability
- Or implement local caching with proper error handling

---

## Environment Variables Reference

| Variable                 | Example                  | Description                       |
| ------------------------ | ------------------------ | --------------------------------- |
| `TELEGRAM_BOT_TOKEN`     | `123456:ABC...`          | Telegram bot token from BotFather |
| `SECRET_KEY`             | `random-secure-key`      | Flask session secret key          |
| `DEBUG`                  | `False`                  | Disable debug mode in production  |
| `ENVIRONMENT`            | `production`             | Environment type                  |
| `DATABASE_TYPE`          | `sqlite` or `postgresql` | Database backend                  |
| `DATABASE_URL`           | `postgresql://...`       | Database connection string        |
| `GEOFENCE_RADIUS_METERS` | `200`                    | Geofencing radius                 |
| `LOG_LEVEL`              | `INFO`                   | Logging level                     |

---

## Performance Tips

1. **Use PostgreSQL** instead of SQLite for better concurrency
2. **Enable caching** for face encodings
3. **Optimize image processing** - resize frames before processing
4. **Use Railway's built-in monitoring** to track performance
5. **Set up alerting** for errors and failures

---

## Logging & Monitoring

1. **View Logs**

   ```bash
   railway logs -f
   ```

2. **Monitor Metrics**
   - CPU usage
   - Memory usage
   - Request count
   - Status codes

3. **Set Alerts**
   - Configure in Railway dashboard
   - Get notified of deployment failures

---

## Deployment Checklist

- [ ] All files pushed to GitHub
- [ ] `.env` variables configured in Railway
- [ ] Database selected (SQLite or PostgreSQL)
- [ ] Memory allocated (2GB minimum)
- [ ] Dockerfile verified
- [ ] Procfile correct
- [ ] requirements.txt up to date
- [ ] Domain configured (optional)
- [ ] Logs checked for errors
- [ ] Telegram bot token verified

---

## Security Best Practices

1. **Never commit `.env`** - use `.env.example`
2. **Use strong `SECRET_KEY`** - at least 32 characters
3. **Enable HTTPS** - Railway does this automatically
4. **Rotate API keys** - regularly change credentials
5. **Monitor logs** - watch for suspicious activity
6. **Use environment-specific configs** - separate dev/prod settings

---

## Next Steps

1. Deploy application
2. Test all features (face recognition, geofencing, etc.)
3. Set up monitoring and alerting
4. Configure backups for face encodings
5. Plan scaling strategy as usage grows

---

## Support & Resources

- **Railway Docs**: https://docs.railway.app/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Project Documentation**: See `DOCUMENTATION.md`

---

**Happy deploying! 🚀**
