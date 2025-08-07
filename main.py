from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# ========== CONFIG ==========
import os
TOKEN = os.getenv("BOT_TOKEN")
current_date = datetime.now().strftime("%d-%b-%Y %a")

# ========== DATA STORAGE ==========
attendance_data = {}

# ========== HELPERS ==========
def store_attendance(section, subject, code):
    if section not in attendance_data:
        attendance_data[section] = {}
    attendance_data[section][subject] = code

def format_attendance():
    if not attendance_data:
        return f"❗ Attendance Code ထည့်သွင်းထားခြင်းမရှိသေးပါ။*\n\n*ATD code ထည့်သွင်းရင် /addatd ကိုအသုံးပြုပါ။\n\n_(Synced: {current_date})_"

    text = f"*Attendance Codes (Synced: {current_date})*\n\n"
    for section, subjects in attendance_data.items():
        text += f'*Section "{section.upper()}"*\n'
        for subject, code in subjects.items():
            text += f"• {subject.capitalize()}: `{code}`\n\n"
    text += "\n ATD code တောင်းပြီးဖြည့်ဖို့မမေ့ပါနဲ့ သငခ။ ကိုယ်မေ့ရင်ကိုယ်ခံပဲ မတတ်နိုင် ;-;"
    return text.strip()


# ========== COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! မင်္ဂလာပါ။ Konichiwa! \n\n I can help you store attendance codes.\n\n"
        "Commands:\n"
        "/addatd [section] [subject] [code]\n"
        "/atd (To view saved ATD codes)"
    )

async def addatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("ATD code ကိုအောက်က format အတိုင်းရိုက်ထည့်ပေးပါ။ \n\n /addatd [section] [subject] [code]")
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

# Store attendance in memory
attendance_data = {}

# /clearatd command
async def clearatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()
    await update.message.reply_text(
        "✅ ATD code အားလုံးကိုဖျက်လိုက်ပါပြီ။"
    )

# ========== MAIN ==========
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addatd", addatd))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("clearatd", clearatd))

    print("✅ Attendance Bot is running...")
    app.run_polling()






