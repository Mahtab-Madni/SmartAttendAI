# Railway Deployment Guide for SmartAttendAI

## 📋 Prerequisites

- GitHub account with your SmartAttendAI repository
- Railway account (https://railway.app)
- Telegram Bot Token (from BotFather @BotFather on Telegram)
- Models files already in `models/` directory

---

## 🚀 Deployment Steps

### Step 1: Prepare Environment Variables

Create a `.env` file from the template:

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
# CRITICAL - Generate a strong SECRET_KEY
SECRET_KEY=<generate-with-python>

# Your Telegram bot token (get from BotFather)
TELEGRAM_BOT_TOKEN=<your-bot-token>

# For production
ENVIRONMENT=production
DEBUG=False
DATABASE_TYPE=postgresql

# Leave DATABASE_URL blank for now - Railway will set this
DATABASE_URL=
```

**Generate secure SECRET_KEY:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 2: Commit Code to GitHub

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 3: Deploy on Railway Dashboard

1. Go to https://railway.app/dashboard
2. Click **"New Project"** → **"Deploy from GitHub"**  
3. Authorize Railway to access GitHub
4. Select your **SmartAttendAI** repository
5. Select **main** branch
6. Click **"Deploy"**

Railway will automatically:
- Build the Docker image
- Install dependencies from `requirements.txt`
- Start the application using `run.py`

### Step 4: Configure Environment Variables

**In Railway Dashboard:**

1. Click on your **SmartAttendAI** project
2. Go to the **Variables** section
3. Add all variables from your `.env` file:

```
ENVIRONMENT=production
DEBUG=False
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
SECRET_KEY=<your-secure-key>
DATABASE_TYPE=postgresql
TELEGRAM_BOT_TOKEN=<your-bot-token>
TELEGRAM_ENABLED=True
GEOFENCE_RADIUS_METERS=200
GPS_ACCURACY_THRESHOLD=50
LIVENESS_DETECTION_ENABLED=true
EMOTION_ANALYSIS_ENABLED=true
FRAUD_DETECTION_ENABLED=true
```

### Step 5: Add PostgreSQL Database (Optional but Recommended)

1. In Railway Dashboard, click **"Add Service"**
2. Select **"PostgreSQL"**
3. Railway will automatically:
   - Create PostgreSQL container
   - Set `DATABASE_URL` environment variable
   - Your app will auto-detect and use PostgreSQL

**If using PostgreSQL:**
- In Variables, verify `DATABASE_TYPE=postgresql` is set
- The `DATABASE_URL` will be auto-populated by Railway
- Tables will be created automatically on first run

### Step 6: Monitor Deployment

**Check Deployment Status:**
- Go to **"Deployments"** tab
- Status should show **"Active"** (green checkmark)
- Build should complete in 2-5 minutes

**View Logs:**
- Click **"Logs"** tab
- Look for: `[OK] SmartAttendAI initialized successfully!`
- View your app URL in **"Domains"** section

**Health Check:**
```bash
curl https://<your-railway-url>/health
# Should return: {"status": "healthy", ...}
```

---

## 🔍 Troubleshooting

### Build Fails

Check logs for:
- `pip install` errors → Update `requirements.txt`
- Memory issues → Models too large
- Missing environment variables → Check step 4

**View detailed logs:**
```bash
railway logs --tail 100
```

### App Crashes on Startup

Check logs for:
- `ModuleNotFoundError` → Missing dependency
- `DatabaseError` → Database connection issue
- `No module named 'tensorflow'` → Run `pip install tensorflow`

### Models Not Loading

Models must be in `models/` directory:
- `emotion_model.h5`
- `spoof_detection_model.h5`
- `shape_predictor_68_face_landmarks.dat`

If missing, the app will use fallback methods ✓

### Database Connection Issues

**SQLite (Default):**
- Works out of the box
- Database stored at `data/smartattend.db`
- **NOTE:** Data lost on redeploy

**PostgreSQL (Recommended for production):**
- Add PostgreSQL service from Railway dashboard
- `DATABASE_URL` auto-set by Railway  
- Data persists across redeployments

---

## 📊 Post-Deployment

### Access Your App

Open your Railway domain URL:
```
https://<your-app-name>.railway.app
```

**Default endpoints:**
- Home: `/`
- Login: `/login`
- Dashboard: `/dashboard`
- API Docs: `/docs` (Swagger UI)
- Health: `/health`

### Create Admin User

Via dashboard API:
```bash
curl -X POST https://<your-app-name>.railway.app/api/admin/create \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "full_name": "Admin User",
    "password": "secure-password"
  }'
