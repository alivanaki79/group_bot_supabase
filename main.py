import os
import logging
import requests
from flask import Flask, request
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# Load from environment
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BOT_TOKEN = os.getenv("BOT_TOKEN")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# --- Supabase Functions ---
def get_group(chat_id):
    url = f"{SUPABASE_URL}/rest/v1/groups?chat_id=eq.{chat_id}&select=*"
    res = requests.get(url, headers=headers)
    return res.json()

def send_expiry_warning(application):
    url = f"{SUPABASE_URL}/rest/v1/groups?select=*"
    groups = requests.get(url, headers=headers).json()
    for group in groups:
        if group.get("expire_date"):
            from datetime import datetime, timedelta
            expire_date = datetime.strptime(group["expire_date"], "%Y-%m-%d")
            if (expire_date - datetime.utcnow()).days == 3:
                application.bot.send_message(chat_id=group["chat_id"], text="⏳ اشتراک شما ۳ روز دیگر به پایان می‌رسد.")

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات مدیریت گروه فعال شد.")

async def check_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "http" in update.message.text or "t.me" in update.message.text:
        try:
            await update.message.delete()
        except:
            pass

async def ping(context: ContextTypes.DEFAULT_TYPE):
    send_expiry_warning(context.application)

# --- Run Bot ---
app = Flask(__name__)

@app.route('/')
def home():
    return 'OK'

async def main():
    logging.basicConfig(level=logging.INFO)
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_links))
    application.job_queue.run_repeating(ping, interval=300, first=10)  # every 5 min
    await application.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
