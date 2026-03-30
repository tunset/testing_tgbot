import os
import random
import sys
import asyncio
from datetime import datetime

from telegram import Update, ForceReply
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, _updater, CallbackQueryHandler, ConversationHandler  # New
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
import json #NEW
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup #NEW
from telegram.request import HTTPXRequest #temp
import random

# ===== Ping Server for Render =====
async def handle_ping(request):
    return web.Response(text="✅ Bot is alive!", content_type="text/plain")


def setup_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    return app


# ===== Config =====
TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "users.json")
reminderFile = os.path.join(BASE_DIR, "atd_reminders.json")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
VPN_PLAN_FILE = "vpn_plan.json" #NEW
VPN_USER_FILE = "vpn_users.json" #NEW

# ===== Only for testing =====
# TOKEN = "8169322933:AAFw-T485FHZrl8yI5VkSwPYwUOgSuwkgwc" #need to edit
# ADMIN_ID = 5069582224 #added
# USERS_FILE = "users.json" #added
# VPN_PLAN_FILE = "vpn_plan.json" #NEW
# VPN_USER_FILE = "vpn_users.json" #NEW
# reminderFile = "atd_reminders.json" # Where settings will live

# ===== Data =====
attendance_data = {}
current_date = datetime.now().strftime("%d-%b-%Y %a")
current_time = datetime.now().strftime("%I:%M:%S %p")
VPN_user = [] #NEW
VPN_plan = [] #NEW
VPNimg = "AgACAgUAAxkBAAID-mmKAAEB3Vd6wswVzf17c-PUUWz19QAC3Q5rG7bwUFTlrVDdl_nTYgEAAwIAA3kAAzoE" #Replaced
mentionData = ["သူငယ်ချင်းလေး", "သူငယ်ချင်းလေး ဘာလုပ်", "သငခ ခေါ်နေတယ်လေ", "သငခ ကအဲ့လိုပေါ့ ရပါတယ် သိလိုက်ပါပြီ", "သငခရေ လာလို့", "သငခ စိတ်ကောက်နေတာလား",
               "သငခ ကဖိတ်ဖရန့်ကြီးပဲ", "သငခ ကရှယ်ချေတယ်နော်", "သူငယ်ချင်းရေးးးးးးးးးးးးးးးးးးးးးးးးးးးးး", "ချစ်သငခလေးးးးးးးးး", "သငခ ကငြိုငြင်တာလား မန်းရှင်းနေတယ်လေ",
               "သငခ ကစိတ်ဓာတ်ပဲ", "ကောက်ပါနဲ့ကောက်ပါနဲ့ ဟိုးစတော့ကောက်ပါနဲ့", "သငခရေ ထမင်းဝအောင်စားထား", "သငခ ရေငုတ်နေတာလား", "သငခ ဂူအောင်းနေတာလား",
               "သငခ တမာရွက်စားပေးရတယ်", "mingalar pr chingu", "annyeonn", "what's uppp", "dude where are u", "yoo my friend", "yoooooo",
               "သငခ ကအဖက်မလုပ်ဘူးပေါ့ ရပါတယ်", "သငခ သိလား။ သငခ မသိပါဘူး။ သငခ ကချေဖို့ပဲသိတာ။", "Hii Fake Frienddddd", "dude what u doin", "Konichiwaa"]


