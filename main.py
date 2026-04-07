# -*- coding: utf-8 -*-
import os
import time
from gtts import gTTS
import pygame

# إعداد محرك الصوت
pygame.mixer.init()

# --- قائمة حِكم ابن عطاء الله السكندري (تم اختيار 50 حكمة كمثال للتدوير) ---
ibn_ataa_wisdom = [
    "من وجد الله فماذا فقد؟ ومن فقد الله فماذا وجد؟",
    "لا يكن تأخر أمد العطاء مع الإلحاح في الدعاء موجباً ليأسك؛ فهو ضمن لك الإجابة فيما يختاره لك، لا فيما تختاره لنفسك.",
    "إرادتك التجريد مع إقامة الله إياك في الأسباب من الشهوة الخفية. وإرادتك الأسباب مع إقامة الله إياك في التجريد انحطاط عن الهمة العلية.",
    "سوابق الهمم لا تخرق أسوار الأقدار.",
    "أرح نفسك من التدبير، فما قام به غيرك عنك لا تقم به أنت لنفسك.",
    "اجتهادك فيما ضمن لك، وتقصيرك فيما طلب منك، دليل على انطماس البصيرة منك.",
    "ما توقف مطلب أنت طالبه بربك، ولا تيسر مطلب أنت طالبه بنفسك.",
    "معصية أورثت ذلاً وانكساراً خير من طاعة أورثت عزاً واستكباراً.",
    "ربما أعطاك فمنعك، وربما منعك فأعطاك.",
    "متى أطلق لسانك بالطلب فاعلم أنه يريد أن يعطيك.",
    "لا ترحل من كون إلى كون فتكون كحمار الرحى، يسير والمكان الذي ارتحل إليه هو الذي ارتحل عنه.",
    "تشوفك إلى ما بطن فيك من العيوب خير من تشوفك إلى ما حجب عنك من الغيوب."
]

# --- هيكل الـ 1000 سؤال (تأكد من وضع القائمة الكاملة هنا) ---
questions_db = [
    {"q": "ما هي السورة التي تسمى عروس القرآن؟", "options": ["الرحمن", "يس", "الواقعة", "الملك"], "correct": "الرحمن"},
    # ... ضع هنا الـ 1000 سؤال بالكامل التي استلمتها سابقاً ...
]

# --- إعدادات المدير (Admin Config) ---
ADMIN_KEY = "admin789"

def speak_wisdom(text):
    """تحويل حكمة ابن عطاء الله إلى صوت وتشغيلها"""
    try:
        print(f"\n📢 نداء الحكمة: {text}")
        tts = gTTS(text=text, lang='ar')
        tts.save("temp_voice.mp3")
        pygame.mixer.music.load("temp_voice.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(1)
        pygame.mixer.music.unload()
        os.remove("temp_voice.mp3")
    except Exception as e:
        print(f"خطأ في النظام الصوتي: {e}")

def admin_console():
    """أوامر المدير للتحكم في البوت"""
    print("\n🔐 [نظام الإدارة المركزي]")
    entry = input("أدخل رمز الوصول: ")
    if entry == ADMIN_KEY:
        print("--- الأوامر المتاحة ---")
        print("1. تخطي 100 سؤال\n2. إنهاء الجلسة فوراً\n3. تصفير النتيجة")
        cmd = input("اختر الأمر: ")
        if cmd == "1": return "skip"
        if cmd == "2": return "exit"
    else:
        print("❌ رمز خاطئ، عودة للمسابقة...")
    return None

def run_engine():
    score = 0
    wisdom_ptr = 0
    total_q = len(questions_db)
    
    print("✨ بسم الله نبدأ مسابقة الـ 1000 سؤال وحِكم ابن عطاء الله ✨")
    
    i = 0
    while i < total_q:
        item = questions_db[i]
        print(f"\n------------------------------")
        print(f"السؤال [{i+1}/1000] | النتيجة الحالية: {score}")
        print(f"------------------------------")
        print(item['q'])
        for idx, opt in enumerate(item['options']):
            print(f"  {idx+1}) {opt}")
            
        user_input = input("\nإجابتك (رقم) أو (admin): ").strip()

        # معالجة أوامر المدير
        if user_input.lower() == 'admin':
            action = admin_console()
            if action == "skip": i += 100; continue
            if action == "exit": break
            continue

        # معالجة الإجابة
        try:
            if item['options'][int(user_input)-1] == item['correct']:
                print("✅ أصبت، بارك الله فيك.")
                score += 1
            else:
                print(f"❌ خطأ. الإجابة الصحيحة: {item['correct']}")
        except:
            print("⚠️ إدخال غير صحيح.")

        # --- الفاصل الروحاني (كل 20 سؤالاً) ---
        if (i + 1) % 20 == 0:
            current_w = ibn_ataa_wisdom[wisdom_ptr % len(ibn_ataa_wisdom)]
            speak_wisdom(current_w)
            wisdom_ptr += 1
            input("\nاضغط Enter للمتابعة بعد الحكمة...")

        i += 1

    print(f"\n🏁 تم الانتهاء! نتيجتك النهائية هي {score} من {i}")

if __name__ == "__main__":
    run_engine()
