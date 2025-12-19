import streamlit as st
from openai import OpenAI
import json

# --- 1. SETUP ---
st.set_page_config(page_title="GiftGenius", page_icon="🎁", layout="wide")

# --- 2. CSS DESIGN (Modern & Clean) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    
    .gradient-text {
        background: -webkit-linear-gradient(45deg, #FF512F, #DD2476);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 600; font-size: 3rem; text-align: center; margin-bottom: 0;
    }
    .subtitle { text-align: center; color: #666; font-size: 1.1rem; margin-bottom: 3rem; }
    
    /* Karten-Design für 3 Spalten */
    .gift-card {
        background: white; 
        border-radius: 20px; 
        padding: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08); 
        transition: all 0.3s ease;
        border: 1px solid rgba(0,0,0,0.05); 
        height: 100%;
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
    }
    
    .gift-card:hover { 
        transform: translateY(-8px); 
        box-shadow: 0 20px 40px rgba(0,0,0,0.12); 
        border-color: #DD2476; 
    }
    
    .card-title { color: #2D3436; font-size: 1.2rem; font-weight: 600; margin-bottom: 10px; }
    .card-desc { color: #636e72; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px; }
    
    /* Der Kaufen-Button */
    .buy-btn {
        display: block; 
        background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
        color: white !important; 
        text-align: center; 
        padding: 12px; 
        border-radius: 12px;
        text-decoration: none; 
        font-weight: 500; 
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
        transition: box-shadow 0.3s;
    }
    .buy-btn:hover { 
        box-shadow: 0 6px 20px rgba(17, 153, 142, 0.5); 
        opacity: 0.95; 
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SEITENLEISTE (Inputs) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4213/4213958.png", width=70)
    st.markdown("### Einstellungen")
    
    # Key automatisch laden
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
        st.success("Bereit ✅", icon="🚀")
    else:
        st.error("API Key fehlt in Secrets!")
        st.stop()
    
    st.markdown("---")
    
    relation = st.selectbox("Für wen?", ["Partner/in", "Eltern", "Bester Freund/in", "Kind", "Kollege", "Nachbar"])
    age = st.slider("Alter", 1, 99, 28)
    budget = st.select_slider("Budget", options=["Kleinigkeit", "20-50€", "50-100€", "Luxus (>100€)"])
    interests = st.text_area("Hobbys & Vorlieben", height=120, placeholder="z.B. Mag Kaffee, Star Wars und Camping...")
    
    st.markdown("---")
    start_search = st.button("✨ 3 Ideen finden", use_container_width=True, type="primary")


# --- 4. HAUPTBEREICH ---
st.markdown('<div class="gradient-text">GiftGenius AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Finde 3 präzise Vorschläge in Sekunden.</div>', unsafe_allow_html=True)

if start_search and interests:
    client = OpenAI(api_key=api_key)
    
    with st.spinner('🔍 Die KI sucht nach konkreten Markenprodukten...'):
        try:
            # DER TRICK: Wir zwingen die KI zu "Specific Model Names"
            prompt = f"""
            Rolle: Shopping-Experte.
            Zielperson: {relation}, {age} Jahre.
            Budget: {budget}.
            Interessen: {interests}.
            
            Aufgabe: Finde 3 KONKRETE Markenprodukte.
            REGEL: Du darfst NICHT generisch sein (z.B. nicht "Eine Kaffeemaschine", sondern "De'Longhi Dedica EC685").
            Das Ziel ist, dass der Suchbegriff bei Amazon genau dieses eine Produkt oben anzeigt.
            
            Format JSON: 
            {{ "items": [ 
                {{ 
                    "title": "Exakter Produktname", 
                    "text": "Kurze Begründung (max 2 Sätze)", 
                    "search": "Marke + Modellnummer" 
                }} 
            ] }}
            """
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            data = json.loads(response.choices[0].message.content.replace("```json", "").replace("```", ""))
            
            st.markdown("<br>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            cols = [col1, col2, col3]

            for i, item in enumerate(data["items"]):
                # Link bauen (ohne Affiliate Tag, rein organisch)
                search_query = item['search'].replace(' ', '+')
                amazon_url = f"https://www.amazon.de/s?k={search_query}"
                
                with cols[i]:
                    st.markdown(f"""
                    <div class="gift-card">
                        <div>
                            <div class="card-title">{item['title']}</div>
                            <div class="card-desc">{item['text']}</div>
                        </div>
                        <a href="{amazon_url}" target="_blank" class="buy-btn">
                            Auf Amazon ansehen ➔
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Fehler: {e}")

elif start_search:
    st.warning("Gib bitte ein paar Interessen ein.")