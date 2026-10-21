import os
import time
import html
import random
import threading
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, request

# ==================== CONFIGURATION ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8822534887:AAHHA7kcKkZ__biIjxLTQvZGQ7D-3OBv3gg")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://summageacademy.github.io/tappystars/")
LOCAL_IMAGE_PATH = "tappy.png"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app-name.onrender.com

# ⚠️ ADMIN TELEGRAM ACCOUNT IDs
ADMIN_IDS = [1645648704, 6904293060]

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

# ==================== FIREBASE SETUP ====================
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"⚠️ Firebase initialization warning: {e}")

db = firestore.client() if firebase_admin._apps else None

# ==================== TRANSLATIONS & REMINDERS ====================
TRANSLATIONS = {
    "en": {
        "button": "🚀 Open TappyStars",
        "welcome": (
            "Hey <b>{name}</b>! 🔥\n\n"
            "Ready to turn taps into <b>REAL Telegram Gifts</b>?\n\n"
            "⚡ Mine coins non-stop\n"
            "🎁 Unlock Mystery Chests\n"
            "⭐ Exchange coins for Stars and redeem actual gifts\n\n"
            "Thousands of players are already climbing the leaderboard.\n"
            "Your first coins are waiting — JUMP IN NOW!"
        ),
        "fallback": "Welcome to TappyStars! Tap below to start earning.",
        "unauthorized": "Sorry, I can't help with that!",
        "reminders": [
            "🚨 <b>FREE STARS ALERT!</b>\n\nYour energy is 100% FULL and Mystery Chests are waiting! Don't let your free daily Telegram Stars expire! 🎁✨\n\n<i>Tap below to claim now!</i>",
            "⚡ <b>URGENT: LEADERBOARD BOOST!</b>\n\nOther miners are passing you right now! Grab your <b>Free Daily Reward</b> and climb back to the top before time runs out! 🔥🏆",
            "🎁 <b>YOU HAVE AN UNOPENED CHEST!</b>\n\nWe reserved a special Mystery Box for you containing Coins & Stars. Open it before it disappears! ⏳✨",
            "💰 <b>TURN COINS INTO REAL GIFTS!</b>\n\nDid you know you can cash out your coins into Telegram Stars & Real Gifts? Collect your free coins right now! 👑💎",
            "🔥 <b>DON'T MISS YOUR STREAK!</b>\n\nYour daily bonus multiplier is ready to be claimed. Log in in 5 seconds and boost your mining power! 🚀🌟"
        ]
    },
    "ru": {
        "button": "🚀 Открыть TappyStars",
        "welcome": (
            "Привет, <b>{name}</b>! 🔥\n\n"
            "Готов превращать тапы в <b>настоящие Telegram-подарки</b>?\n\n"
            "⚡ Добывай монеты без остановки\n"
            "🎁 Открывай секретные сундуки\n"
            "⭐ Обменивай монеты на Звёзды и получай реальные подарки\n\n"
            "Тысячи игроков уже штурмуют таблицу лидеров.\n"
            "Твои первые монеты уже ждут — ЗАХОДИ ПРЯМО СЕЙЧАС!"
        ),
        "fallback": "Добро пожаловать в TappyStars! Нажми ниже, чтобы начать.",
        "unauthorized": "Извините, я ничем не могу с этим помочь!",
        "reminders": [
            "🚨 <b>БЕСПЛАТНЫЕ ЗВЁЗДЫ ЖДУТ!</b>\n\nТвоя энергия на 100% ПОЛНА, а секретные сундуки готовы к открытию! Не упусти бесплатные Telegram Stars! 🎁✨\n\n<i>Жми кнопку и забирай!</i>",
            "⚡ <b>СРОЧНО: ТЕБЯ ОБГОНЯЮТ!</b>\n\nДругие майнеры поднимаются в рейтинге прямо сейчас! Забери <b>Ежедневный Бонус</b> и вернись на вершину! 🔥🏆",
            "🎁 <b>У ТЕБЯ НЕОТКРЫТЫЙ СУНДУК!</b>\n\nМы приберегли для тебя секретный ящик с Монетами и Звёздами. Открой его, пока он не сгорел! ⏳✨",
            "💰 <b>ОБМЕНЯЙ МОНЕТЫ НА GIFTS!</b>\n\nПревращай монеты в реальные Telegram Stars и Подарки! Заходи и забирай свою порцию прямо сейчас! 👑💎",
            "🔥 <b>НЕ ПОТЕРЯЙ СВОЙ БОНУС!</b>\n\nТвой ежедневный множитель наград готов. Зайди на 5 секунд и прокачай майнинг! 🚀🌟"
        ]
    },
    "uz": {
        "button": "🚀 TappyStarsni ochish",
        "welcome": (
            "Salom, <b>{name}</b>! 🔥\n\n"
            "Clicklarni <b>haqiqiy Telegram GIFTLARGA</b> aylantirishga tayyormisiz?\n\n"
            "⚡ To‘xtovsiz tanga yig‘ing\n"
            "🎁 Sirli sandiqlarni oching\n"
            "⭐ Tangalarni Yulduzlarga almashtiring va haqiqiy Telegram GIFTLAR oling\n\n"
            "Minglab o‘yinchilar allaqachon reytingda kurashmoqda.\n"
            "Birinchi tangalaringiz sizni kutmoqda — HOZIROQ KIRING!"
        ),
        "fallback": "TappyStarsga xush kelibsiz! Boshlash uchun pastdagi tugmani bosing.",
        "unauthorized": "Kechirasiz, men bu ishda yordam bera olmayman!",
        "reminders": [
            "🚨 <b>BEPUL YULDUZLARGA SHOSHILING!</b>\n\nSirli Sandiqlar sizni kutmoqda! Bepul Telegram STARS oling! 🎁✨\n\n<i>Olish uchun pastdagi tugmani bosing!</i>",
            "⚡ <b>SHOSHILING: REYTINGDA O'ZINGIZni KO'RSATING!</b>\n\nBoshqa o'yinchilar sizni quvib o'tishmoqda! <b>Kunlik Bepul STARS</b>ni oling va Clickerga qayting! 🔥🏆",
            "🎁 <b>OCHILMAGAN SANDIQINGIZ BOR!</b>\n\nSiz uchun maxsus Coins va Telegram STARS saqlangan sandiq tayyorlab qo'ydik. U yo'qolmasdan oldin oching! ⏳✨",
            "💰 <b>TANGALARNI HAQIQIY GIFTLARGA ALMASHTIRING!</b>\n\nTangalaringizni Telegram STARS va BEPUL TELEGRAM GIFTS ga aylantiring! Hoziroq kiring va Ko'proq Coins yig'ing! 👑💎",
            "🔥 <b>BONUSINGIZNI BOY BERMANG!</b>\n\nKunlik ko'paytiruvchi bonusingiz tayyor. 5 soniyaga kiring va qazib olish kuchingizni oshiring! 🚀🌟"
        ]
    }
}

