from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# ========== CONFIG ==========
import os
BOT_TOKEN = os.getenv("8497434188:AAEfxxO-4NRoGZsFtiKsOHl8QsE0ot2-goM") # Replace with your actual token
current_date = datetime.now().strftime("%Y-%m-%d")

# ========== DATA STORAGE ==========
attendance_data = {}

# ========== HELPERS ==========
def store_attendance(section, subject, code):
    if section not in attendance_data:
        attendance_data[section] = {}
    attendance_data[section][subject] = code

def format_attendance():
    if not attendance_data:
        return f"*❗ No attendance codes yet.*\n_(Synced: {current_date})_"

    text = f"*Attendance Codes (Synced: {current_date})*\n\n"
    for section, subjects in attendance_data.items():
        text += f'*Section "{section.upper()}"*\n'
        for subject, code in subjects.items():
            text += f"• {subject.capitalize()}: `{code}`\n"
        text += "\n"
    return text.strip()

# ========== COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! I can help you store attendance codes.\n\n"
        "Commands:\n"
        "/add_attendance [section] [subject] [code]\n"
        "/show_attendance"
    )

async def add_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /add_attendance [section] [subject] [code]")
        return

    section = context.args[0]
    subject = context.args[1]
    code = " ".join(context.args[2:])
    store_attendance(section, subject, code)
    await update.message.reply_text(
        f"✅ Code saved for *{subject.capitalize()}* in section *{section.upper()}*.",
        parse_mode="Markdown"
    )

async def show_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")

# Store attendance in memory
attendance_data = {}

# /clear_attendance command
async def clear_attendance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    attendance_data.clear()
    await update.message.reply_text(
        "✅ All attendance codes have been cleared."
    )

# ========== MAIN ==========
if __name__ == "__main__":
    app = ApplicationBuilder().token("8497434188:AAEfxxO-4NRoGZsFtiKsOHl8QsE0ot2-goM").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add_attendance", add_attendance))
    app.add_handler(CommandHandler("show_attendance", show_attendance))
    app.add_handler(CommandHandler("clear_attendance", clear_attendance))

    print("✅ Attendance Bot is running...")
    app.run_polling()
