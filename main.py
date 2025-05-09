import os
import re
import threading
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from fastapi import FastAPI
import uvicorn

# لیست کلمات ممنوعه
BAD_WORDS = ['بد', 'فحش', 'کلمه_زشت']  # ← این لیست رو با کلمات واقعی جایگزین کن

# ربات
async def handle_hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "سلام" in update.message.text.lower():
        await update.message.reply_text("بله 👋")

async def remove_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if re.search(r'https?://', update.message.text):
        try:
            await update.message.delete()
        except Exception as e:
            print("خطا در حذف لینک:", e)

async def remove_bad_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if any(bad_word in text for bad_word in BAD_WORDS):
        try:
            await update.message.delete()
            print(f"حذف پیام حاوی کلمات بد: {text}")
        except Exception as e:
            print("خطا در حذف پیام بد:", e)

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("فقط ادمین‌ها می‌تونن بن کنن.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("استفاده: /ban @username")
        return

    username = context.args[0].lstrip("@")
    chat = update.effective_chat

    members = await chat.get_administrators()
    for member in members:
        if member.user.username == username:
            await update.message.reply_text("نمی‌تونم ادمین رو بن کنم.")
            return

    try:
        all_members = await chat.get_administrators()
        for admin in all_members:
            if admin.user.username == username:
                return
        await context.bot.ban_chat_member(chat.id, await get_user_id_by_username(context, chat.id, username))
        await update.message.reply_text(f"{username} بن شد ✅")
    except Exception as e:
        await update.message.reply_text("خطا در بن کاربر.")
        print(e)

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update):
        await update.message.reply_text("فقط ادمین‌ها می‌تونن سکوت بدن.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("استفاده: /mute @username")
        return

    username = context.args[0].lstrip("@")
    try:
        user_id = await get_user_id_by_username(context, update.effective_chat.id, username)
        await context.bot.restrict_chat_member(
            update.effective_chat.id,
            user_id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text(f"{username} ساکت شد 🔇")
    except Exception as e:
        await update.message.reply_text("خطا در سکوت کاربر.")
        print(e)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for user in update.message.new_chat_members:
        await update.message.reply_text(f"سلام {user.first_name} عزیز، خوش اومدی 🌟")

# ابزار کمکی
async def is_admin(update: Update):
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]

async def get_user_id_by_username(context, chat_id, username):
    # فقط برای گروه‌هایی که کاربر توش اخیراً فعال بوده کار می‌کنه
    updates = await context.bot.get_chat_administrators(chat_id)
    for member in updates:
        if member.user.username == username:
            return member.user.id
    raise Exception("کاربر پیدا نشد")

# FastAPI برای بیدار نگه داشتن
app = FastAPI()

@app.get("/ping")
def ping():
    return {"message": "pong"}

@app.get("/")
def root():
    return {"status": "Bot is running!"}

def start_bot():
    TOKEN = os.getenv("BOT_TOKEN")
    app_telegram = ApplicationBuilder().token(TOKEN).build()

    app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_hello))
    app_telegram.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'https?://'), remove_links))
    app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), remove_bad_words))
    app_telegram.add_handler(CommandHandler("ban", ban_user))
    app_telegram.add_handler(CommandHandler("mute", mute_user))
    app_telegram.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))

    app_telegram.run_polling()

# اجرای همزمان FastAPI و Telegram Bot
if __name__ == "__main__":
    if os.getenv("RENDER") == "1":
        threading.Thread(target=start_bot).start()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        start_bot()
