import streamlit as st
import json
import os
import requests
import base64
from datetime import datetime
from pathlib import Path
from jinja2 import Template

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Nano Banana Campaign Director",
    page_icon="🍌",
    layout="wide"
)

# --- LOAD TEMPLATES & PRESETS ---
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

# --- GEMINI SAFETY SETTINGS ---
# BLOCK_ONLY_HIGH: lässt normale Fashion-/Beauty-/Schmuck-Creatives durch (die Standard-Filter
# blocken solche Bilder oft fälschlich), blockt aber weiterhin echte explizite Inhalte.
GEMINI_SAFETY_SETTINGS = [
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
]

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --gold: #FFD37A;
        --gold-bright: #FFE3A3;
        --ink-0: #0e0e18;
        --ink-1: #15162a;
        --ink-2: #1d1f3a;
        --line: rgba(255, 211, 122, 0.10);
        --muted: #9aa3b8;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    div.block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1180px;
    }

    /* === HERO === */
    .hero-banner {
        background:
            radial-gradient(120% 140% at 85% -10%, rgba(255,211,122,0.12) 0%, transparent 55%),
            linear-gradient(135deg, #14152a 0%, #181a33 55%, #101a36 100%);
        border-radius: 18px;
        padding: 1.8rem 2.2rem;
        margin-bottom: 1.4rem;
        border: 1px solid var(--line);
    }
    .hero-banner h1 {
        color: var(--gold);
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.25rem 0;
        letter-spacing: -0.4px;
    }
    .hero-banner p { color: var(--muted); font-size: 0.95rem; margin: 0; }
    .hero-banner .version-badge {
        display: inline-block;
        background: rgba(255,211,122,0.14);
        color: var(--gold);
        padding: 2px 11px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-left: 10px;
        vertical-align: middle;
        border: 1px solid var(--line);
    }

    /* === SECTION CARDS === */
    .section-card {
        background: linear-gradient(150deg, var(--ink-1), var(--ink-2));
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 1rem 1.4rem;
        margin-bottom: 0.9rem;
    }
    .section-card h3 {
        color: var(--gold);
        font-size: 1.02rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: 0.1px;
    }

    /* === BUTTONS === */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, var(--gold) 0%, #F2A93B 100%);
        color: #14152a;
        border-radius: 11px;
        padding: 13px 22px;
        font-weight: 800;
        font-size: 15px;
        border: none;
        margin-top: 10px;
        letter-spacing: 0.2px;
        transition: transform .15s ease, box-shadow .25s ease, filter .2s ease;
        box-shadow: 0 6px 18px rgba(255, 211, 122, 0.16);
    }
    .stButton>button:hover {
        filter: brightness(1.05);
        box-shadow: 0 8px 24px rgba(255, 211, 122, 0.3);
        transform: translateY(-1px);
        color: #14152a;
    }
    .stButton>button:active { transform: translateY(0); }
    .stButton>button:disabled { filter: grayscale(0.5) brightness(0.8); box-shadow: none; }

    .stDownloadButton>button {
        background: linear-gradient(135deg, #25263f 0%, #32355a 100%);
        color: var(--gold);
        border: 1px solid var(--line);
        font-size: 13px;
        padding: 8px 16px;
        font-weight: 600;
        box-shadow: none;
    }
    .stDownloadButton>button:hover { color: var(--gold-bright); border-color: rgba(255,211,122,0.3); }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: rgba(14, 14, 24, 0.6);
        border-radius: 12px;
        padding: 5px;
        border: 1px solid var(--line);
    }
    .stTabs [data-baseweb="tab"] { border-radius: 8px; padding: 9px 18px; font-weight: 600; font-size: 14px; }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(255,211,122,0.16), rgba(242,169,59,0.10));
        border-bottom-color: var(--gold) !important;
    }

    /* === FORM ELEMENTS === */
    .stSelectbox, .stTextInput, .stTextArea { margin-bottom: 6px; }
    .stSelectbox [data-baseweb="select"] > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-color: var(--line);
        border-radius: 9px;
    }
    .stSelectbox [data-baseweb="select"] > div:focus-within,
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: rgba(255,211,122,0.45);
        box-shadow: 0 0 0 1px rgba(255,211,122,0.22);
    }
    div[data-testid="stCheckbox"] label span { font-weight: 600; }

    h1, h2, h3 { font-family: 'Inter', sans-serif; }
    h2 { color: #e9edf5; }
    h3 { color: #cbd5e0; }

    .streamlit-expanderHeader { font-weight: 600; font-size: 13px; }

    hr { border-color: var(--line); margin: 1.1rem 0; }

    [data-testid="stImage"] {
        border-radius: 11px;
        overflow: hidden;
        border: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #101021 0%, #15162a 100%);
        border-right: 1px solid var(--line);
    }
    section[data-testid="stSidebar"] .stMarkdown h2 { color: var(--gold); font-size: 1rem; }
    </style>
""", unsafe_allow_html=True)


# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## ⚙️ Einstellungen")

    # Gemini API Key (used for EVERYTHING: image, video, polish, analysis)
    st.markdown("**🍌 Gemini API**")
    if "GEMINI_API_KEY" in st.secrets:
        st.success("Gemini API Key aktiv ✅")
        gemini_key = st.secrets["GEMINI_API_KEY"]
    else:
        gemini_key = st.text_input("Gemini API Key", type="password",
                                   help="Am besten in Streamlit → Settings → Secrets als GEMINI_API_KEY hinterlegen.")
        if not gemini_key:
            st.caption("Tipp: In den Streamlit Secrets als `GEMINI_API_KEY` speichern – dann musst du ihn nie wieder eingeben.")

    # Model quality selector
    st.markdown("**🎯 Bild-Modell Qualität**")
    model_quality = st.radio(
        "Modell wählen",
        ["⚡ Flash (schnell & günstig)", "💎 Pro (beste Qualität)", "🔀 Hybrid (Flash→Pro)"],
        index=0,
        help="Flash: schnell & günstig. Pro: höhere Auflösung, realistischer. Hybrid: Flash baut das produkt-treue Bild ohne Text, Pro fügt Text + Feinschliff hinzu."
    )
    if "💎 Pro" in model_quality:
        st.caption("⚠️ Pro kostet mehr pro Bild, liefert aber deutlich realistischere Ergebnisse.")
    if "🔀 Hybrid" in model_quality:
        st.caption("🔀 Schritt 1: Flash → produkt-treues Bild ohne Text. Schritt 2: Pro → Text-Overlays + Feinschliff (Haut, Licht, Details), ohne das Produkt zu verändern.")

    st.markdown("---")

    # Optional Gemini-based prompt polish (replaces the old GPT-4o polish — now 100% Gemini)
    use_polish = st.checkbox("✨ Gemini Prompt-Polish (optional)", value=False,
                             help="Verfeinert den Template-Prompt mit einem Gemini-Textmodell zu flüssiger, cinematic Prosa. Nutzt denselben Gemini-Key.")
    if use_polish and not gemini_key:
        st.warning("Für den Polish-Modus brauchst du den Gemini-Key.")

    st.markdown("---")
    st.info("**100% Gemini** – ein einziger API Key für Bild-, Video- und Prompt-Generierung. Kein OpenAI mehr nötig.")
    st.caption("V13 · Gemini-Only · Veo 3 Video · Image-to-Video Konsistenz")

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
        <h1>🍌 Nano Banana Campaign Director <span class="version-badge">V13 · Gemini-Only</span></h1>
        <p>Template-Prompts · Bild-Generierung mit Gemini · Veo 3 Video mit Konsistenz</p>
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

    # --- MODEL REFERENCE IMAGES ---
    st.markdown("**📸 Model-Referenzbilder (optional)**")
    st.caption("Lade bis zu 5 Fotos hoch — Gesicht, Proportionen, Hautton, Haare werden 1:1 übernommen. Die Bilder werden als KI-generierte Figur behandelt.")
    model_ref_files = st.file_uploader(
        "Model-Referenzbilder (max. 5)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="model_ref_upload",
        help="💡 Tipp: Bilder aus verschiedenen Winkeln (frontal, seitlich, Ganzkörper) für beste Ergebnisse."
    )
    if model_ref_files and len(model_ref_files) > 5:
        st.warning("⚠️ Maximal 5 Bilder! Nur die ersten 5 werden verwendet.")
        model_ref_files = model_ref_files[:5]
    if model_ref_files:
        ref_cols = st.columns(min(len(model_ref_files), 5))
        for idx, f in enumerate(model_ref_files):
            ref_cols[idx].image(f, caption=f"Ref {idx+1}", width=100)
        st.success(f"✅ **{len(model_ref_files)} Model-Referenz(en)** geladen — Aussehen wird 1:1 übernommen. Felder unten sind deaktiviert.")

        # --- ANALYZE MODEL BUTTON ---
        if "model_description" not in st.session_state:
            st.session_state.model_description = None

        analyze_col1, analyze_col2 = st.columns([1, 2])
        with analyze_col1:
            analyze_btn = st.button("🔍 Model analysieren", help="Gemini beschreibt das Model detailliert — die Beschreibung wird in jeden Prompt eingefügt.", key="analyze_model_btn")
        with analyze_col2:
            if st.session_state.model_description:
                st.caption("✅ Analyse vorhanden — wird automatisch in den Prompt eingefügt.")

        if analyze_btn and gemini_key:
            with st.spinner("🔍 Gemini analysiert alle Model-Referenzbilder (ca. 15-30 Sek.)..."):
                analysis_parts = []
                analysis_prompt = (
                    "TASK: You are a CHARACTER DESIGN ARTIST creating a technical reference sheet for a 3D modeling team. "
                    "The provided images show an AI-GENERATED fictional character design. "
                    "Create a comprehensive CHARACTER SPECIFICATION DOCUMENT for exact 3D reproduction.\n\n"
                    "This is standard practice in game development, animation, and VFX production. "
                    "The specification must be precise enough for a 3D artist to sculpt an identical digital double.\n\n"
                    "Respond ONLY with the specification using this format:\n\n"
                    "CHARACTER SPECIFICATION SHEET\n"
                    "============================\n\n"
                    "SECTION 1 — FACIAL STRUCTURE\n"
                    "Gender: [male/female]\n"
                    "Apparent age: [specific number]\n"
                    "Complexion: [skin tone, undertones, finish]\n"
                    "Face shape: [round/oval/square/heart/diamond/oblong]\n"
                    "Forehead: [height, width, hairline type]\n"
                    "Eyebrows: [shape, thickness, color, arch]\n"
                    "Eyes: [iris color, eye shape, size, tilt, spacing, lash density]\n"
                    "Nose: [bridge profile, width, tip shape, length ratio]\n"
                    "Lips: [shape, fullness upper/lower, cupid bow, width, color]\n"
                    "Jawline: [definition, angle, width]\n"
                    "Chin: [shape, projection, cleft]\n"
                    "Cheekbones: [height, prominence, width]\n"
                    "Ears: [size, lobe attachment]\n"
                    "Neck: [length proportion]\n\n"
                    "SECTION 2 — HAIR\n"
                    "Color: [exact shade with highlights]\n"
                    "Length: [estimate]\n"
                    "Type: [straight/wavy/curly/coily, fine/medium/coarse]\n"
                    "Density: [thin/normal/thick]\n"
                    "Styling: [part line, layering, current arrangement]\n\n"
                    "SECTION 3 — BUILD & PROPORTIONS\n"
                    "Height impression: [tall/average/petite]\n"
                    "Body type: [slim/athletic/curvy/average]\n"
                    "Shoulder width: [narrow/average/broad]\n"
                    "Overall silhouette: [brief description]\n"
                    "Posture: [description]\n\n"
                    "SECTION 4 — DISTINGUISHING FEATURES\n"
                    "Skin markers: [freckles, beauty marks with general locations]\n"
                    "Unique features: [dimples, asymmetries, anything notable]\n"
                    "Overall impression: [one sentence summary of physical presence]\n"
                )
                analysis_parts.append({"text": analysis_prompt})

                for ref_file in model_ref_files:
                    ref_file.seek(0)
                    img_bytes = ref_file.read()
                    ref_file.seek(0)
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    mime = "image/png" if ref_file.name.lower().endswith(".png") else "image/jpeg"
                    analysis_parts.append({"inlineData": {"mimeType": mime, "data": img_b64}})

                # Dynamically find a working text model for analysis
                analysis_models = []
                try:
                    models_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_key}"
                    models_resp = requests.get(models_url, timeout=30)
                    models_resp.raise_for_status()
                    models_data = models_resp.json()
                    available_models = []
                    for m in models_data.get("models", []):
                        name = m.get("name", "").replace("models/", "")
                        if "generateContent" in m.get("supportedGenerationMethods", []):
                            available_models.append(name)
                    pro_candidates = [m for m in available_models if "pro" in m.lower() and "image" not in m.lower() and "vision" not in m.lower()]
                    flash_candidates = [m for m in available_models if "flash" in m.lower() and "image" not in m.lower()]
                    analysis_models = pro_candidates + flash_candidates
                    if not analysis_models:
                        analysis_models = [m for m in available_models if "image" not in m.lower()]
                    st.caption(f"🔍 {len(analysis_models)} Text-Modelle gefunden.")
                except Exception as e:
                    st.error(f"❌ Konnte Modell-Liste nicht laden: {e}")

                analysis_success = False
                for analysis_model in analysis_models:
                    analysis_url = f"https://generativelanguage.googleapis.com/v1beta/models/{analysis_model}:generateContent?key={gemini_key}"
                    analysis_payload = {
                        "contents": [{"parts": analysis_parts}],
                        "generationConfig": {"responseMimeType": "text/plain"},
                        "safetySettings": GEMINI_SAFETY_SETTINGS,
                    }
                    try:
                        resp = requests.post(analysis_url, json=analysis_payload,
                                             headers={"Content-Type": "application/json"}, timeout=120)
                        if resp.status_code == 404:
                            continue
                        if resp.status_code != 200:
                            try:
                                error_msg = resp.json().get("error", {}).get("message", resp.text[:200])
                            except Exception:
                                error_msg = resp.text[:200]
                            st.caption(f"⚠️ {analysis_model}: {resp.status_code} — {error_msg}")
                            continue
                        data = resp.json()
                        description = ""
                        for candidate in data.get("candidates", []):
                            for part in candidate.get("content", {}).get("parts", []):
                                if "text" in part:
                                    description += part["text"]
                        if description.strip():
                            st.session_state.model_description = description.strip()
                            st.success(f"✅ Model-Analyse fertig! (via {analysis_model})")
                            analysis_success = True
                            break
                        else:
                            st.caption(f"⚠️ {analysis_model} hat keine Beschreibung zurückgegeben — versuche nächstes Modell...")
                    except requests.exceptions.HTTPError:
                        continue
                    except Exception as e:
                        st.error(f"❌ Analyse fehlgeschlagen: {e}")
                        analysis_success = True
                        break

                if not analysis_success and not st.session_state.get("model_description"):
                    st.error("❌ Kein Gemini-Modell für die Text-Analyse verfügbar. Prüfe deinen API Key.")

        elif analyze_btn and not gemini_key:
            st.warning("⚠️ Gemini API Key fehlt — bitte in der Sidebar eingeben.")

        if st.session_state.get("model_description"):
            with st.expander("📝 Model-Beschreibung (wird in den Prompt eingefügt)", expanded=False):
                st.code(st.session_state.model_description, language="text")
                if st.button("🗑️ Beschreibung löschen", key="del_model_desc"):
                    st.session_state.model_description = None
                    st.rerun()
    else:
        model_ref_files = []
        if "model_description" in st.session_state:
            st.session_state.model_description = None

    has_model_ref = len(model_ref_files) > 0

    # --- BODY PROPORTIONS (only when NOT using reference images) ---
    if not has_model_ref:
        st.markdown("---")
        st.markdown('<div class="section-card"><h3>🏋️ Körperbau & Proportionen</h3></div>', unsafe_allow_html=True)
        st.caption("Stelle Größe, Gewicht, Muskulatur und Körperproportionen ein — die SVG-Silhouette zeigt dir in Echtzeit wie dein Model aussehen wird.")

        bp_left, bp_mid, bp_right = st.columns([1, 1, 1])

        with bp_left:
            st.markdown("**📏 Grundmaße**")
            body_height = st.number_input("Größe (cm)", 150, 210, 172, 1, key="body_h")
            body_weight = st.number_input("Gewicht (kg)", 40, 130, 62, 1, key="body_w")
            body_type = st.selectbox("Körpertyp", [
                "Slim / Schlank", "Normal / Durchschnitt", "Athletic / Sportlich",
                "Curvy / Kurvig", "Muscular / Muskulös", "Plus Size / Kräftig",
                "Petite / Zierlich", "Tall & Lean / Groß & Schlank",
            ], index=0, key="body_type_sel")

            st.markdown("**💪 Muskeldefinition**")
            muscle_def = st.slider("Definition", 1, 5, 2, key="musc_def",
                                   help="1 = weich/glatt · 3 = leicht definiert · 5 = sehr definiert, sichtbare Muskeln")
            muscle_def_labels = {1: "Weich / Soft", 2: "Leicht tonisiert", 3: "Definiert",
                                 4: "Sehr definiert", 5: "Stark muskulös"}
            st.caption(f"→ {muscle_def_labels[muscle_def]}")

        with bp_mid:
            st.markdown("**🎛️ Proportionen** *(1 = schmal/kurz · 5 = breit/lang)*")
            prop_shoulders = st.slider("Schulterbreite", 1, 5, 3, key="p_sh")
            prop_neck      = st.slider("Halslänge", 1, 5, 3, key="p_nl")
            prop_bust      = st.slider("Brust / Chest", 1, 5, 3, key="p_bu")
            prop_waist     = st.slider("Taillenbreite", 1, 5, 2, key="p_wa")
            prop_hips      = st.slider("Hüftbreite", 1, 5, 3, key="p_hp")
            prop_thighs    = st.slider("Oberschenkel", 1, 5, 3, key="p_th")
            prop_arms      = st.slider("Armdicke", 1, 5, 2, key="p_ar")
            prop_legs_len  = st.slider("Beinlänge (relativ)", 1, 5, 3, key="p_ll",
                                       help="1 = kurze Beine · 5 = sehr lange Beine (Model-Proportionen)")

        with bp_right:
            st.markdown("**🔬 Muskelverteilung**")
            st.caption("Wo sollen Muskeln betont sein?")
            musc_upper = st.checkbox("Oberkörper (Schultern, Arme, Brust)", value=False, key="mu_upper")
            musc_core  = st.checkbox("Core (Bauch, seitliche Bauchmuskeln)", value=False, key="mu_core")
            musc_lower = st.checkbox("Unterkörper (Oberschenkel, Po, Waden)", value=False, key="mu_lower")
            musc_back  = st.checkbox("Rücken (V-Shape, Latissimus)", value=False, key="mu_back")

            st.markdown("**🦵 Extras**")
            body_torso_len = st.select_slider("Oberkörper-Länge",
                options=["Kurzer Oberkörper", "Durchschnitt", "Langer Oberkörper"],
                value="Durchschnitt", key="torso_len")
            body_waist_height = st.select_slider("Taillenhöhe",
                options=["Niedrige Taille", "Durchschnitt", "Hohe Taille"],
                value="Durchschnitt", key="waist_height")

            # --- SVG SILHOUETTE PREVIEW ---
            st.markdown("**👤 Vorschau**")

            def generate_body_svg(sh, nl, bu, wa, hp, th, ar, mu_d):
                """Generate body proportion SVG silhouette. All params 1-5."""
                def s(v, lo, hi):
                    return lo + (v - 1) * (hi - lo) / 4

                cx, gold = 110, "#FFD37A"
                S = s(sh,30,55); B = s(bu,22,47); W = s(wa,16,42)
                H = s(hp,26,51); T = s(th,13,26); A = s(ar,5,14)
                NL = s(nl,12,26); NW = 8; HR = 17

                hcy = 26
                ynt = hcy + HR + 2
                ynb = ynt + NL
                ysh = ynb + 4
                ybu = ysh + 36
                ywa = ybu + 33
                yhp = ywa + 24
                ycr = yhp + 20
                ykn = ycr + 48
                ycf = ykn + 18
                yan = ycf + 28
                yft = yan + 8
                vh = int(yft + 18)

                def poly(pts):
                    return " ".join(f"{x:.0f},{y:.0f}" for x, y in pts)

                # Muscle definition → more angular shapes
                ang = 0 if mu_d < 3 else (mu_d - 2) * 1.5

                torso = poly([
                    (cx+NW, ynt), (cx+NW, ynb),
                    (cx+S, ysh),
                    (cx+B+ang, ybu),
                    (cx+W, ywa),
                    (cx+H, yhp),
                    (cx+T+7, ycr),
                    (cx-T-7, ycr),
                    (cx-H, yhp),
                    (cx-W, ywa),
                    (cx-B-ang, ybu),
                    (cx-S, ysh),
                    (cx-NW, ynb), (cx-NW, ynt),
                ])
                rleg = poly([
                    (cx+T+7, ycr), (cx+T+4, ykn), (cx+T+2, ycf),
                    (cx+7, yan), (cx+8, yft),
                    (cx+2, yft), (cx+3, yan), (cx+4, ycf),
                    (cx+3, ykn), (cx+2, ycr),
                ])
                lleg = poly([
                    (cx-2, ycr), (cx-3, ykn), (cx-4, ycf),
                    (cx-3, yan), (cx-2, yft),
                    (cx-8, yft), (cx-7, yan), (cx-T-2, ycf),
                    (cx-T-4, ykn), (cx-T-7, ycr),
                ])
                rarm = poly([
                    (cx+S, ysh+2), (cx+S+A, ysh+4),
                    (cx+S+A-1, ywa-8), (cx+S-2, ywa-10),
                ])
                larm = poly([
                    (cx-S, ysh+2), (cx-S-A, ysh+4),
                    (cx-S-A+1, ywa-8), (cx-S+2, ywa-10),
                ])

                markers = ""
                levels = [("Schultern", ysh, S), ("Brust", ybu, B+ang),
                          ("Taille", ywa, W), ("Hüfte", yhp, H)]
                for label, yy, hw in levels:
                    markers += (f'<line x1="{cx-hw:.0f}" y1="{yy:.0f}" x2="{cx+hw:.0f}" y2="{yy:.0f}" '
                                f'stroke="{gold}" stroke-width="0.5" stroke-dasharray="3,3" opacity="0.35"/>')
                    markers += (f'<text x="{cx+hw+4:.0f}" y="{yy+3:.0f}" fill="{gold}" '
                                f'font-size="7.5" font-family="Inter,sans-serif" opacity="0.45">{label}</text>')

                svg = f'''<svg viewBox="0 0 220 {vh}" xmlns="http://www.w3.org/2000/svg"
                          style="max-height:340px;display:block;margin:0 auto;">
                  <defs>
                    <linearGradient id="bf" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stop-color="{gold}" stop-opacity="0.20"/>
                      <stop offset="100%" stop-color="{gold}" stop-opacity="0.06"/>
                    </linearGradient>
                  </defs>
                  <rect width="220" height="{vh}" fill="#12121e" rx="14"/>
                  <circle cx="{cx}" cy="{hcy}" r="{HR}" fill="url(#bf)" stroke="{gold}" stroke-width="1.3" opacity="0.75"/>
                  <polygon points="{torso}" fill="url(#bf)" stroke="{gold}" stroke-width="1.3" stroke-linejoin="round"/>
                  <polygon points="{rleg}" fill="url(#bf)" stroke="{gold}" stroke-width="1.1" stroke-linejoin="round"/>
                  <polygon points="{lleg}" fill="url(#bf)" stroke="{gold}" stroke-width="1.1" stroke-linejoin="round"/>
                  <polygon points="{rarm}" fill="url(#bf)" stroke="{gold}" stroke-width="1.1" stroke-linejoin="round"/>
                  <polygon points="{larm}" fill="url(#bf)" stroke="{gold}" stroke-width="1.1" stroke-linejoin="round"/>
                  {markers}
                </svg>'''
                return svg

            svg_preview = generate_body_svg(prop_shoulders, prop_neck, prop_bust, prop_waist,
                                            prop_hips, prop_thighs, prop_arms, muscle_def)
            st.markdown(svg_preview, unsafe_allow_html=True)

        # --- BUILD BODY DESCRIPTION FOR PROMPT ---
        prop_labels = {
            1: "very narrow/short", 2: "narrow/short", 3: "average",
            4: "wide/long", 5: "very wide/long"
        }
        muscle_labels = {
            1: "soft, no visible muscle definition",
            2: "lightly toned, subtle definition",
            3: "defined, visible muscle tone",
            4: "very defined, clearly visible muscles, veins partially visible",
            5: "heavily muscular, bodybuilder-adjacent, prominent vascularity"
        }
        muscle_zones = []
        if musc_upper: muscle_zones.append("upper body (shoulders, arms, chest)")
        if musc_core:  muscle_zones.append("core (abs, obliques)")
        if musc_lower: muscle_zones.append("lower body (thighs, glutes, calves)")
        if musc_back:  muscle_zones.append("back (lats, V-shape taper)")

        body_description = (
            f"BODY BUILD: {body_type}. Height {body_height}cm, weight approximately {body_weight}kg.\n"
            f"PROPORTIONS: Shoulders {prop_labels[prop_shoulders]}, "
            f"neck {prop_labels[prop_neck]}, bust/chest {prop_labels[prop_bust]}, "
            f"waist {prop_labels[prop_waist]}, hips {prop_labels[prop_hips]}, "
            f"thighs {prop_labels[prop_thighs]}, arms {prop_labels[prop_arms]}, "
            f"legs {prop_labels[prop_legs_len]}.\n"
            f"Torso length: {body_torso_len.lower()}. Waist height: {body_waist_height.lower()}.\n"
            f"MUSCLE DEFINITION: {muscle_labels[muscle_def]}."
        )
        if muscle_zones:
            body_description += f"\nMUSCLE EMPHASIS: Emphasize muscle definition in: {', '.join(muscle_zones)}."
        if muscle_def >= 3 and not muscle_zones:
            body_description += "\nMuscle definition evenly distributed across the body."

    else:
        body_description = ""

    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

with col1:
    if has_model_ref:
        st.info("👤 Wird vom Referenzbild übernommen")
        gender = "As shown in the MODEL REFERENCE images"
        age = "As shown in the MODEL REFERENCE images"
    else:
        gender_options = ["Female Model", "Male Model", "Non-binary Model"]
        gender = st.selectbox("Geschlecht", gender_options,
                              index=gender_options.index(get_val("gender", "Female Model")))
        age_options = ["18-24", "25-34", "35-44", "45-55", "60+"]
        age = st.select_slider("Alter", options=age_options, value=get_val("age", "25-34"))

with col2:
    if has_model_ref:
        st.info("👤 Wird vom Referenzbild übernommen")
        ethnicity = "As shown in the MODEL REFERENCE images"
        hair_color = "As shown in the MODEL REFERENCE images"
    else:
        ethnicity = st.text_input("Ethnie / Look", value=get_val("ethnicity", "olive skin tone"))
        hair_color = st.text_input("Haarfarbe", value=get_val("hair_color", "dark brown"))

with col3:
    if has_model_ref:
        st.info("👤 Wird vom Referenzbild übernommen")
        hair_texture = "As shown in the MODEL REFERENCE images"
        hair_style = "As shown in the MODEL REFERENCE images"
    else:
        hair_tex_options = ["Straight (Glatt)", "Wavy (Wellig)", "Curly (Lockig)", "Coily (Afro)"]
        hair_texture = st.select_slider("Haarstruktur", options=hair_tex_options,
                                        value=get_val("hair_texture", "Wavy (Wellig)"))
        hair_style_options = ["Loose & Open", "Sleek Ponytail", "Messy Bun", "Short Cut", "Bob Cut"]
        hair_style = st.selectbox("Frisur-Stil", hair_style_options,
                                  index=hair_style_options.index(get_val("hair_style", "Loose & Open")))

with col4:
    if has_model_ref:
        st.info("👤 Wird vom Referenzbild übernommen")
        eye_color = "As shown in the MODEL REFERENCE images"
        freckles = "As shown in the MODEL REFERENCE images"
        use_vellus = True
        use_imperfections = False
    else:
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
    makeup = st.select_slider("Make-up", options=makeup_options, value=get_val("makeup", "Natural/Clean"))

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
            pose_category = st.selectbox("Pose-Kategorie", [
                "🧍 Stehend", "🪑 Sitzend", "🚶 Gehend / Bewegung",
                "🧘 Boden / Liegend", "💃 Dynamisch / Fashion", "📐 Angelehnt / Gelehnt",
            ], key="pose_cat")

            pose_map = {
                "🧍 Stehend": [
                    "Standing Upright — aufrecht, selbstbewusst, Gewicht auf beiden Beinen",
                    "Standing Contrapposto — Gewicht auf einem Bein, Hüfte leicht verschoben, klassisch",
                    "Standing Breitbeinig — Beine schulterbreit, kraftvoll, selbstsicher",
                    "Standing Grätsche — Beine weit auseinander, dominant, editorial",
                    "Standing Überkreuzt — ein Bein vor dem anderen gekreuzt, lässig",
                    "Standing Auf Zehenspitzen — auf den Zehenspitzen, elegant, tänzerisch",
                    "Standing Hände in Hüfte — Hände auf den Hüften, Power Pose",
                    "Standing Arme verschränkt — Arme vor der Brust verschränkt, cool",
                    "Standing Ein Arm oben — eine Hand im Haar oder am Kopf, entspannt",
                    "Standing Hände hinter Kopf — beide Arme hoch, Ellbogen nach außen, offen",
                ],
                "🪑 Sitzend": [
                    "Sitting Elegant — auf Stuhl/Hocker, Rücken gerade, Beine übereinander",
                    "Sitting Schneidersitz — auf dem Boden im Schneidersitz, entspannt, gemütlich",
                    "Sitting Knie angezogen — Knie zur Brust, Arme um die Knie, intim",
                    "Sitting Beine ausgestreckt — auf dem Boden, Beine gerade nach vorne",
                    "Sitting Seitlich — seitlich auf einer Fläche, Beine zur Seite, elegant",
                    "Sitting Auf Kante — auf Tischkante/Fensterbank, Beine baumelnd, lässig",
                    "Sitting Stuhl verkehrt — rittlings auf Stuhl sitzend, Arme auf Lehne, frech",
                    "Sitting Hocker — auf einem hohen Barhocker, Beine gekreuzt, modisch",
                ],
                "🚶 Gehend / Bewegung": [
                    "Walking towards Camera — auf die Kamera zugehend, selbstbewusst",
                    "Walking away — von der Kamera weg, Rückenansicht, mysteriös",
                    "Walking Seitlich — seitlich an der Kamera vorbei, Profil, dynamisch",
                    "Mid-Step Freeze — mitten im Schritt eingefroren, Bein in der Luft",
                    "Running leicht — leichtes Joggen/Laufen, Haare in Bewegung",
                    "Treppe steigend — auf einer Treppe nach oben gehend",
                    "Drehung — sich umdrehend, Blick über die Schulter, Stoff fließt",
                ],
                "🧘 Boden / Liegend": [
                    "Lying on back — auf dem Rücken liegend, Haare ausgebreitet",
                    "Lying on side — auf der Seite liegend, Kopf auf Hand gestützt",
                    "Lying on stomach — auf dem Bauch, Kinn auf Händen, verspielt",
                    "Kneeling — kniend, aufrecht, edel, zeremoniell",
                    "Kneeling Zurückgelehnt — kniend und nach hinten gelehnt, dramatisch",
                    "Hocke / Squat — tiefe Hocke, urban, streetwear-Vibe",
                    "Boden Seitlich — seitlich am Boden, ein Bein angewinkelt, lässig-elegant",
                ],
                "💃 Dynamisch / Fashion": [
                    "Fashion Lunge — großer Ausfallschritt nach vorne, dramatisch",
                    "Jump / Sprung — in der Luft, Haare und Kleidung fliegen, energetisch",
                    "Wind Pose — Körper gegen den Wind gelehnt, Haare wehen, editorial",
                    "Tanz-Pose — tänzerische Körperhaltung, ein Bein angehoben, arme fließend",
                    "Hand an Gesicht — Hand zart am Kinn/Wange, nachdenklich, modisch",
                    "Jacke/Mantel über Schulter — Kleidungsstück lässig über eine Schulter",
                    "Haare werfen — Kopf zur Seite, Haare in Bewegung, glamourös",
                    "Rücken durchgestreckt — starke Rückenbeuge, High-Fashion, skulptural",
                ],
                "📐 Angelehnt / Gelehnt": [
                    "Relaxed Leaning — an Wand gelehnt, entspannt, lässig",
                    "Nach vorne gelehnt — Oberkörper nach vorne gebeugt, Hände auf Knien, intensiv",
                    "Schulter an Wand — mit einer Schulter an der Wand, cool, seitlich",
                    "Rücken an Wand — mit dem Rücken an Wand/Tür gelehnt, frontal",
                    "An Geländer gelehnt — auf ein Geländer/Zaun gestützt, outdoor-Vibe",
                    "Auf Tisch gestützt — Hände auf einem Tisch, nach vorne gebeugt, direkt",
                    "Ellbogen auf Knie — sitzend, Ellbogen auf Knie gestützt, nachdenklich",
                ],
            }
            poses_for_cat = pose_map.get(pose_category, pose_map["🧍 Stehend"])
            pose = st.selectbox("Pose", poses_for_cat, index=0)

        with p2:
            gaze_options = ["Straight into Camera", "Looking away (Dreamy)", "Looking down", "Looking up",
                            "Augen geschlossen (peaceful)", "Blick über die Schulter", "Blick zur Seite (Profil)"]
            gaze = st.selectbox("Blickrichtung", gaze_options,
                                index=gaze_options.index(get_val("gaze", "Straight into Camera"))
                                if get_val("gaze", "") in gaze_options else 0)
        with p3:
            expr_options = ["Neutral & Cool", "Confident Smile", "Laughing", "Fierce/Intense", "Seductive",
                            "Nachdenklich / Verträumt", "Überrascht / Staunend", "Entspannt / Zufrieden"]
            expression = st.selectbox("Gesichtsausdruck", expr_options,
                                      index=expr_options.index(get_val("expression", "Neutral & Cool"))
                                      if get_val("expression", "") in expr_options else 0)

    model_view_options = [
        "— Automatisch —", "Frontal (von vorne)", "Leicht gedreht (3/4 Ansicht)",
        "Seitenprofil (von der Seite)", "Rückenansicht (von hinten)", "Über-die-Schulter",
        "Schräg von hinten (3/4 Rücken)", "Selfie-Perspektive (von oben)",
    ]
    model_view_campaign = st.selectbox("🔄 Model-Ansicht / Drehung", model_view_options, index=0,
                                        help="Aus welcher Richtung wird das Model gezeigt? Wichtig für Halsketten (Rücken), Ohrringe (Seite).")

    wind_options = ["Static", "Soft Breeze", "Strong Wind"]
    wind = "Natural movement" if use_candid else st.select_slider(
        "Haar-Dynamik", options=wind_options,
        value=get_val("wind", "Soft Breeze") if get_val("wind", "Soft Breeze") in wind_options else "Soft Breeze")


# --- 3. KAMERA, LICHT & ATMOSPHÄRE ---
with tab_camera:
    st.markdown('<div class="section-card"><h3>Kamera, Licht & Atmosphäre</h3></div>', unsafe_allow_html=True)
    t1, t2, t3, t4 = st.columns(4)

with t1:
    cam_options = ["360° Orbit (Circle around Model)", "Static Tripod", "Slow Zoom In", "Handheld", "Drone Orbit (Landscape)"]
    cam_move = st.selectbox("Kamera-Bewegung", cam_options,
                            index=cam_options.index(get_val("cam_move", "Static Tripod"))
                            if get_val("cam_move", "") in cam_options else 1)
    focus_options = ["Balanced (Model + Product)", "Model Hero (Face Focus)",
                     "Product Hero (Blurry Model)", "Detail Shot (Hands/Product Only)"]
    shot_focus = st.selectbox("Shot Focus", focus_options,
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
    frame_options = ["Extreme Close-Up", "Portrait", "Medium Shot", "Full Body (Kopf bis Fuß)"]
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
            type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="campaign_ref_upload")
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
        ["no airbrush skin", "no plastic look", "no symmetrical face", "no overly smooth skin",
         "no wax figure appearance", "no uncanny valley", "no AI-generated look", "no oversaturated colors",
         "no blurry details", "no deformed hands", "no extra fingers", "no text", "no watermark", "no logo",
         "no cropped frame", "no cartoonish style", "no overexposed highlights", "no flat lighting", "no stock photo feel"],
        default=["no airbrush skin", "no plastic look", "no text", "no watermark"],
        help="Wähle was NICHT im Bild sein soll.")
    neg_custom = st.text_input("Eigene Ausschlüsse (optional)",
                               placeholder="z.B. no hat, no sunglasses...", key="neg_custom_input")
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
        bg_options = ["Clean White Studio", "Dark Luxury", "Warm Beige", "City Street", "Nature", "Blue Sky", "Abstract"]
        bg_sel = st.selectbox("Szenario", bg_options)
        final_bg = f"{bg_sel} background"
    else:
        col = st.color_picker("Farbe", "#FF0044")
        final_bg = f"Solid background hex {col}"


# --- 5. VEO3 VIDEO GENERATION ---
st.markdown("---")
st.markdown('<div class="section-card"><h3>🎬 Veo 3 Video-Generation</h3></div>', unsafe_allow_html=True)
use_video = st.checkbox("Video-Prompt aktivieren", value=False,
                        help="Erweitert den Bild-Prompt um Veo 3 Video-Anweisungen.")

if use_video:
    v1, v2, v3 = st.columns(3)

    with v1:
        st.markdown("**Video-Basics**")
        # Veo 3 unterstützt NUR 4, 6 oder 8 Sekunden
        video_duration = st.select_slider("Dauer (Sekunden)", options=[4, 6, 8], value=8,
                                           help="Veo 3 unterstützt 4, 6 oder 8 Sekunden.")
        # Veo 3 unterstützt NUR 16:9 oder 9:16
        video_ratio = st.selectbox("Video-Format", ["16:9 (Landscape)", "9:16 (Vertical/Reels)"],
                                    help="Veo 3 unterstützt nur 16:9 und 9:16.")
        video_fps = st.selectbox("Framerate (nur Prompt-Hinweis)", ["24fps (Cinematic)"], index=0,
                                  help="Veo rendert nativ mit 24fps.")
        use_video_first_frame = st.checkbox("🎞️ Letztes generiertes Bild als Startframe", value=True,
                                            help="Image-to-Video: Nutzt dein zuletzt generiertes Campaign-Bild als ersten Frame → das Model bleibt 100% konsistent. Stark empfohlen!")

    with v2:
        st.markdown("**Model-Aktion**")
        model_action = st.selectbox("Was macht das Model?", [
            "Walks slowly towards camera", "Walks past camera (Runway Walk)",
            "Poses with jewelry / product", "Turns head slowly to camera",
            "Touches / adjusts product on body", "Picks up product from table",
            "Stands still, only subtle breathing", "Spins around (Full Body Reveal)",
            "Sits down elegantly", "Leans against wall, shifts weight", "Custom..."])
        if model_action == "Custom...":
            model_action = st.text_input("Eigene Aktion beschreiben",
                                         placeholder="z.B. Model nimmt Sonnenbrille ab und lächelt")
        action_detail = st.text_input("Zusatz-Detail (optional)",
                                      placeholder="z.B. Finger streicht über Anhänger, Haare fallen ins Gesicht")
        movement_speed = st.select_slider("Bewegungs-Tempo",
                                          options=["Very Slow (Slow-Mo Feel)", "Slow & Elegant", "Natural Pace", "Energetic / Fast"],
                                          value="Slow & Elegant")

    with v3:
        st.markdown("**Atmosphäre & Sound**")
        video_wind = st.selectbox("Wind im Video", [
            "Kein Wind", "Gentle breeze (leicht)", "Medium wind (Haare wehen)",
            "Strong dramatic wind (Stoff fliegt)", "Fan wind from front (Studio-Ventilator)"])
        video_cam = st.selectbox("Kamera-Bewegung (Video)", [
            "Static (Stativ, Model bewegt sich)", "Slow tracking forward",
            "Slow tracking sideways (Dolly)", "360° Orbit around model",
            "Slow zoom in on face", "Crane shot (oben nach unten)",
            "Handheld (leicht wackelig, authentisch)"])

    st.markdown("**Sprache & Sound**")
    d1, d2 = st.columns(2)
    with d1:
        has_dialogue = st.checkbox("🎤 Model spricht (Lip Sync)", value=False)
        if has_dialogue:
            dialogue_text = st.text_area("Was sagt das Model?",
                                         placeholder='z.B. "This is the one piece you need this summer."', height=80)
            voice_tone = st.selectbox("Stimme / Ton", [
                "Soft & whispery (ASMR-like)", "Confident & clear", "Warm & friendly",
                "Seductive & low", "Energetic & upbeat", "Cool & casual"])
        else:
            dialogue_text = ""
            voice_tone = ""
    with d2:
        has_ambient = st.checkbox("🔊 Ambient Sound", value=False)
        if has_ambient:
            ambient_sound = st.selectbox("Sound-Atmosphäre", [
                "Soft cinematic music", "City ambient (traffic, people)", "Nature sounds (birds, wind)",
                "Studio silence with subtle reverb", "Upbeat fashion/commercial beat", "Lo-fi / chill background"])
        else:
            ambient_sound = ""

    st.markdown("**Kopf, Gesicht & Micro-Movements**")
    h1, h2, h3 = st.columns(3)
    with h1:
        head_movement = st.selectbox("Kopfbewegung", [
            "Keine (statisch)", "Slow head turn to camera", "Slow head turn away from camera",
            "Gentle head tilt to one side", "Chin up (confident / proud)", "Chin down, eyes up (seductive)",
            "Head follows product in hand", "Subtle nod (agreeing / confident)",
            "Head sway side to side (relaxed)", "Looks down then up to camera (reveal)"])
        head_speed = st.select_slider("Kopf-Tempo", options=["Ultra Slow", "Slow", "Natural", "Quick"], value="Slow")
    with h2:
        eye_movement = st.selectbox("Augen / Blick-Animation", [
            "Keine (fixiert)", "Slow eye contact to camera (the look)", "Eyes wander, then lock on camera",
            "Blink naturally (2-3 times)", "Slow deliberate blink (sensual)", "Eyes follow product / hand movement",
            "Squint slightly (sun / intensity)", "Eyes widen (surprise / excitement)", "Look down at product, then up"])
        eyebrow_move = st.selectbox("Augenbrauen", [
            "Keine Bewegung", "Subtle raise (interested)", "One eyebrow up (playful / cheeky)",
            "Slight furrow (intense / focused)", "Raise then relax (surprised then calm)"])
    with h3:
        mouth_movement = st.selectbox("Mund / Lippen", [
            "Keine Bewegung", "Subtle smile develops slowly", "Lips part slightly (sensual)",
            "Bites lower lip gently", "Smirk / half smile (one side)", "Mouth opens to slight laugh",
            "Licks lips subtly", "Pout / duck face (playful)"])
        micro_expressions = st.multiselect("Micro-Expressions (mehrere wählbar)", [
            "Subtle breathing (chest rises)", "Jaw clench then relax", "Nostril flare (intensity)",
            "Swallow (throat movement)", "Shoulder shrug (casual)", "Deep breath in (anticipation)",
            "Neck stretch / tension release"], help="Kleine Details die das Video lebendig machen.")


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
                                  placeholder="z.B. Goldene Kette mit Diamant-Anhänger", key="prod_only_name")
        prod_description = st.text_area("Beschreibung (optional)",
                                        placeholder="z.B. 18K Gold, 2mm Gliederkette, runder Anhänger mit 0.5ct Diamant",
                                        height=80, key="prod_only_desc")
        prod_material = st.selectbox("Material", [
            "— Nicht angeben —", "Gold (glänzend)", "Gold (matt/gebürstet)", "Silber / Sterling Silver",
            "Rosegold", "Platin", "Edelstahl", "Leder", "Stoff / Textil", "Keramik", "Holz",
            "Glas / Kristall", "Kunststoff / Acryl", "Perlen", "Diamant / Edelsteine"])
        if prod_material == "— Nicht angeben —":
            prod_material = ""
        prod_size_text = st.text_input("Größe (optional)", placeholder="z.B. 45cm Kette, Anhänger 1.5cm", key="prod_only_size")

        st.markdown("---")
        st.markdown("**📸 Referenzbilder**")
        use_prod_ref = st.checkbox("Referenzbilder verwenden", value=False,
                                   help="Lade deine Produktbilder hoch — sie werden direkt an Gemini gesendet.")
        if use_prod_ref:
            prod_ref_files = st.file_uploader("Referenzbilder hochladen (max. 4)",
                type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="prod_ref_upload",
                help="2-4 Bilder deines Produkts aus verschiedenen Winkeln.")
            if prod_ref_files and len(prod_ref_files) > 4:
                st.warning("Maximal 4 Bilder! Nur die ersten 4 werden verwendet.")
                prod_ref_files = prod_ref_files[:4]
            prod_ref_angles = st.multiselect("Welche Ansichten zeigen deine Bilder?", [
                "Front view", "Side view", "Back view", "Close-up detail", "Full product overview", "Worn / in use"],
                default=["Front view", "Close-up detail"])
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
            "Floating in air (schwebend, freistehend)", "Lying flat on surface",
            "Draped over curved fabric (Stoff-Wölbung)", "Hanging / suspended from above",
            "Standing upright on display", "Resting on stone / marble slab", "Placed on wooden surface",
            "Nestled in velvet box / cushion", "Wrapped around display bust (Schmuck-Büste)",
            "Scattered artfully (mehrere Teile)", "In hand (close-up, no face)", "On mirror surface (Spiegelung)"])
        prod_arrangement = st.selectbox("Anordnung", [
            "Single Hero Product", "Product + Packaging", "Multiple color variants side by side",
            "Flat Lay (Draufsicht, mehrere Items)", "Stacked / layered"])
        prod_angle = st.selectbox("Kamera-Winkel", [
            "Straight on (Augenhöhe)", "Slightly above (30°, klassisch)", "Top down / Bird's eye (90°)",
            "Low angle (von unten, dramatisch)", "45° angle (dynamisch)", "Macro extreme close-up"])

    st.markdown("---")
    po3, po4 = st.columns(2)
    with po3:
        st.markdown("**Oberfläche & Untergrund**")
        prod_surface = st.selectbox("Untergrund-Material", [
            "— Keiner (schwebend) —", "Weißer Marmor", "Schwarzer Marmor", "Helles Holz (Eiche / Birke)",
            "Dunkles Holz (Walnuss / Mahagoni)", "Beton / Concrete", "Samt / Velvet (schwarz)",
            "Samt / Velvet (bordeaux)", "Samt / Velvet (navy)", "Seide / Silk (weiß)",
            "Seide / Silk (champagner)", "Leinen / Linen (naturfarben)", "Wasser / Wassertropfen",
            "Sand", "Blütenblätter", "Spiegel / reflektierende Oberfläche"])
        if "Samt" in prod_surface or "Seide" in prod_surface or "Leinen" in prod_surface:
            fabric_drape = st.selectbox("Stoff-Form", [
                "Flat / flach ausgelegt", "Soft wave / sanfte Wölbung", "Deep folds / tiefe Falten",
                "Crumpled / leicht zerknittert (lässig)", "Tightly wrapped around object"])
        else:
            fabric_drape = None
        prod_props = st.text_input("Deko / Props (optional)",
                                   placeholder="z.B. Eukalyptus-Zweige, Wassertropfen, Rosenblätter, Kerzen", key="prod_only_props")

    with po4:
        st.markdown("**Licht & Atmosphäre**")
        prod_lighting = st.selectbox("Beleuchtung", [
            "Clean Studio Softbox (klassisch)", "Dramatic Side Light", "Backlit / Rim Light (Halo)",
            "Golden Hour Warm Light", "Cool Daylight (neutral)", "Spotlight on black (Theater)",
            "Neon Glow (bunt)", "Window Light (natürlich, soft)"], key="prod_only_light")
        prod_reflections = st.selectbox("Reflexionen", [
            "— Standard —", "Strong mirror reflections", "Subtle soft reflections",
            "Wet / glossy surface reflections", "No reflections (matte look)"])
        if prod_reflections == "— Standard —":
            prod_reflections = ""
        prod_shadow = st.selectbox("Schatten", [
            "Soft diffused shadow", "Hard dramatic shadow", "No shadow (floating / clean)",
            "Contact shadow only (minimal)", "Long cinematic shadow"])
        prod_color_mood = st.selectbox("Farbstimmung", [
            "— Neutral —", "Warm & luxurious (gold tones)", "Cool & modern (blue/silver tones)",
            "Earthy & natural (beige/green)", "High contrast B&W", "Pastel & soft", "Dark & moody", "Vibrant & colorful"])
        if prod_color_mood == "— Neutral —":
            prod_color_mood = ""

    st.markdown("---")
    po5, po6 = st.columns(2)
    with po5:
        st.markdown("**Hintergrund**")
        prod_bg_type = st.selectbox("Hintergrund-Typ", [
            "Seamless white (E-Commerce Standard)", "Seamless black (Luxury)", "Gradient (hell nach dunkel)",
            "Gradient (dunkel nach hell)", "Textured wall (Betonwand)", "Blurred nature (Bokeh Grün)",
            "Blurred city lights (Bokeh)", "Solid color", "Matching surface extends to background"], key="prod_only_bg")
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
            "Quadrat (1:1) — Instagram / Katalog", "Hochformat (4:5) — Instagram Post",
            "Hochformat (9:16) — Story / Reels", "Querformat (16:9) — Website Banner",
            "Querformat (3:2) — Klassisch"], key="prod_only_ar")
        prod_lens = st.selectbox("Objektiv", [
            "100mm Macro (extreme Detail)", "85mm (classic product)", "50mm (natural perspective)",
            "35mm (context / lifestyle)"], key="prod_only_lens")
        prod_dof = st.selectbox("Tiefenschärfe", [
            "Everything sharp (f/8-f/11)", "Soft background blur (f/2.8)",
            "Extreme bokeh, only product sharp (f/1.4)", "Tilt-shift miniature effect"], key="prod_only_dof")
        st.markdown("**🚫 Negativ-Prompt**")
        prod_neg_presets = st.multiselect("Ausschlüsse", [
            "no people", "no hands", "no text", "no watermark", "no logo", "no blurry details",
            "no AI-generated look", "no oversaturated colors", "no cartoonish style", "no flat lighting",
            "no harsh shadows", "no distracting background", "no dust or scratches"],
            default=["no people", "no hands", "no text", "no watermark", "no logo"], key="prod_neg_presets")
        prod_neg_custom = st.text_input("Eigene Ausschlüsse (optional)", placeholder="z.B. no packaging...", key="prod_neg_custom")
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
            "💛 Emotional / Storytelling", "⭐ Social Proof / Testimonial", "🔥 Urgency / Limited Offer",
            "✨ Lifestyle / Aspirational", "💎 Product Hero / Close-Up", "🎁 Geschenk-Guide",
            "📖 Educational / Craftsmanship", "📱 UGC-Style (User Generated Content)",
            "🌿 Everyday Jewelry / Casual Wear", "🎨 SKU Showcase / Blockfarben",
            "🤖 AI-Mascot / Cartoon-Headline", "💬 Kommentar-Ad (Fake Review Look)",
            "📰 Headline-Hero (Text dominiert)", "📷 Instagram-Organic-Story",
            "🖼️ Collage / Grid-Ad", "🏷️ Clean Produkt + Offer"],
            help="Der Werbe-Typ bestimmt Bildstil, Textton und Komposition.")
        ad_mood = st.selectbox("Stimmung / Mood", [
            "Warm & Einladend", "Luxuriös & Elegant", "Jung & Trendig", "Romantisch & Verträumt",
            "Bold & Selbstbewusst", "Minimalistisch & Clean", "Festlich / Saisonal"])
        ad_format = st.selectbox("Ad Format", [
            "Facebook Feed (1:1 Quadrat)", "Facebook Feed (4:5 Hochformat)",
            "Instagram Story / Reels (9:16)", "Facebook Cover / Banner (16:9)", "Carousel Einzelbild (1:1)"])
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
            "👩 Frauen 18-24 (Trend & Self-Treat)", "👩 Frauen 25-34 (Lifestyle & Everyday Luxury)",
            "👩 Frauen 35-50 (Eleganz & Qualität)", "👨 Männer (Geschenk für Partnerin)",
            "💍 Verlobung / Hochzeit", "🎁 Muttertag / Valentinstag / Weihnachten",
            "🎓 Abschluss / Milestone-Geschenk", "👫 Paare (Matching / Partnergeschenk)"])
        ad_season = st.selectbox("Saison / Anlass (optional)", [
            "— Kein spezifischer Anlass —", "💝 Valentinstag", "🌸 Muttertag", "🎄 Weihnachten",
            "🎃 Black Friday / Cyber Monday", "☀️ Sommer / Festival", "🍂 Herbst / Back to School",
            "💍 Hochzeitssaison", "🎆 Neujahr"])
        ad_price_point = st.selectbox("Preis-Segment", [
            "💰 Budget-friendly (unter 50€)", "💎 Mid-range (50-150€)", "👑 Premium / Luxury (150€+)"])

    st.markdown("---")
    ad3, ad4 = st.columns(2)
    with ad3:
        st.markdown("**📝 Text-Overlay auf dem Bild**")
        ad_headline = st.text_input("Headline (Haupttext auf dem Bild)",
                                    placeholder="z.B. Dein Name. Dein Style.", key="ad_headline",
                                    help="Kurz & knackig. Wird prominent auf dem Bild platziert.")
        ad_subline = st.text_input("Subline (optional)",
                                   placeholder="z.B. Handgefertigt. Einzigartig wie du.", key="ad_subline")
        ad_cta = st.selectbox("Call-to-Action", [
            "Jetzt entdecken →", "Shop Now →", "Jetzt bestellen", "Sichere dir deins", "Zum Shop →",
            "Gratis Versand sichern", "Jetzt personalisieren", "Nur noch heute!", "Custom..."])
        if ad_cta == "Custom...":
            ad_cta = st.text_input("Eigener CTA", placeholder="z.B. Jetzt -20% sichern", key="ad_cta_custom")
        ad_offer = st.text_input("Angebot / Rabatt (optional)",
                                 placeholder="z.B. -20% mit Code LOVE20, Gratis Versand ab 50€", key="ad_offer")
    with ad4:
        st.markdown("**📸 Bild-Komposition**")
        ad_composition = st.selectbox("Layout", [
            "Close-Up Produkt + Text oben/unten", "Model trägt Produkt + Text-Overlay",
            "Split: Links Model, Rechts Produkt-Detail", "Lifestyle-Szene + dezenter Text",
            "Produkt auf Hintergrund + große Headline", "Vorher/Nachher (ohne/mit Schmuck)",
            "Textur-Hintergrund (Stoff, Strick, Haut)", "Layering-Shot (mehrere Teile zusammen)",
            "4er Grid / Collage", "Story-Textfeld-Look (Instagram organic)"])
        ad_text_position = st.selectbox("Text-Position", [
            "Oben (über dem Bild)", "Unten (unter dem Produkt)", "Mittig (Overlay auf Bild)",
            "Links (Text links, Bild rechts)", "Minimal (nur kleiner CTA-Button)"])
        st.markdown("**🔄 Model-Ansicht / Drehung**")
        ad_model_view = st.selectbox("Model-Perspektive", [
            "— Automatisch (passend zum Layout) —", "👤 Frontal (von vorne, Blick zur Kamera)",
            "👤 Leicht gedreht (3/4 Ansicht, schräg)", "👤 Seitenprofil (komplett von der Seite)",
            "👤 Rückenansicht (von hinten, Halskette/Rücken sichtbar)",
            "👤 Über-die-Schulter (Rücken + Gesicht teils sichtbar)", "👤 Schräg von hinten (3/4 Rücken)",
            "🤳 Selfie-Perspektive (Arm ausgestreckt, leicht von oben)"],
            help="Bestimmt aus welcher Richtung das Model gezeigt wird. Wichtig für Halsketten (Rücken) und Ohrringe (Seitenprofil).")
        ad_color_scheme = st.selectbox("Farbschema", [
            "Brand Gold (#FFD700 auf Dunkel)", "Weiß & Clean (heller Hintergrund)",
            "Schwarz & Luxus (dunkler Hintergrund)", "Rosé / Pastelltöne", "Natur / Erdtöne",
            "Kräftige Farben (Pop Art Style)"])
        ad_font = st.selectbox("Schriftart für Text-Overlay", [
            "Elegant Serif (Playfair Display / Didot)", "Modern Sans-Serif (Montserrat / Helvetica)",
            "Luxury Thin (Futura Light / Gill Sans)", "Handwritten / Script (Parisienne / Great Vibes)",
            "Bold Impact (Bebas Neue / Oswald)", "Minimalist (Inter / DM Sans)"],
            help="Beeinflusst wie der Text auf dem Bild gerendert wird.")
        ad_ref_files = st.file_uploader("Produkt-Referenzbilder für Ad (max. 4)",
            type=["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key="ad_ref_upload",
            help="💡 Tipp: Lade mindestens 1 Bild hoch wo der Schmuck GETRAGEN wird — das hilft bei der Größen-Proportion!")
        if ad_ref_files and len(ad_ref_files) > 4:
            st.warning("Maximal 4 Bilder!")
            ad_ref_files = ad_ref_files[:4]

    st.markdown("---")
    ad5, ad6 = st.columns(2)
    with ad5:
        st.markdown("**🎯 Funnel-Stage & Hook**")
        ad_funnel = st.selectbox("Funnel-Stage", [
            "🔝 TOFU — Cold Audience (Aufmerksamkeit gewinnen)",
            "🔄 MOFU — Warm Audience (Vertrauen aufbauen)",
            "🔥 BOFU — Hot Audience / Retargeting (Kauf auslösen)"],
            help="TOFU: Brand Discovery. MOFU: Consideration. BOFU: Conversion/Retargeting.")
        ad_hook = st.selectbox("Scroll-Stopper / Hook", [
            "Kontrast (Vorher/Nachher, mit/ohne Schmuck)", "Extreme Close-Up (Makro-Detail als Blickfang)",
            "Unerwarteter Winkel (von unten, Spiegelung, etc.)", "Emotionaler Moment (Freudentränen, Überraschung)",
            "Bold Text First (große Headline dominiert)", "Produkt in Bewegung (Glitzern, Licht-Reflexe)",
            "Social Proof (Sternebewertung, Kundenzitat)", "Luxus-Setting (Champagner, Rosenblätter, Samt)",
            "Blockfarben (kräftige Farbflächen stoppen den Scroll)", "Absurdes/Unerwartetes Bild (What the…-Moment)",
            "Hand hält Produkt (taktil, Instagram-Story-Stil)", "Produkt in Verpackung (Unboxing-Moment)"],
            help="Der 'Hook' fängt in den ersten 0.5 Sekunden die Aufmerksamkeit.")
        ad_trust_signals = st.multiselect("Vertrauens-Signale (auf dem Bild)", [
            "⭐ 5-Sterne-Bewertung", "❤️ 'Bestseller' Badge", "🚚 'Gratis Versand' Badge",
            "🔒 'Sicher bezahlen' Icon", "🏷️ Preis auf dem Bild", "📦 '1000+ verkauft'",
            "✅ 'Handgefertigt' Siegel", "↩️ 'Kostenlose Rückgabe'"],
            help="Trust-Badges auf dem Bild erhöhen die Conversion-Rate signifikant.")
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
                "🔍 Zoom-Reveal (Weit → Nah → Makro → Am Model)"])
            ad_carousel_cta_last = st.checkbox("Letzte Slide = CTA-Slide", value=True,
                                               help="Die letzte Slide enthält einen starken Call-to-Action.")
        else:
            ad_carousel_count = 1
            ad_carousel_story = ""
            ad_carousel_cta_last = False
        st.markdown("**🧠 Conversion-Psychologie**")
        ad_psych_triggers = st.multiselect("Psychologische Trigger", [
            "⏰ Urgency (begrenzte Zeit)", "📉 Scarcity (nur noch X verfügbar)",
            "🎁 Reciprocity (Gratis-Geschenk bei Kauf)", "👥 Social Proof (andere kaufen das auch)",
            "💎 Exclusivity (Limited Edition / VIP)", "🪞 Self-Image (so sieht das an DIR aus)",
            "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)",
            "💰 Value Framing (Preis im Kontext: 'weniger als 1€/Tag')"],
            default=["🪞 Self-Image (so sieht das an DIR aus)", "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)"],
            help="Psychologische Prinzipien die nachweislich Conversion steigern.")

    st.markdown("---")
    ad7, ad8 = st.columns(2)
    with ad7:
        st.markdown("**🔬 3-2-2 A/B-Test Methode**")
        use_322 = st.checkbox("3-2-2 Methode aktivieren", value=False,
                              help="Generiert 3 Bild-Varianten, 2 Headlines und 2 Primary-Texts für systematisches A/B-Testing.")
        if use_322:
            st.info("**So funktioniert's:**\n- 🖼️ **3 Bild-Varianten**\n- 📝 **2 Headlines** (emotional vs. rational)\n- 💬 **2 Primary Texts** (kurz vs. lang)\n\n→ Bis zu **12 Kombinationen** zum Testen!")
            ad_322_headlines = []
            ad_322_h1 = st.text_input("Headline A (emotional)", placeholder="z.B. Dein Name. Deine Geschichte.", key="h322_1")
            ad_322_h2 = st.text_input("Headline B (rational)", placeholder="z.B. 925 Sterling Silber. Gratis Versand.", key="h322_2")
            if ad_322_h1: ad_322_headlines.append(ad_322_h1)
            if ad_322_h2: ad_322_headlines.append(ad_322_h2)
            ad_322_texts = []
            ad_322_t1 = st.text_area("Primary Text A (kurz, emotional)", placeholder="Jedes Stück erzählt deine Geschichte. ✨ Handgefertigt & personalisierbar.", key="t322_1", height=70)
            ad_322_t2 = st.text_area("Primary Text B (länger, mit Details)", placeholder="Unsere Ketten werden aus 925 Sterling Silber handgefertigt. Personalisierbar mit Namen oder Datum. Gratis Versand. 30 Tage Rückgabe.", key="t322_2", height=70)
            if ad_322_t1: ad_322_texts.append(ad_322_t1)
            if ad_322_t2: ad_322_texts.append(ad_322_t2)
        else:
            ad_322_headlines = []
            ad_322_texts = []
    with ad8:
        st.markdown("**📊 Creative Diversity & Sequencing**")
        st.warning("⚠️ **Meta's Algorithmus bestraft fehlende Vielfalt!** Generiere mind. **3-4 visuell unterschiedliche Creatives** pro Kampagne, sonst steigen die CPMs.")
        st.markdown("**📋 Empfohlene Ad-Sequenz** (Funnel-Reihenfolge):")
        st.markdown("1. **TOFU (Cold):** UGC oder Lifestyle → *Aufmerksamkeit*\n2. **MOFU (Warm):** Social Proof oder Educational → *Vertrauen*\n3. **BOFU (Hot):** Urgency oder Product Hero → *Kauf*")
        ad_creative_angle = st.selectbox("Kreativ-Winkel für Vielfalt", [
            "— Standard (wie oben konfiguriert) —", "🔄 Variante: Anderer Hintergrund/Setting",
            "🔄 Variante: Anderer Kamerawinkel", "🔄 Variante: Andere Stimmung/Beleuchtung",
            "🔄 Variante: Anderes Model/Styling"],
            help="Nutze dies um schnell eine visuell verschiedene Variante zu generieren.")

    st.markdown("---")
    cg_col1, cg_col2 = st.columns(2)
    with cg_col1:
        st.markdown("**🧲 Curiosity-Gap Modus**")
        ad_curiosity_gap = st.checkbox("Curiosity-Gap aktivieren", value=False,
                                        help="Die Ad weckt Neugier statt alles zu verkaufen. Perfekt für TOFU.")
        if ad_curiosity_gap:
            st.info("**Curiosity-Gap = Neugier öffnen, nicht schließen.** Die Ad verspricht eine Lösung/ein Geheimnis, verrät aber NICHT alles.")
            ad_curiosity_hook = st.selectbox("Curiosity-Typ", [
                "❓ Frage stellen (die man beantworten will)", "🔢 Zahl/Statistik (überraschend)",
                "🚫 Mythos entlarven ('Das macht jeder falsch...')", "🤫 Geheimnis andeuten ('Was Top-Stylistinnen wissen')",
                "😱 Schock/Überraschung ('Das wusstest du nicht über...')"], key="curiosity_hook_type")
        else:
            ad_curiosity_hook = None
        st.markdown("**🎭 Primäre Emotion**")
        ad_primary_emotion = st.selectbox("Welche Emotion soll die Ad auslösen?", [
            "— Automatisch (passend zum Werbe-Typ) —", "😂 Humor (lustig, teilbar, viral)",
            "😨 Fear / Pain (Problem ansprechen)", "🌟 Hope (Hoffnung, Transformation)",
            "🤝 Belonging (Zugehörigkeit, 'das ist für mich')", "😍 Desire (Begehren, 'das will ich haben')",
            "🥺 Nostalgie (Erinnerung, sentimentaler Wert)"],
            help="Emotion ist einer der zentralen psychologischen Trigger jeder performanten Ad.")
    with cg_col2:
        st.markdown("**📋 Ad Brief Generator**")
        ad_generate_brief = st.checkbox("Ad Brief als Text generieren", value=False,
                                         help="Generiert zusätzlich ein strukturiertes Ad Brief (Concept, Angle, Persona, Headline, CTA, Visual Direction).")
        if ad_generate_brief:
            st.info("Enthält: Concept · Creative Type · Angle · Persona · Headline · CTA · Visual Direction.")
        st.markdown("**🔀 4-Hebel Diversity Check**")
        st.caption("Meta wertet 'echte Diversity' nur, wenn mind. 2-3 Hebel gleichzeitig verändert werden.")
        diversity_persona = st.checkbox("✅ Persona variiert", value=False, key="div_persona",
                                         help="Selbes Produkt, anderer Käufer (z.B. Athletin vs. Office-Workerin)")
        diversity_messaging = st.checkbox("✅ Messaging variiert", value=False, key="div_msg",
                                           help="Anderer Kaufgrund (z.B. 'Selbstgeschenk' vs. 'Geschenk für sie')")
        diversity_hook = st.checkbox("✅ Hook variiert", value=False, key="div_hook",
                                      help="Andere Aufmerksamkeits-Methode (Visual vs. Bold Claim vs. Demo)")
        diversity_format = st.checkbox("✅ Format variiert", value=False, key="div_format",
                                        help="Anderer Wrapper (UGC, Static, Carousel, Story, Grid)")
        diversity_count = sum([diversity_persona, diversity_messaging, diversity_hook, diversity_format])
        if diversity_count == 0:
            st.error("🔴 **0/4 Hebel** — Meta behandelt alles als dieselbe Ad. Hohe CPMs!")
        elif diversity_count == 1:
            st.warning("🟡 **1/4 Hebel** — Nicht genug. Nur den Hook zu ändern zählt NICHT als echte Diversity.")
        else:
            st.success(f"🟢 **{diversity_count}/4 Hebel** — Gute Diversity! Meta wertet das als verschiedene Ads. 👍")


# --- AD CREATIVE PROMPT BUILDER ---
def build_ad_creative_prompt():
    """Build a prompt for generating Facebook/Instagram Ad Creatives."""
    format_map = {
        "Facebook Feed (1:1 Quadrat)": "1:1 (Square)",
        "Facebook Feed (4:5 Hochformat)": "4:5 (Portrait)",
        "Instagram Story / Reels (9:16)": "9:16 (Vertical / Full Screen)",
        "Facebook Cover / Banner (16:9)": "16:9 (Landscape / Banner)",
        "Carousel Einzelbild (1:1)": "1:1 (Square)",
    }
    ad_ar = format_map.get(ad_format, "1:1 (Square)")

    type_instructions = {
        "💛 Emotional / Storytelling": (
            "VISUAL STYLE: Warm, cinematic storytelling. Show a genuine emotional moment — a woman touching "
            "her necklace in the mirror, receiving jewelry as a gift, or a candid moment of joy. Evoke FEELING. "
            "Soft warm lighting, golden hour tones, slightly shallow depth of field."),
        "⭐ Social Proof / Testimonial": (
            "VISUAL STYLE: Authentic, relatable. A real-looking woman wearing the jewelry in an everyday setting. "
            "Natural lighting, slightly less polished than editorial — like a real customer photo / UGC. Warm and approachable."),
        "🔥 Urgency / Limited Offer": (
            "VISUAL STYLE: High-impact, attention-grabbing. Bold composition, product prominent, dynamic high-contrast "
            "lighting. Feels URGENT. Clean background so text overlay is readable."),
        "✨ Lifestyle / Aspirational": (
            "VISUAL STYLE: Aspirational lifestyle. Beautiful model in a luxurious/desirable setting — rooftop, designer "
            "apartment, sun-drenched terrace. Jewelry as part of a complete aspirational look. Fashion-editorial quality."),
        "💎 Product Hero / Close-Up": (
            "VISUAL STYLE: Product is the absolute hero. Extreme close-up/macro. Every detail visible — metal texture, "
            "engraving, gemstone facets, chain links. Clean minimal background. Product fills 60-70% of the frame."),
        "🎁 Geschenk-Guide": (
            "VISUAL STYLE: Gift-giving scene. Jewelry in beautiful packaging — gift box, ribbon, tissue. Or hands opening "
            "a box, surprise expression. Warm festive lighting. Triggers the emotion of GIVING/RECEIVING."),
        "📖 Educational / Craftsmanship": (
            "VISUAL STYLE: Behind-the-scenes artisan focus. Close-up showing craftsmanship — handmade texture, hallmarks, "
            "material quality. Clean informational composition highlighting QUALITY and CRAFTSMANSHIP."),
        "📱 UGC-Style (User Generated Content)": (
            "VISUAL STYLE: MUST look like a real customer selfie, NOT a pro ad. Smartphone shot, natural light, slightly "
            "imperfect framing. Real-person model, casual outfit, minimal makeup. Real-life setting: mirror selfie, café, "
            "car, kitchen, couch. Warm cozy Instagram-filter grading. Jewelry visible but not the 'focus'. 100% AUTHENTIC, raw."),
        "🌿 Everyday Jewelry / Casual Wear": (
            "VISUAL STYLE: Jewelry as an effortless everyday accessory. Model in daily life — laptop, dog walk, brunch, "
            "casual weekend. Subtle delicate jewelry in a casual look. Bright natural daylight. Approachable, real, not glamorous."),
        "🎨 SKU Showcase / Blockfarben": (
            "VISUAL STYLE: BLOCKFARBEN — Bild in 3-4 vertikale Farbspalten. Jede Spalte eine Variante (Gold, Silber, "
            "Roségold) auf kräftigem Farb-Hintergrund (ROT, BEIGE, GRAU, NAVY, SMARAGD). Kleines Label je Variante. "
            "Produkt am besten in der Hand. KEIN weißer Hintergrund. Die FARBE ist der Scroll-Stopper."),
        "🤖 AI-Mascot / Cartoon-Headline": (
            "VISUAL STYLE: ABSURDES AI-BILD als Scroll-Stopper. Surreal/humorvoll, NICHT wie eine typische Schmuck-Ad. "
            "RIESIGE BOLD HEADLINE oben, kleine Sub-Copy darunter, niedriger CTA ganz unten. Stoppt den Scroll weil ungewöhnlich."),
        "💬 Kommentar-Ad (Fake Review Look)": (
            "VISUAL STYLE: SOCIAL-PROOF-KOMMENTAR-LOOK. OBEN: 'Kommentar' (rundes Profilbild, Name, kurze Review, Sterne). "
            "MITTE: vibrantes Produktbild. UNTEN: CTA-Button. Wirkt wie ein echter begeisterter Kundenkommentar. Authentisch."),
        "📰 Headline-Hero (Text dominiert)": (
            "VISUAL STYLE: DIE HEADLINE IST DER STAR (40-50% des Bildes). Spricht direkt den ICP an — Problem, Emotion, "
            "Versprechen. Produkt sichtbar aber sekundär. Durchgehendes Farbthema. Magazin-Cover / Werbeplakat-Feel."),
        "📷 Instagram-Organic-Story": (
            "VISUAL STYLE: Wie ein ORGANISCHER Instagram-Story-Post — keine Werbung erkennbar. Hand hält das Produkt. "
            "Text in Instagram-Story-Textfeldern (Sticker-Stil). Alltagssituation, leicht unscharf wie Handy-Foto. Verschmilzt mit dem Feed."),
        "🖼️ Collage / Grid-Ad": (
            "VISUAL STYLE: 4-TEILIGES GRID. Oben-links Produkt-Close-Up, oben-rechts Headline/Benefit auf Farbfläche, "
            "unten-links Lifestyle, unten-rechts Benefit/CTA. Alle 4 farblich abgestimmt. Ungewöhnlich im Feed = Scroll-Stopper."),
        "🏷️ Clean Produkt + Offer": (
            "VISUAL STYLE: MINIMALISTISCH & CLEAN. Produkt auf einfarbigem Hintergrund. Markenname dominant oben, Produkt "
            "zentral perfekt beleuchtet, klares Angebot/USP unten. KEIN Model, keine Ablenkung. Einfachheit IST der Scroll-Stopper."),
    }
    style_instr = type_instructions.get(ad_type, type_instructions["✨ Lifestyle / Aspirational"])

    mood_map = {
        "Warm & Einladend": "COLOR MOOD: Warm golden tones, honey-colored lighting, cozy and inviting.",
        "Luxuriös & Elegant": "COLOR MOOD: Rich deep tones. Black, gold, champagne. Luxury feel with high contrast.",
        "Jung & Trendig": "COLOR MOOD: Fresh, vibrant. Bright natural light, clean whites, pops of color. Modern and youthful.",
        "Romantisch & Verträumt": "COLOR MOOD: Soft pastels, rose tones, dreamy bokeh. Gentle, ethereal.",
        "Bold & Selbstbewusst": "COLOR MOOD: Strong contrast, saturated colors, powerful lighting. Confident and bold.",
        "Minimalistisch & Clean": "COLOR MOOD: Neutral tones, lots of whitespace, minimal distractions. Ultra-clean.",
        "Festlich / Saisonal": "COLOR MOOD: Festive — sparkle, warmth, celebration. Rich reds, golds, greens depending on season.",
    }
    mood_instr = mood_map.get(ad_mood, "")

    target_map = {
        "👩 Frauen 18-24 (Trend & Self-Treat)": "MODEL: Young woman, early 20s, trendy and confident. Casual-chic. Relatable, not overly glamorous.",
        "👩 Frauen 25-34 (Lifestyle & Everyday Luxury)": "MODEL: Woman late 20s to early 30s. Stylish, put-together but natural. Modern lifestyle setting.",
        "👩 Frauen 35-50 (Eleganz & Qualität)": "MODEL: Elegant woman late 30s to 40s. Sophisticated, timeless styling. Quality and refinement.",
        "👨 Männer (Geschenk für Partnerin)": "SCENE: The gift-giving moment — hands holding a jewelry box. Masculine hands presenting. Warm romantic lighting.",
        "💍 Verlobung / Hochzeit": "SCENE: Romantic, wedding-adjacent. White, gold, floral. Dreamy fairy-tale quality. Focus on rings/bridal jewelry.",
        "🎁 Muttertag / Valentinstag / Weihnachten": "SCENE: Gift-giving moment for the occasion. Festive elements, warm romantic atmosphere.",
        "🎓 Abschluss / Milestone-Geschenk": "SCENE: Celebration moment. Young woman wearing the jewelry proudly. Achievement, pride.",
        "👫 Paare (Matching / Partnergeschenk)": "SCENE: Two people, romantic setting. Matching/complementary pieces. Connection and togetherness.",
    }
    target_instr = target_map.get(ad_target, "")

    model_view_instr = ""
    if ad_model_view and "Automatisch" not in ad_model_view:
        view_map = {
            "👤 Frontal (von vorne, Blick zur Kamera)": "MODEL VIEW: FRONTAL — facing the camera. Full face visible. Front-body jewelry prominent.",
            "👤 Leicht gedreht (3/4 Ansicht, schräg)": "MODEL VIEW: THREE-QUARTER — turned 30-45°. Adds depth. Ideal for showing how necklaces drape.",
            "👤 Seitenprofil (komplett von der Seite)": "MODEL VIEW: FULL SIDE PROFILE — 90°. Perfect for earrings, jawline, side chain line.",
            "👤 Rückenansicht (von hinten, Halskette/Rücken sichtbar)": "MODEL VIEW: BACK VIEW — from behind, hair to one side revealing the nape. Shows clasp, back of pendant, chain on the back. Backless top. Elegant, intimate.",
            "👤 Über-die-Schulter (Rücken + Gesicht teils sichtbar)": "MODEL VIEW: OVER-THE-SHOULDER — camera behind, face partly turned. Jewelry from behind with human connection.",
            "👤 Schräg von hinten (3/4 Rücken)": "MODEL VIEW: THREE-QUARTER BACK — turned away ~45°. Natural 'walking away' perspective.",
            "🤳 Selfie-Perspektive (Arm ausgestreckt, leicht von oben)": "MODEL VIEW: SELFIE — slightly from above, one arm extended. Casual, Instagram-native. Necklace/décolleté visible.",
        }
        model_view_instr = view_map.get(ad_model_view, "")

    comp_map = {
        "Close-Up Produkt + Text oben/unten": "COMPOSITION: Tight close-up of the jewelry centered. Clear space top/bottom for text. Clean background.",
        "Model trägt Produkt + Text-Overlay": "COMPOSITION: Medium shot, model wearing the jewelry. Breathing room for text. Model slightly off-center.",
        "Split: Links Model, Rechts Produkt-Detail": "COMPOSITION: Split — left model wearing it, right extreme close-up detail. Divide in the middle.",
        "Lifestyle-Szene + dezenter Text": "COMPOSITION: Wide lifestyle scene. Text small in a corner. Focus on the aspirational image.",
        "Produkt auf Hintergrund + große Headline": "COMPOSITION: Product on a clean background, lots of negative space for a large headline. Product centered.",
        "Vorher/Nachher (ohne/mit Schmuck)": "COMPOSITION: Before/after side-by-side — bare neckline vs. with jewelry. Transformation feel.",
        "Textur-Hintergrund (Stoff, Strick, Haut)": "COMPOSITION: Product on a TEXTURED surface — knit, linen, silk, wood, marble, skin. Tactile, sensory, warm close-up.",
        "Layering-Shot (mehrere Teile zusammen)": "COMPOSITION: Multiple pieces styled TOGETHER — layered necklaces, stacked rings. Show the ENSEMBLE. Each piece identifiable.",
        "4er Grid / Collage": "COMPOSITION: 2x2 GRID — product detail, lifestyle, text/benefit, CTA/offer. Cohesive palette, clean dividers.",
        "Story-Textfeld-Look (Instagram organic)": "COMPOSITION: Instagram Story layout — text in Story sticker fields. Hand-held product centered. Casual, spontaneous.",
    }
    comp_instr = comp_map.get(ad_composition, "")

    text_elements = []

    def spell_out(text):
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
            'CRITICAL TEXT RENDERING RULE: Reproduce EVERY text element EXACTLY letter-by-letter. '
            'Do NOT rearrange, abbreviate, or rephrase. Do NOT add or skip letters. Verify before rendering.')

    personalization_instr = ""
    if is_personalizable:
        personalization_instr = (
            "\nPERSONALIZATION SELLING POINT: This product is PERSONALIZABLE. Show or suggest personalization — "
            "a name engraved on the pendant, initials, custom text. If text on the jewelry, use an example name like "
            "'EMMA' or 'MIA'. Make it visually clear this piece can be customized.")

    dimensions_instr = ""
    if ad_use_dimensions and ad_pendant_width and ad_pendant_height:
        dimensions_instr = (
            f"\nPRODUCT DIMENSIONS — CRITICAL: The pendant is exactly {ad_pendant_width}mm wide x {ad_pendant_height}mm tall. "
            f"VERY SMALL — like a fingernail. Render at TRUE real-world size on the body. Do NOT enlarge or exaggerate.")
        if ad_chain_length and ad_chain_length > 0:
            seat = 'at the collarbone' if ad_chain_length <= 40 else 'below the collarbone' if ad_chain_length <= 50 else 'at mid-chest level'
            dimensions_instr += f" The chain is {ad_chain_length}cm long, sitting {seat}."

    season_instr = ""
    if ad_season and "Kein" not in ad_season:
        season_clean = ad_season.split(" ", 1)[1] if " " in ad_season else ad_season
        season_instr = f"\nSEASONAL CONTEXT: This ad is for {season_clean}. Incorporate subtle seasonal elements in styling, lighting, or props."

    color_map = {
        "Brand Gold (#FFD700 auf Dunkel)": "COLOR SCHEME: Dark background (near-black/deep navy), gold accents. Luxury, premium feel.",
        "Weiß & Clean (heller Hintergrund)": "COLOR SCHEME: Bright white/cream background. Clean, airy, modern. Minimal palette.",
        "Schwarz & Luxus (dunkler Hintergrund)": "COLOR SCHEME: Deep black background, dramatic lighting on the product. High-end, exclusive.",
        "Rosé / Pastelltöne": "COLOR SCHEME: Soft rose, blush, light lavender. Feminine, romantic, gentle.",
        "Natur / Erdtöne": "COLOR SCHEME: Warm earth tones — sand, terracotta, olive, brown. Natural, organic.",
        "Kräftige Farben (Pop Art Style)": "COLOR SCHEME: Bold vibrant colors, high saturation, eye-catching. Modern, edgy.",
    }
    color_instr = color_map.get(ad_color_scheme, "")

    pos_map = {
        "Oben (über dem Bild)": "TEXT PLACEMENT: Reserve the top 25% for text. Keep it simpler/darker for readability.",
        "Unten (unter dem Produkt)": "TEXT PLACEMENT: Reserve the bottom 25% for text. Keep it simpler for readability.",
        "Mittig (Overlay auf Bild)": "TEXT PLACEMENT: Center overlay. Ensure a semi-transparent or natural dark/light zone for readability.",
        "Links (Text links, Bild rechts)": "TEXT PLACEMENT: Left third simpler/darker for text. Main visual on the right two-thirds.",
        "Minimal (nur kleiner CTA-Button)": "TEXT PLACEMENT: Only a small CTA button bottom-right. The image does the talking.",
    }
    pos_instr = pos_map.get(ad_text_position, "")

    price_map = {
        "💰 Budget-friendly (unter 50€)": "PRICE POSITIONING: Accessible everyday luxury. Emphasize value and versatility.",
        "💎 Mid-range (50-150€)": "PRICE POSITIONING: Quality meets style. Premium but relatable. Everyday elegance.",
        "👑 Premium / Luxury (150€+)": "PRICE POSITIONING: High-end luxury. Exclusive, aspirational. Every element screams quality.",
    }
    price_instr = price_map.get(ad_price_point, "")

    font_map = {
        "Elegant Serif (Playfair Display / Didot)": "elegant high-contrast serif (Playfair Display / Didot) — luxurious, editorial, classic",
        "Modern Sans-Serif (Montserrat / Helvetica)": "clean geometric sans-serif (Montserrat / Helvetica) — modern, professional",
        "Luxury Thin (Futura Light / Gill Sans)": "ultra-thin refined sans-serif (Futura Light) — minimal, high-end elegance",
        "Handwritten / Script (Parisienne / Great Vibes)": "flowing script (Parisienne / Great Vibes) — personal, romantic, intimate",
        "Bold Impact (Bebas Neue / Oswald)": "bold condensed display (Bebas Neue / Oswald) — attention-grabbing, strong, urgent",
        "Minimalist (Inter / DM Sans)": "clean minimalist sans-serif (Inter / DM Sans) — understated, modern",
    }
    font_instr = font_map.get(ad_font, "clean, modern sans-serif")

    funnel_map = {
        "🔝 TOFU — Cold Audience (Aufmerksamkeit gewinnen)": "FUNNEL STAGE: TOFU (Cold). Priority: STOP THE SCROLL. Striking, emotional, curiosity-inducing. Don't hard-sell. Make them REMEMBER you.",
        "🔄 MOFU — Warm Audience (Vertrauen aufbauen)": "FUNNEL STAGE: MOFU (Warm). Priority: BUILD TRUST. Real-life context, quality, social proof, trust signals.",
        "🔥 BOFU — Hot Audience / Retargeting (Kauf auslösen)": "FUNNEL STAGE: BOFU (Hot/Retargeting). Priority: CONVERT NOW. Product prominent, clear offer/urgency, strong CTA.",
    }
    funnel_instr = funnel_map.get(ad_funnel, "")

    hook_map = {
        "Kontrast (Vorher/Nachher, mit/ohne Schmuck)": "HOOK: Visual CONTRAST — the transformation, with/without the jewelry. Immediately striking.",
        "Extreme Close-Up (Makro-Detail als Blickfang)": "HOOK: EXTREME CLOSE-UP. Macro detail — gemstone facets, metal texture, engraving.",
        "Unerwarteter Winkel (von unten, Spiegelung, etc.)": "HOOK: UNEXPECTED ANGLE — mirror reflection, from below, dramatic perspective.",
        "Emotionaler Moment (Freudentränen, Überraschung)": "HOOK: A genuine EMOTIONAL MOMENT — surprise, joy, happy tears. Human emotion is the hook.",
        "Bold Text First (große Headline dominiert)": "HOOK: TEXT is the hook. Large bold provocative headline/question. Image supports the text.",
        "Produkt in Bewegung (Glitzern, Licht-Reflexe)": "HOOK: Product CATCHING LIGHT — sparkle, shimmer across metal and stones. The 'glitter' is the scroll-stopper.",
        "Social Proof (Sternebewertung, Kundenzitat)": "HOOK: Lead with SOCIAL PROOF — star rating, customer quote, 'bestseller' badge.",
        "Luxus-Setting (Champagner, Rosenblätter, Samt)": "HOOK: LUXURY ATMOSPHERE — velvet, champagne, rose petals, candlelight. Premium value before product is noticed.",
        "Blockfarben (kräftige Farbflächen stoppen den Scroll)": "HOOK: BOLD BLOCK COLORS. Large saturated contrasting areas. Color is processed before shape or text.",
        "Absurdes/Unerwartetes Bild (What the…-Moment)": "HOOK: 'WHAT THE…' MOMENT — surreal/humorous, forces a double-take. Break the feed pattern.",
        "Hand hält Produkt (taktil, Instagram-Story-Stil)": "HOOK: A HAND HOLDING THE PRODUCT close to camera — tactile, personal, Story-style. Hand matches the audience.",
        "Produkt in Verpackung (Unboxing-Moment)": "HOOK: UNBOXING MOMENT — jewelry in packaging being opened. Gift box, ribbon. Anticipation + gift dopamine.",
    }
    hook_instr = hook_map.get(ad_hook, "")

    trust_badges_instr = ""
    if ad_trust_signals:
        badge_texts = [s.split(" ", 1)[1] if " " in s else s for s in ad_trust_signals]
        trust_badges_instr = (f"TRUST BADGES ON IMAGE: small professional badges/icons: {', '.join(badge_texts)}. "
                              f"Place subtly (corner/edge) — visible but not dominating.")

    psych_instr = ""
    if ad_psych_triggers:
        trigger_details = {
            "⏰ Urgency (begrenzte Zeit)": "Visual urgency — timer, 'Nur heute', limited-time cue",
            "📉 Scarcity (nur noch X verfügbar)": "Scarcity — 'Fast ausverkauft' / 'Nur noch 3 verfügbar'",
            "🎁 Reciprocity (Gratis-Geschenk bei Kauf)": "Free gift element — gift box, bonus, 'Gratis dazu' badge",
            "👥 Social Proof (andere kaufen das auch)": "Social proof — customer count, reviews, 'Beliebteste Wahl' badge",
            "💎 Exclusivity (Limited Edition / VIP)": "Exclusivity — 'Limited Edition', premium packaging",
            "🪞 Self-Image (so sieht das an DIR aus)": "Help the viewer see THEMSELVES wearing it — relatable model, achievable lifestyle",
            "❤️ Emotional Anchoring (Liebe, Erinnerung, Meilenstein)": "Anchor to emotion — love, memory, milestone. Jewelry = a FEELING",
            "💰 Value Framing (Preis im Kontext: 'weniger als 1€/Tag')": "Frame the value — show what you GET. Quality-to-price ratio",
        }
        active_triggers = [trigger_details.get(t, "") for t in ad_psych_triggers if t in trigger_details]
        if active_triggers:
            psych_instr = "CONVERSION PSYCHOLOGY:\n" + "\n".join(f"- {t}" for t in active_triggers)

    angle_instr = ""
    if ad_creative_angle and "Standard" not in ad_creative_angle:
        angle_map = {
            "🔄 Variante: Anderer Hintergrund/Setting": "CREATIVE VARIATION: COMPLETELY DIFFERENT background/setting. Indoors↔outdoors, studio↔natural. Visual diversity.",
            "🔄 Variante: Anderer Kamerawinkel": "CREATIVE VARIATION: UNUSUAL camera angle — from below, bird's eye, extreme side profile. Break the perspective.",
            "🔄 Variante: Andere Stimmung/Beleuchtung": "CREATIVE VARIATION: CONTRASTING lighting — warm↔cool, bright↔moody. Different emotional atmosphere.",
            "🔄 Variante: Anderes Model/Styling": "CREATIVE VARIATION: DIFFERENT look — styling, hair, outfit vibe. Demographic diversity.",
        }
        angle_instr = angle_map.get(ad_creative_angle, "")

    curiosity_instr = ""
    if ad_curiosity_gap and ad_curiosity_hook:
        curiosity_map = {
            "❓ Frage stellen (die man beantworten will)": "CURIOSITY GAP — ASK A QUESTION the viewer wants answered. Don't answer it in the ad. The image amplifies curiosity.",
            "🔢 Zahl/Statistik (überraschend)": "CURIOSITY GAP — SURPRISING NUMBER ('97% machen diesen Fehler'). The number stops the scroll. Don't explain.",
            "🚫 Mythos entlarven ('Das macht jeder falsch...')": "CURIOSITY GAP — MYTH BUSTING. Challenge a belief. Cognitive dissonance — they must click to resolve it.",
            "🤫 Geheimnis andeuten ('Was Top-Stylistinnen wissen')": "CURIOSITY GAP — INSIDER SECRET. Hint at exclusive knowledge. Aspirational, exclusive tone.",
            "😱 Schock/Überraschung ('Das wusstest du nicht über...')": "CURIOSITY GAP — SHOCK/SURPRISE. Lead with something unexpected. Striking image matching the shock factor.",
        }
        curiosity_instr = curiosity_map.get(ad_curiosity_hook, "")

    emotion_instr = ""
    if ad_primary_emotion and "Automatisch" not in ad_primary_emotion:
        emotion_map = {
            "😂 Humor (lustig, teilbar, viral)": "PRIMARY EMOTION: HUMOR. Make the viewer smile/laugh. Insider jokes, playful copy, unexpected twist. Shareable. Product stays desirable.",
            "😨 Fear / Pain (Problem ansprechen)": "PRIMARY EMOTION: FEAR/PAIN. Address a pain point (bad gift, cheap-looking jewelry, jewelry turning green). Show PROBLEM then SOLUTION. Empathetic, not fear-mongering.",
            "🌟 Hope (Hoffnung, Transformation)": "PRIMARY EMOTION: HOPE. Show TRANSFORMATION — before/after of owning this. Possibility, fresh start. Uplifting, inspiring.",
            "🤝 Belonging (Zugehörigkeit, 'das ist für mich')": "PRIMARY EMOTION: BELONGING. 'This brand GETS me.' Exact target demographic, relatable situation. Shared identity.",
            "😍 Desire (Begehren, 'das will ich haben')": "PRIMARY EMOTION: DESIRE. Make it look SO desirable — lush lighting, perfect sparkle, seductive angle. 'I NEED this.'",
            "🥺 Nostalgie (Erinnerung, sentimentaler Wert)": "PRIMARY EMOTION: NOSTALGIA. Memories, milestones, sentimental moments. Warm golden vintage feel. A KEEPER beyond material value.",
        }
        emotion_instr = emotion_map.get(ad_primary_emotion, "")

    prompt = f"""FACEBOOK / INSTAGRAM AD CREATIVE — {ad_ar}

PURPOSE: This is a paid advertising creative for Facebook/Instagram. It must STOP THE SCROLL within 0.5 seconds.

PRODUCT: '{product}'
PRODUCT IDENTITY — ABSOLUTE RULE: If a reference image is provided, reproduce the product 1:1 IDENTICALLY.
Do NOT alter, redesign, simplify, or 'improve' it. Do NOT change shape, color, material, texture, chain style,
pendant design, number of stones, metal color, or size. This is a REAL product customers will receive — any deviation is false advertising.
{target_instr}
{model_view_instr}

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

SKIN: Realistic skin with natural texture, visible pores, subtle imperfections. NO airbrushed/plastic/CGI skin.

{body_description}

{"TEXT ELEMENTS TO INCLUDE IN THE IMAGE:" if text_elements else ""}
{chr(10).join(text_elements)}
{trust_badges_instr}
{f"TYPOGRAPHY: Use a {font_instr} font. HIGH CONTRAST against the background, readable at small (mobile) sizes. Clear size hierarchy for headline vs. subline." if text_elements else ""}
{"SPELLING — CRITICAL: All on-image text MUST be spelled correctly. German must be perfect: 'Versand' (not Vershand), 'Geschenk' (not Geschnek), 'personalisierbar', 'Halskette', 'Anhänger', 'kostenlos', 'einzigartig', 'handgefertigt'." if text_elements else ""}
{psych_instr}
{angle_instr}
{curiosity_instr}
{emotion_instr}

AD CREATIVE REQUIREMENTS:
- Works as a standalone ad — communicates product and value proposition visually
- Mobile-first: large clear visuals
- Jewelry clearly visible and desirable
- Creative-agency quality, no generic stock photo feel

JEWELRY BEST PRACTICES (from top-performing ads):
- Show jewelry ON THE BODY — never isolated on white
- Warm tones: gold, beige, creme, nude
- Texture as background: fabric, knit, skin
- Organic feel beats studio look — 'a friend sent me this' outperforms polished editorial
- Minimal copy on image — often brand name + one info
- Layering shots increase average order value

NEGATIVE: no blurry text, no illegible fonts, no cluttered composition, no cheap graphics, no watermarks, no AI artifacts, no deformed hands/fingers

QUALITY: 8K, professional advertising photography, editorial quality, perfect color grading, razor-sharp product detail."""

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
    story_slides = {
        "🎬 Produkt-Journey (Detail → Am Model → Lifestyle → CTA)": [
            "CAROUSEL SLIDE 1 — HOOK/DETAIL: Extreme close-up macro of the jewelry. Finest details — texture, engraving, facets. Stops the scroll with beauty.",
            "CAROUSEL SLIDE 2 — WORN: Medium close-up of the jewelry worn by a model. Natural, elegant, desirable. Focus on the neckline/hand area.",
            "CAROUSEL SLIDE 3 — LIFESTYLE: Wide lifestyle shot. Model wearing it in an aspirational setting — café, rooftop, terrace.",
            "CAROUSEL SLIDE 4 — CTA: Clean product shot on minimal background with clear CTA text overlay. Drives the click.",
            "CAROUSEL SLIDE 5 — BONUS/OFFER: Gift packaging or special offer visual. Final push to convert.",
        ],
        "💝 Emotionale Story (Geschenk-Moment Schritt für Schritt)": [
            "CAROUSEL SLIDE 1 — ANTICIPATION: Beautiful gift box with ribbon, hands about to open it. Build anticipation.",
            "CAROUSEL SLIDE 2 — REVEAL: The opening — jewelry revealed in its box. Sparkle, light catching the surface. The 'wow'.",
            "CAROUSEL SLIDE 3 — JOY: Emotional reaction — genuine happiness/surprise while holding/wearing the piece.",
            "CAROUSEL SLIDE 4 — WORN: Jewelry worn proudly. Candid admiring moment, mirror, or compliment.",
            "CAROUSEL SLIDE 5 — CTA: Product on clean background. Name, key feature ('personalisierbar'), strong CTA.",
        ],
        "🎨 Varianten-Showcase (Farben / Styles nebeneinander)": [
            "CAROUSEL SLIDE 1 — HERO: Bestseller variant, beautifully lit, clean background. The collection 'star'.",
            "CAROUSEL SLIDE 2 — VARIANT A: Second color/style. Same angle for consistency, different color (e.g. rosegold).",
            "CAROUSEL SLIDE 3 — VARIANT B: Third variant. Same visual style. Show diversity.",
            "CAROUSEL SLIDE 4 — GROUP: All variants together, elegantly arranged. Full range available.",
            "CAROUSEL SLIDE 5 — CTA: Model wearing one variant, text: 'find your color' / 'choose your style'.",
        ],
        "📖 Feature-Walkthrough (Material → Gravur → Verpackung → Preis)": [
            "CAROUSEL SLIDE 1 — MATERIAL: Close-up showing material quality. Text: material name ('925 Sterling Silver').",
            "CAROUSEL SLIDE 2 — CRAFT/DETAIL: Close-up of craftsmanship — engraving, stone setting, links. Text: 'Handgefertigt'.",
            "CAROUSEL SLIDE 3 — PACKAGING: Product in premium packaging — gift box, branded elements.",
            "CAROUSEL SLIDE 4 — WORN: Product worn in real life. Relatable, aspirational.",
            "CAROUSEL SLIDE 5 — PRICE/CTA: Product with price + offer (free shipping, code). Strong CTA.",
        ],
        "⭐ Social Proof Carousel (Kundenbild → Review → Produkt → CTA)": [
            "CAROUSEL SLIDE 1 — CUSTOMER: Authentic UGC-style customer photo wearing the jewelry casually.",
            "CAROUSEL SLIDE 2 — REVIEW: Clean card with a 5-star review quote. Product small in corner. Review is the hero.",
            "CAROUSEL SLIDE 3 — PRODUCT: Professional product shot — exactly what they receive.",
            "CAROUSEL SLIDE 4 — STATS: Social proof — '1000+ glückliche Kunden', '4.9/5 Sterne', 'Bestseller'. Infographic style.",
            "CAROUSEL SLIDE 5 — CTA: Product with offer and strong CTA. 'Jetzt selbst überzeugen'.",
        ],
        "🔍 Zoom-Reveal (Weit → Nah → Makro → Am Model)": [
            "CAROUSEL SLIDE 1 — WIDE: Full scene, jewelry barely visible. Curiosity: what is she wearing?",
            "CAROUSEL SLIDE 2 — MEDIUM: Portrait, jewelry now visible on neck/hand. Design becomes clear.",
            "CAROUSEL SLIDE 3 — CLOSE: Close-up of the jewelry area on the skin. Details clear.",
            "CAROUSEL SLIDE 4 — MACRO: Extreme macro — chain links, facets, engraving. Maximum detail.",
            "CAROUSEL SLIDE 5 — CTA: Full product shot with overlay text. Name, price, CTA.",
        ],
    }
    slides = story_slides.get(ad_carousel_story, story_slides["🎬 Produkt-Journey (Detail → Am Model → Lifestyle → CTA)"])
    slides = slides[:ad_carousel_count]
    if not ad_carousel_cta_last and len(slides) > 1:
        slides[-1] = slides[-1].replace("CTA:", "FINAL:").replace("call-to-action", "closing visual")

    carousel_prompts = []
    for i, slide_instr in enumerate(slides):
        slide_prompt = f"""{base_prompt}

--- CAROUSEL CONTEXT ---
This is SLIDE {i+1} of {ad_carousel_count} in a Facebook/Instagram Carousel Ad.
{slide_instr}

PRODUCT IDENTITY — ABSOLUTE RULE: The jewelry in ALL slides must be the EXACT SAME piece, reproduced 1:1 from the
reference image on EVERY slide. Do NOT alter shape, color, material, texture, chain, pendant, stones, metal color, or size.
Indistinguishable from the reference on every slide. Customers will compare the ad to what they receive.

CAROUSEL CONSISTENCY: All slides share the same color palette, lighting mood, and brand feel so they belong together.

TEXT ACCURACY: If this slide has text, reproduce it EXACTLY letter-by-letter. No typos, no missing/extra letters.

Format: 1:1 (Square) — standard for Facebook/Instagram Carousel."""
        carousel_prompts.append(slide_prompt)
    return carousel_prompts


def build_prompt_local():
    """Build prompt locally using Jinja2 template — no API needed."""
    if "16:9" in aspect_ratio: ar_text = "16:9 (Landscape)"
    elif "9:16" in aspect_ratio: ar_text = "9:16 (Vertical / Portrait)"
    elif "21:9" in aspect_ratio: ar_text = "21:9 (Cinematic Ultrawide)"
    else: ar_text = "1:1 (Square)"

    if "360° Orbit" in cam_move:
        move_instr = ("CAMERA: Smooth continuous 360-degree orbital movement circling the subject. "
                      "Keep model centered, revealing outfit and product from all angles.")
    elif "Slow Zoom" in cam_move:
        move_instr = "CAMERA: Slow, cinematic zoom-in towards the subject. Tension-building."
    elif "Handheld" in cam_move:
        move_instr = "CAMERA: Handheld, slightly shaky, documentary-feel movement."
    elif "Drone" in cam_move:
        move_instr = "CAMERA: Elevated drone orbit around subject, sweeping landscape reveal."
    else:
        move_instr = "CAMERA: Static tripod, locked-off frame. Clean and stable."

    size_instr = f"SCALE: The product is exactly {obj_size}cm. Show proportional to hand/body." if use_size and obj_size else ""

    ref_reminder = ""
    if wear_product:
        size_ref = ""
        if use_size and obj_size:
            size_ref = (f" The product is exactly {obj_size}cm in real life. Render it at this EXACT real-world size "
                        f"relative to the human body — a {obj_size}cm pendant is SMALL and delicate on a human neck.")
        prod_instr = (f"The model wears/holds '{product}'. Use the provided REFERENCE IMAGE for EXACT product appearance — "
                      f"reproduce 1:1 IDENTICALLY. Match every detail: exact shape, color, material, texture, chain style, "
                      f"pendant design, proportions. Do NOT alter, redesign, simplify, or 'improve' anything. "
                      f"Indistinguishable from the reference photo.{size_ref} Blend naturally into the scene.")
        ref_reminder = "⚠️ WICHTIG: Lade dein Referenzbild zusammen mit diesem Prompt hoch!"
    else:
        prod_instr = f"Campaign product: '{product}'. Integrate naturally into the composition."

    focus_map = {
        "Model Hero (Face Focus)": "FOCUS PRIORITY: Sharp focus on model's face and expression. Product secondary.",
        "Product Hero (Blurry Model)": f"FOCUS PRIORITY: Razor-sharp focus on '{product}'. Model slightly out of focus (bokeh).",
        "Detail Shot (Hands/Product Only)": f"FOCUS PRIORITY: Macro detail shot of '{product}'. Tight crop, face may be cut off.",
    }
    focus_instr = focus_map.get(shot_focus, "FOCUS PRIORITY: Balanced — model and product equally sharp and prominent.")

    outfit_instr = f"OUTFIT: {clothing}." if clothing else "OUTFIT: High-fashion minimal styling."

    skin_parts = [freckles]
    if use_vellus:
        skin_parts.append("visible vellus hair (peach fuzz) on cheeks and forehead")
    if use_imperfections:
        skin_parts.append("natural facial asymmetry, subtle micro-imperfections")
    skin_details = ", ".join(skin_parts)

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

    prompt = PROMPT_TEMPLATE.render(
        has_model_ref=has_model_ref,
        model_description=st.session_state.get("model_description", ""),
        aspect_ratio=ar_text, gender=gender, age=age, ethnicity=ethnicity, eye_color=eye_color,
        hair_color=hair_color, hair_texture=hair_texture, hair_style=hair_style, wind=wind,
        skin_details=skin_details, body_description=body_description,
        pose=pose, gaze=gaze, expression=expression,
        model_view=model_view_campaign if model_view_campaign and "Automatisch" not in model_view_campaign else "",
        candid_moment=candid_moment or "", makeup=makeup, outfit_instr=outfit_instr, prod_instr=prod_instr,
        focus_instr=focus_instr, size_instr=size_instr, lighting=lighting, lighting_details=lighting_details,
        framing=framing, lens=lens, aperture=aperture, film_look=film_look, move_instr=move_instr,
        final_bg=final_bg, weather=weather, ar_text=ar_text, ref_reminder=ref_reminder,
        quality_keywords=(
            "QUALITY: Editorial photograph quality, professional color grading, natural volumetric lighting, "
            "photorealistic skin texture, magazine cover quality. All products shown at their REAL physical size — "
            "do not enlarge jewelry or accessories."
            if "💎 Pro" in model_quality else
            "QUALITY KEYWORDS: 8K resolution, hyper-realistic, editorial quality, professional color grading, "
            "volumetric lighting, micro-detail rendering, photorealistic skin texture, magazine cover quality."
        ),
    )
    if negative_prompt and negative_prompt.strip():
        prompt += f"\n\nNEGATIVE PROMPT: {negative_prompt.strip()}"

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
    """Extend the image prompt with Veo video instructions (text prompt sent to Veo)."""
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
    fps = video_fps.split("fps")[0]
    has_wind = video_wind != "Kein Wind"
    wind_type = video_wind if has_wind else ""

    video_prompt = VIDEO_TEMPLATE.render(
        image_prompt=image_prompt, duration=video_duration, video_ratio=video_ratio,
        model_action=model_action, action_detail=action_detail if action_detail else "",
        movement_speed=movement_speed, camera_video_move=camera_video_move,
        has_wind=has_wind, wind_type=wind_type,
        has_head_movement=head_movement != "Keine (statisch)", head_movement=head_movement, head_speed=head_speed,
        has_eye_movement=eye_movement != "Keine (fixiert)", eye_movement=eye_movement,
        has_eyebrow=eyebrow_move != "Keine Bewegung", eyebrow_move=eyebrow_move,
        has_mouth=mouth_movement != "Keine Bewegung", mouth_movement=mouth_movement,
        micro_list=", ".join(micro_expressions) if micro_expressions else "",
        has_dialogue=has_dialogue if use_video else False,
        dialogue_text=dialogue_text if use_video and has_dialogue else "",
        voice_tone=voice_tone if use_video and has_dialogue else "",
        has_ambient_sound=has_ambient if use_video else False,
        ambient_sound=ambient_sound if use_video and has_ambient else "",
        fps=fps,
    )
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
    if "1:1" in prod_ar: par = "1:1 (Square)"
    elif "4:5" in prod_ar: par = "4:5 (Portrait)"
    elif "9:16" in prod_ar: par = "9:16 (Vertical)"
    elif "16:9" in prod_ar: par = "16:9 (Landscape)"
    elif "3:2" in prod_ar: par = "3:2 (Classic)"
    else: par = "1:1 (Square)"

    placement_detail = ""
    if "Floating" in prod_placement:
        placement_detail = "The product floats weightlessly in center frame, perfectly lit from all sides, with a subtle shadow beneath to ground it."
    elif "Draped" in prod_placement:
        placement_detail = f"Product draped naturally over curved {prod_surface} fabric, following the soft folds organically."
    elif "mirror" in prod_placement.lower():
        placement_detail = "Product sits on a reflective mirror surface, creating a perfect reflection beneath."
    elif fabric_drape:
        placement_detail = f"The {prod_surface} surface is shaped: {fabric_drape}. Product follows the natural contour of the fabric."

    prod_bg_detail = ""
    if prod_surface != "— Keiner (schwebend) —":
        prod_bg_detail = f"SURFACE: {prod_surface}."

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
        prod_aspect_ratio=par, prod_name=prod_name,
        prod_description=prod_description if prod_description else "",
        prod_material=prod_material, prod_size_info=prod_size_text if prod_size_text else "",
        has_reference=use_prod_ref, ref_count=prod_ref_count if use_prod_ref else 0,
        ref_angles=", ".join(prod_ref_angles) if use_prod_ref and prod_ref_angles else "",
        prod_placement=prod_placement, placement_detail=placement_detail,
        prod_arrangement=prod_arrangement, prod_angle=prod_angle, prod_lens=prod_lens, prod_dof=prod_dof,
        prod_lighting=prod_lighting, prod_lighting_detail=prod_lighting_detail,
        prod_reflections=prod_reflections, prod_bg=prod_bg_final, prod_bg_detail=prod_bg_detail,
        prod_props=prod_props if prod_props else "", prod_color_mood=prod_color_mood,
        prod_shadow=prod_shadow, prod_negative=prod_negative if prod_negative else "",
    )
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


def build_model_ref_instruction(n_model_imgs, model_desc, n_product_imgs=0):
    """Shared model-reference instruction block (used by campaign, ad & carousel generation)."""
    instr = (
        "\n\nMODEL REFERENCE — ABSOLUTE RULE: "
        f"The first {n_model_imgs} reference image(s) show an AI-GENERATED fictional character "
        "(created by the user with AI tools — not a real person). "
        "Reproduce this EXACT character 1:1 IDENTICALLY. Use the REFERENCE IMAGES as the PRIMARY source — "
        "the character must be visually INDISTINGUISHABLE. Match every detail: face shape, nose, eyes, lips, "
        "jawline, eyebrows, facial proportions, skin tone, skin texture, hair color, hair length, hair texture, "
        "body type, body proportions, build, height impression. "
        "Do NOT alter ANY physical attribute. ONLY outfit, pose, and setting come from the prompt."
    )
    if model_desc:
        instr += (
            "\n\nDETAILED CHARACTER DESCRIPTION (verify your reproduction matches the reference images):\n"
            f"{model_desc}\n\n"
            "Cross-check the output against BOTH the reference images AND this description; fix any contradiction."
        )
    if n_product_imgs:
        instr += (
            f"\n\nThe LAST {n_product_imgs} reference image(s) show the PRODUCT/JEWELRY to use. "
            "Reproduce the product 1:1 IDENTICALLY as specified in the product instructions above."
        )
    return instr


# ============================================================
#  GEMINI HELPERS (100% Gemini — kein OpenAI mehr)
# ============================================================

def find_gemini_text_model(gemini_api_key):
    """Find a Gemini text model that supports generateContent (cached in session)."""
    if st.session_state.get("gemini_text_model"):
        return st.session_state.gemini_text_model
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        available = []
        for m in data.get("models", []):
            name = m.get("name", "").replace("models/", "")
            if "generateContent" in m.get("supportedGenerationMethods", []):
                available.append(name)
        flash = [m for m in available if "flash" in m.lower() and "image" not in m.lower() and "lite" not in m.lower()]
        pro = [m for m in available if "pro" in m.lower() and "image" not in m.lower()]
        others = [m for m in available if "image" not in m.lower()]
        candidates = flash + pro + others
        if candidates:
            st.session_state.gemini_text_model = candidates[0]
            return candidates[0]
    except Exception as e:
        st.error(f"Konnte Text-Modell nicht ermitteln: {e}")
    return None


def polish_with_gemini(raw_prompt, gemini_api_key):
    """Refine a structured prompt into flowing, cinematic prose — using Gemini (replaces the old GPT-4o polish)."""
    model = find_gemini_text_model(gemini_api_key)
    if not model:
        st.error("Kein Gemini-Textmodell für den Polish-Modus gefunden.")
        return None
    system = (
        "You are an expert prompt engineer for AI image/video generation (Gemini / Nano Banana / Veo). "
        "Rewrite the given structured prompt as a single, flowing, vivid, cinematic paragraph. "
        "Keep ALL technical details and specifications — do not add or remove specs, only improve prose and flow. "
        "Return ONLY the rewritten prompt, with no preamble or markdown."
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
    payload = {
        "contents": [{"parts": [{"text": f"{system}\n\nPROMPT TO REWRITE:\n{raw_prompt}"}]}],
        "generationConfig": {"responseMimeType": "text/plain", "temperature": 0.6},
        "safetySettings": GEMINI_SAFETY_SETTINGS,
    }
    try:
        resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=90)
        resp.raise_for_status()
        data = resp.json()
        out = ""
        for cand in data.get("candidates", []):
            for part in cand.get("content", {}).get("parts", []):
                if "text" in part:
                    out += part["text"]
        return out.strip() or None
    except Exception as e:
        st.error(f"Gemini Polish Fehler: {e}")
        return None


def find_gemini_image_model(gemini_api_key, prefer_pro=False):
    """Find a Gemini model that supports image generation."""
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={gemini_api_key}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        if prefer_pro:
            preferred_models = [
                "gemini-3-pro-image", "gemini-3-pro-image-preview", "nano-banana-pro",
                "gemini-3.1-flash-image-preview", "gemini-3-flash-image",
                "gemini-2.5-flash-image", "gemini-2.5-flash-preview-image",
            ]
        else:
            preferred_models = [
                "gemini-3.1-flash-image-preview", "gemini-3-flash-image",
                "gemini-2.5-flash-image", "gemini-2.5-flash-preview-image",
                "gemini-3-pro-image-preview", "gemini-2.0-flash-image", "gemini-2.0-flash",
            ]
        available = []
        for model in data.get("models", []):
            name = model.get("name", "").replace("models/", "")
            if "generateContent" in model.get("supportedGenerationMethods", []):
                available.append(name)
        for pref in preferred_models:
            for avail in available:
                if pref in avail:
                    return avail
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
    """Generate an image using Gemini (auto-detects best model). Supports reference images + quality settings."""
    quality_key = "pro" if prefer_pro else "flash"
    if st.session_state.get("gemini_quality_mode") != quality_key:
        st.session_state.gemini_model_name = None
        st.session_state.gemini_quality_mode = quality_key

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

    if prefer_pro:
        quality_boost = (
            "\n\nQUALITY INSTRUCTIONS (Pro): Maximum resolution. Photographic realism — natural skin texture with "
            "visible pores, realistic lighting, accurate fabric draping, professional color grading. High-end editorial look."
            "\n\nPRODUCT SCALE RULE: All jewelry/pendants/rings/accessories MUST appear at TRUE real-world size relative "
            "to the human body — small and delicate, NOT enlarged. Realism of scale is MORE important than product visibility."
            "\n\nPRODUCT FIDELITY: If a reference image is provided, the product must be a 1:1 EXACT copy. Zero deviations."
            "\n\nTEXT SPELLING: Any on-image text must be 100% correctly spelled. German: 'Versand', 'Geschenk', 'kostenlos'."
        )
    else:
        quality_boost = (
            "\n\nQUALITY INSTRUCTIONS: Maximum resolution, tack-sharp, extreme detail when zoomed in. No blur, no softness, "
            "no compression artifacts. Every texture, pore, fabric thread crisply rendered. Pixel-perfect sharpness."
            "\n\nPRODUCT FIDELITY: If a reference image is provided, the product must be a 1:1 EXACT copy. Zero deviations."
            "\n\nTEXT SPELLING: Any on-image text must be 100% correctly spelled. German: 'Versand', 'Geschenk', 'kostenlos'."
        )
    enhanced_prompt = prompt_text + quality_boost

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
            parts.append({"inlineData": {"mimeType": mime, "data": img_b64}})

    gen_config = {"responseModalities": ["IMAGE"]}
    ar_map = {"16:9": "16:9", "9:16": "9:16", "1:1": "1:1", "21:9": "16:9", "4:5": "3:4", "3:2": "4:3"}
    image_config = {}
    if aspect_ratio_str:
        for key, val in ar_map.items():
            if key in aspect_ratio_str:
                image_config["aspectRatio"] = val
                break
    if prefer_pro and "pro" in model.lower():
        image_config["imageSize"] = "2K"
    if image_config:
        gen_config["imageConfig"] = image_config

    payload = {"contents": [{"parts": parts}], "generationConfig": gen_config, "safetySettings": GEMINI_SAFETY_SETTINGS}
    headers = {"Content-Type": "application/json"}
    request_timeout = 300 if prefer_pro else 180

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=request_timeout)
        response.raise_for_status()
        data = response.json()
        for candidate in data.get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    img_bytes = base64.b64decode(part["inlineData"]["data"])
                    return img_bytes, part["inlineData"].get("mimeType", "image/png")
        block_reason = ""
        for candidate in data.get("candidates", []):
            if "finishReason" in candidate:
                block_reason = candidate["finishReason"]
        if block_reason:
            st.error(f"Gemini hat kein Bild generiert. Grund: {block_reason}. Versuche den Prompt anzupassen.")
        else:
            st.error("Gemini hat kein Bild zurückgegeben. Versuche den Prompt anzupassen.")
        return None, None
    except requests.exceptions.Timeout:
        if prefer_pro and "imageSize" in gen_config.get("imageConfig", {}):
            st.warning("⏰ Pro-Timeout bei hoher Auflösung — versuche Standard-Auflösung...")
            del gen_config["imageConfig"]["imageSize"]
            try:
                retry = requests.post(url, json={"contents": [{"parts": parts}], "generationConfig": gen_config,
                                                 "safetySettings": GEMINI_SAFETY_SETTINGS}, headers=headers, timeout=180)
                retry.raise_for_status()
                for candidate in retry.json().get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            st.success("✅ Pro-Bild generiert (Standard-Auflösung)")
                            return base64.b64decode(part["inlineData"]["data"]), part["inlineData"].get("mimeType", "image/png")
            except Exception:
                pass
        st.error("⏰ Timeout — Gemini braucht zu lange. Bitte nochmal versuchen.")
        return None, None
    except requests.exceptions.HTTPError as e:
        error_detail = ""
        try:
            error_detail = e.response.json().get("error", {}).get("message", "")
        except Exception:
            pass
        if e.response.status_code == 400 and prefer_pro and "imageConfig" in gen_config:
            st.warning("⚠️ Pro-Modell unterstützt diese Konfiguration nicht — versuche ohne Größen-Einstellung...")
            gen_config["imageConfig"] = {k: v for k, v in gen_config["imageConfig"].items() if k != "imageSize"}
            try:
                retry = requests.post(url, json={"contents": [{"parts": parts}], "generationConfig": gen_config,
                                                 "safetySettings": GEMINI_SAFETY_SETTINGS}, headers=headers, timeout=240)
                retry.raise_for_status()
                for candidate in retry.json().get("candidates", []):
                    for part in candidate.get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            st.success("✅ Pro-Bild generiert (ohne Größen-Override)")
                            return base64.b64decode(part["inlineData"]["data"]), part["inlineData"].get("mimeType", "image/png")
            except Exception as retry_e:
                st.error(f"Auch Retry fehlgeschlagen: {retry_e}")
                return None, None
        if e.response.status_code == 404:
            st.session_state.gemini_model_name = None
            st.error(f"Modell '{model}' nicht verfügbar. Bitte nochmal klicken — suche alternatives Modell.")
        elif e.response.status_code in (503, 429):
            fallback_models = ["gemini-3.1-flash-image-preview", "gemini-2.5-flash-image", "gemini-2.0-flash"]
            fallback_models = [m for m in fallback_models if m not in model]
            for fb in fallback_models:
                st.warning(f"⚡ {model} überlastet — versuche Fallback: **{fb}**...")
                fb_url = f"https://generativelanguage.googleapis.com/v1beta/models/{fb}:generateContent?key={gemini_api_key}"
                try:
                    fb_response = requests.post(fb_url, json=payload, headers=headers, timeout=180)
                    fb_response.raise_for_status()
                    for candidate in fb_response.json().get("candidates", []):
                        for part in candidate.get("content", {}).get("parts", []):
                            if "inlineData" in part:
                                st.session_state.gemini_model_name = fb
                                st.success(f"✅ Fallback erfolgreich mit **{fb}**")
                                return base64.b64decode(part["inlineData"]["data"]), part["inlineData"].get("mimeType", "image/png")
                except Exception:
                    continue
            st.error("Alle Modelle überlastet. Bitte in 1-2 Minuten nochmal versuchen.")
        else:
            st.error(f"Gemini API Fehler: {e}\n{error_detail}")
        return None, None
    except Exception as e:
        st.error(f"Fehler bei der Bildgenerierung: {e}")
        return None, None


def generate_image_hybrid(prompt_text, gemini_api_key, reference_images=None, aspect_ratio_str=None):
    """Hybrid: Flash generates a product-faithful image WITHOUT text, Pro adds text + refinement."""
    text_lines_for_pro = []
    flash_prompt_lines = []
    for line in prompt_text.split("\n"):
        line_upper = line.strip().upper()
        is_text_line = any(k in line_upper for k in [
            "HEADLINE TEXT ON IMAGE:", "SUBLINE TEXT:", "CTA BUTTON/TEXT:", "OFFER BADGE:",
            "TEXT ELEMENTS TO INCLUDE", "CRITICAL TEXT RENDERING RULE", "TYPOGRAPHY:",
            "SPELLING — CRITICAL:", "SPELLING —", "TEXT PLACEMENT:", "(SPELLED:"])
        if is_text_line:
            text_lines_for_pro.append(line)
        else:
            flash_prompt_lines.append(line)

    flash_prompt = "\n".join(flash_prompt_lines)
    flash_prompt += (
        "\n\n⛔ DO NOT RENDER ANY TEXT ON THIS IMAGE. ⛔\n"
        "No text, headlines, sublines, CTAs, badges, labels, watermarks, or written words. "
        "Purely visual — scene, model, product, lighting, composition. Text is added in a separate step.")

    st.info("🔀 **Hybrid 1/2:** Flash generiert produkt-treues Bild (ohne Text)...")
    flash_bytes, flash_mime = generate_image_gemini(
        flash_prompt, gemini_api_key, reference_images=reference_images,
        aspect_ratio_str=aspect_ratio_str, prefer_pro=False)
    if not flash_bytes:
        st.error("Hybrid abgebrochen — Flash konnte kein Bild generieren.")
        return None, None
    st.success("✅ Schritt 1 fertig — Flash-Bild (ohne Text).")
    st.image(flash_bytes, caption="Flash-Basis ohne Text (Pro fügt Text + Feinschliff hinzu...)", width=300)

    st.info("🔀 **Hybrid 2/2:** Pro fügt Text hinzu + verfeinert Haut, Licht & Details...")
    old_model = st.session_state.get("gemini_model_name")
    old_quality = st.session_state.get("gemini_quality_mode")
    st.session_state.gemini_model_name = None
    st.session_state.gemini_quality_mode = "pro"

    pro_model = find_gemini_image_model(gemini_api_key, prefer_pro=True)
    if not pro_model or "pro" not in pro_model.lower():
        st.warning("⚠️ Pro-Modell nicht verfügbar — verwende Flash-Bild als Ergebnis.")
        st.session_state.gemini_model_name = old_model
        st.session_state.gemini_quality_mode = old_quality
        return flash_bytes, flash_mime

    text_block = "\n".join(text_lines_for_pro) if text_lines_for_pro else ""
    refine_prompt = "EDIT THIS IMAGE — perform TWO tasks:\n\n═══ TASK 1: ADD TEXT OVERLAYS ═══\n"
    if text_block:
        refine_prompt += (
            f"{text_block}\n\nRender ALL text elements above DIRECTLY onto the image. Text must be HIGH CONTRAST, "
            "professional typography, properly positioned, spelled EXACTLY, with clear size hierarchy.\n\n")
    else:
        refine_prompt += "No text elements to add.\n\n"
    refine_prompt += (
        "═══ TASK 2: VISUAL REFINEMENT ═══\nImprove ONLY: skin texture/pores, lighting/highlights/shadows, color "
        "grading, background depth. Make it a high-end editorial photograph.\n\n"
        "═══ ABSOLUTE RULES ═══\n- Do NOT alter the PRODUCT/JEWELRY (shape, design, color, material, size)\n"
        "- Do NOT move/resize the product\n- Do NOT change the model's face, pose, or expression\n"
        "- Do NOT change composition/framing\n- ONLY add text overlays + improve skin/lighting/colors/background.\n")

    flash_b64 = base64.b64encode(flash_bytes).decode("utf-8")
    parts = [{"text": refine_prompt}, {"inlineData": {"mimeType": flash_mime or "image/png", "data": flash_b64}}]
    gen_config = {"responseModalities": ["TEXT", "IMAGE"]}
    ar_map = {"1:1": "1:1", "16:9": "16:9", "9:16": "9:16", "4:5": "3:4", "4:3": "4:3"}
    image_config = {}
    if aspect_ratio_str:
        for key, val in ar_map.items():
            if key in aspect_ratio_str:
                image_config["aspectRatio"] = val
                break
    if image_config:
        gen_config["imageConfig"] = image_config

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{pro_model}:generateContent?key={gemini_api_key}"
    payload = {"contents": [{"parts": parts}], "generationConfig": gen_config, "safetySettings": GEMINI_SAFETY_SETTINGS}
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=300)
        response.raise_for_status()
        for candidate in response.json().get("candidates", []):
            for part in candidate.get("content", {}).get("parts", []):
                if "inlineData" in part:
                    pro_bytes = base64.b64decode(part["inlineData"]["data"])
                    st.success(f"✅ Hybrid fertig! Flash (Bild) → Pro (Text + Feinschliff) via **{pro_model}**")
                    st.session_state.gemini_model_name = old_model
                    st.session_state.gemini_quality_mode = old_quality
                    return pro_bytes, part["inlineData"].get("mimeType", "image/png")
        st.warning("⚠️ Pro hat kein verfeinertes Bild zurückgegeben — verwende Flash-Bild.")
    except Exception as e:
        st.warning(f"⚠️ Pro-Verfeinerung fehlgeschlagen ({e}) — verwende Flash-Bild.")
    st.session_state.gemini_model_name = old_model
    st.session_state.gemini_quality_mode = old_quality
    return flash_bytes, flash_mime


def smart_generate_image(prompt_text, gemini_api_key, reference_images=None, aspect_ratio_str=None):
    """Route to the correct generation mode based on model_quality."""
    if "🔀 Hybrid" in model_quality:
        return generate_image_hybrid(prompt_text, gemini_api_key,
                                     reference_images=reference_images, aspect_ratio_str=aspect_ratio_str)
    return generate_image_gemini(prompt_text, gemini_api_key, reference_images=reference_images,
                                 aspect_ratio_str=aspect_ratio_str, prefer_pro=("💎 Pro" in model_quality))


def generate_video_veo(prompt_text, gemini_api_key, first_frame_bytes=None,
                       first_frame_mime="image/png", aspect_ratio="16:9", duration=8):
    """Generate a video with Veo 3 via the Gemini API. Returns video bytes or None.

    Wichtige Fixes ggü. der alten Version:
      - korrekte aktuelle Modellnamen (veo-3.1-generate-preview, veo-3.0-generate-001, ...)
      - personGeneration = 'allow_adult' (in der EU vorgeschrieben + Pflicht bei Image-to-Video → das war
        der Hauptgrund warum vorher nichts kam)
      - Download des Videos MIT 'x-goog-api-key'-Header (vorher fehlte die Auth → 403)
      - optionaler Startframe (Image-to-Video) für 100% Model-Konsistenz
    """
    import time as _time
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    headers = {"Content-Type": "application/json", "x-goog-api-key": gemini_api_key}

    veo_models = [
        "veo-3.1-generate-preview",
        "veo-3.1-fast-generate-preview",
        "veo-3.0-generate-001",
        "veo-2.0-generate-001",
    ]

    instance = {"prompt": prompt_text}
    if first_frame_bytes is not None:
        instance["image"] = {"inlineData": {"mimeType": first_frame_mime or "image/png",
                                            "data": base64.b64encode(first_frame_bytes).decode("utf-8")}}

    # allow_adult: EU-konform und Pflicht für Image-to-Video. Generiert keine Kinder.
    parameters = {
        "aspectRatio": "9:16" if "9:16" in str(aspect_ratio) else "16:9",
        "durationSeconds": str(duration),
        "personGeneration": "allow_adult",
    }
    payload = {"instances": [instance], "parameters": parameters}

    operation_name = None
    used_model = None
    for model in veo_models:
        url = f"{BASE_URL}/models/{model}:predictLongRunning"
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=60)
            if resp.status_code in (404, 503):
                continue
            resp.raise_for_status()
            operation_name = resp.json().get("name")
            used_model = model
            break
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code in (404, 503):
                continue
            detail = ""
            try:
                detail = e.response.json().get("error", {}).get("message", "")
            except Exception:
                pass
            st.caption(f"⚠️ {model}: {detail[:160]}")
            continue
        except Exception:
            continue

    if not operation_name:
        st.error("❌ Kein Veo-Modell verfügbar oder Anfrage abgelehnt. Prüfe API Key, Billing und ob Veo für deinen Account/deine Region freigeschaltet ist.")
        return None
    st.info(f"🎬 Verwende: **{used_model}** — Operation läuft...")

    poll_url = f"{BASE_URL}/{operation_name}"
    poll_headers = {"x-goog-api-key": gemini_api_key}
    progress = st.progress(0, text="⏳ Video wird generiert...")
    status = st.empty()
    max_wait = 420
    elapsed = 0
    interval = 10

    while elapsed < max_wait:
        _time.sleep(interval)
        elapsed += interval
        progress.progress(min(elapsed / max_wait, 0.95), text=f"⏳ Video wird generiert... ({elapsed}s / max {max_wait}s)")
        try:
            pr = requests.get(poll_url, headers=poll_headers, timeout=30)
            pr.raise_for_status()
            pd = pr.json()
        except Exception as e:
            status.caption(f"Poll-Hinweis ({elapsed}s): {e}")
            continue

        if pd.get("done"):
            progress.progress(1.0, text="✅ Video fertig!")
            if "error" in pd:
                st.error(f"Veo Fehler: {pd['error'].get('message', pd['error'])}")
                return None
            resp_obj = pd.get("response", {})
            samples = (resp_obj.get("generateVideoResponse", {}).get("generatedSamples")
                       or resp_obj.get("generatedSamples")
                       or resp_obj.get("videos")
                       or [])
            if samples:
                vobj = samples[0].get("video", samples[0])
                if "bytesBase64Encoded" in vobj:
                    return base64.b64decode(vobj["bytesBase64Encoded"])
                uri = vobj.get("uri") or vobj.get("gcsUri")
                if uri:
                    status.caption("Lade Video herunter...")
                    dl = requests.get(uri, headers=poll_headers, timeout=180)  # requests folgt Redirects automatisch
                    dl.raise_for_status()
                    return dl.content
            st.warning("Video fertig, aber Download-Quelle nicht gefunden. Response-Struktur:")
            st.json(pd)
            return None

    progress.progress(1.0, text="⏰ Timeout")
    st.error("⏰ Timeout bei der Video-Generierung (>7 Min). Bei hoher Auslastung kann das passieren — bitte nochmal versuchen.")
    return None


# ============================================================
#  OUTPUT
# ============================================================
st.markdown("---")

for k in ["last_image_prompt", "last_video_prompt", "last_product_prompt"]:
    if k not in st.session_state:
        st.session_state[k] = None
if "generated_images" not in st.session_state:
    st.session_state.generated_images = []
if "generated_videos" not in st.session_state:
    st.session_state.generated_videos = []

st.markdown('<div class="section-card"><h3>🚀 Generieren</h3></div>', unsafe_allow_html=True)

if use_video:
    gen_mode = st.radio("Was möchtest du generieren?",
                        ["📷 Nur Foto", "🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"],
                        index=2, horizontal=True)
else:
    gen_mode = "📷 Nur Foto"

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
        with st.spinner("Baue Prompt..."):
            raw_prompt, reminder = build_prompt_local()

        if gen_mode in ["📷 Nur Foto", "📷+🎬 Foto + Video"]:
            st.session_state.last_image_prompt = raw_prompt
            st.success("✅ Bild-Prompt generiert!")
            if reminder:
                st.info(reminder)
            st.markdown("### 📋 Bild-Prompt")
            st.code(raw_prompt, language="text")

        final_video_prompt = None
        if gen_mode in ["🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"] and use_video:
            with st.spinner("Baue Video-Prompt..."):
                final_video_prompt = build_video_prompt(raw_prompt)
            st.session_state.last_video_prompt = final_video_prompt
            # Veo-Settings für den Generieren-Button merken
            st.session_state.video_aspect = "9:16" if "9:16" in video_ratio else "16:9"
            st.session_state.video_duration = video_duration
            st.session_state.video_use_first_frame = use_video_first_frame
            st.success("✅ Veo 3 Video-Prompt generiert!")
            st.markdown("### 🎬 Veo 3 Video-Prompt")
            st.code(final_video_prompt, language="text")

        if gen_mode == "🎬 Nur Video-Prompt":
            st.session_state.last_image_prompt = None

        if use_polish:
            if not gemini_key:
                st.warning("⚠️ Gemini Key fehlt für den Polish-Modus!")
            else:
                polish_target = final_video_prompt if final_video_prompt else raw_prompt
                with st.spinner("Gemini verfeinert..."):
                    polished = polish_with_gemini(polish_target, gemini_key)
                if polished:
                    st.markdown("### ✨ Gemini Polished Version")
                    st.code(polished, language="text")

        if gen_mode == "📷 Nur Foto":
            save_prompt, save_type = raw_prompt, "📷 Bild"
        elif gen_mode == "🎬 Nur Video-Prompt":
            save_prompt, save_type = (final_video_prompt or raw_prompt), "🎬 Video"
        else:
            save_prompt, save_type = (final_video_prompt or raw_prompt), "📷+🎬 Beides"
        st.session_state.prompt_history.append({
            "time": datetime.now().strftime("%H:%M:%S"), "prompt": save_prompt, "type": save_type})

        ex1, ex2 = st.columns(2)
        if gen_mode in ["📷 Nur Foto", "📷+🎬 Foto + Video"]:
            with ex1:
                st.download_button("💾 Bild-Prompt speichern (.txt)", data=raw_prompt,
                    file_name=f"nano_banana_image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")
        if final_video_prompt and gen_mode in ["🎬 Nur Video-Prompt", "📷+🎬 Foto + Video"]:
            with ex2:
                st.download_button("🎬 Video-Prompt speichern (.txt)", data=final_video_prompt,
                    file_name=f"nano_banana_veo3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")


# --- GENERATE IMAGE WITH GEMINI ---
if st.session_state.last_image_prompt:
    st.markdown("---")
    st.markdown("### 🎨 Bild mit Gemini generieren")
    gen1, gen2 = st.columns([2, 1])
    with gen2:
        num_images = st.selectbox("Anzahl Bilder", [1, 2, 3, 4], index=0, key="num_img_campaign")
    with gen1:
        if not gemini_key:
            st.warning("⚠️ Gemini API Key fehlt! Füge ihn in der Sidebar oder in den Streamlit Secrets hinzu.")
        if st.button("🚀 JETZT ERSTELLEN MIT GEMINI", disabled=not gemini_key):
            all_ref_imgs = []
            if model_ref_files:
                all_ref_imgs.extend(model_ref_files)
                if st.session_state.get("model_description"):
                    st.info(f"👤 {len(model_ref_files)} Model-Bild(er) + Beschreibung werden mitgesendet.")
                else:
                    st.info(f"👤 {len(model_ref_files)} Model-Bild(er) werden mitgesendet (Tipp: '🔍 Model analysieren' für bessere Ergebnisse).")
            if wear_product and campaign_ref_files:
                st.info(f"📸 {len(campaign_ref_files)} Produkt-Referenzbild(er) werden mitgesendet...")
                all_ref_imgs.extend(campaign_ref_files)
            ref_imgs = all_ref_imgs if all_ref_imgs else None

            active_prompt = st.session_state.last_image_prompt
            if model_ref_files:
                active_prompt += build_model_ref_instruction(
                    len(model_ref_files), st.session_state.get("model_description", ""),
                    len(campaign_ref_files) if (wear_product and campaign_ref_files) else 0)

            for i in range(num_images):
                pro_hint = " ⚠️ Pro: 2-4 Min!" if "💎 Pro" in model_quality else (" 🔀 Hybrid: 2 Schritte" if "🔀 Hybrid" in model_quality else "")
                with st.spinner(f"Gemini generiert Bild {i+1}/{num_images}...{pro_hint}"):
                    img_bytes, mime_type = smart_generate_image(
                        active_prompt, gemini_key, reference_images=ref_imgs, aspect_ratio_str=aspect_ratio)
                if img_bytes:
                    st.session_state.generated_images.append({
                        "bytes": img_bytes, "mime": mime_type, "type": "campaign",
                        "time": datetime.now().strftime("%H:%M:%S")})

    campaign_imgs = [img for img in st.session_state.generated_images if img["type"] == "campaign"]
    if campaign_imgs:
        st.markdown("### 🖼️ Generierte Bilder")
        cols = st.columns(min(len(campaign_imgs), 4))
        for idx, img in enumerate(campaign_imgs):
            with cols[idx % 4]:
                st.image(img["bytes"], caption=f"Campaign #{idx+1} — {img['time']}", use_container_width=True)
                ext = "png" if "png" in img["mime"] else "jpg"
                st.download_button(f"💾 Bild #{idx+1} speichern", data=img["bytes"],
                    file_name=f"nano_banana_campaign_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                    mime=img["mime"], key=f"dl_campaign_{idx}_{img['time']}")
        if st.button("🗑️ Generierte Campaign-Bilder löschen"):
            st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "campaign"]
            st.rerun()


# --- GENERATE VIDEO WITH VEO ---
if st.session_state.last_video_prompt:
    st.markdown("---")
    st.markdown("### 🎬 Video mit Veo 3 generieren")
    if not gemini_key:
        st.warning("⚠️ Gemini API Key fehlt! Veo nutzt den gleichen API Key.")

    use_ff = st.session_state.get("video_use_first_frame", True)
    campaign_imgs_for_ff = [img for img in st.session_state.generated_images if img["type"] == "campaign"]
    if use_ff and campaign_imgs_for_ff:
        st.caption("🎞️ Image-to-Video aktiv: dein zuletzt generiertes Campaign-Bild wird als Startframe verwendet (max. Konsistenz).")
    elif use_ff and not campaign_imgs_for_ff:
        st.caption("ℹ️ Startframe gewünscht, aber noch kein Campaign-Bild generiert → es wird Text-to-Video genutzt.")

    if st.button("🎬 VIDEO JETZT ERSTELLEN MIT VEO", disabled=not gemini_key):
        ff_bytes, ff_mime = None, "image/png"
        if use_ff and campaign_imgs_for_ff:
            ff_bytes = campaign_imgs_for_ff[-1]["bytes"]
            ff_mime = campaign_imgs_for_ff[-1].get("mime", "image/png")
        with st.spinner("Veo generiert Video... (kann 1-7 Min. dauern)"):
            video_bytes = generate_video_veo(
                st.session_state.last_video_prompt, gemini_key,
                first_frame_bytes=ff_bytes, first_frame_mime=ff_mime,
                aspect_ratio=st.session_state.get("video_aspect", "16:9"),
                duration=st.session_state.get("video_duration", 8))
        if video_bytes:
            st.session_state.generated_videos.append({
                "bytes": video_bytes, "type": "campaign", "time": datetime.now().strftime("%H:%M:%S")})

    campaign_vids = [v for v in st.session_state.generated_videos if v["type"] == "campaign"]
    if campaign_vids:
        st.markdown("### 🎥 Generierte Videos")
        for idx, vid in enumerate(campaign_vids):
            st.video(vid["bytes"], format="video/mp4")
            st.download_button(f"💾 Video #{idx+1} speichern (.mp4)", data=vid["bytes"],
                file_name=f"nano_banana_video_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                mime="video/mp4", key=f"dl_video_{idx}_{vid['time']}")
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
            if use_polish and gemini_key:
                with st.spinner("Gemini verfeinert Product Prompt..."):
                    polished_prod = polish_with_gemini(product_prompt, gemini_key)
                if polished_prod:
                    st.markdown("### ✨ Gemini Polished Product Version")
                    st.code(polished_prod, language="text")
            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"), "prompt": product_prompt, "type": "💎 Product"})
            st.download_button("💾 Product-Prompt speichern (.txt)", data=product_prompt,
                file_name=f"nano_banana_product_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")

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
                prod_refs = prod_ref_files if use_prod_ref and prod_ref_files else None
                if prod_refs:
                    st.info(f"📸 {len(prod_refs)} Referenzbild(er) werden mitgesendet...")
                for i in range(num_prod_images):
                    with st.spinner(f"Gemini generiert Product-Bild {i+1}/{num_prod_images}..."):
                        img_bytes, mime_type = smart_generate_image(
                            st.session_state.last_product_prompt, gemini_key,
                            reference_images=prod_refs, aspect_ratio_str=prod_ar)
                    if img_bytes:
                        st.session_state.generated_images.append({
                            "bytes": img_bytes, "mime": mime_type, "type": "product",
                            "time": datetime.now().strftime("%H:%M:%S")})

        product_imgs = [img for img in st.session_state.generated_images if img["type"] == "product"]
        if product_imgs:
            st.markdown("### 🖼️ Generierte Product-Bilder")
            cols = st.columns(min(len(product_imgs), 4))
            for idx, img in enumerate(product_imgs):
                with cols[idx % 4]:
                    st.image(img["bytes"], caption=f"Product #{idx+1} — {img['time']}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(f"💾 Product #{idx+1} speichern", data=img["bytes"],
                        file_name=f"nano_banana_product_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"], key=f"dl_product_{idx}_{img['time']}")
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

    btn_text = f"🎠 CAROUSEL AD ({ad_carousel_count} SLIDES) GENERIEREN" if ad_carousel else "🎯 AD CREATIVE PROMPT GENERIEREN"

    if st.button(btn_text):
        if not product:
            st.warning("Bitte ein Produkt / Thema eingeben (im Tab 'Format & Produkt')!")
        elif ad_carousel:
            with st.spinner(f"Baue {ad_carousel_count} Carousel-Slide Prompts..."):
                carousel_prompts = build_carousel_prompts()
            st.session_state.last_carousel_prompts = carousel_prompts
            st.session_state.last_ad_prompt = None
            st.success(f"✅ {len(carousel_prompts)} Carousel-Slide Prompts generiert!")
            for idx, cp in enumerate(carousel_prompts):
                with st.expander(f"📄 Slide {idx+1} Prompt", expanded=(idx == 0)):
                    st.code(cp, language="text")
            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"),
                "prompt": f"[CAROUSEL {len(carousel_prompts)} Slides]\n\n" + carousel_prompts[0][:200] + "...",
                "type": "🎠 Carousel"})
        else:
            with st.spinner("Baue Ad Creative Prompt..."):
                ad_prompt = build_ad_creative_prompt()
            st.session_state.last_ad_prompt = ad_prompt
            st.session_state.last_carousel_prompts = None
            st.success("✅ Ad Creative Prompt generiert!")
            st.markdown("### 🎯 Ad Creative Prompt")
            st.code(ad_prompt, language="text")

            if use_322:
                st.markdown("---")
                st.markdown("### 🔬 3-2-2 A/B-Test Paket")
                variations = [
                    ("🖼️ Variante A — Original", ""),
                    ("🖼️ Variante B — Anderer Winkel", "\nCREATIVE VARIATION B: Change the camera angle significantly — different perspective, crop, distance. Same product, fresh visual feel."),
                    ("🖼️ Variante C — Andere Stimmung", "\nCREATIVE VARIATION C: Change mood and lighting completely — different color temperature, time of day, atmosphere. Product identical, different 'world'."),
                ]
                st.session_state["ad_322_prompts"] = []
                for name, variation in variations:
                    var_prompt = ad_prompt + variation
                    st.session_state["ad_322_prompts"].append({"name": name, "prompt": var_prompt})
                    with st.expander(name):
                        st.code(var_prompt[-300:], language="text")
                if ad_322_headlines or ad_322_texts:
                    st.markdown("### 📋 Texte für den Ads Manager")
                    if ad_322_headlines:
                        st.markdown("**Headlines:**")
                        for h in ad_322_headlines:
                            st.code(h, language="text")
                    if ad_322_texts:
                        st.markdown("**Primary Texts:**")
                        for t in ad_322_texts:
                            st.code(t, language="text")
                    st.info(f"🧪 **Kombinationen:** {len(variations)} Bilder × {max(len(ad_322_headlines),1)} Headlines × {max(len(ad_322_texts),1)} Texte = **{len(variations) * max(len(ad_322_headlines),1) * max(len(ad_322_texts),1)} testbare Varianten**")

            st.session_state.prompt_history.append({
                "time": datetime.now().strftime("%H:%M:%S"), "prompt": ad_prompt, "type": "🎯 Ad Creative"})
            st.download_button("💾 Ad-Prompt speichern (.txt)", data=ad_prompt,
                file_name=f"nano_banana_ad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain")

            if ad_generate_brief:
                st.markdown("---")
                st.markdown("### 📋 Ad Brief")
                brief_persona = ad_target.split("(")[0].strip() if "(" in ad_target else ad_target
                brief_type = ad_type.split(" ", 1)[1] if " " in ad_type else ad_type
                brief_funnel = "TOFU" if "TOFU" in ad_funnel else ("MOFU" if "MOFU" in ad_funnel else "BOFU")
                brief_emotion = ad_primary_emotion.split(" ", 1)[1] if ad_primary_emotion and "Automatisch" not in ad_primary_emotion else "Automatisch"
                brief_text = f"""📋 AD BRIEF — {product}
{'='*50}

📌 CONCEPT:       {brief_type} Ad für {product}
🎨 CREATIVE TYPE: {brief_type}
🎯 FUNNEL STAGE:  {brief_funnel}
👤 PERSONA:       {brief_persona}
🎭 EMOTION:       {brief_emotion}

📰 HEADLINE:      {ad_headline if ad_headline else '(noch nicht definiert)'}
📝 SUBLINE:       {ad_subline if ad_subline else '—'}
🔘 CTA:           {ad_cta if ad_cta else '—'}
🏷️ ANGEBOT:       {ad_offer if ad_offer else '—'}

🎣 HOOK:          {ad_hook if ad_hook else '—'}
🖼️ LAYOUT:        {ad_composition}
🎨 FARBSCHEMA:    {ad_color_scheme}
🔤 SCHRIFT:       {ad_font}
📐 FORMAT:        {ad_format}
😊 STIMMUNG:      {ad_mood}
{'🧲 CURIOSITY GAP: ' + ad_curiosity_hook if ad_curiosity_gap and ad_curiosity_hook else ''}

🔀 DIVERSITY CHECK:
   Persona:    {'✅' if diversity_persona else '❌'}
   Messaging:  {'✅' if diversity_messaging else '❌'}
   Hook:       {'✅' if diversity_hook else '❌'}
   Format:     {'✅' if diversity_format else '❌'}
   Score:      {diversity_count}/4 Hebel

{'='*50}
💡 VISUAL DIRECTION:
{ad_composition} mit {ad_color_scheme}. {brief_type} Stil. Hook: {ad_hook}.
Zielgruppe: {brief_persona}.
"""
                st.code(brief_text, language="text")
                st.download_button("📋 Ad Brief speichern (.txt)", data=brief_text,
                    file_name=f"ad_brief_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", key="dl_brief")

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
                all_ad_refs = []
                if model_ref_files:
                    all_ad_refs.extend(model_ref_files)
                if ad_ref_files:
                    all_ad_refs.extend(ad_ref_files)
                ad_refs = all_ad_refs if all_ad_refs else None
                if model_ref_files:
                    desc_hint = " + Beschreibung" if st.session_state.get("model_description") else ""
                    st.info(f"👤 {len(model_ref_files)} Model-Bild(er){desc_hint} werden mitgesendet.")
                if ad_ref_files:
                    st.info(f"📸 {len(ad_ref_files)} Produkt-Referenzbild(er) werden mitgesendet...")

                active_ad_prompt = st.session_state.last_ad_prompt
                model_ref_block = ""
                if model_ref_files:
                    model_ref_block = build_model_ref_instruction(
                        len(model_ref_files), st.session_state.get("model_description", ""),
                        len(ad_ref_files) if ad_ref_files else 0)
                    active_ad_prompt += model_ref_block

                ad_ar_map = {
                    "Facebook Feed (1:1 Quadrat)": "1:1", "Facebook Feed (4:5 Hochformat)": "4:5",
                    "Instagram Story / Reels (9:16)": "9:16", "Facebook Cover / Banner (16:9)": "16:9",
                    "Carousel Einzelbild (1:1)": "1:1"}
                ad_ar_str = ad_ar_map.get(ad_format, "1:1")

                if use_322 and st.session_state.get("ad_322_prompts"):
                    prompts_to_gen = [(p["name"], p["prompt"] + model_ref_block) for p in st.session_state["ad_322_prompts"]]
                    st.info(f"🔬 3-2-2 Modus: Generiere {len(prompts_to_gen)} visuell unterschiedliche Varianten...")
                    for idx, (name, var_prompt) in enumerate(prompts_to_gen):
                        with st.spinner(f"{name} ({idx+1}/{len(prompts_to_gen)})..."):
                            img_bytes, mime_type = smart_generate_image(
                                var_prompt, gemini_key, reference_images=ad_refs, aspect_ratio_str=ad_ar_str)
                        if img_bytes:
                            st.session_state.generated_images.append({
                                "bytes": img_bytes, "mime": mime_type, "type": "ad_creative",
                                "variant": name, "time": datetime.now().strftime("%H:%M:%S")})
                else:
                    for i in range(num_ad_images):
                        with st.spinner(f"Gemini generiert Ad Creative {i+1}/{num_ad_images}..."):
                            img_bytes, mime_type = smart_generate_image(
                                active_ad_prompt, gemini_key, reference_images=ad_refs, aspect_ratio_str=ad_ar_str)
                        if img_bytes:
                            st.session_state.generated_images.append({
                                "bytes": img_bytes, "mime": mime_type, "type": "ad_creative",
                                "time": datetime.now().strftime("%H:%M:%S")})

        ad_imgs = [img for img in st.session_state.generated_images if img["type"] == "ad_creative"]
        if ad_imgs:
            st.markdown("### 🖼️ Generierte Ad Creatives")
            st.caption("💡 Tipp: Generiere 3-4 Varianten und teste sie als A/B-Test im Facebook Ads Manager!")
            cols = st.columns(min(len(ad_imgs), 4))
            for idx, img in enumerate(ad_imgs):
                with cols[idx % 4]:
                    st.image(img["bytes"], caption=f"Ad Creative #{idx+1} — {img['time']}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(f"💾 Ad #{idx+1} speichern", data=img["bytes"],
                        file_name=f"nano_banana_ad_{idx+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"], key=f"dl_ad_{idx}_{img['time']}")
            if st.button("🗑️ Generierte Ad Creatives löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "ad_creative"]
                st.rerun()

    # --- GENERATE CAROUSEL WITH GEMINI ---
    if st.session_state.get("last_carousel_prompts"):
        st.markdown("---")
        st.markdown("### 🎠 Carousel mit Gemini generieren")
        st.caption(f"📌 {len(st.session_state.last_carousel_prompts)} Slides werden nacheinander generiert (1:1).")
        if not gemini_key:
            st.warning("⚠️ Gemini API Key fehlt!")
        if st.button("🚀 CAROUSEL JETZT ERSTELLEN", disabled=not gemini_key):
            all_carousel_refs = []
            if model_ref_files:
                all_carousel_refs.extend(model_ref_files)
            if ad_ref_files:
                all_carousel_refs.extend(ad_ref_files)
            ad_refs = all_carousel_refs if all_carousel_refs else None
            model_ref_block = ""
            if model_ref_files:
                model_ref_block = build_model_ref_instruction(
                    len(model_ref_files), st.session_state.get("model_description", ""),
                    len(ad_ref_files) if ad_ref_files else 0)
                st.info(f"👤 {len(model_ref_files)} Model-Bild(er) bei jeder Slide.")
            if ad_ref_files:
                st.info(f"📸 {len(ad_ref_files)} Produkt-Referenz(en) bei jeder Slide...")

            carousel_progress = st.progress(0, text="🎠 Carousel wird generiert...")
            total = len(st.session_state.last_carousel_prompts)
            for i, slide_prompt in enumerate(st.session_state.last_carousel_prompts):
                carousel_progress.progress(((i + 1) / total) * 0.95, text=f"🎠 Slide {i+1}/{total}...")
                pro_hint = " (Pro)" if "💎 Pro" in model_quality else (" (Hybrid)" if "🔀 Hybrid" in model_quality else "")
                with st.spinner(f"Gemini generiert Slide {i+1}{pro_hint}..."):
                    img_bytes, mime_type = smart_generate_image(
                        slide_prompt + model_ref_block, gemini_key, reference_images=ad_refs, aspect_ratio_str="1:1")
                if img_bytes:
                    st.session_state.generated_images.append({
                        "bytes": img_bytes, "mime": mime_type, "type": "carousel",
                        "slide": i + 1, "time": datetime.now().strftime("%H:%M:%S")})
            carousel_progress.progress(1.0, text="✅ Carousel fertig!")

        carousel_imgs = [img for img in st.session_state.generated_images if img["type"] == "carousel"]
        if carousel_imgs:
            st.markdown("### 🎠 Carousel Slides")
            cols = st.columns(min(len(carousel_imgs), 5))
            for idx, img in enumerate(carousel_imgs):
                with cols[idx % 5]:
                    slide_num = img.get("slide", idx + 1)
                    st.image(img["bytes"], caption=f"Slide {slide_num}", use_container_width=True)
                    ext = "png" if "png" in img["mime"] else "jpg"
                    st.download_button(f"💾 Slide {slide_num}", data=img["bytes"],
                        file_name=f"nano_banana_carousel_slide{slide_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}",
                        mime=img["mime"], key=f"dl_carousel_{idx}_{img['time']}")
            if st.button("🗑️ Carousel-Slides löschen"):
                st.session_state.generated_images = [img for img in st.session_state.generated_images if img["type"] != "carousel"]
                st.rerun()
