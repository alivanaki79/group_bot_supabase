import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, ChatPermissions
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("RENDER_EXTERNAL_URL")  # این آدرس از تنظیمات Render گرفته میشه
BAD_WORDS = ["بد", "فحش", "زشت"]

app = FastAPI()
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

# هندلر پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if "سلام" in text:
        await update.message.reply_text("بله 👋")
    if "http" in text or "https" in text:
        await update.message.delete()
    for word in BAD_WORDS:
        if word in text:
            await update.message.delete()
            break

# خوش‌آمدگویی
async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f"سلام {member.full_name} خوش اومدی 👋")

# بررسی ادمین بودن
async def is_admin(update: Update) -> bool:
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]

# دستور بن
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if context.args:
        username = context.args[0].replace("@", "")
        for member in await update.effective_chat.get_administrators():
            if member.user.username == username:
                await update.message.reply_text("کاربر ادمینه و نمی‌تونم بن کنم")
                return
        await update.effective_chat.ban_member(
            await context.bot.get_chat_member(update.effective_chat.id, username)
        )
        await update.message.reply_text("کاربر بن شد.")

# دستور سکوت
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if context.args:
        username = context.args[0].replace("@", "")
        await update.effective_chat.restrict_member(
            await context.bot.get_chat_member(update.effective_chat.id, username),
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text("کاربر ساکت شد.")

# افزودن هندلرها
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("mute", mute))

@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.bot.set_webhook(f"{APP_URL}/webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.stop()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return JSONResponse(content={"status": "ok"})

@app.get("/")
async def root():
    return {"status": "running"}
