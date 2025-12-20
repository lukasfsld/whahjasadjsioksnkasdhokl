import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Veo Campaign Director Ultimate V5",
    page_icon="🎬",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: white;
        border-radius: 8px;
        padding: 16px;
        font-weight: 700;
        font-size: 18px;
        border: none;
        margin-top: 20px;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    h1, h2, h3 { font-family: 'Helvetica', sans-serif; }
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 10px; }
    
    /* Boxen visuell etwas trennen */
    div.block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)


    else:
        api_key = st.text_input("OpenAI API Key", type="password")
    st.info("Optimiert für Google Veo & Midjourney v6.")

# --- HEADER ---
st.title("🎬 Veo Campaign Director Ultimate (V5)")
st.markdown("Profi-Tool für **High-End Werbekampagnen**. Volle Kontrolle über **Format (Aspect Ratio)**, Größe, Styling und Produkt.")
st.divider()

# --- 1. MODEL LOOK ---
st.subheader("1. Model Details")
col1, col2, col3, col4 = st.columns(4)

with col1:
    gender = st.selectbox("Geschlecht", ["Female Model", "Male Model", "Non-binary Model"])
    age = st.select_slider("Alter", options=["18-24", "25-34", "35-44", "45-55", "60+"], value="25-34")

with col2:
    ethnicity = st.text_input("Ethnie / Look", value="olive skin tone", placeholder="z.B. Scandinavian")
    hair_color = st.text_input("Haarfarbe", value="dark brown")

with col3:
    hair_texture = st.select_slider("Haarstruktur", options=["Straight (Glatt)", "Wavy (Wellig)", "Curly (Lockig)", "Coily (Afro)"], value="Wavy (Wellig)")
    hair_style = st.selectbox("Frisur-Stil", ["Loose & Open", "Sleek Ponytail", "Messy Bun", "Short Cut", "Bob Cut"])

with col4:
    eye_color = st.text_input("Augenfarbe", value="green")
    freckles = st.radio("Haut-Details", ["Klare Haut", "Sommersprossen"], horizontal=True)

# --- 2. KLEIDUNG & POSE ---
st.markdown("---")
st.subheader("2. Kleidung, Pose & Make-up")
c_outfit, c_pose = st.columns([1, 2])

with c_outfit:
    clothing = st.text_area("Was trägt das Model? (Outfit)", 
                            placeholder="z.B. Weißes Seidenkleid, Schwarzer Rollkragenpullover...",
                            height=100)
    makeup = st.select_slider("Make-up", options=["No Makeup", "Natural/Clean", "Soft Glam", "High Fashion"])

with c_pose:
    p1, p2, p3 = st.columns(3)
    with p1:
        pose = st.selectbox("Körperhaltung", 
                            ["Standing Upright (Power Pose)", "Relaxed Leaning", "Walking towards Camera", 
                             "Sitting Elegantly", "Dynamic Action", "Over the Shoulder"])
    with p2:
        gaze = st.selectbox("Blickrichtung", 
                            ["Straight into Camera (Eye Contact)", "Looking away (Dreamy)", 
                             "Looking down", "Looking up"])
    with p3:
        expression = st.selectbox("Gesichtsausdruck", 
                                  ["Neutral & Cool", "Confident Smile", "Laughing", "Fierce/Intense", "Seductive"])
    
    wind = st.select_slider("Haar-Dynamik (Wind)", options=["Static", "Soft Breeze", "Strong Wind"], value="Soft Breeze")


# --- 3. TECHNIK & SETTING ---
st.markdown("---")
st.subheader("3. Technik, Haut & Licht")
t1, t2, t3, t4 = st.columns(4)

with t1:
    skin_finish = st.selectbox("Haut-Finish", ["Natural Matte", "Dewy & Glowy", "Sweaty/Athletic", "Glass Skin"])

with t2:
    lighting = st.selectbox("Licht-Setzung", ["Soft Beauty Light", "Golden Hour (Sun)", "Rembrandt (Moody)", "Cinematic Contrast", "Neon"])

with t3:
    framing = st.selectbox("Ausschnitt", ["Extreme Close-Up (Face)", "Portrait (Head & Shoulders)", "Medium Shot (Waist Up)", "Full Body"])

with t4:
    lens = st.selectbox("Objektiv", ["85mm (Portrait)", "100mm Macro (Details)", "35mm (Lifestyle)", "24mm (Wide)"])

# --- 4. KAMPAGNE & FORMAT (NEU: FORMAT) ---
st.markdown("---")
st.subheader("4. Format, Produkt & Hintergrund")
k1, k2 = st.columns([1, 1])

with k1:
    product = st.text_input("Produkt / Thema", placeholder="z.B. Goldene Halskette mit Rubin")
    
    # GRÖSSEN-FUNKTION
    st.markdown("**Objekt-Größe (Scale):**")
    obj_type = st.radio("Art des Objekts", ["Kettenanhänger (Schmuck)", "Allgemeines Objekt"], horizontal=True)
    obj_size = st.slider(f"Größe in cm", 0.5, 5.0, 2.5, 0.1)
    
    wear_product = st.checkbox("Referenz-Bild wird in Veo hochgeladen?", value=False,
                               help="Wenn an: Prompt befiehlt Veo, das Referenzbild zu nutzen.")

with k2:
    # NEU: FORMAT AUSWAHL
    st.markdown("**Bildformat (Aspect Ratio):**")
    aspect_ratio = st.selectbox("Format wählen", 
                                ["Querformat (16:9) - TV/Kino", 
                                 "Hochformat (9:16) - Social Media/Reels", 
                                 "Quadrat (1:1) - Instagram Post", 
                                 "Cinematic Wide (21:9) - Breitbild Film"])

    st.markdown("**Hintergrund:**")
    bg_mode = st.radio("Hintergrund-Modus", ["Szenisch (Vorgefertigt)", "Einfarbig (Color Code)"], horizontal=True)
    
    if bg_mode == "Szenisch (Vorgefertigt)":
        bg_selection = st.selectbox("Hintergrund Szenario", 
                          ["Clean White Studio", "Dark Luxury Background", "Warm Beige Tone", 
                           "Blurred City Street", "Nature/Forest", "Blue Sky", "Abstract Gradient"])
        final_bg_instruction = f"{bg_selection} background"
    else:
        custom_color = st.color_picker("Wähle Farbe", "#FF0044")
        final_bg_instruction = f"Solid background with exact hex color code {custom_color}, minimal studio style"

# --- GPT GENERATION ---
def generate_prompt():
    if not api_key:
        st.error("⚠️ API Key fehlt!")
        return None

    client = OpenAI(api_key=api_key)

    # FORMAT LOGIK
    if "16:9" in aspect_ratio:
        ar_code = "--ar 16:9"
        ar_text = "Wide Landscape Aspect Ratio (16:9)"
    elif "9:16" in aspect_ratio:
        ar_code = "--ar 9:16"
        ar_text = "Vertical Portrait Aspect Ratio (9:16)"
    elif "21:9" in aspect_ratio:
        ar_code = "--ar 21:9"
        ar_text = "Ultra-Wide Cinematic Aspect Ratio (21:9)"
    else:
        ar_code = "--ar 1:1"
        ar_text = "Square Aspect Ratio (1:1)"

    # GRÖSSEN LOGIK
    if obj_type == "Kettenanhänger (Schmuck)":
  
