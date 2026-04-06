import telebot
import os
import sqlite3
import random
import threading
import time
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعداد السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح! 🚀"
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

# --- 4. محتوى الأسئلة والحكم ---
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

# --- 5. منطق اللعب ---

def send_question(chat_id, score, prefix=""):
    try:
        q_idx = score % len(questions_pool)
        q_data = questions_pool[q_idx]
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}") for opt in q_data['options']]
        markup.add(*btns)
        bot.send_message(chat_id, f"{prefix}\n❓ *السؤال {score + 1}:*\n\n{q_data['q']}", reply_markup=markup, parse_mode="Markdown")
    except Exception as e: print(f"Err Q: {e}")

def handle_hikma_timer(chat_id, msg_id, score):
    time.sleep(7)
    try:
        bot.delete_message(chat_id, msg_id)
    except: pass
    send_question(chat_id, score)

# --- 6. معالجة الرسائل والأزرار ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
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
                msg = bot.send_message(chat_id, f"💎 *حكمة المحطة ({new_score}):*\n\n« {h} »\n\n_(تنتقل للسؤال تلقائياً بعد 7 ثوانٍ)_", parse_mode="Markdown")
                threading.Thread(target=handle_hikma_timer, args=(chat_id, msg.message_id, new_score)).start()
            else:
                send_question(chat_id, new_score)
        else:
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مجدداً", show_alert=True)

# --- 7. أوامر المدير ---

@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 الإحصائيات", "📢 إعلان")
        bot.send_message(message.chat.id, "🛠 لوحة المدير", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 الإحصائيات" and m.from_user.id == ADMIN_ID)
def stats(message):
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    bot.send_message(ADMIN_ID, f"👥 عدد المشتركين: {count}")

@bot.message_handler(func=lambda m: m.text == "📢 إعلان" and m.from_user.id == ADMIN_ID)
def ask_broadcast(message):
    msg = bot.send_message(ADMIN_ID, "📝 أرسل نص الإعلان الآن:")
    bot.register_next_step_handler(msg, send_broadcast)

def send_broadcast(message):
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users')
    rows = cursor.fetchall()
    count = 0
    for row in rows:
        try:
            bot.send_message(row[0], f"📢 *تنبيه من الإدارة:*\n\n{message.text}", parse_mode="Markdown")
            count += 1
            time.sleep(0.1) # لمنع حظر البوت
        except: continue
    bot.send_message(ADMIN_ID, f"✅ تم الإرسال إلى {count} مستخدم.")

# --- 8. التشغيل ---

@bot.message_handler(commands=['start'])
def start(message):
    cursor = db.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (id, name, score) VALUES (?, ?, ?)', (message.chat.id, message.from_user.first_name, 0))
    db.commit()
    cursor.execute('SELECT score FROM users WHERE id = ?', (message.chat.id,))
    score = cursor.fetchone()[0]
    send_question(message.chat.id, score, prefix=f"👋 أهلاً بك مجدداً {message.from_user.first_name}!")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling(timeout=60)
        