```

### Monitor Performance

**Railway Dashboard > Metrics:**
- CPU usage
- Memory usage
- Requests/second
- Error rate

---

## 🛠️ Advanced Configuration

### Scale Your App

In Railway Dashboard:
- **"Services"** → **SmartAttendAI** → **"Settings"**
- Increase **"Resources"** for GPU/CPU

### Custom Domain

- **"Domains"** → **"Add Domain"**
- Point your custom domain's DNS to Railway

### GitHub Auto-Deploy

Railway auto-deploys on push to `main` branch.

To disable:
- **Settings** → Toggle **"Auto-deploy"**

---

## 📝 Important Notes

1. **Models Required**: All ML models must be committed to Git
2. **SECRET_KEY**: Change it! Generate a new one for production  
3. **Telegram Bot**: Test in development first
4. **Database**: Use PostgreSQL for persistent data
5. **Logs**: Check regularly for errors
6. **Health Check**: `/health` endpoint monitors app status

---

## ✅ Checklist

- [ ] `.env` file created and filled
- [ ] SECRET_KEY generated  
- [ ] TELEGRAM_BOT_TOKEN added
- [ ] Code pushed to GitHub
- [ ] Railway project created
- [ ] Environment variables set in Railway
- [ ] PostgreSQL added (optional)
- [ ] Deployment active and healthy
- [ ] Health check endpoint works: `/health`
- [ ] Can access home page at `/`

---

## 🆘 Need Help?

- **Railway Docs**: https://docs.railway.app
- **SmartAttendAI Docs**: See `DOCUMENTATION.md`
- **GitHub Issues**: Report problems in your repo



### Add Environment Variables

1. In Railway project → **"Variables"** tab
2. Add these minimum variables:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   SECRET_KEY=some-random-secure-key-32-chars
   DEBUG=False
   ENVIRONMENT=production
   DATABASE_TYPE=sqlite
   ```

### Increase Memory (if needed)

1. Go to deployment settings
2. Set **Memory**: 2GB (for ML models)
3. Set **CPU**: 1 Shared

### Monitor Logs

Click **"Logs"** tab to see real-time application logs

---

## Troubleshooting

| Issue                    | Solution                                                                       |
| ------------------------ | ------------------------------------------------------------------------------ |
| **Build fails**          | Increase Railway plan to standard or select "Add PostgreSQL" if using database |
| **Can't access app**     | Wait 2-3 min, then refresh; check status is "Success"                          |
| **"Port cannot bind"**   | Already fixed in Procfile; redeploy                                            |
| **Models not loading**   | Check logs for path issues; use absolute paths                                 |
| **Telegram not working** | Verify `TELEGRAM_BOT_TOKEN` is in Variables                                    |

---

## After Deployment

1. **Test the Application**
   - Visit your Railway domain URL
   - Login and test features

2. **Set Up Custom Domain** (Optional)
   - In Railway → **"Settings"** → **"Domains"**
   - Add your custom domain

3. **Enable PostgreSQL** (Recommended)
   - For persistent data, add PostgreSQL plugin
   - Railway auto-creates `DATABASE_URL`

4. **Monitor Performance**
   - Watch Railway dashboard for resource usage
   - Set up alerts in settings

---

## Need Help?

- **Railway Docs**: https://docs.railway.app/
- **Project Docs**: See `DOCUMENTATION.md`
- **Full Guide**: See `RAILWAY_DEPLOYMENT.md`

---

**Deployment successful! Your app is now live on Railway.** 🚀
