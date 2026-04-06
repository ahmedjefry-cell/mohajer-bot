import telebot
import os
import sqlite3
import random
import threading
import time
from telebot import types
from flask import Flask
from threading import Thread
from gtts import gTTS

# --- 1. إعداد السيرفر (Render Web Service) ---
app = Flask('')

@app.route('/')
def home(): 
    return "البوت يعمل بكفاءة على Render! 🎙️"

def run():
    # Render يتطلب استخدام PORT من متغيرات البيئة
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive(): 
    Thread(target=run).start()

# --- 2. الإعدادات ---
TOKEN = '8612878316:AAFmiUcKAUl0mO_pcmmSb_TD4xZ2aS18atM'
ADMIN_ID = 1833628326 
bot = telebot.TeleBot(TOKEN)
DB_NAME = 'almuhajir.db'

# --- 3. إدارة قاعدة البيانات (آمنة للخيوط) ---
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, score INTEGER DEFAULT 0)')
        conn.commit()

init_db()

def get_score(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT score FROM users WHERE id = ?', (user_id,))
        res = cursor.fetchone()
        return res[0] if res else 0

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

# --- 5. منطق الأسئلة والصوت (خاص بـ Render) ---

def send_question(chat_id, score, prefix=""):
    try:
        q_idx = score % len(questions_pool)
        q_data = questions_pool[q_idx]
        markup = types.InlineKeyboardMarkup(row_width=2)
        btns = [types.InlineKeyboardButton(opt, callback_data=f"ans|{opt}") for opt in q_data['options']]
        markup.add(*btns)
        bot.send_message(chat_id, f"{prefix}\n❓ *السؤال {score +
