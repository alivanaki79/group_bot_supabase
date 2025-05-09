import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from telegram import Update, ChatPermissions
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import os

# محیط
BOT_TOKEN = os.getenv("BOT_TOKEN")
BAD_WORDS = ["بد", "فحش", "زشت"]

# FastAPI
app = FastAPI()

@app.api_route("/", methods=["GET", "POST", "HEAD"])
async def root(request: Request):
    return JSONResponse(content={"status": "Bot is running!"})

# ربات
bot_app = ApplicationBuilder().token(BOT_TOKEN).build()

async def is_admin(update: Update) -> bool:
    member = await update.effective_chat.get_member(update.effective_user.id)
    return member.status in ["administrator", "creator"]

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

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        await update.message.reply_text(f"سلام {member.full_name} خوش اومدی 👋")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update): return
    if context.args:
        user = context.args[0].replace("@", "")
        chat = update.effective_chat
        await chat.ban_member(await chat.get_member(user).user.id)
        await update.message.reply_text("کاربر بن شد")

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

# هندلرها
bot_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
bot_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
bot_app.add_handler(CommandHandler("ban", ban))
bot_app.add_handler(CommandHandler("mute", mute))

# اجرای async همزمان
@app.on_event("startup")
async def start_bot():
    asyncio.create_task(bot_app.run_polling())

