from __future__ import annotations

import streamlit as st

from src.ai_widget import render_ai_copilot
from src.page_contexts import PAGE_CONTEXTS
from src.ui import apply_theme, render_section_header, render_top_nav


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Maheswara Reddy Varra | Data Engineer",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("Home")


# ============================================================
# PAGE-SPECIFIC STYLING
# ============================================================

st.html(
    """
    <style>
    .home-intro {
        max-width: 1000px;
        color: var(--portfolio-muted);
        font-size: 1.05rem;
        line-height: 1.75;
        margin-top: 0.35rem;
    }

    .profile-card {
        min-height: 142px;
        padding: 20px;
        border: 1px solid var(--portfolio-border);
        border-radius: 16px;
        background: var(--portfolio-surface);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .profile-icon {
        font-size: 1.55rem;
        margin-bottom: 8px;
    }

    .profile-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--portfolio-muted);
        font-weight: 700;
        margin-bottom: 4px;
    }

    .profile-value {
        color: var(--portfolio-text);
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: 5px;
    }

    .profile-caption {
        color: var(--portfolio-muted);
        font-size: 0.86rem;
        line-height: 1.45;
    }

    .skills-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 6px 0;
    }

    .skill {
        display: inline-block;
        padding: 7px 11px;
        border-radius: 999px;
        background: var(--portfolio-chip);
        border: 1px solid var(--portfolio-border);
        color: var(--portfolio-chip-text);
        font-size: 0.82rem;
        font-weight: 650;
        line-height: 1.2;
    }

    .capability-card {
        min-height: 165px;
        padding: 20px;
        border: 1px solid var(--portfolio-border);
        border-radius: 16px;
        background: var(--portfolio-surface);
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .capability-title {
        color: var(--portfolio-text);
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 9px;
    }

    .capability-text {
        color: var(--portfolio-muted);
        font-size: 0.9rem;
        line-height: 1.62;
    }

    .project-kicker {
        color: var(--portfolio-muted);
        font-size: 0.82rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 2px;
    }

    .home-cta {
        color: var(--portfolio-muted);
        font-size: 0.9rem;
        line-height: 1.55;
    }
    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

def profile_card(
    icon: str,
    label: str,
    value: str,
    caption: str,
) -> None:
    st.html(
        f"""
        <div class="profile-card">
            <div class="profile-icon">{icon}</div>
            <div class="profile-label">{label}</div>
            <div class="profile-value">{value}</div>
            <div class="profile-caption">{caption}</div>
        </div>
        """
    )


def capability_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <div class="capability-card">
            <div class="capability-title">
                {icon} {title}
            </div>
            <div class="capability-text">
                {description}
            </div>
        </div>
        """
    )


SKILL_ICONS = {
    "Python": "🐍",
    "SQL": "🗄️",
    "PySpark": "⚡",
    "Apache Spark": "⚡",
    "Databricks": "🔺",
    "Snowflake": "❄️",
    "dbt": "🧱",
    "Apache Airflow": "🌪️",
    "Apache Kafka": "📡",
    "Confluent Kafka": "🔄",
    "AWS": "☁️",
    "Azure": "🔷",
    "GCP": "🌈",
    "Delta Lake": "🏞️",
    "Amazon S3": "🪣",
    "AWS Glue": "🧩",
    "Athena": "🔎",
    "Lambda": "λ",
    "Terraform": "🧱",
    "Docker": "🐳",
    "GitHub Actions": "🔗",
    "CI/CD": "♾️",
    "PostgreSQL": "🐘",
    "MySQL": "🐬",
    "Data Modeling": "📐",
    "SCD Type 2": "🕒",
    "Medallion Architecture": "🥉",
    "Data Quality": "✅",
    "RAG": "📄",
    "GenAI": "🧠",
    "Pandas": "🐼",
    "Streamlit": "🎈",
    "Ollama": "🦙",
    "Human-in-the-Loop": "👤",
}


def render_tags(tags: list[str]) -> None:
    tag_html_parts = []

    for tag in tags:
        # Keep tags that already include an icon unchanged.
        first_char = tag.strip()[:1]

        if first_char and not first_char.isalnum():
            display_tag = tag
        else:
            icon = SKILL_ICONS.get(tag, "🔹")
            display_tag = f"{icon} {tag}"

        tag_html_parts.append(
            f'<span class="skill">{display_tag}</span>'
        )

    st.html(
        '<div class="skills-wrap">'
        + "".join(tag_html_parts)
        + "</div>"
    )


# ============================================================
# HERO
# ============================================================

hero_left, hero_note = st.columns(
    [3.15, 1.0],
    vertical_alignment="top",
)

