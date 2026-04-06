import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعدادات السيرفر لمنع النوم على Render ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بنجاح!"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. إعدادات البوت والتوكن ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 1833628326 
FINAL_SECRET_CODE = "MOHAJER-VIP-2026"

SOUND_CORRECT = "https://www.myinstants.com/media/sounds/correct.mp3"
SOUND_WRONG = "https://www.myinstants.com/media/sounds/wrong.mp3"

# --- 3. قاعدة البيانات ---
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

# --- 4. بنك الأسئلة (يمكنك إضافة حتى 1000 سؤال هنا بنفس التنسيق) ---
questions_pool = [
    # [1-10] أركان الإسلام والإيمان
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    {"q": "كم عدد أركان الإيمان؟ ✨", "options": ["5", "6", "7", "4"], "correct": "6"},
    {"q": "ما هو أعلى مراتب الدين؟ 🌟", "options": ["الإسلام", "الإيمان", "الإحسان", "التقوى"], "correct": "الإحسان"},
    {"q": "الإيمان بالملائكة هو الركن الـ... من أركان الإيمان؟", "options": ["الأول", "الثاني", "الثالث", "الرابع"], "correct": "الثاني"},
    {"q": "ما اسم الكتاب الذي أنزل على سيدنا محمد ﷺ؟ 📖", "options": ["التوراة", "الإنجيل", "القرآن الكريم", "الزبور"], "correct": "القرآن الكريم"},
    {"q": "كم عدد صلوات الفريضة في اليوم؟ 🕌", "options": ["3", "4", "5", "6"], "correct": "5"},
    {"q": "في أي شهر يصوم المسلمون؟ 🌙", "options": ["شوال", "رجب", "رمضان", "شعبان"], "correct": "رمضان"},
    {"q": "أين توجد الكعبة المشرفة؟ 🕋", "options": ["المدينة المنورة", "مكة المكرمة", "القدس", "اليمن"], "correct": "مكة المكرمة"},
    {"q": "من هو خاتم الأنبياء والمرسلين؟ ✨", "options": ["عيسى", "موسى", "محمد ﷺ", "نوح"], "correct": "محمد ﷺ"},

    # [11-20] رحلة العمرة (تعليمي)
    {"q": "نحن الآن في الميقات ونريد العمرة، ماذا يلبس الرجل؟ ⚪", "options": ["ثوب أبيض", "ملابس الإحرام", "بدلة", "قميص"], "correct": "ملابس الإحرام"},
    {"q": "ماذا يقول المعتمر عند نية الدخول في الإحرام؟", "options": ["لبيك اللهم عمرة", "الله أكبر", "الحمد لله", "بسم الله"], "correct": "لبيك اللهم عمرة"},
    {"q": "وصلنا الكعبة المشرفة! كم شوطاً نطوف حولها؟ 🕋", "options": ["3 أشواط", "5 أشواط", "7 أشواط", "9 أشواط"], "correct": "7 أشواط"},
    {"q": "بأي قدم ندخل المسجد الحرام؟ 🦶", "options": ["اليسرى", "اليمنى", "الاثنتان", "لا يهم"], "correct": "اليمنى"},
    {"q": "ماذا نشرب من ماء مبارك داخل الحرم؟ 💧", "options": ["ماء ورد", "ماء زمزم", "ماء المطر", "عصير"], "correct": "ماء زمزم"},
    {"q": "أين نسعى بعد الطواف؟ 🏃‍♂️", "options": ["بين الصفا والمروة", "في منى", "في عرفات", "في مزدلفة"], "correct": "بين الصفا والمروة"},
    {"q": "ماذا يفعل الرجل بشعره بعد انتهاء العمرة؟ ✂️", "options": ["يغسله", "يقصه أو يحلقه", "يصبغه", "لا شيء"], "correct": "يقصه أو يحلقه"},
    {"q": "ماذا نقول عند رؤية الكعبة لأول مرة؟", "options": ["سبحان الله", "اللهم زد هذا البيت تشريفاً", "الحمد لله", "الله أكبر"], "correct": "اللهم زد هذا البيت تشريفاً"},
    {"q": "ما هو الحجر الذي نبدأ منه الطواف؟ ⚫", "options": ["حجر إسماعيل", "الحجر الأسود", "حجر المقام", "حجر الصفا"], "correct": "الحجر الأسود"},
    {"q": "أين يقع مقام إبراهيم عليه السلام؟", "options": ["في المدينة", "بجوار الكعبة", "في القدس", "في مصر"], "correct": "بجوار الكعبة"},

    # [21-40] أذكار وأخلاق
    {"q": "ماذا نقول عند البدء في الأكل؟ 🍽️", "options": ["الحمد لله", "بسم الله", "الله أكبر", "أستغفر الله"], "correct": "بسم الله"},
    {"q": "ماذا نقول بعد الانتهاء من الأكل؟", "options": ["بسم الله", "الحمد لله", "سبحان الله", "ما شاء الله"], "correct": "الحمد لله"},
    {"q": "ماذا نقول عند دخول المنزل؟ 🏠", "options": ["بسم الله ولجنا", "غفرانك", "أستغفر الله", "الحمد لله"], "correct": "بسم الله ولجنا"},
    {"q": "ماذا نقول عند الخروج من المنزل؟", "options": ["باسم الله توكلت على الله", "سبحان الله", "الله أكبر", "الحمد لله"], "correct": "باسم الله توكلت على الله"},
    {"q": "ماذا نقول عند دخول الخلاء (الحمام)؟", "options": ["اللهم إني أعوذ بك من الخبث والخبائث", "غفرانك", "بسم الله خرجنا", "الحمد لله"], "correct": "اللهم إني أعوذ بك من الخبث والخبائث"},
    {"q": "ماذا نقول عند الخروج من الخلاء؟", "options": ["الحمد لله", "بسم الله", "غفرانك", "سبحان الله"], "correct": "غفرانك"},
    {"q": "ماذا نقول لمن صنع لنا معروفاً؟ ✨", "options": ["شكراً", "جزاك الله خيراً", "أهلاً", "ممتاز"], "correct": "جزاك الله خيراً"},
    {"q": "ماذا نقول عند الغضب؟", "options": ["أعوذ بالله من الشيطان الرجيم", "سبحان الله", "الحمد لله", "لا إله إلا الله"], "correct": "أعوذ بالله من الشيطان الرجيم"},
    {"q": "ما هي أعظم آية في القرآن الكريم؟", "options": ["آية الكرسي", "آية الدين", "آخر سورة البقرة", "الفاتحة"], "correct": "آية الكرسي"},
    {"q": "ما هي السورة التي تعدل ثلث القرآن؟", "options": ["الفاتحة", "الإخلاص", "الناس", "الكوثر"], "correct": "الإخلاص"},
    
    # يمكنك تكرار النمط لإضافة 1000 سؤال...
]

