import io
import re
import time
import urllib.parse
import uuid
import requests
import json
import os
from datetime import datetime, timedelta
from PIL import Image, ImageEnhance, ImageOps
import streamlit as st
from supabase import Client, create_client

# PDF oxumaq üçün pypdf yoxlaması
try:
    import pypdf
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# --- KASŞ VƏ LİMİT SİSTEMİ ---
LIMIT_FILE = "aligo_limits.json"
CACHE_FILE = "aligo_cache.json"

def get_user_limit(user_id):
    if not user_id:
        user_id = "guest_default"
    if os.path.exists(LIMIT_FILE):
        try:
            with open(LIMIT_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
        
    now = datetime.now().timestamp()
    
    if user_id not in data:
        data[user_id] = {"remaining": 100, "reset_time": 0}
        
    if data[user_id]["remaining"] <= 0 and now >= data[user_id]["reset_time"]:
        data[user_id]["remaining"] = 100
        data[user_id]["reset_time"] = 0
        
    return data[user_id]

def update_user_limit(user_id, remaining, reset_time):
    if not user_id:
        user_id = "guest_default"
    if os.path.exists(LIMIT_FILE):
        try:
            with open(LIMIT_FILE, "r") as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
    data[user_id] = {"remaining": remaining, "reset_time": reset_time}
    with open(LIMIT_FILE, "w") as f:
        json.dump(data, f)

# Ağıllı Keşləmə (Smart Caching) Funksiyaları
def get_cached_response(prompt_text):
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        clean_key = prompt_text.strip().lower()
        if clean_key in cache_data:
            return cache_data[clean_key]
    except:
        pass
    return None

def set_cached_response(prompt_text, response_text):
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
        else:
            cache_data = {}
        clean_key = prompt_text.strip().lower()
        cache_data[clean_key] = response_text
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except:
        pass

# --- SƏHİFƏ TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(
    page_title="AliGo - Süni İntellekt Mərkəzi",
    page_icon="⚡",
    layout="centered",
)

# --- GROQ VƏ SUPABASE QOŞULMASI ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("⚠️ GROQ_API_KEY Streamlit Secrets bölməsində tapılmadı! Lütfən Settings->Secrets hissəsinə əlavə edin.")

SUPABASE_URL = "https://iqfxtorbnjvnqsdgloyd.supabase.co"
SUPABASE_KEY = "sb_publishable_dF7WkdLq8ohQrVkl4SDlHw_w_4os4pt"

supabase: Client = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase Qoşulma Xətası: {e}")

