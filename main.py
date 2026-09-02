import os

from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, _updater, CallbackQueryHandler, ConversationHandler  # New
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.request import HTTPXRequest #temp
import random

# ===== Config =====
TOKEN = os.getenv("BOT_TOKEN")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_FILE = os.path.join(BASE_DIR, "IGusers.json")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

#For testing only
# TOKEN = "8956211083:AAFi7ykxGbGRt50A-ute8-EJ0hlJWXbe2_w" #need to edit
# ADMIN_ID = 5069582224 #added
# USERS_FILE = "IGusers.json"


mentionData = ["သူငယ်ချင်းလေး", "သူငယ်ချင်းလေး ဘာလုပ်", "သငခ ခေါ်နေတယ်လေ", "သငခ ကအဲ့လိုပေါ့ ရပါတယ် သိလိုက်ပါပြီ", "သငခရေ လာလို့", "သငခ စိတ်ကောက်နေတာလား",
               "သငခ ကဖိတ်ဖရန့်ကြီးပဲ", "သငခ ကရှယ်ချေတယ်နော်", "သူငယ်ချင်းရေးးးးးးးးးးးးးးးးးးးးးးးးးးးးး", "ချစ်သငခလေးးးးးးးးး", "သငခ ကငြိုငြင်တာလား မန်းရှင်းနေတယ်လေ",
               "သငခ တမာရွက်စားပေးရတယ်", "mingalar pr chingu", "annyeonn", "what's uppp", "dude where are u", "yoo my friend", "yoooooo",
               "သငခ ကစိတ်ဓာတ်ပဲ", "ကောက်ပါနဲ့ကောက်ပါနဲ့ ဟိုးစတော့ကောက်ပါနဲ့", "သငခရေ ထမင်းဝအောင်စားထား", "သငခ ရေငုတ်နေတာလား", "သငခ ဂူအောင်းနေတာလား",
               "သငခ ကအဖက်မလုပ်ဘူးပေါ့ ရပါတယ်", "သငခ သိလား။ သငခ မသိပါဘူး။ သငခ ကချေဖို့ပဲသိတာ။", "Hii Fake Frienddddd", "dude what u doin", "Konichiwaa"]

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
    data[user_id] = user_data
    save_users_data(data)

async def handle_message(update, context):
    save_user_info(update.effective_user)

async def chatid(update, context):
    await update.message.reply_text(f"This chat ID: {update.effective_chat.id}")

def getRandomPhrase():
    num = random.randint(0,len(mentionData)-1)
    return mentionData[num]

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
        elif len(context.args) >= 3 and len(context.args[2]) > 175:
            await update.message.reply_text(text="❌ Mention content ကိုအရှည်ကြီးမရေးကြပါနဲ့ တောင်းပန်ပါတယ်။ ဖင်ယားတာလေးတွေလျှော့")
            return
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

async def mention_everyone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatName = update.effective_user.first_name
    mention_content = ""

    if context.args:
        mention_content = context.args[0]
        if len(context.args) > 1:
            for i in range(1, len(context.args)):
                mention_content += f" {context.args[i]}"
        if len(mention_content) >= 175:
            await update.message.reply_text(
                text="❌ Mention content ကိုအရှည်ကြီးမရေးကြပါနဲ့ တောင်းပန်ပါတယ်။ ဖင်ယားတာလေးတွေလျှော့")
            return

    else:
        mention_content = f"{chatName} is calling you guys ❗️"

    data = load_users_data()
    user_id = []
    user_name = []

    for userID in data:
        user_id.append(userID)
    for userName in data.values():
        firstNAME = userName.get("first_name")
        lastNAME = userName.get("last_name")
        full_name = f"{firstNAME} {lastNAME}"
        user_name.append(full_name)

    # Pretend we pulled this from your JSON file for this specific chat
    saved_users = []
    for i in range(len(user_id)):
        saved_users.append({"id": f"{user_id[i]}", "name": f"{user_name[i]}"})

    if not saved_users:
        await update.message.reply_text("Ain't nobody saved in my database yet 😭")
        return

    mentions = []
    for user in saved_users:
        # This magic format pings them EVEN IF they don't have a username 🙏
        mention_text = f"[{user['name']}](tg://user?id={user['id']})"
        mentions.append(mention_text)

    # Split into chunks of 5 so Telegram doesn't block the notifications
    chunk_size = 5
    for i in range(0, len(mentions), chunk_size):
        chunk = mentions[i:i + chunk_size]
        text_to_send = " ".join(chunk)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{mention_content}\n\n{text_to_send}",
            parse_mode="Markdown"
        )


if __name__ == "__main__":
    request = HTTPXRequest(connect_timeout=20.0, read_timeout=20.0)  # NEW
    app = ApplicationBuilder().token(TOKEN).request(request).build()

    app.add_handler(CommandHandler("call", mention))
    app.add_handler(CommandHandler("callall", mention_everyone))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Bot + Web server started")
    app.run_polling()
