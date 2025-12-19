import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Veo Campaign Director Ultimate V2",
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
    
    /* Hervorhebung für die wichtige Checkbox */
    div[data-testid="stCheckbox"] label span {
        font-weight: bold;
        color: #0068c9;
    }
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
    st.info("Optimiert für Google Veo & Midjourney v6.")

# --- HEADER ---
st.title("🎬 Veo Campaign Director Ultimate (V2)")
st.markdown("Profi-Tool für **High-End Werbekampagnen**. Volle Kontrolle über Haut, Licht, **Outfit** und Produkt-Fokus.")
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
    hair_style = st.selectbox("Frisur", ["Loose & Natural", "Sleek Ponytail", "Wet Look", "Messy Bun", "Short Buzz Cut", "Bob Cut"])
    eye_color = st.text_input("Augenfarbe", value="green")

with col4:
    freckles = st.radio("Haut-Details", ["Klare Haut", "Sommersprossen"], horizontal=True)
    makeup = st.select_slider("Make-up", options=["No Makeup", "Natural/Clean", "Soft Glam", "High Fashion"])

# --- NEU: KLEIDUNG (OUTFIT) ---
st.markdown("---")
st.subheader("2. Kleidung & Styling")
c_outfit, c_pose = st.columns([1, 2])

with c_outfit:
    # NEUES FELD FÜR KLEIDUNG
    clothing = st.text_area("Was trägt das Model? (Outfit)", 
                            placeholder="z.B. Weißes Seidenkleid, Schwarzer Rollkragenpullover, Casual T-Shirt...",
                            height=100)

with c_pose:
    # POSE LOGIK (verschoben für besseres Layout)
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

# --- 4. KAMPAGNE & PRODUKT ---
st.markdown("---")
st.subheader("4. Die Kampagne (Produkt & Referenz)")
k1, k2 = st.columns([1, 1])

with k1:
    product = st.text_input("Produkt / Thema", placeholder="z.B. Goldene Halskette mit Rubin")
    
    # HIER IST DIE ANGEPASSTE LOGIK
    wear_product = st.checkbox("Exaktes Produkt wird als Bild in Veo hochgeladen? (Referenz-Bild)", value=False,
                               help="Wenn an: Prompt befiehlt Veo, das Referenzbild zu nutzen UND den Fokus darauf zu legen.")

with k2:
    bg = st.selectbox("Hintergrund", 
                      ["Clean White Studio", "Dark Luxury Background", "Warm Beige Tone", 
                       "Blurred City Street", "Nature/Forest", "Blue Sky", "Abstract Gradient"])

# --- GPT GENERATION ---
def generate_prompt():
    if not api_key:
        st.error("⚠️ API Key fehlt!")
        return None

    client = OpenAI(api_key=api_key)

    # --- PRODUKT FOKUS LOGIK ---
    if wear_product:
        # HIER WURDE "SHALLOW DEPTH OF FIELD" und "FOCUS" HINZUGEFÜGT
        prod_instr = (f"CRITICAL INSTRUCTION: The user provides a reference image of the product '{product}'. "
                      f"The output prompt MUST explicitly state: 'Using the provided product reference image, ensure the model is wearing exactly this specific item.' "
                      f"The product '{product}' MUST be the absolute visual focus of the shot (shallow depth of field highlighting the product).")
        ref_reminder = "✅ WICHTIG: Lade jetzt das Bild des Produkts in Veo hoch!"
    else:
        prod_instr = f"Campaign for the product category '{product}', but the model is NOT wearing a specific product visibly. Focus on the brand VIBE."
        ref_reminder = ""

    # Check ob Kleidung angegeben wurde
    if clothing:
        outfit_instr = f"OUTFIT: Model is wearing {clothing}."
    else:
        outfit_instr = "OUTFIT: Fashionable, minimal clothing fitting the luxury vibe."

    system_prompt = """
    You are a Senior Art Director for High-End Commercial AI Generation (Google Veo).
    Write a single, highly detailed prompt in English.
    
    MANDATORY RULES:
    1. PRODUCT: If instructed, emphasize the product reference image and make it the focal point.
    2. SKIN: "subsurface scattering, micropore texture, visible pores, vellus hair". NO plastic skin.
    3. OUTFIT: Describe the clothing texture (silk, cotton, wool) based on user input.
    4. CAMERA: Include technical camera specs provided.
    """

    user_prompt = f"""
    Create a luxury ad prompt for Veo:
    
    MODEL: {gender}, {age}, {ethnicity}.
    STYLE: {hair_color} hair ({hair_style}, {wind}), {eye_color} eyes.
    SKIN/MAKEUP: {freckles}, {skin_finish} finish, {makeup} makeup.
    
    {outfit_instr}
    
    POSE & ACTION:
    - Pose: {pose}
    - Gaze: {gaze}
    - Expression: {expression}
    
    CONTEXT: {prod_instr}
    SETTING: {bg} background. Lighting: {lighting}.
    
    TECHNICAL: {framing}, shot on {lens} lens. High fidelity, raw photo style.
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
if st.button("AD-CAMPAIGN STARTEN 🚀"):
    if not product:
        st.warning("Bitte gib ein Produkt ein!")
    else:
        with st.spinner("Writing Director's Treatment..."):
            prompt_res, reminder = generate_prompt()
            if prompt_res:
                st.success("Prompt Generiert!")
                
                if reminder:
                    st.info(reminder)
                    
                st.code(prompt_res, language="text")
                st.caption("Copy & Paste in Veo")
