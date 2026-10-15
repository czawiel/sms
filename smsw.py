# v1.20
import streamlit as st
import requests
import re
import os
import base64

st.set_page_config(page_title="Pomysł na SMS bramka", page_icon="📱", layout="centered")

# --- STYLIZACJA CSS INTERFEJSU ---
st.markdown("""
<style>
    /* Zmniejszenie górnego marginesu strony */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 720px;
    }
    
    /* Nagłówek aplikacji i plakietka wersji */
    .app-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.2rem;
    }
    .app-title {
        font-size: 2.1rem;
        font-weight: 800;
        margin: 0;
        background: linear-gradient(90deg, #1E88E5, #5E35B1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .version-badge {
        background-color: rgba(128, 128, 128, 0.12);
        color: #777;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .app-subtitle {
        color: #6c757d;
        font-size: 0.95rem;
        margin-bottom: 1.8rem;
    }

    /* Wizualne ulepszenie kontenerów z obramowaniem (karty) */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.03);
        padding: 1.2rem !important;
        transition: box-shadow 0.2s ease-in-out;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.06);
    }

    /* Tytuły sekcji wewnątrz kart */
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Zaokrąglenie przycisków i pól tekstowych */
    .stButton > button {
        border-radius: 10px;
        font-weight: 600;
        padding: 0.55rem 1rem;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        border-radius: 10px;
    }

    /* Pasek licznika znaków */
    .char-counter-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.82rem;
        color: #6c757d;
        background: rgba(128, 128, 128, 0.06);
        padding: 6px 12px;
        border-radius: 8px;
        margin-top: -4px;
        margin-bottom: 12px;
    }
    .char-badge {
        font-weight: 700;
        color: #1E88E5;
    }
</style>
""", unsafe_allow_html=True)

# --- NAGŁÓWEK GŁÓWNY ---
st.markdown("""
<div class="app-header">
    <h1 class="app-title">📱 Pomysł na SMS bramka</h1>
    <span class="version-badge">v1.20</span>
</div>
<div class="app-subtitle">Wysyłka wiadomości SMS przez Twój telefon z Androidem na dowolny numer</div>
""", unsafe_allow_html=True)

# Pobieranie danych uwierzytelniających ze Streamlit Secrets
try:
    API_KEY = st.secrets["textbee"]["api_key"]
    DEVICE_ID = st.secrets["textbee"]["device_id"]
    DEEPSEEK_API_KEY = st.secrets["deepseek"]["api_key"]
except Exception as e:
    st.error("Błąd konfiguracji: Brak wymaganych sekretów w pliku secrets.toml. Skonfiguruj sekrety w panelu Streamlit Cloud lub lokalnie.")
    st.stop()

# Inicjalizacja stanu dla treści wiadomości
if "sms_textarea" not in st.session_state:
    st.session_state["sms_textarea"] = ""

# --- PANEL BOCZNY ---
with st.sidebar:
    svg_filename = "logo3.svg"
    if os.path.exists(svg_filename):
        with open(svg_filename, "r", encoding="utf-8") as f:
            svg_content = f.read()
        encoded_svg = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
        st.markdown(
            f'''
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <a href="https://fabryka.tech" target="_blank" rel="noopener noreferrer">
                    <img src="data:image/svg+xml;base64,{encoded_svg}" style="max-width: 85%; height: auto; cursor: pointer;" alt="Fabryka.tech Logo" />
                </a>
            </div>
            ''',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="text-align: center; padding: 10px 0 20px 0;"><a href="https://fabryka.tech" target="_blank" style="font-weight: 800; text-decoration: none; font-size: 1.3rem; color: #1E88E5;">fabryka.tech</a></div>',
            unsafe_allow_html=True
        )

    st.divider()
    st.markdown("### ⚙️ Status urządzenia")
    
    with st.container(border=True):
        st.success(f"**Połączono**\n\nID: `{DEVICE_ID[:8]}...`", icon="🟢")
        st.caption("Upewnij się, że telefon ma włączony internet (Wi-Fi lub dane) i aplikacja działa w tle.")

    st.divider()
    st.link_button("📩 Formularz kontaktowy", "https://fabryka.tech/kontakt", use_container_width=True)

