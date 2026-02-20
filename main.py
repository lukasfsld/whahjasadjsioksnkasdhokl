import streamlit as st
import json
import os
import requests
import base64
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

with open(SCRIPT_DIR / "product_template.j2", "r", encoding="utf-8") as f:
    PRODUCT_TEMPLATE = Template(f.read())

with open(SCRIPT_DIR / "presets.json", "r", encoding="utf-8") as f:
    PRESETS = json.load(f)

# --- SESSION STATE ---
if "prompt_history" not in st.session_state:
    st.session_state.prompt_history = []

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* === GLOBAL === */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    div.block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* === HEADER BANNER === */
    .hero-banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 215, 0, 0.15);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 300px;
        height: 300px;
        background: radial-gradient(circle, rgba(255,215,0,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-banner h1 {
        color: #FFD700;
        font-size: 2.2rem;
        font-weight: 900;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        color: #a0aec0;
        font-size: 1rem;
        margin: 0;
        font-weight: 400;
    }
    .hero-banner .version-badge {
        display: inline-block;
        background: rgba(255, 215, 0, 0.15);
        color: #FFD700;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 10px;
        vertical-align: middle;
    }

    /* === SECTION CARDS === */
    .section-card {
        background: linear-gradient(145deg, #1e1e2e, #252540);
        border: 1px solid rgba(255, 215, 0, 0.08);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1rem;
    }
    .section-card h3 {
        color: #FFD700;
        font-size: 1.1rem;
        font-weight: 700;
        margin: 0 0 0.8rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255, 215, 0, 0.1);
    }

    /* === BUTTONS === */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #1a1a2e;
        border-radius: 10px;
        padding: 14px 24px;
        font-weight: 800;
        font-size: 16px;
        border: none;
        margin-top: 12px;
        letter-spacing: 0.3px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.2);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #FFE44D 0%, #FFB833 100%);
        color: #1a1a2e;
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.35);
        transform: translateY(-1px);
    }
    .stButton>button:active {
        transform: translateY(0px);
    }

    /* Download buttons smaller */
    .stDownloadButton>button {
        background: linear-gradient(135deg, #2d2d44 0%, #3d3d5c 100%);
        color: #FFD700;
        border: 1px solid rgba(255, 215, 0, 0.2);
        font-size: 13px;
        padding: 8px 16px;
        font-weight: 600;
        box-shadow: none;
    }
    .stDownloadButton>button:hover {
        background: linear-gradient(135deg, #3d3d5c 0%, #4d4d6c 100%);
        color: #FFE44D;
        box-shadow: 0 2px 10px rgba(255, 215, 0, 0.15);
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(26, 26, 46, 0.5);
        border-radius: 12px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        font-size: 14px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.15), rgba(255, 165, 0, 0.1));
        border-bottom-color: #FFD700 !important;
    }

    /* === FORM ELEMENTS === */
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 6px; }

    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-color: rgba(255, 215, 0, 0.12);
        border-radius: 8px;
    }
    .stSelectbox [data-baseweb="select"] > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(255, 215, 0, 0.4);
        box-shadow: 0 0 0 1px rgba(255, 215, 0, 0.2);
    }

    /* === CHECKBOXES === */
    div[data-testid="stCheckbox"] label span {
        font-weight: 600;
    }

    /* === HEADINGS === */
    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    h2 { color: #e2e8f0; }
    h3 { color: #cbd5e0; }

    /* === EXPANDER (History) === */
    .streamlit-expanderHeader {
        font-weight: 600;
        font-size: 13px;
    }

    /* === METRIC / INFO CARDS === */
    .stat-row {
        display: flex;
        gap: 12px;
        margin: 1rem 0;
    }
    .stat-card {
        flex: 1;
        background: rgba(255, 215, 0, 0.05);
        border: 1px solid rgba(255, 215, 0, 0.1);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .stat-card .stat-value {
        color: #FFD700;
        font-size: 1.4rem;
        font-weight: 800;
    }
    .stat-card .stat-label {
        color: #718096;
        font-size: 0.75rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* === DIVIDERS === */
    hr {
        border-color: rgba(255, 215, 0, 0.08);
        margin: 1.2rem 0;
    }

    /* === GENERATED IMAGE GALLERY === */
    [data-testid="stImage"] {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255, 215, 0, 0.1);
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12121e 0%, #1a1a2e 100%);
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #FFD700;
        font-size: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 🔑 Settings")

    # Gemini API Key (for image generation)
    st.markdown("**🍌 Nano Banana (Gemini)**")
    if "GEMINI_API_KEY" in st.secrets:
        st.success("Gemini API Key aktiv ✅")
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        gemini_key = st.text_input("Gemini API Key", type="password", help="Für Bild-Generierung mit Gemini.")
        if not gemini_key:
            st.caption("Optional: Für direkte Bild-Generierung.")

    # Model quality selector
    st.markdown("**🎯 Bild-Modell Qualität**")
    model_quality = st.radio(
        "Modell wählen",
        ["⚡ Flash (schnell & günstig)", "💎 Pro (beste Qualität)"],
        index=0,
        help="Flash: ~$0.04/Bild, schnell. Pro: ~$0.14-0.24/Bild, 2K/4K, bessere Gesichter & Details."
    )
    if "💎 Pro" in model_quality:
        st.caption("⚠️ Pro kostet ca. 4-6x mehr pro Bild, liefert aber deutlich realistischere Ergebnisse.")

    st.markdown("---")

    # Optional OpenAI API Key (only for polish mode)
    use_polish = st.checkbox("✨ GPT-4o Polish (optional)", value=False,
                             help="Verfeinert den Prompt mit GPT-4o. Braucht API Key.")
    api_key = None
    if use_polish:
        if "OPENAI_API_KEY" in st.secrets:
            st.success("OpenAI API Key aktiv ✅")
            api_key = st.secrets["OPENAI_API_KEY"]
        else:
            api_key = st.text_input("OpenAI API Key", type="password")
            if not api_key:
                st.warning("API Key nötig für Polish-Modus.")

    st.markdown("---")
    st.info("**Lokal:** Template-basiert, kein API nötig.\n\n**Gemini:** Direkte Bild-Generierung.\n\n**Polish:** Optional GPT-4o Verfeinerung.")
    st.markdown("---")
    st.caption("V12: Lokales Template · Gemini Image Gen · Presets · History")

    # --- HISTORY ---
    st.markdown("---")
    st.markdown("## 📜 Prompt-Historie")
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
st.markdown("""
    <div class="hero-banner">
        <h1>🍌 Nano Banana Campaign Director <span class="version-badge">V12</span></h1>
        <p>Template-basierte Prompts · Direkte Bild-Generierung mit Gemini · Veo3 Video</p>
    </div>
""", unsafe_allow_html=True)

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
tab_model, tab_pose, tab_camera, tab_format = st.tabs([
    "👤 Model & Look",
    "🎭 Pose & Outfit",
    "📸 Kamera & Licht",
    "🎯 Format & Produkt"
])

with tab_model:
    st.markdown('<div class="section-card"><h3>Model & Realismus</h3></div>', unsafe_allow_html=True)
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
with tab_pose:
    st.markdown('<div class="section-card"><h3>Kleidung, Pose & Moments</h3></div>', unsafe_allow_html=True)
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
with tab_camera:
    st.markdown('<div class="section-card"><h3>Kamera, Licht & Atmosphäre</h3></div>', unsafe_allow_html=True)
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
with tab_format:
    st.markdown('<div class="section-card"><h3>Format, Produkt & Extras</h3></div>', unsafe_allow_html=True)
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
    wear_product = st.checkbox("📸 Referenzbilder für Produkt hochladen?", value=False,
                               help="Lade Bilder deines Produkts hoch — werden an Gemini mitgesendet.")
    if wear_product:
        campaign_ref_files = st.file_uploader(
            "Produkt-Referenzbilder (max. 4)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="campaign_ref_upload"
        )
        if campaign_ref_files and len(campaign_ref_files) > 4:
            st.warning("Maximal 4 Bilder!")
            campaign_ref_files = campaign_ref_files[:4]
        if campaign_ref_files:
            ref_preview = st.columns(min(len(campaign_ref_files), 4))
            for idx, f in enumerate(campaign_ref_files):
                with ref_preview[idx % 4]:
                    st.image(f, caption=f"Ref #{idx+1}", use_container_width=True)
    else:
        campaign_ref_files = []

    st.markdown("---")
    st.markdown("**🚫 Negativ-Prompt**")
    neg_presets = st.multiselect(
        "Häufige Ausschlüsse",
        [
            "no airbrush skin",
            "no plastic look",
            "no symmetrical face",
            "no overly smooth skin",
            "no wax figure appearance",
            "no uncanny valley",
            "no AI-generated look",
            "no oversaturated colors",
            "no blurry details",
            "no deformed hands",
            "no extra fingers",
            "no text",
            "no watermark",
            "no logo",
            "no cropped frame",
            "no cartoonish style",
            "no overexposed highlights",
            "no flat lighting",
            "no stock photo feel",
        ],
        default=["no airbrush skin", "no plastic look", "no text", "no watermark"],
        help="Wähle was NICHT im Bild sein soll."
    )
    neg_custom = st.text_input("Eigene Ausschlüsse (optional)",
                               placeholder="z.B. no hat, no sunglasses...",
                               key="neg_custom_input")
    # Combine
    neg_parts = list(neg_presets)
    if neg_custom and neg_custom.strip():
        neg_parts.append(neg_custom.strip())
    negative_prompt = ", ".join(neg_parts) if neg_parts else ""

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
st.markdown('<div class="section-card"><h3>🎬 Veo3 Video-Generation</h3></div>', unsafe_allow_html=True)
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

    # Head, Face & Micro-Movements (separate row)
    st.markdown("**Kopf, Gesicht & Micro-Movements**")
    h1, h2, h3 = st.columns(3)

    with h1:
        head_movement = st.selectbox("Kopfbewegung", [
            "Keine (statisch)",
            "Slow head turn to camera",
            "Slow head turn away from camera",
            "Gentle head tilt to one side",
            "Chin up (confident / proud)",
            "Chin down, eyes up (seductive)",
            "Head follows product in hand",
            "Subtle nod (agreeing / confident)",
            "Head sway side to side (relaxed)",
            "Looks down then up to camera (reveal)"
        ])

        head_speed = st.select_slider("Kopf-Tempo",
                                      options=["Ultra Slow", "Slow", "Natural", "Quick"],
                                      value="Slow")

    with h2:
        eye_movement = st.selectbox("Augen / Blick-Animation", [
            "Keine (fixiert)",
            "Slow eye contact to camera (the look)",
            "Eyes wander, then lock on camera",
            "Blink naturally (2-3 times)",
            "Slow deliberate blink (sensual)",
            "Eyes follow product / hand movement",
            "Squint slightly (sun / intensity)",
            "Eyes widen (surprise / excitement)",
            "Look down at product, then up"
        ])

        eyebrow_move = st.selectbox("Augenbrauen", [
            "Keine Bewegung",
            "Subtle raise (interested)",
            "One eyebrow up (playful / cheeky)",
            "Slight furrow (intense / focused)",
            "Raise then relax (surprised then calm)"
        ])

    with h3:
        mouth_movement = st.selectbox("Mund / Lippen", [
            "Keine Bewegung",
            "Subtle smile develops slowly",
            "Lips part slightly (sensual)",
            "Bites lower lip gently",
            "Smirk / half smile (one side)",
            "Mouth opens to slight laugh",
            "Licks lips subtly",
            "Pout / duck face (playful)"
        ])

        micro_expressions = st.multiselect("Micro-Expressions (mehrere wählbar)", [
            "Subtle breathing (chest rises)",
            "Jaw clench then relax",
            "Nostril flare (intensity)",
            "Swallow (throat movement)",
            "Shoulder shrug (casual)",
            "Deep breath in (anticipation)",
            "Neck stretch / tension release"
        ], help="Kleine Details die das Video lebendig machen.")


# --- 6. PRODUCT ONLY SHOT ---
st.markdown("---")
st.markdown('<div class="section-card"><h3>💎 Product Only Shot (ohne Model)</h3></div>', unsafe_allow_html=True)
use_product_only = st.checkbox("Product-Only Prompt aktivieren", value=False,
                               help="Erstellt einen separaten Prompt NUR für das Produkt – perfekt für Katalog, E-Commerce, Detail-Shots.")

if use_product_only:
    st.markdown("---")

    po1, po2 = st.columns(2)

    with po1:
        st.markdown("**Produkt-Details**")
        prod_name = st.text_input("Produktname", value=product if product else "",
                                  placeholder="z.B. Goldene Kette mit Diamant-Anhänger",
                                  key="prod_only_name")
        prod_description = st.text_area("Beschreibung (optional)",
                                        placeholder="z.B. 18K Gold, 2mm Gliederkette, runder Anhänger mit 0.5ct Diamant",
                                        height=80, key="prod_only_desc")
        prod_material = st.selectbox("Material", [
            "— Nicht angeben —",
            "Gold (glänzend)",
            "Gold (matt/gebürstet)",
            "Silber / Sterling Silver",
            "Rosegold",
            "Platin",
            "Edelstahl",
            "Leder",
            "Stoff / Textil",
            "Keramik",
            "Holz",
            "Glas / Kristall",
            "Kunststoff / Acryl",
            "Perlen",
            "Diamant / Edelsteine"
        ])
        if prod_material == "— Nicht angeben —":
            prod_material = ""

        prod_size_text = st.text_input("Größe (optional)", placeholder="z.B. 45cm Kette, Anhänger 1.5cm",
                                       key="prod_only_size")

        st.markdown("---")
        st.markdown("**📸 Referenzbilder**")
        use_prod_ref = st.checkbox("Referenzbilder verwenden", value=False,
                                   help="Lade deine Produktbilder hoch — sie werden direkt an Gemini gesendet.")
        if use_prod_ref:
            prod_ref_files = st.file_uploader(
                "Referenzbilder hochladen (max. 4)",
                type=["png", "jpg", "jpeg", "webp"],
                accept_multiple_files=True,
                key="prod_ref_upload",
                help="2-4 Bilder deines Produkts aus verschiedenen Winkeln."
            )
            if prod_ref_files and len(prod_ref_files) > 4:
                st.warning("Maximal 4 Bilder! Nur die ersten 4 werden verwendet.")
                prod_ref_files = prod_ref_files[:4]

            prod_ref_angles = st.multiselect("Welche Ansichten zeigen deine Bilder?", [
                "Front view",
                "Side view",
                "Back view",
                "Close-up detail",
                "Full product overview",
                "Worn / in use"
            ], default=["Front view", "Close-up detail"])

            # Preview uploaded images
            if prod_ref_files:
                st.markdown(f"**{len(prod_ref_files)} Bild(er) hochgeladen:**")
                preview_cols = st.columns(min(len(prod_ref_files), 4))
                for idx, f in enumerate(prod_ref_files):
                    with preview_cols[idx % 4]:
                        st.image(f, caption=f"Ref #{idx+1}", use_container_width=True)
                prod_ref_count = len(prod_ref_files)
            else:
                prod_ref_count = 0
        else:
            prod_ref_files = []
            prod_ref_count = 0
            prod_ref_angles = []

    with po2:
        st.markdown("**Platzierung & Präsentation**")
        prod_placement = st.selectbox("Wie liegt / schwebt das Produkt?", [
            "Floating in air (schwebend, freistehend)",
            "Lying flat on surface",
            "Draped over curved fabric (Stoff-Wölbung)",
            "Hanging / suspended from above",
            "Standing upright on display",
            "Resting on stone / marble slab",
            "Placed on wooden surface",
            "Nestled in velvet box / cushion",
            "Wrapped around display bust (Schmuck-Büste)",
            "Scattered artfully (mehrere Teile)",
            "In hand (close-up, no face)",
            "On mirror surface (Spiegelung)"
        ])

        prod_arrangement = st.selectbox("Anordnung", [
            "Single Hero Product",
            "Product + Packaging",
            "Multiple color variants side by side",
            "Flat Lay (Draufsicht, mehrere Items)",
            "Stacked / layered"
        ])

        prod_angle = st.selectbox("Kamera-Winkel", [
            "Straight on (Augenhöhe)",
            "Slightly above (30°, klassisch)",
            "Top down / Bird's eye (90°)",
            "Low angle (von unten, dramatisch)",
            "45° angle (dynamisch)",
            "Macro extreme close-up"
        ])

    st.markdown("---")
    po3, po4 = st.columns(2)

    with po3:
        st.markdown("**Oberfläche & Untergrund**")
        prod_surface = st.selectbox("Untergrund-Material", [
            "— Keiner (schwebend) —",
            "Weißer Marmor",
            "Schwarzer Marmor",
            "Helles Holz (Eiche / Birke)",
            "Dunkles Holz (Walnuss / Mahagoni)",
            "Beton / Concrete",
            "Samt / Velvet (schwarz)",
            "Samt / Velvet (bordeaux)",
            "Samt / Velvet (navy)",
            "Seide / Silk (weiß)",
            "Seide / Silk (champagner)",
            "Leinen / Linen (naturfarben)",
            "Wasser / Wassertropfen",
            "Sand",
            "Blütenblätter",
            "Spiegel / reflektierende Oberfläche"
        ])

        if "Samt" in prod_surface or "Seide" in prod_surface or "Leinen" in prod_surface:
            fabric_drape = st.selectbox("Stoff-Form", [
                "Flat / flach ausgelegt",
                "Soft wave / sanfte Wölbung",
                "Deep folds / tiefe Falten",
                "Crumpled / leicht zerknittert (lässig)",
                "Tightly wrapped around object"
            ])
        else:
            fabric_drape = None

        prod_props = st.text_input("Deko / Props (optional)",
                                   placeholder="z.B. Eukalyptus-Zweige, Wassertropfen, Rosenblätter, Kerzen",
                                   key="prod_only_props")

    with po4:
        st.markdown("**Licht & Atmosphäre**")
        prod_lighting = st.selectbox("Beleuchtung", [
            "Clean Studio Softbox (klassisch)",
            "Dramatic Side Light",
            "Backlit / Rim Light (Halo)",
            "Golden Hour Warm Light",
            "Cool Daylight (neutral)",
            "Spotlight on black (Theater)",
            "Neon Glow (bunt)",
            "Window Light (natürlich, soft)"
        ], key="prod_only_light")

        prod_reflections = st.selectbox("Reflexionen", [
            "— Standard —",
            "Strong mirror reflections",
            "Subtle soft reflections",
            "Wet / glossy surface reflections",
            "No reflections (matte look)"
        ])
        if prod_reflections == "— Standard —":
            prod_reflections = ""

        prod_shadow = st.selectbox("Schatten", [
            "Soft diffused shadow",
            "Hard dramatic shadow",
            "No shadow (floating / clean)",
            "Contact shadow only (minimal)",
            "Long cinematic shadow"
        ])

        prod_color_mood = st.selectbox("Farbstimmung", [
            "— Neutral —",
            "Warm & luxurious (gold tones)",
            "Cool & modern (blue/silver tones)",
            "Earthy & natural (beige/green)",
            "High contrast B&W",
            "Pastel & soft",
            "Dark & moody",
            "Vibrant & colorful"
        ])
        if prod_color_mood == "— Neutral —":
            prod_color_mood = ""

    st.markdown("---")
    po5, po6 = st.columns(2)

    with po5:
        st.markdown("**Hintergrund**")
        prod_bg_type = st.selectbox("Hintergrund-Typ", [
            "Seamless white (E-Commerce Standard)",
            "Seamless black (Luxury)",
            "Gradient (hell nach dunkel)",
            "Gradient (dunkel nach hell)",
            "Textured wall (Betonwand)",
            "Blurred nature (Bokeh Grün)",
            "Blurred city lights (Bokeh)",
            "Solid color",
            "Matching surface extends to background"
        ], key="prod_only_bg")

        if prod_bg_type == "Solid color":
            prod_bg_color = st.color_picker("Hintergrund-Farbe", "#1a1a2e", key="prod_bg_col")
            prod_bg_final = f"Solid {prod_bg_color} background"
        elif prod_bg_type == "Matching surface extends to background":
            prod_bg_final = f"Background seamlessly extends from the {prod_surface} surface, creating an infinite surface look"
        else:
            prod_bg_final = prod_bg_type

    with po6:
        st.markdown("**Format & Extras**")
        prod_ar = st.selectbox("Bildformat", [
            "Quadrat (1:1) — Instagram / Katalog",
            "Hochformat (4:5) — Instagram Post",
            "Hochformat (9:16) — Story / Reels",
            "Querformat (16:9) — Website Banner",
            "Querformat (3:2) — Klassisch"
        ], key="prod_only_ar")

        prod_lens = st.selectbox("Objektiv", [
            "100mm Macro (extreme Detail)",
            "85mm (classic product)",
            "50mm (natural perspective)",
            "35mm (context / lifestyle)"
        ], key="prod_only_lens")

        prod_dof = st.selectbox("Tiefenschärfe", [
            "Everything sharp (f/8-f/11)",
            "Soft background blur (f/2.8)",
            "Extreme bokeh, only product sharp (f/1.4)",
            "Tilt-shift miniature effect"
        ], key="prod_only_dof")

        st.markdown("**🚫 Negativ-Prompt**")
        prod_neg_presets = st.multiselect(
            "Ausschlüsse",
            [
                "no people",
                "no hands",
                "no text",
                "no watermark",
                "no logo",
                "no blurry details",
                "no AI-generated look",
                "no oversaturated colors",
                "no cartoonish style",
                "no flat lighting",
                "no harsh shadows",
                "no distracting background",
                "no dust or scratches",
            ],
            default=["no people", "no hands", "no text", "no watermark", "no logo"],
            key="prod_neg_presets"
        )
        prod_neg_custom = st.text_input("Eigene Ausschlüsse (optional)",
                                        placeholder="z.B. no packaging...",
                                        key="prod_neg_custom")
        prod_neg_parts = list(prod_neg_presets)
        if prod_neg_custom and prod_neg_custom.strip():
            prod_neg_parts.append(prod_neg_custom.strip())
        prod_negative = ", ".join(prod_neg_parts) if prod_neg_parts else ""


# --- 7. AD CREATIVE GENERATOR ---
st.markdown("---")
st.markdown('<div class="section-card"><h3>🎯 Ad Creative Generator — Facebook & Instagram Ads</h3></div>', unsafe_allow_html=True)
use_ad_creative = st.checkbox("Ad Creative Modus aktivieren", value=False,
                              help="Generiert fertige Werbe-Creatives für Facebook & Instagram Ads mit Text-Overlay, CTA und Zielgruppen-Optimierung.")

if use_ad_creative:
    st.markdown("---")

    ad1, ad2 = st.columns(2)

    with ad1:
        st.markdown("**🎨 Ad-Typ & Stil**")
        ad_type = st.selectbox("Werbe-Typ", [
            "💛 Emotional / Storytelling",
            "⭐ Social Proof / Testimonial",
            "🔥 Urgency / Limited Offer",
            "✨ Lifestyle / Aspirational",
            "💎 Product Hero / Close-Up",
            "🎁 Geschenk-Guide",
            "📖 Educational / Craftsmanship",
        ], help="Der Werbe-Typ bestimmt Bildstil, Textton und Komposition.")

        ad_mood = st.selectbox("Stimmung / Mood", [
            "Warm & Einladend",
            "Luxuriös & Elegant",
            "Jung & Trendig",
            "Romantisch & Verträumt",
            "Bold & Selbstbewusst",
            "Minimalistisch & Clean",
            "Festlich / Saisonal",
        ])

        ad_format = st.selectbox("Ad Format", [
            "Facebook Feed (1:1 Quadrat)",
            "Facebook Feed (4:5 Hochformat)",
            "Instagram Story / Reels (9:16)",
            "Facebook Cover / Banner (16:9)",
            "Carousel Einzelbild (1:1)",
        ])

        is_personalizable = st.checkbox("🏷️ Produkt ist personalisierbar", value=True,
                                        help="Wenn aktiviert, wird 'Personalisierbar' als Selling Point eingebaut.")

        st.markdown("**📐 Anhänger-/Produkt-Maße**")
        ad_use_dimensions = st.checkbox("Maße angeben", value=False, key="ad_use_dims",
                                        help="Exakte Maße damit die Kette/der Anhänger nicht vergrößert dargestellt wird.")
        if ad_use_dimensions:
            ad_dim1, ad_dim2 = st.columns(2)
            with ad_dim1:
                ad_pendant_width = st.number_input("Breite (mm)", min_value=1.0, max_value=100.0, value=15.0, step=0.5, key="ad_pw")
            with ad_dim2:
                ad_pendant_height = st.number_input("Höhe (mm)", min_value=1.0, max_value=100.0, value=20.0, step=0.5, key="ad_ph")
            ad_chain_length = st.number_input("Kettenlänge (cm, optional)", min_value=0.0, max_value=100.0, value=45.0, step=1.0, key="ad_cl")
        else:
            ad_pendant_width, ad_pendant_height, ad_chain_length = None, None, None

    with ad2:
        st.markdown("**👥 Zielgruppe**")
        ad_target = st.selectbox("Primäre Zielgruppe", [
            "👩 Frauen 18-24 (Trend & Self-Treat)",
            "👩 Frauen 25-34 (Lifestyle & Everyday Luxury)",
            "👩 Frauen 35-50 (Eleganz & Qualität)",
            "👨 Männer (Geschenk für Partnerin)",
            "💍 Verlobung / Hochzeit",
            "🎁 Muttertag / Valentinstag / Weihnachten",
            "🎓 Abschluss / Milestone-Geschenk",
            "👫 Paare (Matching / Partnergeschenk)",
        ])

        ad_season = st.selectbox("Saison / Anlass (optional)", [
            "— Kein spezifischer Anlass —",
            "💝 Valentinstag",
            "🌸 Muttertag",
            "🎄 Weihnachten",
            "🎃 Black Friday / Cyber Monday",
            "☀️ Sommer / Festival",
            "🍂 Herbst / Back to School",
            "💍 Hochzeitssaison",
            "🎆 Neujahr",
        ])

        ad_price_point = st.selectbox("Preis-Segment", [
            "💰 Budget-friendly (unter 50€)",
            "💎 Mid-range (50-150€)",
            "👑 Premium / Luxury (150€+)",
        ])

    st.markdown("---")
    ad3, ad4 = st.columns(2)

    with ad3:
        st.markdown("**📝 Text-Overlay auf dem Bild**")
        ad_headline = st.text_input("Headline (Haupttext auf dem Bild)",
                                    placeholder="z.B. Dein Name. Dein Style.",
                                    key="ad_headline",
                                    help="Kurz & knackig. Wird prominent auf dem Bild platziert.")
        ad_subline = st.text_input("Subline (optional)",
                                   placeholder="z.B. Handgefertigt. Einzigartig wie du.",
                                   key="ad_subline")
        ad_cta = st.selectbox("Call-to-Action", [
            "Jetzt entdecken →",
            "Shop Now →",
            "Jetzt bestellen",
            "Sichere dir deins",
            "Zum Shop →",
            "Gratis Versand sichern",
            "Jetzt personalisieren",
            "Nur noch heute!",
            "Custom...",
        ])
        if ad_cta == "Custom...":
            ad_cta = st.text_input("Eigener CTA", placeholder="z.B. Jetzt -20% sichern",
                                   key="ad_cta_custom")

        ad_offer = st.text_input("Angebot / Rabatt (optional)",
                                 placeholder="z.B. -20% mit Code LOVE20, Gratis Versand ab 50€",
                                 key="ad_offer")

    with ad4:
        st.markdown("**📸 Bild-Komposition**")
        ad_composition = st.selectbox("Layout", [
            "Close-Up Produkt + Text oben/unten",
            "Model trägt Produkt + Text-Overlay",
            "Split: Links Model, Rechts Produkt-Detail",
            "Lifestyle-Szene + dezenter Text",
            "Produkt auf Hintergrund + große Headline",
            "Vorher/Nachher (ohne/mit Schmuck)",
        ])

        ad_text_position = st.selectbox("Text-Position", [
            "Oben (über dem Bild)",
            "Unten (unter dem Produkt)",
            "Mittig (Overlay auf Bild)",
            "Links (Text links, Bild rechts)",
            "Minimal (nur kleiner CTA-Button)",
        ])

        ad_color_scheme = st.selectbox("Farbschema", [
            "Brand Gold (#FFD700 auf Dunkel)",
            "Weiß & Clean (heller Hintergrund)",
            "Schwarz & Luxus (dunkler Hintergrund)",
            "Rosé / Pastelltöne",
            "Natur / Erdtöne",
            "Kräftige Farben (Pop Art Style)",
        ])

        ad_font = st.selectbox("Schriftart für Text-Overlay", [
            "Elegant Serif (Playfair Display / Didot)",
            "Modern Sans-Serif (Montserrat / Helvetica)",
            "Luxury Thin (Futura Light / Gill Sans)",
            "Handwritten / Script (Parisienne / Great Vibes)",
            "Bold Impact (Bebas Neue / Oswald)",
            "Minimalist (Inter / DM Sans)",
        ], help="Beeinflusst wie der Text auf dem Bild gerendert wird.")

        ad_ref_files = st.file_uploader(
            "Produkt-Referenzbilder für Ad (max. 4)",
            type=["png", "jpg", "jpeg", "webp"],
            accept_multiple_files=True,
            key="ad_ref_upload",
            help="💡 Tipp: Lade mindestens 1 Bild hoch wo der Schmuck GETRAGEN wird — das hilft bei der Größen-Proportion!"
        )
        if ad_ref_files and len(ad_ref_files) > 4:
            st.warning("Maximal 4 Bilder!")
            ad_ref_files = ad_ref_files[:4]

    # --- NEW ROW: Funnel Stage & Conversion Triggers ---
    st.markdown("---")
    ad5, ad6 = st.columns(2)

    with ad5:
        st.markdown("**🎯 Funnel-Stage & Hook**")
        ad_funnel = st.selectbox("Funnel-Stage", [
            "🔝 TOFU — Cold Audience (Aufmerksamkeit gewinnen)",
            "🔄 MOFU — Warm Audience (Vertrauen aufbauen)",
            "🔥 BOFU — Hot Audience / Retargeting (Kauf auslösen)",
        ], help="TOFU: Brand Discovery. MOFU: Consideration. BOFU: Conversion/Retargeting.")

        ad_hook = st.selectbox("Scroll-Stopper / Hook", [
            "Kontrast (Vorher/Nachher, mit/ohne Schmuck)",
            "Extreme Close-Up (Makro-Detail als Blickfang)",
            "Unerwarteter Winkel (von unten, Spiegelung, etc.)",
            "Emotionaler Moment (Freudentränen, Überraschung)",
            "Bold Text First (große Headline dominiert)",
            "Produkt in Bewegung (Glitzern, Licht-Reflexe)",
            "Social Proof (Sternebewertung, Kundenzitat)",
            "Luxus-Setting (Champagner, Rosenblätter, Samt)",
        ], help="Der 'Hook' ist das Element das in den ersten 0.5 Sekunden die Aufmerksamkeit fängt.")

        ad_trust_signals = st.multiselect("Vertrauens-Signale (auf dem Bild)", [
            "⭐ 5-Sterne-Bewertung",
            "❤️ 'Bestseller' Badge",
            "🚚 'Gratis Versand' Badge",
            "🔒 'Sicher bezahlen' Icon",
            "🏷️ Preis auf dem Bild",
            "📦 '1000+ verkauft'",
            "✅ 'Handgefertigt' Siegel",
            "↩️ 'Kostenlose Rückgabe'",
        ], help="Trust-Badges auf dem Bild erhöhen die Conversion-Rate signifikant.")

    with ad6:
        st.markdown("**🎠 Carousel-Modus**")
        ad_carousel = st.checkbox("Carousel Ad (mehrere Slides)", value=False,
                                  help="Generiert 3-5 zusammengehörige Slides für Facebook/Instagram Carousel Ads.")

        if ad_carousel:
            ad_carousel_count = st.select_slider("Anzahl Slides", options=[3, 4, 5], value=4)
            ad_carousel_story = st.selectbox("Carousel-Story-Typ", [
                "🎬 Produkt-Journey (Detail → Am Model → Lifestyle → CTA)",
                "💝 Emotionale Story (Geschenk-Moment Schritt für Schritt)",
                "🎨 Varianten-Showcase (Farben / Styles nebeneinander)",
                "📖 Feature-Walkthrough (Material → Gravur → Verpackung → Preis)",
                "⭐ Social Proof Carousel (Kundenbild → Review → Produkt → CTA)",
                "🔍 Zoom-Reveal (Weit → Nah → Makro → Am Model)",
            ])
            ad_carousel_cta_last = st.checkbox("Letzte Slide = CTA-Slide", value=True,
                                               help="Die letzte Slide enthält einen starken Call-to-Action.")
        else:
            ad_carousel_count = 1
            ad_carousel_story = ""
            ad_carousel_cta_last = False

        st.markdown("**🧠 Conversion-Psychologie**")
        ad_psych_triggers = st.multiselect("Psychologische Trigger", [
            "⏰ Urgency (begrenzte Zeit)",
            "📉 Scarcity (nur noch X verfügbar)",
            "🎁 Reciprocity (Gratis-Geschenk bei Kauf)",
            "👥 Social Proof (andere kaufen das auch)",
            "💎 Exclusivity (Limited Edition / VIP)",
            "🪞 Self-Image (so sieht das an DIR aus)",
            "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)",
            "💰 Value Framing (Preis im Kontext: 'weniger als 1€/Tag')",
        ], default=["🪞 Self-Image (so sieht das an DIR aus)", "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)"],
           help="Psychologische Prinzipien die nachweislich Conversion steigern.")


# --- AD CREATIVE PROMPT BUILDER ---
def build_ad_creative_prompt():
    """Build a prompt for generating Facebook/Instagram Ad Creatives."""

    # Map ad format to aspect ratio
    format_map = {
        "Facebook Feed (1:1 Quadrat)": "1:1 (Square)",
        "Facebook Feed (4:5 Hochformat)": "4:5 (Portrait)",
        "Instagram Story / Reels (9:16)": "9:16 (Vertical / Full Screen)",
        "Facebook Cover / Banner (16:9)": "16:9 (Landscape / Banner)",
        "Carousel Einzelbild (1:1)": "1:1 (Square)",
    }
    ad_ar = format_map.get(ad_format, "1:1 (Square)")

    # Map ad type to visual style instructions
    type_instructions = {
        "💛 Emotional / Storytelling": (
            "VISUAL STYLE: Warm, cinematic storytelling. Show a genuine emotional moment — "
            "a woman touching her necklace while looking in the mirror, receiving the jewelry as a gift, "
            "or a candid moment of joy. The image should evoke FEELING, not just show a product. "
            "Soft, warm lighting. Golden hour tones. Slightly shallow depth of field for dreamy quality."
        ),
        "⭐ Social Proof / Testimonial": (
            "VISUAL STYLE: Authentic, relatable look. Show a real-looking woman wearing the jewelry "
            "in an everyday setting — coffee shop, living room, walking outside. Natural lighting, "
            "slightly less polished than editorial — should feel like a real customer photo or UGC (user-generated content). "
            "Warm and approachable, not overly styled."
        ),
        "🔥 Urgency / Limited Offer": (
            "VISUAL STYLE: High-impact, attention-grabbing. Bold composition with the product prominently displayed. "
            "Dynamic lighting with strong contrast. The image should feel URGENT and exciting. "
            "Clean background so text overlay is readable. Studio-quality product shot with dramatic lighting."
        ),
        "✨ Lifestyle / Aspirational": (
            "VISUAL STYLE: Aspirational lifestyle imagery. Beautiful model in a luxurious or desirable setting — "
            "rooftop, designer apartment, sun-drenched terrace, elegant restaurant. The jewelry is part of a "
            "complete aspirational look. Fashion-editorial quality. Rich colors, perfect styling."
        ),
        "💎 Product Hero / Close-Up": (
            "VISUAL STYLE: Product is the absolute hero. Extreme close-up or macro shot of the jewelry. "
            "Every detail visible — metal texture, engraving, gemstone facets, chain links. "
            "Clean, minimal background. Professional product photography with perfect lighting. "
            "The product should fill 60-70% of the frame."
        ),
        "🎁 Geschenk-Guide": (
            "VISUAL STYLE: Gift-giving scene. Show the jewelry in beautiful packaging — gift box, "
            "ribbon, tissue paper. Or a moment of gifting — hands opening a box, surprise expression. "
            "Warm, festive lighting. Should trigger the emotion of GIVING and RECEIVING a special gift."
        ),
        "📖 Educational / Craftsmanship": (
            "VISUAL STYLE: Behind-the-scenes, artisan quality focus. Close-up of the jewelry showing "
            "craftsmanship details — handmade texture, hallmarks, material quality. "
            "Clean, informational composition that highlights QUALITY and CRAFTSMANSHIP. "
            "Studio lighting that reveals every detail of the material and workmanship."
        ),
    }
    style_instr = type_instructions.get(ad_type, type_instructions["✨ Lifestyle / Aspirational"])

    # Map mood
    mood_map = {
        "Warm & Einladend": "COLOR MOOD: Warm golden tones, honey-colored lighting, cozy and inviting atmosphere.",
        "Luxuriös & Elegant": "COLOR MOOD: Rich, deep tones. Black, gold, champagne. Luxury feel with high contrast.",
        "Jung & Trendig": "COLOR MOOD: Fresh, vibrant. Bright natural light, clean whites, pops of color. Modern and youthful.",
        "Romantisch & Verträumt": "COLOR MOOD: Soft pastels, rose tones, dreamy bokeh. Gentle, ethereal quality.",
        "Bold & Selbstbewusst": "COLOR MOOD: Strong contrast, saturated colors, powerful lighting. Confident and bold.",
        "Minimalistisch & Clean": "COLOR MOOD: Neutral tones, lots of whitespace, minimal distractions. Ultra-clean aesthetic.",
        "Festlich / Saisonal": "COLOR MOOD: Festive atmosphere — sparkle, warmth, celebration. Rich reds, golds, greens depending on season.",
    }
    mood_instr = mood_map.get(ad_mood, "")

    # Map target audience to model/scene description
    target_map = {
        "👩 Frauen 18-24 (Trend & Self-Treat)": "MODEL: Young woman, early 20s, trendy and confident. Casual-chic styling. Relatable, not overly glamorous.",
        "👩 Frauen 25-34 (Lifestyle & Everyday Luxury)": "MODEL: Woman in her late 20s to early 30s. Stylish, put-together but natural. Modern professional or lifestyle setting.",
        "👩 Frauen 35-50 (Eleganz & Qualität)": "MODEL: Elegant woman in her late 30s to 40s. Sophisticated, timeless styling. Quality and refinement are key.",
        "👨 Männer (Geschenk für Partnerin)": "SCENE: Focus on the gift-giving moment — hands holding a jewelry box, or the jewelry beautifully presented as a gift. Masculine hands opening/presenting. Warm, romantic lighting.",
        "💍 Verlobung / Hochzeit": "SCENE: Romantic, wedding-adjacent setting. White, gold, floral elements. Dreamy, fairy-tale quality. Focus on rings or bridal jewelry.",
        "🎁 Muttertag / Valentinstag / Weihnachten": "SCENE: Gift-giving moment appropriate for the occasion. Festive elements, warm family/romantic atmosphere. Emotional resonance.",
        "🎓 Abschluss / Milestone-Geschenk": "SCENE: Celebration moment. Young woman wearing the jewelry proudly. Achievement, pride, new chapter feeling.",
        "👫 Paare (Matching / Partnergeschenk)": "SCENE: Two people, romantic setting. Focus on matching or complementary jewelry pieces. Connection and togetherness.",
    }
    target_instr = target_map.get(ad_target, "")

    # Composition instructions
    comp_map = {
        "Close-Up Produkt + Text oben/unten": "COMPOSITION: Tight close-up of the jewelry product filling the center of the frame. Leave clear space at top and bottom for text overlay. Clean, uncluttered background.",
        "Model trägt Produkt + Text-Overlay": "COMPOSITION: Medium shot of model wearing the jewelry. Product clearly visible. Leave breathing room around edges for text overlay. Model slightly off-center.",
        "Split: Links Model, Rechts Produkt-Detail": "COMPOSITION: Split composition — left half shows the model wearing the jewelry (medium/close-up), right half shows an extreme close-up detail of the product. Visual divide in the middle.",
        "Lifestyle-Szene + dezenter Text": "COMPOSITION: Wide lifestyle scene with the model and product in a beautiful setting. Text will be small and positioned in a corner. Focus is on the aspirational image.",
        "Produkt auf Hintergrund + große Headline": "COMPOSITION: Product floating or placed on a clean background. Lots of negative space for large headline text. Product is centered, background is simple and elegant.",
        "Vorher/Nachher (ohne/mit Schmuck)": "COMPOSITION: Side-by-side or before/after style — left shows a bare neckline/wrist, right shows the same with the jewelry. Transformation and enhancement feel.",
    }
    comp_instr = comp_map.get(ad_composition, "")

    # Text overlay instructions with letter-by-letter spelling help
    text_elements = []

    def spell_out(text):
        """Create letter-by-letter spelling to help Gemini render text correctly."""
        return " — ".join(list(text))

    if ad_headline:
        text_elements.append(f'HEADLINE TEXT ON IMAGE: "{ad_headline}" (spelled: {spell_out(ad_headline)})')
    if ad_subline:
        text_elements.append(f'SUBLINE TEXT: "{ad_subline}" (spelled: {spell_out(ad_subline)})')
    if ad_cta:
        text_elements.append(f'CTA BUTTON/TEXT: "{ad_cta}" (spelled: {spell_out(ad_cta)})')
    if ad_offer:
        text_elements.append(f'OFFER BADGE: "{ad_offer}" (spelled: {spell_out(ad_offer)})')

    if text_elements:
        text_elements.append(
            'CRITICAL TEXT RENDERING RULE: Reproduce EVERY text element EXACTLY letter-by-letter as specified above. '
            'Do NOT rearrange, abbreviate, or rephrase any text. Do NOT add extra letters or skip any letters. '
            'Count the letters in each word and verify they match before rendering.'
        )

    # Personalization hint
    personalization_instr = ""
    if is_personalizable:
        personalization_instr = (
            "\nPERSONALIZATION SELLING POINT: This product is PERSONALIZABLE. "
            "Show or suggest personalization — e.g. a name engraved on the pendant, initials, custom text. "
            "If text is shown on the jewelry, use an example name like 'EMMA' or 'MIA'. "
            "Make it clear visually that this piece can be customized to the buyer's preference."
        )

    # Product dimensions
    dimensions_instr = ""
    if ad_use_dimensions and ad_pendant_width and ad_pendant_height:
        dimensions_instr = (
            f"\nPRODUCT DIMENSIONS — CRITICAL: The pendant/charm is exactly {ad_pendant_width}mm wide × {ad_pendant_height}mm tall. "
            f"This is VERY SMALL — roughly the size of a fingernail or small coin. "
            f"Render the pendant at its TRUE real-world size on the model's body. Do NOT enlarge, exaggerate, or make it more prominent. "
            f"On a human neck, a {ad_pendant_width}mm × {ad_pendant_height}mm pendant appears delicate and subtle."
        )
        if ad_chain_length and ad_chain_length > 0:
            dimensions_instr += f" The chain is {ad_chain_length}cm long, sitting {'at the collarbone' if ad_chain_length <= 40 else 'below the collarbone' if ad_chain_length <= 50 else 'at mid-chest level'}."

    # Season/occasion
    season_instr = ""
    if ad_season and "Kein" not in ad_season:
        season_clean = ad_season.split(" ", 1)[1] if " " in ad_season else ad_season
        season_instr = f"\nSEASONAL CONTEXT: This ad is for {season_clean}. Incorporate subtle seasonal elements in the styling, lighting, or props that evoke this occasion without being heavy-handed."

    # Color scheme
    color_map = {
        "Brand Gold (#FFD700 auf Dunkel)": "COLOR SCHEME: Dark background (near-black or deep navy), gold accent elements. Luxury and premium feel.",
        "Weiß & Clean (heller Hintergrund)": "COLOR SCHEME: Bright white or light cream background. Clean, airy, modern. Minimal color palette.",
        "Schwarz & Luxus (dunkler Hintergrund)": "COLOR SCHEME: Deep black background with dramatic lighting on the product. High-end, exclusive feel.",
        "Rosé / Pastelltöne": "COLOR SCHEME: Soft rose, blush pink, light lavender tones. Feminine, romantic, gentle.",
        "Natur / Erdtöne": "COLOR SCHEME: Warm earth tones — sand, terracotta, olive, warm brown. Natural, organic feel.",
        "Kräftige Farben (Pop Art Style)": "COLOR SCHEME: Bold, vibrant colors. High saturation, eye-catching. Modern and edgy.",
    }
    color_instr = color_map.get(ad_color_scheme, "")

    # Text position
    pos_map = {
        "Oben (über dem Bild)": "TEXT PLACEMENT: Reserve the top 25% of the image for text overlay. Keep this area simpler/darker for readability.",
        "Unten (unter dem Produkt)": "TEXT PLACEMENT: Reserve the bottom 25% of the image for text overlay. Keep bottom area simpler for readability.",
        "Mittig (Overlay auf Bild)": "TEXT PLACEMENT: Text will be overlaid in the center of the image. Ensure there's a semi-transparent area or natural dark/light zone for text readability.",
        "Links (Text links, Bild rechts)": "TEXT PLACEMENT: Left third of image should be simpler/darker for text. Main visual content on the right two-thirds.",
        "Minimal (nur kleiner CTA-Button)": "TEXT PLACEMENT: Only a small CTA button in the bottom-right corner. The image itself does all the talking.",
    }
    pos_instr = pos_map.get(ad_text_position, "")

    # Price segment styling
    price_map = {
        "💰 Budget-friendly (unter 50€)": "PRICE POSITIONING: Accessible, everyday luxury. Emphasize value and versatility. Approachable styling.",
        "💎 Mid-range (50-150€)": "PRICE POSITIONING: Quality meets style. Premium feel but still relatable. Everyday elegance.",
        "👑 Premium / Luxury (150€+)": "PRICE POSITIONING: High-end luxury. Exclusive, aspirational. Every element screams quality and craftsmanship.",
    }
    price_instr = price_map.get(ad_price_point, "")

    # Font style
    font_map = {
        "Elegant Serif (Playfair Display / Didot)": "elegant, high-contrast serif (like Playfair Display or Didot) — luxurious, editorial, classic",
        "Modern Sans-Serif (Montserrat / Helvetica)": "clean, geometric sans-serif (like Montserrat or Helvetica) — modern, professional, versatile",
        "Luxury Thin (Futura Light / Gill Sans)": "ultra-thin, refined sans-serif (like Futura Light or Gill Sans Light) — minimal, high-end, whisper-quiet elegance",
        "Handwritten / Script (Parisienne / Great Vibes)": "flowing script / handwritten (like Parisienne or Great Vibes) — personal, romantic, intimate",
        "Bold Impact (Bebas Neue / Oswald)": "bold, condensed display (like Bebas Neue or Oswald) — attention-grabbing, strong, urgent",
        "Minimalist (Inter / DM Sans)": "clean minimalist sans-serif (like Inter or DM Sans) — understated, modern, tech-forward",
    }
    font_instr = font_map.get(ad_font, "clean, modern sans-serif")

    # Funnel stage instruction
    funnel_map = {
        "🔝 TOFU — Cold Audience (Aufmerksamkeit gewinnen)": (
            "FUNNEL STAGE: TOP OF FUNNEL (Cold Audience). This person has NEVER seen your brand before. "
            "Priority: STOP THE SCROLL. Be visually striking, emotionally compelling, and curiosity-inducing. "
            "Do NOT hard-sell. Focus on aspiration, beauty, and brand impression. The goal is to make them REMEMBER you."
        ),
        "🔄 MOFU — Warm Audience (Vertrauen aufbauen)": (
            "FUNNEL STAGE: MIDDLE OF FUNNEL (Warm Audience). This person has seen the brand before but hasn't bought yet. "
            "Priority: BUILD TRUST. Show the product in real-life context, emphasize quality, craftsmanship, "
            "and social proof. Include trust signals. Make them WANT it and feel confident about the purchase."
        ),
        "🔥 BOFU — Hot Audience / Retargeting (Kauf auslösen)": (
            "FUNNEL STAGE: BOTTOM OF FUNNEL (Hot / Retargeting). This person has visited the site or added to cart. "
            "Priority: CONVERT NOW. Show the product prominently with a clear offer, urgency, or incentive. "
            "Remove any remaining hesitation. Strong CTA, clear price/offer, fast path to purchase."
        ),
    }
    funnel_instr = funnel_map.get(ad_funnel, "")

    # Hook / Scroll-Stopper
    hook_map = {
        "Kontrast (Vorher/Nachher, mit/ohne Schmuck)": "HOOK: Create visual CONTRAST — show the transformation. Before/after, with/without the jewelry. The difference should be immediately striking.",
        "Extreme Close-Up (Makro-Detail als Blickfang)": "HOOK: Start with an EXTREME CLOSE-UP of the jewelry. Macro-level detail that reveals beauty invisible to the naked eye. Gemstone facets, metal texture, engraving detail.",
        "Unerwarteter Winkel (von unten, Spiegelung, etc.)": "HOOK: Use an UNEXPECTED ANGLE that stops the scroll. Reflection in a mirror, shot from below looking up, dramatic perspective that makes the viewer look twice.",
        "Emotionaler Moment (Freudentränen, Überraschung)": "HOOK: Capture a genuine EMOTIONAL MOMENT — surprise, joy, tears of happiness. The human emotion IS the hook. The jewelry is the cause of the emotion.",
        "Bold Text First (große Headline dominiert)": "HOOK: The TEXT is the primary hook. Large, bold headline that makes a provocative statement or asks a question. The image supports the text, not the other way around.",
        "Produkt in Bewegung (Glitzern, Licht-Reflexe)": "HOOK: Show the product CATCHING LIGHT — the sparkle, the shimmer, light dancing across metal and gemstones. The visual 'glitter' effect is the scroll-stopper.",
        "Social Proof (Sternebewertung, Kundenzitat)": "HOOK: Lead with SOCIAL PROOF — a star rating, a customer quote, or a 'bestseller' badge. The credibility of others is the first thing the viewer sees.",
        "Luxus-Setting (Champagner, Rosenblätter, Samt)": "HOOK: Create a LUXURY ATMOSPHERE that triggers aspiration — velvet, champagne, rose petals, soft candlelight. The setting itself communicates premium value before the product is even noticed.",
    }
    hook_instr = hook_map.get(ad_hook, "")

    # Trust badges
    trust_badges_instr = ""
    if ad_trust_signals:
        badge_texts = [s.split(" ", 1)[1] if " " in s else s for s in ad_trust_signals]
        trust_badges_instr = (
            f"TRUST BADGES ON IMAGE: Include these trust elements visually on the image as small, "
            f"professional badges or icons: {', '.join(badge_texts)}. "
            f"Place them subtly (corner or edge) — they should be visible but not dominate the composition."
        )

    # Psychology triggers
    psych_instr = ""
    if ad_psych_triggers:
        trigger_details = {
            "⏰ Urgency (begrenzte Zeit)": "Create visual urgency — a timer, 'Nur heute', or limited-time visual cue",
            "📉 Scarcity (nur noch X verfügbar)": "Suggest scarcity — 'Fast ausverkauft' or 'Nur noch 3 verfügbar' visual element",
            "🎁 Reciprocity (Gratis-Geschenk bei Kauf)": "Show a free gift element — gift box, bonus item, or 'Gratis dazu' badge",
            "👥 Social Proof (andere kaufen das auch)": "Include social proof elements — customer count, reviews, or 'Beliebteste Wahl' badge",
            "💎 Exclusivity (Limited Edition / VIP)": "Communicate exclusivity — 'Limited Edition', 'Nur bei uns', premium packaging",
            "🪞 Self-Image (so sieht das an DIR aus)": "Help the viewer see THEMSELVES wearing this — relatable model, aspirational but achievable lifestyle",
            "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)": "Anchor to emotions — love, memory, milestone. The jewelry represents a FEELING, not just an object",
            "💰 Value Framing (Preis im Kontext: 'weniger als 1€/Tag')": "Frame the value — show what you GET, not what you pay. Emphasize quality-to-price ratio",
        }
        active_triggers = [trigger_details.get(t, "") for t in ad_psych_triggers if t in trigger_details]
        if active_triggers:
            psych_instr = "CONVERSION PSYCHOLOGY:\n" + "\n".join(f"- {t}" for t in active_triggers)

    # Build the full prompt
    prompt = f"""FACEBOOK / INSTAGRAM AD CREATIVE — {ad_ar}

PURPOSE: This is a paid advertising creative for Facebook/Instagram. It must STOP THE SCROLL — grab attention within 0.5 seconds in a fast-moving feed.

PRODUCT: '{product}'
{target_instr}

{style_instr}

{mood_instr}

{comp_instr}
{pos_instr}

{color_instr}
{price_instr}
{personalization_instr}
{dimensions_instr}
{season_instr}
{funnel_instr}
{hook_instr}

SKIN: Realistic skin with natural texture, visible pores, subtle imperfections. NO airbrushed, plastic, or CGI-looking skin.

{"TEXT ELEMENTS TO INCLUDE IN THE IMAGE:" if text_elements else ""}
{chr(10).join(text_elements)}
{trust_badges_instr}
{f"TYPOGRAPHY: Use a {font_instr} font style. Text must be HIGH CONTRAST against the background, easily readable at small sizes (mobile phone viewing). Kerning and spacing should be professional. If headline and subline are present, use clear size hierarchy." if text_elements else ""}
{"SPELLING — CRITICAL: All text rendered on the image MUST be spelled correctly. Double-check every word before rendering. Common German words that MUST be correct: 'Versand' (NOT Vershand), 'Geschenk' (NOT Geschnek), 'personalisierbar' (NOT personalisirbar), 'Halskette' (NOT Halskete), 'Anhänger' (NOT Anhenger), 'kostenlos' (NOT kostelos), 'einzigartig' (NOT einzigarig), 'handgefertigt' (NOT handgefertgt). If any text is in German, ensure PERFECT German spelling and grammar." if text_elements else ""}
{psych_instr}

AD CREATIVE REQUIREMENTS:
- The image must work as a standalone ad — it should communicate the product and value proposition visually
- Mobile-first: design for small screens, large clear visuals
- The product (jewelry) must be clearly visible and desirable
- Professional advertising quality — this should look like it was produced by a creative agency
- No generic stock photo feel — make it specific, intentional, and polished

NEGATIVE: no blurry text, no illegible fonts, no cluttered composition, no cheap-looking graphics, no watermarks, no AI-generated artifacts, no deformed hands or fingers

QUALITY: 8K resolution, professional advertising photography, editorial quality, perfect color grading, razor-sharp product detail."""

    # Clean up blank lines
    lines = prompt.split("\n")
    cleaned = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    return "\n".join(cleaned).strip()


def build_carousel_prompts():
    """Build a set of prompts for a Facebook/Instagram Carousel Ad."""

    base_prompt = build_ad_creative_prompt()

    # Story type determines what each slide shows
    story_slides = {
        "🎬 Produkt-Journey (Detail → Am Model → Lifestyle → CTA)": [
            "CAROUSEL SLIDE 1 — HOOK/DETAIL: Extreme close-up macro shot of the jewelry. Show the finest details — texture, engraving, gemstone facets, metal finish. This slide STOPS THE SCROLL with beauty.",
            "CAROUSEL SLIDE 2 — WORN: Medium close-up of the jewelry being worn by a model. Show how it looks on a real person — natural, elegant, desirable. Focus on the neckline/hand area with the product.",
            "CAROUSEL SLIDE 3 — LIFESTYLE: Wide lifestyle shot. The model wearing the jewelry in an aspirational setting — café, rooftop, sun-drenched terrace. The jewelry is part of a complete, desirable life.",
            "CAROUSEL SLIDE 4 — CTA: Clean product shot on minimal background with clear call-to-action text overlay. This slide drives the click. Product centered, text prominent.",
            "CAROUSEL SLIDE 5 — BONUS/OFFER: Gift packaging or special offer visual. Show the beautiful box/packaging or display a limited-time discount. Final push to convert.",
        ],
        "💝 Emotionale Story (Geschenk-Moment Schritt für Schritt)": [
            "CAROUSEL SLIDE 1 — ANTICIPATION: Beautiful gift box, wrapped with ribbon, perhaps with hands about to open it. Build anticipation and curiosity.",
            "CAROUSEL SLIDE 2 — REVEAL: The moment of opening — the jewelry revealed in its box. Sparkle, light catching the surface. The 'wow' moment.",
            "CAROUSEL SLIDE 3 — JOY: The emotional reaction — the recipient's face showing genuine happiness, surprise, or touched emotion while holding/wearing the piece.",
            "CAROUSEL SLIDE 4 — WORN: The jewelry now being worn proudly. A candid moment of the person admiring it, looking in a mirror, or being complimented.",
            "CAROUSEL SLIDE 5 — CTA: Product on clean background with text: the product name, key feature (e.g. 'personalisierbar'), and strong call-to-action.",
        ],
        "🎨 Varianten-Showcase (Farben / Styles nebeneinander)": [
            "CAROUSEL SLIDE 1 — HERO: The main/bestseller variant of the product, beautifully lit, on a clean background. The 'star' of the collection.",
            "CAROUSEL SLIDE 2 — VARIANT A: Second color/style variant. Same composition angle for visual consistency, different color (e.g. rosegold).",
            "CAROUSEL SLIDE 3 — VARIANT B: Third variant. Maintain the same visual style. Show diversity of the collection.",
            "CAROUSEL SLIDE 4 — GROUP: All variants together in one shot — arranged elegantly side by side. Shows the full range available.",
            "CAROUSEL SLIDE 5 — CTA: Model wearing one variant, with text encouraging to 'find your color' or 'choose your style'. Call-to-action.",
        ],
        "📖 Feature-Walkthrough (Material → Gravur → Verpackung → Preis)": [
            "CAROUSEL SLIDE 1 — MATERIAL: Extreme close-up showing material quality — the shine of gold, the texture of sterling silver. Text overlay: material name and quality (e.g. '925 Sterling Silver').",
            "CAROUSEL SLIDE 2 — CRAFT/DETAIL: Close-up of the craftsmanship — engraving, stone setting, chain links. Text: 'Handgefertigt' or key craft detail.",
            "CAROUSEL SLIDE 3 — PACKAGING: The product in its premium packaging — gift box, velvet pouch, branded elements. Shows the complete gifting experience.",
            "CAROUSEL SLIDE 4 — WORN: The product being worn, showing how it looks in real life. Relatable, aspirational.",
            "CAROUSEL SLIDE 5 — PRICE/CTA: Product with price displayed prominently. Any offer (free shipping, discount code). Strong CTA button.",
        ],
        "⭐ Social Proof Carousel (Kundenbild → Review → Produkt → CTA)": [
            "CAROUSEL SLIDE 1 — CUSTOMER: Authentic-looking customer photo (UGC-style) — someone wearing the jewelry in a casual, real-life setting. Not overly styled.",
            "CAROUSEL SLIDE 2 — REVIEW: Clean card-style layout with a 5-star review quote. Product small in corner. The review text is the hero.",
            "CAROUSEL SLIDE 3 — PRODUCT: Professional product shot — the item itself, beautifully lit, showing exactly what they'll receive.",
            "CAROUSEL SLIDE 4 — STATS: Social proof numbers — '1000+ glückliche Kunden', '4.9/5 Sterne', 'Bestseller 2025'. Clean infographic style.",
            "CAROUSEL SLIDE 5 — CTA: Product with offer and strong CTA. 'Jetzt selbst überzeugen' or similar.",
        ],
        "🔍 Zoom-Reveal (Weit → Nah → Makro → Am Model)": [
            "CAROUSEL SLIDE 1 — WIDE: Full scene — model in a beautiful setting, jewelry barely visible. Establishes mood and aspiration. Curiosity: what is she wearing?",
            "CAROUSEL SLIDE 2 — MEDIUM: Closer — portrait shot, the jewelry now visible on the neck/hand. Starting to see the design.",
            "CAROUSEL SLIDE 3 — CLOSE: Close-up of just the jewelry area — the pendant on the skin, the ring on the finger. Details becoming clear.",
            "CAROUSEL SLIDE 4 — MACRO: Extreme macro — individual chain links, gemstone facets, engraving letters. Maximum detail and beauty.",
            "CAROUSEL SLIDE 5 — CTA: Back to the full product shot with overlay text. Name, price, CTA. The viewer now appreciates every detail.",
        ],
    }

    slides = story_slides.get(ad_carousel_story, story_slides["🎬 Produkt-Journey (Detail → Am Model → Lifestyle → CTA)"])
    slides = slides[:ad_carousel_count]

    # If CTA on last slide is off, replace last slide instruction
    if not ad_carousel_cta_last and len(slides) > 1:
        slides[-1] = slides[-1].replace("CTA:", "FINAL:").replace("call-to-action", "closing visual")

    # Build individual prompts for each slide
    carousel_prompts = []
    for i, slide_instr in enumerate(slides):
        slide_prompt = f"""{base_prompt}

--- CAROUSEL CONTEXT ---
This is SLIDE {i+1} of {ad_carousel_count} in a Facebook/Instagram Carousel Ad.
{slide_instr}

CAROUSEL CONSISTENCY: All slides must share the same overall color palette, lighting mood, and brand feel.
The visual style must be CONSISTENT across all slides so they look like they belong together as a set.
Format: 1:1 (Square) — standard for Facebook/Instagram Carousel."""

        carousel_prompts.append(slide_prompt)

    return carousel_prompts
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
        size_ref = ""
        if use_size and obj_size:
            size_ref = (f" The product is exactly {obj_size}cm in real life. "
                        f"Render it at this EXACT real-world size relative to the human body — "
                        f"do NOT enlarge or shrink it. A {obj_size}cm pendant is SMALL and delicate on a human neck.")
        prod_instr = (f"The model wears/holds '{product}'. Use the provided REFERENCE IMAGE "
                      f"for exact product appearance — match the design, shape, color, texture, and proportions "
                      f"from the reference as closely as possible.{size_ref} "
                      f"Blend naturally into the scene.")
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
        quality_keywords=(
            "QUALITY: Editorial photograph quality, professional color grading, "
            "natural volumetric lighting, photorealistic skin texture, magazine cover quality. "
            "All products shown at their REAL physical size — do not enlarge jewelry or accessories."
            if "💎 Pro" in model_quality else
            "QUALITY KEYWORDS: 8K resolution, hyper-realistic, editorial quality, professional color grading, "
            "volumetric lighting, micro-detail rendering, photorealistic skin texture, magazine cover quality."
        ),
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
        # Head & Face
        has_head_movement=head_movement != "Keine (statisch)",
        head_movement=head_movement,
        head_speed=head_speed,
        has_eye_movement=eye_movement != "Keine (fixiert)",
        eye_movement=eye_movement,
        has_eyebrow=eyebrow_move != "Keine Bewegung",
        eyebrow_move=eyebrow_move,
        has_mouth=mouth_movement != "Keine Bewegung",
        mouth_movement=mouth_movement,
        micro_list=", ".join(micro_expressions) if micro_expressions else "",
        # Sound
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


def build_product_only_prompt():
    """Build a product-only prompt using the product template."""

    # Aspect ratio
    if "1:1" in prod_ar: par = "1:1 (Square)"
    elif "4:5" in prod_ar: par = "4:5 (Portrait)"
    elif "9:16" in prod_ar: par = "9:16 (Vertical)"
    elif "16:9" in prod_ar: par = "16:9 (Landscape)"
    elif "3:2" in prod_ar: par = "3:2 (Classic)"
    else: par = "1:1 (Square)"

    # Placement detail
    placement_detail = ""
    if "Floating" in prod_placement:
        placement_detail = "The product floats weightlessly in center frame, perfectly lit from all sides, with a subtle shadow beneath to ground it."
    elif "Draped" in prod_placement:
        placement_detail = f"Product draped naturally over curved {prod_surface} fabric, following the soft folds organically."
    elif "mirror" in prod_placement.lower():
        placement_detail = "Product sits on a reflective mirror surface, creating a perfect reflection beneath."
    elif fabric_drape:
        placement_detail = f"The {prod_surface} surface is shaped: {fabric_drape}. Product follows the natural contour of the fabric."

    # Surface as background detail
    prod_bg_detail = ""
    if prod_surface != "— Keiner (schwebend) —":
        prod_bg_detail = f"SURFACE: {prod_surface}."

    # Lighting detail
    light_details = {
        "Clean Studio Softbox (klassisch)": "Large softbox key light from above-right, fill light from left. Minimal shadows, even illumination.",
        "Dramatic Side Light": "Single hard light source from 90° to one side. Deep contrast, moody feel.",
        "Backlit / Rim Light (Halo)": "Strong backlight creating luminous edge around the product. Soft fill from front.",
        "Golden Hour Warm Light": "Warm directional light simulating late afternoon sun. Rich golden tones.",
        "Cool Daylight (neutral)": "Cool-toned neutral daylight. Clean, accurate color reproduction.",
        "Spotlight on black (Theater)": "Tight spotlight beam on product against pure black. Dramatic theater effect.",
        "Neon Glow (bunt)": "Colored neon light sources creating vivid reflections on the product surface.",
        "Window Light (natürlich, soft)": "Soft directional window light from one side. Natural, editorial feel.",
    }
    prod_lighting_detail = light_details.get(prod_lighting, "")

    prompt = PRODUCT_TEMPLATE.render(
        prod_aspect_ratio=par,
        prod_name=prod_name,
        prod_description=prod_description if prod_description else "",
        prod_material=prod_material,
        prod_size_info=prod_size_text if prod_size_text else "",
        has_reference=use_prod_ref,
        ref_count=prod_ref_count if use_prod_ref else 0,
        ref_angles=", ".join(prod_ref_angles) if use_prod_ref and prod_ref_angles else "",
        prod_placement=prod_placement,
        placement_detail=placement_detail,
        prod_arrangement=prod_arrangement,
        prod_angle=prod_angle,
        prod_lens=prod_lens,
        prod_dof=prod_dof,
        prod_lighting=prod_lighting,
        prod_lighting_detail=prod_lighting_detail,
        prod_reflections=prod_reflections,
        prod_bg=prod_bg_final,
        prod_bg_detail=prod_bg_detail,
        prod_props=prod_props if prod_props else "",
        prod_color_mood=prod_color_mood,
        prod_shadow=prod_shadow,
        prod_negative=prod_negative if prod_negative else "",
    )

    # Clean blank lines
    lines = prompt.split("\n")
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


def find_gemini_image_model(gemini_api_key, prefer_pro=False):
    """Find the correct Gemini model that supports image generation."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Different priority based on quality preference
        if prefer_pro:
            preferred_models = [
                "gemini-3-pro-image-preview",
                "gemini-2.5-flash-image",
                "gemini-2.5-flash-preview-image",
            ]
        else:
            preferred_models = [
                "gemini-2.5-flash-image",
                "gemini-2.5-flash-preview-image",
                "gemini-3-pro-image-preview",
                "gemini-2.0-flash-image",
                "gemini-2.0-flash",
            ]

        available = []
        for model in data.get("models", []):
            name = model.get("name", "").replace("models/", "")
            methods = model.get("supportedGenerationMethods", [])
            if "generateContent" in methods:
                available.append(name)

        # Try preferred models first
        for pref in preferred_models:
            for avail in available:
                if pref in avail:
                    return avail

        # Fallback: any model with "image" in name
        for avail in available:
            if "image" in avail.lower():
                return avail

        for avail in available:
            if "flash" in avail.lower() and "lite" not in avail.lower():
                return avail

        return None
    except Exception as e:
        st.error(f"Fehler beim Laden der Modell-Liste: {e}")
        return None


def generate_image_gemini(prompt_text, gemini_api_key, reference_images=None, aspect_ratio_str=None, prefer_pro=False):
    """Generate an image using Gemini (auto-detects best model). Supports reference images and quality settings."""

    # Detect if quality preference changed -> reset cached model
    quality_key = "pro" if prefer_pro else "flash"
    if st.session_state.get("gemini_quality_mode") != quality_key:
        st.session_state.gemini_model_name = None
        st.session_state.gemini_quality_mode = quality_key

    # Find correct model
    if "gemini_model_name" not in st.session_state or not st.session_state.gemini_model_name:
        with st.spinner("Suche bestes Gemini-Modell..."):
            model_name = find_gemini_image_model(gemini_api_key, prefer_pro=prefer_pro)
            if not model_name:
                st.error("❌ Kein Gemini-Modell mit Bildgenerierung gefunden. Prüfe deinen API Key.")
                return None, None
            st.session_state.gemini_model_name = model_name
            st.info(f"🤖 Verwende Modell: **{model_name}**")

    model = st.session_state.gemini_model_name
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"

    # Add sharpness boost to prompt
    # Different quality instructions for Flash vs Pro
    # Pro model tends to enlarge products when told to add "extreme detail" —
    # so we focus Pro instructions on SKIN/PHOTO quality, not product prominence
    if prefer_pro:
        quality_boost = (
            "\n\nQUALITY INSTRUCTIONS (Pro Model): Generate at maximum resolution. "
            "Focus on photographic realism: natural skin texture with visible pores, "
            "realistic lighting with proper highlights and shadows, accurate fabric draping, "
            "and professional color grading. The image should look like a high-end editorial photograph."
            "\n\nCRITICAL PRODUCT SCALE RULE: All jewelry, necklaces, pendants, rings, and accessories "
            "MUST appear at their TRUE real-world physical size relative to the human body. "
            "A typical necklace pendant is only 10-25mm (1-2.5cm) — it should appear SMALL and DELICATE "
            "on a human neck, NOT enlarged or exaggerated. A ring is thin and subtle on a finger. "
            "Do NOT make any product bigger, bolder, or more visually dominant than it would be "
            "in a real photograph. The product should be naturally proportioned — if you have to squint "
            "to see it in real life, it should be similarly subtle in the image. "
            "NEVER enlarge a product to make it more visible. Realism of scale is MORE important than product visibility."
            "\n\nTEXT SPELLING RULE: If ANY text appears in the image, it MUST be spelled 100% correctly. "
            "Check every letter carefully. No typos, no missing letters, no swapped letters. "
            "German text must use correct German spelling (e.g. 'Versand' not 'Vershand', "
            "'Geschenk' not 'Geschnek', 'kostenlos' not 'kostelos'). "
            "If unsure about a word, use simpler/shorter text instead."
        )
    else:
        quality_boost = (
            "\n\nIMPORTANT QUALITY INSTRUCTIONS: Generate at MAXIMUM available resolution. "
            "The image must be tack-sharp with extreme detail when zoomed in. "
            "Razor-sharp focus, no blur, no softness, no compression artifacts. "
            "Every texture, pore, fabric thread, and material grain must be crisply rendered. "
            "Professional retouching quality with pixel-perfect sharpness throughout the entire frame."
            "\n\nTEXT SPELLING RULE: If ANY text appears in the image, it MUST be spelled 100% correctly. "
            "Check every letter carefully. No typos, no missing letters, no swapped letters. "
            "German text must use correct German spelling (e.g. 'Versand' not 'Vershand', "
            "'Geschenk' not 'Geschnek', 'kostenlos' not 'kostelos'). "
            "If unsure about a word, use simpler/shorter text instead."
        )
    enhanced_prompt = prompt_text + quality_boost

    # Build parts: text prompt + reference images
    parts = [{"text": enhanced_prompt}]

    if reference_images:
        for ref_img in reference_images:
            img_bytes = ref_img.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")

            fname = ref_img.name.lower()
            if fname.endswith(".png"):
                mime = "image/png"
            elif fname.endswith(".webp"):
                mime = "image/webp"
            else:
                mime = "image/jpeg"

            parts.append({
                "inlineData": {
                    "mimeType": mime,
                    "data": img_b64
                }
            })

    # Build generation config — IMAGE only mode for better quality
    gen_config = {
        "responseModalities": ["IMAGE"],
    }

    # Map aspect ratio
    ar_map = {
        "16:9": "16:9",
        "9:16": "9:16",
        "1:1": "1:1",
        "21:9": "16:9",  # Fallback, 21:9 not always supported
        "4:5": "3:4",    # Closest match
        "3:2": "4:3",    # Closest match
    }
    image_config = {}
    if aspect_ratio_str:
        for key, val in ar_map.items():
            if key in aspect_ratio_str:
                image_config["aspectRatio"] = val
                break

    # Pro model supports higher resolution (1K, 2K, 4K)
    if prefer_pro and "pro" in model.lower():
        image_config["imageSize"] = "2K"

    if image_config:
        gen_config["imageConfig"] = image_config

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": gen_config,
    }

    headers = {"Content-Type": "application/json"}

    # Pro model needs longer timeout (2K generation can take 3-5 min)
    request_timeout = 300 if prefer_pro else 180

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=request_timeout)
        response.raise_for_status()
        data = response.json()

        # Extract image from response
        candidates = data.get("candidates", [])
        for candidate in candidates:
            content = candidate.get("content", {})
            parts_resp = content.get("parts", [])
            for part in parts_resp:
                if "inlineData" in part:
                    img_data = part["inlineData"]["data"]
                    mime_type = part["inlineData"].get("mimeType", "image/png")
                    img_bytes = base64.b64decode(img_data)
                    return img_bytes, mime_type

        # Check for blocked content
        block_reason = ""
        for candidate in candidates:
            if "finishReason" in candidate:
                block_reason = candidate["finishReason"]

        if block_reason:
            st.error(f"Gemini hat kein Bild generiert. Grund: {block_reason}. Versuche den Prompt anzupassen.")
        else:
            st.error("Gemini hat kein Bild zurückgegeben. Versuche den Prompt anzupassen.")
        return None, None

    except requests.exceptions.Timeout:
        # If Pro timed out, try again without high-res config
        if prefer_pro:
            st.warning("⏰ Pro-Modell Timeout bei hoher Auflösung — versuche Standard-Auflösung...")
            if "imageSize" in gen_config.get("imageConfig", {}):
                del gen_config["imageConfig"]["imageSize"]
            retry_payload = {
                "contents": [{"parts": parts}],
                "generationConfig": gen_config,
            }
            try:
                retry_resp = requests.post(url, json=retry_payload, headers=headers, timeout=180)
                retry_resp.raise_for_status()
                retry_data = retry_resp.json()
                for candidate in retry_data.get("candidates", []):
                    content = candidate.get("content", {})
                    for part in content.get("parts", []):
                        if "inlineData" in part:
                            img_data = part["inlineData"]["data"]
                            mime_type = part["inlineData"].get("mimeType", "image/png")
                            st.success("✅ Pro-Bild generiert (Standard-Auflösung)")
                            return base64.b64decode(img_data), mime_type
            except:
                pass
        st.error("⏰ Timeout — Gemini braucht zu lange. Bitte nochmal versuchen.")
        return None, None
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("error", {}).get("message", "")
        except:
            pass

        # If Pro fails with 400 (bad config), retry without imageSize
        if e.response.status_code == 400 and prefer_pro:
            st.warning("⚠️ Pro-Modell unterstützt diese Konfiguration nicht — versuche ohne Größen-Einstellung...")
            if "imageConfig" in gen_config:
                gen_config["imageConfig"] = {k: v for k, v in gen_config["imageConfig"].items()
                                             if k != "imageSize"}
            retry_payload = {
                "contents": [{"parts": parts}],
                "generationConfig": gen_config,
            }
            try:
                retry_resp = requests.post(url, json=retry_payload, headers=headers, timeout=240)
                retry_resp.raise_for_status()
                retry_data = retry_resp.json()
                for candidate in retry_data.get("candidates", []):
                    content = candidate.get("content", {})
                    for part in content.get("parts", []):
                        if "inlineData" in part:
                            img_data = part["inlineData"]["data"]
                            mime_type = part["inlineData"].get("mimeType", "image/png")
                            st.success("✅ Pro-Bild generiert (ohne Größen-Override)")
                            return base64.b64decode(img_data), mime_type
            except Exception as retry_e:
                st.error(f"Auch Retry fehlgeschlagen: {retry_e}")
                return None, None

        if e.response.status_code == 404:
            st.session_state.gemini_model_name = None
            st.error(f"Modell '{model}' nicht verfügbar. Bitte nochmal klicken — suche alternatives Modell.")
        elif e.response.status_code == 503 or e.response.status_code == 429:
            # Model overloaded — try fallback
            fallback_models = [
                "gemini-2.5-flash-image",
                "gemini-2.5-flash-preview-image",
                "gemini-2.0-flash",
            ]
            # Remove current model from fallbacks
            fallback_models = [m for m in fallback_models if m not in model]

            for fb in fallback_models:
                st.warning(f"⚡ {model} überlastet — versuche Fallback: **{fb}**...")
                fb_url = f"https://generativelanguage.googleapis.com/v1beta/models/{fb}:generateContent?key={gemini_api_key}"
                try:
                    fb_response = requests.post(fb_url, json=payload, headers=headers, timeout=180)
                    fb_response.raise_for_status()
                    fb_data = fb_response.json()

                    for candidate in fb_data.get("candidates", []):
                        content = candidate.get("content", {})
                        parts_resp = content.get("parts", [])
                        for part in parts_resp:
                            if "inlineData" in part:
                                img_data = part["inlineData"]["data"]
                                mime_type = part["inlineData"].get("mimeType", "image/png")
                                img_bytes_result = base64.b64decode(img_data)
                                st.session_state.gemini_model_name = fb
                                st.success(f"✅ Fallback erfolgreich mit **{fb}**")
                                return img_bytes_result, mime_type
                except:
                    continue

            st.error(f"Alle Modelle überlastet. Bitte in 1-2 Minuten nochmal versuchen.")
        else:
            st.error(f"Gemini API Fehler: {e}\n{error_detail}")
        return None, None
    except Exception as e:
        st.error(f"Fehler bei der Bildgenerierung: {e}")
        return None, None


def generate_video_veo(prompt_text, gemini_api_key):
    """Generate a video using Veo via the Gemini API. Returns video bytes or None."""
    import time as _time

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": gemini_api_key,
    }

    # Try Veo models in order
    veo_models = [
        "veo-3.0-generate-preview",
        "veo-3.1-generate-preview",
        "veo-2.0-generate-001",
    ]

    operation_name = None
    used_model = None

    for model in veo_models:
        url = f"{BASE_URL}/models/{model}:predictLongRunning"
        payload = {
            "instances": [{"prompt": prompt_text}],
            "parameters": {
                "personGeneration": "allow_all",
            }
        }
        # generateAudio only supported on veo-3.0
        if "3.0" in model:
            payload["parameters"]["generateAudio"] = True

        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code == 404:
                continue
            if resp.status_code == 503:
                continue
            resp.raise_for_status()
            data = resp.json()
            operation_name = data.get("name")
            used_model = model
            break
        except requests.exceptions.HTTPError as e:
            if e.response.status_code in [404, 503]:
                continue
            error_detail = ""
            try:
                error_detail = e.response.json().get("error", {}).get("message", "")
            except:
                pass
            st.error(f"Veo API Fehler ({model}): {e}\n{error_detail}")
            return None
        except Exception:
            continue

    if not operation_name:
        st.error("❌ Kein Veo-Modell verfügbar. Prüfe API Key und Billing.")
        return None

    st.info(f"🤖 Verwende: **{used_model}** — Operation: `{operation_name}`")

    # Poll for completion — use x-goog-api-key header
    poll_headers = {"x-goog-api-key": gemini_api_key}
    poll_url = f"{BASE_URL}/{operation_name}"

    progress_bar = st.progress(0, text="⏳ Video wird generiert...")
    status_text = st.empty()
    max_wait = 600  # 10 minutes
    elapsed = 0
    poll_interval = 10

    while elapsed < max_wait:
        _time.sleep(poll_interval)
        elapsed += poll_interval
        pct = min(elapsed / max_wait, 0.95)
        progress_bar.progress(pct, text=f"⏳ Video wird generiert... ({elapsed}s / max {max_wait}s)")

        try:
            poll_resp = requests.get(poll_url, headers=poll_headers, timeout=30)
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()

            is_done = poll_data.get("done", False)
            status_text.caption(f"Status: done={is_done} | Keys: {list(poll_data.keys())}")

            if is_done:
                progress_bar.progress(1.0, text="✅ Video fertig!")

                # Extract video from response
                response_obj = poll_data.get("response", {})

                # Try multiple known response structures
                video_samples = None

                # Structure 1: response.generateVideoResponse.generatedSamples
                gvr = response_obj.get("generateVideoResponse", {})
                if gvr:
                    video_samples = gvr.get("generatedSamples", [])

                # Structure 2: response.generatedSamples
                if not video_samples:
                    video_samples = response_obj.get("generatedSamples", [])

                # Structure 3: response.videos (Vertex style)
                if not video_samples:
                    video_samples = response_obj.get("videos", [])

                if video_samples:
                    sample = video_samples[0]
                    video_obj = sample.get("video", sample)

                    # Base64 encoded
                    if "bytesBase64Encoded" in video_obj:
                        video_bytes = base64.b64decode(video_obj["bytesBase64Encoded"])
                        return video_bytes

                    # URI to download
                    uri = video_obj.get("uri") or video_obj.get("gcsUri")
                    if uri:
                        status_text.caption(f"Downloading video from: {uri[:80]}...")
                        vid_resp = requests.get(uri, timeout=120)
                        vid_resp.raise_for_status()
                        return vid_resp.content

                # Debug: show full response structure
                st.warning(f"Video fertig, aber unbekanntes Format. Response-Keys: {list(response_obj.keys())}")
                st.json(poll_data)
                return None

            # Check for error in response
            if "error" in poll_data:
                err = poll_data["error"]
                st.error(f"Veo Fehler: {err.get('message', str(err))}")
                progress_bar.progress(1.0, text="❌ Fehler")
                return None

        except requests.exceptions.HTTPError as e:
            status_text.caption(f"Poll-Fehler ({elapsed}s): {e} — versuche weiter...")
            continue
        except Exception as e:
            status_text.caption(f"Poll-Fehler ({elapsed}s): {e} — versuche weiter...")
            continue

    progress_bar.progress(1.0, text="⏰ Timeout")
    st.error("Video-Generierung hat zu lange gedauert (>10 Min). Das kann bei hoher Nachfrage passieren. Bitte nochmal versuchen.")
    return None


# --- OUTPUT ---
st.markdown("---")

# Session state for generated prompts (so generate button can access them)
if "last_image_prompt" not in st.session_state:
    st.session_state.last_image_prompt = None
if "last_video_prompt" not in st.session_state:
    st.session_state.last_video_prompt = None
if "last_product_prompt" not in st.session_state:
    st.session_state.last_product_prompt = None
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []
if "generated_videos" not in st.session_state:
    st.session_state.generated_videos = []

# --- GENERATION MODE SELECTOR ---
st.markdown('<div class="section-card"><h3>🚀 Generieren</h3></div>', unsafe_allow_html=True)

if use_video:
    gen_mode = st.radio(
        "Was möchtest du generieren?",
        ["📷 Nur Foto", "🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"],
        index=2,
        horizontal=True,
        help="Wähle ob du ein Foto, einen Video-Prompt oder beides generieren willst."
    )
else:
    gen_mode = "📷 Nur Foto"

# Dynamic button text
if gen_mode == "📷 Nur Foto":
    btn_label = "🍌 FOTO-PROMPT GENERIEREN"
elif gen_mode == "🎬 Nur Video-Prompt":
    btn_label = "🎬 VIDEO-PROMPT GENERIEREN"
else:
    btn_label = "🍌🎬 FOTO + VIDEO PROMPT GENERIEREN"

if st.button(btn_label):
    if not product:
        st.warning("Bitte ein Produkt / Thema eingeben!")
    else:
        # Always build the base image prompt (needed for video too)
        with st.spinner("Baue Prompt..."):
            raw_prompt, reminder = build_prompt_local()

        # --- FOTO ---
        if gen_mode in ["📷 Nur Foto", "📷+🎬 Foto + Video"]:
            st.session_state.last_image_prompt = raw_prompt
            st.success("✅ Bild-Prompt generiert!")
            if reminder:
                st.info(reminder)
            st.markdown("### 📋 Bild-Prompt")
            st.code(raw_prompt, language="text")

        # --- VIDEO ---
        final_video_prompt = None
        if gen_mode in ["🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"]:
            if use_video:
                with st.spinner("Baue Video-Prompt..."):
                    final_video_prompt = build_video_prompt(raw_prompt)
                st.session_state.last_video_prompt = final_video_prompt
                st.success("✅ Veo3 Video-Prompt generiert!")
                st.markdown("### 🎬 Veo3 Video-Prompt")
                st.code(final_video_prompt, language="text")

        # If video-only mode, don't show image prompt but still store it
        if gen_mode == "🎬 Nur Video-Prompt":
            st.session_state.last_image_prompt = None  # Don't show image generate button

        # Optional GPT polish
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

        # Save to history
        if gen_mode == "📷 Nur Foto":
            save_prompt = raw_prompt
            save_type = "📷 Bild"
        elif gen_mode == "🎬 Nur Video-Prompt":
            save_prompt = final_video_prompt or raw_prompt
            save_type = "🎬 Video"
        else:
            save_prompt = final_video_prompt or raw_prompt
            save_type = "📷+🎬 Beides"

        st.session_state.prompt_history.append({
            "time": datetime.now().strftime("%H:%M:%S"),
            "prompt": save_prompt,
            "type": save_type,
        })

        # Export buttons
        ex1, ex2 = st.columns(2)
        if gen_mode in ["📷 Nur Foto", "📷+🎬 Foto + Video"]:
            with ex1:
                st.download_button(
                    label="💾 Bild-Prompt speichern (.txt)",
                    data=raw_prompt,
                    file_name=f"nano_banana_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
        if final_video_prompt and gen_mode in ["🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"]:
            with ex2:
                st.download_button(
                    label="🎬 Video-Prompt speichern (.txt)",
                    data=final_video_prompt,
                    file_name=f"nano_banana_veo3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

# --- GENERATE IMAGE WITH GEMINI ---
if st.session_state.last_image_prompt:
    st.markdown("---")
    st.markdown("### 🎨 Bild mit Gemini generieren")

    gen1, gen2 = st.columns([2, 1])
    with gen2:
        num_images = st.selectbox("Anzahl Bilder", [1, 2, 3, 4], index=0, key="num_img_campaign")

    with gen1:
        if not gemini_key:
            st.warning("⚠️ Gemini API Key fehlt! Füge ihn in der Sidebar oder in Streamlit Secrets hinzu.")

        if st.button("🚀 JETZT ERSTELLEN MIT GEMINI", disabled=not gemini_key):
            # Collect campaign reference images if any
            ref_imgs = campaign_ref_files if wear_product and campaign_ref_files else None
            if ref_imgs:
                st.info(f"📸 {len(ref_imgs)} Referenzbild(er) werden mitgesendet...")
            for i in range(num_images):
                pro_hint = " ⚠️ Pro-Modell: kann 2-4 Min. dauern!" if "💎 Pro" in model_quality else ""
                with st.spinner(f"Gemini generiert Bild {i+1}/{num_images}...{pro_hint}"):
                    img_bytes, mime_type = generate_image_gemini(
                        st.session_state.last_image_prompt, gemini_key,
                        reference_images=ref_imgs, aspect_ratio_str=aspect_ratio,
                        prefer_pro=("💎 Pro" in model_quality)
                    )
                if img_bytes:
                    st.session_state.generated_images.append({
                        "bytes": img_bytes,
                        "mime": mime_type,
                        "type": "campaign",
                        "time": datetime.now().strftime("%H:%M:%S"),
                    })

    # Show generated images
    if st.session_state.generated_images:
        campaign_imgs = [img for img in st.session_state.generated_images if img["type"] == "campaign"]
        if campaign_imgs:
            st.markdown("### 🖼️ Generierte Bilder")
            cols = st.columns(min(len(campaign_imgs), 4))
            for idx, img in enumerate(campaign_imgs):
                with cols[idx % 4]:
                    st.image(img["bytes"], caption=f"Campaign #{idx+1} — {img['time']}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(
                        label=f"💾 Bild #{idx+1} speichern",
                        data=img["bytes"],
                        file_name=f"nano_banana_campaign_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"],
                        key=f"dl_campaign_{idx}_{img['time']}"
                    )

            if st.button("🗑️ Generierte Campaign-Bilder löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "campaign"]
                st.rerun()

# --- GENERATE VIDEO WITH VEO ---
if st.session_state.last_video_prompt:
    st.markdown("---")
    st.markdown("### 🎬 Video mit Veo generieren")

    if not gemini_key:
        st.warning("⚠️ Gemini API Key fehlt! Veo nutzt den gleichen API Key.")

    if st.button("🎬 VIDEO JETZT ERSTELLEN MIT VEO", disabled=not gemini_key):
        with st.spinner("Veo generiert Video... (kann 1-5 Min. dauern)"):
            video_bytes = generate_video_veo(
                st.session_state.last_video_prompt, gemini_key
            )
        if video_bytes:
            st.session_state.generated_videos.append({
                "bytes": video_bytes,
                "type": "campaign",
                "time": datetime.now().strftime("%H:%M:%S"),
            })

    # Show generated videos
    campaign_vids = [v for v in st.session_state.generated_videos if v["type"] == "campaign"]
    if campaign_vids:
        st.markdown("### 🎥 Generierte Videos")
        for idx, vid in enumerate(campaign_vids):
            st.video(vid["bytes"], format="video/mp4")
            st.download_button(
                label=f"💾 Video #{idx+1} speichern (.mp4)",
                data=vid["bytes"],
                file_name=f"nano_banana_video_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                mime="video/mp4",
                key=f"dl_video_{idx}_{vid['time']}"
            )

        if st.button("🗑️ Generierte Videos löschen"):
            st.session_state.generated_videos = [v for v in st.session_state.generated_videos if v["type"] != "campaign"]
            st.rerun()


# --- PRODUCT ONLY BUTTON ---
if use_product_only:
    st.markdown("---")
    if st.button("💎 PRODUCT ONLY PROMPT GENERIEREN"):
        if not prod_name:
            st.warning("Bitte Produktname eingeben!")
        else:
            with st.spinner("Baue Product-Only Prompt..."):
                product_prompt = build_product_only_prompt()

            st.session_state.last_product_prompt = product_prompt
            st.success("✅ Product-Only Prompt generiert!")
            st.markdown("### 💎 Product Only Prompt")
            st.code(product_prompt, language="text")

            # Optional GPT polish
            if use_polish and api_key:
                with st.spinner("GPT-4o verfeinert Product Prompt..."):
                    polished_prod = polish_with_gpt(product_prompt, api_key)
                if polished_prod:
                    st.markdown("### ✨ GPT-4o Polished Product Version")
                    st.code(polished_prod, language="text")

            # Save to history
            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "prompt": product_prompt,
                "type": "💎 Product",
            })

            st.download_button(
                label="💾 Product-Prompt speichern (.txt)",
                data=product_prompt,
                file_name=f"nano_banana_product_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

    # --- GENERATE PRODUCT IMAGE WITH GEMINI ---
    if st.session_state.last_product_prompt:
        st.markdown("---")
        st.markdown("### 🎨 Product-Bild mit Gemini generieren")

        pg1, pg2 = st.columns([2, 1])
        with pg2:
            num_prod_images = st.selectbox("Anzahl Bilder", [1, 2, 3, 4], index=0, key="num_img_product")

        with pg1:
            if not gemini_key:
                st.warning("⚠️ Gemini API Key fehlt!")

            if st.button("🚀 PRODUCT JETZT ERSTELLEN", disabled=not gemini_key):
                # Collect product reference images if any
                prod_refs = prod_ref_files if use_prod_ref and prod_ref_files else None
                if prod_refs:
                    st.info(f"📸 {len(prod_refs)} Referenzbild(er) werden mitgesendet...")
                for i in range(num_prod_images):
                    with st.spinner(f"Gemini generiert Product-Bild {i+1}/{num_prod_images}..."):
                        img_bytes, mime_type = generate_image_gemini(
                            st.session_state.last_product_prompt, gemini_key,
                            reference_images=prod_refs, aspect_ratio_str=prod_ar,
                            prefer_pro=("💎 Pro" in model_quality)
                        )
                    if img_bytes:
                        st.session_state.generated_images.append({
                            "bytes": img_bytes,
                            "mime": mime_type,
                            "type": "product",
                            "time": datetime.now().strftime("%H:%M:%S"),
                        })

        # Show product images
        product_imgs = [img for img in st.session_state.generated_images if img["type"] == "product"]
        if product_imgs:
            st.markdown("### 🖼️ Generierte Product-Bilder")
            cols = st.columns(min(len(product_imgs), 4))
            for idx, img in enumerate(product_imgs):
                with cols[idx % 4]:
                    st.image(img["bytes"], caption=f"Product #{idx+1} — {img['time']}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(
                        label=f"💾 Product #{idx+1} speichern",
                        data=img["bytes"],
                        file_name=f"nano_banana_product_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"],
                        key=f"dl_product_{idx}_{img['time']}"
                    )

            if st.button("🗑️ Generierte Product-Bilder löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "product"]
                st.rerun()

# --- AD CREATIVE BUTTON ---
if use_ad_creative:
    st.markdown("---")
    st.markdown('<div class="section-card"><h3>🎯 Ad Creative generieren</h3></div>', unsafe_allow_html=True)

    if "last_ad_prompt" not in st.session_state:
        st.session_state.last_ad_prompt = None
    if "last_carousel_prompts" not in st.session_state:
        st.session_state.last_carousel_prompts = None

    # Different button for carousel vs single
    if ad_carousel:
        btn_text = f"🎠 CAROUSEL AD ({ad_carousel_count} SLIDES) GENERIEREN"
    else:
        btn_text = "🎯 AD CREATIVE PROMPT GENERIEREN"

    if st.button(btn_text):
        if not product:
            st.warning("Bitte ein Produkt / Thema eingeben (im Tab 'Format & Produkt')!")
        elif ad_carousel:
            # --- CAROUSEL MODE ---
            with st.spinner(f"Baue {ad_carousel_count} Carousel-Slide Prompts..."):
                carousel_prompts = build_carousel_prompts()

            st.session_state.last_carousel_prompts = carousel_prompts
            st.session_state.last_ad_prompt = None  # Clear single mode
            st.success(f"✅ {len(carousel_prompts)} Carousel-Slide Prompts generiert!")

            for idx, cp in enumerate(carousel_prompts):
                with st.expander(f"📄 Slide {idx+1} Prompt", expanded=(idx == 0)):
                    st.code(cp, language="text")

            # Save to history
            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "prompt": f"[CAROUSEL {len(carousel_prompts)} Slides]\n\n" + carousel_prompts[0][:200] + "...",
                "type": "🎠 Carousel",
            })
        else:
            # --- SINGLE AD MODE ---
            with st.spinner("Baue Ad Creative Prompt..."):
                ad_prompt = build_ad_creative_prompt()

            st.session_state.last_ad_prompt = ad_prompt
            st.session_state.last_carousel_prompts = None  # Clear carousel mode
            st.success("✅ Ad Creative Prompt generiert!")
            st.markdown("### 🎯 Ad Creative Prompt")
            st.code(ad_prompt, language="text")

            # Save to history
            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "prompt": ad_prompt,
                "type": "🎯 Ad Creative",
            })

            st.download_button(
                label="💾 Ad-Prompt speichern (.txt)",
                data=ad_prompt,
                file_name=f"nano_banana_ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )

    # --- GENERATE AD IMAGE WITH GEMINI ---
    if st.session_state.get("last_ad_prompt"):
        st.markdown("---")
        st.markdown("### 🎨 Ad Creative mit Gemini generieren")

        ag1, ag2 = st.columns([2, 1])
        with ag2:
            num_ad_images = st.selectbox("Anzahl Varianten", [1, 2, 3, 4], index=1, key="num_img_ad",
                                         help="Generiere mehrere Varianten zum A/B-Testen!")

        with ag1:
            if not gemini_key:
                st.warning("⚠️ Gemini API Key fehlt!")

            if st.button("🚀 AD CREATIVE JETZT ERSTELLEN", disabled=not gemini_key):
                ad_refs = ad_ref_files if use_ad_creative and ad_ref_files else None
                if ad_refs:
                    st.info(f"📸 {len(ad_refs)} Referenzbild(er) werden mitgesendet...")

                # Map ad format to aspect ratio string for Gemini
                ad_ar_map = {
                    "Facebook Feed (1:1 Quadrat)": "1:1",
                    "Facebook Feed (4:5 Hochformat)": "4:5",
                    "Instagram Story / Reels (9:16)": "9:16",
                    "Facebook Cover / Banner (16:9)": "16:9",
                    "Carousel Einzelbild (1:1)": "1:1",
                }
                ad_ar_str = ad_ar_map.get(ad_format, "1:1")

                for i in range(num_ad_images):
                    with st.spinner(f"Gemini generiert Ad Creative {i+1}/{num_ad_images}..."):
                        img_bytes, mime_type = generate_image_gemini(
                            st.session_state.last_ad_prompt, gemini_key,
                            reference_images=ad_refs, aspect_ratio_str=ad_ar_str,
                            prefer_pro=("💎 Pro" in model_quality)
                        )
                    if img_bytes:
                        st.session_state.generated_images.append({
                            "bytes": img_bytes,
                            "mime": mime_type,
                            "type": "ad_creative",
                            "time": datetime.now().strftime("%H:%M:%S"),
                        })

        # Show ad creative images
        ad_imgs = [img for img in st.session_state.generated_images if img["type"] == "ad_creative"]
        if ad_imgs:
            st.markdown("### 🖼️ Generierte Ad Creatives")
            st.caption("💡 Tipp: Generiere 3-4 Varianten und teste sie als A/B-Test in Facebook Ads Manager!")
            cols = st.columns(min(len(ad_imgs), 4))
            for idx, img in enumerate(ad_imgs):
                with cols[idx % 4]:
                    st.image(img["bytes"], caption=f"Ad Creative #{idx+1} — {img['time']}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(
                        label=f"💾 Ad #{idx+1} speichern",
                        data=img["bytes"],
                        file_name=f"nano_banana_ad_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"],
                        key=f"dl_ad_{idx}_{img['time']}"
                    )

            if st.button("🗑️ Generierte Ad Creatives löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "ad_creative"]
                st.rerun()

    # --- GENERATE CAROUSEL WITH GEMINI ---
    if st.session_state.get("last_carousel_prompts"):
        st.markdown("---")
        st.markdown("### 🎠 Carousel mit Gemini generieren")
        st.caption(f"📌 {len(st.session_state.last_carousel_prompts)} Slides werden nacheinander generiert. Alle im 1:1 Format (Carousel-Standard).")

        if not gemini_key:
            st.warning("⚠️ Gemini API Key fehlt!")

        if st.button("🚀 CAROUSEL JETZT ERSTELLEN", disabled=not gemini_key):
            ad_refs = ad_ref_files if use_ad_creative and ad_ref_files else None
            if ad_refs:
                st.info(f"📸 {len(ad_refs)} Referenzbild(er) werden bei jeder Slide mitgesendet...")

            carousel_progress = st.progress(0, text="🎠 Carousel wird generiert...")

            for i, slide_prompt in enumerate(st.session_state.last_carousel_prompts):
                pct = (i + 1) / len(st.session_state.last_carousel_prompts)
                carousel_progress.progress(pct * 0.95, text=f"🎠 Slide {i+1}/{len(st.session_state.last_carousel_prompts)}...")

                pro_hint = " (Pro)" if "💎 Pro" in model_quality else ""
                with st.spinner(f"Gemini generiert Slide {i+1}{pro_hint}..."):
                    img_bytes, mime_type = generate_image_gemini(
                        slide_prompt, gemini_key,
                        reference_images=ad_refs, aspect_ratio_str="1:1",
                        prefer_pro=("💎 Pro" in model_quality)
                    )
                if img_bytes:
                    st.session_state.generated_images.append({
                        "bytes": img_bytes,
                        "mime": mime_type,
                        "type": "carousel",
                        "slide": i + 1,
                        "time": datetime.now().strftime("%H:%M:%S"),
                    })

            carousel_progress.progress(1.0, text="✅ Carousel fertig!")

        # Show carousel images
        carousel_imgs = [img for img in st.session_state.generated_images if img["type"] == "carousel"]
        if carousel_imgs:
            st.markdown("### 🎠 Carousel Slides")
            st.caption("💡 Lade alle Slides herunter und erstelle damit eine Carousel Ad im Facebook Ads Manager.")
            cols = st.columns(min(len(carousel_imgs), 5))
            for idx, img in enumerate(carousel_imgs):
                with cols[idx % 5]:
                    slide_num = img.get("slide", idx + 1)
                    st.image(img["bytes"], caption=f"Slide {slide_num}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(
                        label=f"💾 Slide {slide_num}",
                        data=img["bytes"],
                        file_name=f"nano_banana_carousel_slide{slide_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"],
                        key=f"dl_carousel_{idx}_{img['time']}"
                    )

            if st.button("🗑️ Carousel-Slides löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "carousel"]
                st.rerun()
