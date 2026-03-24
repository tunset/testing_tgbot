import os
import sys
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, _updater, CallbackQueryHandler #New
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiohttp import web
import json #NEW
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup #NEW
from telegram.request import HTTPXRequest #temp

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
ADMIN_ID = int(os.getenv("ADMIN_ID")) 
VPN_PLAN_FILE = "vpn_plan.json" #NEW
VPN_USER_FILE = "vpn_users.json" #NEW

# ===== Data =====
attendance_data = {}
current_date = datetime.now().strftime("%d-%b-%Y %a")
current_time = datetime.now().strftime("%I:%M:%S %p")
VPN_user = [] #NEW
VPN_plan = [] #NEW
VPNimg = "AgACAgUAAxkBAAID-mmKAAEB3Vd6wswVzf17c-PUUWz19QAC3Q5rG7bwUFTlrVDdl_nTYgEAAwIAA3kAAzoE" #Replaced


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


async def send_reminder(app):
    text = f"""*🚨ATD Reminder for those who forgot❗️*

⚠️DO NOT FORGET TO TAKE ATTENDANCE⚠️
Attendance ဖြည့်ဖို့မမေ့ကြပါနဲ့။ ကိုယ်မေ့ရင်ကိုယ်ပဲခံရမှာပါသငခတို့ 🥰

💠 /atd ကိုနှိပ်ပြီးယနေ့အတွက် ATD codes များကိုရယူနိုင်ပါတယ်။

💠 [Take ATD](https://pathfinder-mm.org/portal/office/login/index.php) ကိုနှိပ်၍ ATD သွားဖြည့်နိုင်ပါတယ်။

_(Reminded at {get_time()})_"""

    
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

# === VPN Function === 
async def vpn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    userID = update.effective_user.id
    # Get the type of the chat
    chat_type = update.effective_chat.type
    price = round(int(VPN_plan[0]) / 3, -2) + 200
    key = VPN_plan[4]

    # work in a group
    if chat_type in ["group", "supergroup"]:
        if VPN_plan:
            url = "https://t.me/nhn_stdhelper_beta_bot?text=/vpn"
            keyboard = []
            text = f"*{VPN_plan[5]} VPN*\n\n*▫️Ongoing plan*\n- {VPN_plan[0]} Ks: {VPN_plan[1]} Expire on {VPN_plan[2]} {VPN_plan[3]}(Limit to 3 people)\n\nIndividual Fee: {price}Ks (Bot fee Included)\n\n👥 Currently Shared with {len(VPN_user)} users\n\n"
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
                text = f"*{VPN_plan[5]} VPN*\n\n*▫️Ongoing plan*\n- {VPN_plan[0]} Ks: {VPN_plan[1]} Expire on {VPN_plan[2]} {VPN_plan[3]}(Limit to 3 people)\n\nIndividual Fee: {price}Ks (Bot fee Included)\n\n👥 Currently Shared with {len(VPN_user)} users\n\n"
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
    price = round(int(VPN_plan[0]) / 3, -2) + 200

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



async def atd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    save_user_info(update.effective_user) #NEW
    text = format_attendance()
    await update.message.reply_text(text, parse_mode="Markdown")



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



async def handle_message(update, context):
    save_user_info(update.effective_user)

# ===== Main =====


if __name__ == "__main__":
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0) 
    app = ApplicationBuilder().token(TOKEN).request(request).build() 
    load_vpn_data() 

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addatd", addatd))
    app.add_handler(CommandHandler("atd", atd))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("clearatd", clearatd))
    app.add_handler(CommandHandler("broadcast", broadcast))  
    app.add_handler(CommandHandler("vpn", vpn))  
    app.add_handler(CommandHandler("addvpn", add_vpn))  
    app.add_handler(CommandHandler("addvpnuser", add_vpn_user))  
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_ss)) 
    app.add_handler(CallbackQueryHandler(handle_callback)) 

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









