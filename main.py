import os
import sys
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, _updater
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
import json #NEW

# ===== Ping Server for Render =====
async def handle_ping(request):
    return web.Response(text="✅ Bot is alive!", content_type="text/plain")


def setup_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    return app


# ===== Config =====
TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #NEW
USERS_FILE = os.path.join(BASE_DIR, "users.json") #NEW
ADMIN_ID = int(os.getenv("ADMIN_ID")) #NEW

# ===== Data =====
attendance_data = {}
current_date = datetime.now().strftime("%d-%b-%Y %a")
current_time = datetime.now().strftime("%I:%M:%S %p")

#NEW
#To save user info to JSON File
def save_user_info(user):
    user_id = str(user.id)

    data = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

    data[user_id] = {
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    }

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


#NEW
#For getting user ID from JSON File
def get_userid():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_time():
    return datetime.now().strftime("%I:%M:%S %p")


def reset_daily_data():
    global attendance_data, current_date
    attendance_data.clear()
    current_date = datetime.now().strftime("%d-%b-%Y %a")

#Edited partially
async def send_reminder(app):
    text = f"""*🚨ATD Reminder for those who forgot❗️*

⚠️DO NOT FORGET TO TAKE ATTENDANCE⚠️
Attendance ဖြည့်ဖို့မမေ့ကြပါနဲ့။ ကိုယ်မေ့ရင်ကိုယ်ပဲခံရမှာပါသငခတို့ 🥰

💠 /atd ကိုနှိပ်ပြီးယနေ့အတွက် ATD codes များကိုရယူနိုင်ပါတယ်။

💠 [Take ATD](https://pathfinder-mm.org/portal/office/login/index.php) ကိုနှိပ်၍ ATD သွားဖြည့်နိုင်ပါတယ်။

_(Reminded at {get_time()})_"""

    #NEW
    success = 0
    userid = get_userid()
    for chat_id in userid.keys():
        try:
            await app.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="Markdown")
            success += 1
        except Exception as e:  # Watchout
            pass

    status = f"✅ *Sent reminders to {success} users and groups*"
    await app.bot.send_message(chat_id=ADMIN_ID, text=status, parse_mode="Markdown")
    # userid = get_userid()
    # for chat_id in userid.keys():
    #     try:
    #         await app.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="Markdown")
    #     except:
    #         pass



def store_attendance(section, subject, code):
    if section not in attendance_data:
        attendance_data[section] = {}
    attendance_data[section][subject] = code


#Added partially
def format_attendance():
    if not attendance_data:
        return f"*❗ Attendance Code ထည့်သွင်းထားခြင်းမရှိသေးပါ။*\n\n" \
               f"ATD code ထည့်သွင်းရန် /addatd ကိုအသုံးပြုပါ။\n\n_(Synced: {current_date})_"

    text = f"*▫️Attendance Codes (Requested at: {get_time()})*\n\n"
    for section, subjects in attendance_data.items():
        text += f'*Section "{section.upper()}"*\n'
        for subject, code in subjects.items():
            text += f"• {subject.capitalize()}: `{code}`\n"
        text += "\n"
    text += "ATD code တောင်းပြီးဖြည့်ဖို့မမေ့ပါနဲ့ သငခ။ ကိုယ်မေ့ရင်ကိုယ်ခံပဲ မတတ်နိုင်🗿💔\n\n"
    text += "ATD Code များဖျက်ပြီးပြင်ချင်ပါက /clearatd ကိုသုံးပါ။\n\n" #NEW
    text += f"""👉 [Take ATD Here](https://pathfinder-mm.org/portal/office/login/index.php)"""
    return text.strip()


#NEW
def valid_section(section):
    num = "1234567890"
    alpha = "BCDEFGHIJKLMNOPQRSTUVWXYZ-"
    if len(section) == 1: #2
        section = "A-0" + section
    elif len(section) == 2 and section[0] in num and section[1] in num: #02 #11
        section = "A-" + section
    #For Section "A"
    elif len(section) == 2 and section[0] == "A" and section[1] in num: #a2
        section = section[0] + "-0" + section[1]
    elif len(section) == 3 and section[0] == "A" and section[1] in num and section[2] in num: #a11
        section = section[0] + "-" + section[1:]
    elif len(section) == 3 and section[:2] == "A-" and section[2] in num: #a-2
        section = section[:2] + "0" + section[2]

    #For Others section
    elif len(section) == 2 and section[0] in alpha and section[1] in num: #b2
        section = section[0] + "-0" + section[1]
    elif len(section) == 3 and section[0] in alpha and section[1] in num and section[2] in num: #b11
        section = section[0] + "-" + section[1:]
    elif len(section) == 3 and section[0] in alpha and section[1] == "-" and section[2] in num: #b-2
        section = section[:2] + "0" + section[2]

    return section


