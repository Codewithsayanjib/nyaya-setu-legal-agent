import streamlit as st
import os
import json
import base64
import tempfile
from dotenv import load_dotenv

from audio_recorder_streamlit import audio_recorder
from src.sarvam_client import SarvamClient
from src.statute_db import StatuteDatabase
from src.legal_agent import LegalAgent

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Nyaya-Setu | Explainable BNS Statute Predictor",
    page_icon="⚖️",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .badge-bns {
        background-color: #EEF2FF;
        color: #3730A3;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        border: 1px solid #C7D2FE;
    }
    .badge-ipc {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        border: 1px solid #FDE68A;
    }
    .status-satisfied {
        color: #047857;
        font-weight: 600;
    }
    .status-failed {
        color: #B91C1C;
        font-weight: 600;
    }
    .status-borderline {
        color: #D97706;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar configuration
with st.sidebar:
    st.image("https://img.icons8.com/color/96/scales.png", width=64)
    st.markdown("### ⚙️ Engine Settings")

    api_key_input = st.text_input(
        "Sarvam API Key",
        value="",
        type="password",
        help="Optional. Leave blank to use the server-side SARVAM_API_KEY (.env or Streamlit secrets)."
    )
    # Never prefill the widget with the server key: it would be sent to every visitor's browser.
    if not api_key_input:
        api_key_input = os.getenv("SARVAM_API_KEY", "")
        if not api_key_input:
            try:
                api_key_input = st.secrets.get("SARVAM_API_KEY", "")
            except Exception:
                api_key_input = ""

    indic_lang = st.selectbox(
        "Preferred Citizen / Voice Language",
        options=[
            ("Hindi", "hi-IN"),
            ("Bengali", "bn-IN"),
            ("Kannada", "kn-IN"),
            ("Marathi", "mr-IN"),
            ("Tamil", "ta-IN"),
            ("Telugu", "te-IN"),
            ("Gujarati", "gu-IN"),
            ("Malayalam", "ml-IN"),
            ("Punjabi", "pa-IN"),
            ("Odia", "od-IN"),
            ("English", "en-IN")
        ],
        format_func=lambda x: x[0],
        index=0
    )
    selected_lang_code = indic_lang[1]

    st.markdown("---")
    st.markdown("#### ⚖️ Grounding Scope")
    st.markdown("""
    **Bharatiya Nyaya Sanhita (BNS) 2023**
    - High-frequency FIR offences
    - Dual IPC 1860 concordance
    - Ingredient-level verification
    """)

    # Mock Mode toggle for easy testing without active credits
    use_mock_mode = st.toggle("Mock Evaluation Mode (Demo)", value=False, help="Simulate Sarvam API responses if running without an active key.")

st.markdown('<div class="main-title">⚖️ Nyaya-Setu (न्याय-सेतु)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Multilingual Explainable Statute Predictor & FIR Legal Triage Agent powered by Sarvam AI</div>', unsafe_allow_html=True)

# Sample Incidents for quick demo
SAMPLE_CASES = {
    "Select a preloaded FIR scenario...": "",
    "Robbery at gunpoint in shop (Hindi)": "कल रात करीब 11 बजे दो अज्ञात लड़के मेरी किराने की दुकान में जबरन घुसे। एक ने मुझे कट्टा दिखाया और जान से मारने की धमकी दी। दूसरे ने गल्ले से 25,000 रुपये नकद निकाले और दोनों मोटरसाइकिल पर भाग गए।",
    "Cheating / Fraud investment promise (Hindi)": "रमेश नाम के व्यक्ति ने मुझे 2 लाख रुपये एक सरकारी ठेके में लगाने को कहा और 30 दिन में दोगुना मुनाफा देने का फर्जी लेटर दिखाया। पैसे लेने के बाद उसने अपना फोन बंद कर लिया और अब फरार है।",
    "Assault and trespass into residential house (English)": "Yesterday evening around 8 PM, neighbor Suresh broke open our front gate, illegally barged into our living room, and physically punched my brother causing a fracture on his nose, threatening to burn our house down.",
    "Street snatching with criminal intimidation (English)": "While returning from work near Sector 14, an unknown man obstructed my path, threatened to stab me with a knife, and snatched my gold chain and wallet before fleeing into the alley."
}

selected_sample = st.selectbox("📝 Quick Demo Presets:", list(SAMPLE_CASES.keys()))

col1, col2 = st.columns([1, 1], gap="medium")

with col1:
    st.markdown("### 🎙️ 1. Incident Intake")

    intake_mode = st.radio(
        "Intake Method:",
        ["🎙️ Live Mic Recording", "📝 Type / Paste Incident Text", "📁 Upload Audio File"],
        horizontal=True
    )

    incident_text = ""
    audio_file_path = None

    if intake_mode == "🎙️ Live Mic Recording":
        st.info("Click the microphone icon below and speak your incident statement in your preferred language:")
        audio_bytes = audio_recorder(
            text="Click to record / stop",
            recording_color="#e74c3c",
            neutral_color="#3498db",
            icon_size="2x"
        )
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                audio_file_path = tmp.name

    elif intake_mode == "📝 Type / Paste Incident Text":
        default_val = SAMPLE_CASES[selected_sample] if selected_sample != "Select a preloaded FIR scenario..." else ""
        incident_text = st.text_area(
            "Enter Statement / Complainant Account (in any Indian language or English):",
            value=default_val,
            height=200,
            placeholder="उदाहरण: कल रात 11 बजे दो लड़के मेरी दुकान में घुसे..."
        )
    else:
        uploaded_audio = st.file_uploader("Upload audio statement (.wav, .mp3, .m4a):", type=["wav", "mp3", "m4a", "ogg"])
        if uploaded_audio:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_audio.name)[1]) as tmp:
                tmp.write(uploaded_audio.getvalue())
                audio_file_path = tmp.name
            st.audio(uploaded_audio)

    analyze_btn = st.button("⚖️ Analyze & Predict Statutes", type="primary", use_container_width=True)

