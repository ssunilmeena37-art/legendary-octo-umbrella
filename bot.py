import os
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

DB_NAME = "users.db"


# -------------------------
# Render Port Server
# -------------------------

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def run_health_server():
    port = int(os.environ.get("PORT", 10000))

    server = HTTPServer(
        ("0.0.0.0", port),
        HealthHandler
    )

    print(f"Web server running on port {port}")
    server.serve_forever()


# -------------------------
# Database
# -------------------------

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            subscribed INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


def save_user(user):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
    """, (
        user.id,
        user.username,
        user.first_name
    ))

    conn.commit()
    conn.close()


# -------------------------
# Telegram Commands
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    await update.message.reply_text(
        "Welcome!\n\n"
        "Use /subscribe to subscribe.\n"
        "Use /unsubscribe to unsubscribe."
    )


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET subscribed = 1 WHERE user_id = ?",
        (user.id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text("✅ You are subscribed.")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET subscribed = 0 WHERE user_id = ?",
        (user.id,)
    )

    conn.commit()
    conn.close()

    await update.message.reply_text("❌ You are unsubscribed.")


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Admin only.")
        return

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT user_id, username, first_name
        FROM users
        WHERE subscribed = 1
        ORDER BY user_id
    """)

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("No subscribed users.")
        return

    text = f"👥 Subscribed users: {len(rows)}\n\n"

    for i, (user_id, username, first_name) in enumerate(rows, 1):
        username_text = f"@{username}" if username else "No username"

        text += (
            f"{i}. {first_name or 'Unknown'}\n"
            f"ID: {user_id}\n"
            f"Username: {username_text}\n\n"
        )

    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i + 4000])


# -------------------------
# Main
# -------------------------

def main():
    init_db()

    # Start Render web server
    threading.Thread(
        target=run_health_server,
        daemon=True
    ).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("users", users))

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
