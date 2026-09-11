from __future__ import annotations

from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_DIRECTORY = PROJECT_ROOT / "assets" / "resumes"


NAV_ITEMS = [
    ("Home", "app.py"),
    ("Projects", "pages/1_Projects.py"),
    ("Resume", "pages/3_Resume.py"),
    ("About", "pages/5_About.py"),
    ("Contact", "pages/4_Contact.py"),
]


def _first_resume() -> Path | None:
    RESUME_DIRECTORY.mkdir(parents=True, exist_ok=True)
    files = sorted(RESUME_DIRECTORY.glob("*.pdf"))
    return files[0] if files else None


@st.cache_data(show_spinner=False)
def _read_resume_bytes(path_text: str, modified_ns: int) -> bytes:
    """Cache resume bytes; the mtime argument invalidates stale cached data."""
    del modified_ns
    return Path(path_text).read_bytes()


def apply_theme() -> None:
    """Apply the shared light/dark portfolio theme."""

    dark = bool(st.session_state.get("portfolio_dark_mode", False))

    if dark:
        background = "#07111f"
        surface = "rgba(15, 27, 45, 0.92)"
        surface_soft = "rgba(18, 34, 55, 0.78)"
        text = "#f5f8ff"
        muted = "#9db0cf"
        border = "rgba(126, 156, 205, 0.18)"
        header = "rgba(7, 17, 31, 0.92)"
        chip = "rgba(62, 99, 160, 0.23)"
        chip_text = "#dce8ff"
        input_bg = "#0d1b2e"
    else:
        background = "#f7fbff"
        surface = "rgba(255, 255, 255, 0.94)"
        surface_soft = "rgba(255, 255, 255, 0.80)"
        text = "#0d2148"
        muted = "#5f7398"
        border = "rgba(84, 111, 165, 0.14)"
        header = "rgba(248, 251, 255, 0.92)"
        chip = "#edf3ff"
        chip_text = "#173b80"
        input_bg = "#ffffff"

    st.html(
        f"""
        <style>
        :root {{
            --portfolio-bg: {background};
            --portfolio-surface: {surface};
            --portfolio-surface-soft: {surface_soft};
            --portfolio-text: {text};
            --portfolio-muted: {muted};
            --portfolio-border: {border};
            --portfolio-header: {header};
            --portfolio-chip: {chip};
            --portfolio-chip-text: {chip_text};
            --portfolio-input: {input_bg};
            --portfolio-blue: #1768f2;
            --portfolio-blue-2: #285cff;
        }}

        html, body, [class*="css"] {{
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
        }}

        .stApp {{
            background:
                radial-gradient(circle at 93% 10%, rgba(86, 118, 255, 0.12), transparent 25%),
                radial-gradient(circle at 4% 92%, rgba(72, 155, 255, 0.08), transparent 28%),
                var(--portfolio-bg);
            color: var(--portfolio-text);
        }}

        /* Remove Streamlit's default navigation chrome. */
        [data-testid="stSidebar"] {{
            display: none !important;
        }}

        [data-testid="collapsedControl"] {{
            display: none !important;
        }}

        header[data-testid="stHeader"] {{
            height: 0 !important;
            min-height: 0 !important;
            background: transparent !important;
        }}

        .block-container {{
            max-width: 1500px;
            padding-top: 0.65rem;
            padding-bottom: 7rem;
            padding-left: 2.2rem;
            padding-right: 2.2rem;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--portfolio-text) !important;
            letter-spacing: -0.02em;
        }}

        h1 {{
            font-weight: 850 !important;
        }}

        p, label, div, span {{
            color: inherit;
        }}

        .portfolio-muted {{
            color: var(--portfolio-muted);
        }}

        /* Top navigation */
        .st-key-top_nav {{
            position: sticky;
            top: 0;
            z-index: 9990;
            background: var(--portfolio-header);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--portfolio-border);
            border-radius: 18px;
            box-shadow: 0 10px 32px rgba(31, 64, 128, 0.07);
            padding: 0.36rem 0.65rem;
            margin-bottom: 1.15rem;
        }}

        .brand-logo {{
            width: 48px;
            height: 48px;
            border-radius: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 900;
            font-size: 1.25rem;
            color: var(--portfolio-text);
            background: var(--portfolio-surface);
            border: 1px solid var(--portfolio-border);
            box-shadow: 0 6px 16px rgba(36, 74, 150, 0.12);
            margin-top: 1px;
        }}

        .nav-active {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 44px;
            border-radius: 12px;
            background: var(--portfolio-chip);
            color: var(--portfolio-chip-text) !important;
            font-weight: 750;
            padding: 0 0.55rem;
        }}

        .st-key-top_nav [data-testid="stPageLink"] a {{
            min-height: 44px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 650;
            color: var(--portfolio-text) !important;
            text-decoration: none !important;
            border: 1px solid transparent;
            transition: 0.2s ease;
        }}

        .st-key-top_nav [data-testid="stPageLink"] a:hover {{
            background: var(--portfolio-chip);
            border-color: var(--portfolio-border);
            transform: translateY(-1px);
        }}

        .st-key-top_nav .stDownloadButton > button {{
            min-height: 44px !important;
            background: linear-gradient(135deg, #1768f2, #1557d4) !important;
            color: white !important;
            border: none !important;
            font-weight: 750 !important;
            border-radius: 12px !important;
        }}

        .st-key-top_nav [data-testid="stToggle"] {{
            padding-top: 0.2rem;
        }}

        /* Hero */
        .hello-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.38rem 0.75rem;
            border: 1px solid var(--portfolio-border);
            border-radius: 999px;
            color: var(--portfolio-chip-text) !important;
            background: var(--portfolio-chip);
            font-weight: 650;
            margin-bottom: 0.45rem;
        }}

        .hero-title {{
            font-size: clamp(2.4rem, 4.2vw, 4.25rem);
            line-height: 1.01;
            margin: 0;
            color: var(--portfolio-text);
            font-weight: 900;
            letter-spacing: -0.045em;
        }}

        .hero-subtitle {{
            font-size: clamp(1.05rem, 1.55vw, 1.35rem);
            color: var(--portfolio-muted);
            font-weight: 700;
            margin-top: 0.45rem;
            margin-bottom: 0.55rem;
        }}

        .hero-description {{
            font-size: 1.05rem;
            color: var(--portfolio-muted);
            max-width: 820px;
            line-height: 1.55;
        }}

        .hand-note {{
            color: #1e5eff !important;
            font-family: "Comic Sans MS", "Segoe Print", cursive;
            font-style: italic;
            font-size: clamp(1.0rem, 1.7vw, 1.55rem);
            transform: rotate(-5deg);
            display: inline-block;
            margin-top: 2.2rem;
        }}

        /* Cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            border-radius: 18px !important;
            border: 1px solid var(--portfolio-border) !important;
            background: var(--portfolio-surface) !important;
            box-shadow: 0 9px 26px rgba(37, 73, 135, 0.07);
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"]:hover {{
            transform: translateY(-3px);
            box-shadow: 0 16px 34px rgba(37, 73, 135, 0.12);
        }}

        .mini-card {{
            min-height: 106px;
            border-radius: 18px;
            background: var(--portfolio-surface);
            border: 1px solid var(--portfolio-border);
            box-shadow: 0 9px 26px rgba(37, 73, 135, 0.07);
            padding: 1rem 1.05rem;
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .mini-icon {{
            width: 46px;
            height: 46px;
            flex: 0 0 46px;
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.65rem;
            background: var(--portfolio-chip);
            border: 1px solid var(--portfolio-border);
        }}

        .mini-label {{
            font-size: 0.82rem;
            color: var(--portfolio-muted);
            font-weight: 650;
        }}

        .mini-value {{
            margin-top: 0.12rem;
            font-size: 1.06rem;
            color: var(--portfolio-text);
            font-weight: 800;
        }}

        .mini-caption {{
            margin-top: 0.12rem;
            font-size: 0.76rem;
            color: var(--portfolio-muted);
        }}

        .section-row {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 0.65rem;
            margin-bottom: 0.55rem;
        }}

        .section-title {{
            font-size: 1.45rem;
            font-weight: 850;
            color: var(--portfolio-text);
        }}

        .section-link {{
            font-size: 0.86rem;
            color: #175fe8 !important;
            font-weight: 700;
        }}

        /* Skills */
        .skills-wrap {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 0.55rem;
        }}

        .skill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.47rem 0.82rem;
            border-radius: 999px;
            background: var(--portfolio-chip);
            color: var(--portfolio-chip-text) !important;
            border: 1px solid var(--portfolio-border);
            font-size: 0.86rem;
            font-weight: 650;
            box-shadow: 0 4px 12px rgba(45, 79, 140, 0.04);
        }}

        /* Metrics */
        [data-testid="stMetric"] {{
            border-radius: 16px;
            padding: 0.95rem;
            background: var(--portfolio-surface);
            border: 1px solid var(--portfolio-border);
            box-shadow: 0 8px 24px rgba(37, 73, 135, 0.06);
        }}

        /* Buttons */
        .stButton > button,
        .stDownloadButton > button,
        [data-testid="stLinkButton"] a,
        [data-testid="stPageLink"] a {{
            border-radius: 12px !important;
            transition: transform 0.18s ease, box-shadow 0.18s ease;
        }}

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        [data-testid="stLinkButton"] a:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(44, 89, 190, 0.15);
        }}

        /* Forms / inputs */
        input, textarea {{
            background: var(--portfolio-input) !important;
            color: var(--portfolio-text) !important;
        }}

        [data-testid="stDataFrame"] {{
            border-radius: 15px;
            overflow: hidden;
        }}

        [data-testid="stExpander"] {{
            border-radius: 15px !important;
            overflow: hidden;
            border-color: var(--portfolio-border) !important;
        }}

        /* A soft bottom decorative wave, similar to the reference. */
        .portfolio-wave {{
            position: fixed;
            left: 0;
            right: 0;
            bottom: 0;
            height: 160px;
            pointer-events: none;
            z-index: 0;
            opacity: 0.48;
            background:
                radial-gradient(80% 90% at 12% 100%, rgba(85, 151, 255, 0.15), transparent 60%),
                radial-gradient(60% 100% at 78% 110%, rgba(104, 99, 255, 0.13), transparent 65%);
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            .st-key-top_nav {{
                position: static;
            }}

            .brand-logo {{
                width: 42px;
                height: 42px;
            }}
        }}
        </style>
        <div class="portfolio-wave"></div>
        """
    )


