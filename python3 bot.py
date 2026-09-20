import telebot
import sqlite3
from datetime import datetime

BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 914679628

bot = telebot.TeleBot(BOT_TOKEN)

# Database
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    joined_at TEXT
)
""")
conn.commit()


# /start
@bot.message_handler(commands=["start"])
def start(message):
    user = message.from_user

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (user_id, username, joined_at)
        VALUES (?, ?, ?)
    """, (
        user.id,
        user.username or "",
        datetime.now().isoformat()
    ))

    conn.commit()

    bot.reply_to(message, "Welcome! ✅")


# /stats — Admin only
@bot.message_handler(commands=["stats"])
def stats(message):

    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "Access denied.")
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    month = datetime.now().strftime("%Y-%m")

    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE joined_at LIKE ?",
        (month + "%",)
    )
    monthly = cursor.fetchone()[0]

    bot.reply_to(
        message,
        f"📊 Bot Statistics\n\n"
        f"Total users: {total}\n"
        f"This month: {monthly}"
    )


bot.infinity_polling()
