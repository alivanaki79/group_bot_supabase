import os
import time
import threading
import requests
from datetime import datetime
from supabase import create_client, Client
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def check_subscription(group_id: int) -> bool:
    try:
        response = supabase.table("groups").select("*").eq("group_id", group_id).single().execute()
        data = response.data
        if not data:
            return False
        expire_date = datetime.strptime(data["expire_date"], "%Y-%m-%d")
        return expire_date >= datetime.now()
    except Exception:
        return False

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    group_id = update.message.chat.id
    if not await check_subscription(group_id):
        await update.message.reply_text("⛔ این گروه اشتراک فعال ندارد.")
        return
    for user in update.message.new_chat_members:
        await update.message.reply_text(f"🎉 خوش آمدی {user.full_name}!")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    group_id = update.message.chat.id
    if not await check_subscription(group_id):
        await update.message.reply_text("❌ اشتراک این گروه به پایان رسیده است.")
        return
    await update.message.reply_text("✅ ربات مدیریت گروه فعال است.")

app = Flask(__name__)
@app.route("/")
def ping():
    return "Bot is alive", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def start_pinger():
    def ping_forever():
        while True:
            try:
                requests.get("https://YOUR-RENDER-URL.onrender.com")
            except:
                pass
            time.sleep(300)
    threading.Thread(target=ping_forever).start()

def main():
    start_pinger()
    threading.Thread(target=run_flask).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.run_polling()

if __name__ == "__main__":
    main()