# --- STİLLƏR VƏ VİZUAL DİZAYN ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(10, 15, 35, 0.4), rgba(5, 10, 25, 0.8)), 
                    url('https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=3840&q=100');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    .pro-badge-container {
        display: flex;
        justify-content: center;
        gap: 15px;
        margin-bottom: 10px;
    }
    .pro-badge {
        background: linear-gradient(135deg, rgba(0, 242, 254, 0.2), rgba(168, 85, 247, 0.2));
        border: 1px solid rgba(0, 242, 254, 0.6);
        padding: 6px 16px;
        border-radius: 20px;
        color: #00f2fe;
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
        animation: pulseGlow 2s infinite alternate;
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 0 10px rgba(0, 242, 254, 0.2); }
        100% { box-shadow: 0 0 22px rgba(168, 85, 247, 0.6); }
    }

    .aligo-logo {
        text-align: center;
        font-size: 5.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -1px;
        margin-top: -10px;
        margin-bottom: 5px;
        background: linear-gradient(45deg, #00f2fe, #4facfe, #a855f7, #22c55e, #f43f5e, #00f2fe);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: textShine 4s linear infinite, floatAnim 3s ease-in-out infinite;
        filter: drop-shadow(0px 10px 25px rgba(0, 242, 254, 0.6));
    }

    @keyframes textShine {
        to { background-position: 200% center; }
    }

    @keyframes floatAnim {
        0%, 100% { transform: translateY(0px); filter: drop-shadow(0px 10px 25px rgba(0, 242, 254, 0.6)); }
        50% { transform: translateY(-12px); filter: drop-shadow(0px 20px 35px rgba(168, 85, 247, 0.9)); }
    }

    @keyframes spinRing {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }

    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 15px;
    }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }

    .user-message-box {
        background: rgba(0, 242, 254, 0.1);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 242, 254, 0.5);
        box-shadow: 0 8px 32px 0 rgba(0, 242, 254, 0.2);
        padding: 14px 20px;
        border-radius: 20px 20px 4px 20px;
        max-width: 75%;
        color: #ffffff;
        font-family: 'Segoe UI', sans-serif;
        font-size: 1.05rem;
    }

    .ai-message-box {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        padding: 16px 22px;
        border-radius: 20px 20px 20px 4px;
        max-width: 85%;
        color: #f8fafc;
        font-family: 'Segoe UI', sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE TƏNZİMLƏMƏLƏRİ ---
if "app_mode" not in st.session_state:
    st.session_state.app_mode = "AliGo (Standard)"

if "guest_plan" not in st.session_state:
    st.session_state.guest_plan = "Pro"

if "show_aliai" not in st.session_state:
    st.session_state.show_aliai = False

if "trigger_prompt" not in st.session_state:
    st.session_state.trigger_prompt = None

if "ai_temp" not in st.session_state:
    st.session_state.ai_temp = 0.7

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if "user_info" not in st.session_state:
    st.session_state.user_info = None

if "ai_persona" not in st.session_state:
    st.session_state.ai_persona = "Programmer Mode"

if "custom_system_prompt" not in st.session_state:
    st.session_state.custom_system_prompt = ""

if "show_file_uploader" not in st.session_state:
    st.session_state.show_file_uploader = False

# --- DİL SEÇİMİ ---
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "Azərbaycan"

translations = {
    "Azərbaycan": {
        "title": "AliGo - Süni İntellekt Mərkəzi",
        "subtitle": "Süni İntellekt və Söhbət Mərkəzi",
        "new_chat": "Yeni Söhbət",
        "ask_placeholder": "AliGo-dan soruş...",
        "profile": "Profil və Yaddaş",
        "history": "Söhbət Tarixçəsi",
        "settings": "Ekspert Tənzimləmələri",
        "google_login": "Google ilə Giriş Et",
        "google_logout": "Google-dan Çıxış",
        "logout": "Çıxış Et",
        "name_label": "Adınız:",
        "email_label": "Email (istəyə bağlı):",
        "login_btn": "Daxil ol",
        "download_txt": "Söhbəti TXT olaraq yüklə",
        "download_md": "Söhbəti Markdown olaraq yüklə",
        "creativity": "AI Yaradıcılıq",
        "persona": "Ekspert Rejimi / Asistent:",
        "q1": "❓ Sual Soruş",
        "q2": "💻 Kod Yaz & Debug",
        "q3": "🎨 Şəkil Yarat",
        "q4": "🎵 Musiqi Hazırla",
        "close_panel": "❌ Paneli Bağla",
        "add_file": "PDF, Şəkil və ya Kod Faylı yüklə",
        "lang_select": "Dil / Language / Язык",
    },
    "English": {
        "title": "AliGo - AI Center",
        "subtitle": "Artificial Intelligence & Chat Center",
        "new_chat": "New Chat",
        "ask_placeholder": "Ask AliGo...",
        "profile": "Profile & Memory",
        "history": "Chat History",
        "settings": "Expert Settings",
        "google_login": "Sign in with Google",
        "google_logout": "Sign out from Google",
        "logout": "Log Out",
        "name_label": "Your Name:",
        "email_label": "Email (optional):",
        "login_btn": "Log In",
        "download_txt": "Download Chat as TXT",
        "download_md": "Download Chat as Markdown",
        "creativity": "AI Creativity",
        "persona": "Expert Mode / Assistant:",
        "q1": "❓ Ask a Question",
        "q2": "💻 Write Code & Debug",
        "q3": "🎨 Generate Image",
        "q4": "🎵 Create Music",
        "close_panel": "❌ Close Panel",
        "add_file": "Upload PDF, Image or Code File",
        "lang_select": "Language",
    },
    "Русский": {
        "title": "AliGo - Центр ИИ",
        "subtitle": "Центр искусственного интеллекта и чата",
        "new_chat": "Новый чат",
        "ask_placeholder": "Спросите AliGo...",
        "profile": "Профиль и Память",
        "history": "История чатов",
        "settings": "Настройки эксперта",
        "google_login": "Войти через Google",
        "google_logout": "Выйти из Google",
        "logout": "Выйти",
        "name_label": "Ваше имя:",
        "email_label": "Email (необязательно):",
        "login_btn": "Войти",
        "download_txt": "Скачать чат в TXT",
        "download_md": "Скачать чат в Markdown",
        "creativity": "Креативность ИИ",
        "persona": "Экспертный режим / Ассистент:",
        "q1": "❓ Задать вопрос",
        "q2": "💻 Написать код и отладка",
        "q3": "🎨 Создать рисунок",
        "q4": "🎵 Создать музыку",
        "close_panel": "❌ Закрыть панель",
        "add_file": "Загрузить PDF, картинку или файл кода",
        "lang_select": "Язык",
    },
}

lang = translations[st.session_state.ui_lang]

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": lang["new_chat"], "messages": []}
    st.session_state.current_chat_id = first_id

# --- SUPABASE QEYD VƏ UZUNMÜDDƏTLİ YADDAŞ ---
def save_user_to_db(name, email, interests=""):
    if not supabase:
        return
    try:
        clean_email = email or f"{name.lower().replace(' ', '')}@user.com"
        res = supabase.table("users_log").select("email").eq("email", clean_email).execute()
        if not res.data:
            supabase.table("users_log").insert({
                "name": name,
                "email": clean_email,
                "user_code": f"PRO-USR-{str(uuid.uuid4())[:8].upper()}",
                "interests": interests
            }).execute()
        st.session_state["logged_to_db"] = True
    except Exception:
        pass

def save_feedback_to_db(user_name, feedback_type, message_text):
    if not supabase:
        return
    try:
        supabase.table("likes_log").insert({
            "user_name": user_name,
            "feedback_type": feedback_type,
            "message": str(message_text)[:200],
        }).execute()
    except Exception as e:
        st.error(f"Xəta: {e}")

# --- İSTİFADƏÇİ MƏLUMATLARININ TƏYİNİ ---
user_name = None
user_email = None

try:
    if hasattr(st, "experimental_user") and getattr(st.experimental_user, "is_logged_in", False):
        user_name = getattr(st.experimental_user, "name", None) or getattr(st.experimental_user, "email", "").split("@")[0]
        user_email = getattr(st.experimental_user, "email", None)
    elif hasattr(st, "user") and getattr(st.user, "is_logged_in", False):
        user_name = st.user.name or st.user.email.split("@")[0]
        user_email = st.user.email
except Exception:
    pass

if not user_name and st.session_state.get("user_info"):
    user_name = st.session_state.user_info.get("name")
    user_email = st.session_state.user_info.get("email")

if not user_name:
    if "auto_guest_id" not in st.session_state:
        st.session_state.auto_guest_id = f"User_{str(uuid.uuid4())[:5]}"
    user_name = st.session_state.auto_guest_id
    user_email = f"{user_name.lower()}@aligo.ai"

if "logged_to_db" not in st.session_state:
    save_user_to_db(user_name, user_email)

# --- EKRANDA ASILI QALAN LİMİT PƏNCƏRƏSİ (Yalnız Pro Rejimdə) ---
if st.session_state.app_mode == "AliGo Pro Flash":
    limit_data_initial = get_user_limit(user_name)
    if limit_data_initial["remaining"] <= 0 and "limit_alert_shown" not in st.session_state:
        @st.dialog("⏳ Pro Limitiniz Bitdi!")
        def limit_lock_dialog():
            reset_dt = datetime.fromtimestamp(limit_data_initial['reset_time'])
            st.error("Siz günlük 100 Pro sual limitinizi doldurmusunuz.")
            st.info(f"Lütfən 12 saat sonra, {reset_dt.strftime('%d.%m.%Y %H:%M')} tarixində yenidən cəhd edin.")
        limit_lock_dialog()
        st.session_state.limit_alert_shown = True

# --- MİNİMALİST ANİMASİYA ---
def show_small_spinner():
    st.markdown(
        """
        <div style="display: flex; align-items: center; gap: 12px; margin: 12px 0;">
            <div style="width: 30px; height: 30px; border: 3px solid rgba(0, 242, 254, 0.2); border-top-color: #00f2fe; border-bottom-color: #a855f7; border-radius: 50%; animation: spinRing 1s linear infinite;"></div>
            <span style="color: #00f2fe; font-family: 'Segoe UI', sans-serif; font-size: 0.95rem; font-weight: bold; text-shadow: 0 0 10px rgba(0,242,254,0.7);">AliGo analiz edir...</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# --- ŞƏKİL VƏ MUSİQİ NƏZARƏTİ ---
def is_image_request(prompt_text):
    if not isinstance(prompt_text, str):
        return False
    keywords = [
        "şəkil çək", "şəkil yarat", "şəklini çək", "draw", "generate image",
        "resim çək", "şəklini yarat", "нарисуй", "создай изображение", "resim çiz"
    ]
    return any(kw in prompt_text.lower() for kw in keywords)

def is_music_request(prompt_text):
    if not isinstance(prompt_text, str):
        return False
    keywords = [
        "musiqi yarat", "mahnı yaz", "beat yarat", "musiqi bəstələ",
        "создай музыку", "напиши песню", "make music", "generate music", "create beat"
    ]
    return any(kw in prompt_text.lower() for kw in keywords)

def generate_image_url(prompt_text, style="Default"):
    style_modifiers = {
        "Default": "",
        "Anime / Manga": ", anime style, studio ghibli, vibrant colors",
        "3D Render / Cyberpunk": ", 3d render, Unreal Engine 5, cyberpunk, neon lights",
        "Realistic / Photo": ", ultra realistic, 8k resolution, photorealistic",
        "Oil Painting": ", classical oil painting texture, fine art",
    }
    full_prompt = prompt_text + style_modifiers.get(style, "")
    encoded_prompt = urllib.parse.quote(full_prompt)
    return f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={uuid.uuid4().int % 10000}"

def edit_user_image(pil_img, action_type):
    try:
        img = pil_img.copy()
        if action_type == "Qara-Ağ (Grayscale)":
            img = ImageOps.grayscale(img).convert("RGB")
        elif action_type == "Parlaqlığı Artır":
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(1.5)
        elif action_type == "Kontrastı Artır":
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.6)
        elif action_type == "Tərsinə Çevir (Invert)":
            if img.mode == "RGBA":
                img = img.convert("RGB")
            img = ImageOps.invert(img)
        elif action_type == "Kvadrat Kəs (Thumbnail)":
            img.thumbnail((512, 512))
        return img
    except Exception:
        return pil_img

def generate_music_track(prompt_text):
    tracks = [
        ("Lo-Fi Chill Beat", "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"),
        ("Cyberpunk Synthwave", "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3"),
        ("Epic Cinematic Orchestra", "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3"),
        ("Modern Trap Beat", "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3"),
    ]
    import random
    selected_name, selected_url = random.choice(tracks)
    return selected_name, selected_url

# --- GROQ ENGINE & TOKEN OPTİMİZASİYASI ---
def ask_groq_ai(messages_history):
    if not GROQ_API_KEY:
        return "⚠️ GROQ_API_KEY Secrets bölməsində tapılmadı!"

    is_pro = st.session_state.app_mode == "AliGo Pro Flash"

    base_identity = (
        "SƏNİN ADIN ALİGO-DUR!\n"
        "1. SALAMLAŞMA QAYDASI: Yalnız və yalnız söhbətin ƏN İLK mesajında (tarixçə boş olanda və ya ilk dəfə yazanda) "
        "nəzakətlə salam ver və özünü AliGo olaraq təqdim et. Əgər bu, davam edən söhbətdirsə, heç vaxt təzədən özünü tanıtma! Birbaşa sualın cavabına keç.\n"
        "2. KİMLİK: Heç vaxt Google, OpenAI və ya ChatGPT olduğunu demə. Sən AliGo Süni İntellekt mərkəzisən!\n"
    )

    if is_pro:
        persona_map = {
            "Programmer Mode": "Xüsusi Ekspert Rejimi: Programmer Mode. Kod yazdırmaq, struktur qurmaq və səhvləri (debug) tapmaq üçün maksimum optimallaşdırılmış ekspert rejimisən. Təmiz, səmərəli və qüsursuz kod yaz.\n",
            "Study Helper": "Xüsusi Ekspert Rejimi: Study Helper. Dərsləri, elmi məqalələri, PDF kitabları izah edən, bilikləri sadələşdirən və testlər/suallar tərtib edən təhsil köməkçisən.\n",
            "Content Creator": "Xüsusi Ekspert Rejimi: Content Creator. YouTube ssenariləri, sosial media postları, cəlbedici başlıqlar və marketinq mətnləri yazan yaradıcı ekspert rejimisən.\n",
            "Custom Prompt": f"Xüsusi Prompt Rejimi: {st.session_state.custom_system_prompt}\n" if st.session_state.custom_system_prompt else "Standart AliGo Pro Ekspert Rejimi.\n"
        }
        persona_text = persona_map.get(st.session_state.ai_persona, persona_map["Programmer Mode"])
        pro_instruction = (
            "🔥 PRO ENGINE AKTİVDİR: Sən hazırda AliGo-nun Pro versiyasısan. "
            "Hər bir suala son dərəcə əhatəli, analitik, elmi və texniki dəqiqliklə, addım-addım izahatlarla, real nümunələrlə cavab ver.\n"
        )
        system_instruction = base_identity + persona_text + pro_instruction
    else:
        system_instruction = base_identity + "Standart AliGo köməkçisisən. Suallara səlist və faydalı cavab ver."

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    formatted_messages = [{"role": "system", "content": system_instruction}]
    
    # TOKEN QƏNAƏTİ: Tarixçənin qısaldılması (Yalnız son 4-5 mesaj göndərilir)
    trimmed_history = messages_history[-5:] if len(messages_history) > 5 else messages_history

    for m in trimmed_history:
        role = "user" if m["role"] == "user" else "assistant"
        content_val = m["content"]
        if isinstance(content_val, list):
            txt_part = next((item for item in content_val if isinstance(item, str)), "")
            formatted_messages.append({"role": role, "content": txt_part})
        else:
            formatted_messages.append({"role": role, "content": str(content_val)})

    models_to_try = [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "mixtral-8x7b-32768"
    ]

    last_error = ""
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": formatted_messages,
            "temperature": st.session_state.ai_temp,
            "max_tokens": 4096
        }
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=15
            )
            if res.status_code == 200:
                return res.json()["choices"][0]["message"]["content"]
            else:
                last_error = f"HTTP {res.status_code}: {res.text}"
        except Exception as err:
            last_error = str(err)
            continue

    return f"⚠️ AliGo Engine Xətası: {last_error}"

# --- SOL PANEL ---
st.sidebar.markdown(f"### 🌐 {lang['lang_select']}")
st.session_state.ui_lang = st.sidebar.selectbox(
    "",
    ["Azərbaycan", "English", "Русский"],
    index=["Azərbaycan", "English", "Русский"].index(st.session_state.ui_lang),
    label_visibility="collapsed",
)
lang = translations[st.session_state.ui_lang]

# --- REJİM SEÇİMİ (KİÇİK PƏNCƏRƏ / SEÇİM HİSSƏSİ) ---
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚡ Rejim Seçimi")
st.session_state.app_mode = st.sidebar.selectbox(
    "Rejim",
    ["AliGo (Standard)", "AliGo Pro Flash"],
    index=0 if st.session_state.app_mode == "AliGo (Standard)" else 1,
    label_visibility="collapsed"
)

st.sidebar.markdown(f"### 🔐 {lang['profile']}")

is_google_logged = False
try:
    if (hasattr(st, "experimental_user") and getattr(st.experimental_user, "is_logged_in", False)) or (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
        is_google_logged = True
except Exception:
    pass

if user_name and not user_name.startswith("User_"):
    st.sidebar.success(f"👤 {user_name}")
    if user_email:
        st.sidebar.caption(f"📧 {user_email}")

    if is_google_logged:
        if st.sidebar.button(f"🚪 {lang['google_logout']}", use_container_width=True):
            if hasattr(st, "logout"):
                try:
                    st.logout()
                except Exception:
                    pass
            st.rerun()
    else:
        if st.sidebar.button(f"🚪 {lang['logout']}", use_container_width=True):
            st.session_state.user_info = None
            if "logged_to_db" in st.session_state:
                del st.session_state["logged_to_db"]
            st.rerun()
else:
    if st.sidebar.button(f"🔵 {lang['google_login']}", use_container_width=True):
        if hasattr(st, "login"):
            try:
                st.login("google")
            except Exception as e:
                st.sidebar.error(f"Giriş xətası: {e}")

    with st.sidebar.expander(f"👤 {lang['name_label']} & Yaddaş"):
        input_name = st.text_input(lang["name_label"], value=user_name if not user_name.startswith("User_") else "")
        input_email = st.text_input(lang["email_label"], value=user_email if "@aligo.ai" not in user_email else "")
        user_interests = st.text_area("Maraqlarınız və Üstünlükləriniz:", placeholder="Məs: Python, AI...")
        if st.button(lang["login_btn"]):
            if input_name:
                st.session_state.user_info = {
                    "name": input_name,
                    "email": input_email or f"{input_name.lower().replace(' ', '')}@user.com",
                }
                save_user_to_db(input_name, input_email, user_interests)
                st.rerun()

# --- ƏGƏR PRO FLASH REJİMDƏDİRSƏ - LİMİT VİZUAL BAR VƏ ƏLAVƏ TƏNZİMLƏMƏLƏR GÖRÜNSÜN ---
if st.session_state.app_mode == "AliGo Pro Flash":
    st.sidebar.markdown("---")
    limit_data = get_user_limit(user_name)
    st.sidebar.markdown(f"### ⚡ Günlük Pro Limitiniz: {limit_data['remaining']} / 100")
    st.sidebar.progress(max(0, limit_data['remaining']) / 100.0)
    if limit_data['remaining'] <= 0:
        reset_dt = datetime.fromtimestamp(limit_data['reset_time'])
        st.sidebar.error(f"Limit bitib! Yenilənmə: {reset_dt.strftime('%H:%M')}")

st.sidebar.markdown("---")
st.sidebar.markdown(f"### 💬 {lang['history']}")

if st.sidebar.button(f"➕ {lang['new_chat']}", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    st.session_state.chats[new_id] = {"title": lang["new_chat"], "messages": []}
    st.session_state.current_chat_id = new_id
    st.session_state.show_aliai = True
    st.rerun()

for cid, cdata in list(st.session_state.chats.items()):
    col_a, col_b = st.sidebar.columns([4, 1])
    with col_a:
        is_active = cid == st.session_state.current_chat_id
        btn_label = f"📍 {cdata['title']}" if is_active else cdata["title"]
        if st.button(btn_label, key=f"chat_{cid}", use_container_width=True):
            st.session_state.current_chat_id = cid
            st.session_state.show_aliai = True
            st.rerun()
    with col_b:
        if st.sidebar.button("🗑️", key=f"del_{cid}"):
            del st.session_state.chats[cid]
            if st.session_state.current_chat_id == cid:
                if st.session_state.chats:
                    st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                else:
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.chats[new_id] = {"title": lang["new_chat"], "messages": []}
                    st.session_state.current_chat_id = new_id
            st.rerun()

current_chat_data = st.session_state.chats.get(
    st.session_state.current_chat_id,
    {"title": lang["new_chat"], "messages": []},
)
if current_chat_data["messages"] and st.session_state.app_mode == "AliGo Pro Flash":
    chat_export_txt = ""
    chat_export_md = "# AliGo Pro Chat Export\n\n"
    for m in current_chat_data["messages"]:
        role_name = "Sən" if m["role"] == "user" else "AliGo"
        txt_content = m["content"] if isinstance(m["content"], str) else "[Şəkil və ya Fayl məzmunu]"
        chat_export_txt += f"{role_name}: {txt_content}\n\n"
        chat_export_md += f"**{role_name}**: {txt_content}\n\n---\n"

    col_exp1, col_exp2 = st.sidebar.columns(2)
    with col_exp1:
        st.download_button(
            label=f"📥 TXT",
            data=chat_export_txt,
            file_name=f"{current_chat_data['title']}.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_exp2:
        st.download_button(
            label=f"📥 Markdown",
            data=chat_export_md,
            file_name=f"{current_chat_data['title']}.md",
            mime="text/markdown",
            use_container_width=True,
        )

if st.session_state.app_mode == "AliGo Pro Flash":
    with st.sidebar.expander(f"⚙️ {lang['settings']}"):
        st.session_state.ai_temp = st.slider(lang["creativity"], 0.0, 1.0, st.session_state.ai_temp, 0.1)
        st.session_state.ai_persona = st.selectbox(
            lang["persona"],
            [
                "Programmer Mode",
                "Study Helper",
                "Content Creator",
                "Custom Prompt"
            ],
        )
        if st.session_state.ai_persona == "Custom Prompt":
            st.session_state.custom_system_prompt = st.text_area("Şəxsi System Prompt daxil et:", value=st.session_state.custom_system_prompt)

        st.markdown("---")
        st.markdown("🎨 **Şəkil Yaratma Üslubu:**")
        st.session_state.image_style = st.selectbox(
            "Üslub",
            ["Default", "Anime / Manga", "3D Render / Cyberpunk", "Realistic / Photo", "Oil Painting"],
            label_visibility="collapsed",
        )

# --- ƏSAS EKRAN ---
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
    st.markdown(f"<h4 style='color: #00f2fe; margin-top: 5px;'>{lang['title']}</h4>", unsafe_allow_html=True)

with col_top2:
    if user_name and not user_name.startswith("User_"):
        st.markdown(
            f"""
                <div style="background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; padding: 6px 12px; border-radius: 12px; text-align: center; color: #fff; font-weight: bold; font-size: 0.95rem;">
                    👤 {user_name}
                </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if st.button("🤖 Panel"):
            st.session_state.show_aliai = not st.session_state.show_aliai
            st.rerun()

# Əgər Pro Flash rejimi aktivdirsə, əlavə vizuallar göstər
if st.session_state.app_mode == "AliGo Pro Flash":
    st.markdown(
        """
        <div class="pro-badge-container">
            <div class="pro-badge">⚡ Pro Flash Active</div>
            <div class="pro-badge">🚀 Lightning Fast Mode</div>
            <div class="pro-badge">🧠 Advanced Memory On</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="aligo-logo">AliGo</div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.15rem; font-weight: bold; margin-bottom: 25px; filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));">{lang['subtitle']}</p>
""",
    unsafe_allow_html=True,
)

# --- SÜRƏTLİ DÜYMƏLƏR ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
    if st.button(lang["q1"], use_container_width=True):
        st.session_state.trigger_prompt = "Mənə maraqlı bir mövzu haqqında ətraflı məlumat ver."
        st.session_state.show_aliai = True
        st.rerun()
with col_q2:
    if st.button(lang["q2"], use_container_width=True):
        st.session_state.trigger_prompt = "Mənə sadə bir Python kodu yaz."
        st.session_state.show_aliai = True
        st.rerun()
with col_q3:
    if st.button(lang["q3"], use_container_width=True):
        st.session_state.trigger_prompt = "Gözəl bir təbiət mənzərəsi çək."
        st.session_state.show_aliai = True
        st.rerun()
with col_q4:
    if st.button(lang["q4"], use_container_width=True):
        st.session_state.trigger_prompt = "Mənə dinləmək üçün musiqi tövsiyə et."
        st.session_state.show_aliai = True
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(
        st.session_state.current_chat_id,
        {"title": lang["new_chat"], "messages": []},
    )

    new_chat_title = st.text_input("Söhbətin Adı / Chat Title:", value=current_chat["title"], key="rename_chat_input")
    if new_chat_title != current_chat["title"]:
        current_chat["title"] = new_chat_title
        st.rerun()

    if st.session_state.trigger_prompt:
        p_text = st.session_state.trigger_prompt
        st.session_state.trigger_prompt = None
        current_chat["messages"].append({"role": "user", "content": p_text})
        if current_chat["title"] == lang["new_chat"]:
            current_chat["title"] = p_text[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner()

        is_pro = st.session_state.app_mode == "AliGo Pro Flash"
        
        if is_pro:
            limit_data_check = get_user_limit(user_name)
            if limit_data_check["remaining"] > 0:
                cached_res = get_cached_response(p_text)
                if cached_res:
                    response = cached_res + "\n\n*(⚡ Sürətli Keş yaddaşından dərhal qaytarıldı)*"
                else:
                    selected_style = st.session_state.get("image_style", "Default")
                    if is_image_request(p_text):
                        img_url = generate_image_url(p_text, selected_style)
                        response = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
                    elif is_music_request(p_text):
                        track_name, track_url = generate_music_track(p_text)
                        response = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
                    else:
                        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
                        response = ask_groq_ai(history_for_api)
                        set_cached_response(p_text, response)
                    
                new_remaining = limit_data_check["remaining"] - 1
                reset_time = limit_data_check["reset_time"]
                if new_remaining <= 0:
                    reset_time = (datetime.now() + timedelta(hours=12)).timestamp()
                update_user_limit(user_name, new_remaining, reset_time)
            else:
                reset_dt = datetime.fromtimestamp(limit_data_check['reset_time'])
                response = f"🛑 **Limitiniz bitdi!** Siz günlük 100 sual limitinizi doldurmusunuz. Lütfən **12 saat sonra** ({reset_dt.strftime('%H:%M')}) yenidən cəhd edin."
        else:
            history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
            response = ask_groq_ai(history_for_api)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    for idx, message in enumerate(current_chat["messages"]):
        if message["role"] == "user":
            display_content = message["content"]
            if isinstance(display_content, list):
                img_display = next((item for item in display_content if isinstance(item, Image.Image)), None)
                text_display = next((item for item in display_content if isinstance(item, str)), "")
                if img_display:
                    st.image(img_display, width=250)
                display_content = f"📷 [Şəkil/Fayl analizi] <br>{text_display}"

            st.markdown(
                f"""
                    <div class="chat-row user">
                        <div class="user-message-box"><b>Sən:</b><br>{display_content}</div>
                    </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                    <div class="chat-row assistant">
                        <div class="ai-message-box">
                """,
                unsafe_allow_html=True,
            )

            msg_content = str(message["content"])
            if "__IMAGE_URL__" in msg_content:
                parts = msg_content.split("__IMAGE_URL__")
                st.markdown(parts[0])
                if len(parts) > 1:
                    img_link = parts[1].strip()
                    st.markdown(f'<img src="{img_link}" style="width:100%; border-radius:15px; margin-top:10px; margin-bottom:10px; box-shadow: 0 4px 20px rgba(0,242,254,0.3);" />', unsafe_allow_html=True)
                    st.markdown(f"[🔗 Şəklin birbaşa keçidi]({img_link})")
            elif "__MUSIC_URL__" in msg_content:
                parts = msg_content.split("__MUSIC_URL__")
                st.markdown(parts[0])
                if len(parts) > 1:
                    st.audio(parts[1].strip(), format="audio/mp3")
            else:
                st.markdown(msg_content)

            st.markdown(
                """
                        </div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.app_mode == "AliGo Pro Flash":
                c_like, c_dislike, c_space = st.columns([1, 1, 6])
                with c_like:
                    if st.button("👍", key=f"like_{idx}"):
                        save_feedback_to_db(user_name, "Bəyəndi 👍", str(message["content"]))
                        st.toast("🎉 Rəyiniz üçün təşəkkürlər!", icon="👍")
                with c_dislike:
                    if st.button("👎", key=f"dislike_{idx}"):
                        save_feedback_to_db(user_name, "Bəyənmədi 👎", str(message["content"]))
                        st.toast("⚠️ Qeyd olundu! Təşəkkürlər.", icon="🔧")

            st.markdown("---")

    if st.session_state.app_mode == "AliGo Pro Flash":
        col_input_ctrls1, col_input_ctrls2 = st.columns([1, 5])
        with col_input_ctrls1:
            if st.button("➕ Fayl/Şəkil/PDF", use_container_width=True):
                st.session_state.show_file_uploader = not st.session_state.show_file_uploader

        with col_input_ctrls2:
            st.markdown(f"<div style='color: #00f2fe; font-weight: bold; padding-top: 6px;'>🎯 Aktiv Rejim: {st.session_state.ai_persona}</div>", unsafe_allow_html=True)

        uploaded_file = None
        if st.session_state.show_file_uploader:
            uploaded_file = st.file_uploader(
                lang["add_file"],
                type=["png", "jpg", "jpeg", "txt", "py", "json", "pdf"],
            )

            if uploaded_file is not None:
                file_extension = uploaded_file.name.split(".")[-1].lower()
                if file_extension in ["png", "jpg", "jpeg"]:
                    st.markdown("🛠️ **Şəkil Vision Analizi:**")
                    edit_action = st.selectbox(
                        "Effekt seç",
                        ["Seçim edin...", "Qara-Ağ (Grayscale)", "Parlaqlığı Artır", "Kontrastı Artır", "Tərsinə Çevir (Invert)", "Kvadrat Kəs (Thumbnail)"],
                        key="edit_action_box",
                    )
                    if edit_action != "Seçim edin...":
                        try:
                            raw_img = Image.open(uploaded_file)
                            processed_img = edit_user_image(raw_img, edit_action)
                            st.image(processed_img, caption=f"Redaktə olundu: {edit_action}", width=300)

                            buf = io.BytesIO()
                            processed_img.save(buf, format="PNG")
                            byte_im = buf.getvalue()
                            st.download_button(
                                label="📥 Redaktə olunan şəkli yüklə",
                                data=byte_im,
                                file_name="aligo_edited_image.png",
                                mime="image/png",
                            )
                        except Exception as ex:
                            st.error(f"Şəkil redaktə xətası: {ex}")
    else:
        uploaded_file = None

    if prompt := st.chat_input(lang["ask_placeholder"]):
        user_message_content = prompt

        if st.session_state.app_mode == "AliGo Pro Flash" and uploaded_file is not None:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            if file_extension in ["png", "jpg", "jpeg"]:
                try:
                    pil_image = Image.open(uploaded_file)
                    user_message_content = [pil_image, prompt if prompt else "Bu şəkli analiz et."]
                except Exception:
                    user_message_content = prompt
            elif file_extension == "pdf":
                if PDF_SUPPORT:
                    try:
                        reader = pypdf.PdfReader(uploaded_file)
                        pdf_text = ""
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""
                        user_message_content = f"{prompt}\n\n[PDF Sənəd Məzmunu - {uploaded_file.name}]:\n{pdf_text[:10000]}"
                    except Exception as e:
                        user_message_content = f"{prompt}\n[PDF oxunma xətası: {e}]"
                else:
                    user_message_content = f"{prompt}\n[PDF fayl yükləndi, lakin pypdf kitabxanası quraşdırılmayıb]"
            else:
                try:
                    file_text_extra = uploaded_file.read().decode("utf-8")
                    user_message_content = f"{prompt}\n\n[Kod/Fayl Məzmunu - {uploaded_file.name}]:\n```\n{file_text_extra}\n```"
                except Exception:
                    user_message_content = f"{prompt}\n[Fayl əlavə edildi: {uploaded_file.name}]"

        current_chat["messages"].append({"role": "user", "content": user_message_content})
        if current_chat["title"] == lang["new_chat"]:
            current_chat["title"] = prompt[:20] + "..." if prompt else "Söhbət"

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner()

        is_pro = st.session_state.app_mode == "AliGo Pro Flash"

        if is_pro:
            limit_data_check2 = get_user_limit(user_name)
            if limit_data_check2["remaining"] > 0:
                cached_res = get_cached_response(prompt if prompt else "")
                if cached_res and not uploaded_file:
                    response = cached_res + "\n\n*(⚡ Sürətli Keş yaddaşından dərhal qaytarıldı)*"
                else:
                    selected_style = st.session_state.get("image_style", "Default")
                    if is_image_request(prompt if prompt else ""):
                        img_url = generate_image_url(prompt, selected_style)
                        response = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
                    elif is_music_request(prompt if prompt else ""):
                        track_name, track_url = generate_music_track(prompt)
                        response = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
                    else:
                        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
                        response = ask_groq_ai(history_for_api)
                        if not uploaded_file:
                            set_cached_response(prompt, response)
                    
                new_remaining = limit_data_check2["remaining"] - 1
                reset_time = limit_data_check2["reset_time"]
                if new_remaining <= 0:
                    reset_time = (datetime.now() + timedelta(hours=12)).timestamp()
                update_user_limit(user_name, new_remaining, reset_time)
            else:
                reset_dt = datetime.fromtimestamp(limit_data_check2['reset_time'])
                response = f"🛑 **Limitiniz bitdi!** Siz günlük 100 sual limitinizi doldurmusunuz. Lütfən **12 saat sonra** ({reset_dt.strftime('%H:%M')}) yenidən cəhd edin."
        else:
            history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
            response = ask_groq_ai(history_for_api)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    if st.button(lang["close_panel"]):
        st.session_state.show_aliai = False
        st.rerun()
else:
    if st.session_state.app_mode == "AliGo Pro Flash":
        col_main_ctrls1, col_main_ctrls2 = st.columns([1, 5])
        with col_main_ctrls1:
            if st.button("➕ Fayl/PDF", key="main_plus_btn", use_container_width=True):
                st.session_state.show_file_uploader = not st.session_state.show_file_uploader

        with col_main_ctrls2:
            st.markdown(f"<div style='color: #00f2fe; font-weight: bold; padding-top: 6px;'>🎯 Rejim: {st.session_state.ai_persona}</div>", unsafe_allow_html=True)

        if st.session_state.show_file_uploader:
            main_uploaded_file = st.file_uploader(
                lang["add_file"],
                type=["png", "jpg", "jpeg", "txt", "py", "json", "pdf"],
                key="main_file_up",
            )
            if main_uploaded_file is not None:
                file_extension = main_uploaded_file.name.split(".")[-1].lower()
                if file_extension in ["png", "jpg", "jpeg"]:
                    st.markdown("🛠️ **Şəkil Vision Analizi:**")
                    main_edit_action = st.selectbox(
                        "Effekt seç",
                        ["Seçim edin...", "Qara-Ağ (Grayscale)", "Parlaqlığı Artır", "Kontrastı Artır", "Tərsinə Çevir (Invert)", "Kvadrat Kəs (Thumbnail)"],
                        key="main_edit_action_box",
                    )
                    if main_edit_action != "Seçim edin...":
                        try:
                            raw_img = Image.open(main_uploaded_file)
                            processed_img = edit_user_image(raw_img, main_edit_action)
                            st.image(processed_img, caption=f"Redaktə olundu: {main_edit_action}", width=300)

                            buf = io.BytesIO()
                            processed_img.save(buf, format="PNG")
                            byte_im = buf.getvalue()
                            st.download_button(
                                label="📥 Redaktə olunan şəkli yüklə",
                                data=byte_im,
                                file_name="aligo_edited_image.png",
                                mime="image/png",
                                key="main_download_edited_img",
                            )
                        except Exception as ex:
                            st.error(f"Şəkil redaktə xətası: {ex}")
        else:
            main_uploaded_file = None
    else:
        main_uploaded_file = None

    search_query = st.text_input(
        "",
        placeholder=lang["ask_placeholder"],
        key="main_search",
        label_visibility="collapsed",
    )
    if search_query:
        st.session_state.show_aliai = True
        current_chat = st.session_state.chats[st.session_state.current_chat_id]

        user_message_content = search_query
        if st.session_state.app_mode == "AliGo Pro Flash" and main_uploaded_file is not None:
            file_extension = main_uploaded_file.name.split(".")[-1].lower()
            if file_extension in ["png", "jpg", "jpeg"]:
                try:
                    pil_image = Image.open(main_uploaded_file)
                    user_message_content = [pil_image, search_query]
                except Exception:
                    user_message_content = search_query
            elif file_extension == "pdf":
                if PDF_SUPPORT:
                    try:
                        reader = pypdf.PdfReader(main_uploaded_file)
                        pdf_text = ""
                        for page in reader.pages:
                            pdf_text += page.extract_text() or ""
                        user_message_content = f"{search_query}\n\n[PDF Sənəd Məzmunu - {main_uploaded_file.name}]:\n{pdf_text[:10000]}"
                    except Exception as e:
                        user_message_content = f"{search_query}\n[PDF oxunma xətası: {e}]"
                else:
                    user_message_content = f"{search_query}\n[PDF fayl yükləndi, lakin pypdf kitabxanası quraşdırılmayıb]"
            else:
                try:
                    file_text_extra = main_uploaded_file.read().decode("utf-8")
                    user_message_content = f"{search_query}\n\n[Fayl Məzmunu - {main_uploaded_file.name}]:\n```\n{file_text_extra}\n```"
                except Exception:
                    user_message_content = f"{search_query}\n[Fayl əlavə edildi: {main_uploaded_file.name}]"

        current_chat["messages"].append({"role": "user", "content": user_message_content})
        if current_chat["title"] == lang["new_chat"]:
            current_chat["title"] = search_query[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner()

        is_pro = st.session_state.app_mode == "AliGo Pro Flash"

        if is_pro:
            limit_data_check3 = get_user_limit(user_name)
            if limit_data_check3["remaining"] > 0:
                cached_res = get_cached_response(search_query)
                if cached_res and not main_uploaded_file:
                    ai_resp = cached_res + "\n\n*(⚡ Sürətli Keş yaddaşından dərhal qaytarıldı)*"
                else:
                    selected_style = st.session_state.get("image_style", "Default")
                    if is_image_request(search_query):
                        img_url = generate_image_url(search_query, selected_style)
                        ai_resp = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
                    elif is_music_request(search_query):
                        track_name, track_url = generate_music_track(search_query)
                        ai_resp = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
                    else:
                        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
                        ai_resp = ask_groq_ai(history_for_api)
                        if not main_uploaded_file:
                            set_cached_response(search_query, ai_resp)
                    
                new_remaining = limit_data_check3["remaining"] - 1
                reset_time = limit_data_check3["reset_time"]
                if new_remaining <= 0:
                    reset_time = (datetime.now() + timedelta(hours=12)).timestamp()
                update_user_limit(user_name, new_remaining, reset_time)
            else:
                reset_dt = datetime.fromtimestamp(limit_data_check3['reset_time'])
                ai_resp = f"🛑 **Limitiniz bitdi!** Siz günlük 100 sual limitinizi doldurmusunuz. Lütfən **12 saat sonra** ({reset_dt.strftime('%H:%M')}) yenidən cəhd edin."
        else:
            history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
            ai_resp = ask_groq_ai(history_for_api)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": ai_resp})
        st.rerun()