# --- SEKCJA 1: GENERATOR AI (KARTA) ---
with st.container(border=True):
    st.markdown('<div class="section-title">💡 Pomysł na SMS (Asystent AI)</div>', unsafe_allow_html=True)
    
    ai_prompt = st.text_input(
        "O czym ma być wiadomość?",
        placeholder="np. zapytaj czy weźmie myszkę, informacja o spóźnieniu 10 min, przypomnienie..."
    )

    col_ai1, col_ai2 = st.columns([3, 2], vertical_alignment="bottom")
    with col_ai1:
        char_limit = st.selectbox(
            "Maksymalny limit znaków:",
            options=[70, 160, 300],
            index=0,
            format_func=lambda x: f"{x} znaków ({'krótki SMS' if x==70 else 'długi SMS' if x==160 else 'dłuższy SMS'})"
        )

    with col_ai2:
        no_accents = st.checkbox(
            "Bez polskich znaków (ą -> a)", 
            value=True, 
            help="Pozwala zmieścić pełną treść w standardowym limicie kodowania GSM."
        )

    st.write("") # Drobny odstęp wizualny
    generate_button = st.button("✨ Wygeneruj treść przez AI", use_container_width=True, type="secondary")

    if generate_button:
        if not ai_prompt.strip():
            st.warning("Wpisz najpierw temat lub intencję wiadomości.", icon="⚠️")
        else:
            with st.status("🤖 Trwa generowanie treści przez AI...", expanded=True) as status:
                prompt_instruction = (
                    f"Napisz krótką, naturalną i bezpośrednią wiadomość SMS od użytkownika do innej osoby na temat: '{ai_prompt}'. "
                    f"Wiadomość ma być zwykłym SMS-em (np. pytaniem, informacją lub przypomnieniem), a NIE ogłoszeniem handlowym, reklamą, ofertą sprzedaży ani komunikatem z ceną czy miejscem odbioru. "
                    f"Całość wiadomości MUSI mieć BEZWZGLĘDNIE MAKSYMALNIE {char_limit} ZNAKÓW. "
                    f"Nie dodawaj żadnych cudzysłowów, wyjaśnień ani nagłówków – zwróć wyłącznie gotowy tekst SMS-a."
                )
                
                deepseek_url = "https://api.deepseek.com/chat/completions"
                headers = {
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                }
                
                candidate_models = ["deepseek-chat", "deepseek-coder"]
                generated_text = None
                last_err = ""

                for model_name in candidate_models:
                    status.update(label=f"Próbuję model DeepSeek: {model_name}...")
                    payload = {
                        "model": model_name,
                        "messages": [
                            {"role": "system", "content": "Jesteś pomocnym asystentem piszącym naturalne, codzienne wiadomości SMS."},
                            {"role": "user", "content": prompt_instruction}
                        ],
                        "stream": False
                    }
                    
                    try:
                        res = requests.post(deepseek_url, json=payload, headers=headers, timeout=30)
                        data = res.json()
                        if res.status_code == 200 and "choices" in data and len(data["choices"]) > 0:
                            generated_text = data["choices"][0]["message"]["content"].strip()
                            break
                        else:
                            last_err = data.get("error", {}).get("message", res.text)
                    except Exception as e:
                        last_err = str(e)

                if generated_text:
                    if no_accents:
                        replacements = {
                            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
                            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
                            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
                            'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
                        }
                        for k, v in replacements.items():
                            generated_text = generated_text.replace(k, v)

                    generated_text = generated_text[:char_limit]
                    st.session_state["sms_textarea"] = generated_text
                    status.update(label="✅ Wygenerowano pomyślnie przez AI!", state="complete", expanded=False)
                    st.rerun()
                else:
                    status.update(label="❌ Błąd generowania", state="error", expanded=True)
                    st.error(f"Nie udało się wygenerować tekstu przez DeepSeek. Ostatni błąd: {last_err}")

st.write("") # Odstęp między kartami

# --- SEKCJA 2: FORMULARZ WYSYŁANIA (KARTA) ---
with st.container(border=True):
    st.markdown('<div class="section-title">✉️ Parametry i wysyłka wiadomości</div>', unsafe_allow_html=True)
    
    recipient = st.text_input(
        "Numer telefonu odbiorcy", 
        placeholder="np. 500123456 lub +48500123456",
        help="Możesz wpisać dowolny numer telefonu."
    )

    message = st.text_area(
        "Treść wiadomości SMS", 
        placeholder="Wpisz treść wiadomości lub wygeneruj powyżej za pomocą AI...",
        max_chars=600,
        height=130,
        key="sms_textarea"
    )

    char_count = len(message)
    st.markdown(f"""
    <div class="char-counter-bar">
        <span>Progi: krótki SMS (70 zn.) • długi SMS (160 zn.)</span>
        <span>Liczba znaków: <span class="char-badge">{char_count} / 600</span></span>
    </div>
    """, unsafe_allow_html=True)

    send_button = st.button("📤 Wyślij SMS teraz", use_container_width=True, type="primary")

    # --- OBSŁUGA WYSYŁANIA ---
    if send_button:
        if not recipient.strip():
            st.error("Podaj numer telefonu odbiorcy.", icon="📵")
        elif not message.strip():
            st.error("Wpisz treść wiadomości.", icon="📝")
        else:
            clean_nr = re.sub(r'[^0-9]', '', recipient)
            if len(clean_nr) == 9:
                clean_nr = "+48" + clean_nr
            else:
                clean_nr = "+" + clean_nr

            api_url = f"https://api.textbee.dev/api/v1/gateway/devices/{DEVICE_ID}/send-sms"
            headers = {
                "x-api-key": API_KEY,
                "Content-Type": "application/json"
            }
            payload = {
                "recipients": [clean_nr],
                "message": message
            }

            try:
                with st.spinner("Przesyłanie zlecenia do Twojego telefonu..."):
                    response = requests.post(api_url, json=payload, headers=headers, timeout=15)
                    
                if response.status_code in (200, 201):
                    st.success(f"Sukces! Telefon wysyła wiadomość na numer `{clean_nr}`.", icon="🚀")
                else:
                    st.error(f"Błąd bramki (kod {response.status_code}): {response.text}", icon="❌")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Błąd połączenia z serwerem Textbee: {e}", icon="🔌")
