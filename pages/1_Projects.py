from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.ai_widget import render_ai_copilot
from src.page_contexts import PAGE_CONTEXTS
from src.ui import apply_theme, render_section_header, render_top_nav


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Projects | Maheswara Reddy Varra",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("Projects")


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"


# ============================================================
# PAGE STYLES
# ============================================================

st.html(
    """
    <style>
    .projects-intro {
        max-width: 1080px;
        color: #64748b;
        font-size: 1.04rem;
        line-height: 1.75;
        margin-bottom: 0.6rem;
    }

    .skills-wrap {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 6px 0 14px 0;
    }

    .skill {
        display: inline-block;
        padding: 6px 11px;
        border-radius: 999px;
        background: #eef4ff;
        border: 1px solid #d8e5ff;
        color: #24457a;
        font-size: 0.82rem;
        font-weight: 650;
        line-height: 1.2;
    }

    .architecture-card {
        min-height: 142px;
        padding: 18px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .architecture-title {
        color: #14264d;
        font-size: 0.98rem;
        font-weight: 750;
        margin-bottom: 8px;
    }

    .architecture-text {
        color: #61718b;
        font-size: 0.88rem;
        line-height: 1.55;
    }

    .value-card {
        min-height: 155px;
        padding: 20px;
        border: 1px solid #dce5f1;
        border-radius: 16px;
        background: #ffffff;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        margin-bottom: 12px;
    }

    .value-title {
        color: #14264d;
        font-size: 1rem;
        font-weight: 750;
        margin-bottom: 9px;
    }

    .value-text {
        color: #64748b;
        font-size: 0.9rem;
        line-height: 1.6;
    }

    .project-kicker {
        color: #4f6d9d;
        font-size: 0.86rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
    }

    /* Larger flagship Live Demo CTA */
    .st-key-live_demo_button [data-testid="stPageLink"] a {
        min-height: 68px !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
        border-radius: 16px !important;
        padding: 0.9rem 1.2rem !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    @media (max-width: 700px) {
        .st-key-live_demo_button [data-testid="stPageLink"] a {
            min-height: 62px !important;
            font-size: 1.02rem !important;
            padding: 0.75rem 0.95rem !important;
        }
    }
    </style>
    """
)


# ============================================================
# HELPERS
# ============================================================

def render_tags(tags: list[str]) -> None:
    """Render compact technology tags."""
    tag_html = "".join(
        f'<span class="skill">{tag}</span>'
        for tag in tags
    )
    st.html(
        f'<div class="skills-wrap">{tag_html}</div>'
    )


def architecture_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <div class="architecture-card">
            <div class="architecture-title">
                {icon} {title}
            </div>
            <div class="architecture-text">
                {description}
            </div>
        </div>
        """
    )


def value_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <div class="value-card">
            <div class="value-title">
                {icon} {title}
            </div>
            <div class="value-text">
                {description}
            </div>
        </div>
        """
    )


# ============================================================
# HERO
# ============================================================

st.html(
    '<div class="hello-pill">🚀 Engineering Portfolio</div>'
)

st.html(
    '<h1 class="hero-title" style="font-size:3.3rem">Data Engineering Projects</h1>'
)

st.html(
    """
    <div class="projects-intro">
        Hands-on projects covering batch and streaming data pipelines,
        cloud lakehouse architecture, event-driven processing, data quality,
        infrastructure automation, observability, and AI-assisted data engineering.
        Each project is built around a real engineering problem and emphasizes
        reliability, maintainability, and production-style design.
    </div>
    """
)

st.write("")


# ============================================================
# PORTFOLIO SNAPSHOT
# ============================================================

render_section_header(
    "Engineering Portfolio at a Glance",
    "⚡",
)

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Featured Projects",
    "5",
)

m2.metric(
    "Core Languages",
    "Python + SQL",
)

m3.metric(
    "Data Processing",
    "PySpark + Spark",
)

m4.metric(
    "Cloud / Platforms",
    "AWS + Databricks",
)


# ============================================================
# ARCHITECTURE COVERAGE
# ============================================================

render_section_header(
    "Architecture Coverage",
    "🏛️",
)

a1, a2, a3, a4 = st.columns(4)

