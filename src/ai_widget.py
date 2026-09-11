from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from src.ai_engine import ask_ai_stream


PROJECT_ROOT = Path(__file__).resolve().parents[1]
AI_IMAGE = PROJECT_ROOT / "assets" / "ai_bot.png"
MAX_CHAT_MESSAGES = 20


@st.cache_data(show_spinner=False)
def _bot_image_data_uri() -> str:
    """Return the chatbot image as a cached data URI for the floating button."""
    if not AI_IMAGE.exists():
        return ""

    try:
        encoded = base64.b64encode(AI_IMAGE.read_bytes()).decode("utf-8")
        return "data:image/png;base64," + encoded
    except OSError:
        return ""


def _assistant_avatar():
    return str(AI_IMAGE) if AI_IMAGE.exists() else "🤖"


def _trim_chat_history() -> None:
    """Keep the UI responsive during long portfolio sessions."""
    history = st.session_state.setdefault("ai_chat_history", [])
    if len(history) > MAX_CHAT_MESSAGES:
        st.session_state["ai_chat_history"] = history[-MAX_CHAT_MESSAGES:]


def _quick_questions(quality_report: dict | None) -> list[tuple[str, str]]:
    if quality_report:
        return [
            ("Score", "What is the current data quality score?"),
            ("Top issues", "What are the top 3 data quality issues?"),
            ("Fix first", "Which issue should I fix first?"),
        ]

    return [
        ("Projects", "Tell me about Maheswara's strongest projects."),
        ("Skills", "What are Maheswara's strongest technical skills?"),
        ("This page", "What can I do on this page?"),
    ]