with hero_left:

    st.html(
        '<div class="hello-pill">👋 Hello, I&apos;m</div>'
    )

    st.html(
        '<h1 class="hero-title">Maheswara Reddy Varra</h1>'
    )

    st.html(
        """
        <div class="hero-subtitle">
            Data Engineer | Python | SQL | PySpark | Databricks |
            Snowflake | AWS · Azure · GCP
        </div>
        """
    )

    st.html(
        """
        <div class="home-intro">
            I build reliable batch and streaming data pipelines, cloud lakehouse
            platforms, data-quality systems, and AI-assisted data engineering
            solutions. My focus is turning raw data into scalable, governed,
            analytics-ready data products.
        </div>
        """
    )

with hero_note:

    st.html(
        """
        <div class="hand-note">
            Building reliable<br>
            data systems ↗
        </div>
        """
    )

st.write("")


# ============================================================
# DATA ENGINEERING PROFILE
# ============================================================

render_section_header(
    "Data Engineering Profile",
    "⚡",
)

p1, p2, p3, p4 = st.columns(4)

with p1:
    profile_card(
        "🎯",
        "Primary Focus",
        "Data Engineering",
        "Scalable pipelines, reliability, modeling, and analytics-ready data.",
    )

with p2:
    profile_card(
        "☁️",
        "Cloud Platforms",
        "AWS · Azure · GCP",
        "Cloud-native data engineering and multi-cloud architecture.",
    )

with p3:
    profile_card(
        "⚡",
        "Processing",
        "PySpark · Spark",
        "Distributed batch processing and large-scale transformation.",
    )

with p4:
    profile_card(
        "🏗️",
        "Modern Data Stack",
        "Databricks · Snowflake · dbt",
        "Lakehouse, warehouse, transformation, and analytics workflows.",
    )


# ============================================================
# CORE DATA ENGINEERING STACK
# ============================================================

render_section_header(
    "Core Data Engineering Stack",
    "🛠️",
)

render_tags(
    [
        "🐍 Python",
        "🗄 SQL",
        "⚡ PySpark",
        "Apache Spark",
        "Databricks",
        "Snowflake",
        "dbt",
        "Apache Airflow",
        "Apache Kafka",
        "Confluent Kafka",
        "AWS",
        "Azure",
        "GCP",
        "Delta Lake",
        "Amazon S3",
        "AWS Glue",
        "Athena",
        "Lambda",
        "Terraform",
        "Docker",
        "GitHub Actions",
        "CI/CD",
        "PostgreSQL",
        "MySQL",
        "Data Modeling",
        "SCD Type 2",
        "Medallion Architecture",
        "Data Quality",
        "RAG",
        "GenAI",
    ]
)


# ============================================================
# DATA ENGINEERING CAPABILITIES
# ============================================================

