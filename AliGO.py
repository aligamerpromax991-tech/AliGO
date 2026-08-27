import base64
import re
import time
import urllib.parse
import uuid
import requests
import streamlit as st
from groq import Groq
from supabase import Client, create_client

# --- SƏHİFƏ TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(
    page_title="AliGo - Süni İntellekt Mərkəzi",
    page_icon="⚡",
    layout="centered",
)

# --- GROQ VƏ SUPABASE QOŞULMASI ---
def get_groq_client():
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        st.error(
            "⚠️ 'GROQ_API_KEY' tapılmadı! Xahiş olunur secrets.toml faylını yoxlayın."
        )
        return None
    return Groq(api_key=api_key)

SUPABASE_URL = "https://iqfxtorbnjvnqsdgloyd.supabase.co"
SUPABASE_KEY = "sb_publishable_dF7WkdLq8ohQrVkl4SDlHw_w_4os4pt"

supabase: Client = None
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Supabase Qoşulma Xətası: {e}")

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

    .stChatInputContainer {
        border-radius: 25px !important;
        border: 2px solid #00f2fe !important;
        background-color: rgba(15, 23, 42, 0.9) !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
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

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
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
    except Exception as e:
        st.error(f"Xəta: {e}")

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
    ]
    return any(kw in prompt_text.lower() for kw in keywords)

def generate_image_url(prompt_text):
    encoded_prompt = urllib.parse.quote(prompt_text)
    return f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={uuid.uuid4().int % 10000}"

# --- SOL PANEL ---
st.sidebar.markdown("### 🔐 Profil")

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
        if st.sidebar.button("🚪 Google-dan Çıxış", use_container_width=True):
            if hasattr(st, "logout"):
                try:
                    st.logout()
                except Exception:
                    pass
            st.rerun()
    else:
        if st.sidebar.button("🚪 Çıxış Et", use_container_width=True):
            st.session_state.user_info = None
            if "logged_to_db" in st.session_state:
                del st.session_state["logged_to_db"]
            st.rerun()
else:
    if st.sidebar.button("🔵 Google ilə Giriş Et", use_container_width=True):
        if hasattr(st, "login"):
            try:
                st.login("google")
            except Exception as e:
                st.sidebar.error(f"Giriş xətası: {e}")

    with st.sidebar.expander("👤 Ad yazaraq daxil ol"):
        input_name = st.text_input("Adınız:")
        input_email = st.text_input("Email (istəyə bağlı):")
        if st.button("Daxil ol"):
            if input_name:
                st.session_state.user_info = {
                    "name": input_name,
                    "email": input_email
                    or f"{input_name.lower().replace(' ', '')}@user.com",
                }
                save_user_to_db(input_name, input_email)
                st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 💬 Söhbət Tarixçəsi")

if st.sidebar.button("➕ Yeni Çat Yarat", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
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
                        "title": "Yeni Söhbət",
                        "messages": []
                    }
                    st.session_state.current_chat_id = new_id
            st.rerun()

current_chat_data = st.session_state.chats.get(
    st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []}
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
        label="📥 Söhbəti TXT olaraq yüklə",
        data=chat_export_text,
        file_name=f"{current_chat_data['title']}.txt",
        mime="text/plain",
        use_container_width=True,
    )

with st.sidebar.expander("⚙️ Tənzimləmələr"):
    st.session_state.ai_temp = st.slider(
        "AI Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1
    )
    st.session_state.ai_persona = st.selectbox(
        "AI Xarakteri (Persona):",
        [
            "Python / Kod Mütəxəssisi",
            "Standart AliGo",
            "Oyun Dizayneri (Minecraft/Roblox)",
            "Dost / Səmimi Məsləhətçi",
        ],
    )

# --- ƏSAS EKRAN ---
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
    st.markdown(
        "<h4 style='color: #00f2fe; margin-top: 5px;'>AliGo İntellektual"
        " Mərkəzi</h4>",
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
    """
    <div class="aligo-logo">AliGo</div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 10px;">Süni İntellekt və Kodlaşdırma Mərkəzi</p>
""",
    unsafe_allow_html=True,
)

