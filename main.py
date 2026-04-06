import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعداد السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بكفاءة قصوى! 🚀"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. الإعدادات ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
ADMIN_ID = 1833628326 
bot = telebot.TeleBot(TOKEN)

# --- 3. قاعدة البيانات ---
def get_db_connection():
    conn = sqlite3.connect('almuhajir.db', check_same_thread=False)
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, score INTEGER DEFAULT 0)')
        conn.commit()

init_db()

def set_user_score(user_id, name, score):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO users (id, name, score) VALUES (?, ?, ?)', (user_id, name, score))
        conn.commit()

def get_user_score(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM users WHERE id = ?', (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0

# --- 4. محتوى الأسئلة والحكم ---
questions_pool = [
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    {"q": "كم عدد أركان الإيمان؟ ✨", "options": ["5", "6", "7", "4"], "correct": "6"},
    {"q": "ما هو أعلى مراتب الدين؟ 🌟", "options": ["الإسلام", "الإيمان", "الإحسان", "التقوى"], "correct": "الإحسان"},
    {"q": "وصلنا الكعبة المشرفة! كم شوطاً نطوف حولها؟ 🕋", "options": ["3", "5", "7", "9"], "correct": "7"},
    {"q": "ماذا نشرب من ماء مبارك داخل الحرم؟ 💧", "options": ["ماء ورد", "ماء زمزم", "ماء المطر", "عصير"], "correct": "ماء زمزم"},
    {"q": "من هو النبي الذي بنى الكعبة مع ابنه إسماعيل؟", "options": ["إبراهيم عليه السلام", "نوح عليه السلام", "موسى عليه السلام", "عيسى عليه السلام"], "correct": "إبراهيم عليه السلام"},
    # أضف بقية الـ 1000 سؤال هنا...
]

hikam_list = [
    "من علامة الاعتماد على العمل، نقصان الرجاء عند وجود الزلل.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به لنفسك.",
    "اجتهادك فيما ضمن لك، وتقصيرك فيما طلب منك، دليل على انطماس البصيرة منك.",
    "لا يكن تأخر أمد العطاء مع الإلحاح في الدعاء موجباً ليأسك.",
    "لا تصحب من لا ينهضك حاله، ولا يدلك على الله مقاله."
]

# --- 5. منطق اللعب (تم تصحيح خطأ التكرار هنا) ---
def send_next_step(chat_id, score, is_continuation=False):
    try:
        if score >= 1000:
            bot.send_message(chat_id, "🏆 **تهانينا!** لقد أتممت 1000 سؤال بنجاح!")
            return

        # إظهار الحكمة فقط إذا كانت النتيجة من مضاعفات 20 ولم يضغط المستخدم للتو على "واصل"
        if score > 0 and score % 20 == 0 and not is_continuation:
            h = random.choice(hikam_list)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("فهمت الحكمة.. واصل الرحلة 🚀", callback_data="force_next"))
            bot.send_message(chat_id, f"💎 **حكمة المحطة ({score}):**\n\n« {h} »", reply_markup=markup, parse_mode="Markdown")
            return

        # إرسال السؤال التالي
        q_idx = score % len(questions_pool)
        q_data = questions_pool[q_idx]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}") for opt in q_data['options']]
        markup.add(*btns)
        
        bot.send_message(chat_id, f"❓ *السؤال {score + 1}:*\n\n{q_data['q']}", reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Error: {e}")

# --- 6. معالجة الردود ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    score = get_user_score(chat_id)
    
    if call.data == "force_next":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        # نمرر True لنتجاوز فحص الحكمة ونرسل السؤال مباشرة
        send_next_step(chat_id, score, is_continuation=True)

    elif call.data.startswith("ans|"):
        selected = call.data.split("|")[1]
        q_idx = score % len(questions_pool)
        correct = questions_pool[q_idx]['correct']
        
        if selected == correct:
            bot.answer_callback_query(call.id, "✅ صحيح!")
            new_score = score + 1
            set_user_score(chat_id, call.from_user.first_name, new_score)
            try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            except: pass
            send_next_step(chat_id, new_score)
        else:
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مجدداً", show_alert=True)

# --- 7. أوامر المدير ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 الإحصائيات", "📢 إعلان عام")
        bot.send_message(message.chat.id, "🛠 لوحة المدير:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📊 الإحصائيات" and m.from_user.id == ADMIN_ID)
def stats(message):
    with get_db_connection() as conn:
        count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
    bot.send_message(ADMIN_ID, f"👥 عدد المستخدمين: {count}")

@bot.message_handler(func=lambda m: m.text == "📢 إعلان عام" and m.from_user.id == ADMIN_ID)
def broadcast_prompt(message):
    msg = bot.send_message(ADMIN_ID, "أرسل نص الإعلان:")
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(message):
    with get_db_connection() as conn:
        users = conn.execute('SELECT id FROM users').fetchall()
    for u in users:
        try: bot.send_message(u[0], f"📢 إعلان:\n\n{message.text}")
        except: continue
    bot.send_message(ADMIN_ID, "✅ تم الإرسال.")

# --- 8. البداية ---
@bot.message_handler(commands=['start'])
def start(message):
    score = get_user_score(message.chat.id)
    if score == 0:
        set_user_score(message.chat.id, message.from_user.first_name, 0)
        bot.send_message(message.chat.id, "🕋 مرحباً بك في تحدي المهاجر!")
    send_next_step(message.chat.id, score)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
