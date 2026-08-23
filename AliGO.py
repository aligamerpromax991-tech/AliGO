import streamlit as st
import uuid
import time
from groq import Groq

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Süni İntellekt Mərkəzi", page_icon="✨", layout="wide")

# --- GROQ MÜŞTƏRİSİ ---
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- GEMINI STİLİNDƏ ULTRA-PRO CSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #131314; /* Tam Gemini dark mode rəngi */
        color: #e3e9f2;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Üst Başlıq */
    .hero-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-top: 10vh;
        margin-bottom: 30px;
        background: linear-gradient(90deg, #c4a7ff, #6b8df8, #c4a7ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-shift 3s infinite linear;
        background-size: 200% auto;
    }

    @keyframes gradient-shift {
        0% { background-position: 0% center; }
        100% { background-position: 200% center; }
    }

    /* Söhbət Baloncukları */
    .chat-row { display: flex; width: 100%; margin-bottom: 12px; }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }
    
    .chat-bubble {
        max-width: 75%; padding: 14px 18px; border-radius: 18px; font-size: 0.98rem;
    }
    .chat-row.user .chat-bubble {
        background-color: #333538; color: #ffffff; border-bottom-right-radius: 4px;
    }
    .chat-row.assistant .chat-bubble {
        background-color: transparent; color: #f1f5f9; border-left: 2px solid #6b8df8; padding-left: 15px;
    }

    /* "Alətlər Paneli" - Inputun düz üstündə eyni rəngdə docked dayanır */
    [data-testid="stHorizontalBlock"] {
        background-color: #1e1f20;
        border-radius: 25px;
        padding: 4px 15px;
        margin-bottom: -15px; /* Inputla aradakı məsafəni bağlayır */
        border: 1px solid rgba(255,255,255,0.1);
        align-items: center;
    }

    /* Popover və Selectbox düymələrinin təmizlənməsi */
    .stPopover > div > button, .stSelectbox > div > div {
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #e3e9f2 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "guest_plan" not in st.session_state: st.session_state.guest_plan = "Pro"
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat_id" not in st.session_state: st.session_state.current_chat_id = None

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = first_id

current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})

# --- SOL PANEL ---
with st.sidebar:
    st.markdown("### 💬 AliGo Mərkəzi")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.current_chat_id = new_id
        st.rerun()

# --- ƏSAS EKRAN & MESAJLAŞMA ---
if not current_chat["messages"]:
    st.markdown('<div class="hero-title">AliGo ilə nələri kəşf edək?</div>', unsafe_allow_html=True)
else:
    for i, message in enumerate(current_chat["messages"]):
        role_class = "user" if message["role"] == "user" else "assistant"
        st.markdown(f'<div class="chat-row {role_class}"><div class="chat-bubble">{message["content"]}</div></div>', unsafe_allow_html=True)

st.markdown("<br><br><br><br>", unsafe_allow_html=True) # Boşluq

# --- GEMINI STİLİNDƏ BOTTOM BAR (Hacker Üsulu) ---
# Burada + və Rejim düyməsini xüsusi "container" içində yanaşı qoyuruq ki, inputun üst hissəsi kimi görünsün.
col1, col2, col3 = st.columns([1, 6, 2])
with col1:
    with st.popover("➕ Alətlər"):
        st.file_uploader("Faylları yükləyin", label_visibility="collapsed")
        st.button("🖼️ Şəkil Yarat", use_container_width=True)
        st.button("🎶 Musiqi Yarat", use_container_width=True)
with col3:
    st.session_state.guest_plan = st.selectbox(
        "Model Seçimi", 
        ["Flash", "Pro", "UltiPremium"], 
        index=1, 
        label_visibility="collapsed"
    )

# Əsas Input - Bu həmişə altdadır, amma yuxarıdakı panellə eyni blokda kimi görünəcək.
if prompt := st.chat_input("AliGo-dan istəyin..."):
    current_chat["messages"].append({"role": "user", "content": prompt})
    if current_chat["title"] == "Yeni Söhbət":
        current_chat["title"] = prompt[:18] + "..."
    
    st.rerun() # Məntiqi sürətləndirmək üçün səhifəni dərhal yeniləyirik
