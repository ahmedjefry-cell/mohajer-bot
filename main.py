import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread
from gtts import gTTS

# --- 1. إعداد السيرفر (Render) ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بالأسئلة الجديدة! 🕋"

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

# --- 4. الأسئلة الجديدة من موقع المفيد ---
questions_pool = [
    {"q": "كم عدد أولي العزم من الرسل؟", "options": ["أربعة", "خمسة", "ستة"], "correct": "خمسة"},
    {"q": "من هو النبي الذي آمن به كل قومه؟", "options": ["يونس عليه السلام", "صالح عليه السلام", "نوح عليه السلام"], "correct": "يونس عليه السلام"},
    {"q": "ما اسم العبد الصالح الذي رافقه موسى عليه السلام؟", "options": ["عزير", "الخضر", "لقمان"], "correct": "الخضر"},
    {"q": "من هو النبي الملقب بـ 'روح الله'؟", "options": ["عيسى عليه السلام", "موسى عليه السلام", "إبراهيم عليه السلام"], "correct": "عيسى عليه السلام"},
    {"q": "أين صعد الرسول ﷺ عند الجهر بالدعوة ليدعو القبائل؟", "options": ["جبل أحد", "جبل الصفا", "جبل المروة"], "correct": "جبل الصفا"},
    {"q": "في أي عام وشهر كان فتح مكة؟", "options": ["رمضان - 8 هـ", "شوال - 8 هـ", "محرم - 8 هـ"], "correct": "رمضان - 8 هـ"},
    {"q": "ما هو عدد السجدات في القرآن الكريم؟", "options": ["10 سجدات", "15 سجدة", "20 سجدة"], "correct": "15 سجدة"},
    {"q": "ما هي السورة التي يبكي الشيطان عند سماعها؟", "options": ["سورة الفاتحة", "سورة السجدة", "سورة البقرة"], "correct": "سورة السجدة"},
    {"q": "من هو آخر من توفي من العشرة المبشرين بالجنة؟", "options": ["سعد بن أبي وقاص", "عثمان بن عفان", "أبو بكر الصديق"], "correct": "سعد بن أبي وقاص"},
    {"q": "ما هي العدة التي أقرها الإسلام للمرأة المطلقة؟", "options": ["حيضتان", "ثلاث حيضات", "أربع حيضات"], "correct": "ثلاث حيضات"},
    {"q": "من هو صفي الله من الأنبياء؟", "options": ["آدم عليه السلام", "نوح عليه السلام", "إبراهيم عليه السلام"], "correct": "آدم عليه السلام"},
    {"q": "من هي ذات النطاقين؟", "options": ["أسماء بنت أبي بكر", "عائشة بنت أبي بكر", "فاطمة الزهراء"], "correct": "أسماء بنت أبي بكر"},
    {"q": "ما هي السورة التي تسمى 'أم الكتاب'؟", "options": ["سورة البقرة", "سورة الفاتحة", "سورة الإخلاص"], "correct": "سورة الفاتحة"},
    {"q": "من هو خاتم الأنبياء والمرسلين؟", "options": ["عيسى عليه السلام", "موسى عليه السلام", "محمد ﷺ"], "correct": "محمد ﷺ"},
    {"q": "كم عدد أركان الإسلام؟", "options": ["خمسة", "ستة", "سبعة"], "correct": "خمسة"},
    {"q": "ما هي السورة التي تحدثت عن تقسيم الغنائم؟", "options": ["سورة الأنفال", "سورة التوبة", "سورة الحج"], "correct": "سورة الأنفال"},
    {"q": "من هو الصحابي الذي يلقب بـ 'إمام القراء'؟", "options": ["زيد بن ثابت", "معاذ بن جبل", "أبي بن كعب"], "correct": "معاذ بن جبل"},
    {"q": "ما معنى 'الأعراف'؟", "options": ["وديان في النار", "تلال بين الجنة والنار", "أنهار في الجنة"], "correct": "تلال بين الجنة والنار"},
    {"q": "من هو أول من جاهد في سبيل الله؟", "options": ["إدريس عليه السلام", "إبراهيم عليه السلام", "نوح عليه السلام"], "correct": "إدريس عليه السلام"},
    {"q": "ما هي الغزوة التي أُسرت فيها الشيماء شقيقة الرسول ﷺ؟", "options": ["غزوة حنين", "غزوة بدر", "غزوة الخندق"], "correct": "غزوة حنين"}
]

hikam_list = [
    "من علامة الاعتماد على العمل، نقصان الرجاء عند وجود الزلل.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به لنفسك.",
    "اجتهادك فيما ضمن لك، وتقصيرك فيما طلب منك، دليل على انطماس البصيرة."
]

# --- 5. منطق إرسال السؤال ---
def send_question(chat_id, score, prefix=""):
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
    send_question(message.chat.id, score, "مرحباً بك في بوت المهاجر! 🕋\nتم تحديث الأسئلة بنجاح.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('ans|'))
def check_answer(call):
    _, user_answer, current_score = call.data.split('|')
    current_score = int(current_score)
    user_id = call.from_user.id
    
    real_score = get_user_score(user_id)
    if current_score != real_score:
        bot.answer_callback_query(call.id, "هذا السؤال قديم!")
        return

    q_idx = current_score % len(questions_pool)
    if user_answer == questions_pool[q_idx]['correct']:
        new_score = current_score + 1
        update_user_score(user_id, new_score)
        
        # الحكمة تظهر فقط كل 20 سؤالاً
        if new_score > 0 and new_score % 20 == 0:
            hikma = random.choice(hikam_list)
            try:
                tts = gTTS(text=f"أحسنت! إليك هذه الحكمة: {hikma}", lang='ar')
                voice_file = f"v_{user_id}.mp3"
                tts.save(voice_file)
                with open(voice_file, 'rb') as v:
                    bot.send_voice(call.message.chat.id, v, caption=f"✨ حكمة المستوى {new_score}:\n_{hikma}_", parse_mode="Markdown")
                os.remove(voice_file)
            except:
                bot.send_message(call.message.chat.id, f"✨ حكمة المستوى {new_score}: {hikma}")
        
        send_question(call.message.chat.id, new_score, "✅ إجابة صحيحة!")
    else:
        bot.answer_callback_query(call.id, "إجابة خاطئة! حاول مجدداً ❌", show_alert=True)

if __name__ == '__main__':
    keep_alive()
    bot.infinity_polling()