# --- REJİMLƏR (MODLAR) ---
active_plan = st.session_state.guest_plan

cols_mode = st.columns(3)
with cols_mode[0]:
    if st.button(
        "⚡ Flash",
        use_container_width=True,
        type="primary" if active_plan == "Flash" else "secondary",
    ):
        st.session_state.guest_plan = "Flash"
        st.rerun()
with cols_mode[1]:
    if st.button(
        "🚀 Pro",
        use_container_width=True,
        type="primary" if active_plan == "Pro" else "secondary",
    ):
        st.session_state.guest_plan = "Pro"
        st.rerun()
with cols_mode[2]:
    if st.button(
        "👑 UltiPremium",
        use_container_width=True,
        type="primary" if active_plan == "UltiPremium" else "secondary",
    ):
        st.session_state.guest_plan = "UltiPremium"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- GROQ CAVABINDA DAXILI <think> MƏTNİNİ TƏMİZLƏ ---
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

# --- GROQ SORĞUSU ---
def ask_groq(messages_history, user_plan="UltiPremium", mode="chat"):
    start_time = time.time()
    client = get_groq_client()
    if not client:
        return (
            "⚠️ Groq client yaradıla bilmədi. API açarınızı (GROQ_API_KEY)"
            " yoxlayın."
        )

    base_identity = (
        "ÇOX VACİB QAYDA 1: Sən heç vaxt ChatGPT, OpenAI, Google, Gemini və ya başqa "
        "bir süni intellekt modeli olduğunu deməyəcəksən. Sənin adın AliGo-dur! "
        "Sən AliGo Süni İntellekt və Axtarış Mərkəzisən.\n"
        "ÇOX VACİB QAYDA 2: İstifadəçi səndən veb-sayt, simulyator və ya kod istədikdə, "
        "həmişə müasir dizayn və tam işlək funksionallıqla təchiz olunmuş peşəkar kodlar yaz.\n"
        "ÇOX VACİB QAYDA 3: Kodu yazarkən yarımçıq saxlama, tam şəkildə tamamla.\n"
        "DAXİLİ DÜŞÜNMƏNİ İSTİFADƏÇİYƏ GÖSTƏRMƏ. Yalnız yekun cavabı ver.\n\n"
    )

    persona_text = (
        "Xüsusi xarakter: Sən peşəkar proqramlaşdırma və mühəndislik ekspertisən.\n"
    )

    system_content = base_identity + persona_text + (
        "Sən həmişə ən peşəkar səviyyədə cavablar verirsən."
    )

    system_msg = {"role": "system", "content": system_content}
    
    # Uzun mətnlər üçün token limitini 8000 saxlayırıq
    max_tokens = 8000

    # Tam güncəl, 100% aktiv işləyən Groq istehsal modelləri siyahısı
    candidate_models = [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b"
    ]

    full_messages = [system_msg] + messages_history

    last_error = None
    for model_name in candidate_models:
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=full_messages,
                temperature=st.session_state.ai_temp,
                max_tokens=max_tokens,
            )

            elapsed = time.time() - start_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

            raw_response = completion.choices[0].message.content or ""
            return clean_ai_response(raw_response)
        except Exception as e:
            last_error = e
            continue

    return f"⚠️ Groq API Xətası baş verdi: {last_error}"

