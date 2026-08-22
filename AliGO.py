import streamlit as st
import psutil
import urllib.request
import json
import urllib.parse
from groq import Groq
import os
import re
import uuid
import hashlib
import extra_streamlit_components as st_st

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Şəxsi Mərkəz", page_icon="🏔️", layout="centered")

# --- KUKİ (COOKIE) İDARƏETMƏSİ ---
cookie_manager = st_st.CookieManager()

# --- PAROLU ŞİFRƏLƏMƏK ÜÇÜN HASH FUNKSİYASI ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- İSTİFADƏÇİLƏRİN FAYLDA DAXLANMASI (HƏMİŞƏLİK) ---
DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
        except Exception:
            pass
    default_db = {"admin": {"pass": hash_password("1234"), "vip": True, "email": "admin@aligo.com"}}
    save_users(default_db)
    return default_db

def save_users(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

# --- GROQ API QURAŞDIRMASI ---
ai_client = None
try:
    if "GROQ_API_KEY" in st.secrets:
        GROQ_KEY = st.secrets["GROQ_API_KEY"]
        ai_client = Groq(api_key=GROQ_KEY)
except Exception:
    ai_client = None

# --- MÖHTƏŞƏM FUTURİSTİK DAĞ MƏNZƏRƏSİ ---
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(10, 15, 30, 0.75), rgba(5, 10, 20, 0.92)), 
                          url('https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }

    .aligo-logo {
        text-align: center;
        font-size: 4.2rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -2px;
        margin-top: 5px;
        margin-bottom: 0px;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.5), 0 4px 15px rgba(0,0,0,0.8);
    }

    .stChatInputContainer {
        border-radius: 25px !important;
        border: 2px solid #00f2fe !important;
        background-color: rgba(15, 23, 42, 0.9) !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
    }
    </style>