with a1:
    architecture_card(
        "📦",
        "Batch Processing",
        "Scheduled ingestion, distributed transformations, incremental loads, "
        "and analytics-ready outputs.",
    )

with a2:
    architecture_card(
        "⚡",
        "Streaming Processing",
        "Kafka-based event ingestion, low-latency processing, and continuously "
        "updated downstream data.",
    )

with a3:
    architecture_card(
        "📨",
        "Event-Driven",
        "Data workflows triggered by new events or objects using cloud-native "
        "services and asynchronous processing.",
    )

with a4:
    architecture_card(
        "λ",
        "Serverless",
        "Managed, event-triggered processing using AWS Lambda, S3, IAM, "
        "and CloudWatch.",
    )


a5, a6, a7, a8 = st.columns(4)

with a5:
    architecture_card(
        "🏞️",
        "Lakehouse",
        "Scalable data lake and analytics architecture using Spark, governed "
        "storage, catalogs, and query layers.",
    )

with a6:
    architecture_card(
        "🥉",
        "Medallion",
        "Bronze, Silver, and Gold layers separating raw ingestion, cleaned data, "
        "and business-ready datasets.",
    )

with a7:
    architecture_card(
        "🔁",
        "ETL / ELT",
        "Source ingestion, transformation, validation, orchestration, and "
        "warehouse/lakehouse delivery patterns.",
    )

with a8:
    architecture_card(
        "🤖",
        "AI + Reliability",
        "Deterministic quality and reliability systems combined with RAG and "
        "LLM-assisted diagnosis and explanation.",
    )


# ============================================================
# PROJECT 1 — FLAGSHIP
# ============================================================

render_section_header(
    "Flagship Project",
    "🤖",
)

with st.container(border=True):

    title, status = st.columns([5, 1])

    with title:
        st.html(
            '<div class="project-kicker">Data Quality + GenAI</div>'
        )
        st.markdown("## AI Data Quality Copilot")

    with status:
        st.success("● Live Demo")

    render_tags(
        [
            "Python",
            "Pandas",
            "Streamlit",
            "Ollama",
            "Data Quality",
            "GenAI",
            "Human-in-the-Loop",
        ]
    )

    st.write(
        "A non-destructive Data Quality Copilot that analyzes CSV/JSON datasets, "
        "detects deterministic quality problems, identifies exact affected records, "
        "calculates quality scores, and supports human-approved remediation while "
        "keeping the original uploaded data protected."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎯 Engineering Problem",
            "✅ Quality + Safety",
            "🏗 Architecture",
        ]
    )

    with tab1:
        st.markdown(
            """
            **Problem addressed**

            Data teams frequently spend significant time identifying where bad data
            entered a pipeline, determining which records are affected, and deciding
            whether a proposed fix is safe.

            **Design approach**

            - Deterministic checks produce reproducible results
            - Exact record-level failures are surfaced to the user
            - AI explains the structured report instead of inventing quality facts
            - Remediation is approval-based and applies only to a working copy
            """
        )

    with tab2:
        st.markdown(
            """
            **Quality coverage**

            - Missing and blank values
            - Duplicate rows and primary-key issues
            - Invalid / future dates
            - Email and phone validation
            - Retail, Healthcare, and Banking rule packs

            **Safety controls**

            - Original upload remains unchanged
            - Human-approved remediation
            - Before vs after validation
            - Remediation history
            - Cleaned-data download
            - Local AI explanations grounded in the quality report
            """
        )

    with tab3:
        st.code(
            """
CSV / JSON
    ↓
Data Loader
    ↓
Pandas DataFrame
    ↓
Deterministic Quality Engine
    ↓
Industry Rule Pack
    ↓
Structured Quality Report
    ↓
Human Approval
    ↓
Protected Working Copy
    ↓
Re-run Validation
    ↓
AI Copilot Explanation
            """.strip()
        )

    d1, d2 = st.columns(2)

    with d1:
        with st.container(key="live_demo_button"):
            st.page_link(
                "pages/2_Data_Quality_Copilot.py",
                label="🚀 Open Live Demo",
                use_container_width=True,
            )

    with d2:
        st.link_button(
            "💻 View GitHub Profile",
            "https://github.com/maheswara11",
            use_container_width=True,
        )