# فواصل إيمانية كل 10 أسئلة
spiritual_breaks = [
    "💡 **استراحة إيمانية:** قال رسول الله ﷺ: 'تبسمك في وجه أخيك لك صدقة'. 😊",
    "💡 **استراحة إيمانية:** الصلاة في المسجد الحرام تعادل 100,000 صلاة! 🕋",
    "💡 **استراحة إيمانية:** كلمة 'سبحان الله وبحمده' تغرس لك نخلة في الجنة. 🌴"
]

def get_rank(score):
    if score >= 1000: return "سفير وكالة المهاجر الذهبي 🏆"
    if score >= 500: return "رحالة المهاجر الذكي 🧭"
    if score >= 100: return "بطل المهاجر المبدع 🌟"
    return "متحدي المهاجر الصغير 👶"

# --- 5. وظائف إرسال الأسئلة والشهادات ---
def send_actual_question(chat_id, score):
    if score >= 1000:
        name, _, _ = get_user_data(chat_id)
        cert = (f"🎓 **شهادة إنجاز من وكالة المهاجر** 🎓\n\n"
                f"نهنئ البطل: **{name}**\n"
                f"لقد أتممت 1000 سؤال بنجاح وحصلت على لقب:\n"
                f"🏆 **{get_rank(score)}** 🏆\n\n"
                f"كود الجائزة: `{FINAL_SECRET_CODE}`")
        bot.send_message(chat_id, cert, parse_mode="Markdown")
        return

    if score > 0 and score % 10 == 0:
        tip = random.choice(spiritual_breaks)
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("واصل الرحلة 🚀", callback_data="continue"))
        bot.send_message(chat_id, tip, reply_markup=markup, parse_mode="Markdown")
        return

    if score >= len(questions_pool):
        bot.send_message(chat_id, "✅ أحسنت! انتهت المرحلة الحالية، انتظرنا قريباً لزيادة الأسئلة!")
        return

    q_data = questions_pool[score]
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}|{q_data['correct']}") for opt in q_data['options']]
    markup.add(*btns)
    
    msg = (f"❓ **السؤال رقم ({score + 1}):**\n\n"
           f"**{q_data['q']}**\n\n"
           f"🏅 **لقبك:** {get_rank(score)}")
    bot.send_message(chat_id, msg, reply_markup=markup, parse_mode="Markdown")

# --- 6. معالجة الردود ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    user_data = get_user_data(chat_id)
    if not user_data: return
    name, score, fails = user_data
    
    if call.data == "continue":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        send_actual_question(chat_id, score)
        
    elif call.data.startswith("ans|"):
        _, selected, correct = call.data.split("|", 2)
        if selected == correct:
            try: bot.send_audio(chat_id, SOUND_CORRECT)
            except: pass
            new_score = score + 1
            update_user(chat_id, name, new_score, 0)
            
            try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            except: pass
            
            if new_score > 0 and new_score % 20 == 0:
                try:
                    with open('IMG_٢٠٢٥٠٨٠٩_١١٠٤٥٤.jpg', 'rb') as photo:
                        bot.send_photo(chat_id, photo, caption=f"🎊 مبارك! أكملت {new_score} سؤالاً يا بطل المهاجر!", 
                                       reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("السؤال التالي 🚀", callback_data="continue")))
                except: send_actual_question(chat_id, new_score)
            else:
                send_actual_question(chat_id, new_score)
        else:
            try: bot.send_audio(chat_id, SOUND_WRONG)
            except: pass
            new_fails = fails + 1
            update_user(chat_id, name, score, new_fails)
            if new_fails >= 3:
                bot.send_message(chat_id, "🛡️ **درع الأبطال:** لا تحزن! العلم محاولة وخطأ، تنفس بعمق وحاول مجدداً!")
                update_user(chat_id, name, score, 0)
            else:
                bot.answer_callback_query(call.id, "❌ خطأ! حاول مرة أخرى", show_alert=True)

@bot.message_handler(commands=['start'])
def start(message):
    update_user(message.chat.id, message.from_user.first_name, 0, 0)
    bot.send_message(message.chat.id, "🕋 **مرحباً بك في تحدي أبطال وكالة المهاجر!**\nرحلتنا التعليمية تبدأ الآن.. هل أنت مستعد؟", parse_mode="Markdown")
    send_actual_question(message.chat.id, 0)

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
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
  