def detect_lang(user) -> str:
    code = (user.language_code or "en").lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("uz"):
        return "uz"
    return "en"

def process_referral(referrer_id: str, new_user_id: str, new_user_name: str):
    if not db:
        return
    try:
        if referrer_id == new_user_id:
            return
        new_user_ref = db.collection("users").document(new_user_id)
        new_user_doc = new_user_ref.get()
        if new_user_doc.exists and new_user_doc.to_dict().get("referredBy"):
            return
        new_user_ref.set({
            "telegramId": new_user_id,
            "name": new_user_name,
            "referredBy": referrer_id,
            "referralCredited": False,
            "createdAt": firestore.SERVER_TIMESTAMP
        }, merge=True)
        print(f"🔗 Pending referral linked: User {new_user_id} was invited by {referrer_id}")
    except Exception as e:
        print(f"❌ Error processing referral: {e}")

# ==================== BROADCAST LOGIC ====================
def broadcast_reminders(force: bool = False):
    if not db:
        return 0
    sent_count = 0
    try:
        users_ref = db.collection("users")
        docs = users_ref.stream()
        now = time.time()
        two_days_seconds = 2 * 24 * 60 * 60

        for doc in docs:
            user_data = doc.to_dict()
            user_id = doc.id
            last_notif = user_data.get("lastNotificationAt", 0)

            if force or (now - last_notif >= two_days_seconds):
                lang = user_data.get("language_code", "en")
                t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
                markup = InlineKeyboardMarkup()
                markup.add(InlineKeyboardButton(text=t["button"], web_app=WebAppInfo(url=WEBAPP_URL)))
                reminder_text = random.choice(t.get("reminders", TRANSLATIONS["en"]["reminders"]))

                try:
                    if os.path.exists(LOCAL_IMAGE_PATH):
                        with open(LOCAL_IMAGE_PATH, "rb") as photo:
                            bot.send_photo(chat_id=int(user_id), photo=photo, caption=reminder_text, reply_markup=markup)
                    else:
                        bot.send_message(chat_id=int(user_id), text=reminder_text, reply_markup=markup)

                    users_ref.document(user_id).update({"lastNotificationAt": now})
                    sent_count += 1
                except Exception as ex:
                    print(f"⚠️ Failed to send reminder to {user_id}: {ex}")
                time.sleep(0.35)
    except Exception as e:
        print(f"❌ Error in broadcasting reminders: {e}")
    return sent_count

