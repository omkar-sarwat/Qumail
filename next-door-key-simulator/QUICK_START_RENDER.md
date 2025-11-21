# Quick Start: Deploy to Render.com

## 🚀 Fast Track (5 minutes)

### Step 1: Push to GitHub
```powershell
cd "d:\New folder (8)\qumail-secure-email"
git add next-door-key-simulator/
git commit -m "Add KME simulator for Render"
git push
```

### Step 2: Deploy to Render
1. Go to https://dashboard.render.com
2. Click **New +** → **Blueprint**
3. Connect your GitHub repo
4. Select `next-door-key-simulator/render.yaml`
5. Click **Apply** - Both KME servers will deploy automatically!

### Step 3: Update Backend
```powershell
cd qumail-backend
```

Edit `.env`:
```env
KM1_BASE_URL=https://qumail-kme-sender.onrender.com
KM2_BASE_URL=https://qumail-kme-receiver.onrender.com
```

### Step 4: Test
```powershell
python test_cloud_kme.py
```

## 🎯 Expected Results

**Health Check (both KMEs):**
```bash
Invoke-WebRequest https://qumail-kme-sender.onrender.com/api/v1/kme/status
Invoke-WebRequest https://qumail-kme-receiver.onrender.com/api/v1/kme/status
```

**Status Code:** 200 OK
**Response:**
```json
{
  "status": "ok",
  "kme_id": "1",
  "key_pool_size": 1000,
  "available_keys": 950
}
```

## 📋 Service URLs

After deployment, you'll get:

- **KME 1 (Sender):** `https://qumail-kme-sender.onrender.com`
- **KME 2 (Receiver):** `https://qumail-kme-receiver.onrender.com`

## 🔑 ETSI QKD 014 Endpoints

Both KME servers support:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/kme/status` | GET | Health check |
| `/api/v1/keys/{slave_sae_id}/status` | GET | Key pool status |
| `/api/v1/keys/{slave_sae_id}/enc_keys` | POST | Generate keys |
| `/api/v1/keys/{master_sae_id}/dec_keys` | POST | Retrieve keys |

## ⚡ Performance Notes

**Free Tier:**
- Services sleep after 15 min inactivity
- First request takes 30-60 sec (wake up time)
- Perfect for development/testing

**Upgrade to Starter ($7/month per service):**
- No cold starts
- Always-on
- Better performance
- Recommended for production

## 🛠️ Troubleshooting

### "Service Unavailable"
**Solution:** Wait 60 seconds for service to wake up from sleep.

### Connection Timeout
**Solution:** Check Render logs and verify environment variables.

### Backend 404 Errors
**Solution:** Restart backend after updating `.env`.

## 📝 Environment Variables Reference

**KME 1 (Sender):**
```env
KME_ID=1
ATTACHED_SAE_ID=25840139-0dd4-49ae-ba1e-b86731601803
OTHER_KMES=https://qumail-kme-receiver.onrender.com
```

**KME 2 (Receiver):**
```env
KME_ID=2
ATTACHED_SAE_ID=c565d5aa-8670-4446-8471-b0e53e315d2a
OTHER_KMES=https://qumail-kme-sender.onrender.com
```

## 🎊 Success Checklist

- [ ] Both KME services deployed on Render
- [ ] Health checks return 200 OK
- [ ] Backend .env updated with Render URLs
- [ ] `test_cloud_kme.py` passes all tests
- [ ] Backend server starts without errors
- [ ] Can send encrypted emails through QuMail

## 📚 Full Documentation

See `RENDER_DEPLOYMENT_GUIDE.md` for comprehensive instructions.

## 🆘 Need Help?

1. Check Render service logs: Dashboard → Service → Logs
2. Test endpoints with PowerShell: `Invoke-WebRequest -Uri "..."`
3. Verify environment variables in Render dashboard
4. Review backend logs for connection errors

## 💰 Cost

**Current Setup (Free Tier):** $0/month

**Production Setup (Starter):** $14/month ($7 per KME)

Both free tier services give you 750 hours/month - plenty for testing!
