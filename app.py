import io
import streamlit as st
from engine import (
    encode_image_bytes_to_base64,
    analyze_image,
    chat_about_image,
    generate_summary_audio,
    generate_detailed_audio,
    generate_full_audio,
    text_to_audio_buffer,
    LANGUAGES,
)

# ──────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sight-to-Speech",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────
# CSS  — warm cream/sand light theme, full readability
# ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Sans+3:wght@300;400;500;600&display=swap');

/* ── Reset & base ── */
html, body, [class*="css"] {
    font-family: 'Source Sans 3', sans-serif;
    color: #1a1410;
}

/* ── Page background — warm cream ── */
.stApp { background: #faf7f2 !important; }
.main .block-container { padding-top: 1.5rem; padding-bottom: 3rem; }

/* ── Sidebar — warm white ── */
[data-testid="stSidebar"] {
    background: #f5f0e8 !important;
    border-right: 1px solid #e0d8cc !important;
}
[data-testid="stSidebar"] section { padding-top: 1.5rem; }

/* Force ALL sidebar text to dark */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] caption,
[data-testid="stSidebar"] small {
    color: #2c2420 !important;
}

/* Sidebar select box */
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: #ede8df !important;
    border: 1px solid #c8bfb0 !important;
    color: #1a1410 !important;
    border-radius: 8px !important;
}
[data-testid="stSidebar"] .stSelectbox svg { color: #5c4a3a !important; fill: #5c4a3a !important; }

/* Sidebar radio */
[data-testid="stSidebar"] .stRadio label { color: #2c2420 !important; }

/* Sidebar button */
[data-testid="stSidebar"] .stButton > button {
    background: #e8ddd0 !important;
    border: 1px solid #c8bfb0 !important;
    color: #2c2420 !important;
    border-radius: 8px !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #ddd3c5 !important;
    border-color: #a89880 !important;
}

/* ── HERO ── */
.hero {
    text-align: center;
    padding: 2rem 1rem 1.8rem;
    background: linear-gradient(180deg, #faf7f2 0%, #f5f0e8 100%);
    border-bottom: 1px solid #e8e0d4;
    margin-bottom: 1.8rem;
    border-radius: 0 0 20px 20px;
}
.hero-eyebrow {
    font-size: 0.65rem; letter-spacing: 4px; text-transform: uppercase;
    color: #9c7c5c; font-weight: 600; margin-bottom: 0.5rem;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: 3rem; font-weight: 900;
    color: #1a1410; line-height: 1.1;
    margin-bottom: 0.5rem;
    letter-spacing: -0.5px;
}
.hero-title span { color: #b5651d; }
.hero-sub {
    font-size: 1rem; color: #6b5a48;
    max-width: 480px; margin: 0 auto;
    font-weight: 300; line-height: 1.6;
}

/* ── Section headers ── */
.sec-head {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem; font-weight: 700;
    color: #2c2420; margin: 1.4rem 0 0.7rem;
    display: flex; align-items: center; gap: 0.45rem;
    border-bottom: 2px solid #e8ddd0;
    padding-bottom: 0.45rem;
}

/* ── Result cards ── */
.rcard {
    background: #ffffff;
    border: 1px solid #e8e0d4;
    border-left: 4px solid #b5651d;
    border-radius: 10px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.8rem;
    box-shadow: 0 1px 4px rgba(90,60,30,0.06);
}
.rcard-label {
    font-size: 0.6rem; font-weight: 600;
    letter-spacing: 2.5px; text-transform: uppercase;
    color: #9c7c5c; margin-bottom: 0.5rem;
}
.rcard-text {
    font-size: 1rem; color: #1a1410;
    line-height: 1.75; font-weight: 400;
}

/* ── Audio section ── */
.audio-row {
    background: #f5f0e8;
    border: 1px solid #e0d4c4;
    border-radius: 8px;
    padding: 0.6rem 0.9rem 0.3rem;
    margin-bottom: 1rem;
}
.audio-row-label {
    font-size: 0.62rem; font-weight: 600;
    letter-spacing: 2px; text-transform: uppercase;
    color: #9c7c5c; margin-bottom: 0.25rem;
}

/* Force audio player to look good on light bg */
audio { width: 100%; border-radius: 6px; }

/* ── Language badge ── */
.lang-pill {
    display: inline-flex; align-items: center; gap: 5px;
    background: #f0e8dc; border: 1px solid #d4c4b0;
    color: #7c5c3c; font-size: 0.72rem; font-weight: 600;
    padding: 3px 12px; border-radius: 20px;
    margin-bottom: 1rem; letter-spacing: 0.5px;
}

/* ── Divider ── */
.warm-hr { border: none; border-top: 1px solid #e8e0d4; margin: 1.2rem 0; }

/* ── Upload area ── */
[data-testid="stFileUploader"] > div {
    background: #ffffff !important;
    border: 2px dashed #c8b89a !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"] span,
[data-testid="stFileUploader"] p,
[data-testid="stFileUploader"] small {
    color: #6b5a48 !important;
}
[data-testid="stFileUploader"] button {
    background: #f0e8dc !important;
    color: #5c4030 !important;
    border: 1px solid #c8b89a !important;
    border-radius: 6px !important;
}

/* ── Chat bubbles ── */
.chat-outer { margin-top: 0.5rem; }
.cmsg { display: flex; gap: 0.6rem; margin-bottom: 0.9rem; align-items: flex-start; }
.cmsg.user { flex-direction: row-reverse; }

.cbubble {
    max-width: 80%; padding: 0.75rem 1rem;
    border-radius: 12px; font-size: 0.95rem; line-height: 1.65;
}
.cbubble.user {
    background: #b5651d; color: #fff;
    border-bottom-right-radius: 3px;
}
.cbubble.assistant {
    background: #ffffff; border: 1px solid #e0d4c4;
    color: #1a1410; border-bottom-left-radius: 3px;
    box-shadow: 0 1px 3px rgba(90,60,30,0.07);
}

.cavatar {
    width: 28px; height: 28px; border-radius: 50%; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.75rem; margin-top: 2px;
}
.cavatar.user { background: #b5651d; color: #fff; }
.cavatar.assistant { background: #f0e8dc; border: 1px solid #d4c4b0; color: #7c5c3c; }

/* ── Chat input override ── */
[data-testid="stChatInput"] > div {
    background: #ffffff !important;
    border: 1px solid #d4c4b0 !important;
    border-radius: 10px !important;
}
[data-testid="stChatInput"] textarea {
    color: #1a1410 !important;
    background: transparent !important;
}

/* ── Main column text ── */
p, span, div, label, h1, h2, h3, caption {
    color: #1a1410;
}

/* ── Info / warning / error boxes ── */
.stAlert { border-radius: 8px !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #b5651d !important; }

/* ── Caption / small text ── */
.stCaption, small { color: #7c6a58 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #faf7f2; }
::-webkit-scrollbar-thumb { background: #d4c4b0; border-radius: 3px; }

/* ── Empty state placeholder ── */
.empty-state {
    text-align: center; padding: 4rem 2rem;
    color: #9c8878;
}
.empty-state .big-icon { font-size: 3.5rem; margin-bottom: 0.8rem; }
.empty-state .empty-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem; color: #5c4a38; font-weight: 700;
    margin-bottom: 0.4rem;
}
.empty-state .empty-sub { font-size: 0.88rem; color: #9c8878; line-height: 1.6; }
.empty-tags {
    margin-top: 1.2rem; font-size: 0.75rem; color: #b8a898;
    display: flex; justify-content: center; gap: 1.2rem;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# SESSION STATE  — all keys initialised once
# ──────────────────────────────────────────────────────────
defaults = {
    "analysis":     None,
    "image_b64":    None,
    "chat_history": [],
    "cached_lang":  "English",   # language used for the CURRENT cached analysis
    "cached_file":  None,        # filename used for the CURRENT cached analysis
    "reply_audios": [],          # list of bytes objects, one per assistant reply
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ──────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    language = st.selectbox(
        "Output Language",
        options=list(LANGUAGES.keys()),
        index=0,
        help="AI will respond and speak in this language.",
    )

    st.markdown("---")
    st.markdown("### 🔊 Audio Speed")
    audio_slow = st.radio("Speed", ["Normal", "Slow"], index=0, horizontal=True) == "Slow"

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.caption(
        "Uses **Ollama (llava)** locally — 100% private and free. "
        "Audio by **gTTS** (needs internet)."
    )
    st.caption("Run: `ollama pull llava` to get the model.")

    st.markdown("---")
    if st.button("🗑️ Clear & Reset Everything"):
        for k, v in defaults.items():
            st.session_state[k] = (v.copy() if isinstance(v, list) else v)
        st.rerun()


# ──────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-eyebrow">AI Accessibility Tool</div>
    <div class="hero-title">👁️ Sight<span>-to-</span>Speech</div>
    <div class="hero-sub">Upload any image — AI reads, describes, and speaks it aloud in your language.</div>
</div>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# TWO-COLUMN LAYOUT
# ──────────────────────────────────────────────────────────
left_col, right_col = st.columns([1, 1.15], gap="large")


# ════════════════════════════════════
# LEFT — Upload + preview
# ════════════════════════════════════
with left_col:
    st.markdown('<div class="sec-head">📁 Upload Image</div>', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "upload",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file:
        st.image(uploaded_file, use_container_width=True, caption=uploaded_file.name)

        # ── Determine whether we need to re-analyse ──
        # Compare against what was LAST used to build the cached result
        need_reanalysis = (
            st.session_state.analysis is None
            or st.session_state.cached_file != uploaded_file.name
            or st.session_state.cached_lang  != language
        )

        if need_reanalysis:
            # Read bytes NOW while file object is still valid
            image_bytes = uploaded_file.read()
            st.session_state.image_b64    = encode_image_bytes_to_base64(image_bytes)
            st.session_state.chat_history = []   # fresh chat for new image/lang
            st.session_state.reply_audios = []   # fresh audio list
            st.session_state.analysis     = None # clear stale result

            with st.spinner(f"🤖 Analysing in {language} — this may take 20–60 s…"):
                try:
                    result = analyze_image(st.session_state.image_b64, language)
                    # Only persist after success
                    st.session_state.analysis    = result
                    st.session_state.cached_file = uploaded_file.name
                    st.session_state.cached_lang = language
                except RuntimeError as e:
                    st.error(f"**Connection error:** {e}")
                    st.info("Make sure Ollama is running: open a terminal and type `ollama serve`")
                    st.stop()
                except ValueError as e:
                    st.error(f"**Model error:** {e}")
                    st.info("Try: `ollama pull llava`")
                    st.stop()
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="big-icon">🖼️</div>
            <div class="empty-title">No image yet</div>
            <div class="empty-sub">Click Browse files or drag &amp; drop<br>a JPG, PNG, or WebP here to get started.</div>
            <div class="empty-tags">
                <span>📋 Menus</span><span>🚦 Signs</span>
                <span>✉️ Letters</span><span>🌄 Scenes</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ════════════════════════════════════
# RIGHT — Results + Chat
# ════════════════════════════════════
with right_col:

    if st.session_state.analysis:
        result = st.session_state.analysis

        # ── Language pill ──
        st.markdown(
            f'<div class="lang-pill">🌐 {st.session_state.cached_lang}</div>',
            unsafe_allow_html=True,
        )

        # ────────────────────────────────
        # QUICK SUMMARY
        # ────────────────────────────────
        st.markdown('<div class="sec-head">⚡ Quick Summary</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="rcard">
            <div class="rcard-label">Summary</div>
            <div class="rcard-text">{result['quick_summary']}</div>
        </div>""", unsafe_allow_html=True)

        try:
            s_audio = generate_summary_audio(result, st.session_state.cached_lang)
            st.markdown('<div class="audio-row"><div class="audio-row-label">🔊 Listen — Summary</div>', unsafe_allow_html=True)
            st.audio(s_audio, format="audio/mp3")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Audio unavailable: {e}")

        st.markdown('<hr class="warm-hr">', unsafe_allow_html=True)

        # ────────────────────────────────
        # DETAILED READOUT
        # ────────────────────────────────
        st.markdown('<div class="sec-head">📋 Detailed Readout</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="rcard">
            <div class="rcard-label">Full Description</div>
            <div class="rcard-text">{result['detailed_readout']}</div>
        </div>""", unsafe_allow_html=True)

        try:
            d_audio = generate_detailed_audio(result, st.session_state.cached_lang)
            st.markdown('<div class="audio-row"><div class="audio-row-label">🔊 Listen — Full Description</div>', unsafe_allow_html=True)
            st.audio(d_audio, format="audio/mp3")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Audio unavailable: {e}")

        st.markdown('<hr class="warm-hr">', unsafe_allow_html=True)

        # ────────────────────────────────
        # FULL COMBINED AUDIO
        # ────────────────────────────────
        st.markdown('<div class="sec-head">🎧 Complete Audio Readout</div>', unsafe_allow_html=True)
        st.caption("Summary + full description played together.")
        try:
            full_audio = generate_full_audio(result, st.session_state.cached_lang)
            st.markdown('<div class="audio-row"><div class="audio-row-label">🔊 Full Readout</div>', unsafe_allow_html=True)
            st.audio(full_audio, format="audio/mp3")
            st.markdown('</div>', unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"Audio unavailable: {e}")

        st.markdown('<hr class="warm-hr">', unsafe_allow_html=True)

        # ────────────────────────────────
        # FOLLOW-UP CHAT
        # ────────────────────────────────
        st.markdown(
            f'<div class="sec-head">💬 Ask About This Image</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"Replies will be in **{st.session_state.cached_lang}**. Ask anything about what's in the image.")

        # Render chat history — interleave text bubbles + audio players
        if st.session_state.chat_history:
            # Build an index: assistant_reply_index -> position in reply_audios list
            assistant_turn = 0
            for msg in st.session_state.chat_history:
                role    = msg["role"]
                content = msg["content"].replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
                avatar  = "🧑" if role == "user" else "👁️"

                st.markdown(f"""
                <div class="cmsg {role}">
                    <div class="cavatar {role}">{avatar}</div>
                    <div class="cbubble {role}">{content}</div>
                </div>""", unsafe_allow_html=True)

                # After each assistant bubble, show its audio player
                if role == "assistant":
                    audios = st.session_state.reply_audios
                    if assistant_turn < len(audios) and audios[assistant_turn]:
                        import io as _io
                        buf = _io.BytesIO(audios[assistant_turn])
                        st.markdown(
                            '<div class="audio-row"><div class="audio-row-label">🔊 Listen — Reply</div>',
                            unsafe_allow_html=True,
                        )
                        st.audio(buf, format="audio/mp3")
                        st.markdown('</div>', unsafe_allow_html=True)
                    assistant_turn += 1

        # Input
        user_input = st.chat_input(f"Ask something… (answering in {st.session_state.cached_lang})")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.spinner("Thinking…"):
                try:
                    reply = chat_about_image(
                        image_b64       = st.session_state.image_b64,
                        user_question   = user_input,
                        chat_history    = st.session_state.chat_history[:-1],
                        analysis_result = result,
                        language        = st.session_state.cached_lang,
                    )
                except (RuntimeError, ValueError) as e:
                    reply = f"⚠️ Error: {e}"

            st.session_state.chat_history.append({"role": "assistant", "content": reply})

            # Generate audio and store as raw bytes in session state so it
            # survives the st.rerun() below
            try:
                r_buf = text_to_audio_buffer(reply, st.session_state.cached_lang)
                st.session_state.reply_audios.append(r_buf.read())
            except Exception:
                st.session_state.reply_audios.append(None)

            st.rerun()

    else:
        # Empty right panel
        st.markdown("""
        <div class="empty-state" style="padding-top: 5rem;">
            <div class="big-icon">✨</div>
            <div class="empty-title">Results will appear here</div>
            <div class="empty-sub">
                Once you upload an image on the left,<br>
                the AI will describe it and audio players<br>
                will appear for each section.
            </div>
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding: 2rem 0 0.5rem;
            color: #b8a898; font-size:0.72rem; border-top: 1px solid #e8e0d4; margin-top:2rem;">
    Powered by&nbsp;<strong style="color:#7c5c3c;">Ollama llava</strong>
    &nbsp;·&nbsp;<strong style="color:#7c5c3c;">gTTS</strong>
    &nbsp;·&nbsp;<strong style="color:#7c5c3c;">Streamlit</strong>
    &nbsp;·&nbsp; 100 % free &amp; private
</div>
""", unsafe_allow_html=True)
