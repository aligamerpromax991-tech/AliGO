import streamlit as st
import psutil
import urllib.request
import json

# Səhifənin tənzimləmələri
st.set_page_config(page_title="AliGo - Şəxsi Mərkəz", page_icon="🏔️", layout="centered")

# CSS Dizaynları: Dağ mənzərəsi, şık axtarış və Google tərzi nəticə kartları
st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.92)), 
                    url('https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    /* Axtarış sətrinin dizaynı */
    .stTextInput input { 
        background-color: rgba(30, 41, 59, 0.9); 
        color: white; 
        border-radius: 30px; 
        border: 2px solid #38bdf8;
        padding: 15px 25px;
        font-size: 1.1rem;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.5);
    }
    .stTextInput input:focus {
        border-color: #34d399;
        box-shadow: 0 0 20px rgba(52, 211, 153, 0.4);
    }

    /* AliGo Loqosu */
    .aligo-logo {
        text-align: center;
        font-size: 4.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -2px;
        margin-top: 20px;
        margin-bottom: 5px;
        text-shadow: 0 4px 15px rgba(0,0,0,0.6);
    }

    /* Google Nəticə Kartı (AliGo daxilində) */
    .google-result-card {
        background-color: rgba(30, 41, 59, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 18px 22px;
        border-radius: 15px;
        margin-bottom: 15px;
        backdrop-filter: blur(8px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        transition: 0.2s;
    }
    .google-result-card:hover {
        border-color: #38bdf8;
        transform: translateY(-2px);
    }
    </style>
""", unsafe_allow_html=True)

# --- YAN PANEL (REKLAM VƏ DƏSTƏK BÖLMƏSİ) ---
st.sidebar.markdown("### 📢 Sponsor & Reklam")
st.sidebar.markdown("""
    <div style="background: rgba(30, 41, 59, 0.85); padding: 12px; border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.2); text-align: center;">
        <p style="color: #94a3b8; font-size: 0.85rem; margin-bottom: 8px;">AliGo-nu dəstəkləyin</p>
        <a href="https://example.com" target="_blank" style="color: #38bdf8; font-weight: bold; text-decoration: none; font-size: 0.95rem;">
            🚀 Reklam Yerləşdir
        </a>
    </div>
""", unsafe_allow_html=True)

# Yuxarı sağ künc - Hesab yoxdursa sual işarəsi
col1, col2 = st.columns([5, 1])
with col2:
    st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); padding: 8px 16px; border-radius: 30px; border: 1px solid rgba(255,255,255,0.2); display: flex; align-items: center; gap: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <div style="background: #334155; color: #38bdf8; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 0.9rem;">?</div>
            <span style="font-size: 0.85rem; color: #cbd5e1; font-weight: 500;">Hesab yoxdur</span>
        </div>
    """, unsafe_allow_html=True)

# Loqo
st.markdown("""
    <div class="aligo-logo">
        <span style="color: #38bdf8;">A</span><span style="color: #818cf8;">l</span><span style="color: #c084fc;">i</span><span style="color: #34d399;">G</span><span style="color: #f43f5e;">o</span>
    </div>
    <p style="text-align:-webkit-center; text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 30px; text-shadow: 0 2px 5px rgba(0,0,0,0.5);">Nəticələr Google-dan, Pəncərə AliGo-dan!</p>
""", unsafe_allow_html=True)

# Axtarış Sətri
search_query = st.text_input("", placeholder="AliGo daxilində Google-dan axtar...", label_visibility="collapsed")

if search_query:
    st.markdown(f"<p style='color: #38bdf8; text-align: center; font-size: 1.1rem;'>'{search_query}' üçün Google nəticələri:</p>", unsafe_allow_html=True)
    
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(search_query)}&format=json"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        
        has_results = False
        if data.get("AbstractText"):
            has_results = True
            st.markdown(f"""
                <div class="google-result-card">
                    <span style="color: #34d399; font-size: 0.8rem; font-weight: bold;">Məlumat</span>
                    <h3 style="color: #38bdf8; margin: 5px 0 8px 0; font-size: 1.2rem;">{data.get('Heading', search_query)}</h3>
                    <p style="color: #cbd5e1; margin: 0; font-size: 0.95rem;">{data.get('AbstractText')}</p>
                    <a href="{data.get('AbstractURL', '#')}" target="_blank" style="color: #818cf8; font-size: 0.85rem; text-decoration: none; display: inline-block; margin-top: 8px;">Ətraflı oxu ↗</a>
                </div>
            """, unsafe_allow_html=True)
            
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and "Text" in topic and "FirstURL" in topic:
                has_results = True
                st.markdown(f"""
                    <div class="google-result-card">
                        <a href="{topic['FirstURL']}" target="_blank" style="color: #38bdf8; font-size: 1.1rem; font-weight: bold; text-decoration: none;">{topic['Text'].split(' - ')[0]} ↗</a>
                        <p style="color: #94a3b8; margin: 5px 0 0 0; font-size: 0.9rem;">{topic['Text']}</p>
                    </div>
                """, unsafe_allow_html=True)
                
        if not has_results:
            google_fallback = f"https://www.google.com/search?q={search_query}"
            st.markdown(f"""
                <div class="google-result-card" style="text-align: center;">
                    <p style="color: #f8fafc; margin-bottom: 10px;">'{search_query}' üçün internetdən birbaşa nəticələr:</p>
                    <a href="{google_fallback}" target="_blank" style="background: #38bdf8; color: #0f172a; padding: 10px 22px; border-radius: 20px; text-decoration: none; font-weight: bold;">Google-da Nəticələrə Bax 🚀</a>
                </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Xəta baş verdi: {e}")

else:
    st.markdown("<p style='text-align: center; color: #64748b;'>Axtarış sətrinə istədiyin sözü yaz, nəticələr birbaşa bu pəncərədə görünsün.</p>", unsafe_allow_html=True)

# Alt hissədə kompüterin sistem vəziyyəti
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("💻 Kompüter Sistem Vəziyyəti"):
    ram = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.1)
    st.write(f"Prosessor Yükü (CPU): {cpu}%")
    st.write(f"İstifadə olunan RAM: {ram.percent}% ({ram.used / (1024**3):.2f} GB / {ram.total / (1024**3):.2f} GB)")
