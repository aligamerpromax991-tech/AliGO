import streamlit as st
import uuid
import time
from groq import Groq
from gtts import gTTS
import base64
import io

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Süni İntellekt Mərkəzi", page_icon="🏔️", layout="centered")

# --- GROQ MÜŞTƏRİSİ ---
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- MÜASİR VƏ SƏLİQƏLİ ÇAT QRAFIKASI (SAĞ-SOL BALONCUKLAR VƏ DALĞALI ANİMASİYA) ---
st.markdown("""
    <style>
    .stApp {
        background-color: #0d1117;
        color: #e6edf3;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Sol Panel (Sidebar) Dizaynı */
    [data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* Loqo Stili */
    .aligo-logo {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin-bottom: 5px;
        background: linear-gradient(45deg, #00f2fe, #4facfe, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Söhbət Baloncukları - Sağ (İstifadəçi) və Solda (AI) */
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 16px;
    }
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.assistant {
        justify-content: flex-start;
    }

    .chat-bubble {
        max-width: 80%;
        padding: 12px 16px;
        border-radius: 16px;
        font-size: 0.95rem;
        line-height: 1.5;
        word-wrap: break-word;
    }
    .chat-row.user .chat-bubble {
        background: #1f6feb;
        color: #ffffff;
        border-bottom-right-radius: 4px;
    }
    .chat-row.assistant .chat-bubble {
        background: #161b22;
        color: #e6edf3;
        border: 1px solid #30363d;
        border-bottom-left-radius: 4px;
    }

    /* Dalğalı Animasiyalı Kiçik AliGo Göstəricisi */
    @keyframes aligo-pulse {
        0%, 100% { opacity: 0.4; transform: scale(0.98); }
        50% { opacity: 1; transform: scale(1.02); text-shadow: 0 0 10px rgba(0, 242, 254, 0.6); }
    }

    .typing-indicator {
        display: inline-flex;
        align-items: center;
        font-weight: 600;
        font-size: 0.9rem;
        background: linear-gradient(45deg, #00f2fe, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: aligo-pulse 1.2s infinite ease-in-out;
        padding: 8px 0;
    }

    /* Düymələr və İnputlar */
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid #30363d !important;
        background-color: #21262d !important;
        color: #c9d1d9 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        border-color: #00f2fe !important;
        color: #00f2fe !important;
        background-color: #30363d !important;
    }

    .stChatInputContainer {
        border-radius: 24px !important;
        border: 1px solid #30363d !important;
        background-color: #161b22 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE TƏNZİMLƏMƏLƏRİ ---
if "guest_plan" not in st.session_state:
    st.session_state.guest_plan = "Flash"

if "show_aliai" not in st.session_state:
    st.session_state.show_aliai = False

if "ai_temp" not in st.session_state:
    st.session_state.ai_temp = 0.7

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = first_id

# --- DALĞALI KİÇİK ANİMASİYA KOMPONENTİ ---
def show_typing_animation():
    st.markdown("""
        <div class="chat-row assistant">
            <div class="chat-bubble">
                <span class="typing-indicator">✨ AliGo düşünür...</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# --- SƏSLİ OXUTMA (TTS) ---
def text_to_speech_audio(text, lang='az'):
    try:
        clean_text = text.replace('*', '').replace('#', '').replace('`', '')
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        b64 = base64.b64encode(audio_bytes).decode()
        return f'<audio controls style="width: 100%; height: 26px; margin-top: 8px; opacity: 0.8;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except Exception:
        return ""

# --- SOL PANEL (SÖHBƏTLƏR VƏ AYARLAR) ---
st.sidebar.markdown("### 💬 Söhbətlər")

if st.sidebar.button("➕ Yeni Söhbət", use_container_width=True):
    new_id = str(uuid.uuid4())[:8]
    st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = new_id
    st.session_state.show_aliai = True
    st.rerun()

for cid, cdata in list(st.session_state.chats.items()):
    col_a, col_b = st.sidebar.columns([4, 1])
    with col_a:
        is_active = (cid == st.session_state.current_chat_id)
        btn_label = f"📍 {cdata['title']}" if is_active else cdata['title']
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
                    st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
                    st.session_state.current_chat_id = new_id
            st.rerun()

st.sidebar.markdown("---")
with st.sidebar.expander("⚙️ Parametrlər"):
    st.session_state.ai_temp = st.slider("Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1)

# --- ƏSAS EKRAN ---
st.markdown('<div class="aligo-logo">AliGo</div>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #8b949e; font-size: 0.85rem; margin-bottom: 20px;'>Süni İntellekt və Axtarış Mərkəzi</p>", unsafe_allow_html=True)

# Rejim seçimi
cols_mode = st.columns(3)
with cols_mode[0]:
    if st.button("⚡ Flash", use_container_width=True):
        st.session_state.guest_plan = "Flash"
        st.rerun()
with cols_mode[1]:
    if st.button("🚀 Pro", use_container_width=True):
        st.session_state.guest_plan = "Pro"
        st.rerun()
with cols_mode[2]:
    if st.button("👑 Ulti", use_container_width=True):
        st.session_state.guest_plan = "UltiPremium"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- GROQ FUNKSİYASI (MƏLUMATLI VƏ DƏQİQ QAYDA İLƏ) ---
def ask_groq(messages_history, user_plan="Flash", mode="chat"):
    start_time = time.time()
    base_identity = (
        "QAYDA: Sənin adın AliGo-dur! Sən AliGo Süni İntellekt Mərkəzisən. "
        "Kimsə səndən kimliyini və ya səni kimin yaratdığını soruşduqda, təbii və məlumatlı şəkildə izah et ki, "
        "səni Əli adlı mütəxəssis proqramçı yaradıb və sən istifadəçilərə kömək etmək üçün hazırlanmış süni intellekt mərkəzisən.\n\n"
    )
    
    if mode == "search":
        system_content = base_identity + "Sən AliGo Axtarış Mərkəzisən. Rəsmi mənbələri və faydalı linkləri səliqəli təqdim et."
        max_tokens = 2000
    else:
        max_tokens = 1500 if user_plan == "Flash" else 3000
        system_content = base_identity + f"Sən {user_plan} rejimində işləyən ağıllı köməkçisən."

    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "system", "content": system_content}] + messages_history,
            temperature=st.session_state.ai_temp,
            max_tokens=max_tokens,
        )
        elapsed = time.time() - start_time
        if elapsed < 2:
            time.sleep(2 - elapsed)
        return completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ Xəta baş verdi: {e}"