def broadcast_nft_competition():
    if not db:
        return 0, 0
    sent_count = 0
    failed_count = 0
    try:
        users_ref = db.collection("users")
        docs = users_ref.stream()
        caption = (
            "<b>🔥💎 TEKINGA NFT OLING! 💎🔥</b>\n\n"
            "<b>BU IMKONIYATNI QO'LDAN BOY BERMANG! NFT MUSOBAQADA QATNASHING!</b>\n\n"
            "<b>👑 1 O'RIN TELEGRAM NFT SOHIBIGA AYLANADI!</b>\n"
            "<b>⭐ 2 VA 3 O'RINLAR KO'PLAB TELEGRAM START YUTIB OLADI!</b>\n\n"
            "<b>VAQT O'TIB KETMOQDA! HOZIROQ MUSOBAQAGA QO'SHILING VA NFT UCHUN KURASHING! 🚀🌟</b>\n\n"
            "<b>HOZIROQ ISHTIROK ETING!</b>"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text="🚀 NFT MUSOBAQASIGA KIRISH", web_app=WebAppInfo(url=WEBAPP_URL)))
        nft_image_path = "banner.png"

        for doc in docs:
            user_id = doc.id
            try:
                if os.path.exists(nft_image_path):
                    with open(nft_image_path, "rb") as photo:
                        bot.send_photo(chat_id=int(user_id), photo=photo, caption=caption, reply_markup=markup)
                elif os.path.exists(LOCAL_IMAGE_PATH):
                    with open(LOCAL_IMAGE_PATH, "rb") as photo:
                        bot.send_photo(chat_id=int(user_id), photo=photo, caption=caption, reply_markup=markup)
                else:
                    bot.send_message(chat_id=int(user_id), text=caption, reply_markup=markup)
                sent_count += 1
            except Exception as ex:
                failed_count += 1
    except Exception as e:
        print(f"❌ Error in NFT broadcast: {e}")
    return sent_count, failed_count

# ==================== BOT COMMAND HANDLERS ====================
@bot.message_handler(commands=["automated"])
def trigger_automated_broadcast(message):
    try:
        user_id = message.from_user.id
        lang = detect_lang(message.from_user)
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        if user_id not in ADMIN_IDS:
            bot.send_message(chat_id=message.chat.id, text=t.get("unauthorized", "Sorry!"), parse_mode="HTML")
            return

        bot.send_message(chat_id=message.chat.id, text="🚀 <b>Starting automated broadcast...</b>", parse_mode="HTML")
        def run_broadcast():
            count = broadcast_reminders(force=False)
            try:
                bot.send_message(chat_id=message.chat.id, text=f"✅ <b>Completed!</b> Sent to <b>{count}</b> users.", parse_mode="HTML")
            except Exception:
                pass
        threading.Thread(target=run_broadcast, daemon=True).start()
    except Exception as e:
        print(f"❌ /automated error: {e}")

@bot.message_handler(commands=["nft"])
def send_nft_competition(message):
    try:
        user_id = message.from_user.id
        lang = detect_lang(message.from_user)
        t = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
        if user_id not in ADMIN_IDS:
            bot.send_message(chat_id=message.chat.id, text=t.get("unauthorized", "Sorry!"), parse_mode="HTML")
            return

        bot.send_message(chat_id=message.chat.id, text="🚀 <b>Starting NFT broadcast...</b>", parse_mode="HTML")
        def run_nft_broadcast():
            sent, failed = broadcast_nft_competition()
            try:
                bot.send_message(chat_id=message.chat.id, text=f"✅ <b>NFT Broadcast Completed!</b> Sent: {sent}, Failed: {failed}", parse_mode="HTML")
            except Exception:
                pass
        threading.Thread(target=run_nft_broadcast, daemon=True).start()
    except Exception as e:
        print(f"❌ /nft error: {e}")

@bot.message_handler(commands=["start"])
def send_welcome(message):
    try:
        lang = detect_lang(message.from_user)
        t = TRANSLATIONS[lang]
        user_id = str(message.from_user.id)
        safe_name = html.escape(message.from_user.first_name or "Explorer")

        if db:
            try:
                db.collection("users").document(user_id).set({"language_code": lang}, merge=True)
            except Exception:
                pass

        text_parts = message.text.split()
        if len(text_parts) > 1 and text_parts[1].startswith("ref_"):
            referrer_id = text_parts[1].replace("ref_", "")
            if referrer_id:
                threading.Thread(target=process_referral, args=(referrer_id, user_id, message.from_user.first_name or "Miner"), daemon=True).start()

        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton(text=t["button"], web_app=WebAppInfo(url=WEBAPP_URL)))
        welcome_text = t["welcome"].format(name=safe_name)

        if os.path.exists(LOCAL_IMAGE_PATH):
            with open(LOCAL_IMAGE_PATH, "rb") as photo:
                bot.send_photo(chat_id=message.chat.id, photo=photo, caption=welcome_text, reply_markup=markup)
        else:
            bot.send_message(chat_id=message.chat.id, text=welcome_text, reply_markup=markup)
    except Exception as e:
        print(f"❌ /start error: {e}")

# ==================== FLASK WEBHOOK ROUTES ====================
@app.route("/", methods=["GET"])
def index():
    return "TappyStars Bot Webhook Server is active!", 200

@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

# ==================== SETUP & STARTUP ====================
if __name__ == "__main__":
    if WEBHOOK_URL:
        bot.remove_webhook()
        time.sleep(0.5)
        bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
        print(f"🌐 Webhook set to: {WEBHOOK_URL}/{BOT_TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
