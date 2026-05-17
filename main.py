import os
import random
import sys
import asyncio
import html
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
SOCIAL_POINTS_PER_ATD = 5
WEEKLY_WINNER_ANNOUNCE_CHAT_IDS = [-1002412292404]

# ===== Only for testing =====
# TOKEN = "8059645292:AAHylr2L6n4ZU3d8iUJk72PAaq4tjsPury8" #need to edit
# ADMIN_ID = 5069582224 #added
# USERS_FILE = "users.json" #added
# VPN_PLAN_FILE = "vpn_plan.json" #NEW
# VPN_USER_FILE = "vpn_users.json" #NEW
# reminderFile = "atd_reminders.json" # Where settings will live
# SOCIAL_POINTS_PER_ATD = 5
# WEEKLY_WINNER_ANNOUNCE_CHAT_IDS = [-1002339036511] # Add target group/chat IDs here

# ===== Data =====
attendance_data = {}
current_date = datetime.now().strftime("%d-%b-%Y %a")
current_time = datetime.now().strftime("%I:%M:%S %p")
VPN_user = [] #NEW
VPN_plan = [] #NEW
VPNimg = "AgACAgUAAxkBAAID-mmKAAEB3Vd6wswVzf17c-PUUWz19QAC3Q5rG7bwUFTlrVDdl_nTYgEAAwIAA3kAAzoE" #Replaced
mentionData = ["သူငယ်ချင်းလေး", "သူငယ်ချင်းလေး ဘာလုပ်", "သငခ ခေါ်နေတယ်လေ", "သငခ ကအဲ့လိုပေါ့ ရပါတယ် သိလိုက်ပါပြီ", "သငခရေ လာလို့", "သငခ စိတ်ကောက်နေတာလား",
               "သငခ ကဖိတ်ဖရန့်ကြီးပဲ", "သငခ ကရှယ်ချေတယ်နော်", "သူငယ်ချင်းရေးးးးးးးးးးးးးးးးးးးးးးးးးးးးး", "ချစ်သငခလေးးးးးးးးး", "သငခ ကငြိုငြင်တာလား မန်းရှင်းနေတယ်လေ",
               "သငခ တမာရွက်စားပေးရတယ်", "mingalar pr chingu", "annyeonn", "what's uppp", "dude where are u", "yoo my friend", "yoooooo",
               "သငခ ကစိတ်ဓာတ်ပဲ", "ကောက်ပါနဲ့ကောက်ပါနဲ့ ဟိုးစတော့ကောက်ပါနဲ့", "သငခရေ ထမင်းဝအောင်စားထား", "သငခ ရေငုတ်နေတာလား", "သငခ ဂူအောင်းနေတာလား",
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


def load_users_data():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users_data(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


#To save user info to JSON File
def save_user_info(user):
    user_id = str(user.id)

    data = load_users_data()
    user_data = data.get(user_id, {})

    user_data.update({
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    })
    user_data.setdefault("social_points", 0)
    user_data.setdefault("weekly_social_points", 0)
    data[user_id] = user_data

    save_users_data(data)


def add_social_points(user, points=SOCIAL_POINTS_PER_ATD):
    user_id = str(user.id)
    data = load_users_data()
    user_data = data.get(user_id, {})

    user_data.update({
        "username": user.username or "",
        "first_name": user.first_name or "",
        "last_name": user.last_name or ""
    })
    user_data["social_points"] = int(user_data.get("social_points", 0)) + points
    user_data["weekly_social_points"] = int(user_data.get("weekly_social_points", 0)) + points
    data[user_id] = user_data

    save_users_data(data)
    return user_data["social_points"]

def already_exist(section, subject, code):
    return section in attendance_data and subject in attendance_data[section] and code in attendance_data[section][subject]

def for_edit(section, subject, code):
    return section in attendance_data and subject in attendance_data[section] and code not in attendance_data[section][subject]

def should_award_social_points(section, subject):
    return section not in attendance_data or subject not in attendance_data[section]


def get_ranked_users(point_key="social_points", limit=None):
    ranked_users = []
    for user_id, user_data in get_userid().items():
        points = int(user_data.get(point_key, 0))
        if points > 0:
            ranked_users.append((user_id, user_data, points))

    ranked_users.sort(key=lambda item: item[2], reverse=True)
    if limit:
        return ranked_users[:limit]
    return ranked_users


def get_leaderboard_name(user_id, user_data):
    username = user_data.get("username", "")
    full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
    if full_name:
        return full_name
    elif username:
        return f"@{username}"

    return f"User {user_id}"

def get_leaderboard_username(user_data):
    username = user_data.get("username", "")
    return f"{username}"

def format_leaderboard(title, ranked_users):
    if not ranked_users:
        return None

    text = f"<b>{html.escape(title)}</b>\n\n"
    for index, (user_id, user_data, points) in enumerate(ranked_users, start=1):
        name = html.escape(get_leaderboard_name(user_id, user_data))
        text += f"""{index}. <a href="https://t.me/{get_leaderboard_username(user_data)}">{name}</a> - <b>{points}</b> NHN\n"""

    return text


def format_user_link(user_data):
    name = html.escape(get_leaderboard_name("", user_data))
    username = get_leaderboard_username(user_data)
    if username:
        return f"""<a href="https://t.me/{html.escape(username)}">{name}</a>"""
    return name


async def announce_weekly_winners(app):
    if not WEEKLY_WINNER_ANNOUNCE_CHAT_IDS:
        return

    top_users = get_ranked_users("weekly_social_points", 3)
    if not top_users:
        return

    winner_id, winner_data, winner_points = top_users[0]
    text = (
        "<b>🏆 Weekly Social Credit Winners</b>\n\n"
        f"🎉 Winner: {format_user_link(winner_data)} with <b>{winner_points}</b> NHN\n\n"
    )

    other_top_users = top_users[1:]
    if other_top_users:
        place_names = {2: "ဒုတိယဆု", 3: "တတိယဆု"}
        for index, (user_id, user_data, points) in enumerate(other_top_users, start=2):
            text += f"▫️<b>{place_names[index]}</b>\n{format_user_link(user_data)} with <b>{points}</b> NHN\n\n"
        text += f"<i>(Announced at {current_date})</i>"

    for chat_id in WEEKLY_WINNER_ANNOUNCE_CHAT_IDS:
        try:
            await app.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            await app.bot.send_message(chat_id=ADMIN_ID, text=f"❌ Failed to send weekly winners to {chat_id}: {e}")


async def reset_weekly_leaderboard():
    data = load_users_data()
    for user_data in data.values():
        user_data["weekly_social_points"] = 0

    save_users_data(data)

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
    return load_users_data()


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


async def legacy_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("âŒ Leaderboard command can only be used in groups.")
        return

    users = get_userid()
    ranked_users = []
    for user_id, user_data in users.items():
        points = int(user_data.get("social_points", 0))
        if points > 0:
            ranked_users.append((user_id, user_data, points))

    ranked_users.sort(key=lambda item: item[2], reverse=True)
    top_users = ranked_users[:5]

    if not top_users:
        await update.message.reply_text("No social points yet.")
        return

    text = "🏆 *Social Credit Leaderboard*\n\n"
    for index, (user_id, user_data, points) in enumerate(top_users, start=1):
        name = get_leaderboard_name(user_id, user_data)
        text += f"{index}. {name} - *{points}* points\n"

    await update.message.reply_text(text, parse_mode="Markdown")

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
            # disable_web_page_preview=False  # Let them see the login link preview
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
    should_award_points = should_award_social_points(validSection, validSubject)
    alreadyExist = already_exist(validSection, validSubject, code)
    toEdit = for_edit(validSection, validSubject, code)
    store_attendance(validSection, validSubject, code)

    if alreadyExist:
        text = f"❗️ Section *{validSection}* အတွက် *{validSubject}* Code က ATD List ထဲတွင်ရှိနှင့်ပြီးသားပါ။\n\n /atd - to see ATD List"
    elif toEdit:
        text = f"📝 Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာပြင်ဆင်ပြီးပါပြီ။\n\n /atd - to see ATD List"
    else:
        text = f"✅ Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။\n\n /atd - to see ATD List"

    if should_award_points:
        add_social_points(update.effective_user)
        text += "\n\n🎉 You Gained +5 Social Points - /mypoints to show Your Total Points"

    await update.message.reply_text(
        text=text, parse_mode="Markdown"
    )
    return ConversationHandler.END

async def handle_atd_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    parts = text.split(" ")
    if len(parts) == 3 and parts[0].isdigit() and parts[1].isalpha() and parts[2].isalnum():
        section, subject, code = parts[0].upper(), parts[1].capitalize(), " ".join(parts[2:]).upper()
        validSection = valid_section(section)
        validSubject = valid_subject(subject)
        should_award_points = should_award_social_points(validSection, validSubject)
        alreadyExist = already_exist(validSection, validSubject, code)
        toEdit = for_edit(validSection, validSubject, code)
        store_attendance(validSection, validSubject, code)

        if alreadyExist:
            text = f"❗️ Section *{validSection}* အတွက် *{validSubject}* Code က ATD List ထဲတွင်ရှိနှင့်ပြီးသားပါ။\n\n /atd - to see ATD List"
        elif toEdit:
            text = f"📝 Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာပြင်ဆင်ပြီးပါပြီ။\n\n /atd - to see ATD List"
        else:
            text = f"✅ Section *{validSection}* အတွက် *{validSubject}* Code ကိုအောင်မြင်စွာထည့်သွင်းပြီးပါပြီ။\n\n /atd - to see ATD List"

        if should_award_points:
            add_social_points(update.effective_user)
            text += "\n\n🎉 You Gained +5 Social Points - /mypoints to show Your Total Points"

        await update.message.reply_text(
            text=text,
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


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Leaderboard command ကို Group chat မှာသာအသုံးပြုနိုင်ပါတယ်။")
        return

    text = format_leaderboard("🏆 Social Credit Leaderboard", get_ranked_users("social_points", 5))
    if not text:
        await update.message.reply_text("❗️ Social Credit Points မရှိသေးပါ။")
        return

    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def weeklyleaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_type = update.effective_chat.type
    if chat_type not in ["group", "supergroup"]:
        await update.message.reply_text("❌ Weekly leaderboard command ကို Group Chat မှာသာအသုံးပြုနိုင်ပါတယ်။")
        return

    text = format_leaderboard("🏆 Weekly Social Credit Leaderboard", get_ranked_users("weekly_social_points", 5))
    if not text:
        await update.message.reply_text("No weekly social points yet.")
        return

    await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=True)


async def mypoints(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_info(update.effective_user)
    user_id = str(update.effective_user.id)
    users = get_userid()
    user_data = users.get(user_id, {})
    lifetime_points = int(user_data.get("social_points", 0))
    weekly_points = int(user_data.get("weekly_social_points", 0))

    text = (
        "🔘<b>Social Credit</b>\n\n"
        f"Name: {user_data.get('first_name')} {user_data.get('last_name')}\n"
        f"Total Points: <b>{lifetime_points} NHN</b>\n"
        f"Weekly Points: <b>{weekly_points} NHN</b>"
    )
    await update.message.reply_text(text, parse_mode="HTML")


# ===== Main =====

#Added partially
if __name__ == "__main__":
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0) #NEW
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
    app.add_handler(CommandHandler("mypoints", mypoints))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("weeklyleaderboard", weeklyleaderboard))
    app.add_handler(CommandHandler("clearatd", clearatd))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("call", mention))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    scheduler = AsyncIOScheduler()

    scheduler.add_job(reset_daily_data, "cron", hour=1, minute=11)
    scheduler.add_job(announce_weekly_winners, "cron", day_of_week="sun", hour=9, minute=0, args=[app])
    scheduler.add_job(reset_weekly_leaderboard, "cron", day_of_week="mon", hour=0, minute=0)

    # scheduler.start()

    # Optional web server (if needed)
    # web_app = setup_web_server()
    # runner = web.AppRunner(web_app)
    # asyncio.get_event_loop().run_until_complete(runner.setup())
    # site = web.TCPSite(runner, "0.0.0.0", port=int(os.environ.get("PORT", 8080)))
    # asyncio.get_event_loop().run_until_complete(site.start())

    print("✅ Bot + Web server started")
    app.run_polling()