render_section_header(
    "Data Engineering Capabilities",
    "🏛️",
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    capability_card(
        "📦",
        "Batch & ETL / ELT",
        "Scheduled ingestion, incremental loading, watermarking, Spark/PySpark "
        "transformations, dbt models, partitioning, and backfills.",
    )

with c2:
    capability_card(
        "📡",
        "Streaming & Event-Driven",
        "Kafka-based event ingestion, streaming pipelines, event-driven workflows, "
        "and serverless processing with cloud services.",
    )

with c3:
    capability_card(
        "🏞️",
        "Lakehouse & Warehousing",
        "Databricks, Delta Lake, Snowflake, Medallion layers, catalogs, "
        "analytics-ready datasets, and scalable storage patterns.",
    )

with c4:
    capability_card(
        "✅",
        "Data Quality & Reliability",
        "Schema drift, null and duplicate detection, deterministic validation, "
        "monitoring, retries, alerts, and human-approved remediation.",
    )


c5, c6, c7, c8 = st.columns(4)

with c5:
    capability_card(
        "📐",
        "Data Modeling",
        "Star schema, dimensional modeling, SCD Type 2, normalization, "
        "OLTP / OLAP concepts, and schema design.",
    )

with c6:
    capability_card(
        "⚙️",
        "DevOps & Infrastructure",
        "Terraform, Docker, GitHub Actions, CI/CD, Infrastructure as Code, "
        "and cloud deployment automation.",
    )

with c7:
    capability_card(
        "🔐",
        "Governance & Observability",
        "IAM, Lake Formation, CloudWatch, access control, monitoring, "
        "data lineage concepts, and operational visibility.",
    )

with c8:
    capability_card(
        "🤖",
        "AI for Data Engineering",
        "RAG, local LLM integration, AI-assisted diagnostics, grounded "
        "recommendations, and intelligent data-quality workflows.",
    )


# ============================================================
# FEATURED PROJECT
# ============================================================

render_section_header(
    "Featured Project",
    "⭐",
    "View All Projects →",
)

with st.container(border=True):

    project_icon, project_body, project_arrow = st.columns(
        [0.65, 4.9, 0.45],
        vertical_alignment="center",
    )

    with project_icon:

        st.html(
            '<div style="font-size:58px;text-align:center;padding:8px 0">🛡️</div>'
        )

    with project_body:

        st.html(
            '<div class="project-kicker">Data Quality + GenAI</div>'
        )

        st.markdown(
            "### AI Data Quality Copilot"
        )

        st.write(
            "A non-destructive data quality platform that analyzes CSV and JSON "
            "datasets, identifies exact affected records, calculates quality scores, "
            "supports human-approved remediation, and uses a grounded local AI "
            "copilot to explain issues and recommendations."
        )

        render_tags(
            [
                "Python",
                "Pandas",
                "Streamlit",
                "Data Quality",
                "Ollama",
                "GenAI",
                "Human-in-the-Loop",
            ]
        )

        f1, f2 = st.columns(2)

        with f1:
            st.page_link(
                "pages/2_Data_Quality_Copilot.py",
                label="🚀 Try Live Data Quality Copilot",
                use_container_width=True,
            )

        with f2:
            st.page_link(
                "pages/1_Projects.py",
                label="📁 View Project Details",
                use_container_width=True,
            )

    with project_arrow:

        st.page_link(
            "pages/1_Projects.py",
            label="›",
        )


# ============================================================
# WHAT I BUILD
# ============================================================

render_section_header(
    "What I Build",
    "🧊",
)

b1, b2, b3 = st.columns(3)

with b1:

    with st.container(border=True):

        st.markdown(
            "### ⚙️ Data Platforms"
        )

        st.caption(
            "Batch and streaming pipelines, ETL/ELT, PySpark processing, "
            "orchestration, lakehouse systems, and data modeling."
        )

with b2:

    with st.container(border=True):

        st.markdown(
            "### ☁️ Cloud Data Systems"
        )

        st.caption(
            "AWS, Azure, and GCP data solutions using scalable cloud services, "
            "Databricks, Snowflake, Terraform, and CI/CD."
        )

with b3:

    with st.container(border=True):

        st.markdown(
            "### 🤖 Reliable Data + AI"
        )

        st.caption(
            "Data quality, observability, RAG, GenAI, and AI-assisted diagnostics "
            "with deterministic systems and human approval."
        )


# ============================================================
# PORTFOLIO HIGHLIGHTS
# ============================================================

render_section_header(
    "Portfolio Highlights",
    "🚀",
)

h1, h2, h3, h4 = st.columns(4)

with h1:
    profile_card(
        "🏞️",
        "Architecture",
        "Lakehouse + Medallion",
        "Bronze, Silver, and Gold data layers with governed processing.",
    )

with h2:
    profile_card(
        "📡",
        "Real-Time",
        "Kafka + Streaming",
        "Event ingestion and continuously updated downstream data.",
    )

with h3:
    profile_card(
        "λ",
        "Serverless",
        "S3 + Lambda",
        "Event-triggered processing with managed cloud services.",
    )

with h4:
    profile_card(
        "🧠",
        "AI + Reliability",
        "RAG + Data Quality",
        "Grounded diagnostics, recommendations, and safe remediation.",
    )


# ============================================================
# EXPLORE PORTFOLIO
# ============================================================

render_section_header(
    "Explore My Portfolio",
    "💼",
)

n1, n2, n3 = st.columns(3)

with n1:

    with st.container(border=True):

        st.page_link(
            "pages/1_Projects.py",
            label="📁 View Projects",
            use_container_width=True,
        )

        st.caption(
            "Explore engineering projects, architectures, and implementation details."
        )

with n2:

    with st.container(border=True):

        st.page_link(
            "pages/3_Resume.py",
            label="📄 View Resume",
            use_container_width=True,
        )

        st.caption(
            "Review my Data Engineering profile, technical stack, and resume."
        )

with n3:

    with st.container(border=True):

        st.page_link(
            "pages/4_Contact.py",
            label="✉️ Contact Me",
            use_container_width=True,
        )

        st.caption(
            "Connect for Data Engineering, Cloud, and related opportunities."
        )


# ============================================================
# GLOBAL AI COPILOT
# ============================================================

render_ai_copilot(
    page_name="Home",
    page_context=PAGE_CONTEXTS["Home"],
)
