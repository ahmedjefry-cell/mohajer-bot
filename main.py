import telebot
import os
import sqlite3
import random
from telebot import types
from flask import Flask
from threading import Thread

# --- 1. إعداد السيرفر لمنع النوم (Render) ---
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل بكفاءة قصوى! 🚀"
def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive(): Thread(target=run).start()

# --- 2. الإعدادات الأساسية ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
ADMIN_ID = 1833628326 
bot = telebot.TeleBot(TOKEN)

# --- 3. إدارة قاعدة البيانات ---
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

# --- 4. محتوى البوت (الأسئلة والحكم) ---
# ملاحظة: يمكنك إضافة حتى 1000 سؤال في هذه القائمة
questions_pool = [
    {"q": "كم عدد أركان الإسلام؟ 🕋", "options": ["3", "5", "7", "4"], "correct": "5"},
    {"q": "ما هو الركن الأول من أركان الإسلام؟", "options": ["الصلاة", "الشهادتان", "الزكاة", "الحج"], "correct": "الشهادتان"},
    {"q": "كم عدد أركان الإيمان؟ ✨", "options": ["5", "6", "7", "4"], "correct": "6"},
    {"q": "ما هو أعلى مراتب الدين؟ 🌟", "options": ["الإسلام", "الإيمان", "الإحسان", "التقوى"], "correct": "الإحسان"},
    {"q": "وصلنا الكعبة المشرفة! كم شوطاً نطوف حولها؟ 🕋", "options": ["3", "5", "7", "9"], "correct": "7"},
    {"q": "ماذا نشرب من ماء مبارك داخل الحرم؟ 💧", "options": ["ماء ورد", "ماء زمزم", "ماء المطر", "عصير"], "correct": "ماء زمزم"},
    {"q": "من هو النبي الذي بنى الكعبة مع ابنه إسماعيل؟", "options": ["إبراهيم عليه السلام", "نوح عليه السلام", "موسى عليه السلام", "عيسى عليه السلام"], "correct": "إبراهيم عليه السلام"},
    # أضف هنا بقية الـ 1000 سؤال بنفس التنسيق...
]

hikam_list = [
    "من علامة الاعتماد على العمل، نقصان الرجاء عند وجود الزلل.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به لنفسك.",
    "اجتهادك فيما ضمن لك، وتقصيرك فيما طلب منك، دليل على انطماس البصيرة منك.",
    "لا يكن تأخر أمد العطاء مع الإلحاح في الدعاء موجباً ليأسك.",
    "لا تصحب من لا ينهضك حاله، ولا يدلك على الله مقاله.",
    "ربما كنت مسيئاً فأراك الإحسان منك صحبتك لمن هو أسوأ حالاً منك.",
    "ما قل عمل برز من قلب زاهد، ولا كثر عمل برز من قلب راغب."
]

# --- 5. منطق اللعب الرئيسي ---
def send_next_step(chat_id, score):
    try:
        # حالة إنهاء الـ 1000 سؤال
        if score >= 1000:
            bot.send_message(chat_id, "🏆 **تهانينا يا بطل!**\nلقد أتممت رحلة الـ 1000 سؤال بنجاح وأصبحت سفير وكالة المهاجر الذهبي!")
            return

        # نظام الاستراحة والحكم (كل 20 سؤال)
        if score > 0 and score % 20 == 0:
            h = random.choice(hikam_list)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("فهمت الحكمة.. واصل الرحلة 🚀", callback_data="next_q"))
            bot.send_message(chat_id, f"💎 **استراحة محارب (حكمة المهاجر):**\n\n« {h} »", reply_markup=markup, parse_mode="Markdown")
            return

        # جلب السؤال التالي
        q_idx = score % len(questions_pool) # يضمن الدوران إذا كانت الأسئلة أقل من 1000
        q_data = questions_pool[q_idx]
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}") for opt in q_data['options']]
        markup.add(*btns)
        
        bot.send_message(chat_id, f"❓ *السؤال {score + 1}:*\n\n{q_data['q']}", reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"Error in send_next_step: {e}")

# --- 6. معالجة الأزرار (Callback Queries) ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    score = get_user_score(chat_id)
    
    if call.data == "next_q":
        try: bot.delete_message(chat_id, call.message.message_id)
        except: pass
        send_next_step(chat_id, score)

    elif call.data.startswith("ans|"):
        selected = call.data.split("|")[1]
        q_idx = score % len(questions_pool)
        correct = questions_pool[q_idx]['correct']
        
        if selected == correct:
            bot.answer_callback_query(call.id, "✅ إجابة صحيحة!")
            new_score = score + 1
            set_user_score(chat_id, call.from_user.first_name, new_score)
            try: bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
            except: pass
            send_next_step(chat_id, new_score)
        else:
            bot.answer_callback_query(call.id, "❌ خطأ! حاول مجدداً 🔄", show_alert=True)

# --- 7. أوامر المدير (Admin Panel) ---
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 إحصائيات البوت", "📢 إرسال إعلان")
        markup.add("🔄 تصفير نقاطي")
        bot.send_message(message.chat.id, "🛠 **لوحة تحكم المدير:**", reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(message.chat.id, "❌ هذا الأمر مخصص للإدارة فقط.")

@bot.message_handler(func=lambda m: m.text == "📊 إحصائيات البوت" and m.from_user.id == ADMIN_ID)
def admin_stats(message):
    with get_db_connection() as conn:
        count = conn.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        top = conn.execute('SELECT MAX(score) FROM users').fetchone()[0]
    bot.send_message(message.chat.id, f"📈 **الإحصائيات:**\n\n👥 عدد المشتركين: {count}\n🏆 أعلى نتيجة: {top}")

@bot.message_handler(func=lambda m: m.text == "📢 إرسال إعلان" and m.from_user.id == ADMIN_ID)
def admin_broadcast(message):
    msg = bot.send_message(message.chat.id, "📝 أرسل نص الإعلان الآن:")
    bot.register_next_step_handler(msg, start_broadcasting)

def start_broadcasting(message):
    with get_db_connection() as conn:
        users = conn.execute('SELECT id FROM users').fetchall()
    
    success = 0
    for u in users:
        try:
            bot.send_message(u[0], f"📢 **تنبيه من إدارة المهاجر:**\n\n{message.text}")
            success += 1
        except: continue
    bot.send_message(ADMIN_ID, f"✅ تم الإرسال بنجاح إلى {success} مستخدم.")

@bot.message_handler(func=lambda m: m.text == "🔄 تصفير نقاطي" and m.from_user.id == ADMIN_ID)
def reset_self(message):
    set_user_score(ADMIN_ID, message.from_user.first_name, 0)
    bot.send_message(ADMIN_ID, "✅ تم تصفير نقاطك بنجاح للبدء من جديد.")

# --- 8. الأوامر العامة ---
@bot.message_handler(commands=['start'])
def start(message):
    # لا نصفر النقاط إذا كان المستخدم مسجلاً مسبقاً ليكمل من حيث وقف
    score = get_user_score(message.chat.id)
    if score == 0:
        set_user_score(message.chat.id, message.from_user.first_name, 0)
        bot.send_message(message.chat.id, "🕋 **مرحباً بك في تحدي وكالة المهاجر!**\n\nرحلة الـ 1000 سؤال تبدأ الآن.. استعن بالله.")
    else:
        bot.send_message(message.chat.id, f"👋 أهلاً بك مجدداً! أنت الآن في السؤال رقم {score + 1}")
    
    send_next_step(message.chat.id, score)

# --- 9. التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive()
    print("البوت يعمل الآن بأقصى سرعة...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
