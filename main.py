import telebot
import os
import sqlite3
import random
import threading
import time
from telebot import types
from flask import Flask
from threading import Thread
from gtts import gTTS # المكتبة المسؤولة عن الصوت

# --- 1. إعداد السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بالصوت والنص! 🎙️"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. الإعدادات ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
ADMIN_ID = 1833628326 
bot = telebot.TeleBot(TOKEN)

# --- 3. قاعدة البيانات ---
def get_db():
    conn = sqlite3.connect('almuhajir.db', check_same_thread=False)
    conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, score INTEGER DEFAULT 0)')
    conn.commit()
    return conn

db = get_db()

# --- 4. المحتوى ---
questions_pool = [
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    {"q": "كم عدد أركان الإيمان؟ ✨", "options": ["5", "6", "7", "4"], "correct": "6"},
    {"q": "ما هو أعلى مراتب الدين؟ 🌟", "options": ["الإسلام", "الإيمان", "الإحسان", "التقوى"], "correct": "الإحسان"},
    {"q": "وصلنا الكعبة المشرفة! كم شوطاً نطوف حولها؟ 🕋", "options": ["3", "5", "7", "9"], "correct": "7"},
    {"q": "ماذا نشرب من ماء مبارك داخل الحرم؟ 💧", "options": ["ماء ورد", "ماء زمزم", "ماء المطر", "عصير"], "correct": "ماء زمزم"},
    {"q": "من هو النبي الذي بنى الكعبة مع ابنه إسماعيل؟", "options": ["إبراهيم عليه السلام", "نوح عليه السلام", "موسى عليه السلام", "عيسى عليه السلام"], "correct": "إبراهيم عليه السلام"},
]

hikam_list = [
    "من علامة الاعتماد على العمل، نقصان الرجاء عند وجود الزلل.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به لنفسك.",
    "اجتهادك فيما ضمن لك، وتقصيرك فيما طلب منك، دليل على انطماس البصيرة منك.",
    "لا يكن تأخر أمد العطاء مع الإلحاح في الدعاء موجباً ليأسك.",
    "لا تصحب من لا ينهضك حاله، ولا يدلك على الله مقاله."
]

# --- 5. منطق الصوت والحذف ---

def send_question(chat_id, score, prefix=""):
    try:
        q_idx = score % len(questions_pool)
        q_data = questions_pool[q_idx]
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}") for opt in q_data['options']]
        markup.add(*btns)
        bot.send_message(chat_id, f"{prefix}\n❓ *السؤال {score + 1}:*\n\n{q_data['q']}", reply_markup=markup, parse_mode="Markdown")
    except Exception as e: print(f"Err Q: {e}")

def voice_hikma_logic(chat_id, text, score):
    """تحويل النص لصوت، إرساله، ثم الحذف بعد 10 ثواني"""
    try:
        # 1. توليد الملف الصوتي
        tts = gTTS(text=text, lang='ar')
        filename = f"hikma_{chat_id}.mp3"
        tts.save(filename)

        # 2. إرسال النص والصوت
        msg_text = bot.send_message(chat_id, f"💎 **استمع للحكمة..**\n\n« {text} »", parse_mode="Markdown")
        with open(filename, 'rb') as audio:
            msg_voice = bot.send_voice(chat_id, audio)

        # 3. الانتظار (زدنا الوقت قليلاً ليتمكن من سماع الصوت كاملاً)
        time.sleep(10)

        # 4. الحذف
        try:
            bot.delete_message(chat_id, msg_text.message_id)
            bot.delete_message(chat_id, msg_voice.message_id)
            if os.path.exists(filename): os.remove(filename) # حذف الملف من السيرفر لتوفير المساحة
        except: pass

        # 5. السؤال التالي
        send_question(chat_id, score)

    except Exception as e:
        print(f"Voice Error: {e}")
        send_question(chat_id, score) # في حال فشل الصوت، لا يتوقف البوت بل يرسل السؤال

# --- 6. معالجة التفاعلات ---

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id
    cursor = db.cursor()
    cursor.execute('SELECT score FROM users WHERE id = ?', (chat_id,))
    res = cursor.fetchone()
    score = res[0] if res else 0

    if call.data.startswith("ans|"):
        selected = call.data.split("|")[1]
        correct = questions_pool[score % len(questions_pool)]['correct']

        if selected == correct:
            bot.answer_callback_query(call.id, "✅ صحيح")
            new_score = score + 1
            cursor.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, chat_id))
            db.commit()
            
            try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            except: pass

            if new_score > 0 and new_score % 20 == 0:
                h = random.choice(hikam_list)
                # تشغيل الصوت والنص في Thread منفصل لعدم تعطيل البوت
                threading.Thread(target=voice_hikma_logic, args=(chat_id, h, new_score)).start()
            else:
                send_question(chat_id, new_score)
        else:
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مجدداً", show_alert=True)

# --- 7. أوامر المدير ---

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 إحصائيات مفصلة", "📢 إعلان")
        bot.send_message(message.chat.id, "🛠 لوحة المدير", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 إحصائيات مفصلة" and m.from_user.id == ADMIN_ID)
def stats(message):
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT name, score FROM users ORDER BY score DESC LIMIT 10')
    rows = cursor.fetchall()
    report = f"👥 الإجمالي: {total}\n\n"
    for r in rows: report += f"👤 {r[0]}: السؤال {r[1]}\n"
    bot.send_message(ADMIN_ID, report)

@bot.message_handler(func=lambda m: m.text == "📢 إعلان" and m.from_user.id == ADMIN_ID)
def broadcast(message):
    msg = bot.send_message(ADMIN_ID, "أرسل نص الإعلان:")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(message):
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users')
    users = cursor.fetchall()
    for u in users:
        try: bot.send_message(u[0], f"📢 إعلان:\n\n{message.text}")
        except: continue
    bot.send_message(ADMIN_ID, "✅ تم الإرسال.")

# --- 8. البداية ---

@bot.message_handler(commands=['start'])
def start(message):
    cursor = db.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (id, name, score) VALUES (?, ?, ?)', (message.chat.id, message.from_user.first_name, 0))
    db.commit()
    cursor.execute('SELECT score FROM users WHERE id = ?', (message.chat.id,))
    score = cursor.fetchone()[0]
    send_question(message.chat.id, score, prefix="👋 أهلاً بك في تحدي المهاجر!")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
