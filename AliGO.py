import base64
import io
import re
import time
import urllib.parse
import uuid
from PIL import Image, ImageOps, ImageEnhance
import requests
import streamlit as st
from supabase import Client, create_client

# --- SƏHİFƏ TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(
    page_title="AliGo - Süni İntellekt və Media Mərkəzi",
    page_icon="⚡",
    layout="centered",
)

# --- SESSION STATE ---
if "guest_plan" not in st.session_state:
    st.session_state.guest_plan = "UltiPremium"

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
    st.session_state.ai_persona = "Python / Kod Mütəxəssisi"

if "show_file_uploader" not in st.session_state:
    st.session_state.show_file_uploader = False

# --- SUPABASE QOŞULMASI ---
SUPABASE_URL = "https://iqfxtorbnjvnqsdgloyd.supabase.co"
SUPABASE_KEY = "sb_publishable_dF7WkdLq8ohQrVkl4SDlHw_w_4os4pt"

supabase: Client = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception:
    pass

# --- STİLLƏR VƏ QALAKTİKA ARXA PLANI (CSS) ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: linear-gradient(rgba(10, 15, 35, 0.65), rgba(5, 10, 25, 0.88)), 
                    url('https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    .aligo-logo {
        text-align: center;
        font-size: 4.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -2px;
        margin-top: 5px;
        margin-bottom: 0px;
        background: linear-gradient(45deg, #00f2fe, #4facfe, #a855f7, #22c55e, #f43f5e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 4px 15px rgba(0, 242, 254, 0.4));
    }

    @keyframes aligo-wave {
        0%, 100% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 8px #00f2fe); }
        50% { transform: translateY(-5px) scale(1.05); filter: drop-shadow(0 0 15px #a855f7); }
    }

    .small-spinning-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 15px 0;
    }

    .small-spinning-logo {
        font-size: 1.8rem;
        font-weight: 900;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        animation: aligo-wave 1.2s infinite ease-in-out;
        display: inline-block;
    }

    .loading-text-small {
        color: #00f2fe;
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.5);
    }

    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
    }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }

    .user-message-box {
        background: rgba(0, 242, 254, 0.15);
        border: 1px solid rgba(0, 242, 254, 0.4);
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }

    .ai-message-box {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        color: #f1f5f9;
        font-family: 'Segoe UI', sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- DİL SEÇİMİ (AZ / EN / RU) ---
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "Azərbaycan"

translations = {
    "Azərbaycan": {
        "title": "AliGo - Süni İntellekt və Media Mərkəzi",
        "subtitle": "Süni İntellekt, Şəkil və Musiqi Mərkəzi",
        "new_chat": "Yeni Söhbət",
        "ask_placeholder": "AliGo-dan soruş və ya əmr ver...",
        "profile": "Profil",
        "history": "Söhbət Tarixçəsi",
        "settings": "Tənzimləmələr",
        "google_login": "Google ilə Giriş Et",
        "google_logout": "Google-dan Çıxış",
        "logout": "Çıxış Et",
        "name_label": "Adınız:",
        "email_label": "Email (istəyə bağlı):",
        "login_btn": "Daxil ol",
        "download_txt": "Söhbəti TXT olaraq yüklə",
        "creativity": "AI Yaradıcılıq",
        "persona": "AI Xarakteri (Persona):",
        "q1": "❓ Sual Soruş",
        "q2": "💻 Kod Yaz",
        "q3": "🎨 Şəkil Yarat",
        "q4": "🎵 Musiqi Hazırla",
        "close_panel": "❌ Paneli Bağla",
        "add_file": "Şəkil və ya fayl əlavə et",
        "thinking": "AliGo düşünür...",
        "searching": "AliGo araşdırır...",
        "replying": "AliGo cavab hazırlayır...",
        "lang_select": "Dil / Language / Язык",
    },
    "English": {
        "title": "AliGo - AI & Media Hub",
        "subtitle": "Artificial Intelligence, Image & Music Center",
        "new_chat": "New Chat",
        "ask_placeholder": "Ask AliGo or give a command...",
        "profile": "Profile",
        "history": "Chat History",
        "settings": "Settings",
        "google_login": "Sign in with Google",
        "google_logout": "Sign out from Google",
        "logout": "Log Out",
        "name_label": "Your Name:",
        "email_label": "Email (optional):",
        "login_btn": "Log In",
        "download_txt": "Download Chat as TXT",
        "creativity": "AI Creativity",
        "persona": "AI Persona:",
        "q1": "❓ Ask a Question",
        "q2": "💻 Write Code",
        "q3": "🎨 Generate Image",
        "q4": "🎵 Create Music",
        "close_panel": "❌ Close Panel",
        "add_file": "Add image or file",
        "thinking": "AliGo is thinking...",
        "searching": "AliGo is searching...",
        "replying": "AliGo is preparing a response...",
        "lang_select": "Language",
    },
    "Русский": {
        "title": "AliGo - Центр ИИ и Медиа",
        "subtitle": "Центр Искусственного Интеллекта, Картин и Музыки",
        "new_chat": "Новый чат",
        "ask_placeholder": "Спросите AliGo или дайте команду...",
        "profile": "Профиль",
        "history": "История чатов",
        "settings": "Настройки",
        "google_login": "Войти через Google",
        "google_logout": "Выйти из Google",
        "logout": "Выйти",
        "name_label": "Ваше имя:",
        "email_label": "Email (необязательно):",
        "login_btn": "Войти",
        "download_txt": "Скачать чат в TXT",
        "creativity": "Креативность ИИ",
        "persona": "Персонаж ИИ:",
        "q1": "❓ Задать вопрос",
        "q2": "💻 Написать код",
        "q3": "🎨 Создать рисунок",
        "q4": "🎵 Создать музыку",
        "close_panel": "❌ Закрыть панель",
        "add_file": "Добавить изображение или файл",
        "thinking": "AliGo думает...",
        "searching": "AliGo ищет...",
        "replying": "AliGo готовит ответ...",
        "lang_select": "Язык",
    },
}

lang = translations[st.session_state.ui_lang]

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": lang["new_chat"], "messages": []}
    st.session_state.current_chat_id = first_id

# --- SUPABASE QEYD FUNKSİYALARI ---
def save_user_to_db(name, email):
    if not supabase:
        return
    try:
        clean_email = email or f"{name.lower().replace(' ', '')}@user.com"
        res = (
            supabase.table("users_log")
            .select("email")
            .eq("email", clean_email)
            .execute()
        )
        if not res.data:
            supabase.table("users_log").insert({
                "name": name,
                "email": clean_email,
                "user_code": f"USR-{str(uuid.uuid4())[:8].upper()}",
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
    except Exception:
        pass


# --- İSTİFADƏÇİ MƏLUMATLARININ TƏYİNİ ---
user_name = None
user_email = None

try:
    if hasattr(st, "experimental_user") and getattr(
        st.experimental_user, "is_logged_in", False
    ):
        user_name = (
            getattr(st.experimental_user, "name", None)
            or getattr(st.experimental_user, "email", "").split("@")[0]
        )
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
        st.session_state.auto_guest_id = f"Qonaq_{str(uuid.uuid4())[:5]}"
    user_name = st.session_state.auto_guest_id
    user_email = f"{user_name.lower()}@aligo.app"

if "logged_to_db" not in st.session_state:
    save_user_to_db(user_name, user_email)

# --- KÖMƏKÇİ PROQRAM ---
def show_small_spinner(text="AliGo ağıllı cavab hazırlayır..."):
    st.markdown(
        f"""
        <div class="small-spinning-container">
            <div class="small-spinning-logo">
                <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
            </div>
            <div class="loading-text-small">{text}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )


def is_image_request(prompt_text):
    if not isinstance(prompt_text, str):
        return False
    keywords = [
        "şəkil çək",
        "şəkil yarat",
        "şəklini çək",
        "draw",
        "generate image",
        "resim çək",
        "yarad",
        "çək",
        "нарисуй",
        "создай изображение",
    ]
    return any(kw in prompt_text.lower() for kw in keywords)


def is_music_request(prompt_text):
    if not isinstance(prompt_text, str):
        return False
    keywords = [
        "musiqi",
        "mahnı",
        "beat",
        "melody",
        "musiqi yarat",
        "mahnı yaz",
        "музыка",
        "песня",
        "трек",
        "beat make",
        "sound track",
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
    return f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={uuid.uuid4().int % 10000}"


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


def clean_ai_response(text):
    if not isinstance(text, str):
        return text
    text = re.sub(
        r"<think\b[^>]*>.*?</think\s*>", "", text, flags=re.IGNORECASE | re.DOTALL
    )
    text = re.sub(
        r"<thinking\b[^>]*>.*?</thinking\s*>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    text = re.sub(r"</?think\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?thinking\b[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text


# --- ÇOXLU URL DƏSTƏKLƏYƏN ETİBARLI VƏ TƏKRARLI (RETRY) GET FUNKSİYASI ---
def ask_ai_text(messages_history, user_plan="UltiPremium"):
    last_msg = ""
    for m in reversed(messages_history):
        if m["role"] == "user":
            content = m["content"]
            if isinstance(content, str):
                last_msg = content
            break
    
    if not last_msg:
        last_msg = "Salam"

    encoded_prompt = urllib.parse.quote(last_msg)
    
    urls = [
        f"https://text.pollinations.ai/{encoded_prompt}?seed={uuid.uuid4().int % 10000}",
        f"https://api.allorigins.win/raw?url={urllib.parse.quote(f'https://text.pollinations.ai/{encoded_prompt}')}"
    ]
    
    for url in urls:
        for attempt in range(2):
            try:
                response = requests.get(url, timeout=25)
                if response.status_code == 200 and len(response.text.strip()) > 0:
                    return clean_ai_response(response.text)
            except Exception:
                pass
            time.sleep(1)
        
    return "⚠️ Server hazırda yüklənib və ya cavab verməkdə gecikir. Zəhmət olmasa bir qədər sonra yenidən cəhd edin."


# --- SOL PANEL ---
st.sidebar.markdown(f"### 🌐 {lang['lang_select']}")
st.session_state.ui_lang = st.sidebar.selectbox(
    "",
    ["Azərbaycan", "English", "Русский"],
    index=["Azərbaycan", "English", "Русский"].index(st.session_state.ui_lang),
    label_visibility="collapsed",
)
lang = translations[st.session_state.ui_lang]

st.sidebar.markdown(f"### 🔐 {lang['profile']}")

is_google_logged = False
try:
    if (
        hasattr(st, "experimental_user")
        and getattr(st.experimental_user, "is_logged_in", False)
    ) or (hasattr(st, "user") and getattr(st.user, "is_logged_in", False)):
        is_google_logged = True
except Exception:
    pass

if user_name and not user_name.startswith("Qonaq_"):
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

    with st.sidebar.expander(f"👤 {lang['name_label']} ..."):
        input_name = st.text_input(lang['name_label'])
        input_email = st.text_input(lang['email_label'])
        if st.button(lang['login_btn']):
            if input_name:
                st.session_state.user_info = {
                    "name": input_name,
                    "email": input_email
                    or f"{input_name.lower().replace(' ', '')}@user.com",
                }
                save_user_to_db(input_name, input_email)
                st.rerun()

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
                    st.session_state.current_chat_id = list(
                        st.session_state.chats.keys()
                    )[0]
                else:
                    new_id = str(uuid.uuid4())[:8]
                    st.session_state.chats[new_id] = {
                        "title": lang["new_chat"],
                        "messages": [],
                    }
                    st.session_state.current_chat_id = new_id
            st.rerun()

current_chat_data = st.session_state.chats.get(
    st.session_state.current_chat_id, {"title": lang["new_chat"], "messages": []}
)
if current_chat_data["messages"]:
    chat_export_text = ""
    for m in current_chat_data["messages"]:
        role_name = "Sən" if m["role"] == "user" else "AliGo"
        txt_content = (
            m["content"]
            if isinstance(m["content"], str)
            else "[Şəkil və ya Fayl məzmunu]"
        )
        chat_export_text += f"{role_name}: {txt_content}\n\n"

    st.sidebar.download_button(
        label=f"📥 {lang['download_txt']}",
        data=chat_export_text,
        file_name=f"{current_chat_data['title']}.txt",
        mime="text/plain",
        use_container_width=True,
    )

with st.sidebar.expander(f"⚙️ {lang['settings']}"):
    st.session_state.ai_temp = st.slider(
        lang["creativity"], 0.0, 1.0, st.session_state.ai_temp, 0.1
    )
    st.session_state.ai_persona = st.selectbox(
        lang["persona"],
        [
            "Python / Kod Mütəxəssisi",
            "Standart AliGo",
            "Oyun Dizayneri (Minecraft/Roblox)",
            "Musiqi və İncəsənət Generatoru",
        ],
    )

    st.markdown("---")
    st.markdown("🎨 **Şəkil Yaratma Üslubu:**")
    st.session_state.image_style = st.selectbox(
        "Üslub",
        [
            "Default",
            "Anime / Manga",
            "3D Render / Cyberpunk",
            "Realistic / Photo",
            "Oil Painting",
        ],
        label_visibility="collapsed",
    )

# --- ƏSAS EKRAN ---
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
    st.markdown(
        f"<h4 style='color: #00f2fe; margin-top: 5px;'>{lang['title']}</h4>",
        unsafe_allow_html=True,
    )

with col_top2:
    if user_name and not user_name.startswith("Qonaq_"):
        st.markdown(
            f"""
                <div style="background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; padding: 6px 12px; border-radius: 12px; text-align: center; color: #fff; font-weight: bold; font-size: 0.95rem;">
                    👤 {user_name}
                </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        if st.button("🤖 AliAI"):
            st.session_state.show_aliai = not st.session_state.show_aliai
            st.rerun()

st.markdown(
    f"""
    <div class="aligo-logo">AliGo</div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 20px;">{lang['subtitle']}</p>
""",
    unsafe_allow_html=True,
)

# --- SÜRƏTLİ DÜYMƏLƏR ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
    if st.button(lang["q1"], use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə maraqlı bir mövzu haqqında ətraflı məlumat ver."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q2:
    if st.button(lang["q2"], use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə peşəkar bir veb tətbiqi və ya simulyator kodu yaz."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q3:
    if st.button(lang["q3"], use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə gələcəyin texnoloji şəhərini göstərən möhtəşəm bir vizual yarat."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q4:
    if st.button(lang["q4"], use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə gümrah bir lo-fi və ya cyberpunk musiqi parçası hazırla."
        )
        st.session_state.show_aliai = True
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(
        st.session_state.current_chat_id,
        {"title": lang["new_chat"], "messages": []},
    )

    new_chat_title = st.text_input(
        "Söhbətin Adı / Chat Title:",
        value=current_chat["title"],
        key="rename_chat_input",
    )
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
            show_small_spinner(lang["thinking"])

        selected_style = st.session_state.get("image_style", "Default")
        if is_image_request(p_text):
            img_url = generate_image_url(p_text, selected_style)
            response = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
        elif is_music_request(p_text):
            track_name, track_url = generate_music_track(p_text)
            response = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            response = ask_ai_text(history_for_api, st.session_state.guest_plan)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    for idx, message in enumerate(current_chat["messages"]):
        if message["role"] == "user":
            display_content = message["content"]
            if isinstance(display_content, list):
                img_display = next(
                    (
                        item
                        for item in display_content
                        if isinstance(item, Image.Image)
                    ),
                    None,
                )
                text_display = next(
                    (item for item in display_content if isinstance(item, str)), ""
                )
                if img_display:
                    st.image(img_display, width=250)
                display_content = f"📷 [Şəkil əlavə olundu] <br>{text_display}"

            st.markdown(
                f"""
                    <div class="chat-row user">
                        <div class="user-message-box"><b>Sən / You:</b><br>{display_content}</div>
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
                    st.image(parts[1].strip(), use_container_width=True)
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

            c_like, c_dislike, c_space = st.columns([1, 1, 6])
            with c_like:
                if st.button("👍", key=f"like_{idx}"):
                    save_feedback_to_db(
                        user_name, "Bəyəndi 👍", str(message["content"])
                    )
                    st.toast("🎉 Rəyiniz üçün təşəkkürlər!", icon="👍")
            with c_dislike:
                if st.button("👎", key=f"dislike_{idx}"):
                    save_feedback_to_db(
                        user_name, "Bəyənmədi 👎", str(message["content"])
                    )
                    st.toast("⚠️ Qeyd olundu! Təşəkkürlər.", icon="🔧")

            st.markdown("---")

    col_input_ctrls1, col_input_ctrls2 = st.columns([1, 5])
    with col_input_ctrls1:
        if st.button("➕ Fayl/Şəkil", use_container_width=True):
            st.session_state.show_file_uploader = (
                not st.session_state.show_file_uploader
            )

    with col_input_ctrls2:
        st.session_state.guest_plan = st.selectbox(
            "Rejim:",
            ["Flash", "Pro", "UltiPremium"],
            index=["Flash", "Pro", "UltiPremium"].index(
                st.session_state.guest_plan
            ),
            label_visibility="collapsed",
        )

    uploaded_file = None
    if st.session_state.show_file_uploader:
        uploaded_file = st.file_uploader(
            lang["add_file"],
            type=["png", "jpg", "jpeg", "txt", "py", "json"],
        )

        if (
            uploaded_file is not None
            and uploaded_file.name.split(".")[-1].lower() in ["png", "jpg", "jpeg"]
        ):
            st.markdown("🛠️ **Şəkil Redaktə Etmə Paneli:**")
            edit_action = st.selectbox(
                "Effekt seç",
                [
                    "Seçim edin...",
                    "Qara-Ağ (Grayscale)",
                    "Parlaqlığı Artır",
                    "Kontrastı Artır",
                    "Tərsinə Çevir (Invert)",
                    "Kvadrat Kəs (Thumbnail)",
                ],
                key="edit_action_box",
            )
            if edit_action != "Seçim edin...":
                try:
                    raw_img = Image.open(uploaded_file)
                    processed_img = edit_user_image(raw_img, edit_action)
                    st.image(
                        processed_img,
                        caption=f"Redaktə olundu: {edit_action}",
                        width=300,
                    )

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

    if prompt := st.chat_input(lang["ask_placeholder"]):
        user_message_content = prompt

        if uploaded_file is not None:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            if file_extension in ["png", "jpg", "jpeg"]:
                try:
                    pil_image = Image.open(uploaded_file)
                    user_message_content = [
                        pil_image,
                        prompt if prompt else "Bu şəkli analiz et.",
                    ]
                except Exception:
                    user_message_content = prompt
            else:
                try:
                    file_text_extra = uploaded_file.read().decode("utf-8")
                    user_message_content = f"{prompt}\n\n[Fayl Məzmunu - {uploaded_file.name}]:\n```\n{file_text_extra}\n```"
                except Exception:
                    user_message_content = (
                        f"{prompt}\n[Fayl əlavə edildi: {uploaded_file.name}]"
                    )

        current_chat["messages"].append(
            {"role": "user", "content": user_message_content}
        )
        if current_chat["title"] == lang["new_chat"]:
            current_chat["title"] = (
                prompt[:20] + "..." if prompt else "Media Söhbəti"
            )

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner(lang["replying"])

        selected_style = st.session_state.get("image_style", "Default")
        if is_image_request(prompt if prompt else ""):
            img_url = generate_image_url(prompt, selected_style)
            response = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
        elif is_music_request(prompt if prompt else ""):
            track_name, track_url = generate_music_track(prompt)
            response = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            response = ask_ai_text(history_for_api, st.session_state.guest_plan)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    if st.button(lang["close_panel"]):
        st.session_state.show_aliai = False
        st.rerun()
else:
    col_main_ctrls1, col_main_ctrls2 = st.columns([1, 5])
    with col_main_ctrls1:
        if st.button(
            "➕ Fayl/Şəkil", key="main_plus_btn", use_container_width=True
        ):
            st.session_state.show_file_uploader = (
                not st.session_state.show_file_uploader
            )

    with col_main_ctrls2:
        st.session_state.guest_plan = st.selectbox(
            "Rejim:",
            ["Flash", "Pro", "UltiPremium"],
            index=["Flash", "Pro", "UltiPremium"].index(
                st.session_state.guest_plan
            ),
            key="main_plan_select",
            label_visibility="collapsed",
        )

    if st.session_state.show_file_uploader:
        main_uploaded_file = st.file_uploader(
            lang["add_file"],
            type=["png", "jpg", "jpeg", "txt", "py", "json"],
            key="main_file_up",
        )
        if (
            main_uploaded_file is not None
            and main_uploaded_file.name.split(".")[-1].lower()
            in ["png", "jpg", "jpeg"]
        ):
            st.markdown("🛠️ **Şəkil Redaktə Etmə Paneli:**")
            main_edit_action = st.selectbox(
                "Effekt seç",
                [
                    "Seçim edin...",
                    "Qara-Ağ (Grayscale)",
                    "Parlaqlığı Artır",
                    "Kontrastı Artır",
                    "Tərsinə Çevir (Invert)",
                    "Kvadrat Kəs (Thumbnail)",
                ],
                key="main_edit_action_box",
            )
            if main_edit_action != "Seçim edin...":
                try:
                    raw_img = Image.open(main_uploaded_file)
                    processed_img = edit_user_image(raw_img, main_edit_action)
                    st.image(
                        processed_img,
                        caption=f"Redaktə olundu: {main_edit_action}",
                        width=300,
                    )

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
        if main_uploaded_file is not None:
            file_extension = main_uploaded_file.name.split(".")[-1].lower()
            if file_extension in ["png", "jpg", "jpeg"]:
                try:
                    pil_image = Image.open(main_uploaded_file)
                    user_message_content = [pil_image, search_query]
                except Exception:
                    user_message_content = search_query
            else:
                try:
                    file_text_extra = main_uploaded_file.read().decode("utf-8")
                    user_message_content = f"{search_query}\n\n[Fayl Məzmunu - {main_uploaded_file.name}]:\n```\n{file_text_extra}\n```"
                except Exception:
                    user_message_content = (
                        f"{search_query}\n[Fayl əlavə edildi: {main_uploaded_file.name}]"
                    )

        current_chat["messages"].append(
            {"role": "user", "content": user_message_content}
        )
        if current_chat["title"] == lang["new_chat"]:
            current_chat["title"] = search_query[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner(lang["searching"])

        selected_style = st.session_state.get("image_style", "Default")
        if is_image_request(search_query):
            img_url = generate_image_url(search_query, selected_style)
            ai_resp = f"🎨 İstədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
        elif is_music_request(search_query):
            track_name, track_url = generate_music_track(search_query)
            ai_resp = f"🎵 İstədiyiniz musiqi/audio parçası hazırlandı: **{track_name}**\n\n__MUSIC_URL__{track_url}"
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            ai_resp = ask_ai_text(history_for_api, st.session_state.guest_plan)

        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": ai_resp})
        st.rerun()