""", unsafe_allow_html=True)

current_db = load_users()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# ⚡ KUKİDƏN HESABI OXUYUB BƏRPA ETMƏK (Brauzer bağlansa belə silinmir)
saved_cookie_user = cookie_manager.get(cookie="aligo_user")
if not st.session_state.logged_in_user and saved_cookie_user:
    if saved_cookie_user in current_db:
        st.session_state.logged_in_user = saved_cookie_user

if "show_aliai" not in st.session_state:
    st.session_state.show_aliai = False

# --- ÇAT TARİXÇƏSİ İDARƏETMƏSİ ---
if "chats" not in st.session_state:
    st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = None

if not st.session_state.chats:
    first_id = str(uuid.uuid4())[:8]
    st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
    st.session_state.current_chat_id = first_id

# --- LOGİN VƏ QEYDİYYAT MODULU (SOL PANEL) ---
st.sidebar.markdown("### 🔐 İstifadəçi Hesabı")

if not st.session_state.logged_in_user:
    login_tab, register_tab = st.sidebar.tabs(["Daxil Ol", "Qeydiyyat"])
    
    with login_tab:
        st.markdown("#### Hesabınıza daxil olun")
        login_user = st.text_input("İstifadəçi adı və ya E-poçt", key="l_user")
        login_pass = st.text_input("Şifrə", type="password", key="l_pass")
        
        if st.button("Daxil Ol", use_container_width=True, key="btn_login"):
            matched_user = None
            for uname, udata in current_db.items():
                if uname == login_user or udata.get("email") == login_user:
                    matched_user = uname
                    break
            
            if matched_user and current_db[matched_user]["pass"] == hash_password(login_pass):
                st.session_state.logged_in_user = matched_user
                # Kukiyə yazırıq ki, 30 gün boyunca heç vaxt silinməsin
                cookie_manager.set("aligo_user", matched_user, expires_at=None)
                st.sidebar.success(f"Xoş gəldin, {matched_user}!")
                st.rerun()
            else:
                st.error("İstifadəçi adı/e-poçt və ya şifrə yanlışdır!")

    with register_tab:
        st.markdown("#### Yeni Hesab Yarat")
        new_username = st.text_input("İstifadəçi adı", key="r_user")
        new_email = st.text_input("E-poçt ünvanı", key="r_email")
        new_pass1 = st.text_input("Şifrə", type="password", key="r_pass1")
        new_pass2 = st.text_input("Şifrəni təsdiqlə", type="password", key="r_pass2")
        
        if st.button("Qeydiyyatı Tamamla", use_container_width=True, key="btn_reg"):
            if not new_username or not new_email or not new_pass1:
                st.error("Bütün xanaları doldurun!")
            elif new_username in current_db:
                st.error("Bu istifadəçi adı artıq mövcuddur!")
            elif new_pass1 != new_pass2:
                st.error("Şifrələr bir-biri ilə eyni deyil!")
            elif len(new_pass1) < 4:
                st.error("Şifrə ən azı 4 simvoldan ibarət olmalıdır!")
            else:
                current_db[new_username] = {
                    "pass": hash_password(new_pass1),
                    "email": new_email,
                    "vip": False
                }
                save_users(current_db)
                st.session_state.logged_in_user = new_username
                cookie_manager.set("aligo_user", new_username, expires_at=None)
                st.sidebar.success("Hesab uğurla yaradıldı!")
                st.rerun()
else:
    current_user = st.session_state.logged_in_user
    if current_user in current_db:
        udata = current_db[current_user]
        is_vip = udata.get("vip", False)
        
        st.sidebar.markdown(f"👤 **{current_user}**")
        st.sidebar.markdown(f"📧 *{udata.get('email', 'Təyin edilməyib')}*")
        
        if is_vip:
            st.sidebar.markdown("<p style='color: #facc15; font-weight: bold;'>👑 VIP Statusu Aktivdir!</p>", unsafe_allow_html=True)
        else:
            st.sidebar.info("Standart Hesab")
            if st.sidebar.button("👑 VIP Ol ($3/ay)", use_container_width=True):
                current_db[current_user]["vip"] = True
                save_users(current_db)
                st.sidebar.success("Təbriklər! Artıq VIP statusunuz aktivləşdi 🚀")
                st.rerun()
                
    if st.sidebar.button("Hesabdan Çıx", use_container_width=True):
        st.session_state.logged_in_user = None
        cookie_manager.delete("aligo_user")
        st.rerun()

# --- SÖHBƏT TARİXÇƏSİ ---
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
        is_active = (cid == st.session_state.current_chat_id)
        btn_label = f"📍 {cdata['title']}" if is_active else cdata['title']
        if st.button(btn_label, key=f"chat_{cid}", use_container_width=True):
            st.session_state.current_chat_id = cid
            st.session_state.show_aliai = True
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

# --- ƏSAS EKRAN ---
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.logged_in_user:
        st.markdown(f"<h4 style='color: #00f2fe;'>Xoş gəldin, {st.session_state.logged_in_user}!</h4>", unsafe_allow_html=True)
    else:
        st.markdown("<h4 style='color: #cbd5e1;'>Qonaq Rejimi</h4>", unsafe_allow_html=True)

with col2:
    if st.button("🤖 AliAI"):
        st.session_state.show_aliai = not st.session_state.show_aliai
        st.rerun()

st.markdown("""
    <div class="aligo-logo">
        <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
    </div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 25px;">Süni İntellekt və Axtarış Mərkəzi</p>
""", unsafe_allow_html=True)

# --- GROQ FUNKSİYASI ---
def ask_groq(prompt_text):
    if not ai_client:
        return "⚠️ Diqqət: Streamlit secrets hissəsində 'GROQ_API_KEY' tapılmadı."
    try:
        completion = ai_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt_text}],
            temperature=0.7,
            max_completion_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception:
        return "⚠️ Süni intellekt hazırda cavab verə bilmir."

# --- ALİ-Aİ VƏ YA AXTARIŞ ---
if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})
    
    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("AliAI-dən soruş..."):
        current_chat["messages"].append({"role": "user", "content": prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:20] + "..."

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("AliAI düşünür..."):
                response = ask_groq(prompt)
                st.markdown(response)
                current_chat["messages"].append({"role": "assistant", "content": response})

    if st.button("❌ Paneli Bağla"):
        st.session_state.show_aliai = False
        st.rerun()
else:
    search_query = st.text_input("", placeholder="AliAI-dən soruş və ya axtar...", key="main_search", label_visibility="collapsed")
    if search_query:
        with st.spinner("AliGO düşünür..."):
            ai_resp = ask_groq(search_query)
            st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #00f2fe; padding: 20px; border-radius: 20px;">
                    <span style="color: #00f2fe; font-size: 0.8rem; font-weight: bold;">🧠 AliAI Cavabı</span>
                    <p style="color: #f8fafc; margin-top: 10px;">{ai_resp}</p>
                </div>
            """, unsafe_allow_html=True)
