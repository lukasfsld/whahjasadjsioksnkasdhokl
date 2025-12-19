import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Veo Campaign Director Pro",
    page_icon="🎬",
    layout="wide" # Breiteres Layout für mehr Übersicht
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: white;
        border-radius: 8px;
        padding: 15px;
        font-weight: 700;
        font-size: 18px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    h1, h2, h3 {
        font-family: 'Helvetica', sans-serif;
    }
    /* Boxen visuell trennen */
    .stSelectbox, .stTextInput, .stRadio {
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🎬 Veo Campaign Director Pro")
st.markdown("Erstelle High-End Prompts mit exakter Kontrolle über **Hauttextur**, **Styling** und **Produkt-Platzierung**.")
st.info("💡 Tipp: Nutze die Sidebar (links) für deinen API Key.")
st.divider()

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Sicherheit")
    # Versucht erst den Key aus Secrets zu holen, sonst Eingabefeld
    if "OPENAI_API_KEY" in st.secrets:
        st.success("API Key aus Secrets geladen ✅")
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        api_key = st.text_input("OpenAI API Key eingeben", type="password")
        if not api_key:
            st.warning("Bitte Key eingeben.")

# --- INPUT: MODEL DETAILS ---
st.subheader("1. Das Model & Look")
col1, col2, col3 = st.columns(3)

with col1:
    gender = st.selectbox("Geschlecht", ["Female Model", "Male Model", "Non-binary Model"])
    age_range = st.select_slider("Alter", options=["18-24", "25-34", "35-44", "45-55", "60+"], value="25-34")
    ethnicity = st.text_input("Ethnie / Herkunft", value="mixed heritage", placeholder="z.B. Scandinavian")

with col2:
    hair_color = st.text_input("Haarfarbe", value="dark brown")
    hair_style = st.selectbox("Frisur", ["Loose & Natural", "Sleek Ponytail", "Wet Look", "Messy Bun", "Bob Cut", "Very Short"])
    # FEATURE 1: Wind/Dynamik
    wind_level = st.select_slider("Haar-Dynamik (Wind)", options=["Static (No Wind)", "Gentle Breeze", "Strong Wind/Motion"], value="Gentle Breeze")

with col3:
    eye_color = st.text_input("Augenfarbe", value="green")
    # WIEDER DA: Sommersprossen
    freckles = st.radio("Sommersprossen?", ["Keine / Klare Haut", "Leichte Sommersprossen", "Starke Sommersprossen"], horizontal=True)
    # NEU: Make-up
    makeup_style = st.select_slider("Make-up Intensität", 
                                    options=["No Makeup (Raw)", "Clean Girl (Natural)", "Soft Glam", "High Fashion / Editorial", "Avant-Garde"])

# --- INPUT: HAUT & EXPRESSION (Die 5 neuen Features) ---
st.markdown("---")
st.subheader("2. Details & Stimmung")
c1, c2, c3 = st.columns(3)

with c1:
    # FEATURE 2: Expression
    expression = st.selectbox("Gesichtsausdruck (Mimik)", 
                              ["Neutral & Cool", "Confident Smile", "Laughing/Joyful", "Seductive/Intense", "Fierce/Serious", "Dreamy/Closed Eyes"])

with c2:
    # FEATURE 3: Haut-Finish
    skin_finish = st.selectbox("Haut-Finish", 
                               ["Natural Matte", "Dewy & Glowy (Hydrated)", "Sweaty/Oily (Athletic)", "Glass Skin (K-Beauty)"])

with c3:
    # FEATURE 4: Lichtsetzung
    lighting = st.selectbox("Licht-Stimmung", 
                            ["Soft Studio Lighting (Beauty)", "Golden Hour (Sunlight)", "Rembrandt (Moody)", "Cinematic (Dark & Contrast)", "Neon/Colorful"])

# --- INPUT: KAMPAGNE & TECHNIK ---
st.markdown("---")
st.subheader("3. Kampagne, Produkt & Kamera")

k1, k2 = st.columns([1, 1])

with k1:
    # PRODUKT LOGIK
    product_focus = st.text_input("Für welches Produkt/Branche ist die Werbung?", 
                                placeholder="z.B. Goldene Ohrringe, Anti-Aging Creme")
    
    # NEU: Checkbox um das Problem mit den ungewollten Ohrringen zu lösen
    wear_product = st.checkbox("Soll das Model das Produkt physisch tragen/halten?", value=False, 
                               help="Wenn aus, bestimmt das Produkt nur den Vibe, ist aber nicht unbedingt zu sehen.")
    
    bg_choice = st.selectbox("Hintergrund", 
                             ["Clean White Studio", "Dark Luxury Studio", "Warm Beige Tone", "Blurred City (Bokeh)", "Nature/Forest", "Blue Sky", "Abstract Gradient"])

with k2:
    # FRAMING
    framing = st.select_slider("Bildausschnitt (Zoom)", 
                               options=["Extreme Close-Up (Eye/Mouth)", "Close-Up (Face)", "Medium Shot (Chest up)", "Waist up"])
    
    # FEATURE 5: Objektiv (Kamera)
    lens_choice = st.selectbox("Kamera-Objektiv (Look)", 
                               ["85mm (Standard Portrait)", "100mm Macro (Extreme Details)", "35mm (Lifestyle/Doku)", "50mm (Neutral)"])


# --- GPT LOGIC ---

def generate_pro_prompt():
    if not api_key:
        st.error("⚠️ Kein API Key gefunden!")
        return None

    client = OpenAI(api_key=api_key)

    # Logik für das Produkt-Tragen
    if wear_product:
        product_instruction = f"The model is WEARING/HOLDING the product: '{product_focus}'. Make it the focal point."
    else:
        product_instruction = f"This is an ad campaign for '{product_focus}', but the model is NOT wearing the product visibly in this shot. Focus on the face/mood that fits the brand image."

    # System Prompt: Der "Gehirn"-Teil
    system_instruction = """
    You are a World-Class AI Art Director for high-end video/image generation (Veo/Midjourney).
    
    STRICT RULES:
    1. SKIN: You must ALWAYS include: "subsurface scattering, micropore texture, visible pores, vellus hair on face".
    2. REALISM: Reject "smooth" or "plastic" looks. Use keywords: "raw photo, unretouched, 8k, phase one capture".
    3. LANGUAGE: Output one cohesive, professional English paragraph.
    """

    # User Content: Die Variablen
    user_content = f"""
    Create a photorealistic prompt with these specs:
    
    SUBJECT: {gender}, age {age_range}, {ethnicity}.
    LOOK: {hair_color} hair ({hair_style}), {wind_level}. {eye_color} eyes.
    SKIN FEATURES: {freckles}, {skin_finish} finish.
    MAKEUP: {makeup_style}.
    EXPRESSION: {expression}.
    
    CONTEXT: {product_instruction}
    BACKGROUND: {bg_choice}.
    LIGHTING: {lighting}.
    
    TECHNICAL: Shot on {lens_choice} lens. Framing: {framing}.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- ACTION ---

if st.button("PROMPT GENERIEREN 🚀"):
    if not product_focus:
        st.warning("Bitte gib eine Branche/ein Produkt ein.")
    else:
        with st.spinner("Erstelle High-End Prompt..."):
            prompt_text = generate_pro_prompt()
            if prompt_text:
                st.success("Fertig!")
                st.markdown("### Dein Prompt:")
                st.code(prompt_text, language="text")
                st.caption("Copy & Paste in Veo")
