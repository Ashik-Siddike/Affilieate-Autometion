# 🚀 Quick Fix: Facebook Posting Issue

## 📌 সমস্যা:
Website-এ post হয়েছে কিন্তু Facebook-এ post হয়নি

## ✅ Immediate Actions:

### Step 1: Quick Status Check
```bash
python check_facebook_status.py
```
এই script দিয়ে quickly check করুন connection এবং workflow status

### Step 2: Detailed Debug (যদি Step 1 fail করে)
```bash
python debug_n8n_facebook.py
```
এই script detailed analysis দেবে

### Step 3: n8n Dashboard Check
1. Go to: https://ashik-mama.app.n8n.cloud
2. Click "Executions" tab
3. Find latest execution
4. Check "Post to Facebook1" node:
   - ✅ **Green** = Success (check Facebook page)
   - ❌ **Red** = Error (see below)

---

## 🔧 Most Common Fixes:

### Fix 1: Facebook Token Expired (90% cases)
**Symptoms:** Red node in n8n, error about token

**Fix:**
1. n8n Dashboard → Credentials
2. Find "Facebook" → Edit
3. Click "Connect my account" / "Renew token"
4. Follow Facebook OAuth
5. Save & Re-run

### Fix 2: Workflow Not Active
**Symptoms:** 404 error

**Fix:**
1. n8n Dashboard → Workflows
2. Find "Master Amazon Social Media Auto-Poster"
3. Toggle **ON** (should be green)

### Fix 3: Facebook Permissions Missing
**Symptoms:** Permission denied error

**Fix:**
1. https://developers.facebook.com
2. Your App → Permissions
3. Add: `pages_manage_posts`
4. Re-authenticate in n8n

---

## 📋 Verification:

After fixing, verify:

1. **Run test:**
   ```bash
   python check_facebook_status.py
   ```

2. **Check n8n:**
   - All nodes Green ✅
   - Facebook node Success ✅

3. **Check Facebook:**
   - Post visible on page ✅
   - Content correct ✅
   - Link works ✅

---

## 🆘 Still Not Working?

Read full guide: `FACEBOOK_TROUBLESHOOTING.md`

Or check:
- n8n Executions tab for detailed errors
- Facebook Developer Portal for token status
- Facebook Page settings for permissions

---

**Quick Commands:**
```bash
# Status check
python check_facebook_status.py

# Detailed debug
python debug_n8n_facebook.py

# Test workflow
python test_n8n_facebook.py
```

