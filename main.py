import os
import sys
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web

# ===== Ping Server for Render =====
async def handle_ping(request):
    return web.Response(text="✅ Bot is alive!", content_type="text/plain")

def setup_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    return app

# ===== Config =====
TOKEN = os.getenv("BOT_TOKEN")

# ===== Data =====
attendance_data = {}
current_date = datetime.now().strftime("%d-%b-%Y %a")

def reset_daily_data():
    global attendance_data, current_date
    attendance_data.clear()
    current_date = datetime.now().strftime("%d-%b-%Y %a")
    print(f"[INFO] Data reset and synced at {current_date}")

def store_attendance(section, subject, code):
    if section not in attendance_data:
        attendance_data[section] = {}
    attendance_data[section][subject] = code

def format_attendance():
    if not attendance_data:
        return f"❗ Attendance Code ထည့်သွင်းထားခြင်းမရှိသေးပါ။\n\n" \
               f"*ATD code ထည့်သွင်းရန် /addatd ကိုအသုံးပြုပါ။*\n\n_(Synced: {current_date})_"

    text = f"*Attendance Codes (Synced: {current_date})*\n\n"
    for section, subjects in attendance_data.items():
        text += f'*Section "{section.upper()}"*\n'
        for subject, code in subjects.items():
            text += f"• {subject.capitalize()}: `{code}`\n"
        text += "\n"
    text += "ATD code တောင်းပြီးဖြည့်ဖို့မမေ့ပါနဲ့။"
    return text.strip()

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! I can help you store attendance codes.\n\n"
        "Commands:\n"
        "/addatd [section] [subject] [code]\n"
        "/atd (View saved ATD codes)\n"
        "/clearatd (Clear all codes)"
    )

async def addatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "Format: /addatd [section] [subject] [code]"
        )
        return
    section = context.args[0]
    subject = context.args[1]
    code = " ".join(context.args[2:])
    store_attendance(section, subject, code)
    await update.message.reply_text(
        f"✅ Section *{section.upper()}* – *{subject.capitalize()}* code saved.",
        parse_mode="Markdown"
    )

async def atd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")

async def clearatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()
    await update.message.reply_text("✅ All ATD codes cleared.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Message from {update.effective_user.username}: {update.message.text}")

# ===== Main =====
async def main():
    # Telegram app
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addatd", addatd))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("clearatd", clearatd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_data, "cron", hour=18, minute=30)  # Myanmar midnight (UTC+6:30)
    scheduler.start()

    # Web server for Render
    web_app = setup_web_server()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    await site.start()

    print("✅ Bot + Web server started")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
