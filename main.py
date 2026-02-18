import streamlit as st
import json
import os
from datetime import datetime
from jinja2 import Template

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nano Banana Campaign Director (V11)",
    page_icon="🍌",
    layout="wide"
)

# --- LOAD TEMPLATE & PRESETS ---
# Works on both local and Streamlit Cloud
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

with open(SCRIPT_DIR / "prompt_template.j2", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE = Template(f.read())

with open(SCRIPT_DIR / "video_template.j2", "r", encoding="utf-8") as f:
    VIDEO_TEMPLATE = Template(f.read())

with open(SCRIPT_DIR / "presets.json", "r", encoding="utf-8") as f:
    PRESETS = json.load(f)

# --- SESSION STATE ---
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #FFD700;
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
    div[data-testid="stCheckbox"] label span { font-weight: 600; }
    .prompt-box {
        background: #1a1a2e;
        color: #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        font-family: monospace;
        font-size: 14px;
        white-space: pre-wrap;
        border: 1px solid #333;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 Settings")

    # Optional API Key (only for polish mode)
    use_polish = st.checkbox("✨ GPT-4o Polish (optional)", value=False,
                             help="Verfeinert den Prompt mit GPT-4o. Braucht API Key.")
    api_key = None
    if use_polish:
        if "OPENAI_API_KEY" in st.secrets:
            st.success("API Key aktiv (Secrets) ✅")
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            api_key = st.text_input("OpenAI API Key", type="password")
            if not api_key:
                st.warning("API Key nötig für Polish-Modus.")

    st.markdown("---")
    st.info("**Lokal:** Template-basiert, kein API nötig.\n\n**Polish:** Optional GPT-4o Verfeinerung.")
    st.markdown("---")
    st.caption("V11: Lokales Template · Presets · History · Optional Polish")

    # --- HISTORY ---
    st.markdown("---")
    st.header("📜 Prompt-Historie")
    if st.session_state.prompt_history:
        for i, entry in enumerate(reversed(st.session_state.prompt_history)):
            etype = entry.get("type", "📷 Bild")
            with st.expander(f"#{len(st.session_state.prompt_history) - i} {etype} — {entry['time']}"):
                st.code(entry["prompt"], language="text")
        if st.button("🗑️ Historie löschen"):
            st.session_state.prompt_history = []
            st.rerun()
    else:
        st.caption("Noch keine Prompts generiert.")


# --- HEADER ---
st.title("🍌 Nano Banana Campaign Director (V11)")
st.markdown("**Lokal & sofort** — Template-basierte Prompts. Optional mit GPT-4o Polish.")
st.divider()

# --- PRESETS ---
st.subheader("⚡ Schnellstart: Presets")
preset_names = ["— Kein Preset —"] + list(PRESETS.keys())
selected_preset = st.selectbox("Preset laden", preset_names, help="Befüllt alle Felder mit einem Klick.")

if selected_preset != "— Kein Preset —":
    p = PRESETS[selected_preset]
else:
    p = {}

def get_val(key, default=""):
    """Get value from preset or return default."""
    return p.get(key, default)


# --- 1. MODEL & REALISMUS ---
st.markdown("---")
st.subheader("1. Model & Realismus")
col1, col2, col3, col4 = st.columns(4)

with col1:
    gender_options = ["Female Model", "Male Model", "Non-binary Model"]
    gender = st.selectbox("Geschlecht", gender_options,
                          index=gender_options.index(get_val("gender", "Female Model")))
    age_options = ["18-24", "25-34", "35-44", "45-55", "60+"]
    age = st.select_slider("Alter", options=age_options,
                           value=get_val("age", "25-34"))

with col2:
    ethnicity = st.text_input("Ethnie / Look", value=get_val("ethnicity", "olive skin tone"))
    hair_color = st.text_input("Haarfarbe", value=get_val("hair_color", "dark brown"))

with col3:
    hair_tex_options = ["Straight (Glatt)", "Wavy (Wellig)", "Curly (Lockig)", "Coily (Afro)"]
    hair_texture = st.select_slider("Haarstruktur", options=hair_tex_options,
                                    value=get_val("hair_texture", "Wavy (Wellig)"))
    hair_style_options = ["Loose & Open", "Sleek Ponytail", "Messy Bun", "Short Cut", "Bob Cut"]
    hair_style = st.selectbox("Frisur-Stil", hair_style_options,
                              index=hair_style_options.index(get_val("hair_style", "Loose & Open")))

with col4:
    eye_color = st.text_input("Augenfarbe", value=get_val("eye_color", "green"))
    freckle_options = ["Klare Haut", "Sommersprossen"]
    freckles = st.radio("Haut-Basis", freckle_options, horizontal=True,
                        index=freckle_options.index(get_val("freckles", "Klare Haut")))
    use_vellus = st.checkbox("Vellus Hair (Flaum)", value=get_val("use_vellus", True),
                             help="Ultra-realistische Härchen auf der Haut.")
    use_imperfections = st.checkbox("Natural Imperfections", value=get_val("use_imperfections", False),
                                   help="Asymmetrie und kleine Makel.")


# --- 2. KLEIDUNG & POSE ---
st.markdown("---")
st.subheader("2. Kleidung, Pose & Moments")
c_outfit, c_pose = st.columns([1, 2])

with c_outfit:
    clothing = st.text_area("Outfit", value=get_val("clothing", ""),
                            placeholder="z.B. Weißes Seidenkleid...", height=100)
    makeup_options = ["No Makeup", "Natural/Clean", "Soft Glam", "High Fashion"]
    makeup = st.select_slider("Make-up", options=makeup_options,
                              value=get_val("makeup", "Natural/Clean"))

with c_pose:
    use_candid = st.checkbox("📸 Candid Moment?", value=get_val("use_candid", False))

    p1, p2, p3 = st.columns(3)

    if use_candid:
        with p1:
            candid_options = ["Caught off guard", "Laughing mid-sentence", "Fixing Hair", "Looking past camera"]
            candid_moment = st.selectbox("Moment", candid_options)
            pose = f"Candid Shot: {candid_moment}"
            gaze = "Natural / Ungestellt"
            expression = "Authentic"
    else:
        candid_moment = None
        with p1:
            pose_options = ["Standing Upright (Power Pose)", "Relaxed Leaning",
                            "Walking towards Camera", "Sitting Elegantly",
                            "Dynamic Action", "Over the Shoulder"]
            pose = st.selectbox("Körperhaltung", pose_options,
                                index=pose_options.index(get_val("pose", "Standing Upright (Power Pose)"))
                                if get_val("pose", "") in pose_options else 0)
        with p2:
            gaze_options = ["Straight into Camera", "Looking away (Dreamy)", "Looking down", "Looking up"]
            gaze = st.selectbox("Blickrichtung", gaze_options,
                                index=gaze_options.index(get_val("gaze", "Straight into Camera"))
                                if get_val("gaze", "") in gaze_options else 0)
        with p3:
            expr_options = ["Neutral & Cool", "Confident Smile", "Laughing", "Fierce/Intense", "Seductive"]
            expression = st.selectbox("Gesichtsausdruck", expr_options,
                                      index=expr_options.index(get_val("expression", "Neutral & Cool"))
                                      if get_val("expression", "") in expr_options else 0)

    wind_options = ["Static", "Soft Breeze", "Strong Wind"]
    wind = "Natural movement" if use_candid else st.select_slider(
        "Haar-Dynamik", options=wind_options, value=get_val("wind", "Soft Breeze")
        if get_val("wind", "Soft Breeze") in wind_options else "Soft Breeze")


# --- 3. KAMERA, LICHT & ATMOSPHÄRE ---
st.markdown("---")
st.subheader("3. Kamera, Licht & Atmosphäre")
t1, t2, t3, t4 = st.columns(4)

with t1:
    cam_options = ["360° Orbit (Circle around Model)", "Static Tripod",
                   "Slow Zoom In", "Handheld", "Drone Orbit (Landscape)"]
    cam_move = st.selectbox("Kamera-Bewegung", cam_options,
                            index=cam_options.index(get_val("cam_move", "Static Tripod"))
                            if get_val("cam_move", "") in cam_options else 1)

    focus_options = ["Balanced (Model + Product)", "Model Hero (Face Focus)",
                     "Product Hero (Blurry Model)", "Detail Shot (Hands/Product Only)"]
    shot_focus = st.selectbox("Shot Focus",focus_options,
                              index=focus_options.index(get_val("shot_focus", "Balanced (Model + Product)"))
                              if get_val("shot_focus", "") in focus_options else 0)

with t2:
    light_options = ["Butterfly Lighting (Beauty)", "Split Lighting (Dramatic Side)",
                     "Rim Light / Backlight (Halo Effect)", "Rembrandt (Classic)",
                     "Golden Hour (Sun)", "Softbox Studio (Clean)", "Neon / Cyberpunk"]
    lighting = st.selectbox("Licht-Setup", light_options,
                            index=light_options.index(get_val("lighting", "Butterfly Lighting (Beauty)"))
                            if get_val("lighting", "") in light_options else 0)

with t3:
    film_options = ["Standard Commercial", "Kodak Portra 400", "Teal & Orange",
                    "Black & White", "Pastel/Dreamy", "Moody/Dark"]
    film_look = st.selectbox("Film Look", film_options,
                             index=film_options.index(get_val("film_look", "Standard Commercial"))
                             if get_val("film_look", "") in film_options else 0)

    frame_options = ["Extreme Close-Up", "Portrait", "Medium Shot", "Full Body"]
    framing = st.selectbox("Ausschnitt", frame_options,
                           index=frame_options.index(get_val("framing", "Portrait"))
                           if get_val("framing", "") in frame_options else 1)

with t4:
    lens_options = ["85mm (Portrait)", "100mm Macro", "35mm (Lifestyle)", "24mm (Wide)"]
    lens = st.selectbox("Objektiv", lens_options,
                        index=lens_options.index(get_val("lens", "85mm (Portrait)"))
                        if get_val("lens", "") in lens_options else 0)

    use_aperture = st.checkbox("Manuelle Blende?", value=get_val("use_aperture", False))
    ap_options = ["f/1.2 (Bokeh)", "f/1.8 (Soft)", "f/8.0 (Sharp)"]
    aperture = st.selectbox("Blende", ap_options,
                            index=ap_options.index(get_val("aperture", "f/1.2 (Bokeh)"))
                            if get_val("aperture", "") in ap_options else 0) if use_aperture else None


# --- 4. FORMAT & PRODUKT ---
st.markdown("---")
st.subheader("4. Format, Produkt & Extras")
k1, k2 = st.columns([1, 1])

with k1:
    product = st.text_input("Produkt / Thema", value=get_val("product", ""),
                            placeholder="z.B. Goldene Halskette")

    st.markdown("---")
    use_size = st.checkbox("Spezifische Größe (cm)?", value=False)
    if use_size:
        obj_type = st.radio("Objekt Art", ["Kettenanhänger", "Objekt"], horizontal=True)
        obj_size = st.slider("Größe (cm)", 0.5, 5.0, 2.5, 0.1)
    else:
        obj_type, obj_size = None, None

    st.markdown("---")
    wear_product = st.checkbox("Referenz-Bild hochladen?", value=False)

    st.markdown("---")
    negative_prompt = st.text_area("🚫 Negativ-Prompt (optional)",
                                  placeholder="z.B. no text, no watermark, no deformed hands...",
                                  height=80)

with k2:
    st.markdown("**Bildformat:**")
    ar_options = ["Querformat (16:9)", "Hochformat (9:16)", "Quadrat (1:1)", "Cinematic (21:9)"]
    aspect_ratio = st.selectbox("Format", ar_options,
                                index=ar_options.index(get_val("aspect_ratio", "Querformat (16:9)"))
                                if get_val("aspect_ratio", "") in ar_options else 0)

    st.markdown("**Hintergrund:**")
    weather_options = ["Clear/Sunny", "Cloudy", "Rainy/Wet", "Foggy", "Snowing"]
    weather = st.selectbox("Wetter", weather_options,
                           index=weather_options.index(get_val("weather", "Clear/Sunny"))
                           if get_val("weather", "") in weather_options else 0)

    bg_mode = st.radio("Hintergrund", ["Szenisch", "Einfarbig"], horizontal=True, label_visibility="collapsed")
    if bg_mode == "Szenisch":
        bg_options = ["Clean White Studio", "Dark Luxury", "Warm Beige",
                      "City Street", "Nature", "Blue Sky", "Abstract"]
        bg_sel = st.selectbox("Szenario", bg_options)
        final_bg = f"{bg_sel} background"
    else:
        col = st.color_picker("Farbe", "#FF0044")
        final_bg = f"Solid background hex {col}"


# --- 5. VEO3 VIDEO GENERATION ---
st.markdown("---")
st.subheader("5. 🎬 Veo3 Video-Generation (optional)")
use_video = st.checkbox("Video-Prompt aktivieren", value=False,
                        help="Erweitert den Bild-Prompt um Veo3 Video-Anweisungen.")

if use_video:
    v1, v2, v3 = st.columns(3)

    with v1:
        st.markdown("**Video-Basics**")
        video_duration = st.select_slider("Dauer (Sekunden)", options=[3, 5, 8, 10, 15], value=5)
        video_ratio = st.selectbox("Video-Format", ["16:9 (Landscape)", "9:16 (Vertical/Reels)", "1:1 (Square)"])
        video_fps = st.selectbox("Framerate", ["24fps (Cinematic)", "30fps (Standard)", "60fps (Smooth)"])

    with v2:
        st.markdown("**Model-Aktion**")
        model_action = st.selectbox("Was macht das Model?", [
            "Walks slowly towards camera",
            "Walks past camera (Runway Walk)",
            "Poses with jewelry / product",
            "Turns head slowly to camera",
            "Touches / adjusts product on body",
            "Picks up product from table",
            "Stands still, only subtle breathing",
            "Spins around (Full Body Reveal)",
            "Sits down elegantly",
            "Leans against wall, shifts weight",
            "Custom..."
        ])
        if model_action == "Custom...":
            model_action = st.text_input("Eigene Aktion beschreiben",
                                         placeholder="z.B. Model nimmt Sonnenbrille ab und lächelt")

        action_detail = st.text_input("Zusatz-Detail (optional)",
                                      placeholder="z.B. Finger streicht über Anhänger, Haare fallen ins Gesicht")

        movement_speed = st.select_slider("Bewegungs-Tempo",
                                          options=["Very Slow (Slow-Mo Feel)", "Slow & Elegant",
                                                   "Natural Pace", "Energetic / Fast"],
                                          value="Slow & Elegant")

    with v3:
        st.markdown("**Atmosphäre & Sound**")

        # Wind
        video_wind = st.selectbox("Wind im Video", [
            "Kein Wind",
            "Gentle breeze (leicht)",
            "Medium wind (Haare wehen)",
            "Strong dramatic wind (Stoff fliegt)",
            "Fan wind from front (Studio-Ventilator)"
        ])

        # Camera movement for video
        video_cam = st.selectbox("Kamera-Bewegung (Video)", [
            "Static (Stativ, Model bewegt sich)",
            "Slow tracking forward",
            "Slow tracking sideways (Dolly)",
            "360° Orbit around model",
            "Slow zoom in on face",
            "Crane shot (oben nach unten)",
            "Handheld (leicht wackelig, authentisch)"
        ])

    # Dialogue & Sound (separate row)
    st.markdown("**Sprache & Sound**")
    d1, d2 = st.columns(2)

    with d1:
        has_dialogue = st.checkbox("🎤 Model spricht (Lip Sync)", value=False)
        if has_dialogue:
            dialogue_text = st.text_area("Was sagt das Model?",
                                         placeholder='z.B. "This is the one piece you need this summer."',
                                         height=80)
            voice_tone = st.selectbox("Stimme / Ton", [
                "Soft & whispery (ASMR-like)",
                "Confident & clear",
                "Warm & friendly",
                "Seductive & low",
                "Energetic & upbeat",
                "Cool & casual"
            ])
        else:
            dialogue_text = ""
            voice_tone = ""

    with d2:
        has_ambient = st.checkbox("🔊 Ambient Sound", value=False)
        if has_ambient:
            ambient_sound = st.selectbox("Sound-Atmosphäre", [
                "Soft cinematic music",
                "City ambient (traffic, people)",
                "Nature sounds (birds, wind)",
                "Studio silence with subtle reverb",
                "Upbeat fashion/commercial beat",
                "Lo-fi / chill background"
            ])
        else:
            ambient_sound = ""


# --- PROMPT BUILD (LOCAL) ---
def build_prompt_local():
    """Build prompt locally using Jinja2 template — no API needed."""

    # Aspect ratio text
    if "16:9" in aspect_ratio: ar_text = "16:9 (Landscape)"
    elif "9:16" in aspect_ratio: ar_text = "9:16 (Vertical / Portrait)"
    elif "21:9" in aspect_ratio: ar_text = "21:9 (Cinematic Ultrawide)"
    else: ar_text = "1:1 (Square)"

    # Camera movement
    if "360° Orbit" in cam_move:
        move_instr = ("CAMERA: Smooth continuous 360-degree orbital movement circling the subject. "
                      "Keep model perfectly centered, revealing outfit and product from all angles.")
    elif "Slow Zoom" in cam_move:
        move_instr = "CAMERA: Slow, cinematic zoom-in towards the subject. Tension-building."
    elif "Handheld" in cam_move:
        move_instr = "CAMERA: Handheld, slightly shaky, documentary-feel movement."
    elif "Drone" in cam_move:
        move_instr = "CAMERA: Elevated drone orbit around subject, sweeping landscape reveal."
    else:
        move_instr = "CAMERA: Static tripod, locked-off frame. Clean and stable."

    # Size instruction
    size_instr = f"SCALE: The product is exactly {obj_size}cm. Show proportional to hand/body." if use_size and obj_size else ""

    # Product instruction
    ref_reminder = ""
    if wear_product:
        prod_instr = (f"The model wears/holds '{product}'. Use the provided REFERENCE IMAGE "
                      f"for exact product appearance. Blend naturally into the scene.")
        ref_reminder = "⚠️ WICHTIG: Lade dein Referenzbild zusammen mit diesem Prompt hoch!"
    else:
        prod_instr = f"Campaign product: '{product}'. Integrate naturally into the composition."

    # Focus instruction
    focus_map = {
        "Model Hero (Face Focus)": "FOCUS PRIORITY: Sharp focus on model's face and expression. Product secondary.",
        "Product Hero (Blurry Model)": f"FOCUS PRIORITY: Razor-sharp focus on '{product}'. Model slightly out of focus (bokeh).",
        "Detail Shot (Hands/Product Only)": f"FOCUS PRIORITY: Macro detail shot of '{product}'. Tight crop, face may be cut off.",
    }
    focus_instr = focus_map.get(shot_focus, "FOCUS PRIORITY: Balanced — model and product equally sharp and prominent.")

    # Outfit
    outfit_instr = f"OUTFIT: {clothing}." if clothing else "OUTFIT: High-fashion minimal styling."

    # Skin details
    skin_parts = [freckles]
    if use_vellus:
        skin_parts.append("visible vellus hair (peach fuzz) on cheeks and forehead")
    if use_imperfections:
        skin_parts.append("natural facial asymmetry, subtle micro-imperfections")
    skin_details = ", ".join(skin_parts)

    # Lighting details (extra tips per setup)
    lighting_tips = {
        "Butterfly Lighting (Beauty)": "Key light directly above and in front of face, creating butterfly shadow under nose. Fill from below.",
        "Split Lighting (Dramatic Side)": "Single hard light from 90° to one side. Deep shadow splits the face in half.",
        "Rim Light / Backlight (Halo Effect)": "Strong backlight creating luminous edge around hair and shoulders. Minimal front fill.",
        "Rembrandt (Classic)": "Key light 45° above and to one side, triangle of light on shadow-side cheek.",
        "Golden Hour (Sun)": "Warm, low-angle sunlight. Long shadows, golden skin tones, lens flare possible.",
        "Softbox Studio (Clean)": "Large soft key light, minimal shadows, clean commercial look.",
        "Neon / Cyberpunk": "Colored neon light sources (pink, blue, purple). High contrast, urban night feel.",
    }
    lighting_details = lighting_tips.get(lighting, "")

    # Render template
    prompt = PROMPT_TEMPLATE.render(
        aspect_ratio=ar_text,
        gender=gender,
        age=age,
        ethnicity=ethnicity,
        eye_color=eye_color,
        hair_color=hair_color,
        hair_texture=hair_texture,
        hair_style=hair_style,
        wind=wind,
        skin_details=skin_details,
        pose=pose,
        gaze=gaze,
        expression=expression,
        candid_moment=candid_moment or "",
        makeup=makeup,
        outfit_instr=outfit_instr,
        prod_instr=prod_instr,
        focus_instr=focus_instr,
        size_instr=size_instr,
        lighting=lighting,
        lighting_details=lighting_details,
        framing=framing,
        lens=lens,
        aperture=aperture,
        film_look=film_look,
        move_instr=move_instr,
        final_bg=final_bg,
        weather=weather,
        ar_text=ar_text,
        ref_reminder=ref_reminder,
    )

    # Add negative prompt if provided
    if negative_prompt and negative_prompt.strip():
        prompt += f"\n\nNEGATIVE PROMPT: {negative_prompt.strip()}"

    # Clean up extra blank lines
    lines = prompt.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty
    prompt = "\n".join(cleaned).strip()

    return prompt, ref_reminder


def build_video_prompt(image_prompt):
    """Extend the image prompt with Veo3 video instructions."""

    # Camera movement mapping
    cam_map = {
        "Static (Stativ, Model bewegt sich)": "CAMERA: Locked-off static tripod. All motion comes from the model.",
        "Slow tracking forward": "CAMERA: Slow, steady forward tracking shot towards the model.",
        "Slow tracking sideways (Dolly)": "CAMERA: Smooth lateral dolly movement, revealing the model from a new angle.",
        "360° Orbit around model": "CAMERA: Continuous smooth 360-degree orbit around the model, maintaining center frame.",
        "Slow zoom in on face": "CAMERA: Very slow, cinematic push-in zoom towards the model's face.",
        "Crane shot (oben nach unten)": "CAMERA: Crane shot descending from above, revealing the model and scene.",
        "Handheld (leicht wackelig, authentisch)": "CAMERA: Handheld with subtle natural shake, documentary/authentic feel.",
    }
    camera_video_move = cam_map.get(video_cam, "CAMERA: Static tripod.")

    # FPS
    fps = video_fps.split("fps")[0]

    # Wind
    has_wind = video_wind != "Kein Wind"
    wind_type = video_wind if has_wind else ""

    video_prompt = VIDEO_TEMPLATE.render(
        image_prompt=image_prompt,
        duration=video_duration,
        video_ratio=video_ratio,
        model_action=model_action,
        action_detail=action_detail if action_detail else "",
        movement_speed=movement_speed,
        camera_video_move=camera_video_move,
        has_wind=has_wind,
        wind_type=wind_type,
        has_dialogue=has_dialogue if use_video else False,
        dialogue_text=dialogue_text if use_video and has_dialogue else "",
        voice_tone=voice_tone if use_video and has_dialogue else "",
        has_ambient_sound=has_ambient if use_video else False,
        ambient_sound=ambient_sound if use_video and has_ambient else "",
        fps=fps,
    )

    # Clean up blank lines
    lines = video_prompt.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    return "\n".join(cleaned).strip()


def polish_with_gpt(raw_prompt, api_key):
    """Optional: refine the template prompt with GPT-4o."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    system = """You are an expert prompt engineer for AI image generation (Gemini 2.5 / Midjourney / DALL-E).
Take the given structured prompt and rewrite it as a single, flowing, highly detailed paragraph.
Keep ALL technical details. Make it more vivid and cinematic in language.
Do NOT add or remove any specifications — only improve the prose and flow."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": f"Rewrite this prompt into polished prose:\n\n{raw_prompt}"}
            ],
            temperature=0.6
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"GPT Polish Fehler: {e}")
        return None


