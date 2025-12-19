import streamlit as st
from openai import OpenAI

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Veo/AI Ad-Prompt Generator",
    page_icon="🎬",
    layout="centered"
)

# --- CSS STYLING ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #10a37f; /* OpenAI Green */
        color: white;
        font-weight: bold;
        border: none;
        padding: 10px;
    }
    .stTextInput>div>div>input {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: API KEY ---
with st.sidebar:
    st.header("🔑 Einstellung")
    api_key = st.text_input("OpenAI API Key eingeben", type="password", help="Dein Key beginnt mit sk-...")
    st.info("Der Key wird nur für diese Sitzung verwendet und nicht gespeichert.")
    st.markdown("---")
    st.markdown("**Generiert für:**\n- Veo (Video)\n- Midjourney / Flux (Bild)")

# --- MAIN CONTENT ---
st.title("🎬 High-End Ad Campaign Prompter")
st.markdown("Nutzt **ChatGPT**, um aus deinen Stichworten einen komplexen, photorealistischen Prompt zu schreiben.")
st.divider()

# --- INPUTS ---

st.subheader("1. Das Model")
col1, col2 = st.columns(2)
with col1:
    gender = st.selectbox("Geschlecht", ["Female Model", "Male Model", "Non-binary Model"])
    age_range = st.select_slider("Alter", options=["20s", "30s", "40s", "50s", "60+"], value="30s")
    hair_color = st.text_input("Haarfarbe", value="dark brown", placeholder="z.B. platinum blonde")

with col2:
    ethnicity = st.text_input("Ethnie / Hauttyp", value="olive skin tone", placeholder="z.B. scandinavian, east asian")
    eye_color = st.text_input("Augenfarbe", value="hazel", placeholder="z.B. green")
    freckles = st.radio("Haut-Details", ["Klare Haut (aber texturiert)", "Sommersprossen / Charakter"], horizontal=True)

st.markdown("---")

st.subheader("2. Ausschnitt & Kampagne")
c1, c2 = st.columns(2)

with c1:
    # Framing Auswahl
    frame_from = st.selectbox("Ausschnitt Start (Unten)", ["Chest", "Shoulders", "Neck", "Chin"])
    frame_to = st.selectbox("Ausschnitt Ende (Oben)", ["Top of Head", "Hairline", "Forehead", "Eyes"])
    
with c2:
    industry = st.selectbox("Branche", ["Skincare (Macro)", "Fashion (Editorial)", "Tech (Business)", "Automotive/Lifestyle"])
    background = st.text_input("Hintergrund", value="blurred city lights at dusk", placeholder="Ortsbeschreibung")

# --- GPT GENERATION FUNCTION ---

def get_chatgpt_prompt():
    if not api_key:
        st.error("⚠️ Bitte gib zuerst deinen OpenAI API Key in der Sidebar ein.")
        return None

    client = OpenAI(api_key=api_key)

    # Hier definieren wir die "Rolle" von ChatGPT
    system_instruction = """
    You are an expert AI Prompt Engineer specialized in creating prompts for Google Veo and Midjourney v6.
    Your goal is to write prompts for HIGH-END ADVERTISING CAMPAIGNS.
    
    CRITICAL RULES FOR REALISM:
    1. You MUST include these technical terms to ensure realistic skin: "subsurface scattering, micropore texture, visible skin pores, peach fuzz, vellus hair, unretouched raw photo".
    2. Avoid "smooth" or "plastic" skin descriptions. 
    3. Specify the camera gear based on the industry (e.g., Phase One XF IQ4 for fashion).
    4. Write the output as a single, highly descriptive paragraph in English.
    """

    # Der Inhalt, den ChatGPT verarbeiten soll
    user_content = f"""
    Create a photorealistic prompt for a {gender} in their {age_range}.
    Details: {hair_color} hair, {eye_color} eyes, {ethnicity}.
    Skin features: {freckles}.
    
    FRAMING: The shot must be a close-up specifically from {frame_from} to {frame_to}.
    CONTEXT: This is a {industry} campaign. Background: {background}.
    
    Make it look like a high-budget commercial production.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # oder gpt-3.5-turbo, wenn du sparen willst
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7 # Ein bisschen Kreativität zulassen
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
        return None

# --- ACTION BUTTON ---

if st.button("Prompt mit ChatGPT generieren ✨"):
    with st.spinner("ChatGPT schreibt den perfekten Prompt..."):
        gpt_result = get_chatgpt_prompt()
        
        if gpt_result:
            st.success("Fertig!")
            st.markdown("### Dein Veo/Midjourney Prompt")
            st.code(gpt_result, language="text")
            st.caption("Kopiere diesen Text in deinen AI-Video- oder Bildgenerator.")

st.markdown("---")
st.caption("Powered by OpenAI API & Streamlit")