# ============================================================
# PROJECT 2 — AWS RETAIL LAKEHOUSE
# ============================================================

render_section_header(
    "Cloud Data Engineering",
    "☁️",
)

with st.container(border=True):

    title, status = st.columns([5, 1])

    with title:
        st.html(
            '<div class="project-kicker">Batch + Lakehouse + Medallion</div>'
        )
        st.markdown("## End-to-End AWS Retail Sales Lakehouse")

    with status:
        st.info("● Completed")

    render_tags(
        [
            "AWS",
            "PySpark",
            "Apache Spark",
            "Airflow",
            "AWS Glue",
            "S3",
            "Athena",
            "Terraform",
            "GitHub Actions",
        ]
    )

    st.write(
        "A production-style AWS lakehouse pipeline using Bronze/Silver/Gold layers, "
        "distributed PySpark transformations, Airflow orchestration, incremental "
        "processing, monitoring, Infrastructure as Code, and CI/CD."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎯 Engineering Problem",
            "✅ Pipeline + Reliability",
            "🏗 Architecture",
        ]
    )

    with tab1:
        st.markdown(
            """
            **Problem addressed**

            Retail data arrives continuously and must be transformed into reliable,
            analytics-ready datasets without reprocessing the entire history on every run.

            **Design approach**

            - Separate raw, cleaned, and curated data using Medallion layers
            - Use PySpark for scalable transformations
            - Use Airflow to orchestrate dependencies and retries
            - Process only new data using watermark-based incremental logic
            - Automate infrastructure and deployment
            """
        )

    with tab2:
        st.markdown(
            """
            **Pipeline capabilities**

            - S3 raw ingestion
            - AWS Glue + PySpark transformations
            - CSV → Parquet
            - Bronze → Silver → Gold
            - Partitioned processing
            - Glue Data Catalog + Athena

            **Reliability & DevOps**

            - Watermark-based incremental loading
            - Airflow retries and task dependencies
            - CloudWatch monitoring
            - SNS failure notifications
            - Terraform Infrastructure as Code
            - GitHub Actions CI/CD
            - OIDC-based AWS authentication
            - IAM + Lake Formation governance
            """
        )

    with tab3:
        architecture_image = ASSETS_DIR / "pic.png"

        if architecture_image.is_file():
            st.image(
                str(architecture_image),
                caption="AWS Retail Sales Lakehouse Architecture",
                use_container_width=True,
            )
        else:
            st.code(
                """
New Data
    ↓
Airflow Orchestration
    ↓
Watermark Check
    ↓
Amazon S3 Raw
    ↓
AWS Glue / PySpark
    ↓
Bronze → Silver → Gold
    ↓
Glue Data Catalog
    ↓
Athena

CloudWatch + SNS → Monitoring / Alerts
Terraform → Infrastructure
GitHub Actions + OIDC → CI/CD
                """.strip()
            )

    d1, d2 = st.columns(2)

    with d1:
        st.link_button(
            "💻 View GitHub Project",
            "https://github.com/maheswara11/retail-sales-lakehouse-pipeline",
            use_container_width=True,
        )

    with d2:
        st.link_button(
            "👤 View GitHub Profile",
            "https://github.com/maheswara11",
            use_container_width=True,
        )


# ============================================================
# PROJECT 3 — STREAMING
# ============================================================

render_section_header(
    "Real-Time Data Engineering",
    "📡",
)

