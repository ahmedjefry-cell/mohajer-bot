import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread

# --- إعدادات Flask لمنع البوت من النوم ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- إعدادات البوت ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 1833628326 
FINAL_SECRET_CODE = "MOHAJER-VIP-2026"

SOUND_CORRECT = "https://www.myinstants.com/media/sounds/correct.mp3"
SOUND_WRONG = "https://www.myinstants.com/media/sounds/wrong.mp3"

# --- قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect('users_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, name TEXT, score INTEGER, fails INTEGER DEFAULT 0)''')
    conn.commit()
    return conn

db_conn = init_db()

def update_user(user_id, name, score, fails=0):
    cursor = db_conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (id, name, score, fails) VALUES (?, ?, ?, ?)', (user_id, name, score, fails))
    db_conn.commit()

def get_user_data(user_id):
    cursor = db_conn.cursor()
    cursor.execute('SELECT name, score, fails FROM users WHERE id = ?', (user_id,))
    return cursor.fetchone()

# --- بنك الأسئلة (رحلة المهاجر) ---
questions_pool = [
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    {"q": "ماذا يقول المعتمر عند نية الدخول في الإحرام؟", "options": ["لبيك اللهم عمرة", "الله أكبر", "الحمد لله", "بسم الله"], "correct": "لبيك اللهم عمرة"},
    {"q": "وصلنا الكعبة المشرفة! كم شوطاً نطوف حولها؟ 🕋", "options": ["3 أشواط", "5 أشواط", "7 أشواط", "9 أشواط"], "correct": "7 أشواط"},
    {"q": "ماذا نشرب من ماء مبارك داخل الحرم؟ 💧", "options": ["ماء ورد", "ماء زمزم", "ماء المطر", "عصير"], "correct": "ماء زمزم"}
]

spiritual_breaks = ["قال رسول الله ﷺ: 'أحب الكلام إلى الله أربع: سبحان الله، والحمد لله، ولا إله إلا الله، والله أكبر'. ✨"]

def get_rank(score):
    if score >= 1000: return "سفير وكالة المهاجر الذهبي 🏆"
    return "متحدي المهاجر الصغير 👶"

def send_actual_question(chat_id, score):
    if score >= len(questions_pool):
        bot.send_message(chat_id, "أحسنت! انتظر إضافة المراحل القادمة قريباً!")
        return
    q_data = questions_pool[score]
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}|{q_data['correct']}") for opt in q_data['options']]
    markup.add(*btns)
    bot.send_message(chat_id, f"السؤال ({score + 1}):\n\n*{q_data['q']}*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    user_data = get_user_data(chat_id)
    if not user_data: return
    name, score, fails = user_data
    if call.data == "continue":
        send_actual_question(chat_id, score)
    elif call.data.startswith("ans|"):
        _, selected, correct = call.data.split("|", 2)
        if selected == correct:
            new_score = score + 1
            update_user(chat_id, name, new_score, 0)
            if new_score % 20 == 0:
                try:
                    with open('IMG_٢٠٢٥٠٨٠٩_١١٠٤٥٤.jpg', 'rb') as photo:
                        bot.send_photo(chat_id, photo, caption=f"🎊 مذهل! أكملت {new_score} سؤالاً!", reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("التالي 🚀", callback_data="continue")))
                except: send_actual_question(chat_id, new_score)
            else: send_actual_question(chat_id, new_score)
        else:
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مرة أخرى", show_alert=True)

@bot.message_handler(commands=['start'])
def start(message):
    update_user(message.chat.id, message.from_user.first_name, 0, 0)
    bot.send_message(message.chat.id, "🕋 مرحباً بك في تحدي 'أبطال المهاجر'!")
    send_actual_question(message.chat.id, 0)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
  
