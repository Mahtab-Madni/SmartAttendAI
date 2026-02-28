# Quick Railway Deployment Checklist

## 5-Minute Setup

### Step 1: Prepare Your Code

```bash
# Ensure you're in the project root
cd c:\SmartAttendAI

# Create .env file from example
copy .env.example .env

# Edit .env with your values (especially TELEGRAM_BOT_TOKEN)
# Use Notepad or your editor to fill in:
# - TELEGRAM_BOT_TOKEN
# - SECRET_KEY (optional, but recommended)
```

### Step 2: Push to GitHub

```bash
git add .
git commit -m "Add Railway deployment files"
git push origin main
```

### Step 3: Deploy on Railway

1. Go to **https://railway.app/dashboard**
2. Click **"New Project"** → **"Deploy from GitHub"**
3. Select your SmartAttendAI repository
4. Wait for auto-deployment (2-5 minutes)
5. In Railway dashboard, go to **Variables**
6. Copy all your `.env` variables into Railway:
   - Click "Add Variable"
   - Paste each key=value pair from your `.env`

### Step 4: Verify

Once deployed, check:

- Deployment status → "Active" (green)
- View logs: **"Logs"** tab
- Check URL in **"Deploy"** tab → "Domains"

---

## Configuration on Railway Dashboard

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