# --- OUTPUT ---
st.markdown("---")

# Dynamic button text
btn_label = "🍌🎬 IMAGE + VIDEO PROMPT GENERIEREN" if use_video else "🍌 PROMPT GENERIEREN"

if st.button(btn_label):
    if not product:
        st.warning("Bitte ein Produkt / Thema eingeben!")
    else:
        with st.spinner("Baue Prompt..."):
            raw_prompt, reminder = build_prompt_local()

        st.success("✅ Bild-Prompt generiert!")
        if reminder:
            st.info(reminder)

        # Show raw template prompt
        st.markdown("### 📋 Bild-Prompt")
        st.code(raw_prompt, language="text")

        # VIDEO PROMPT
        final_video_prompt = None
        if use_video:
            with st.spinner("Baue Video-Prompt..."):
                final_video_prompt = build_video_prompt(raw_prompt)
            st.success("✅ Veo3 Video-Prompt generiert!")
            st.markdown("### 🎬 Veo3 Video-Prompt")
            st.code(final_video_prompt, language="text")

        # Optional GPT polish
        prompt_to_save = raw_prompt
        if use_polish:
            if not api_key:
                st.warning("⚠️ API Key fehlt für den Polish-Modus!")
            else:
                polish_target = final_video_prompt if final_video_prompt else raw_prompt
                with st.spinner("GPT-4o verfeinert..."):
                    polished = polish_with_gpt(polish_target, api_key)
                if polished:
                    st.markdown("### ✨ GPT-4o Polished Version")
                    st.code(polished, language="text")
                    prompt_to_save = polished

        # Save to history
        st.session_state.prompt_history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "prompt": final_video_prompt if final_video_prompt else raw_prompt,
            "type": "🎬 Video" if use_video else "📷 Bild",
        })

        # Export buttons
        ex1, ex2 = st.columns(2)
        with ex1:
            st.download_button(
                label="💾 Bild-Prompt speichern (.txt)",
                data=raw_prompt,
                file_name=f"nano_banana_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        with ex2:
            if final_video_prompt:
                st.download_button(
                    label="🎬 Video-Prompt speichern (.txt)",
                    data=final_video_prompt,
                    file_name=f"nano_banana_veo3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