#NEW
def valid_subject(subject):
    if subject[0] == "C":
        subject = "Chemistry"
    elif subject[0:2] == "Ma":
        subject = "Mathematics"
    elif subject[0] == "P":
        subject = "Physics"
    elif subject[0] == "S":
        subject = "Social"
    elif subject[0] == "E":
        subject = "English"
    elif subject[0:2] == "My":
        subject = "Myanmar"
    elif subject[0] == "B":
        subject = "Biology"

    return subject

# ===== Commands =====

#NEW
#Broadcasting for users and groups from admin
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ တင်ပါးမယားကြပါနဲ့။ Adm တွေပဲသုံးလို့ရတဲ့ command ပါ။ TwT")
        return

    if not update.message.reply_to_message:
        await update.message.reply_text(
            "Reply to a message with /broadcast to send it."
        )
        return

    userid = get_userid()
    source_message = update.message.reply_to_message

    success = 0
    failed = 0

    for user_id in userid.keys():
        try:
            await context.bot.copy_message(
                chat_id=int(user_id),
                from_chat_id=source_message.chat_id,
                message_id=source_message.message_id
            )
            success += 1
        except Exception as e: #Watchout
            failed += 1
            pass

    await update.message.reply_text(
        f"✅ Broadcast finished.\n\n"
        f"✔ Sent: {success}\n"
        f"❌ Failed: {failed}"
    )


async def chatid(update, context):
    await update.message.reply_text(f"This chat ID: {update.effective_chat.id}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 မင်္ဂလာပါနေထူးနိုင်သားများ။ Attendance Bot ကနေကြိုဆိုပါတယ်။ 🤓\n\n"
        "🙌 အသုံးပြုနည်းလမ်းညွှန်များ:\n\n"
        "/addatd - Attendance Code အသစ်ထည့်ရန် အသုံးပြုပါ။\n"
        "/atd - Save ထားသော ATD code များအားကြည့်ရန် အသုံးပြုပါ။\n"
        "/clearatd - ထည့်ထားသော ATD code များအားလုံးကိုဖျက်ရန် အသုံးပြုပါ။"
    )


#NEW
async def addatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_info(update.effective_user)
    if len(context.args) < 3:
        await update.message.reply_text(
            "ATD code ကိုအောက်ပါ format example အတိုင်းရိုက်ထည့်ပေးပါ။ 🤗🔪 \n\n /addatd 5 b codeee (b for Biology)"
        )
        return
    section = context.args[0].upper()
    validSection = valid_section(section)

    subject = context.args[1].capitalize()
    validSubject = valid_subject(subject)

    code = " ".join(context.args[2:]).upper()
    store_attendance(validSection, validSubject, code)
    await update.message.reply_text(
        f"✅ Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။\n\n /atd - to see ATD List",
        parse_mode="Markdown"
    )


#Added partially
async def atd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_info(update.effective_user) #NEW
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")


#Edited the whole
async def clearatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_info(update.effective_user)
    if len(context.args) < 2:
        await update.message.reply_text(
            "❗ ATD Code ကို‌အောက်ပါ Format အတိုင်းဖျက်ပေးပါ။\n\n/clearatd [Section] [Subject]"
        )
        return

    section = context.args[0].upper()
    validsection = valid_section(section)

    subject = context.args[1].capitalize()
    validsubject = valid_subject(subject)

    if validsection not in attendance_data:
        await update.message.reply_text(f"❌ Section *{validsection}* not found.", parse_mode="Markdown")
        return

    if validsubject not in attendance_data[validsection]:
        await update.message.reply_text(
            f"❌ Subject *{validsubject}* not found in section *{validsection}*.",
            parse_mode="Markdown"
        )
        return

    # Delete the subject
    del attendance_data[validsection][validsubject]

    # If section becomes empty, remove it too (optional but clean)
    if not attendance_data[validsection]:
        del attendance_data[validsection]

    await update.message.reply_text(
        f"🗑️ Section *{validsection}* အတွက် *{validsubject}* Code ကို ဖျက်သိမ်းပြီးပါပြီ။\n\n ATD List ကိုပြန်ကြည့်ရင် /atd ကိုနှိပ်ပါ။",
        parse_mode="Markdown"
    )


#NEW
async def handle_message(update, context):#added
    save_user_info(update.effective_user)

# ===== Main =====

#Added partially
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addatd", addatd))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("clearatd", clearatd))
    app.add_handler(CommandHandler("broadcast", broadcast))  #NEW
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  #NEW

    scheduler = AsyncIOScheduler()

    scheduler.add_job(reset_daily_data, "cron", hour=1, minute=11)
    scheduler.add_job(
        send_reminder,
        trigger="cron",
        day_of_week='mon-fri',
        hour=22,
        minute=40,
        args=[app]  # Pass app to the function
    )
    scheduler.start()

    # Optional web server (if needed)
    web_app = setup_web_server()
    runner = web.AppRunner(web_app)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    asyncio.get_event_loop().run_until_complete(site.start())

    print("✅ Bot + Web server started")
    app.run_polling()





