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

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Şəxsi Mərkəz", page_icon="🏔️", layout="centered")

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
    # Varsayılan admin hesabı (şifrə: 1234 -> hash formatında)
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

# --- MÖHTƏŞƏM FUTURİSTİK DAĞ MƏNZƏRƏSİ VƏ CHAT DİZAYNI ---
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

    <script>
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
    });
    function installApp() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                deferredPrompt = null;
            });
        } else {
            alert("AliGo-nu əsas ekrana əlavə etmək üçün brauzer menyusundan 'Tətbiqi quraşdır' seçə bilərsiniz!");
        }
    }
    </script>
""", unsafe_allow_html=True)

# --- SESSİYA VƏ URL PARAMETRLƏRİ ---
query_params = st.query_params

if "logged_in_user" not in st.session_state:
    if "user" in query_params:
        st.session_state.logged_in_user = query_params["user"]
    else:
        st.session_state.logged_in_user = None

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

# --- ƏSL LOGİN VƏ QEYDİYYAT MODULU (SOL PANEL) ---
current_db = load_users()

st.sidebar.markdown("### 🔐 İstifadəçi Hesabı")

if not st.session_state.logged_in_user:
    # Giriş və Qeydiyyat üçün Tablar (Sekmələr)
    login_tab, register_tab = st.sidebar.tabs(["Daxil Ol", "Qeydiyyat"])
    
    with login_tab:
        st.markdown("#### Hesabınıza daxil olun")
        login_user = st.text_input("İstifadəçi adı və ya E-poçt", key="l_user")
        login_pass = st.text_input("Şifrə", type="password", key="l_pass")
        
        if st.button("Daxil Ol", use_container_width=True, key="btn_login"):
            matched_user = None
            # İstifadəçi adı və ya e-poçt ilə yoxlama
            for uname, udata in current_db.items():
                if uname == login_user or udata.get("email") == login_user:
                    matched_user = uname
                    break
            
            if matched_user and current_db[matched_user]["pass"] == hash_password(login_pass):
                st.session_state.logged_in_user = matched_user
                st.query_params["user"] = matched_user
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
                # Bazaya əlavə et (şifrəni hash edərək)
                current_db[new_username] = {
                    "pass": hash_password(new_pass1),
                    "email": new_email,
                    "vip": False
                }
                save_users(current_db)
                st.session_state.logged_in_user = new_username
                st.query_params["user"] = new_username
                st.sidebar.success("Hesab uğurla yaradıldı!")
                st.rerun()
else:
    # İstifadəçi artıq daxil olubsa
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
                
        if current_user == "admin":
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🛡️ Admin Paneli")
            with st.sidebar.expander("Qeydiyyatdan Keçənlər"):
                for uname, udata_info in current_db.items():
                    status_text = "👑 VIP" if udata_info.get("vip") else "👤 Standart"
                    st.write(f"• **{uname}** ({status_text}) - *{udata_info.get('email','')}*")
                
    if st.sidebar.button("Hesabdan Çıx", use_container_width=True):
        st.session_state.logged_in_user = None
        if "user" in st.query_params:
            del st.query_params["user"]
        st.rerun()

# --- SÖHBƏT TARİXÇƏSİ (ÇATLAR PANELİ) ---
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

st.sidebar.markdown("---")
show_ads = True
if st.session_state.logged_in_user and st.session_state.logged_in_user in current_db:
    if current_db[st.session_state.logged_in_user].get("vip"):
        show_ads = False

if show_ads:
    st.sidebar.markdown("### 📢 Sponsor & Reklam")
    st.sidebar.markdown("""
        <div style="background: rgba(15, 23, 42, 0.85); padding: 12px; border-radius: 12px; border: 1px solid rgba(0, 242, 254, 0.3); text-align: center;">
            <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px;">AliGo-nu dəstəkləyin</p>
            <a href="#" target="_blank" style="color: #00f2fe; font-weight: bold; text-decoration: none; font-size: 0.95rem;">
                🚀 Reklam Yerləşdir
            </a>
        </div>
    """, unsafe_allow_html=True)
else:
    st.sidebar.markdown("✨ *VIP üstünlüyü: Reklamlar gizlədildi!*")

# --- YUXARI SAĞ KÜNC ---
col1, col2, col3 = st.columns([2.2, 1.4, 1.2])

with col1:
    if st.session_state.logged_in_user and st.session_state.logged_in_user in current_db:
        user_name = st.session_state.logged_in_user
        is_user_vip = current_db[user_name].get("vip", False)
        badge = "👑 " if is_user_vip else "👤 "
        color = "#facc15" if is_user_vip else "#00f2fe"
        st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); padding: 8px 12px; border-radius: 30px; border: 1px solid {color}; text-align: center;">
                <span style="font-size: 0.85rem; color: {color}; font-weight: bold;">{badge}{user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); padding: 8px 12px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.2); text-align: center;">
                <span style="font-size: 0.8rem; color: #cbd5e1; font-weight: 500;">Qonaq Rejimi</span>
            </div>
        """, unsafe_allow_html=True)

with col2:
    if st.button("🤖 AliAI"):
        st.session_state.show_aliai = not st.session_state.show_aliai
        st.rerun()

with col3:
    st.markdown("""
        <a href="javascript:void(0);" onclick="installApp()" style="text-decoration: none;">
            <div style="background: linear-gradient(135deg, #00f2fe, #4facfe); backdrop-filter: blur(10px); padding: 8px 14px; border-radius: 30px; text-align: center; box-shadow: 0 4px 15px rgba(0,242,254,0.4);">
                <span style="color: #050b14; font-weight: bold; font-size: 0.85rem;">📥 İndir</span>
            </div>
        </a>
    """, unsafe_allow_html=True)

