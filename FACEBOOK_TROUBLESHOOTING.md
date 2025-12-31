# Facebook Posting Troubleshooting Guide

## 🔍 সমস্যা: Website-এ Post হয়েছে কিন্তু Facebook-এ Post হয়নি

### ✅ Quick Check List:

1. **n8n Workflow Status**
   - ✅ Workflow active আছে?
   - ✅ Webhook URL correct?
   - ✅ Latest execution successful?

2. **Facebook Node Status**
   - ✅ Facebook credentials configured?
   - ✅ Facebook Graph API token valid?
   - ✅ Facebook page permissions set?

3. **AI Content Transformer**
   - ✅ Output properly formatted?
   - ✅ Message text generated?

---

## 🛠️ Step-by-Step Debugging:

### Step 1: n8n Dashboard Check করুন

1. **Go to n8n Dashboard**: https://ashik-mama.app.n8n.cloud
2. **Click "Executions" tab** (left sidebar)
3. **Find latest execution** (should be recent, same time as your run)
4. **Click on the execution** to see details

### Step 2: Check Workflow Nodes

#### Node 1: Amazon-Master-Webhook1
- ✅ Should be **Green** (Success)
- ✅ Check if it received the data:
  - `title`: Product title
  - `description`: Product description
  - `amazon_link`: WordPress post link

#### Node 2: AI Content Transformer1
- ✅ Should be **Green** (Success)
- ✅ Click on it to see output
- ✅ Check `output` field - should contain Facebook post text
- ⚠️ If **Red** (Error):
  - Check Groq API credentials
  - Verify AI model is working

#### Node 3: Post to Facebook1
- ✅ Should be **Green** (Success) = Post published
- ❌ If **Red** (Error):
  - **Most Common Issues:**
    1. **Facebook Token Expired**
       - Solution: Go to n8n Credentials → Facebook → Renew token
    2. **Facebook Page Permissions Missing**
       - Solution: Add `pages_manage_posts` permission
    3. **Invalid Page ID**
       - Solution: Verify page ID in node settings
    4. **Rate Limit Exceeded**
       - Solution: Wait a few minutes and retry

### Step 3: Check Facebook Page

1. **Go to your Facebook Page**
2. **Check "Posts" section**
3. **Look for recent posts**
4. If post is not there:
   - Check "Scheduled Posts" (might be scheduled)
   - Check "Drafts" (might be saved as draft)
   - Check page permissions

---

## 🔧 Common Fixes:

### Fix 1: Facebook Token Expired

**Symptoms:**
- n8n execution shows error in "Post to Facebook1" node
- Error message: "Invalid OAuth access token" or "Token expired"

**Solution:**
1. Go to n8n Dashboard → Credentials
2. Find "Facebook" credential
3. Click "Edit"
4. Click "Connect my account" or "Renew token"
5. Follow Facebook OAuth flow
6. Save credentials
7. Re-run workflow

### Fix 2: Facebook Page Permissions

**Symptoms:**
- Error: "Insufficient permissions" or "Permission denied"

**Solution:**
1. Go to Facebook Developer Portal: https://developers.facebook.com
2. Select your app
3. Go to "Permissions" → "User Data Permissions"
4. Add these permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `pages_show_list`
5. Re-authenticate in n8n

### Fix 3: AI Content Transformer Output Issue

**Symptoms:**
- AI node executes but output is empty or malformed
- Facebook node receives empty message

**Solution:**
1. Check "AI Content Transformer1" node output
2. Verify `output` field contains text
3. If empty, check:
   - Groq API credentials
   - AI model is working
   - Prompt is correct

### Fix 4: Network/Timeout Issues

**Symptoms:**
- Workflow times out
- Connection errors

**Solution:**
1. Increase timeout in workflow settings
2. Check n8n instance is running
3. Verify internet connection
4. Check firewall settings

---

## 🧪 Debug Scripts:

### Script 1: Basic Test
```bash
python test_n8n_facebook.py
```
Tests basic n8n workflow connection

### Script 2: Detailed Debug
```bash
python debug_n8n_facebook.py
```
Shows detailed response and analysis

---

## 📋 n8n Workflow Configuration Check:

### Required Settings:

1. **Webhook Node (Amazon-Master-Webhook1)**
   - Method: POST
   - Path: `amazon-master-webhook`
   - Response Mode: Response Node

2. **AI Content Transformer Node**
   - Model: Groq Chat Model
   - Input: `{{ $json.title }}`, `{{ $json.description }}`, `{{ $json.amazon_link }}`
   - Output: Facebook post text

3. **Facebook Post Node (Post to Facebook1)**
   - Method: POST
   - Graph API Version: v21.0
   - Node: Your Facebook Page ID
   - Edge: `feed`
   - Message: `{{ $json.output }}`
   - Link: `{{ $('Amazon-Master-Webhook1').first().json.body.amazon_link }}`

---

## 🔍 Verification Steps:

After fixing issues, verify:

1. **Run test script:**
   ```bash
   python debug_n8n_facebook.py
   ```

2. **Check n8n execution:**
   - All nodes should be Green
   - Facebook node should show success

3. **Check Facebook page:**
   - Post should be visible
   - Post should have correct content
   - Link should work

---

## 📞 Still Having Issues?

If Facebook posting still doesn't work:

1. **Check n8n Logs:**
   - Go to n8n Dashboard → Settings → Logs
   - Look for Facebook-related errors

2. **Check Facebook Graph API:**
   - Go to: https://developers.facebook.com/tools/explorer
   - Test your token
   - Verify permissions

3. **Manual Test:**
   - Try posting manually to Facebook page
   - If manual post works, issue is in n8n workflow
   - If manual post fails, issue is in Facebook setup

---

## ✅ Success Indicators:

You'll know it's working when:

1. ✅ n8n execution shows all nodes Green
2. ✅ Facebook node shows "Success" status
3. ✅ Post appears on Facebook page within 1-2 minutes
4. ✅ Post contains correct content and link

---

**Last Updated**: 2025-01-25
**Status**: Active Troubleshooting Guide