def render_top_nav(active_page: str) -> None:
    """Render the shared top navigation used on every page."""

    with st.container(key="top_nav"):
        cols = st.columns([0.65, 1, 1, 1, 1, 1, 0.65, 1.75], gap="small")

        with cols[0]:
            st.html('<div class="brand-logo">MR</div>')

        for idx, (label, path) in enumerate(NAV_ITEMS, start=1):
            with cols[idx]:
                if label == active_page:
                    st.html(f'<div class="nav-active">{label}</div>')
                else:
                    st.page_link(path, label=label, use_container_width=True)

        with cols[6]:
            st.toggle(
                "Dark",
                key="portfolio_dark_mode",
                label_visibility="collapsed",
                help="Toggle light / dark appearance",
            )

        with cols[7]:
            resume = _first_resume()
            if resume is not None:
                st.download_button(
                    "⇩  Download Resume",
                    data=_read_resume_bytes(
                        str(resume),
                        resume.stat().st_mtime_ns,
                    ),
                    file_name=resume.name,
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"nav_resume_{active_page}",
                )
            else:
                st.page_link(
                    "pages/3_Resume.py",
                    label="⇩  View Resume",
                    use_container_width=True,
                )


def render_section_header(title: str, icon: str = "", trailing: str = "") -> None:
    icon_html = f"{icon} " if icon else ""
    trailing_html = f'<span class="section-link">{trailing}</span>' if trailing else ""
    st.html(
        f"""
        <div class="section-row">
            <div class="section-title">{icon_html}{title}</div>
            {trailing_html}
        </div>
        """
    )
