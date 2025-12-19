import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Veo Campaign Director",
    page_icon="🎬",
    layout="centered"
)

# --- CUSTOM CSS (Design-Upgrade) ---
st.markdown("""
    <style>
    /* Button Design */
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: white;
        border-radius: 8px;
        padding: 12px;
        font-weight: 600;
        border: none;
    }
    .stButton>button:hover {
        background-color: #333333;
        color: white;
    }
    /* Input Felder Styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    /* Header Styling */
    h1 {
        font-family: 'Helvetica', sans-serif;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- HEADER ---
st.title("🎬 Veo Campaign Director")
st.markdown("Generiere High-End Prompts für Werbekampagnen mit Fokus auf **ultra-realistische Hauttextur**.")
st.divider()

# --- INPUT SECTION: MODEL ---
st.subheader("1. Das Model")
col1, col2 = st.columns(2)

with col1:
    gender = st.selectbox("Model Typ", ["Female Model", "Male Model", "Non-binary Model"])
    age_range = st.select_slider("Alter", options=["20s", "30s", "40s", "50s", "60+"], value="30s")
    ethnicity = st.text_input("Ethnie / Look", value="olive skin tone", placeholder="z.B. Scandinavian, Afro-Caribbean")

with col2:
    hair_color = st.text_input("Haarfarbe", value="dark brown")
    # NEU: Auswahl Frisur
    hair_style = st.selectbox("Frisur", ["Open loose hair", "Sleek ponytail", "Messy bun", "Braided hair", "Short buzz cut"])
    eye_color = st.text_input("Augenfarbe", value="hazel")

# --- INPUT SECTION: KAMPAGNE ---
st.markdown("---")
st.subheader("2. Kampagne & Setting")

c1, c2 = st.columns(2)

with c1:
    # NEU: Freies Textfeld für das Produkt
    product_focus = st.text_input("Wofür ist die Werbung?", 
                                placeholder="z.B. Goldene Ohrringe, Anti-Aging Creme, Luxus-Handtasche")
    
    # NEU: Vorgefertigte Hintergründe
    bg_options = {
        "Studio White": "clean bright white studio background, commercial lighting",
        "Studio Red": "deep red background, dramatic cinematic lighting",
        "Studio Beige": "warm beige soft luxury background, organic feel",
        "Studio Black": "pitch black background, rim lighting, moody",
        "Outdoor City": "blurred city street at golden hour (bokeh)",
        "Outdoor Nature": "soft green forest background, natural sunlight",
        "Abstract Gradient": "soft abstract color gradient background, modern art style"
    }
    selected_bg_name = st.selectbox("Hintergrund wählen", list(bg_options.keys()))
    background_prompt = bg_options[selected_bg_name]

with c2:
    # Framing
    frame_from = st.selectbox("Ausschnitt Start (Unten)", ["Chest", "Shoulders", "Neck", "Chin", "Waist"])
    frame_to = st.selectbox("Ausschnitt Ende (Oben)", ["Top of Head", "Hairline", "Forehead", "Eyes"])

# --- GPT LOGIC ---

def get_chatgpt_prompt():
    # SICHERHEITS-CHECK: Prüfen ob der Secret Key da ist
    if "OPENAI_API_KEY" not in st.secrets:
        st.error("⚠️ API Key fehlt! Bitte setze 'OPENAI_API_KEY' in den Streamlit Secrets.")
        return None

    # Key aus den Secrets laden (nicht hardcodiert!)
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    system_instruction = """
    You are a High-End Commercial Art Director specializing in Generative AI (Veo/Midjourney).
    Your goal is to write a single, fluid, highly descriptive prompt in English.
    
    MANDATORY TEXTURE RULES:
    - You must strictly enforce "subsurface scattering, micropore texture, visible pores, vellus hair".
    - Reject any "smooth" or "airbrushed" skin descriptions. 
    - Include camera gear specifics (e.g., "Shot on Phase One XF IQ4, 100mm Macro lens" for jewelry/beauty).
    """

    user_content = f"""
    Create a luxury commercial prompt.
    
    SUBJECT: {gender}, {age_range}, {ethnicity}.
    HAIR: {hair_color}, styled in {hair_style}.
    EYES: {eye_color}.
    
    CAMPAIGN FOCUS: The product is "{product_focus}". Ensure the pose and lighting highlights this specific product.
    
    FRAMING: Strict close-up from {frame_from} to {frame_to}.
    BACKGROUND: {background_prompt}.
    
    Make it look like a global campaign (Vogue/Billboard quality).
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
        st.error(f"Fehler bei OpenAI: {e}")
        return None

# --- OUTPUT ---

if st.button("AD-PROMPT GENERIEREN ✨"):
    if not product_focus:
        st.warning("Bitte gib ein, wofür die Werbung ist (z.B. 'Ohrringe').")
    else:
        with st.spinner("AI Director schreibt den Prompt..."):
            gpt_result = get_chatgpt_prompt()
            
            if gpt_result:
                st.success("Prompt fertig!")
                st.markdown("### 📋 Dein Prompt")
                st.code(gpt_result, language="text")
                st.caption("Kopiere diesen Text in Veo oder Midjourney.")

st.markdown("---")
st.caption("Internal Tool • Protected by Streamlit Secrets")
