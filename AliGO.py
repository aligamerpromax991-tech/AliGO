import streamlit as st
import psutil
import json
import uuid
import hashlib
from groq import Groq
import os
import streamlit.components.v1 as components

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Şəxsi Mərkəz", page_icon="🏔️", layout="centered")

# --- PAROLU ŞİFRƏLƏMƏK ÜÇÜN HASH FUNKSİYASI ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- İSTİFADƏÇİLƏRİN FAYLDA DAXLANMASI ---
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
    default_db = {"admin": {"pass": hash_password("1234"), "plan": "UltiPremium", "email": "admin@aligo.com"}}
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

# --- MÖHTƏŞƏM FUTURİSTİK DAĞ MƏNZƏRƏSİ VƏ ÜSLUBLAR ---
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

# --- BRAUZER YADDAŞINDAN OXUMAK ÜÇÜN JS ---
local_storage_code = """
<script>
    const savedUser = localStorage.getItem("aligo_logged_user");
    if (savedUser) {
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('hesab')) {
            urlParams.set('hesab', savedUser);
            window.location.search = urlParams.toString();
        }
    }
</script>
"""
components.html(local_storage_code, height=0, width=0)

query_params = st.query_params
if not st.session_state.logged_in_user and "hesab" in query_params:
    url_user = query_params["hesab"]
    if url_user in current_db:
        st.session_state.logged_in_user = url_user

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
                st.query_params["hesab"] = matched_user
                components.html(f"""<script>localStorage.setItem("aligo_logged_user", "{matched_user}");</script>""", height=0, width=0)
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
                current_db[new_username] = {"pass": hash_password(new_pass1), "email": new_email, "plan": "Flash"}
                save_users(current_db)
                st.session_state.logged_in_user = new_username
                st.query_params["hesab"] = new_username
                components.html(f"""<script>localStorage.setItem("aligo_logged_user", "{new_username}");</script>""", height=0, width=0)
                st.sidebar.success("Hesab uğurla yaradıldı!")
                st.rerun()
else:
    current_user = st.session_state.logged_in_user
    if current_user in current_db:
        udata = current_db[current_user]
        current_plan = udata.get("plan", "Flash")
        
        st.sidebar.markdown(f"👤 **{current_user}**")
        st.sidebar.markdown(f"📦 Versiya: **{current_plan}**")
        
        # --- VERSİYA SEÇİMİ ---
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🚀 Paketini Seç")
        
        col_p1, col_p2, col_p3 = st.sidebar.columns(3)
        with col_p1:
            if st.button("⚡ Flash", use_container_width=True):
                current_db[current_user]["plan"] = "Flash"
                save_users(current_db)
                st.rerun()
        with col_p2:
            if st.button("🚀 Pro", use_container_width=True):
                current_db[current_user]["plan"] = "Pro"
                save_users(current_db)
                st.rerun()
        with col_p3:
            if st.button("👑 Ulti", use_container_width=True):
                current_db[current_user]["plan"] = "UltiPremium"
                save_users(current_db)
                st.rerun()

        # --- AYARLAR PANELİ ---
        with st.sidebar.expander("⚙️ Tənzimləmələr"):
            st.session_state.ai_temp = st.slider("AI Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1)
            new_pwd = st.text_input("Yeni Şifrə", type="password", key="new_p")
            if st.button("Şifrəni Yenilə"):
                if len(new_pwd) >= 4:
                    current_db[current_user]["pass"] = hash_password(new_pwd)
                    save_users(current_db)
                    st.success("Şifrə dəyişdirildi!")
                else:
                    st.error("Şifrə qısadır!")

    if st.sidebar.button("Hesabdan Çıx", use_container_width=True):
        st.session_state.logged_in_user = None
        if "hesab" in st.query_params:
            del st.query_params["hesab"]
        components.html("""<script>localStorage.removeItem("aligo_logged_user");</script>""", height=0, width=0)
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

# --- ƏSAS EKRAN ---
col1, col2 = st.columns([3, 1])
with col1:
    if st.session_state.logged_in_user:
        active_plan = current_db[st.session_state.logged_in_user].get("plan", "Flash")
        st.markdown(f"<h4 style='color: #00f2fe;'>Xoş gəldin, {st.session_state.logged_in_user} ({active_plan})!</h4>", unsafe_allow_html=True)
    else:
        st.markdown("<h4 style='color: #cbd5e1;'>Qonaq Rejimi (Flash)</h4>", unsafe_allow_html=True)

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

# --- GROQ SORĞU FUNKSİYASI (PAKET MƏNTİQİ: FLASH, PRO, ULTIPREMIUM) ---
def ask_groq(messages_history, user_plan="Flash"):
    if not ai_client:
        return "⚠️ Diqqət: Streamlit secrets hissəsində 'GROQ_API_KEY' tapılmadı."
    try:
        # İstədiyin nisbətə uyğun olaraq token gücünü tənzimləyirik:
        # Flash: 400 token | Pro: 2000 token (~5 qat) | UltiPremium: 4000 token (~10 qat)
        if user_plan == "Flash":
            max_tokens = 400
            system_content = "Sən Flash rejimində işləyən sürətli köməkçisən. Qısa, dəqiq və birbaşa cavablar ver."
        elif user_plan == "Pro":
            max_tokens = 2000
            system_content = "Sən Pro rejimində işləyən mütəxəssissən. Ətraflı, strukturlu və səliqəli kod/izahatlar təqdim et."
        else: # UltiPremium
            max_tokens = 4000
            system_content = (
                "Sən UltiPremium ekspert və strateji müzakirəçi partnyorusan. "
                "Boş-boş danışma, hər zaman dərin məntiqi təhlil apar, məsələnin kökünü aç, "
                "akademik və peşəkar səviyyədə müzakirə apar, ən optimal həll yollarını və əlaqəli mənbə linklərini təqdim et."
            )

        system_msg = {"role": "system", "content": system_content}
        full_messages = [system_msg] + messages_history

        completion = ai_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=full_messages,
            temperature=st.session_state.ai_temp,
            max_completion_tokens=max_tokens,
        )
        return completion.choices[0].message.content
    except Exception:
        return f"⚠️ Xəta baş verdi: İnternet bağlantınızı və ya API açarını yoxlayın."

