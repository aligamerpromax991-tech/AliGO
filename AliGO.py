import streamlit as st
import uuid
import time
from groq import Groq
from gtts import gTTS
import base64
import io

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Süni İntellekt Mərkəzi", page_icon="✨", layout="wide")

# --- GROQ MÜŞTƏRİSİ ---
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- ŞƏKILDƏKİ KİMİ ULTRA SƏLİQƏLİ KAPSUL İMPUT VƏ QRAFİKA ---
st.markdown("""
    <style>
    .stApp {
        background: radial-gradient(circle at 50% 20%, #101728 0%, #080c14 60%, #030509 100%);
        color: #e3e9f2;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Sol Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0b0f19;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    /* Əsas Başlıq */
    .hero-title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-top: 15vh;
        margin-bottom: 25px;
        background: linear-gradient(135deg, #ffffff 30%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Söhbət Baloncukları (Sağ-Sol Struktur) */
    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 18px;
    }
    .chat-row.user {
        justify-content: flex-end;
    }
    .chat-row.assistant {
        justify-content: flex-start;
    }

    .chat-bubble {
        max-width: 75%;
        padding: 14px 18px;
        border-radius: 18px;
        font-size: 0.98rem;
        line-height: 1.6;
        word-wrap: break-word;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .chat-row.user .chat-bubble {
        background: linear-gradient(135deg, #2563eb, #1d4ed8);
        color: #ffffff;
        border-bottom-right-radius: 4px;
    }
    .chat-row.assistant .chat-bubble {
        background: rgba(22, 28, 45, 0.85);
        color: #f1f5f9;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-bottom-left-radius: 4px;
    }

    /* Dalğalı Animasiyalı Kiçik AliGo İkonu */
    @keyframes aligo-glow {
        0%, 100% { opacity: 0.4; transform: scale(0.97); text-shadow: 0 0 5px rgba(0, 242, 254, 0.3); }
        50% { opacity: 1; transform: scale(1.03); text-shadow: 0 0 15px rgba(0, 242, 254, 0.8); }
    }

    .typing-badge {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        background: linear-gradient(45deg, #00f2fe, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: aligo-glow 1.2s infinite ease-in-out;
        padding: 6px 0;
    }

    /* Sidebar Düymələri */
    .stButton > button {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        background-color: rgba(255, 255, 255, 0.03) !important;
        color: #cbd5e1 !important;
        transition: all 0.25s ease !important;
    }
    .stButton > button:hover {
        border-color: #00f2fe !important;
        color: #00f2fe !important;
        background-color: rgba(0, 242, 254, 0.08) !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE TƏNZİMLƏMƏLƏRİ ---
if "guest_plan" not in st.session_state:
    st.session_state.guest_plan = "Flash"

if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = first_id

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

# --- SOL PANEL (SÖHBƏTLƏR İDARƏETMƏSİ) ---
with st.sidebar:
    st.markdown("### 💬 Söhbətlər")
    if st.button("➕ Yeni Söhbət", use_container_width=True):
        new_id = str(uuid.uuid4())[:8]
        st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
        st.session_state.current_chat_id = new_id
        st.rerun()

    st.markdown("---")
    for cid, cdata in list(st.session_state.chats.items()):
        col_a, col_b = st.columns([4, 1])
        with col_a:
            is_active = (cid == st.session_state.current_chat_id)
            btn_label = f"📍 {cdata['title']}" if is_active else cdata['title']
            if st.button(btn_label, key=f"chat_{cid}", use_container_width=True):
                st.session_state.current_chat_id = cid
                st.rerun()
        with col_b:
            if st.button("🗑️", key=f"del_{cid}"):
                del st.session_state.chats[cid]
                if st.session_state.current_chat_id == cid:
                    if st.session_state.chats:
                        st.session_state.current_chat_id = list(st.session_state.chats.keys())[0]
                    else:
                        new_id = str(uuid.uuid4())[:8]
                        st.session_state.chats[new_id] = {"title": "Yeni Söhbət", "messages": []}
                        st.session_state.current_chat_id = new_id
                st.rerun()

# --- GROQ MƏNTİQİ ---
def ask_groq(messages_history, user_plan="Flash"):
    start_time = time.time()
    base_identity = (
        "QAYDA: Sənin adın AliGo-dur! Sən AliGo Süni İntellekt Mərkəzisən. "
        "Kimsə səndən kimliyini və ya səni kimin yaratdığını soruşduqda, təbii və məlumatlı şəkildə izah et ki, "
        "səni Əli adlı mütəxəssis proqramçı yaradıb və sən istifadəçilərə kömək etmək üçün hazırlanmış süni intellekt mərkəzisən.\n\n"
    )
    
    max_tokens = 1500 if user_plan == "Flash" else 3000
    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "system", "content": base_identity + f"Sən {user_plan} rejimində işləyən ağıllı köməkçisən."}] + messages_history,
            temperature=0.7,
            max_tokens=max_tokens,
        )
        elapsed = time.time() - start_time
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed)
        return completion.choices[0].message.content
    exceptException as e:
        return f"⚠️ Xəta baş verdi: {e}"

# --- ƏSAS EKRAN ---
current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})

if not current_chat["messages"]:
    st.markdown('<div class="hero-title">Başqa hansı ideyaları araşdıraq?</div>', unsafe_allow_html=True)
else:
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

# --- ŞƏKILDƏKİ KİMİ KAPSUL İMPUTUN SAĞINDA REJİM SEÇİMİ ---
col_input, col_mode = st.columns([5, 1])
with col_mode:
    st.session_state.guest_plan = st.selectbox(
        "Rejim",
        ["Flash", "Pro", "UltiPremium"],
        index=["Flash", "Pro", "UltiPremium"].index(st.session_state.guest_plan),
        label_visibility="collapsed"
    )

with col_input:
    if prompt := st.chat_input("AliGo-dan istəyin..."):
        current_chat["messages"].append({"role": "user", "content": prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:18] + "..."

        st.markdown(f"""
            <div class="chat-row user">
                <div class="chat-bubble">{prompt}</div>
            </div>
        """, unsafe_allow_html=True)

        # Dalğalı Animasiyalı Kiçik AliGo Göstəricisi
        placeholder = st.empty()
        with placeholder.container():
            st.markdown("""
                <div class="chat-row assistant">
                    <div class="chat-bubble">
                        <span class="typing-badge">✨ AliGo axtarır...</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        response = ask_groq(current_chat["messages"], st.session_state.guest_plan)
        placeholder.empty()

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