with st.container(border=True):

    title, status = st.columns([5, 1])

    with title:
        st.html(
            '<div class="project-kicker">Streaming + Kafka + Databricks</div>'
        )
        st.markdown("## Real-Time Streaming Data Pipeline")

    with status:
        st.info("● Completed")

    render_tags(
        [
            "Databricks",
            "Confluent Kafka",
            "PySpark",
            "PostgreSQL",
            "Streaming",
            "Dashboard",
        ]
    )

    st.write(
        "A real-time data pipeline using Kafka for event ingestion, "
        "Databricks/PySpark for stream processing, PostgreSQL for downstream "
        "storage, and an analytics layer for near real-time visibility."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎯 Engineering Problem",
            "✅ Streaming + Processing",
            "🏗 Architecture",
        ]
    )

    with tab1:
        st.markdown(
            """
            **Problem addressed**

            Traditional batch pipelines introduce delays when applications or analytics
            need continuously updated information.

            **Design approach**

            - Ingest events through Kafka instead of waiting for scheduled files
            - Process incoming records with Databricks and PySpark
            - Maintain a continuous flow from producer to downstream storage
            - Make processed data available for analytics and dashboards
            """
        )

    with tab2:
        st.markdown(
            """
            **Streaming capabilities**

            - Kafka producer / topic workflow
            - Confluent Kafka event ingestion
            - Databricks processing
            - PySpark transformations
            - Continuous / incremental data flow
            - PostgreSQL downstream storage
            - Dashboard-ready curated output

            **Architecture concepts**

            - Streaming processing
            - Event ingestion
            - Producer / consumer workflow
            - Low-latency data movement
            """
        )

    with tab3:
        st.code(
            """
Event Source
    ↓
Kafka Producer
    ↓
Confluent Kafka Topic
    ↓
Databricks / PySpark
    ↓
Streaming Transformations
    ↓
PostgreSQL
    ↓
Analytics Dashboard
            """.strip()
        )

    d1, d2 = st.columns(2)

    with d1:
        st.link_button(
            "💻 Explore GitHub Projects",
            "https://github.com/maheswara11",
            use_container_width=True,
        )

    with d2:
        st.page_link(
            "pages/3_Resume.py",
            label="📄 View Related Skills",
            use_container_width=True,
        )


# ============================================================
# PROJECT 4 — SERVERLESS
# ============================================================

render_section_header(
    "Serverless & Event-Driven",
    "⚡",
)

with st.container(border=True):

    title, status = st.columns([5, 1])

    with title:
        st.html(
            '<div class="project-kicker">Serverless + Event-Driven</div>'
        )
        st.markdown("## AWS Serverless Event-Driven Data Pipeline")

    with status:
        st.info("● Completed")

    render_tags(
        [
            "AWS Lambda",
            "Amazon S3",
            "Python",
            "boto3",
            "IAM",
            "CloudWatch",
        ]
    )

    st.write(
        "An event-driven serverless data pipeline that automatically processes "
        "new S3 objects with AWS Lambda and Python, validates required fields, "
        "transforms records, and writes curated output back to S3."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎯 Engineering Problem",
            "✅ Event + Operations",
            "🏗 Architecture",
        ]
    )

    with tab1:
        st.markdown(
            """
            **Problem addressed**

            File-based workflows often require manual execution or continuously running
            servers even when data only arrives occasionally.

            **Design approach**

            - Trigger processing automatically when a new object lands in S3
            - Use Lambda for serverless execution
            - Validate required fields before producing output
            - Keep infrastructure operationally simple and event-driven
            """
        )

    with tab2:
        st.markdown(
            """
            **Processing flow**

            - S3 ObjectCreated event
            - Lambda invocation
            - Python validation logic
            - Data transformation
            - Processed S3 output

            **Operations & security**

            - IAM access controls
            - CloudWatch logging
            - Event-driven execution
            - Serverless compute
            - No continuously running application server
            """
        )

    with tab3:
        st.code(
            """
Incoming Dataset
    ↓
Amazon S3
    ↓ ObjectCreated Event
AWS Lambda
    ↓
Python Validation / Transformation
    ↓
Processed S3

IAM → Access Control
CloudWatch → Logs / Monitoring
            """.strip()
        )

    d1, d2 = st.columns(2)

    with d1:
        st.link_button(
            "💻 View GitHub Project",
            "https://github.com/maheswara11/aws-serverless-data-processing-pipeline",
            use_container_width=True,
        )

    with d2:
        st.link_button(
            "👤 View GitHub Profile",
            "https://github.com/maheswara11",
            use_container_width=True,
        )


# ============================================================
# PROJECT 5 — AIOPS / FINOPS
# ============================================================

render_section_header(
    "AIOps + FinOps",
    "🧠",
)

