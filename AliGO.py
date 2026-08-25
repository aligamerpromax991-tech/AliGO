import base64
import time
import urllib.parse
import uuid
from groq import Groq
from supabase import Client, create_client
import streamlit as st

# --- SƏHİFƏ TƏNZİMLƏMƏLƏRİ ---
st.set_page_config(
    page_title="AliGo - Süni İntellekt Mərkəzi",
    page_icon="⚡",
    layout="centered",
)

# --- GROQ VƏ SUPABASE QOŞULMASI ---


def get_groq_client():
  return Groq(api_key=st.secrets.get("GROQ_API_KEY", ""))


SUPABASE_URL = "https://iqfxtorbnjvnqsdgloyd.supabase.co"
SUPABASE_KEY = "sb_publishable_dF7WkdLq8ohQrVkl4SDlHw_w_4os4pt"

supabase: Client = None
try:
  supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
  st.error(f"Supabase Qoşulma Xətası: {e}")

# --- STİLLƏR VƏ CSS ---
st.markdown(
    """
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
        font-size: 4.5rem;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 900;
        letter-spacing: -2px;
        margin-top: 5px;
        margin-bottom: 0px;
        background: linear-gradient(45deg, #00f2fe, #4facfe, #a855f7, #22c55e, #f43f5e);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0px 4px 15px rgba(0, 242, 254, 0.4));
    }

    @keyframes aligo-wave {
        0%, 100% { transform: translateY(0) scale(1); filter: drop-shadow(0 0 8px #00f2fe); }
        50% { transform: translateY(-5px) scale(1.05); filter: drop-shadow(0 0 15px #a855f7); }
    }

    .small-spinning-container {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 15px 0;
    }

    .small-spinning-logo {
        font-size: 1.8rem;
        font-weight: 900;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        animation: aligo-wave 1.2s infinite ease-in-out;
        display: inline-block;
    }

    .loading-text-small {
        color: #00f2fe;
        font-family: 'Segoe UI', sans-serif;
        font-size: 0.95rem;
        letter-spacing: 0.5px;
        text-shadow: 0 0 8px rgba(0, 242, 254, 0.5);
    }

    .stChatInputContainer {
        border-radius: 25px !important;
        border: 2px solid #00f2fe !important;
        background-color: rgba(15, 23, 42, 0.9) !important;
        box-shadow: 0 0 20px rgba(0, 242, 254, 0.3) !important;
    }

    .chat-row {
        display: flex;
        width: 100%;
        margin-bottom: 12px;
    }
    .chat-row.user { justify-content: flex-end; }
    .chat-row.assistant { justify-content: flex-start; }

    .user-message-box {
        background: rgba(0, 242, 254, 0.15);
        border: 1px solid rgba(0, 242, 254, 0.4);
        padding: 12px 18px;
        border-radius: 18px 18px 4px 18px;
        max-width: 75%;
        color: #e2e8f0;
        font-family: 'Segoe UI', sans-serif;
    }

    .ai-message-box {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 14px 18px;
        border-radius: 18px 18px 18px 4px;
        max-width: 85%;
        color: #f1f5f9;
        font-family: 'Segoe UI', sans-serif;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATE ---
if "guest_plan" not in st.session_state:
  st.session_state.guest_plan = "Flash"

if "show_aliai" not in st.session_state:
  st.session_state.show_aliai = False

if "trigger_prompt" not in st.session_state:
  st.session_state.trigger_prompt = None

if "ai_temp" not in st.session_state:
  st.session_state.ai_temp = 0.7

if "chats" not in st.session_state:
  st.session_state.chats = {}

if "current_chat_id" not in st.session_state:
  st.session_state.current_chat_id = None

if "user_info" not in st.session_state:
  st.session_state.user_info = None

if "ai_persona" not in st.session_state:
  st.session_state.ai_persona = "Standart AliGo"

if not st.session_state.chats:
  first_id = str(uuid.uuid4())[:8]
  st.session_state.chats[first_id] = {"title": "Yeni Söhbət", "messages": []}
  st.session_state.current_chat_id = first_id

# --- SUPABASE QEYD FUNKSİYALARI ---


def save_user_to_db(name, email):
  if not supabase:
    return
  try:
    clean_email = email or f"{name.lower().replace(' ', '')}@user.com"
    res = (
        supabase.table("users_log")
        .select("email")
        .eq("email", clean_email)
        .execute()
    )
    if not res.data:
      supabase.table("users_log").insert({
          "name": name,
          "email": clean_email,
          "user_code": f"USR-{str(uuid.uuid4())[:8].upper()}",
      }).execute()
    st.session_state["logged_to_db"] = True
  except Exception:
    pass


def save_feedback_to_db(user_name, feedback_type, message_text):
  if not supabase:
    return
  try:
    supabase.table("likes_log").insert({
        "user_name": user_name,
        "feedback_type": feedback_type,
        "message": message_text[:200],
    }).execute()
  except Exception as e:
    st.error(f"Xəta: {e}")


# --- İSTİFADƏÇİ MƏLUMATLARININ TƏYİNİ ---
user_name = None
user_email = None

try:
  if hasattr(st, "experimental_user") and st.experimental_user.get(
      "is_logged_in", False
  ):
    user_name = st.experimental_user.get("name") or st.experimental_user.get(
        "email"
    ).split("@")[0]
    user_email = st.experimental_user.get("email")
  elif hasattr(st, "user") and st.user.is_logged_in:
    user_name = st.user.name or st.user.email.split("@")[0]
    user_email = st.user.email
except Exception:
  pass

if not user_name and st.session_state.get("user_info"):
  user_name = st.session_state.user_info.get("name")
  user_email = st.session_state.user_info.get("email")

if not user_name:
  if "auto_guest_id" not in st.session_state:
    st.session_state.auto_guest_id = f"Qonaq_{str(uuid.uuid4())[:5]}"
  user_name = st.session_state.auto_guest_id
  user_email = f"{user_name.lower()}@aligo.app"

if "logged_to_db" not in st.session_state:
  save_user_to_db(user_name, user_email)

# --- KÖMƏKÇİ PROQRAM ---


def show_small_spinner(text="AliGo cavab yazır..."):
  st.markdown(
      f"""
        <div class="small-spinning-container">
            <div class="small-spinning-logo">
                <span style="color: #00f2fe;">A</span><span style="color: #4facfe;">l</span><span style="color: #a855f7;">i</span><span style="color: #22c55e;">G</span><span style="color: #f43f5e;">o</span>
            </div>
            <div class="loading-text-small">{text}</div>
        </div>
    """,
      unsafe_allow_html=True,
  )


# --- ŞƏKİL YARATMA FUNKSİYASI (Pollinations AI) ---
def generate_image_url(prompt_text):
  encoded_prompt = urllib.parse.quote(prompt_text)
  return (
      f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed={uuid.uuid4().int % 10000}"
  )


# --- SOL PANEL ---
st.sidebar.markdown("### 🔐 Profil")

is_google_logged = False
try:
  if (
      hasattr(st, "experimental_user")
      and st.experimental_user.get("is_logged_in", False)
  ) or (hasattr(st, "user") and st.user.is_logged_in):
    is_google_logged = True
except:
  pass

if user_name and not user_name.startswith("Qonaq_"):
  st.sidebar.success(f"👤 {user_name}")
  if user_email:
    st.sidebar.caption(f"📧 {user_email}")

  if is_google_logged:
    if st.sidebar.button("🚪 Google-dan Çıxış", use_container_width=True):
      if hasattr(st, "logout"):
        try:
          st.logout()
        except:
          pass
      st.rerun()
  else:
    if st.sidebar.button("🚪 Çıxış Et", use_container_width=True):
      st.session_state.user_info = None
      if "logged_to_db" in st.session_state:
        del st.session_state["logged_to_db"]
      st.rerun()
else:
  if st.sidebar.button("🔵 Google ilə Giriş Et", use_container_width=True):
    if hasattr(st, "login"):
      try:
        st.login("google")
      except Exception as e:
        st.sidebar.error(f"Giriş xətası: {e}")

  with st.sidebar.expander("👤 Ad yazaraq daxil ol"):
    input_name = st.text_input("Adınız:")
    input_email = st.text_input("Email (istəyə bağlı):")
    if st.button("Daxil ol"):
      if input_name:
        st.session_state.user_info = {
            "name": input_name,
            "email": input_email
            or f"{input_name.lower().replace(' ', '')}@user.com",
        }
        save_user_to_db(input_name, input_email)
        st.rerun()

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
    is_active = cid == st.session_state.current_chat_id
    btn_label = f"📍 {cdata['title']}" if is_active else cdata["title"]
    if st.button(btn_label, key=f"chat_{cid}", use_container_width=True):
      st.session_state.current_chat_id = cid
      st.session_state.show_aliai = True
      st.rerun()
  with col_b:
    if st.sidebar.button("🗑️", key=f"del_{cid}"):
      del st.session_state.chats[cid]
      if st.session_state.current_chat_id == cid:
        if st.session_state.chats:
          st.session_state.current_chat_id = list(
              st.session_state.chats.keys()
          )[0]
        else:
          new_id = str(uuid.uuid4())[:8]
          st.session_state.chats[new_id] = {
              "title": "Yeni Söhbət",
              "messages": [],
          }
          st.session_state.current_chat_id = new_id
      st.rerun()

current_chat_data = st.session_state.chats.get(
    st.session_state.current_chat_id, {"title": "Yeni Söhbət", "messages": []}
)
if current_chat_data["messages"]:
  chat_export_text = ""
  for m in current_chat_data["messages"]:
    role_name = "Sən" if m["role"] == "user" else "AliGo"
    txt_content = (
        m["content"]
        if isinstance(m["content"], str)
        else "[Şəkil və ya Fayl məzmunu]"
    )
    chat_export_text += f"{role_name}: {txt_content}\n\n"

  st.sidebar.download_button(
      label="📥 Söhbəti TXT olaraq yüklə",
      data=chat_export_text,
      file_name=f"{current_chat_data['title']}.txt",
      mime="text/plain",
      use_container_width=True,
  )

with st.sidebar.expander("⚙️ Tənzimləmələr"):
  st.session_state.ai_temp = st.slider(
      "AI Yaradıcılıq", 0.0, 1.0, st.session_state.ai_temp, 0.1
  )
  st.session_state.ai_persona = st.selectbox(
      "AI Xarakteri (Persona):",
      [
          "Standart AliGo",
          "Python / Kod Mütəxəssisi",
          "Oyun Dizayneri (Minecraft/Roblox)",
          "Dost / Səmimi Məsləhətçi",
      ],
  )

# --- ƏSAS EKRAN ---
col_top1, col_top2 = st.columns([3, 1])

with col_top1:
  st.markdown(
      "<h4 style='color: #00f2fe; margin-top: 5px;'>AliGo İntellektual"
      " Mərkəzi</h4>",
      unsafe_allow_html=True,
  )

with col_top2:
  if user_name and not user_name.startswith("Qonaq_"):
    st.markdown(
        f"""
            <div style="background: rgba(0, 242, 254, 0.15); border: 1px solid #00f2fe; padding: 6px 12px; border-radius: 12px; text-align: center; color: #fff; font-weight: bold; font-size: 0.95rem;">
                👤 {user_name}
            </div>
        """,
        unsafe_allow_html=True,
    )
  else:
    if st.button("🤖 AliAI"):
      st.session_state.show_aliai = not st.session_state.show_aliai
      st.rerun()

st.markdown(
    """
    <div class="aligo-logo">AliGo</div>
    <p style="text-align: center; color: #94a3b8; font-size: 1.1rem; margin-bottom: 10px;">Süni İntellekt və Axtarış Mərkəzi</p>
""",
    unsafe_allow_html=True,
)

# --- REJİMLƏR (MODLAR) ---
active_plan = st.session_state.guest_plan

cols_mode = st.columns(3)
with cols_mode[0]:
  if st.button(
      "⚡ Flash (Sürətli)",
      use_container_width=True,
      type="primary" if active_plan == "Flash" else "secondary",
  ):
    st.session_state.guest_plan = "Flash"
    st.rerun()
with cols_mode[1]:
  if st.button(
      "🚀 Pro (Balanslı)",
      use_container_width=True,
      type="primary" if active_plan == "Pro" else "secondary",
  ):
    st.session_state.guest_plan = "Pro"
    st.rerun()
with cols_mode[2]:
  if st.button(
      "👑 UltiPremium (Ekspert)",
      use_container_width=True,
      type="primary" if active_plan == "UltiPremium" else "secondary",
  ):
    st.session_state.guest_plan = "UltiPremium"
    st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# --- GROQ SORĞUSU ---


def ask_groq(messages_history, user_plan="Flash", mode="chat"):
  start_time = time.time()
  client = get_groq_client()

  # Əgər istifadəçi şəkil çəkməyimizi istəyirsə
  last_msg = messages_history[-1]["content"] if messages_history else ""
  if isinstance(last_msg, str) and (
      "şəkil çək" in last_msg.lower()
      or "şəkil yarat" in last_msg.lower()
      or "şəklini çək" in last_msg.lower()
      or "draw" in last_msg.lower()
      or "generate image" in last_msg.lower()
  ):
    img_url = generate_image_url(last_msg)
    return f"Buyurun, istədiyiniz şəkil yaradıldı:\n\n![Yaradılmış Şəkil]({img_url})"

  base_identity = (
      "ÇOX VACİB QAYDA: Sən heç vaxt ChatGPT, OpenAI, Google, Gemini və ya başqa"
      " bir süni intellekt modeli olduğunu deməyəcəksən. Sənin adın AliGo-dur!"
      " Sən AliGo Süni İntellekt və Axtarış Mərkəzisən. Kimliyini soruşsalar,"
      " qürurla AliGo olduğunu bildir.\n\n"
  )

  persona_text = ""
  if st.session_state.ai_persona == "Python / Kod Mütəxəssisi":
    persona_text = (
        "Xüsusi xarakter: Sən peşəkar Python və proqramlaşdırma mütəxəssisisən."
        " Kodları həmişə səliqəli, izahatlı və səhvsiz yaz.\n"
    )
  elif st.session_state.ai_persona == "Oyun Dizayneri (Minecraft/Roblox)":
    persona_text = (
        "Xüsusi xarakter: Sən oyun yaradıcısı, Roblox Studio (Lua) və Minecraft"
        " mütəxəssisisən. Oyunlar üçün kodlar və məsləhətlər ver.\n"
    )
  elif st.session_state.ai_persona == "Dost / Səmimi Məsləhətçi":
    persona_text = (
        "Xüsusi xarakter: İstifadəçi ilə dost kimi, səmimi, qardaşca və isti"
        " tonda danış.\n"
    )

  if mode == "search":
    system_content = base_identity + persona_text + (
        "Sən AliGo Axtarış Mərkəzisən. İstifadəçi səndən nəsə tapmağı, endirməyi"
        " və ya hər hansı fayl/proqram haqqında məlumat istəyir. Ona birbaşa"
        " rəsmi mənbələri, yükləmə yollarını, aydın və ətraflı şəkildə haradan"
        " əldə edə biləcəyini göstər."
    )
  else:
    if user_plan == "Flash":
      system_content = (
          base_identity
          + persona_text
          + "Sən Flash rejimində işləyən sürətli köməkçisən. Sualı normal,"
          " anlaşılan və kifayət qədər ətraflı izah et."
      )
    elif user_plan == "Pro":
      system_content = (
          base_identity
          + persona_text
          + "Sən Pro rejimində işləyən mütəxəssis mühəndis/analitiksen."
          " Strukturlu və ətraflı cavablar ver."
      )
    else:
      system_content = (
          base_identity
          + persona_text
          + "Sən UltiPremium səviyyəsində işləyən ekspert strateji"
          " müzakirəçisən. Dərin təhlil apar."
      )

  system_msg = {"role": "system", "content": system_content}

  max_tokens = (
      1200 if user_plan == "Flash" else (2500 if user_plan == "Pro" else 4000)
  )

  # Şəkil analizi olub-olmadığını yoxlayırıq
  has_image = False
  for m in messages_history:
    if isinstance(m.get("content"), list):
      for item in m["content"]:
        if isinstance(item, dict) and item.get("type") == "image_url":
          has_image = True

  if has_image:
    candidate_models = ["meta-llama/llama-3.2-11b-vision-preview"]
    full_messages = messages_history
  else:
    # Yenilənmiş işlək modellər siyahısı
    candidate_models = [
        "llama-3.3-70b-versatile",
        "llama3-8b-8192",
        "llama3-70b-8192",
    ]
    full_messages = [system_msg] + messages_history

  last_error = None
  for model_name in candidate_models:
    try:
      completion = client.chat.completions.create(
          model=model_name,
          messages=full_messages,
          temperature=st.session_state.ai_temp,
          max_tokens=max_tokens,
      )

      elapsed = time.time() - start_time
      if elapsed < 1.5:
        time.sleep(1.5 - elapsed)

      return completion.choices[0].message.content
    except Exception as e:
      last_error = e
      continue

  return f"⚠️ Groq API Xətası baş verdi: `{last_error}`"


# --- DÜYMƏLƏR VƏ ÇAT ---
col_q1, col_q2, col_q3, col_q4 = st.columns(4)
with col_q1:
  if st.button("❓ Sual Soruş", use_container_width=True):
    st.session_state.trigger_prompt = (
        "Mənə maraqlı bir mövzu haqqında məlumat ver."
    )
    st.session_state.show_aliai = True
    st.rerun()
with col_q2:
  if st.button("💻 Kod Yaz", use_container_width=True):
    st.session_state.trigger_prompt = (
        "Mənə bir proqramlaşdırma layihəsində kömək et, kod yazaq."
    )
    st.session_state.show_aliai = True
    st.rerun()
with col_q3:
  if st.button("📊 Plan Qur", use_container_width=True):
    st.session_state.trigger_prompt = (
        "Mənə məhsuldar bir plan qurmağımda kömək et."
    )
    st.session_state.show_aliai = True
    st.rerun()
with col_q4:
  if st.button("🎨 Şəkil Yarat", use_container_width=True):
    st.session_state.trigger_prompt = (
        "Mənə kosmosda uçan neon rəngli pişiyin şəklini çək."
    )
    st.session_state.show_aliai = True
    st.rerun()

if st.session_state.show_aliai:
  current_chat = st.session_state.chats.get(
      st.session_state.current_chat_id,
      {"title": "Yeni Söhbət", "messages": []},
  )

  new_chat_title = st.text_input(
      "Söhbətin Adı:", value=current_chat["title"], key="rename_chat_input"
  )
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
      show_small_spinner("AliGo düşünür...")

    history_for_api = [
        {"role": m["role"], "content": m["content"]}
        for m in current_chat["messages"]
    ]
    response = ask_groq(history_for_api, active_plan, mode="chat")

    placeholder.empty()
    current_chat["messages"].append({"role": "assistant", "content": response})
    st.rerun()

  for idx, message in enumerate(current_chat["messages"]):
    if message["role"] == "user":
      display_content = message["content"]
      if isinstance(display_content, list):
        text_part = next(
            (
                item["text"]
                for item in display_content
                if item.get("type") == "text"
            ),
            "Şəkil göndərildi",
        )
        display_content = f"📷 [Şəkil yükləndi] <br>{text_part}"

      st.markdown(
          f"""
                <div class="chat-row user">
                    <div class="user-message-box"><b>Sən:</b><br>{display_content}</div>
                </div>
            """,
          unsafe_allow_html=True,
      )
    else:
      st.markdown(
          """
                <div class="chat-row assistant">
                    <div class="ai-message-box">
            """,
          unsafe_allow_html=True,
      )
      st.markdown(message["content"])
      st.markdown(
          """
                    </div>
                </div>
            """,
          unsafe_allow_html=True,
      )

      c_like, c_dislike, c_space = st.columns([1, 1, 6])
      with c_like:
        if st.button("👍", key=f"like_{idx}"):
          save_feedback_to_db(user_name, "Bəyəndi 👍", str(message["content"]))
          st.toast("🎉 Rəyiniz üçün təşəkkürlər!", icon="👍")
      with c_dislike:
        if st.button("👎", key=f"dislike_{idx}"):
          save_feedback_to_db(
              user_name, "Bəyənmədi 👎", str(message["content"])
          )
          st.toast("⚠️ Qeyd olundu! Təşəkkürlər.", icon="🔧")

      st.markdown("---")

  uploaded_file = st.file_uploader(
      "Şəkil və ya fayl əlavə et",
      type=["png", "jpg", "jpeg", "txt", "py", "json"],
  )

  if prompt := st.chat_input("AliGo-dan soruş... (məs: 'şəkil çək: futuristic city')"):
    if uploaded_file is not None and uploaded_file.type in [
        "image/png",
        "image/jpeg",
        "image/jpg",
    ]:
      bytes_data = uploaded_file.getvalue()
      base64_image = base64.b64encode(bytes_data).decode("utf-8")

      content = [{
          "type": "image_url",
          "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
      }]
      content.append({"type": "text", "text": prompt})
      user_message_content = content
    else:
      full_prompt = prompt
      if uploaded_file is not None:
        full_prompt += f"\n[İstifadəçi bir fayl yüklədi: {uploaded_file.name}]"
      user_message_content = full_prompt

    current_chat["messages"].append(
        {"role": "user", "content": user_message_content}
    )
    if current_chat["title"] == "Yeni Söhbət":
      current_chat["title"] = prompt[:20] + "..."

    placeholder = st.empty()
    with placeholder.container():
      show_small_spinner("AliGo cavab axtarır...")

    history_for_api = [
        {"role": m["role"], "content": m["content"]}
        for m in current_chat["messages"]
    ]
    response = ask_groq(history_for_api, active_plan, mode="chat")

    placeholder.empty()
    current_chat["messages"].append({"role": "assistant", "content": response})
    st.rerun()

  if st.button("❌ Paneli Bağla"):
    st.session_state.show_aliai = False
    st.rerun()
else:
  search_query = st.text_input(
      "",
      placeholder=(
          "Axtarış Mərkəzi: Məsələn, 'CapCut PC indir' və ya 'Python öyrənmək"
          " üçün saytlar'..."
      ),
      key="main_search",
      label_visibility="collapsed",
  )
  if search_query:
    st.session_state.show_aliai = True
    current_chat = st.session_state.chats[st.session_state.current_chat_id]
    current_chat["messages"].append({"role": "user", "content": search_query})
    if current_chat["title"] == "Yeni Söhbət":
      current_chat["title"] = search_query[:20] + "..."

    placeholder = st.empty()
    with placeholder.container():
      show_small_spinner("AliGo axtarış edir...")

    history_for_api = [
        {"role": m["role"], "content": m["content"]}
        for m in current_chat["messages"]
    ]
    ai_resp = ask_groq(history_for_api, active_plan, mode="search")

    placeholder.empty()
    current_chat["messages"].append({"role": "assistant", "content": ai_resp})
    st.rerun()