def render_ai_copilot(
    page_name: str = "Portfolio",
    page_context: str = "",
    industry: str = "General",
) -> None:
    """Render the responsive floating AI Portfolio and Data Quality Copilot."""
    st.session_state["current_page_name"] = page_name
    st.session_state["current_page_context"] = page_context
    st.session_state.setdefault("ai_chat_history", [])
    _trim_chat_history()

    image_uri = _bot_image_data_uri()

    st.html(
        f"""
<style>
.st-key-global_ai_widget {{
    position: fixed !important;
    right: 24px !important;
    bottom: 88px !important;
    width: 72px !important;
    height: 72px !important;
    z-index: 1000000;
    padding: 0 !important;
}}
.st-key-global_ai_widget [data-testid="stPopover"] button {{
    width: 72px !important;
    height: 72px !important;
    min-height: 72px;
    padding: 0 !important;
    border-radius: 50%;
    border: 3px solid white;
    background-color: #4169ff;
    background-image: url('{image_uri}');
    background-size: 64px 64px;
    background-position: center;
    background-repeat: no-repeat;
    box-shadow: 0 6px 24px #365dff55;
}}
.st-key-global_ai_widget [data-testid="stPopover"] button p {{
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
}}
.st-key-global_ai_widget [data-testid="stPopover"] button svg {{ display: none; }}
.st-key-global_ai_widget [data-testid="stPopover"] button::after {{
    content: '{"🤖" if not image_uri else ""}';
    font-size: 36px;
}}
.st-key-global_ai_widget button:focus-visible {{
    outline: 3px solid #172d66;
    outline-offset: 4px;
}}
div[data-testid="stPopoverBody"]:has(.ai-panel-title) {{
    width: 440px !important;
    max-width: calc(100vw - 24px) !important;
    max-height: calc(100dvh - 112px) !important;
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 16px !important;
    border-radius: 20px;
    background: var(--portfolio-surface, #ffffff);
    color: var(--portfolio-text, #182c50);
    border: 1px solid var(--portfolio-border, rgba(84, 111, 165, 0.14));
    box-shadow: 0 16px 48px #1b346633;
}}
.ai-panel-title {{
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.4;
    color: var(--portfolio-text, #182c50);
}}
div[data-testid="stPopoverBody"]:has(.ai-panel-title) .st-key-ai_messages {{
    height: clamp(140px, 32dvh, 300px) !important;
    overflow-y: auto;
}}
div[data-testid="stPopoverBody"]:has(.ai-panel-title) [data-testid="stChatMessage"] {{
    padding: 10px;
    border-radius: 12px;
}}
@media (max-width: 700px) {{
    .st-key-global_ai_widget {{
        right: 14px !important;
        bottom: max(76px, calc(env(safe-area-inset-bottom) + 62px)) !important;
        width: 54px !important;
        height: 54px !important;
    }}

    .st-key-global_ai_widget [data-testid="stPopover"] button {{
        width: 54px !important;
        height: 54px !important;
        min-width: 54px !important;
        min-height: 54px !important;
        background-size: 46px 46px;
    }}

    /* Compact mobile chatbot instead of nearly full-screen panel. */
    div[data-testid="stPopoverBody"]:has(.ai-panel-title) {{
        width: calc(100vw - 32px) !important;
        max-width: 420px !important;
        max-height: 70dvh !important;
        padding: 10px !important;
        border-radius: 16px !important;
        overflow-y: auto !important;
        overscroll-behavior: contain;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) .ai-panel-title {{
        font-size: 0.95rem !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) .st-key-ai_messages {{
        height: min(190px, 24dvh) !important;
        min-height: 130px !important;
        overflow-y: auto !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) [data-testid="stChatMessage"] {{
        padding: 7px !important;
        font-size: 0.90rem !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) [data-testid="stCaptionContainer"] {{
        font-size: 0.72rem !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) .stButton > button,
    div[data-testid="stPopoverBody"]:has(.ai-panel-title) .stFormSubmitButton > button {{
        min-height: 38px !important;
        padding-top: 0.35rem !important;
        padding-bottom: 0.35rem !important;
        font-size: 0.82rem !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) input {{
        min-height: 40px !important;
        font-size: 16px !important;
    }}
}}

@media (max-width: 390px) {{
    div[data-testid="stPopoverBody"]:has(.ai-panel-title) {{
        width: calc(100vw - 20px) !important;
        max-height: 66dvh !important;
        padding: 8px !important;
    }}

    div[data-testid="stPopoverBody"]:has(.ai-panel-title) .st-key-ai_messages {{
        height: min(160px, 21dvh) !important;
        min-height: 115px !important;
    }}
}}
</style>
        """
    )

    with st.container(key="global_ai_widget"):
        with st.popover(
            "Open AI Portfolio Copilot",
            help="Open AI Portfolio Copilot",
        ):
            header_left, header_right = st.columns([5, 1])

            with header_left:
                st.html('<div class="ai-panel-title">🤖 AI Portfolio Copilot</div>')
                st.caption(
                    "Ask about my work, projects, this page, or your dataset."
                )

            with header_right:
                if st.button(
                    "🗑",
                    key=f"ai_clear_{page_name}",
                    help="Clear conversation",
                    use_container_width=True,
                ):
                    st.session_state["ai_chat_history"] = []
                    st.rerun()

            st.caption(f"📍 Current page: **{page_name}**")

            quality_report = st.session_state.get("quality_report")
            if quality_report:
                score = quality_report.get("quality_score", 0)
                issue_count = quality_report.get(
                    "total_issues",
                    len(quality_report.get("issues", [])),
                )
                st.info(
                    f"📊 Dataset connected · Score **{score}/100** · "
                    f"Issues **{issue_count}**"
                )

            chat_box = st.container(height=300, key="ai_messages")

            with chat_box:
                if not st.session_state["ai_chat_history"]:
                    with st.chat_message("assistant", avatar=_assistant_avatar()):
                        st.markdown(
                            "👋 **Hi! I'm Maheswara's AI Copilot.**\n\n"
                            "Ask about my **skills and projects**, or get help "
                            "understanding your **uploaded data and quality recommendations**."
                        )

                for message in st.session_state["ai_chat_history"]:
                    role = message.get("role", "assistant")
                    avatar = _assistant_avatar() if role == "assistant" else "👤"
                    with st.chat_message(role, avatar=avatar):
                        st.markdown(message.get("content", ""))

            st.markdown("**Try asking:**")
            quick_question = None
            quick_items = _quick_questions(quality_report)
            quick_cols = st.columns(3)

            for index, ((label, prompt), column) in enumerate(
                zip(quick_items, quick_cols)
            ):
                with column:
                    if st.button(
                        label,
                        key=f"quick_{index}_{page_name}",
                        use_container_width=True,
                    ):
                        quick_question = prompt

            placeholder = (
                "Ask about this dataset..."
                if quality_report
                else "Ask a question about my portfolio..."
            )

            with st.form(
                key=f"ai_form_{page_name}",
                clear_on_submit=True,
            ):
                question = st.text_input(
                    "Question",
                    placeholder=placeholder,
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button(
                    "➤ Send",
                    type="primary",
                    use_container_width=True,
                )

            final_question = quick_question or question.strip()

            if (submitted or quick_question) and final_question:
                previous_chat = st.session_state["ai_chat_history"][-MAX_CHAT_MESSAGES:].copy()

                st.session_state["ai_chat_history"].append(
                    {"role": "user", "content": final_question}
                )
                _trim_chat_history()

                with chat_box:
                    with st.chat_message("user", avatar="👤"):
                        st.markdown(final_question)

                    with st.chat_message("assistant", avatar=_assistant_avatar()):
                        answer = st.write_stream(
                            ask_ai_stream(
                                question=final_question,
                                quality_report=quality_report,
                                industry=industry,
                                remediation_history=st.session_state.get(
                                    "remediation_history", []
                                ),
                                chat_history=previous_chat,
                                page_name=page_name,
                                page_context=page_context,
                            )
                        )

                if not isinstance(answer, str):
                    answer = "".join(map(str, answer))

                st.session_state["ai_chat_history"].append(
                    {"role": "assistant", "content": answer}
                )
                _trim_chat_history()

            st.caption("Tip: Ask about projects, skills, or uploaded data.")
