import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread
from gtts import gTTS

# --- 1. إعداد السيرفر ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بكفاءة! 🎙️"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive(): Thread(target=run).start()

# --- 2. الإعدادات ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
bot = telebot.TeleBot(TOKEN)
DB_NAME = 'almuhajir.db'

# --- 3. قاعدة البيانات ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, score INTEGER DEFAULT 0)')
        conn.commit()
init_db()

def get_user_score(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM users WHERE id = ?', (user_id,))
        res = cursor.fetchone()
        if res: return res[0]
        conn.execute('INSERT INTO users (id, score) VALUES (?, ?)', (user_id, 0))
        conn.commit()
        return 0

def update_user_score(user_id, new_score):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, user_id))
        conn.commit()

# --- 4. محتوى الأسئلة (تأكد من إضافة 40 سؤال هنا) ---
questions_pool = [
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    # ... أضف بقية الأسئلة هنا حتى تكتمل الـ 40 ...
]

hikam_list = [
    "من علامة الاعتماد على العمل، نقصان الرجاء عند وجود الزلل.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به لنفسك.",
    "لا تصحب من لا ينهضك حاله، ولا يدلك على الله مقاله."
]

# --- 5. منطق إرسال السؤال ---
def send_question(chat_id, score, prefix=""):
    # المنطق يضمن عدم التكرار حتى تنتهي المصفوفة كاملة
    q_idx = score % len(questions_pool) 
    q_data = questions_pool[q_idx]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}|{score}") for opt in q_data['options']]
    markup.add(*btns)
    
    msg_text = f"{prefix}\n\n⭐ *المستوى: {score + 1}*\n❓ {q_data['q']}"
    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

# --- 6. معالجة الإجابات ---
@bot.message_handler(commands=['start'])
def welcome(message):
    score = get_user_score(message.from_user.id)
    send_question(message.chat.id, score, "مرحباً بك في رحلة المهاجر! 🕋")

@bot.callback_query_handler(func=lambda call: call.data.startswith('ans|'))
def check_answer(call):
    _, user_answer, current_score = call.data.split('|')
    current_score = int(current_score)
    user_id = call.from_user.id
    
    # جلب السكور الحقيقي من القاعدة للتأكد من عدم التلاعب
    real_score = get_user_score(user_id)
    if current_score != real_score:
        bot.answer_callback_query(call.id, "عذراً، هذا السؤال انتهى صلاحيته. أجب على الأحدث!")
        return

    q_idx = current_score % len(questions_pool)
    if user_answer == questions_pool[q_idx]['correct']:
        new_score = current_score + 1
        update_user_score(user_id, new_score)
        
        # --- التعديل المطلوب: الحكمة تظهر كل 20 سؤال فقط ---
        if new_score > 0 and new_score % 20 == 0:
            hikma = random.choice(hikam_list)
            try:
                tts = gTTS(text=f"مبروك وصولك للمستوى {new_score}. إليك هذه الحكمة: {hikma}", lang='ar')
                voice_file = f"v_{user_id}.mp3"
                tts.save(voice_file)
                with open(voice_file, 'rb') as v:
                    bot.send_voice(call.message.chat.id, v, caption=f"✨ حكمة المهاجر (المستوى {new_score}):\n_{hikma}_", parse_mode="Markdown")
                os.remove(voice_file)
            except:
                bot.send_message(call.message.chat.id, f"✨ حكمة المستوى {new_score}: {hikma}")
        
        send_question(call.message.chat.id, new_score, "✅ إجابة صحيحة!")
    else:
        bot.answer_callback_query(call.id, "إجابة خاطئة! حاول مجدداً ❌", show_alert=True)

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
def get_user_score(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM users WHERE id = ?', (user_id,))
        res = cursor.fetchone()
        if res: return res[0]
        else:
            conn.execute('INSERT INTO users (id, score) VALUES (?, ?)', (user_id, 0))
            conn.commit()
            return 0

def update_user_score(user_id, new_score):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('UPDATE users SET score = ? WHERE id = ?', (new_score, user_id))
        conn.commit()

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

# --- 5. منطق الأسئلة ---

def send_question(chat_id, score, prefix=""):
    q_idx = score % len(questions_pool)
    q_data = questions_pool[q_idx]
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}|{score}") for opt in q_data['options']]
    markup.add(*btns)
    
    msg_text = f"{prefix}\n\n❓ *السؤال {score + 1}:*\n{q_data['q']}"
    bot.send_message(chat_id, msg_text, reply_markup=markup, parse_mode="Markdown")

# --- 6. معالجة الرسائل ---

@bot.message_handler(commands=['start'])
def welcome(message):
    score = get_user_score(message.from_user.id)
    send_question(message.chat.id, score, "مرحباً بك في رحلة المهاجر! 🕋")

@bot.callback_query_handler(func=lambda call: call.data.startswith('ans|'))
def check_answer(call):
    data = call.data.split('|')
    user_answer = data[1]
    current_score = int(data[2])
    user_id = call.from_user.id
    
    q_idx = current_score % len(questions_pool)
    correct_answer = questions_pool[q_idx]['correct']
    
    if user_answer == correct_answer:
        new_score = current_score + 1
        update_user_score(user_id, new_score)
        
        # اختيار حكمة عشوائية
        hikma = random.choice(hikam_list)
        
        # تحويل الحكمة لصوت وإرسالها (بدون حذف)
        try:
            tts = gTTS(text=hikma, lang='ar')
            voice_file = f"voice_{user_id}.mp3"
            tts.save(voice_file)
            
            with open(voice_file, 'rb') as voice:
                bot.send_voice(call.message.chat.id, voice, caption=f"✨ حكمة لك:\n_{hikma}_", parse_mode="Markdown")
            
            os.remove(voice_file) # حذف الملف المؤقت من السيرفر فقط وليس من التليجرام
        except Exception as e:
            bot.send_message(call.message.chat.id, f"✨ حكمة لك:\n{hikma}")

        # الانتقال للسؤال التالي
        send_question(call.message.chat.id, new_score, "إجابة صحيحة! استمر في رحلتك..")
    else:
        bot.answer_callback_query(call.id, "إجابة خاطئة! حاول مجدداً ❌", show_alert=True)

# --- التشغيل ---
if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
