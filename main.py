# -*- coding: utf-8 -*-
import io
import asyncio
import threading
from flask import Flask
from gtts import gTTS
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# --- الإعدادات (استبدل القيم أدناه) ---
TOKEN = '8612878316:AAEKIklqPde9vN5--B310CkmB_BJ6ZQ3trI'
ADMIN_ID = 123456789  # ضع الآيدي الخاص بك هنا

# --- خادم ويب وهمي لإبقاء Render مستيقظاً ---
server = Flask(__name__)

@server.route('/')
def index():
    return "البوت يعمل بنجاح..."

def run_flask():
    server.run(host='0.0.0.0', port=8080)

# --- قائمة حِكم ابن عطاء الله السكندري ---
ibn_ataa_wisdom = [
    "من وجد الله فماذا فقد؟ ومن فقد الله فماذا وجد؟",
    "لا يكن تأخر أمد العطاء مع الإلحاح في الدعاء موجباً ليأسك؛ فهو ضمن لك الإجابة فيما يختاره لك.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به أنت لنفسك.",
    "معصية أورثت ذلاً وانكساراً خير من طاعة أورثت عزاً واستكباراً."
]

# --- قاعدة بيانات الـ 1000 سؤال ---
questions_db = [
    {"q": "ما هي السورة التي تسمى عروس القرآن؟", "options": ["الرحمن", "يس", "الواقعة", "الملك"], "correct": "الرحمن"},
    {"q": "من هو النبي الذي لُقب بكليم الله؟", "options": ["موسى عليه السلام", "محمد ﷺ", "عيسى عليه السلام", "إبراهيم عليه السلام"], "correct": "موسى عليه السلام"},
    # ... أضف بقية الـ 1000 سؤال هنا ...
]

async def send_wisdom_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """تحويل الحكمة لصوت وإرسالها كبصمة صوتية"""
    try:
        tts = gTTS(text=text, lang='ar')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_io.seek(0)
        await context.bot.send_voice(chat_id=update.effective_chat.id, voice=audio_io, caption=f"✨ حكمة ابن عطاء الله:\n{text}")
    except: pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['score'] = 0
    context.user_data['current_q'] = 0
    await update.message.reply_text("✨ أهلاً بك! اضغط /quiz للبدء بالمسابقة.")

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    idx = context.user_data.get('current_q', 0)
    if idx >= len(questions_db):
        await update.effective_message.reply_text(f"🏁 انتهت المسابقة! نتيجتك: {context.user_data.get('score', 0)}")
        return

    q_item = questions_db[idx]
    keyboard = [[InlineKeyboardButton(opt, callback_data=str(i))] for i, opt in enumerate(q_item['options'])]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg_text = f"السؤال [{idx + 1}/1000]:\n\n{q_item['q']}"
    if update.callback_query:
        await update.callback_query.message.reply_text(msg_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(msg_text, reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    idx = context.user_data.get('current_q', 0)
    user_choice = int(query.data)
    correct_ans = questions_db[idx]['correct']
    
    if questions_db[idx]['options'][user_choice] == correct_ans:
        context.user_data['score'] = context.user_data.get('score', 0) + 1
        await query.edit_message_text(f"✅ إجابة صحيحة!")
    else:
        await query.edit_message_text(f"❌ خطأ. الصواب: {correct_ans}")

    context.user_data['current_q'] = idx + 1
    new_idx = context.user_data['current_q']

    if new_idx % 20 == 0 and new_idx != 0:
        wisdom = ibn_ataa_wisdom[(new_idx // 20 - 1) % len(ibn_ataa_wisdom)]
        await send_wisdom_voice(update, context, wisdom)
        await asyncio.sleep(1)

    await ask_question(update, context)

if __name__ == '__main__':
    # تشغيل Flask في خيط منفصل (Thread)
    threading.Thread(target=run_flask, daemon=True).start()
    
    # تشغيل البوت
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", ask_question))
    application.add_handler(CallbackQueryHandler(handle_answer))
    
    print("البوت يعمل الآن...")
    application.run_polling()