with st.container(border=True):

    title, status = st.columns([5, 1])

    with title:
        st.html(
            '<div class="project-kicker">Reliability + RAG + FinOps</div>'
        )
        st.markdown("## AIOps Data Reliability & FinOps Platform")

    with status:
        st.warning("● In Development")

    render_tags(
        [
            "PySpark",
            "AWS",
            "PostgreSQL",
            "pgvector",
            "RAG",
            "GenAI",
            "FinOps",
            "Data Reliability",
        ]
    )

    st.write(
        "A data-reliability platform focused on detecting data-quality, Spark "
        "performance, and cloud-cost incidents, retrieving historical context, "
        "and supporting evidence-based diagnosis with human approval."
    )

    tab1, tab2, tab3 = st.tabs(
        [
            "🎯 Engineering Problem",
            "✅ Reliability + AI",
            "🏗 Architecture",
        ]
    )

    with tab1:
        st.markdown(
            """
            **Problem addressed**

            Data incidents can involve multiple systems at once: bad data, Spark
            performance regressions, pipeline failures, and unexpected cloud cost.
            Engineers often need to manually search logs, runbooks, past incidents,
            and code changes before deciding what to do.

            **Design approach**

            - Detect deterministic data and performance signals first
            - Retrieve historical incident context with RAG
            - Generate evidence-based recommendations
            - Validate proposed actions before execution
            - Keep humans in control of impactful remediation
            """
        )

    with tab2:
        st.markdown(
            """
            **Data reliability**

            - Schema drift
            - Null spikes
            - Duplicate spikes
            - Data-contract validation
            - Post-fix verification

            **AIOps + FinOps**

            - Spark skew and shuffle analysis
            - Runtime anomalies
            - Join-strategy regressions
            - Incident / runbook retrieval
            - PostgreSQL + pgvector
            - Cloud-cost anomaly analysis
            - Runtime vs cost analysis
            - Human approval workflow
            """
        )

    with tab3:
        st.code(
            """
Observe
  ↓
Detect
  ↓
Contain
  ↓
Investigate
  ↓
Retrieve Historical Context
  ↓
Generate Recommendation
  ↓
Validate in Sandbox
  ↓
Estimate Impact
  ↓
Human Approval
  ↓
Apply / Backfill
  ↓
Verify Recovery
  ↓
Learn From Outcome
            """.strip()
        )

    d1, d2 = st.columns(2)

    with d1:
        st.link_button(
            "💻 Explore GitHub",
            "https://github.com/maheswara11",
            use_container_width=True,
        )

    with d2:
        st.page_link(
            "pages/3_Resume.py",
            label="📄 View Related Skills",
            use_container_width=True,
        )


# ============================================================
# WHAT THE PORTFOLIO DEMONSTRATES
# ============================================================

render_section_header(
    "What This Portfolio Demonstrates",
    "🎯",
)

v1, v2, v3, v4 = st.columns(4)

with v1:
    value_card(
        "⚙️",
        "Data Pipeline Engineering",
        "Batch, streaming, incremental, event-driven, and serverless data flows "
        "with clear ingestion-to-serving architecture.",
    )

with v2:
    value_card(
        "☁️",
        "Cloud Engineering",
        "AWS services, Databricks, managed data platforms, IAM, monitoring, "
        "and infrastructure automation.",
    )

with v3:
    value_card(
        "🛡️",
        "Reliability & Quality",
        "Data validation, schema handling, observability, retries, alerts, "
        "human approval, and safe remediation.",
    )

with v4:
    value_card(
        "🤖",
        "AI for Data Engineering",
        "RAG, local LLMs, AI-assisted diagnostics, grounded explanations, "
        "and reliability-focused AI workflows.",
    )


# ============================================================
# CALL TO ACTION
# ============================================================

render_section_header(
    "Explore More",
    "💻",
)

g1, g2 = st.columns(2)

with g1:
    st.link_button(
        "🚀 Explore All GitHub Projects",
        "https://github.com/maheswara11",
        use_container_width=True,
    )

with g2:
    st.page_link(
        "pages/3_Resume.py",
        label="📄 View Data Engineering Resume",
        use_container_width=True,
    )


# ============================================================
# AI COPILOT
# ============================================================

render_ai_copilot(
    page_name="Projects",
    page_context=PAGE_CONTEXTS["Projects"],
)
