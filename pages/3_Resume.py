from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ai_widget import render_ai_copilot
from src.page_contexts import PAGE_CONTEXTS
from src.ui import apply_theme, render_section_header, render_top_nav

try:
    import fitz
except ImportError:
    fitz = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Resume | Maheswara Reddy Varra",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("Resume")


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESUME_DIRECTORY = PROJECT_ROOT / "assets" / "resumes"


# ============================================================
# PAGE-SPECIFIC STYLING
# ============================================================

st.html(
    """
    <style>

    .resume-intro {
        font-size: 1.05rem;
        color: #64748b;
        line-height: 1.7;
        max-width: 1050px;
        margin-bottom: 1rem;
    }

    .skill-card {
        min-height: 145px;
        padding: 1.35rem;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 0.8rem;
    }

    .skill-card-title {
        font-size: 1rem;
        font-weight: 700;
        color: #14264d;
        margin-bottom: 0.65rem;
    }

    .skill-card-text {
        font-size: 0.92rem;
        color: #52627d;
        line-height: 1.65;
    }

    .strength-card {
        padding: 1.35rem;
        border: 1px solid rgba(148, 163, 184, 0.25);
        border-radius: 16px;
        min-height: 155px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 14px;
    }

    .strength-title {
        font-size: 1rem;
        font-weight: 700;
        color: #14264d;
        margin-bottom: 0.55rem;
    }

    .strength-text {
        font-size: 0.9rem;
        line-height: 1.6;
        color: #64748b;
    }

    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

def show_pdf_viewer(
    pdf_bytes: bytes,
    key_prefix: str,
) -> None:

    if fitz is None:
        st.info(
            "PDF preview requires PyMuPDF. "
            "The resume can still be downloaded."
        )
        return

    try:
        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf",
        )
    except Exception as exc:
        st.error(
            f"Could not open this PDF: {exc}"
        )
        return

    try:
        total_pages = len(document)

        if total_pages == 0:
            st.warning(
                "This PDF does not contain any pages."
            )
            return

        page_key = f"{key_prefix}_page"

        st.session_state.setdefault(
            page_key,
            0,
        )

        current_page = min(
            max(
                int(
                    st.session_state[
                        page_key
                    ]
                ),
                0,
            ),
            total_pages - 1,
        )

        st.session_state[
            page_key
        ] = current_page

        c1, c2, c3 = st.columns(
            [1, 2, 1]
        )

        with c1:

            if st.button(
                "⬅ Previous",
                key=f"{key_prefix}_previous",
                disabled=current_page == 0,
                use_container_width=True,
            ):
                st.session_state[
                    page_key
                ] -= 1

                st.rerun()

        with c2:

            zoom = st.slider(
                "🔍 Zoom",
                min_value=70,
                max_value=170,
                value=100,
                step=10,
                key=f"{key_prefix}_zoom",
            )

        with c3:

            if st.button(
                "Next ➡",
                key=f"{key_prefix}_next",
                disabled=(
                    current_page
                    == total_pages - 1
                ),
                use_container_width=True,
            ):
                st.session_state[
                    page_key
                ] += 1

                st.rerun()

        current_page = (
            st.session_state[
                page_key
            ]
        )

        st.caption(
            f"Page {current_page + 1} "
            f"of {total_pages}"
        )

        page = document.load_page(
            current_page
        )

        matrix = fitz.Matrix(
            zoom / 100 * 1.5,
            zoom / 100 * 1.5,
        )

        pixmap = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        st.image(
            pixmap.tobytes("png"),
            use_container_width=True,
        )

    finally:
        document.close()


def skill_card(
    icon: str,
    title: str,
    skills: str,
) -> None:
    """Render a clean technical-skill card."""
    st.html(
        f"""
        <div class="skill-card">
            <div class="skill-card-title">
                {icon} {title}
            </div>
            <div class="skill-card-text">
                {skills}
            </div>
        </div>
        """
    )


def strength_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    """Render a clean engineering-strength card."""
    st.html(
        f"""
        <div class="strength-card">
            <div class="strength-title">
                {icon} {title}
            </div>
            <div class="strength-text">
                {description}
            </div>
        </div>
        """
    )

# ============================================================
# HERO
# ============================================================

st.markdown(
    '<div class="hello-pill">'
    '📄 Professional Profile'
    '</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <h1
        class="hero-title"
        style="font-size:3.25rem"
    >
        Data Engineering Resume
    </h1>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="resume-intro">
        Data Engineer focused on building reliable data pipelines,
        multi-cloud data platforms, batch and streaming architectures, lakehouse design, data quality
        solutions, and AI-assisted data engineering systems.
        Explore my technical stack, projects, and downloadable resume.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Professional Snapshot
# ============================================================

render_section_header(
    "Professional Snapshot",
    "⚡",
)

r1, r2, r3, r4 = st.columns(4)

r1.metric(
    "Target Role",
    "Data Engineer",
)

r2.metric(
    "Programming",
    "Python",
)

r3.metric(
    "Query Language",
    "SQL",
)

r4.metric(
    "Cloud Platforms",
    "AWS · Azure · GCP",
)


r5, r6, r7, r8 = st.columns(4)

r5.metric(
    "Data Processing",
    "PySpark",
)

r6.metric(
    "Lakehouse Platform",
    "Databricks",
)

r7.metric(
    "Data Warehouse",
    "Snowflake",
)

r8.metric(
    "Transformation",
    "dbt",
)


# ============================================================
# CORE TECHNICAL SKILLS
# ============================================================

render_section_header(
    "Technical Skills",
    "🛠️",
)

# Row 1
c1, c2, c3 = st.columns(3)

with c1:
    skill_card(
        "💻",
        "Programming & Querying",
        "<strong>Python</strong> · <strong>SQL</strong> · "
        "PySpark · Apache Spark · Pandas · NumPy",
    )

with c2:
    skill_card(
        "☁️",
        "Cloud Platforms",
        "<strong>AWS</strong> · <strong>Azure</strong> · "
        "<strong>Google Cloud Platform (GCP)</strong>",
    )

with c3:
    skill_card(
        "🏗️",
        "Lakehouse & Warehouse",
        "<strong>Databricks</strong> · <strong>Snowflake</strong> · "
        "Delta Lake · Medallion Architecture · Data Lakehouse",
    )

# Row 2
c4, c5, c6 = st.columns(3)

with c4:
    skill_card(
        "🟧",
        "AWS Data Engineering",
        "Amazon S3 · AWS Glue · Athena · Lambda · IAM · "
        "CloudWatch · SNS · Lake Formation · EventBridge · SQS",
    )

with c5:
    skill_card(
        "🔷",
        "Azure Data Engineering",
        "Azure Data Factory · Azure Synapse · Microsoft Fabric · "
        "OneLake · Power BI",
    )

with c6:
    skill_card(
        "🔵",
        "GCP",
        "Google Cloud Platform for cloud data engineering workloads "
        "and multi-cloud architecture.",
    )

# Row 3
c7, c8, c9 = st.columns(3)

with c7:
    skill_card(
        "🔄",
        "Orchestration & Pipelines",
        "Apache Airflow · ETL / ELT · Incremental Loading · "
        "Watermarking · Batch Processing · Pipeline Monitoring",
    )

with c8:
    skill_card(
        "📡",
        "Streaming & Messaging",
        "Apache Kafka · Confluent Kafka · Event-Driven Pipelines · "
        "Streaming Data Processing",
    )

with c9:
    skill_card(
        "🧱",
        "Transformation",
        "<strong>dbt</strong> · Incremental Models · Snapshots · "
        "Data Transformations · Reusable SQL Models",
    )

# Row 4
c10, c11, c12 = st.columns(3)

with c10:
    skill_card(
        "⚙️",
        "DevOps & Infrastructure",
        "Terraform · Docker · GitHub Actions · CI/CD · "
        "Infrastructure as Code · AWS SAM",
    )

with c11:
    skill_card(
        "🗄️",
        "Databases & Storage",
        "PostgreSQL · MySQL · Amazon RDS · Data Lakes · "
        "Object Storage · Relational Databases",
    )

with c12:
    skill_card(
        "📐",
        "Data Modeling",
        "Star Schema · SCD Type 2 · Dimensional Modeling · "
        "Normalization · OLTP / OLAP · Schema Design",
    )

# Row 5
c13, c14, c15 = st.columns(3)

with c13:
    skill_card(
        "✅",
        "Data Quality & Reliability",
        "Data Profiling · Data Validation · Schema Drift · "
        "Duplicate Detection · Null Monitoring · Data Quality Scoring · "
        "Idempotent Loads",
    )

with c14:
    skill_card(
        "🔐",
        "Governance & Observability",
        "AWS Lake Formation · IAM · CloudWatch · Pipeline Monitoring · "
        "Data Lineage Concepts · Access Control",
    )

with c15:
    skill_card(
        "🤖",
        "AI for Data Engineering",
        "Generative AI · RAG · Vector Search · Ollama · "
        "LLM Integration · AI-assisted Data Quality & Diagnostics",
    )

# Row 6
c16, c17, c18 = st.columns(3)

with c16:
    skill_card(
        "📊",
        "Analytics & BI",
        "Tableau · Power BI · Amazon Athena · "
        "Data Visualization · Business Intelligence",
    )

with c17:
    skill_card(
        "🧪",
        "Data Engineering Patterns",
        "Bronze / Silver / Gold · Schema Evolution · "
        "Incremental Processing · Partitioning · Backfills · "
        "Error Handling",
    )

with c18:
    skill_card(
        "🌐",
        "APIs & Integration",
        "REST APIs · FastAPI Basics · API Gateway · "
        "JSON · Authentication Concepts · Service Integration",
    )


# ============================================================
# DATA ENGINEERING ARCHITECTURE PATTERNS
# ============================================================

render_section_header(
    "Data Engineering Architecture Patterns",
    "🏛️",
)

a1, a2, a3, a4 = st.columns(4)

with a1:
    skill_card(
        "📦",
        "Batch Processing",
        "Scheduled ingestion and transformation of large datasets using "
        "Spark, PySpark, Airflow, dbt, and cloud data platforms.",
    )

with a2:
    skill_card(
        "⚡",
        "Streaming Processing",
        "Near real-time ingestion and processing using Kafka, Spark Streaming, "
        "event streams, checkpoints, and incremental processing.",
    )

with a3:
    skill_card(
        "🔀",
        "Lambda Architecture",
        "Combines batch and real-time processing layers to support both "
        "historical accuracy and low-latency analytics.",
    )

with a4:
    skill_card(
        "🌊",
        "Kappa Architecture",
        "Stream-first architecture where events are continuously processed "
        "and replayed without maintaining a separate batch layer.",
    )


a5, a6, a7, a8 = st.columns(4)

with a5:
    skill_card(
        "🏞️",
        "Lakehouse Architecture",
        "Unified data lake and warehouse design using Databricks, Delta Lake, "
        "open formats, scalable storage, and analytics.",
    )

with a6:
    skill_card(
        "🥉",
        "Medallion Architecture",
        "Bronze, Silver, and Gold data layers for raw ingestion, cleaned data, "
        "business transformations, and analytics-ready outputs.",
    )

with a7:
    skill_card(
        "📨",
        "Event-Driven Architecture",
        "Systems triggered by events using Kafka, AWS Lambda, EventBridge, "
        "SQS, SNS, and asynchronous processing patterns.",
    )

with a8:
    skill_card(
        "🔁",
        "ETL / ELT Architecture",
        "Extract, load, and transformation pipelines using Airflow, dbt, "
        "Spark, Snowflake, Databricks, and cloud-native services.",
    )


# ============================================================
# ENGINEERING STRENGTHS
# ============================================================

render_section_header(
    "What I Bring",
    "🎯",
)

s1, s2, s3, s4 = st.columns(4)

with s1:
    strength_card(
        "🔄",
        "End-to-End Pipelines",
        "Build reliable data pipelines from ingestion and transformation "
        "through validation, storage, orchestration, and analytics.",
    )

with s2:
    strength_card(
        "☁️",
        "Cloud Data Engineering",
        "Build cloud-based data solutions using AWS, Databricks, Snowflake, "
        "and scalable lakehouse architecture.",
    )

with s3:
    strength_card(
        "✅",
        "Data Reliability",
        "Detect missing values, duplicates, schema drift, invalid records, "
        "and pipeline-quality issues before they affect downstream systems.",
    )

with s4:
    strength_card(
        "🤖",
        "AI + Data",
        "Combine deterministic data engineering with Generative AI and RAG "
        "for diagnostics, explanations, and recommendations.",
    )


# ============================================================
# RESUME FILES
# ============================================================

render_section_header(
    "Resume",
    "📁",
)

RESUME_DIRECTORY.mkdir(
    parents=True,
    exist_ok=True,
)

resume_files = sorted(
    RESUME_DIRECTORY.glob(
        "*.pdf"
    )
)

if not resume_files:

    st.warning(
        "No resume PDFs found. "
        "Add your PDF to `assets/resumes/`."
    )

else:

    resume_names = {
        file.stem.replace(
            "_",
            " ",
        ): file
        for file in resume_files
    }

    selected_name = st.selectbox(
        "Resume Version",
        list(
            resume_names.keys()
        ),
    )

    selected_file = (
        resume_names[
            selected_name
        ]
    )

    resume_bytes = (
        selected_file.read_bytes()
    )

    with st.container(
        border=True
    ):

        st.markdown(
            "### 📄 Selected Resume"
        )

        st.success(
            f"✅ {selected_name}"
        )

        i1, i2, i3 = st.columns(3)

        i1.metric(
            "Format",
            "PDF",
        )

        i2.metric(
            "Version",
            selected_name,
        )

        i3.metric(
            "File Size",
            (
                f"{selected_file.stat().st_size / 1024:.1f} KB"
            ),
        )

        st.download_button(
            "⬇️ Download Data Engineering Resume",
            data=resume_bytes,
            file_name=selected_file.name,
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )


    # ========================================================
    # RESUME HIGHLIGHTS
    # ========================================================

    render_section_header(
        "Resume Highlights",
        "🚀",
    )

    h1, h2, h3 = st.columns(3)

    with h1:

        with st.container(
            border=True
        ):

            st.markdown(
                "### ⚙️ Data Engineering"
            )

            st.caption(
                "Python • SQL • PySpark • Spark • "
                "Airflow • Kafka • ETL/ELT • "
                "Batch • Streaming • Data Pipelines"
            )

    with h2:

        with st.container(
            border=True
        ):

            st.markdown(
                "### ☁️ Modern Data Stack"
            )

            st.caption(
                "AWS • Azure • GCP • Databricks • Snowflake • "
                "dbt • Delta Lake • Terraform • Docker"
            )

    with h3:

        with st.container(
            border=True
        ):

            st.markdown(
                "### 🤖 Data + AI"
            )

            st.caption(
                "Data Quality • RAG • Generative AI • "
                "Ollama • AI-assisted Diagnostics"
            )


    # ========================================================
    # PDF PREVIEW
    # ========================================================

    render_section_header(
        "Resume Preview",
        "👀",
    )

    with st.expander(
        "Open Resume Preview",
        expanded=True,
    ):

        show_pdf_viewer(
            resume_bytes,
            key_prefix=(
                f"resume_"
                f"{selected_file.stem}"
            ),
        )


# ============================================================
# NEXT STEP
# ============================================================

render_section_header(
    "Explore More",
    "💼",
)

c1, c2 = st.columns(2)

with c1:

    st.page_link(
        "pages/1_Projects.py",
        label="🚀 Explore My Data Engineering Projects",
        use_container_width=True,
    )

with c2:

    st.page_link(
        "pages/4_Contact.py",
        label="📬 Contact Me",
        use_container_width=True,
    )


# ============================================================
# AI COPILOT
# ============================================================

render_ai_copilot(
    page_name="Resume",
    page_context=PAGE_CONTEXTS[
        "Resume"
    ],
)