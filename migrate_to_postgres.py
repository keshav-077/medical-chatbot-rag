"""
One-time migration script: SQLite → Neon PostgreSQL.

Run this ONCE after setting up your Neon database.
It reads all data from local SQLite and writes to Neon PostgreSQL.

Usage:
    1. Set DATABASE_URL in your .env file (Neon connection string)
    2. Run: python migrate_to_postgres.py
    3. Verify data in Neon dashboard
    4. Deploy to Vercel

Prerequisites:
    - Neon account: https://neon.tech (free tier: 512MB storage)
    - DATABASE_URL in .env (use the -pooler endpoint)
"""

import os
import sys
import sqlite3
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def migrate_sqlite_to_postgres():
    """Migrate all data from SQLite to Neon PostgreSQL."""

    # Check DATABASE_URL
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        print("❌ DATABASE_URL not set in .env")
        print("")
        print("Steps to set up Neon PostgreSQL:")
        print("  1. Sign up at https://neon.tech (free)")
        print("  2. Create a new project")
        print("  3. Copy the connection string (use the -pooler endpoint)")
        print("  4. Add to .env: DATABASE_URL=postgresql://...")
        print("  5. Re-run this script")
        return False

    # Normalize URL
    if postgres_url.startswith("postgres://"):
        postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

    # Check SQLite source
    sqlite_paths = [
        "instance/medical_chatbot.db",
        "medical_chatbot.db",
    ]
    sqlite_path = None
    for path in sqlite_paths:
        if os.path.exists(path):
            sqlite_path = path
            break

    if not sqlite_path:
        print(f"ℹ️  No SQLite database found (checked: {sqlite_paths})")
        print("   Creating fresh PostgreSQL tables...")

        # Set environment for app import
        os.environ["DATABASE_URL"] = postgres_url
        os.environ["FLASK_ENV"] = "production"

        from app import app, db
        with app.app_context():
            db.create_all()

        print("✅ PostgreSQL tables created successfully!")
        print("   Your app is ready for production use.")
        return True

    print(f"📂 Source: SQLite at {sqlite_path}")
    print(f"📂 Target: PostgreSQL at {postgres_url[:50]}...")
    print("")

    # Read from SQLite
    print("🔍 Reading SQLite data...")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row
    cursor = sqlite_conn.cursor()

    try:
        users = cursor.execute("SELECT * FROM user").fetchall()
        conversations = cursor.execute("SELECT * FROM conversation").fetchall()
        messages = cursor.execute("SELECT * FROM message").fetchall()
    except sqlite3.OperationalError as e:
        print(f"⚠️  SQLite read error: {e}")
        print("   The SQLite database may be empty or have a different schema.")
        users, conversations, messages = [], [], []

    print(f"   Found: {len(users)} users, {len(conversations)} conversations, {len(messages)} messages")

    if not users and not conversations and not messages:
        print("ℹ️  No data to migrate. Creating fresh PostgreSQL tables...")
        os.environ["DATABASE_URL"] = postgres_url
        os.environ["FLASK_ENV"] = "production"

        from app import app, db
        with app.app_context():
            db.create_all()

        print("✅ PostgreSQL tables created successfully!")
        sqlite_conn.close()
        return True

    # Create PostgreSQL tables and migrate data
    print("🚀 Starting migration...")
    os.environ["DATABASE_URL"] = postgres_url
    os.environ["FLASK_ENV"] = "production"

    from app import app, db
    from models import User, Conversation, Message

    with app.app_context():
        # Create tables
        db.create_all()
        print("   ✅ PostgreSQL tables created")

        # Migrate users
        migrated_users = 0
        for row in users:
            try:
                user = User(
                    id=row["id"],
                    name=row["name"],
                    email=row["email"],
                    password_hash=row["password_hash"],
                )
                # Handle datetime fields
                if row["created_at"]:
                    user.created_at = datetime.fromisoformat(str(row["created_at"]))
                if row["last_login"]:
                    user.last_login = datetime.fromisoformat(str(row["last_login"]))
                db.session.add(user)
                migrated_users += 1
            except Exception as e:
                print(f"   ⚠️  Skipping user {row['id']}: {e}")

        # Migrate conversations
        migrated_convs = 0
        for row in conversations:
            try:
                conv = Conversation(
                    id=row["id"],
                    user_id=row["user_id"],
                    title=row["title"],
                )
                if row["created_at"]:
                    conv.created_at = datetime.fromisoformat(str(row["created_at"]))
                if row["updated_at"]:
                    conv.updated_at = datetime.fromisoformat(str(row["updated_at"]))
                db.session.add(conv)
                migrated_convs += 1
            except Exception as e:
                print(f"   ⚠️  Skipping conversation {row['id']}: {e}")

        # Migrate messages
        migrated_msgs = 0
        for row in messages:
            try:
                msg = Message(
                    id=row["id"],
                    conversation_id=row["conversation_id"],
                    content=row["content"],
                    is_user=bool(row["is_user"]),
                )
                if row["timestamp"]:
                    msg.timestamp = datetime.fromisoformat(str(row["timestamp"]))
                db.session.add(msg)
                migrated_msgs += 1
            except Exception as e:
                print(f"   ⚠️  Skipping message {row['id']}: {e}")

        # Commit all changes
        try:
            db.session.commit()
            print(f"   ✅ Committed to PostgreSQL")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ Migration failed during commit: {e}")
            sqlite_conn.close()
            return False

    sqlite_conn.close()

    print("")
    print("=" * 50)
    print("✅ Migration complete!")
    print(f"   Users:         {migrated_users}/{len(users)}")
    print(f"   Conversations: {migrated_convs}/{len(conversations)}")
    print(f"   Messages:      {migrated_msgs}/{len(messages)}")
    print("=" * 50)
    print("")
    print("Next steps:")
    print("  1. Verify data in Neon dashboard: https://console.neon.tech")
    print("  2. Deploy to Vercel with DATABASE_URL set")
    print("  3. Test the deployed application")
    return True


if __name__ == "__main__":
    success = migrate_sqlite_to_postgres()
    sys.exit(0 if success else 1)
