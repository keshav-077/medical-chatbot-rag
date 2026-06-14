# 🤖 Telegram Bot Setup Guide

Your medical chatbot is configured and ready! Follow these steps to get it running.

## ✅ Current Status

- **Bot Name**: medical-bot
- **Username**: @medical7725_Bot
- **Bot Link**: https://t.me/medical7725_Bot
- **Configuration**: ✅ Token added to .env
- **API Connection**: ✅ Verified working
- **Webhook**: ⚠️ Not configured yet (needs public URL)

---

## 🚀 Quick Start Options

### Option 1: Deploy to Vercel (Recommended for Production)

This is the easiest and most reliable way to run your bot.

#### Step 1: Install Vercel CLI
```bash
npm install -g vercel
```

#### Step 2: Login to Vercel
```bash
vercel login
```

#### Step 3: Deploy
```bash
vercel --prod
```

#### Step 4: Add Environment Variables
After deployment, go to your Vercel dashboard:
1. Select your project
2. Go to Settings → Environment Variables
3. Add these variables (copy from your `.env` file):
   ```
   PINECONE_API_KEY=your_pinecone_api_key_here
   GROQ_API_KEY=your_groq_api_key_here
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   SECRET_KEY=your_secret_key_here
   ```

#### Step 5: Register Webhook
Visit this URL (replace with your Vercel URL):
```
https://your-app.vercel.app/api/telegram/setup
```

You should see:
```json
{
  "status": "webhook set",
  "result": {"ok": true, ...}
}
```

#### Step 6: Test Your Bot! 🎉
1. Open Telegram
2. Search for `@medical7725_Bot`
3. Send `/start`
4. Ask medical questions!

---

### Option 2: Local Testing with ngrok

Use this for testing before deploying to production.

#### Step 1: Install ngrok
Download from: https://ngrok.com/download

Or use Chocolatey (Windows):
```bash
choco install ngrok
```

#### Step 2: Start Your Flask App
```bash
python app.py
```

Your app should be running on `http://localhost:8080`

#### Step 3: Start ngrok
In a new terminal:
```bash
ngrok http 8080
```

You'll see output like:
```
Forwarding  https://abcd-1234.ngrok-free.app -> http://localhost:8080
```

Copy the HTTPS URL (e.g., `https://abcd-1234.ngrok-free.app`)

#### Step 4: Register Webhook
Run this command (replace YOUR-BOT-TOKEN and YOUR-NGROK-URL):
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://YOUR-NGROK-URL/api/telegram"
```

Or visit this URL in your browser:
```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://YOUR-NGROK-URL/api/telegram
```

#### Step 5: Test Your Bot
1. Open Telegram
2. Search for `@medical7725_Bot`
3. Send `/start`
4. Ask questions!

**Note**: Keep both the Flask app and ngrok running while testing.

---

## 🎮 Bot Commands

Once your bot is running, you can use these commands:

- `/start` - Welcome message and introduction
- `/help` - Show available commands
- `/clear` - Start a new conversation
- Just type any medical question to get an answer!

### Example Questions:
- "What are the symptoms of diabetes?"
- "How does hypertension affect the kidneys?"
- "What is the normal range for blood pressure?"
- "Explain what causes a heart attack"

---

## 🔧 Troubleshooting

### Bot Not Responding

**Check webhook status:**
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
```

**Remove webhook (for testing):**
```bash
curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook"
```

### Webhook Errors

Check your server logs:
- Vercel: Go to your project dashboard → Deployments → View logs
- Local: Check the Flask console output

### Environment Variables Not Working

Make sure:
1. `.env` file exists in project root
2. All required variables are set
3. No extra spaces around `=` signs
4. Restart your Flask app after changing `.env`

---

## 📊 Verify Setup

Run the test script to check your configuration:
```bash
python test_bot.py
```

This will verify:
- Bot token is valid
- API connection works
- Webhook status
- Bot information

---

## 🔒 Security Notes

**IMPORTANT**: Your bot token is sensitive! 

- ✅ Keep `.env` file private (it's in .gitignore)
- ✅ Never commit tokens to Git
- ✅ Use environment variables on Vercel
- ✅ Regenerate token if accidentally exposed

**To regenerate token:**
1. Open Telegram
2. Search for `@BotFather`
3. Send `/mybots`
4. Select your bot
5. Go to Bot Settings → API Token → Regenerate

---

## 📱 Bot Features

Your bot includes:

✅ **RAG-Powered Responses**
- Retrieves relevant medical information from knowledge base
- Uses Groq LLM for natural language generation
- Provides concise, accurate answers

✅ **Conversation Management**
- Maintains conversation history per user
- `/clear` command to start fresh
- Automatic session handling

✅ **User-Friendly Interface**
- Typing indicators while processing
- Formatted responses with Markdown
- Medical disclaimer on all responses

✅ **Error Handling**
- Graceful error messages
- Automatic retry logic
- Timeout protection

---

## 🌐 Dual Interface

Your medical chatbot runs on TWO interfaces:

1. **Web UI**: `http://localhost:8080` (or your Vercel URL)
   - Full chat interface
   - User authentication
   - Conversation history
   - Multi-session support

2. **Telegram Bot**: `@medical7725_Bot`
   - Instant messaging
   - No login required
   - Mobile-friendly
   - Push notifications

Both use the **same RAG pipeline** for consistent answers!

---

## 📈 Next Steps

1. ✅ Deploy to Vercel
2. ✅ Set up webhook
3. ✅ Test with medical questions
4. 🎨 Customize bot description:
   - Open Telegram
   - Search `@BotFather`
   - Send `/mybots`
   - Select your bot
   - Edit description, about, and profile picture

5. 📢 Share your bot!
   - Direct link: https://t.me/medical7725_Bot
   - QR code available in BotFather

---

## 🆘 Need Help?

**Check these resources:**
- Main README: `README.md`
- Documentation: `DOCUMENTATION.md`
- Test script: `python test_bot.py`

**Common issues:**
1. Bot not responding → Check webhook is set
2. Wrong answers → Verify Pinecone index is initialized
3. Slow responses → Check Groq API key is set (faster than OpenRouter)

---

## 🎉 Success Checklist

- [x] Bot created with @BotFather
- [x] Token added to .env
- [x] Bot API connection verified
- [ ] Deployed to Vercel (or ngrok for testing)
- [ ] Webhook registered
- [ ] Tested with `/start` command
- [ ] Asked a medical question
- [ ] Received accurate response

**Your bot is ready to help users with medical questions!** 🏥
