import os
import telebot
from telebot import types
import sqlite3
from flask import Flask, request

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = [7702942505]

CHANNELS = [
{"@Shein_Reward",
"@SheinRewardsGc",
  "@sheinlinks202",
  "@sheinverse22"},
  { "@W4DEXZON",
   "@sheinverse052"},

]

DB_NAME = "railway_shein.db"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        referrals INTEGER DEFAULT 0,
        credits INTEGER DEFAULT 0,
        verified INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= UTIL =================

def is_joined(user_id):
    for ch in CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🎟 Claim Reward", "💸 Invite & Earn")
    markup.row("📊 Profile", "🏆 Leaderboard")
    return markup

# ================= START =================

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

    markup = types.InlineKeyboardMarkup()
    for ch in CHANNELS:
        markup.add(types.InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch[1:]}"))
    markup.add(types.InlineKeyboardButton("✅ I Joined", callback_data="verify"))

    bot.send_message(
        message.chat.id,
        "🔥 <b>Welcome To Premium Rewards Hub</b>\n\n"
        "🎯 Complete All Steps Below To Unlock Rewards\n\n"
        "1️⃣ Join All Channels\n"
        "2️⃣ Click Verify Button\n\n"
        "💎 Start Earning Instantly!",
        reply_markup=markup
    )

# ================= VERIFY =================

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify(call):
    user_id = call.from_user.id

    if not is_joined(user_id):
        bot.answer_callback_query(call.id, "❌ Please Join All Channels First", show_alert=True)
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()

    bot.send_message(
        call.message.chat.id,
        "✅ <b>Verification Successful!</b>\n\n"
        "🚀 You Can Now Start Earning Credits!",
        reply_markup=main_menu()
    )

# ================= INVITE =================

@bot.message_handler(func=lambda m: m.text == "💸 Invite & Earn")
def invite(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT referrals, credits FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()

    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"

    bot.send_message(
        message.chat.id,
        f"💰 <b>Invite & Earn Program</b>\n\n"
        f"👥 Referrals: {data[0]}\n"
        f"💎 Credits: {data[1]}\n\n"
        f"🔗 Your Link:\n{ref_link}\n\n"
        f"⚡ 1 Invite = 1 Credit"
    )

# ================= PROFILE =================

@bot.message_handler(func=lambda m: m.text == "📊 Profile")
def profile(message):
    user_id = message.from_user.id

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT referrals, credits, verified FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()

    bot.send_message(
        message.chat.id,
        f"👤 <b>Your Profile</b>\n\n"
        f"📌 Referrals: {data[0]}\n"
        f"💎 Credits: {data[1]}\n"
        f"🔐 Status: {'Active ✅' if data[2]==1 else 'Not Verified ❌'}"
    )

# ================= LEADERBOARD =================

@bot.message_handler(func=lambda m: m.text == "🏆 Leaderboard")
def leaderboard(message):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT referrals FROM users ORDER BY referrals DESC LIMIT 5")
    rows = c.fetchall()
    conn.close()

    text = "🏆 <b>Top 5 Invitors</b>\n\n"
    for i,row in enumerate(rows):
        text += f"{i+1}. 🔥 {row[0]} Referrals\n"

    bot.send_message(message.chat.id, text)

# ================= WEBHOOK =================

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index():
    return "Bot Running 🚀"

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=os.getenv("WEBHOOK_URL"))
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
