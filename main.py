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
        return f"*❗ Attendance Code ထည့်သွင်းထားခြင်းမရှိသေးပါ။*\n\n" \
               f"ATD code ထည့်သွင်းရန် /addatd ကိုအသုံးပြုပါ။\n\n_(Synced: {current_date})_"

    text = f"*▫️Attendance Codes (Synced: {current_date})*\n\n"
    for section, subjects in attendance_data.items():
        text += f'*Section "{section.upper()}"*\n'
        for subject, code in subjects.items():
            text += f"• {subject.capitalize()}: `{code}`\n"
        text += "\n"
    text += "ATD code တောင်းပြီးဖြည့်ဖို့မမေ့ပါနဲ့ သငခ။ ကိုယ်မေ့ရင်ကိုယ်ခံပဲ မတတ်နိုင်🗿💔"
    return text.strip()

# ===== Commands =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 မင်္ဂလာပါနေထူးနိုင်သားများ။ Attendance Bot ကနေကြိုဆိုပါတယ်။ 🤓\n\n"
        "🙌 အသုံးပြုနည်းလမ်းညွှန်များ:\n\n"
        "/addatd - Attendance Code အသစ်ထည့်ရန် အသုံးပြုပါ။\n"
        "/atd - Save ထားသော ATD code များအားကြည့်ရန် အသုံးပြုပါ။\n"
        "/clearatd - ထည့်ထားသော ATD code များအားလုံးကိုဖျက်ရန် အသုံးပြုပါ။"
    )

async def addatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text(
            "ATD code ကိုအောက်ပါ format အတိုင်းရိုက်ထည့်ပေးပါ။ 🤗🔪 \n\n /addatd [section] [subject] [code]"
        )
        return
    section = context.args[0]
    subject = context.args[1]
    code = " ".join(context.args[2:])
    store_attendance(section, subject, code)
    await update.message.reply_text(
        f"✅ Section *{section.upper()}* အတွက် *{subject.capitalize()}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။",
        parse_mode="Markdown"
    )

async def atd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")

async def clearatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()
    await update.message.reply_text("✅ ATD code အားလုံးကိုဖျက်လိုက်ပါပြီ။")

# ===== Main =====

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addatd", addatd))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("clearatd", clearatd))

    scheduler = AsyncIOScheduler()
    scheduler.add_job(reset_daily_data, "cron", hour=18, minute=30)  # UTC+6:30
    scheduler.start()

    # Optional web server (if needed)
    web_app = setup_web_server()
    runner = web.AppRunner(web_app)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    asyncio.get_event_loop().run_until_complete(site.start())

    print("✅ Bot + Web server started")
    app.run_polling()










