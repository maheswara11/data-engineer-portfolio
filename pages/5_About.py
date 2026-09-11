from __future__ import annotations

import streamlit as st

from src.ai_widget import render_ai_copilot
from src.page_contexts import PAGE_CONTEXTS
from src.ui import apply_theme, render_section_header, render_top_nav


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="About | Maheswara Reddy Varra",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("About")


# ============================================================
# PAGE-SPECIFIC STYLES
# ============================================================

st.html(
    """
    <style>
    .about-intro {
        max-width: 1050px;
        color: #64748b;
        font-size: 1.05rem;
        line-height: 1.75;
        margin-top: 0.35rem;
    }

    .about-card {
        min-height: 165px;
        padding: 20px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .about-card-title {
        color: #14264d;
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 9px;
    }

    .about-card-text {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.62;
    }

    .profile-card {
        min-height: 135px;
        padding: 18px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .profile-label {
        color: #718096;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 5px;
    }

    .profile-value {
        color: #14264d;
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: 5px;
    }

    .profile-caption {
        color: #64748b;
        font-size: 0.85rem;
        line-height: 1.45;
    }

    .skills-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 8px 0 5px 0;
    }

    .skill {
        display: inline-block;
        padding: 7px 11px;
        border-radius: 999px;
        background: #eef4ff;
        border: 1px solid #d8e5ff;
        color: #24457a;
        font-size: 0.82rem;
        font-weight: 650;
        line-height: 1.2;
    }

    .education-box {
        padding: 22px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .education-title {
        color: #14264d;
        font-size: 1.05rem;
        font-weight: 750;
        margin-bottom: 6px;
    }

    .education-text {
        color: #64748b;
        font-size: 0.92rem;
        line-height: 1.6;
    }
    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

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
    "Terraform": "🧱",
    "Docker": "🐳",
    "GitHub Actions": "🔗",
    "CI/CD": "♾️",
    "PostgreSQL": "🐘",
    "MySQL": "🐬",
    "Data Quality": "✅",
    "Data Modeling": "📐",
    "Lakehouse": "🏞️",
    "Batch Processing": "📦",
    "Streaming": "📡",
    "ETL / ELT": "🔁",
    "GenAI": "🧠",
    "RAG": "📄",
}


def render_tags(tags: list[str]) -> None:
    html = ""

    for tag in tags:
        icon = SKILL_ICONS.get(tag, "🔹")
        html += (
            f'<span class="skill">'
            f'{icon} {tag}'
            f'</span>'
        )

    st.html(
        f'<div class="skills-wrap">{html}</div>'
    )


def profile_card(
    icon: str,
    label: str,
    value: str,
    caption: str,
) -> None:
    st.html(
        f"""
        <div class="profile-card">
            <div style="font-size:1.4rem;margin-bottom:7px">
                {icon}
            </div>
            <div class="profile-label">
                {label}
            </div>
            <div class="profile-value">
                {value}
            </div>
            <div class="profile-caption">
                {caption}
            </div>
        </div>
        """
    )


def about_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <div class="about-card">
            <div class="about-card-title">
                {icon} {title}
            </div>
            <div class="about-card-text">
                {description}
            </div>
        </div>
        """
    )


# ============================================================
# HERO
# ============================================================

st.html(
    '<div class="hello-pill">👨‍💻 About Me</div>'
)

st.html(
    '<h1 class="hero-title" style="font-size:3.25rem">'
    'Building Reliable Data Systems'
    '</h1>'
)

st.html(
    """
    <div class="about-intro">
        I am a Data Engineer focused on building reliable data pipelines,
        cloud data platforms, lakehouse architectures, data-quality systems,
        and AI-assisted engineering workflows. I enjoy solving practical
        data problems by combining strong engineering fundamentals with
        modern cloud and AI technologies.
    </div>
    """
)

st.write("")


# ============================================================
# PROFESSIONAL SNAPSHOT
# ============================================================

render_section_header(
    "Professional Snapshot",
    "⚡",
)

p1, p2, p3, p4 = st.columns(4)

with p1:
    profile_card(
        "🎯",
        "Target Role",
        "Data Engineer",
        "Focused on scalable, reliable, production-style data systems.",
    )

with p2:
    profile_card(
        "💻",
        "Core Languages",
        "Python · SQL",
        "Data processing, transformation, validation, and automation.",
    )

with p3:
    profile_card(
        "☁️",
        "Cloud Platforms",
        "AWS · Azure · GCP",
        "Cloud-native and multi-cloud data engineering.",
    )

with p4:
    profile_card(
        "🏗️",
        "Modern Data Stack",
        "Databricks · Snowflake · dbt",
        "Lakehouse, warehouse, and transformation workflows.",
    )


# ============================================================
# BACKGROUND
# ============================================================

render_section_header(
    "Background",
    "🎓",
)

