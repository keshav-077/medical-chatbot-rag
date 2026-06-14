"""
Quick test script to verify Telegram bot configuration
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in .env file")
    exit(1)

print("🔍 Testing Telegram Bot Configuration...\n")

# Test 1: Get bot info
print("1️⃣ Fetching bot information...")
response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe")
if response.status_code == 200:
    data = response.json()
    if data.get("ok"):
        bot_info = data.get("result", {})
        print(f"   ✅ Bot connected successfully!")
        print(f"   📱 Bot Name: {bot_info.get('first_name')}")
        print(f"   👤 Username: @{bot_info.get('username')}")
        print(f"   🆔 Bot ID: {bot_info.get('id')}")
    else:
        print(f"   ❌ Error: {data.get('description')}")
else:
    print(f"   ❌ HTTP Error: {response.status_code}")
    exit(1)

# Test 2: Check webhook status
print("\n2️⃣ Checking webhook status...")
response = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo")
if response.status_code == 200:
    data = response.json()
    if data.get("ok"):
        webhook_info = data.get("result", {})
        webhook_url = webhook_info.get("url", "Not set")
        
        if webhook_url and webhook_url != "":
            print(f"   ✅ Webhook configured: {webhook_url}")
            print(f"   📊 Pending updates: {webhook_info.get('pending_update_count', 0)}")
            if webhook_info.get('last_error_message'):
                print(f"   ⚠️  Last error: {webhook_info.get('last_error_message')}")
        else:
            print("   ⚠️  Webhook NOT configured (this is normal for local dev)")
            print("   💡 To test locally, use ngrok (see instructions)")
            print("   💡 For production, deploy to Vercel first")

print("\n" + "="*60)
print("✅ Configuration test complete!")
print("="*60)

print("\n📚 Next Steps:")
print("   1. Local Testing: Use ngrok (see README)")
print("   2. Production: Deploy to Vercel")
print("\n🔗 Your Bot Link: https://t.me/medical7725_Bot")
