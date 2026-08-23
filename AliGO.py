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

# --- GEMİNİ ÜSLUBUNDA MÜASİR VƏ ZƏRİF STİLLƏR ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(10, 15, 30, 0.8), rgba(5, 10, 20, 0.95)), 
                    url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    .aligo-logo {
        text-align: center;
        font-size: 3.8rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 800;
        letter-spacing: -1.5px;
        margin-top: 0px;
        margin-bottom: 0px;
        text-shadow: 0 0 20px rgba(0, 242, 254, 0.4);
    }

    @keyframes aligo-wave {
        0%, 100% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 8px #00f2fe); }
        50% { transform: translateY(-6px) scale(1.05); filter: drop-shadow(0 0 18px #a855f7); }
    }

    .spinning-aligo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 25px 0;
    }

    .spinning-logo {
        font-size: 2.8rem;
        font-weight: 800;
        animation: aligo-wave 1.5s infinite ease-in-out;
        display: inline-block;
    }

    .loading-text {
        color: #00f2fe;
        font-size: 1rem;
        margin-top: 10px;
        letter-spacing: 0.5px;
    }

    .stButton > button {
        border-radius: 20px !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        background-color: rgba(30, 41, 59, 0.7) !important;
        color: #f1f5f9 !important;
        transition: all 0.3s ease !important;
    }

    .stButton > button:hover {
        border-color: #00f2fe !important;
        background-color: rgba(0, 242, 254, 0.15) !important;
        box-shadow: 0 0 12px rgba(0, 242, 254, 0.3);
    }

    .stChatInputContainer {
        border-radius: 30px !important;
        border: 1px solid rgba(0, 242, 254, 0.4) !important;
        background-color: rgba(15, 23, 42, 0.85) !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5) !important;
    }

    .user-message-box {
        background: rgba(0, 242, 254, 0.08);
        border: 1px solid rgba(0, 242, 254, 0.2);
        padding: 12px 16px;
        border-radius: 18px;
        margin-bottom: 12px;
        color: #f1f5f9;
        font-family: 'Segoe UI', sans-serif;
    }
    
    [data-testid="stSidebar"] {
        background-color: rgba(10, 15, 30, 0.85);
        backdrop-filter: blur(10px);
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE TƏNZİMLƏMƏLƏRİ ---
if "guest_plan" not in st.session_state:
    st.session_state.guest_plan = "Flash"

if "show_aliai" not in st.session_state:
    st.session_state.show_aliai = False

if "trigger_prompt" not in st.session_state:
    st.session_state.trigger_prompt = None

if "ai_temp" not in st.session_state:
    st.session_state.ai_temp = 0.7

# --- ÇAT TARİXÇƏSİ İDARƏETMƏSİ ---
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = first_id

# --- ANIMASİYA EKRANI ---
def show_custom_spinner(text="AliGo düşünür..."):
    st.markdown(f"""
        <div class="spinning-aligo-container">
            <div class="spinning-logo">
                <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
            </div>
            <div class="loading-text">{text}</div>
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
        return f'<audio controls style="width: 100%; height: 30px; margin-top: 6px; opacity: 0.85;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except Exception:
        return ""

# --- SOL PANEL ---
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

with st.sidebar.expander("⚙️ Tənzimləmələr"):
    st.session_state.ai_temp = st.slider("Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1)

# --- ƏSAS EKRAN ---
active_plan = st.session_state.guest_plan

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h5 style='color: #00f2fe; margin:0;'>✨ Rejim aktivdir</h5>", unsafe_allow_html=True)
with col2:
    if st.button("🤖 AliAI"):
        st.session_state.show_aliai = not st.session_state.show_aliai
        st.rerun()

st.markdown("""
    <div class="aligo-logo">
        <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
    </div>
    <p style="text-align: center; color: #94a3b8; font-size: 0.95rem; margin-bottom: 15px;">Süni İntellekt və Axtarış Mərkəzi</p>
""", unsafe_allow_html=True)

# --- REJİM SEÇİMİ ---
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

# --- GROQ FUNKSİYASI (TƏBİİ VƏ MƏLUMATLI QAYDA İLƏ) ---
def ask_groq(messages_history, user_plan="Flash", mode="chat"):
    start_time = time.time()
    base_identity = (
        "QAYDA: Sənin adın AliGo-dur! Sən AliGo Süni İntellekt və Axtarış Mərkəzisən. "
        "Kimsə səndən kimliyini və ya səni kimin yaratdığını soruşduqda, məlumatlı şəkildə izah et ki, "
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

# --- HAZIR PROMPTLAR ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
    if st.button("❓ Sual", use_container_width=True):
        st.session_state.trigger_prompt = "Mənə maraqlı bir elm faktı de."
        st.session_state.show_aliai = True
        st.rerun()
with col_q2:
    if st.button("💻 Kod", use_container_width=True):
        st.session_state.trigger_prompt = "Python-da sadə oyun kodu yaz."
        st.session_state.show_aliai = True
        st.rerun()
with col_q3:
    if st.button("📊 Plan", use_container_width=True):
        st.session_state.trigger_prompt = "İdeal gün planı qur."
        st.session_state.show_aliai = True
        st.rerun()
with col_q4:
    if st.button("🎮 Oyun", use_container_width=True):
        st.session_state.trigger_prompt = "Minecraft üçün maraqlı ideyalar ver."
        st.session_state.show_aliai = True
        st.rerun()

# --- ÇAT VƏ YA AXTARIŞ ---
if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})
    
    new_chat_title = st.text_input("Söhbət adı:", value=current_chat["title"], key="rename_chat_input")
    if new_chat_title != current_chat["title"]:
        current_chat["title"] = new_chat_title
        st.rerun()

    if st.session_state.trigger_prompt:
        p_text = st.session_state.trigger_prompt
        st.session_state.trigger_prompt = None
        current_chat["messages"].append({"role": "user", "content": p_text})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = p_text[:18] + "..."
        
        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo cavab hazırlayır...")
        
        response = ask_groq(current_chat["messages"], active_plan, mode="chat")
        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    for message in current_chat["messages"]:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message-box"><b>Sən:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
            audio_html = text_to_speech_audio(message["content"])
            if audio_html:
                st.markdown(audio_html, unsafe_allow_html=True)
            st.markdown("---")

    with st.expander("➕ Fayl / Şəkil əlavə et"):
        uploaded_file = st.file_uploader("", type=["png", "jpg", "jpeg", "txt", "py"], label_visibility="collapsed")

    if prompt := st.chat_input("AliGo-dan nəsə soruş..."):
        full_prompt = prompt
        if 'uploaded_file' in locals() and uploaded_file is not None:
            full_prompt += f"\n[Yüklənən fayl: {uploaded_file.name}]"

        current_chat["messages"].append({"role": "user", "content": full_prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:18] + "..."

        st.markdown(f'<div class="user-message-box"><b>Sən:</b><br>{full_prompt}</div>', unsafe_allow_html=True)

        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo cavab hazırlayır...")
        
        response = ask_groq(current_chat["messages"], active_plan, mode="chat")
        placeholder.empty()
        st.markdown(response)
        audio_html = text_to_speech_audio(response)
        if audio_html:
            st.markdown(audio_html, unsafe_allow_html=True)
            
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    if st.button("❌ Bağla"):
        st.session_state.show_aliai = False
        st.rerun()
else:
    search_query = st.text_input("", placeholder="Axtarış Mərkəzi: Məsələn, 'CapCut PC indir'...", key="main_search", label_visibility="collapsed")
    if search_query:
        st.session_state.show_aliai = True
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        current_chat["messages"].append({"role": "user", "content": search_query})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = search_query[:18] + "..."
        
        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo axtarır...")
        
        ai_resp = ask_groq(current_chat["messages"], active_plan, mode="search")
        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": ai_resp})
        st.rerun()