# --- ÇAT TARİXÇƏSİNİN GÖSTƏRİLMƏSİ (SAĞ-SOL BALONCUKLAR) ---
current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})

for message in current_chat["messages"]:
    if message["role"] == "user":
        st.markdown(f"""
            <div class="chat-row user">
                <div class="chat-bubble">{message["content"]}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="chat-row assistant">
                <div class="chat-bubble">{message["content"]}</div>
            </div>
        """, unsafe_allow_html=True)
        audio_html = text_to_speech_audio(message["content"])
        if audio_html:
            st.markdown(audio_html, unsafe_allow_html=True)

# --- MESAJ GÖNDƏRMƏ VƏ AXTARIŞ ---
if prompt := st.chat_input("AliGo-dan nəsə soruş..."):
    current_chat["messages"].append({"role": "user", "content": prompt})
    if current_chat["title"] == "Yeni Söhbət":
        current_chat["title"] = prompt[:18] + "..."

    # İstifadəçi mesajını dərhal göstər
    st.markdown(f"""
        <div class="chat-row user">
            <div class="chat-bubble">{prompt}</div>
        </div>
    """, unsafe_allow_html=True)

    # Dalğalı animasiyanı göstər
    placeholder = st.empty()
    with placeholder.container():
        show_typing_animation()
    
    response = ask_groq(current_chat["messages"], st.session_state.guest_plan, mode="chat")
    placeholder.empty()

    # AI cavabını solda göstər
    st.markdown(f"""
        <div class="chat-row assistant">
            <div class="chat-bubble">{response}</div>
        </div>
    """, unsafe_allow_html=True)
    
    audio_html = text_to_speech_audio(response)
    if audio_html:
        st.markdown(audio_html, unsafe_allow_html=True)
        
    current_chat["messages"].append({"role": "assistant", "content": response})
    st.rerun()
