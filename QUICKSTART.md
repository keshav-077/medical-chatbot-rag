# 🚀 Quick Start Guide - Medical Chatbot

Get your medical chatbot running in minutes!

## ✅ Prerequisites Check

Make sure you have these installed:
- [x] Python 3.10+ → `python --version`
- [x] pip → `pip --version`
- [x] Virtual environment activated

---

## 🏃 Run Locally (5 Minutes)

### Step 1: Activate Virtual Environment
```bash
# If not already activated
venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Check Environment Variables
Your `.env` file is already configured with:
- ✅ PINECONE_API_KEY
- ✅ GROQ_API_KEY
- ✅ TELEGRAM_BOT_TOKEN
- ✅ SECRET_KEY

### Step 4: Initialize Vector Database (One-Time Only)
```bash
python store_index.py
```
⏳ This takes 2-5 minutes. It processes the medical PDF and creates embeddings.

**You'll see output like:**
```
Loading PDF files...
Splitting text into chunks...
Creating embeddings...
Uploading to Pinecone...
✅ Done!
```

### Step 5: Run the Application
```bash
python app.py
```

**You should see:**
```
* Running on http://0.0.0.0:8080
* Debug mode: on
```

### Step 6: Test the Web Interface
Open your browser:
```
http://localhost:8080
```

1. Click "Sign Up" to create an account
2. Login with your credentials
3. Start asking medical questions!

---

## 🤖 Test Telegram Bot Locally

### Option A: Quick Test (Using ngrok)

1. **Keep Flask running** (from Step 5 above)

2. **Install ngrok**: https://ngrok.com/download

3. **In a new terminal, start ngrok:**
   ```bash
   ngrok http 8080
   ```

4. **Copy the HTTPS URL** (looks like: `https://abcd-1234.ngrok-free.app`)

5. **Set up webhook:**
   ```bash
   python setup_webhook.py
   ```
   - Choose option 1
   - Paste your ngrok URL
   - Press Enter

6. **Open Telegram and test:**
   - Search: `@medical7725_Bot`
   - Send: `/start`
   - Ask: "What is diabetes?"

### Option B: Deploy to Vercel (Permanent)

See section below for production deployment.

---

## 🌐 Deploy to Vercel (10 Minutes)

### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

### Step 2: Login
```bash
vercel login
```

### Step 3: Deploy
```bash
vercel --prod
```

Follow the prompts:
- Link to existing project? **No**
- Project name? **medical-chatbot** (or your choice)
- Directory? **.** (current directory)

### Step 4: Add Environment Variables

Go to your Vercel dashboard: https://vercel.com/dashboard

1. Select your project
2. Settings → Environment Variables
3. Add these (copy from your `.env` file):

```
PINECONE_API_KEY=your_pinecone_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
SECRET_KEY=your_secret_key_here
```

### Step 5: Redeploy (to apply env vars)
```bash
vercel --prod
```

### Step 6: Set Up Telegram Webhook

Visit this URL in your browser (replace with your Vercel URL):
```
https://your-app.vercel.app/api/telegram/setup
```

You should see:
```json
{"status": "webhook set", "result": {"ok": true}}
```

### Step 7: Test Everything! 🎉

**Web Interface:**
```
https://your-app.vercel.app
```

**Telegram Bot:**
```
https://t.me/medical7725_Bot
```

---

## 🧪 Testing & Verification

### Test Script
```bash
python test_bot.py
```

**Expected Output:**
```
✅ Bot connected successfully!
📱 Bot Name: medical-bot
👤 Username: @medical7725_Bot
```

### Webhook Setup Tool
```bash
python setup_webhook.py
```

Options:
1. Set webhook (for deployment)
2. Check webhook status
3. Delete webhook (for local testing)

### Manual API Test
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
```

---

## 📱 Using Your Bot

### Telegram Commands
- `/start` - Welcome message
- `/help` - Show commands
- `/clear` - New conversation

### Example Questions
```
What are the symptoms of diabetes?
How does hypertension affect the kidneys?
What is the normal blood pressure range?
Explain what causes a heart attack
What are the side effects of aspirin?
```

### Web Interface
1. Sign up at: `http://localhost:8080/signup`
2. Login
3. Start chatting!
4. Create multiple conversations
5. View history in sidebar

---

## 🔧 Troubleshooting

### Port Already in Use
```python
# In app.py, change the port:
app.run(host="0.0.0.0", port=5000, debug=True)
```

### Module Not Found
```bash
pip install -r requirements.txt
```

### Vector Store Not Found
```bash
# Re-run the initialization
python store_index.py
```

### Bot Not Responding (Telegram)
1. Check webhook status: `python setup_webhook.py` → option 2
2. Verify Flask is running
3. Check ngrok is active (for local testing)
4. Check Vercel logs (for production)

### Database Errors
```bash
# Reset database
python -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"
```

---

## 📊 Project Status

| Component | Status | URL/Info |
|-----------|--------|----------|
| Flask App | ✅ Configured | `http://localhost:8080` |
| Telegram Bot | ✅ Created | `@medical7725_Bot` |
| API Token | ✅ Set | In `.env` file |
| Vector DB | ⏳ Needs Init | Run `store_index.py` |
| Web Interface | ✅ Ready | Templates included |
| Vercel Config | ✅ Ready | `vercel.json` exists |

---

## 🎯 Next Steps After Setup

1. **Customize Bot Profile:**
   - Open Telegram → `@BotFather`
   - `/mybots` → Select your bot
   - Set description, about text, profile picture

2. **Add More Medical Documents:**
   - Add PDF files to `Data/` folder
   - Re-run: `python store_index.py`

3. **Customize Responses:**
   - Edit `src/prompt.py` to change AI behavior
   - Adjust temperature in `app.py` (line ~75)

4. **Monitor Usage:**
   - Pinecone dashboard: https://app.pinecone.io
   - Groq console: https://console.groq.com
   - Vercel analytics: https://vercel.com/dashboard

5. **Share Your Bot:**
   - Direct link: `https://t.me/medical7725_Bot`
   - Generate QR code via @BotFather

---

## 📚 Documentation

- **Full Setup**: `README.md`
- **Telegram Details**: `TELEGRAM_SETUP.md`
- **Complete Docs**: `DOCUMENTATION.md`
- **This Guide**: `QUICKSTART.md`

---

## 🆘 Common Commands Reference

```bash
# Activate environment
venv\Scripts\activate

# Run app
python app.py

# Test bot config
python test_bot.py

# Setup webhook
python setup_webhook.py

# Initialize vector DB (one-time)
python store_index.py

# Deploy to Vercel
vercel --prod

# Start ngrok (for local testing)
ngrok http 8080
```

---

## ✅ Success Checklist

- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Vector database initialized (`store_index.py`)
- [ ] Flask app running (`python app.py`)
- [ ] Web interface working (`http://localhost:8080`)
- [ ] Telegram bot tested (`@medical7725_Bot`)
- [ ] Webhook configured (ngrok or Vercel)
- [ ] Production deployment (Vercel)

---

## 🎉 You're All Set!

Your medical chatbot is ready to help users! 

**Need help?** Check the documentation or run `python test_bot.py` to diagnose issues.

**Bot Link**: https://t.me/medical7725_Bot 🤖
