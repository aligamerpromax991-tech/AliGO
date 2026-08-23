import streamlit as st
import uuid
import time
from groq import Groq

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(page_title="AliGo - Süni İntellekt Mərkəzi", page_icon="🏔️", layout="centered")

# --- GROQ MÜŞTƏRİSİ ---
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

# --- STİLLƏR VƏ DALĞALI ANIMASİYA ---
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

    @keyframes aligo-wave {
        0%, 100% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 10px #00f2fe); }
        50% { transform: translateY(-10px) scale(1.08); filter: drop-shadow(0 0 25px #a855f7); }
    }

    .spinning-aligo-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 30px 0;
    }

    .spinning-logo {
        font-size: 3rem;
        font-weight: 900;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        animation: aligo-wave 1.5s infinite ease-in-out;
        display: inline-block;
    }

    .loading-text {
        color: #00f2fe;
        font-family: 'Segoe UI', sans-serif;
        font-size: 1.1rem;
        margin-top: 15px;
        letter-spacing: 1px;
        text-shadow: 0 0 10px rgba(0, 242, 254, 0.6);
    }

    .stChatInputContainer {
        border-radius: 25px !important;
        border: 2px solid #00f2fe !important;
        background-color: rgba(15, 23, 42, 0.9) !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
    }

    .user-message-box {
        background: rgba(0, 242, 254, 0.1);
        border: 1px solid rgba(0, 242, 254, 0.3);
        padding: 12px 18px;
        border-radius: 15px;
        margin-bottom: 10px;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
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

# --- KÖMƏKÇİ: DALĞALI ALIGO ANIMASİYA EKRANI ---
def show_custom_spinner(text="AliGo cavab axtarır..."):
    st.markdown(f"""
        <div class="spinning-aligo-container">
            <div class="spinning-logo">
                <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
            </div>
            <div class="loading-text">{text}</div>
        </div>
    """, unsafe_allow_html=True)

# --- SOL PANEL ---
st.sidebar.markdown("### 💬 Söhbət Tarixçəsi")
st.sidebar.markdown("🔒 *Qeydiyyatsız Rejim aktivdir*")

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

with st.sidebar.expander("⚙️ Tənzimləmələr"):
    st.session_state.ai_temp = st.slider("AI Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1)

# --- ƏSAS EKRAN ---
active_plan = st.session_state.guest_plan

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("<h4 style='color: #00f2fe;'>Qeydiyyatsız Rejim</h4>", unsafe_allow_html=True)

with col2:
    if st.button("🤖 AliAI"):
        st.session_state.show_aliai = not st.session_state.show_aliai
        st.rerun()

st.markdown("""
    <div class="aligo-logo">
        <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
    </div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 15px;">Süni İntellekt və Axtarış Mərkəzi</p>
""", unsafe_allow_html=True)

# --- REJİM SEÇİM PANELİ ---
cols_mode = st.columns(3)
with cols_mode[0]:
    if st.button("⚡ Flash (Sürətli)", use_container_width=True, type="primary" if active_plan=="Flash" else "secondary"):
        st.session_state.guest_plan = "Flash"
        st.rerun()
with cols_mode[1]:
    if st.button("🚀 Pro (Balanslı)", use_container_width=True, type="primary" if active_plan=="Pro" else "secondary"):
        st.session_state.guest_plan = "Pro"
        st.rerun()
with cols_mode[2]:
    if st.button("👑 UltiPremium (Ekspert)", use_container_width=True, type="primary" if active_plan=="UltiPremium" else "secondary"):
        st.session_state.guest_plan = "UltiPremium"
        st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- GROQ SORĞU FUNKSİYASI ---
def ask_groq(messages_history, user_plan="Flash", mode="chat"):
    start_time = time.time()
    
    # Əsas şəxsiyyət və davranış qaydası
    base_identity = (
        "QAYDA: Sənin adın AliGo-dur! Sən AliGo Süni İntellekt və Axtarış Mərkəzisən. "
        "Hər salamlaşmada və ya ümumi söhbətlərdə dərhal özünü tərifləmə və ya kim tərəfindən yaradıldığını öz-özünə danışma — sadəcə təbii, səmimi və normal cavab ver. "
        "Amma kimsə səndən xüsusi olaraq kimliyini, səni kimin yaratdığını və ya yaşını soruşsa, qürurla bildir ki: "
        "'Mən AliGo-yam, səni isə 14 yaşı olmasına baxmayaraq çox istedadlı və dahi olan Əli adlı mütəxəssis proqramçı kodlayıb və yaradıb!'\n\n"
    )
    
    if mode == "search":
        system_content = base_identity + (
            "Sən AliGo Axtarış Mərkəzisən. İstifadəçi səndən nəsə tapmağı, endirməyi və ya hər hansı fayl/proqram haqqında məlumat istəyir. "
            "Ona birbaşa rəsmi mənbələri, yükləmə yollarını, aydın və ətraflı şəkildə haradan əldə edə biləcəyini göstər."
        )
        max_tokens = 2000
    else:
        if user_plan == "Flash":
            max_tokens = 1200
            system_content = base_identity + "Sən Flash rejimində işləyən sürətli köməkçisən. Sualı qısa deyil, normal, anlaşılan və kifayət qədər ətraflı izah et."
        elif user_plan == "Pro":
            max_tokens = 2500
            system_content = base_identity + "Sən Pro rejimində işləyən mütəxəssis mühəndis/analitiksen. Strukturlu və ətraflı cavablar ver."
        else:
            max_tokens = 4000
            system_content = base_identity + "Sən UltiPremium səviyyəsində işləyən ekspert strateji müzakirəçisən. Dərin təhlil apar."

    system_msg = {"role": "system", "content": system_content}
    full_messages = [system_msg] + messages_history

    try:
        client = get_groq_client()
        completion = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=full_messages,
            temperature=st.session_state.ai_temp,
            max_tokens=max_tokens,
        )
        
        elapsed = time.time() - start_time
        if elapsed < 2.5:
            time.sleep(2.5 - elapsed)
            
        return completion.choices[0].message.content

    except Exception as e:
        return f"⚠️ Xəta baş verdi: {e}"

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

# --- ÇAT VƏ YA AXTARIŞ MƏRKƏZİ ---
if st.session_state.show_aliai:
    current_chat = st.session_state.chats.get(st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []})
    
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
        
        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo cavab axtarır...")
        
        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
        response = ask_groq(history_for_api, active_plan, mode="chat")
        
        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    for message in current_chat["messages"]:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message-box"><b>Sən:</b><br>{message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(message["content"])
            st.markdown("---")

    uploaded_file = st.file_uploader("Fayl və ya şəkil əlavə et", type=["png", "jpg", "jpeg", "txt", "py", "json"])

    if prompt := st.chat_input("AliGo-dan soruş..."):
        full_prompt = prompt
        if uploaded_file is not None:
            full_prompt += f"\n[İstifadəçi bir fayl/şəkil yüklədi: {uploaded_file.name}]"

        current_chat["messages"].append({"role": "user", "content": full_prompt})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = prompt[:20] + "..."

        st.markdown(f'<div class="user-message-box"><b>Sən:</b><br>{full_prompt}</div>', unsafe_allow_html=True)

        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo cavab axtarır...")
        
        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
        response = ask_groq(history_for_api, active_plan, mode="chat")
        
        placeholder.empty()
        st.markdown(response)
        current_chat["messages"].append({"role": "assistant", "content": response})
        st.rerun()

    if st.button("❌ Paneli Bağla"):
        st.session_state.show_aliai = False
        st.rerun()
else:
    search_query = st.text_input("", placeholder="Axtarış Mərkəzi: Məsələn, 'CapCut PC indir' və ya 'Python öyrənmək üçün saytlar'...", key="main_search", label_visibility="collapsed")
    if search_query:
        st.session_state.show_aliai = True
        current_chat = st.session_state.chats[st.session_state.current_chat_id]
        current_chat["messages"].append({"role": "user", "content": search_query})
        if current_chat["title"] == "Yeni Söhbət":
            current_chat["title"] = search_query[:20] + "..."
        
        placeholder = st.empty()
        with placeholder.container():
            show_custom_spinner("AliGo cavab axtarır...")
        
        history_for_api = [{"role": m["role"], "content": m["content"]} for m in current_chat["messages"]]
        ai_resp = ask_groq(history_for_api, active_plan, mode="search")
        
        placeholder.empty()
        current_chat["messages"].append({"role": "assistant", "content": ai_resp})
        st.rerun()
