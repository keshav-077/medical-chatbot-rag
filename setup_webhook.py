"""
Helper script to set up Telegram webhook
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found in .env file")
    sys.exit(1)

print("🔧 Telegram Webhook Setup Tool")
print("=" * 60)

# Menu
print("\nWhat would you like to do?")
print("1. Set webhook (for Vercel or ngrok)")
print("2. Check webhook status")
print("3. Delete webhook (for local testing without ngrok)")
print("4. Exit")

choice = input("\nEnter your choice (1-4): ").strip()

if choice == "1":
    # Set webhook
    url = input("\nEnter your webhook URL (e.g., https://your-app.vercel.app): ").strip()
    
    if not url.startswith("https://"):
        print("❌ ERROR: Webhook URL must start with https://")
        sys.exit(1)
    
    # Remove trailing slash if present
    url = url.rstrip("/")
    webhook_url = f"{url}/api/telegram"
    
    print(f"\n📡 Setting webhook to: {webhook_url}")
    
    response = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook",
        json={"url": webhook_url}
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            print("✅ Webhook set successfully!")
            print(f"   URL: {webhook_url}")
        else:
            print(f"❌ Error: {data.get('description')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

elif choice == "2":
    # Check webhook status
    print("\n📊 Fetching webhook information...")
    
    response = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo"
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get("ok"):
            info = data.get("result", {})
            
            print("\n" + "=" * 60)
            print("Webhook Information:")
            print("=" * 60)
            print(f"URL: {info.get('url', 'Not set')}")
            print(f"Pending updates: {info.get('pending_update_count', 0)}")
            print(f"Max connections: {info.get('max_connections', 'N/A')}")
            
            if info.get('last_error_date'):
                from datetime import datetime
                error_time = datetime.fromtimestamp(info.get('last_error_date'))
                print(f"\n⚠️  Last error: {info.get('last_error_message')}")
                print(f"   Time: {error_time}")
            
            if info.get('url'):
                print("\n✅ Webhook is configured and active!")
            else:
                print("\n⚠️  No webhook configured")
                print("   Use option 1 to set up webhook")
        else:
            print(f"❌ Error: {data.get('description')}")
    else:
        print(f"❌ HTTP Error: {response.status_code}")

elif choice == "3":
    # Delete webhook
    confirm = input("\n⚠️  Are you sure you want to delete the webhook? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        print("\n🗑️  Deleting webhook...")
        
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Webhook deleted successfully!")
                print("   Your bot will no longer receive updates until you set a new webhook")
            else:
                print(f"❌ Error: {data.get('description')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    else:
        print("❌ Cancelled")

elif choice == "4":
    print("\n👋 Goodbye!")
    sys.exit(0)

else:
    print("❌ Invalid choice")
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ Done!")
print("=" * 60)

print("\n📚 Useful Commands:")
print("   • Test bot: python test_bot.py")
print("   • Run app: python app.py")
print("   • Check logs: See Flask console output")
print("\n🔗 Your Bot: https://t.me/medical7725_Bot")
