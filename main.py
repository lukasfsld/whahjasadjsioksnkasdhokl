import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nano Banana Campaign Director (V8)",
    page_icon="🍌",
    layout="wide"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FFD700; /* Banana Yellow */
        color: black;
        border-radius: 8px;
        padding: 16px;
        font-weight: 800;
        font-size: 18px;
        border: none;
        margin-top: 20px;
    }
    .stButton>button:hover {
        background-color: #E5C100;
        color: black;
    }
    h1, h2, h3 { font-family: 'Helvetica', sans-serif; }
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 10px; }
    
    div.block-container { padding-top: 2rem; }
    /* Wichtiger Hinweis Style */
    .stAlert { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Settings")
    if "OPENAI_API_KEY" in st.secrets:
        st.success("API Key aktiv (Secrets) ✅")
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("OpenAI API Key", type="password")
    
    st.info("Optimiert für **Nano Banana** (Gemini 2.5 Flash / 3 Pro Image).")
    st.markdown("---")
    st.caption("Nano Banana ist der Codename für Googles neueste Image-Modelle.")

# --- HEADER ---
st.title("🍌 Nano Banana Campaign Director")
st.markdown("Erstelle perfekte Prompts für **Nano Banana** (Google Gemini Image). Nutze die Stärken: **Text-Rendering**, **Referenz-Bilder** und **High-Speed Editing**.")
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


# --- 3. TECHNIK & CINEMATOGRAPHY ---
st.markdown("---")
st.subheader("3. Technik, Film-Look & Kamera")
t1, t2, t3, t4 = st.columns(4)

with t1:
    # Nano Banana ist super für Texturen
    cam_move = st.selectbox("Kamera-Bewegung (Falls Video)", 
                            ["Static Tripod (Best for Image)", "Slow Zoom In", "Handheld", "Drone Orbit"])

with t2:
    film_look = st.selectbox("Film Look (Color Grading)", 
                             ["Standard Commercial (Clean)", "Kodak Portra 400 (Warm/Vintage)", 
                              "Teal & Orange (Blockbuster)", "Black & White (Noir)", 
                              "Pastel/Dreamy (Soft)", "Moody/Desaturated (Dark)"])

with t3:
    framing = st.selectbox("Ausschnitt", ["Extreme Close-Up (Face)", "Portrait (Head & Shoulders)", "Medium Shot (Waist Up)", "Full Body"])

with t4:
    lens = st.selectbox("Objektiv", ["85mm (Portrait)", "100mm Macro (Details)", "35mm (Lifestyle)", "24mm (Wide)"])

# --- 4. SETTING, PRODUKT & REFERENZ ---
st.markdown("---")
st.subheader("4. Format, Produkt & Nano-Features")
k1, k2 = st.columns([1, 1])

with k1:
    product = st.text_input("Produkt / Thema", placeholder="z.B. Goldene Halskette mit Rubin")
    
    st.markdown("---")
    use_size = st.checkbox("Spezifische Größe (cm) angeben?", value=False)
    
    if use_size:
        st.caption("Größen-Einstellungen:")
        obj_type = st.radio("Art des Objekts", ["Kettenanhänger (Schmuck)", "Allgemeines Objekt"], horizontal=True)
        obj_size = st.slider(f"Größe in cm", 0.5, 5.0, 2.5, 0.1)
    else:
        obj_type = None
        obj_size = None
    
    st.markdown("---")
    # NANO BANANA SPECIFIC: REFERENCE IMAGES
    wear_product = st.checkbox("Referenz-Bild wird in Nano Banana hochgeladen?", value=False,
                               help="Nano Banana (Gemini) unterstützt bis zu 14 Referenzbilder für perfektes Style-Matching.")

with k2:
    st.markdown("**Bildformat:**")
    aspect_ratio = st.selectbox("Format wählen", 
                                ["Querformat (16:9)", "Hochformat (9:16)", "Quadrat (1:1)", "Cinematic (21:9)"])

    st.markdown("**Hintergrund & Wetter:**")
    weather = st.selectbox("Wetter / Atmosphäre", 
                           ["Clear/Sunny", "Cloudy/Soft", "Rainy/Wet Skin", "Foggy/Misty", "Snowing"])
    
    bg_mode = st.radio("Hintergrund-Modus", ["Szenisch", "Einfarbig"], horizontal=True, label_visibility="collapsed")
    
    if bg_mode == "Szenisch":
        bg_selection = st.selectbox("Hintergrund Szenario", 
                          ["Clean White Studio", "Dark Luxury Background", "Warm Beige Tone", 
                           "Blurred City Street", "Nature/Forest", "Blue Sky", "Abstract Gradient"])
        final_bg_instruction = f"{bg_selection} background"
    else:
        custom_color = st.color_picker("Wähle Farbe", "#FF0044")
        final_bg_instruction = f"Solid background with exact hex color code {custom_color}, minimal studio style"
    
    lighting = st.selectbox("Licht-Setzung", ["Soft Beauty Light", "Golden Hour", "Rembrandt", "Cinematic Contrast", "Neon"])

# --- GPT GENERATION FOR NANO BANANA ---
def generate_prompt():
    if not api_key:
        st.error("⚠️ API Key fehlt!")
        return None

    client = OpenAI(api_key=api_key)

    # FORMAT LOGIK (Nano Banana versteht Aspect Ratios in Natural Language gut)
    if "16:9" in aspect_ratio: ar_text = "Aspect Ratio: 16:9 (Wide)"
    elif "9:16" in aspect_ratio: ar_text = "Aspect Ratio: 9:16 (Vertical)"
    elif "21:9" in aspect_ratio: ar_text = "Aspect Ratio: 21:9 (Cinematic)"
    else: ar_text = "Aspect Ratio: 1:1 (Square)"

    # GRÖSSE
    size_instr = ""
    if use_size and obj_size:
        if obj_type == "Kettenanhänger (Schmuck)":
            size_instr = f"SCALE: The necklace pendant must be rendered exactly {obj_size}cm in height, appearing delicate."
        else:
            size_instr = f"SCALE: The product object is approximately {obj_size}cm in size relative to the model."

    # PRODUKT & REFERENZ (Nano Banana Stärke)
    if wear_product:
        prod_instr = (f"CRITICAL FOR NANO BANANA: The user is providing a REFERENCE IMAGE of the product '{product}'. "
                      f"Instructions: 'Use the uploaded reference image to perform precise in-context blending. "
                      f"The model should be wearing exactly this item.' Focus strictly on '{product}'. {size_instr}")
        ref_reminder = "✅ WICHTIG: Lade jetzt dein Produkt-Bild in Nano Banana (Gemini) hoch!"
    else:
        prod_instr = f"Campaign for '{product}'. Model is NOT wearing a specific reference item. Generate a high-quality representation based on description. {size_instr}"
        ref_reminder = ""

    outfit_instr = f"OUTFIT: Model is wearing {clothing}." if clothing else "OUTFIT: High-fashion minimal clothing."

    atmosphere_instr = f"ATMOSPHERE: {weather}. COLOR GRADE: {film_look}."

    # SYSTEM PROMPT FÜR NANO BANANA (GEMINI)
    system_prompt = """
    You are an expert Prompt Engineer for Google's 'Nano Banana' (Gemini 2.5 Flash / Gemini 3 Pro Image) model.
    
    NANO BANANA SPECIFICS:
    1. It excels at adhering to prompt complexity and text rendering.
    2. It supports multi-turn editing and reference images perfectly.
    3. Use keywords like "photorealistic", "8k", "highly detailed skin texture" (it's known for this).
    
    YOUR GOAL:
    Write a single, comprehensive paragraph prompt in English that triggers Nano Banana's best capabilities.
    Include "subsurface scattering" and "micropore texture" as requested.
    """

    user_prompt = f"""
    Write a Nano Banana prompt:
    
    SUBJECT: {gender}, {age}, {ethnicity}.
    LOOK: {hair_texture}, {hair_color}, {hair_style}, {wind}. {eye_color} eyes.
    SKIN: {freckles}, {makeup} makeup. (Ensure subsurface scattering & micropore texture).
    
    POSE: {pose}, {gaze}, {expression}.
    
    PRODUCT CONTEXT: {prod_instr}
    
    SCENE: {final_bg_instruction}. {lighting}. {atmosphere_instr}.
    CAMERA: {framing}, {lens}. {cam_move}.
    FORMAT: {ar_text}.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content, ref_reminder
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None

# --- OUTPUT ---
if st.button("NANO BANANA PROMPT GENERIEREN 🍌"):
    if not product:
        st.warning("Bitte gib ein Produkt ein!")
    else:
        with st.spinner("Optimiere für Gemini 2.5 / Nano Banana..."):
            prompt_res, reminder = generate_prompt()
            if prompt_res:
                st.success("🍌 Nano Banana Prompt fertig!")
                if reminder:
                    st.info(reminder)
                st.code(prompt_res, language="text")
                st.caption("Kopiere diesen Text in Google Gemini / Nano Banana Interface.")