# --- HELPER 1: LOAD SETTINGS FROM JSON ---
def load_atd_settings():
    try:
        with open(reminderFile, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default empty structure if file doesn't exist
        return {}

# --- HELPER 2: SAVE SETTINGS TO JSON ---
def save_atd_settings(data):
    with open(reminderFile, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


# ==== JSON setup for VPN ====
def load_vpn_data():
    global VPN_plan, VPN_user
    # Load VPN Plan
    if os.path.exists(VPN_PLAN_FILE):
        with open(VPN_PLAN_FILE, "r") as f:
            VPN_plan = json.load(f)
    else:
        VPN_plan = []

    # Load VPN Users
    if os.path.exists(VPN_USER_FILE):
        with open(VPN_USER_FILE, "r") as f:
            VPN_user = json.load(f)
    else:
        VPN_user = [] # Keep your default

def save_vpn_plan():
    with open(VPN_PLAN_FILE, "w") as f:
        json.dump(VPN_plan, f)

def save_vpn_users():
    with open(VPN_USER_FILE, "w") as f:
        json.dump(VPN_user, f)


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
#For atd reminder users
def save_reminder_user(user):
    user_id = str(user.id)

    data = {}
    if os.path.exists(reminderFile):
        with open(reminderFile, "r", encoding="utf-8") as f:
            data = json.load(f)

    data[user_id] = {
        "hour": 10,
        "minute": 40,
        "days": "PM"
    }
    with open(reminderFile, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    text += f"ATD Code တောင်းပြီးဖြည့်ဖို့မမေ့ပါနဲ့ 🗿💔\n\n"
    text += f"""👉 [Take ATD Here](https://pathfinder-mm.org/portal/office/login/index.php)\n\n_(Synced: {current_date})_"""
    return text.strip()


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

# === VPN Function === #NEW
async def vpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userID = update.effective_user.id
    # Get the type of the chat
    chat_type = update.effective_chat.type
    price = round(int(VPN_plan[0]) / 6, -2)
    key = VPN_plan[4]

    # work in a group
    if chat_type in ["group", "supergroup"]:
        if VPN_plan:
            url = "https://t.me/nhn_stdhelper_beta_bot?text=/vpn"
            keyboard = []
            text = f"*{VPN_plan[5]} VPN*\n\n*▫️Ongoing plan*\n- {VPN_plan[0]} Ks: {VPN_plan[1]} Expire on {VPN_plan[2]} {VPN_plan[3]}(Limit to 6 people)\n\nIndividual Fee: {price}Ks (Bot fee Included)\n\n👥 Currently Shared with {len(VPN_user)} users\n\n"
            keyboard.append([InlineKeyboardButton("💳 Subscribe VPN Plan", url=url)])

            await update.message.reply_photo(
                photo=VPNimg,
                caption=text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
    else:
        #For DMs
        if userID not in VPN_user:
            if VPN_plan:
                keyboard = []
                text = f"*{VPN_plan[5]} VPN*\n\n*▫️Ongoing plan*\n- {VPN_plan[0]} Ks: {VPN_plan[1]} Expire on {VPN_plan[2]} {VPN_plan[3]}(Limit to 6 people)\n\nIndividual Fee: {price}Ks (Bot fee Included)\n\n👥 Currently Shared with {len(VPN_user)} users\n\n"
                keyboard.append([InlineKeyboardButton("💳 Subscribe VPN Plan", callback_data=f"sub")])

                await context.bot.send_photo(
                    chat_id=userID,
                    photo=VPNimg,
                    caption=text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
        else:
            text = (
                f"💠 <b>Your {VPN_plan[5]} VPN Plan is Active Until {VPN_plan[2]} {VPN_plan[3]}</b>\n\n"
                f"<b>Plan Details</b>\n"
                f"▫️ {VPN_plan[1]} {VPN_plan[0]} Ks ({price} Ks For Each)\n"
                f"👥 Sharing with {len(VPN_user)} people\n"
                f"🔑 Key: <code>{key}</code>"
            )
            await update.message.reply_text(text=text, parse_mode="HTML")


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    userName = "@Unknown"
    if query.from_user.username:
        userName = "@" + query.from_user.username

    keyboard = []
    price = round(int(VPN_plan[0]) / 6, -2)

    if data == "sub":
        text = f"*KBZPay* - 09751336111 (Tun Set Paing)\n\nAmount to Transfer: {price} Ks\n\nIf you done transferring, Send screenshot and click '*Transferred*\n '"
        keyboard.append([InlineKeyboardButton("✅ Transferred", callback_data="done")])
        await context.bot.send_message(chat_id=user_id, text=text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data == "done":
        receipt_id = context.user_data.get("receipt_id")
        if receipt_id:
            await context.bot.send_photo(chat_id=ADMIN_ID, photo=receipt_id, caption=f"Screenshot from User: {user_id} {userName}")
            await context.bot.send_message(chat_id=user_id,
                                           text="✅ *Your Receipt has been sent to Admin*\n\nYou will get VPN key shortly after your receipt is being checked",
                                           parse_mode="Markdown")
        else:
            # If they clicked the button WITHOUT sending a photo first
            await context.bot.send_message(
                chat_id=user_id,
                text="⚠️ Please send the screenshot first, then click 'Transferred'!"
            )

async def handle_ss(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Access the 'photo' list
    photo_list = update.message.photo

    # 2. Get the last item (highest resolution)
    highest_res_photo = photo_list[-1]

    # 3. Grab the file_id
    context.user_data["receipt_id"] = highest_res_photo.file_id

async def add_vpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if len(context.args) != 6:
        await update.message.reply_text(
            "Put VPN key in format like this(4000 150GB 20 Dec)[price size(GB) date month vpnName]"
        )
        return

    price = context.args[0]
    size = context.args[1]
    day = context.args[2]
    month = context.args[3]
    key = str(context.args[4])
    name = context.args[5]

    # VPN_plan.extend([price, size, day, month, key, name])
    VPN_plan.clear()
    VPN_plan.extend([price, size, day, month, key, name])
    save_vpn_plan()  # SAVE TO JSON

    await update.message.reply_text(text=f"✅ VPN plan has been added")

async def add_vpn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        return
    userID = int(context.args[0])
    # VPN_user.append(userID)
    if userID not in VPN_user:
        VPN_user.append(userID)
        save_vpn_users()  # SAVE TO JSON
    key = VPN_plan[4]
    text = (
        f"🎉 <b>Congratulations! You've successfully subscribed to {VPN_plan[5]} VPN plan</b>\n\n"
        f"Your Plan is Active Until <b>{VPN_plan[2]} {VPN_plan[3]}</b>\n\n"
        f"Here is your key ⬇️\n"
        f"<code>{key}</code>\n"
        f"(Click to copy)"
    )

    await context.bot.send_message(chat_id=userID, text=text, parse_mode="HTML")
    await update.message.reply_text(text=f"✅ User {userID} added to subscription")


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

async def send_per_chat_reminder_callback(application: Application, chat_id: int):
    if not attendance_data:
        return
    # Copy your message text from Image 4 here
    text = f"""*🚨ATD Reminder for those who forgot❗️*

⚠️⚠️DO NOT FORGET TO TAKE ATTENDANCE⚠️⚠️\n\n({current_date})\n"""
    for section, subjects in attendance_data.items():
        text += f'*{section.upper()}* have *{len(subjects)}* class(es)\n• '
        for subject, code in subjects.items():
            text += f"*{subject.capitalize()}* "
        text += "\n\n"
    text += f"""💠 /atd ကိုနှိပ်ပြီးယနေ့အတွက် ATD codes များကိုရယူနိုင်ပါတယ်။\n\n_(Reminded at {get_time()})_"""

    try:
        # We use 'application' passed through apscheduler args
        await application.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=False  # Let them see the login link preview
        )
        await application.bot.send_message(chat_id=ADMIN_ID, text=f"✅ Successfully sent reminder to {chat_id}")
    except Exception as e:
        await application.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Failed to send reminder to {chat_id}: {e}")


# --- HELPER 3: JOB MANAGER ---
# This is the brains. It handles scheduling (Image 3) from within our handlers.
def update_scheduler_job(chat_id_str: str, settings: dict, application: Application):
    # Remove existing job if it exists to avoid duplicate alarms
    job_id = f"reminder_{chat_id_str}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

    hour = int(settings["hour"])
    if settings["days"] == "PM" and settings["hour"] != 12:
        hour = int(settings["hour"]) + 12
    elif settings["days"] == "AM" and settings["hour"] != 12:
        hour = int(settings["hour"]) - 12
    minute = int(settings["minute"])

    # Schedule the new job using 'cron'
    scheduler.add_job(
        send_per_chat_reminder_callback,
        trigger="cron",
        hour=hour,
        minute=minute,
        id=job_id, # Set fixed ID so we can find it easily
        args=[application, int(chat_id_str)] # Pass application and chat_id
    )

remind_data = 1
async def setReminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "ယခု Chat အတွက် <b>ATD reminder</b> ကိုအောက်ပါ format အတိုင်းရိုက်ထည့်ပြီး reply ပြန်ပေးပါ။\n\n<i>Format: 10 40 pm</i>"
    if len(context.args) < 3:
        await update.message.reply_text(text,reply_markup=ForceReply(selective=True, input_field_placeholder="Reminder time ကိုရိုက်ထည့်ပါ။"), parse_mode="HTML")
        return remind_data
    elif len(context.args) == 3 and not (context.args[0].isdigit() and context.args[1].isdigit() and context.args[2].isalpha()):
        await update.message.reply_text(text, reply_markup=ForceReply(selective=True, input_field_placeholder="Reminder time ကိုရိုက်ထည့်ပါ။"), parse_mode="HTML")
        return remind_data

async def handle_remind_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = str(update.effective_chat.id)
    text = update.message.text
    parts = text.split(" ")
    if len(parts) == 3 and (parts[0].isdigit() and parts[1].isdigit() and parts[2].isalpha()):
        hour = int(parts[0])
        minute = int(parts[1])
        day = parts[2].upper()

        # 3. Save to Persistent Storage
        all_settings = load_atd_settings()

        # Update this specific chat's data isolated from others
        all_settings[chatID] = {
            "hour": hour,
            "minute": minute,
            "days": day
        }
        save_atd_settings(all_settings)

        # 4. Schedule the job NOW (connecting persistence to action)
        update_scheduler_job(chatID, all_settings[chatID], context.application)

        await update.message.reply_text(
            f"✅ ယခု Chat အတွက် *ATD Reminder* ကိုနေ့စဉ် *{hour}:{minute} {day}* မှာအောင်မြင်စွာသတ်မှတ်ပြီးပါပြီ။\n\n*Note*: _The Reminder will be skipped if there are no codes in ATD list_",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "<b>ATD reminder</b> ကိုအောက်ပါ format example အတိုင်းရိုက်ထည့်ပေးပါ။ 🤗🔪\n\n<i>Format: 10 40 pm</i>",
            reply_markup=ForceReply(selective=True, input_field_placeholder="Reminder time ကိုရိုက်ထည့်ပါ။"), parse_mode="HTML"
        )
        return remind_data

# --- MAIN SETUP: STARTUP LOGIC ---
# This is a critical step user missed. On bot boot, we must load all saved jobs.
async def post_init(application: Application):
    all_settings = load_atd_settings()

    for chat_id, settings in all_settings.items():
        # Register every saved job with the scheduler
        update_scheduler_job(chat_id, settings, application)

    # Finally, start the scheduler
    scheduler.start()
    print("Scheduler loaded with existing jobs.")

ATD_data = 1
async def addatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_reminder_user(update.effective_user)
    if len(context.args) < 3:
        await update.message.reply_text(
            "<b>ATD code</b> ကိုအောက်ပါ format အတိုင်းရိုက်ထည့်ပြီး reply ပြန်ပေးပါ။\n\n<i>Format: 5 b code (b for Biology)</i>",
            reply_markup=ForceReply(selective=True, input_field_placeholder="ATD code ကိုရိုက်ထည့်ပါ။"), parse_mode="HTML"
        )
        return ATD_data

    section = context.args[0].upper()
    subject = context.args[1].capitalize()
    code = " ".join(context.args[2:]).upper()

    validSection = valid_section(section)
    validSubject = valid_subject(subject)
    store_attendance(validSection, validSubject, code)

    await update.message.reply_text(
        f"✅ Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။\n\n /atd - to see ATD List",
        parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_atd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split(" ")
    if len(parts) == 3 and parts[0].isdigit() and parts[1].isalpha() and parts[2].isalnum():
        section, subject, code = parts[0].upper(), parts[1].capitalize(), " ".join(parts[2:]).upper()
        validSection = valid_section(section)
        validSubject = valid_subject(subject)
        store_attendance(validSection, validSubject, code)

        await update.message.reply_text(
            f"✅ Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။\n\n /atd - to see ATD List",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    else:
        await update.message.reply_text(
            "<b>ATD code</b> ကိုအောက်ပါ format example အတိုင်းရိုက်ထည့်ပေးပါ။ 🤗🔪\n\n<i>Format: 5 b code (b for Biology)</i>",
            reply_markup=ForceReply(selective=True, input_field_placeholder="ATD code ကိုရိုက်ထည့်ပါ။"), parse_mode="HTML"
        )
        return ATD_data


#Added partially
async def atd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_reminder_user(update.effective_user)
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")


async def clearatd(update: Update, context: ContextTypes.DEFAULT_TYPE):
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



async def handle_message(update, context):#added
    save_user_info(update.effective_user)

#NEW
def getRandomPhrase():
    num = random.randint(0,len(mentionData)-1)
    return mentionData[num]

#NEW
async def mention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatID = update.effective_chat.id
    chat_type = update.effective_chat.type
    if chat_type in ["group", "supergroup"]:
        if len(context.args) < 2:
            await update.message.reply_text(
                text="Mention ခေါ်ရန် အောက်ပါ format example အတိုင်းအသုံးပြုပါ။\n\n/call @username 5[times] content(optional)")
            return
        elif len(context.args) == 2 and context.args[0][0] == "@" and int(context.args[1]) <= 14:
            username = context.args[0]
            times = int(context.args[1])
            for i in range(0, times):
                await app.bot.send_message(chat_id=chatID, text=f"{username} {getRandomPhrase()}")
        elif len(context.args) >= 3 and context.args[0][0] == "@" and int(context.args[1]) <= 14:
            text = ""
            for contents in context.args[2:]:
                text += contents + " "
            username = context.args[0]
            times = int(context.args[1])
            for i in range(0, times):
                await app.bot.send_message(chat_id=chatID, text=f"{username} {text}")
        elif int(context.args[1]) > 14:
            await update.message.reply_text(text="❌ တစ်ခါ mention ခေါ်တိုင်း 14 ခါထက်ကျော်ပြီးမခေါ်ပါနဲ့။ စားချင်ရာစား memory usage တော့လာမစားနဲ့(memory usage များလို့ပါ)")
            return
    else:
        await update.message.reply_text(text="❌ Mention command ကို Group chat မှာသာအသုံးပြုနိုင်ပါတယ်။")
        return

# ===== Main =====

#Added partially
if __name__ == "__main__":
    request = HTTPXRequest(connection_pool_size=100, connect_timeout=20.0, read_timeout=20.0) #NEW
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).request(request).build() #Partially Added
    load_vpn_data() #NEW
    atd_conv = ConversationHandler(
        entry_points=[CommandHandler("addatd", addatd)],
            states={ATD_data: [
            MessageHandler(
            # Combine TEXT with the REPLY filter
            filters.TEXT & filters.REPLY & ~filters.COMMAND,
            handle_atd_reply
        )
    ]}, fallbacks=[], conversation_timeout=60
    )

    reminder_conv = ConversationHandler(
        entry_points=[CommandHandler("setreminder", setReminder)],
        states={remind_data: [
            MessageHandler(filters.TEXT & filters.REPLY & ~filters.COMMAND, handle_remind_reply)
        ]}, fallbacks=[], conversation_timeout=60
    )


    app.add_handler(reminder_conv)
    app.add_handler(atd_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("clearatd", clearatd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("vpn", vpn))
    app.add_handler(CommandHandler("addvpn", add_vpn))
    app.add_handler(CommandHandler("addvpnuser", add_vpn_user))
    app.add_handler(CommandHandler("call", mention))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_ss))
    app.add_handler(CallbackQueryHandler(handle_callback))

    scheduler = AsyncIOScheduler()

    scheduler.add_job(reset_daily_data, "cron", hour=1, minute=11)

    # scheduler.start()

    # Optional web server (if needed)
    web_app = setup_web_server()
    runner = web.AppRunner(web_app)
    asyncio.get_event_loop().run_until_complete(runner.setup())
    site = web.TCPSite(runner, "0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    asyncio.get_event_loop().run_until_complete(site.start())

    print("✅ Bot + Web server started")
    app.run_polling()








