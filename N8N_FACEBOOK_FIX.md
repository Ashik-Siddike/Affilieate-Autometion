# n8n Facebook Auto-Posting Fix Summary

## ✅ কি কি Fix করা হয়েছে:

### 1. **Default n8n Automation Enabled**
   - `main.py`-তে n8n automation-এর default value এখন **True**
   - এখন project run করলে automatically Facebook-এ post হবে (যদি WordPress publishing enable থাকে)

### 2. **Improved Error Handling**
   - `n8n_handler.py`-তে better error messages যোগ করা হয়েছে
   - Response validation improve করা হয়েছে
   - Facebook posting success check করা হচ্ছে
   - Timeout 30s থেকে 90s করা হয়েছে (AI processing-এর জন্য)

### 3. **Better Logging**
   - `main.py`-তে n8n trigger করার সময় detailed logs
   - Success/failure status clear করে দেখানো হচ্ছে

### 4. **GUI Update**
   - Streamlit GUI-তে n8n automation default **True** করা হয়েছে
   - Label update: "Facebook Auto-Post" যোগ করা হয়েছে

### 5. **Test Script**
   - `test_n8n_facebook.py` script তৈরি করা হয়েছে
   - এই script দিয়ে আপনি test করতে পারবেন n8n workflow ঠিকমতো কাজ করছে কিনা

## 🚀 কিভাবে Use করবেন:

### Option 1: CLI থেকে Run করুন
```bash
python main.py
```
- Configuration menu-তে "Trigger n8n Automation" prompt-এ **Enter** চাপুন (default: Yes)
- অথবা **y** type করুন

### Option 2: GUI থেকে Run করুন
```bash
streamlit run gui.py
```
- "Trigger n8n Automation (Facebook Auto-Post)" checkbox automatically checked থাকবে
- "Start Automation" button click করুন

### Option 3: Test Script Run করুন
```bash
python test_n8n_facebook.py
```
- এই script test data send করবে n8n workflow-এ
- Facebook-এ post হয়েছে কিনা check করতে পারবেন

## 📋 n8n Workflow Details:

- **Workflow Name**: Master Amazon Social Media Auto-Poster
- **Status**: ✅ Active
- **Webhook URL**: `https://ashik-mama.app.n8n.cloud/webhook/amazon-master-webhook`
- **Workflow ID**: `fel6PaueVbNGu8kI`

### Workflow Flow:
1. **Webhook Trigger** → Receives product data
2. **AI Content Transformer** → Creates Facebook post content using Groq AI
3. **Post to Facebook** → Publishes to Facebook page
4. **Response** → Returns success status

## ⚠️ Important Notes:

1. **Workflow Must Be Active**: n8n dashboard-এ workflow **ON** থাকতে হবে
2. **Facebook Credentials**: n8n-এ Facebook credentials properly configured থাকতে হবে
3. **Facebook Permissions**: Facebook page-এ proper permissions থাকতে হবে
4. **Check n8n Dashboard**: যদি post না হয়, n8n dashboard-এর "Executions" tab check করুন

## 🔍 Troubleshooting:

### যদি Facebook-এ post না হয়:

1. **n8n Dashboard Check করুন**:
   - https://ashik-mama.app.n8n.cloud
   - "Executions" tab-এ latest execution check করুন
   - Error messages দেখুন

2. **Facebook Credentials Check করুন**:
   - n8n workflow-এ "Post to Facebook1" node-এ credentials verify করুন
   - Facebook Graph API token valid আছে কিনা check করুন

3. **Workflow Status Check করুন**:
   - Workflow active আছে কিনা verify করুন
   - Webhook URL correct আছে কিনা check করুন

4. **Test Script Run করুন**:
   ```bash
   python test_n8n_facebook.py
   ```
   - এই script detailed error messages দেখাবে

## 📝 Configuration:

`config.py`-তে n8n webhook URL:
```python
N8N_WEBHOOK_URL = "https://ashik-mama.app.n8n.cloud/webhook/amazon-master-webhook"
```

## ✅ Verification:

Project run করার পর:
1. WordPress-এ post published হয়েছে ✅
2. n8n workflow triggered হয়েছে ✅
3. Facebook-এ post published হয়েছে ✅ (check your Facebook page)

---

**Created**: 2025-01-25
**Status**: ✅ Ready for Production