# --- SÜRƏTLİ ƏMƏLİYYAT DÜYMƏLƏRİ ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
    if st.button("❓ Sual Soruş", use_container_width=True):
        st.session_state.trigger_prompt = "Mənə maraqlı bir mövzu haqqında məlumat ver."
        st.session_state.show_aliai = True
        st.rerun()
with col_q2:
    if st.button("💻 Kod Yaz", use_container_width=True):
        st.session_state.trigger_prompt = "Mənə bir proqramlaşdırma layihəsində kömək et, kod yazaq."
        st.session_state.show_aliai = True
        st.rerun()
with col_q3:
    if st.button("📊 Plan Qur", use_container_width=True):
        st.session_state.trigger_prompt = "Mənə məhsuldar bir plan qurmağımda kömək et."
        st.session_state.show_aliai = True
        st.rerun()
with col_q4:
    if st.button("🎨 Şəkil/İdeya", use_container_width=True):
        st.session_state.trigger_prompt = "Mənə yaradıcı dizayn və ya layihə ideyaları ver."
        st.session_state.show_aliai = True
        st.rerun()

# --- ALİ-Aİ ÇAT VƏ YA ƏSAS AXTARIŞ ---
if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})
    
    active_plan = "Flash"
    if st.session_state.logged_in_user and st.session_state.logged_in_user in current_db:
        active_plan = current_db[st.session_state.logged_in_user].get("plan", "Flash")

    new_chat_title = st.text_input("Söhbətin Adı:", value=current_chat["title"], key="rename_chat_input")
    if new_chat_title != current_chat["title"]:
        current_chat["title"] = new_chat_title
        st.rerun()

    if st.session_state.trigger_prompt:
        p_text = st.session_state.trigger_prompt
        st.session_state.trigger_prompt = None
        current_chat["messages"].append({"role": "user", "content": p_text})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = p_text[:20] + "..."
        
        with st.spinner(f"AliAI ({active_plan}) düşünür..."):
            history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
            response = ask_groq(history_for_api, active_plan)
            current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    for message in current_chat["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    uploaded_file = st.file_uploader("Fayl və ya şəkil əlavə et", type=["png", "jpg", "jpeg", "txt", "py", "json"])

    if prompt := st.chat_input("AliAI-dən soruş..."):
        full_prompt = prompt
        if uploaded_file is not None:
            full_prompt += f"\n[İstifadəçi bir fayl/şəkil yüklədi: {uploaded_file.name}]"

        current_chat["messages"].append({"role": "user", "content": full_prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:20] + "..."

        with st.chat_message("user"):
            st.markdown(full_prompt)

        with st.chat_message("assistant"):
            with st.spinner(f"AliAI ({active_plan}) düşünür..."):
                history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
                response = ask_groq(history_for_api, active_plan)
                st.markdown(response)
                current_chat["messages"].append({"role": "assistant", "content": response})

    if st.button("❌ Paneli Bağla"):
        st.session_state.show_aliai = False
        st.rerun()
else:
    active_plan = "Flash"
    if st.session_state.logged_in_user and st.session_state.logged_in_user in current_db:
        active_plan = current_db[st.session_state.logged_in_user].get("plan", "Flash")

    search_query = st.text_input("", placeholder="AliAI-dən soruş və ya hər hansı bir şeyi axtar...", key="main_search", label_visibility="collapsed")
    if search_query:
        st.session_state.show_aliai = True
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        current_chat["messages"].append({"role": "user", "content": search_query})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = search_query[:20] + "..."
        
        with st.spinner(f"AliGO ({active_plan}) axtarır..."):
            history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
            ai_resp = ask_groq(history_for_api, active_plan)
            current_chat["messages"].append({"role": "assistant", "content": ai_resp})
        st.rerun()