with st.container(border=True):

    st.markdown(
        "### Maheswara Reddy Varra"
    )

    st.write(
        "I completed an M.S. in Information Systems at Central Michigan University. "
        "My academic and project work strengthened my understanding of databases, "
        "cloud computing, data visualization, system design, business intelligence, "
        "and AI while I continued building hands-on Data Engineering projects."
    )

    st.write(
        "My current work focuses on Python, SQL, PySpark, Databricks, cloud platforms, "
        "orchestration, data quality, modern data architecture, Infrastructure as Code, "
        "and AI-assisted Data Engineering."
    )


# ============================================================
# ENGINEERING MINDSET
# ============================================================

render_section_header(
    "How I Think About Data Engineering",
    "🧠",
)

a1, a2, a3, a4 = st.columns(4)

with a1:
    about_card(
        "✅",
        "Reliability First",
        "Pipelines should be observable, testable, recoverable, and safe "
        "when schemas, volumes, or upstream data change.",
    )

with a2:
    about_card(
        "📈",
        "Design for Scale",
        "Use distributed processing, incremental patterns, partitioning, "
        "and cloud-native architecture where they provide real value.",
    )

with a3:
    about_card(
        "🔄",
        "Automate Repetitive Work",
        "Use orchestration, CI/CD, Infrastructure as Code, and reusable "
        "transformation patterns to reduce manual operational work.",
    )

with a4:
    about_card(
        "🛡️",
        "Keep Automation Safe",
        "Use deterministic validation and human approval for changes that "
        "can affect production data or downstream systems.",
    )


# ============================================================
# CORE DATA ENGINEERING FOCUS
# ============================================================

render_section_header(
    "Core Data Engineering Focus",
    "🎯",
)

render_tags(
    [
        "Python",
        "SQL",
        "PySpark",
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
        "PostgreSQL",
        "MySQL",
        "Terraform",
        "Docker",
        "GitHub Actions",
        "CI/CD",
        "Data Modeling",
        "Data Quality",
        "Batch Processing",
        "Streaming",
        "ETL / ELT",
        "Lakehouse",
        "GenAI",
        "RAG",
    ]
)


# ============================================================
# ARCHITECTURE INTERESTS
# ============================================================

render_section_header(
    "Architecture & Engineering Interests",
    "🏛️",
)

i1, i2, i3, i4 = st.columns(4)

with i1:
    about_card(
        "📦",
        "Batch Data Systems",
        "Incremental ingestion, ETL/ELT, PySpark transformations, "
        "partitioning, watermarking, backfills, and scheduled orchestration.",
    )

with i2:
    about_card(
        "📡",
        "Streaming Systems",
        "Kafka-based event ingestion, real-time processing, continuously "
        "updated datasets, and event-driven data flows.",
    )

with i3:
    about_card(
        "🏞️",
        "Lakehouse Platforms",
        "Medallion architecture, Delta Lake, Databricks, governed storage, "
        "and analytics-ready Bronze, Silver, and Gold datasets.",
    )

with i4:
    about_card(
        "🤖",
        "AI + Data Reliability",
        "RAG, local LLMs, grounded recommendations, data-quality diagnostics, "
        "and AI-assisted engineering workflows.",
    )


# ============================================================
# WHAT I BRING
# ============================================================

render_section_header(
    "What I Bring",
    "🚀",
)

w1, w2, w3 = st.columns(3)

with w1:
    about_card(
        "⚙️",
        "End-to-End Thinking",
        "I look at the full data lifecycle: ingestion, transformation, "
        "validation, storage, orchestration, serving, monitoring, and recovery.",
    )

with w2:
    about_card(
        "☁️",
        "Cloud + Engineering",
        "I combine cloud services with Spark, Databricks, Snowflake, Airflow, "
        "Terraform, Docker, and CI/CD to build maintainable data systems.",
    )

with w3:
    about_card(
        "🧠",
        "Continuous Learning",
        "I actively build projects across modern Data Engineering, cloud, "
        "data reliability, streaming, and Generative AI to strengthen practical skills.",
    )


# ============================================================
# EXPLORE
# ============================================================

render_section_header(
    "Explore My Work",
    "💼",
)

x1, x2, x3 = st.columns(3)

with x1:

    with st.container(border=True):

        st.page_link(
            "pages/1_Projects.py",
            label="🚀 View Projects",
            use_container_width=True,
        )

        st.caption(
            "See my Data Engineering projects, architectures, and implementation details."
        )

with x2:

    with st.container(border=True):

        st.page_link(
            "pages/3_Resume.py",
            label="📄 View Resume",
            use_container_width=True,
        )

        st.caption(
            "Review my technical stack, experience, and downloadable resume."
        )

with x3:

    with st.container(border=True):

        st.page_link(
            "pages/4_Contact.py",
            label="✉️ Contact Me",
            use_container_width=True,
        )

        st.caption(
            "Connect with me for Data Engineering, Cloud, and related opportunities."
        )


# ============================================================
# GLOBAL AI COPILOT
# ============================================================

render_ai_copilot(
    page_name="About",
    page_context=PAGE_CONTEXTS["About"],
)