with col2:
    st.markdown("### 🔍 2. Explainable Legal Audit")

    if analyze_btn:
        if not api_key_input and not use_mock_mode:
            st.error("Please provide your Sarvam API Key in the sidebar or enable 'Mock Evaluation Mode'.")
        elif not incident_text and not audio_file_path:
            st.warning("Please enter incident text or upload an audio file.")
        else:
            with st.spinner("Processing through Sarvam AI Legal Pipeline..."):
                client = SarvamClient(api_key=api_key_input)
                agent = LegalAgent(sarvam_client=client)

                original_statement = incident_text
                english_statement = incident_text

                # 1. ASR Step
                if audio_file_path:
                    st.info("Transcribing audio using Sarvam Saaras ASR...")
                    if use_mock_mode:
                        original_statement = "कल रात करीब 11 बजे दो अज्ञात लड़के मेरी किराने की दुकान में जबरन घुसे। एक ने मुझे कट्टा दिखाया और 25,000 रुपये लूट लिए।"
                    else:
                        try:
                            original_statement = agent.transcribe_audio(audio_file_path, language_code=selected_lang_code)
                        except Exception as e:
                            st.error(f"ASR Error: {e}")
                            original_statement = ""

                st.markdown(f"**Original Statement:** *\"{original_statement}\"*")

                # 2. Translation & Normalization Step
                if selected_lang_code != "en-IN" and original_statement:
                    if use_mock_mode:
                        english_statement = "Last night around 11 PM, two unknown men forcibly entered my grocery store. One brandished a country pistol at me and threatened to kill me, while the other looted Rs 25,000 from the cash drawer."
                    else:
                        try:
                            english_statement = agent.translate_to_english(original_statement, source_lang=selected_lang_code)
                        except Exception as e:
                            english_statement = original_statement

                with st.expander("🌐 English Standardized Legal Fact Statement", expanded=False):
                    st.write(english_statement)

                # 3. LLM Statute Extraction & Audit
                analysis = None
                if use_mock_mode:
                    analysis = {
                        "incident_summary": "Two unknown offenders forcibly entered a commercial shop during late hours, threatened the owner with a firearm, and seized Rs 25,000 in cash.",
                        "extracted_facts": {
                            "accused_count": "2 persons",
                            "weapons_used": ["Country-made pistol (katta)"],
                            "property_involved": "Rs 25,000 cash from drawer",
                            "violence_or_threat": "Threat of instant death with firearm",
                            "location_type": "Grocery store / Closed commercial establishment at 11 PM",
                            "intent_mens_rea": "Dishonest and predatory criminal intent to steal by force"
                        },
                        "predicted_charges": [
                            {
                                "bns_section": "309(4)",
                                "ipc_equivalent": "392 / 397",
                                "offence_title": "Robbery (with deadly weapon/fear of instant death)",
                                "confidence": "High",
                                "ingredients_evaluation": [
                                    {
                                        "ingredient": "Movable property taken out of possession without consent",
                                        "status": "Satisfied",
                                        "supporting_fact": "Rs 25,000 seized from the shop cash box."
                                    },
                                    {
                                        "ingredient": "Causing or attempting fear of instant death or hurt",
                                        "status": "Satisfied",
                                        "supporting_fact": "Pointed a country-made pistol ('katta') at victim."
                                    }
                                ],
                                "procedural_nature": {
                                    "cognizable": True,
                                    "bailable": False,
                                    "compoundable": "No",
                                    "max_punishment": "Rigorous imprisonment up to 10-14 years"
                                },
                                "reasoning": "Simple theft is elevated to Robbery under BNS 309 because the perpetrators actively used a deadly weapon to induce imminent terror."
                            },
                            {
                                "bns_section": "331(4)",
                                "ipc_equivalent": "457",
                                "offence_title": "Lurking house-trespass or house-breaking by night",
                                "confidence": "High",
                                "ingredients_evaluation": [
                                    {
                                        "ingredient": "Entry into building/property used for custody of property",
                                        "status": "Satisfied",
                                        "supporting_fact": "Grocery shop holding merchandise and cash box."
                                    },
                                    {
                                        "ingredient": "Committed between sunset and sunrise (night)",
                                        "status": "Satisfied",
                                        "supporting_fact": "Incident occurred at 11:00 PM."
                                    }
                                ],
                                "procedural_nature": {
                                    "cognizable": True,
                                    "bailable": False,
                                    "compoundable": "No",
                                    "max_punishment": "Imprisonment up to 14 years and fine"
                                },
                                "reasoning": "Unlawful entry into premises after hours to commit robbery fulfills aggravated house-breaking."
                            }
                        ],
                        "excluded_or_borderline_charges": [
                            {
                                "bns_section": "310",
                                "offence_title": "Dacoity",
                                "reason_excluded": "Statute requires 5 or more persons conjointly committing robbery. In this incident, only 2 persons were involved."
                            }
                        ],
                        "complainant_rights_summary": "This complaint outlines Cognizable and Non-Bailable offences. The police are mandated to register an FIR under Section 173 BNSS immediately. The weapon details will be recorded under the Arms Act, and you are entitled to a free signed copy of the FIR.",
                        "complainant_rights_summary_indic": "यह शिकायत संज्ञेय और गैर-जमानती अपराधों को दर्शाती है। पुलिस बीएनएसएस की धारा 173 के तहत तुरंत प्राथमिकी (FIR) दर्ज करने के लिए बाध्य है। हथियार का विवरण दर्ज किया जाएगा और आपको एफआईआर की एक निःशुल्क हस्ताक्षरित प्रति पाने का पूरा अधिकार है।"
                    }
                else:
                    try:
                        analysis = agent.analyze_incident(
                            incident_text_english=english_statement,
                            original_incident_text=original_statement,
                            user_lang=selected_lang_code
                        )
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

                if analysis:
                    st.success("Statute Analysis & Ingredient Verification Completed!")

                    # Display Extracted Facts
                    with st.expander("📋 Extracted Legal Incident Parameters", expanded=True):
                        facts = analysis.get("extracted_facts", {})
                        f_cols = st.columns(3)
                        f_cols[0].metric("Perpetrators", facts.get("accused_count", "N/A"))
                        f_cols[1].metric("Location", facts.get("location_type", "N/A"))
                        f_cols[2].metric("Property Loss", facts.get("property_involved", "None"))
                        st.markdown(f"**Weapons:** `{', '.join(facts.get('weapons_used', ['None']))}` | **Threat:** {facts.get('violence_or_threat', 'N/A')}")

                    # Display Recommended BNS Charges with Ingredient Audit
                    st.markdown("#### 📌 Recommended BNS Statutory Charges")

                    charges = analysis.get("predicted_charges", [])
                    for i, charge in enumerate(charges):
                        bns_sec = charge.get("bns_section")
                        ipc_sec = charge.get("ipc_equivalent")
                        title = charge.get("offence_title")
                        confidence = charge.get("confidence", "High")

                        with st.container():
                            st.markdown(f"""
                            <div style="background-color: #F9FAFB; padding: 12px; border-radius: 8px; border: 1px solid #E5E7EB; margin-bottom: 12px;">
                                <div style="display:flex; justify-content:space-between; align-items:center;">
                                    <h4 style="margin:0;">{title}</h4>
                                    <div>
                                        <span class="badge-bns">BNS § {bns_sec}</span>
                                        <span class="badge-ipc">IPC § {ipc_sec}</span>
                                    </div>
                                </div>
                                <p style="margin-top: 6px; font-size: 0.95rem; color: #374151;">{charge.get('reasoning')}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            # Ingredients Table
                            ing_evals = charge.get("ingredients_evaluation", [])
                            if ing_evals:
                                st.markdown("**Ingredient Audit Checklist:**")
                                ing_data = []
                                for ing in ing_evals:
                                    status_color = "status-satisfied" if ing.get("status") == "Satisfied" else "status-failed"
                                    st.markdown(f"- **{ing.get('ingredient')}**: <span class='{status_color}'>[{ing.get('status')}]</span> — *{ing.get('supporting_fact')}*", unsafe_allow_html=True)

                            # Procedural stats
                            proc = charge.get("procedural_nature", {})
                            p1, p2, p3 = st.columns(3)
                            p1.caption(f"**Cognizable:** {'Yes (Police can arrest without warrant)' if proc.get('cognizable') else 'No'}")
                            p2.caption(f"**Bailable:** {'Yes' if proc.get('bailable') else 'No (Non-Bailable)'}")
                            p3.caption(f"**Max Penalty:** {proc.get('max_punishment', 'N/A')}")
                            st.markdown("---")

                    # Display Excluded / Boundary Offenses
                    excluded = analysis.get("excluded_or_borderline_charges", [])
                    if excluded:
                        with st.expander("🛡️ Negative & Boundary Checks (Excluded Offences)", expanded=False):
                            for ex in excluded:
                                st.markdown(f"❌ **BNS Section {ex.get('bns_section')} ({ex.get('offence_title')}):** {ex.get('reason_excluded')}")

                    # Complainant Rights & Vernacular Readout
                    st.markdown("#### 📢 Complainant Rights & Legal Guidance")
                    indic_advisory = analysis.get("complainant_rights_summary_indic", analysis.get("complainant_rights_summary", ""))
                    st.info(indic_advisory)

                    # Sarvam TTS Audio Playback
                    if st.button("🔊 Listen to Legal Advisory (Sarvam Bulbul TTS)"):
                        with st.spinner("Synthesizing Indic voice via Sarvam Bulbul..."):
                            if use_mock_mode:
                                st.info("Audio generation simulated in Mock mode.")
                            else:
                                audio_b64 = agent.generate_audio_advisory(indic_advisory, target_lang=selected_lang_code)
                                if audio_b64:
                                    audio_bytes = base64.b64decode(audio_b64)
                                    st.audio(audio_bytes, format="audio/wav")
                                else:
                                    st.warning("Could not synthesize audio. Please verify your Sarvam API subscription.")
    else:
        st.info("👈 Enter an incident statement or upload audio on the left, then click **Analyze & Predict Statutes**.")