# Loqo
st.markdown("""
    <div class="aligo-logo">
        <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
    </div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 25px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">Süni İntellekt və Axtarış Mərkəzi</p>
""", unsafe_allow_html=True)

# --- GROQ MODEL FUNKSİYASI ---
def ask_groq(prompt_text):
    if not ai_client:
        return "⚠️ Diqqət: Streamlit secrets hissəsində 'GROQ_API_KEY' tapılmadı."
    
    models_to_try = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    for model_name in models_to_try:
        try:
            completion = ai_client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt_text}],
                temperature=0.7,
                max_completion_tokens=1024,
            )
            return completion.choices[0].message.content
        except Exception as e:
            err_str = str(e)
            if "rate_limit_exceeded" in err_str or "429" in err_str:
                match = re.search(r'in\s+([\d\.]+)(s|m)', err_str)
                if match:
                    wait_time = match.group(1)
                    return f"⏳ **Sürət Limiti Aşılıb!** Təxminən **{wait_time} saniyə** gözləyib yenidən cəhd edin."
                else:
                    return "⏳ **Sürət Limiti Aşılıb!** Zəhmət olmasa bir neçə saniyə gözləyin."
            continue
    return f"⚠️ Süni intellekt hazırda cavab verə bilmir."

# --- ƏĞƏR ALİ-Aİ AKTİVDİRSƏ ---
if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})
    
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0, 242, 254, 0.4); padding: 15px; border-radius: 15px; margin-bottom: 20px; text-align: center;">
            <h3 style="color: #00f2fe; margin: 0;">🧠 AliAI Söhbət Mərkəzi</h3>
            <p style="color: #94a3b8; font-size: 0.85rem; margin: 5px 0 0 0;">Aktiv Söhbət: <b style="color: #4facfe;">{current_chat['title']}</b></p>
        </div>
    """, unsafe_allow_html=True)

    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if not current_chat["messages"]:
        st.markdown("<p style='text-align: center; color: #cbd5e1; font-size: 0.9rem;'>Sürətli başlanğıc üçün seçin:</p>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("💻 Kod yazmaq"):
                prompt = "Mənə Python-da sadə bir kalkulyator kodu yaz."
                current_chat["messages"].append({"role": "user", "content": prompt})
                current_chat["title"] = "Python Kalkulyator"
                with st.spinner("AliAI yazır..."):
                    resp = ask_groq(prompt)
                    current_chat["messages"].append({"role": "assistant", "content": resp})
                st.rerun()
        with c2:
            if st.button("🎨 Şəkil yaratmaq"):
                prompt = "Gələcəyin şəhəri haqqında təsvir yaz."
                current_chat["messages"].append({"role": "user", "content": prompt})
                current_chat["title"] = "Gələcək Şəhəri"
                with st.spinner("AliAI yazır..."):
                    resp = ask_groq(prompt)
                    current_chat["messages"].append({"role": "assistant", "content": resp})
                st.rerun()
        with c3:
            if st.button("🚀 Plan qurmaq"):
                prompt = "YouTube üçün kanal açmaq planı qur."
                current_chat["messages"].append({"role": "user", "content": prompt})
                current_chat["title"] = "YouTube Planı"
                with st.spinner("AliAI yazır..."):
                    resp = ask_groq(prompt)
                    current_chat["messages"].append({"role": "assistant", "content": resp})
                st.rerun()

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

    if st.button("❌ AliAI Panelini Bağla"):
        st.session_state.show_aliai = False
        st.rerun()

else:
    search_query = st.text_input("", placeholder="AliAI-dən soruş və ya axtar...", key="main_search", label_visibility="collapsed")

    if search_query:
        st.markdown(f"<p style='color: #00f2fe; text-align: center; font-size: 1.1rem;'>'{search_query}' üçün nəticələr:</p>", unsafe_allow_html=True)
        
        with st.spinner("AliGO düşünür..."):
            ai_resp = ask_groq(search_query)
            st.markdown(f"""
                <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid #00f2fe; padding: 20px; border-radius: 20px; margin-bottom: 15px;">
                    <span style="color: #00f2fe; font-size: 0.8rem; font-weight: bold;">🧠 AliAI Cavabı</span>
                    <p style="color: #f8fafc; margin-top: 10px; font-size: 1.05rem; line-height: 1.5;">{ai_resp}</p>
                </div>
            """, unsafe_allow_html=True)

        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(search_query)}&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data.get("AbstractText"):
                st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(0, 242, 254, 0.4); padding: 20px; border-radius: 20px;">
                        <span style="color: #4facfe; font-size: 0.8rem; font-weight: bold;">🌐 Web Nəticəsi</span>
                        <h3 style="color: #00f2fe; margin: 5px 0 8px 0; font-size: 1.2rem;">{data.get('Heading', search_query)}</h3>
                        <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem;">{data.get('AbstractText')}</p>
                    </div>
                """, unsafe_allow_html=True)
        except Exception:
            pass
    else:
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Axtarış sətrinə nəsə yazın və ya yuxarıdakı **AliAI** düyməsinə basaraq söhbət panelini açın.</p>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("💻 Kompüter Sistem Vəziyyəti"):
    try:
        ram = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.1)
        st.write(f"Prosessor Yükü (CPU): {cpu}%")
        st.write(f"İstifadə olunan RAM: {ram.percent}% ({ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB)")
    except Exception:
        st.write("Sistem məlumatları oxunmadı.")
