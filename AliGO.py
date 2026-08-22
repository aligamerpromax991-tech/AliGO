import streamlit as st
import psutil
import urllib.request
import json
import urllib.parse
import google.generativeai as genai

# --- SƏHİFƏNİN TƏNZİMLƏMƏLƏRİ (ƏVVƏLDƏ OLMALIDIR) ---
st.set_page_config(page_title="AliGo - Şəxsi Mərkəz", page_icon="🏔️", layout="centered")

# --- GEMINI API QURAŞDIRMASI (YENİ MODEL: gemini-3.6-flash) ---
ai_model = None
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    # Ən son rəsmi model adı təyin edildi
    ai_model = genai.GenerativeModel("gemini-3.6-flash")
except Exception as e:
    try:
        ai_model = genai.GenerativeModel("models/gemini-3.6-flash")
    except:
        ai_model = None

# --- MÖHTƏŞƏM FUTURİSTİK DAĞ MƏNZƏRƏSİ VƏ NEON QRAFİKA ---
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

    .stTextInput input { 
        background-color: rgba(15, 23, 42, 0.85); 
        color: #f8fafc; 
        border-radius: 35px; 
        border: 2px solid #00f2fe;
        padding: 15px 25px;
        font-size: 1.1rem;
        box-shadow: 0 0 15px rgba(0, 242, 254, 0.3);
    }
    .stTextInput input:focus {
        border-color: #4facfe;
        box-shadow: 0 0 25px rgba(79, 172, 254, 0.6);
    }

    .aligo-logo {
        text-align: center;
        font-size: 4.8rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -2px;
        margin-top: 10px;
        margin-bottom: 0px;
        text-shadow: 0 0 25px rgba(0, 242, 254, 0.5), 0 4px 15px rgba(0,0,0,0.8);
    }

    .google-result-card {
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(0, 242, 254, 0.4);
        padding: 20px;
        border-radius: 20px;
        margin-bottom: 15px;
        backdrop-filter: blur(12px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
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

if "users_db" not in st.session_state:
    st.session_state.users_db = {"admin": {"pass": "1234", "vip": True}}
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None
if "show_aliai" not in st.session_state:
    st.session_state.show_aliai = False

# --- YAN PANEL ---
st.sidebar.markdown("### 👤 AliGo Hesab & VIP")

if st.session_state.logged_in_user:
    current_user = st.session_state.logged_in_user
    is_vip = st.session_state.users_db[current_user]["vip"]
    
    if is_vip:
        st.sidebar.markdown("<p style='color: #facc15; font-weight: bold;'>👑 VIP Statusu Aktivdir!</p>", unsafe_allow_html=True)
    else:
        st.sidebar.info("Standart Hesab")
        if st.sidebar.button("👑 VIP Ol ($3/ay)"):
            st.session_state.users_db[current_user]["vip"] = True
            st.sidebar.success("Təbriklər! Artıq VIP statusunuz aktivləşdi 🚀")
            st.rerun()
            
    if st.sidebar.button("Hesabdan Çıx"):
        st.session_state.logged_in_user = None
        st.rerun()
else:
    auth_mode = st.sidebar.radio("Seçim", ["Daxil ol", "Qeydiyyatdan keç"])
    if auth_mode == "Daxil ol":
        login_user = st.sidebar.text_input("İstifadəçi adı")
        login_pass = st.sidebar.text_input("Şifrə", type="password")
        if st.sidebar.button("Daxil Ol"):
            if login_user in st.session_state.users_db and st.session_state.users_db[login_user]["pass"] == login_pass:
                st.session_state.logged_in_user = login_user
                st.sidebar.success("Uğurla daxil oldunuz!")
                st.rerun()
            else:
                st.sidebar.error("Ad və ya şifrə səhvdir!")
    else:
        new_user = st.sidebar.text_input("Yeni İstifadəçi adı")
        new_pass = st.sidebar.text_input("Yeni Şifrə", type="password")
        if st.sidebar.button("Hesab Yarat"):
            if new_user in st.session_state.users_db:
                st.sidebar.error("Bu istifadəçi artıq mövcuddur!")
            elif new_user.strip() == "":
                st.sidebar.error("Ad boş ola bilməz!")
            else:
                st.session_state.users_db[new_user] = {"pass": new_pass, "vip": False}
                st.sidebar.success("Hesab uğurla yaradıldı!")

st.sidebar.markdown("---")
show_ads = True
if st.session_state.logged_in_user and st.session_state.users_db[st.session_state.logged_in_user]["vip"]:
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
col1, col2, col3, col4 = st.columns([2.2, 1.4, 1.2, 1])

with col1:
    if st.session_state.logged_in_user:
        user_name = st.session_state.logged_in_user
        is_user_vip = st.session_state.users_db[user_name]["vip"]
        badge = "👑 " if is_user_vip else "👤 "
        color = "#facc15" if is_user_vip else "#00f2fe"
        st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); padding: 8px 12px; border-radius: 30px; border: 1px solid {color}; text-align: center;">
                <span style="font-size: 0.8rem; color: {color}; font-weight: bold;">{badge}{user_name}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(10px); padding: 8px 12px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.2); text-align: center;">
                <span style="font-size: 0.8rem; color: #cbd5e1; font-weight: 500;">Hesab yoxdur</span>
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
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 30px; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">Süni İntellekt və Axtarış Mərkəzi</p>
""", unsafe_allow_html=True)

# --- ALİ-Aİ SÖHBƏT PƏNCƏRƏSİ ---
if st.session_state.show_aliai:
    st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.92); border: 2px solid #00f2fe; padding: 22px; border-radius: 22px; margin-bottom: 25px; box-shadow: 0 0 25px rgba(0,242,254,0.3);">
            <h2 style="color: #00f2fe; margin-top: 0; text-align: center;">🧠 AliAI - Şəxsi Süni İntellekt Mərkəzi</h2>
            <p style="text-align: center; color: #94a3b8; font-size: 0.95rem;">Tamamilə sənə özəl hazırlanmış orijinal AI interfeysi.</p>
        </div>
    """, unsafe_allow_html=True)
    
    ai_chat_query = st.text_input("", placeholder="AliAI-dən soruş...", key="aliai_input", label_visibility="collapsed")
    if ai_chat_query:
        if ai_model:
            try:
                with st.spinner("AliAI düşünür..."):
                    response = ai_model.generate_content(ai_chat_query)
                    if response and response.text:
                        st.markdown(f"""
                            <div class="google-result-card" style="border-color: #00f2fe;">
                                <span style="color: #00f2fe; font-size: 0.85rem; font-weight: bold;">✨ AliAI Cavabı:</span>
                                <p style="color: #f8fafc; margin-top: 10px; font-size: 1.1rem; line-height: 1.6;">{response.text}</p>
                            </div>
                        """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Xəta baş verdi: {e}")
        else:
            st.error("AI modeli aktiv deyil.")
            
    if st.button("❌ AliAI-ı Bağla"):
        st.session_state.show_aliai = False
        st.rerun()

# Əsas Axtarış Sətri
search_query = st.text_input("", placeholder="AliAI-dən soruş...", key="main_search", label_visibility="collapsed")

if search_query and not st.session_state.show_aliai:
    st.markdown(f"<p style='color: #00f2fe; text-align: center; font-size: 1.1rem;'>'{search_query}' üçün nəticələr:</p>", unsafe_allow_html=True)
    
    if ai_model:
        try:
            with st.spinner("AliGO düşünür..."):
                ai_response = ai_model.generate_content(search_query)
                if ai_response and ai_response.text:
                    st.markdown(f"""
                        <div class="google-result-card" style="border-color: #00f2fe;">
                            <span style="color: #00f2fe; font-size: 0.8rem; font-weight: bold;">🧠 AliAI Cavabı</span>
                            <p style="color: #f8fafc; margin-top: 10px; font-size: 1.05rem; line-height: 1.5;">{ai_response.text}</p>
                        </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"AI Xətası: {e}") 

    # Web Nəticəsi
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(search_query)}&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        has_result = False
        if data.get("AbstractText"):
            has_result = True
            st.markdown(f"""
                <div class="google-result-card">
                    <span style="color: #4facfe; font-size: 0.8rem; font-weight: bold;">🌐 Web Nəticəsi</span>
                    <h3 style="color: #00f2fe; margin: 5px 0 8px 0; font-size: 1.2rem;">{data.get('Heading', search_query)}</h3>
                    <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem;">{data.get('AbstractText')}</p>
                    <a href="{data.get('AbstractURL', '#')}" target="_blank" style="color: #a855f7; font-size: 0.85rem; text-decoration: none; display: inline-block; margin-top: 8px;">Ətraflı oxu ↗</a>
                </div>
            """, unsafe_allow_html=True)
            
        if not has_result and data.get("RelatedTopics"):
            for topic in data["RelatedTopics"][:2]:
                if "Text" in topic and "FirstURL" in topic:
                    st.markdown(f"""
                        <div class="google-result-card">
                            <span style="color: #4facfe; font-size: 0.8rem; font-weight: bold;">🌐 Web Nəticəsi</span>
                            <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem;">{topic['Text']}</p>
                            <a href="{topic['FirstURL']}" target="_blank" style="color: #a855f7; font-size: 0.85rem; text-decoration: none; display: inline-block; margin-top: 8px;">Ətraflı oxu ↗</a>
                        </div>
                    """, unsafe_allow_html=True)
                    has_result = True
                    
        if not has_result:
            st.markdown(f"""
                <div class="google-result-card">
                    <span style="color: #4facfe; font-size: 0.8rem; font-weight: bold;">🌐 Web Nəticəsi</span>
                    <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem;">'{search_query}' üzrə birbaşa web tapılmadı, lakin yuxarıdakı AliAI cavabı sualınızı cavablandırdı!</p>
                </div>
            """, unsafe_allow_html=True)
    except Exception:
        pass

elif not search_query and not st.session_state.show_aliai:
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Axtarış sətrinə nəsə yazın və ya yuxarıdakı **AliAI** düyməsinə basaraq söhbətə başlayın.</p>", unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("💻 Kompüter Sistem Vəziyyəti"):
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    st.write(f"Prosessor Yükü (CPU): {cpu}%")
    st.write(f"İstifadə olunan RAM: {ram.percent}% ({ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB)")