# --- DÜYMƏLƏR VƏ ÇAT ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
    if st.button("❓ Sual Soruş", use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə maraqlı bir mövzu haqqında ətraflı məlumat ver."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q2:
    if st.button("💻 Kod Yaz", use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə peşəkar bir veb tətbiqi və ya simulyator kodu yaz."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q3:
    if st.button("📊 Plan Qur", use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə mükəmməl bir inkişaf planı qur."
        )
        st.session_state.show_aliai = True
        st.rerun()
with col_q4:
    if st.button("🎨 Şəkil Yarat", use_container_width=True):
        st.session_state.trigger_prompt = (
            "Mənə gələcəyin şəhərini göstərən möhtəşəm bir vizual yarat."
        )
        st.session_state.show_aliai = True
        st.rerun()

if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(
        st.session_state.current_chat_id,
        {"title": "Yeni Söhbət", "messages": []},
    )

    new_chat_title = st.text_input(
        "Söhbətin Adı:", value=current_chat["title"], key="rename_chat_input"
    )
    if new_chat_title != current_chat["title"]:
        current_chat["title"] = new_chat_title
        st.rerun()

    if st.session_state.trigger_prompt:
        p_text = st.session_state.trigger_prompt
        st.session_state.trigger_prompt = None
        current_chat["messages"].append({"role": "user", "content": p_text})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = p_text[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner("AliGo düşünür və kod yazır...")

        if is_image_request(p_text):
            img_url = generate_image_url(p_text)
            response = (
                f"Buyurun, istədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
            )
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            response = ask_groq(history_for_api, active_plan, mode="chat")

        placeholder.empty()
        current_chat["messages"].append(
            {"role": "assistant", "content": response}
        )
        st.rerun()

    for idx, message in enumerate(current_chat["messages"]):
        if message["role"] == "user":
            display_content = message["content"]
            if isinstance(display_content, list):
                text_part = next(
                    (
                        item["text"]
                        for item in display_content
                        if item.get("type") == "text"
                    ),
                    "Şəkil göndərildi",
                )
                display_content = f"📷 [Şəkil yükləndi] <br>{text_part}"

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
                    st.image(parts[1].strip(), use_container_width=True)
            else:
                st.markdown(msg_content)

            st.markdown(
                """
                        </div>
                    </div>
                """,
                unsafe_allow_html=True,
            )

            # --- RƏY DÜYMƏLƏRİ ---
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

    uploaded_file = st.file_uploader(
        "Şəkil və ya fayl əlavə et",
        type=["png", "jpg", "jpeg", "txt", "py", "json"],
    )

    if prompt := st.chat_input("AliGo-dan soruş..."):
        file_text_extra = ""
        if uploaded_file is not None:
            if uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
                bytes_data = uploaded_file.getvalue()
                base64_image = base64.b64encode(bytes_data).decode("utf-8")
                user_message_content = [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ]
            else:
                try:
                    file_text_extra = uploaded_file.read().decode("utf-8")
                    user_message_content = f"{prompt}\n\n[Fayl Məzmunu - {uploaded_file.name}]:\n```\n{file_text_extra}\n```"
                except Exception:
                    user_message_content = (
                        f"{prompt}\n[Fayl əlavə edildi: {uploaded_file.name}]"
                    )
        else:
            user_message_content = prompt

        current_chat["messages"].append(
            {"role": "user", "content": user_message_content}
        )
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner("AliGo cavab hazırlayır...")

        if is_image_request(prompt):
            img_url = generate_image_url(prompt)
            response = (
                f"Buyurun, istədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
            )
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            response = ask_groq(history_for_api, active_plan, mode="chat")

        placeholder.empty()
        current_chat["messages"].append(
            {"role": "assistant", "content": response}
        )
        st.rerun()

    if st.button("❌ Paneli Bağla"):
        st.session_state.show_aliai = False
        st.rerun()
else:
    search_query = st.text_input(
        "",
        placeholder=(
            "AliGo-dan soruş..."
        ),
        key="main_search",
        label_visibility="collapsed",
    )
    if search_query:
        st.session_state.show_aliai = True
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        current_chat["messages"].append(
            {"role": "user", "content": search_query}
        )
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = search_query[:20] + "..."

        placeholder = st.empty()
        with placeholder.container():
            show_small_spinner("AliGo araşdırır...")

        if is_image_request(search_query):
            img_url = generate_image_url(search_query)
            ai_resp = (
                f"Buyurun, istədiyiniz şəkil yaradıldı:\n\n__IMAGE_URL__{img_url}"
            )
        else:
            history_for_api = [
                {"role": m["role"], "content": m["content"]}
                for m in current_chat["messages"]
            ]
            ai_resp = ask_groq(history_for_api, active_plan, mode="search")

        placeholder.empty()
        current_chat["messages"].append(
            {"role": "assistant", "content": ai_resp}
        )
        st.rerun()
