import asyncio
import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
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
        user = context.args[0].replace("@", "")
        chat = update.effective_chat
        await chat.ban_member(await chat.get_member(user).user.id)
        await update.message.reply_text("کاربر بن شد")

# دستور سکوت
async def mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if context.args:
        user = context.args[0].replace("@", "")
        chat = update.effective_chat
        await chat.restrict_member(
            await chat.get_member(user).user.id,
            ChatPermissions(can_send_messages=False)
        )
        await update.message.reply_text("کاربر ساکت شد")

# افزودن هندلرها
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
bot_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("mute", mute))

@app.get("/")
async def root():
    return {"status": "Bot is running"}

# ⛓️ Lifespan برای اجرای ربات در FastAPI
@app.on_event("startup")
async def on_startup():
    await bot_app.initialize()
    await bot_app.start()
    asyncio.create_task(bot_app.updater.start_polling())

@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.updater.stop()
    await bot_app.stop()
    await bot_app.shutdown()

# اجرای FastAPI روی پورت مناسب رندر
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
