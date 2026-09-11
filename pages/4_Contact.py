import streamlit as st

from src.ai_widget import render_ai_copilot
from src.page_contexts import PAGE_CONTEXTS
from src.ui import apply_theme, render_section_header, render_top_nav


st.set_page_config(
    page_title="Contact | Maheswara Reddy Varra",
    page_icon="📬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_theme()
render_top_nav("Contact")

st.markdown('<div class="hello-pill">📬 Let\'s Connect</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title" style="font-size:3.25rem">Contact Me</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-description">Open to Data Engineering, Databricks, PySpark, Cloud Data, Lakehouse, and AI + Data opportunities in the United States.</div>',
    unsafe_allow_html=True,
)

render_section_header("Connect With Me", "🤝")

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("### 💼 LinkedIn")
        st.caption("Connect professionally and view my experience, projects, and updates.")
        st.link_button(
            "Open LinkedIn",
            "https://www.linkedin.com/in/maheswara-reddy-varra",
            use_container_width=True,
        )
with c2:
    with st.container(border=True):
        st.markdown("### 💻 GitHub")
        st.caption("Explore my Data Engineering, AWS, Cloud, Data Quality, and AI projects.")
        st.link_button(
            "Open GitHub",
            "https://github.com/maheswara11",
            use_container_width=True,
        )
with c3:
    with st.container(border=True):
        st.markdown("### 📧 Email")
        st.caption("Reach out regarding Data Engineering opportunities or professional collaboration.")
        st.link_button(
            "Send Email",
            "mailto:maheswara7569@gmail.com",
            use_container_width=True,
        )

render_section_header("Roles I'm Interested In", "🎯")
r1, r2, r3 = st.columns(3)
with r1:
    with st.container(border=True):
        st.markdown("### ⚙️ Data Engineering")
        st.markdown("- Data Engineer\n- PySpark Data Engineer\n- ETL / ELT Developer\n- Big Data Engineer\n- Analytics Engineer")
with r2:
    with st.container(border=True):
        st.markdown("### ☁️ Cloud & Lakehouse")
        st.markdown("- Cloud Data Engineer\n- AWS Data Engineer\n- Databricks Engineer\n- Lakehouse Engineer\n- Data Platform Engineer")
with r3:
    with st.container(border=True):
        st.markdown("### 🧠 AI + Data")
        st.markdown("- GenAI Data Engineer\n- AI / Data Platform Engineer\n- Data Reliability Engineer\n- Data Quality Engineer")

render_section_header("Core Technical Stack", "🛠")
st.markdown(
    """
    <div class="skills-wrap">
        <span class="skill">Python</span><span class="skill">SQL</span>
        <span class="skill">PySpark</span><span class="skill">Apache Spark</span>
        <span class="skill">Databricks</span><span class="skill">Delta Lake</span>
        <span class="skill">AWS</span><span class="skill">Airflow</span>
        <span class="skill">Kafka</span><span class="skill">Terraform</span>
        <span class="skill">Docker</span><span class="skill">CI/CD</span>
        <span class="skill">GenAI</span><span class="skill">RAG</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.container(border=True):
    st.markdown("### 💼 Currently Open to Opportunities")
    st.success("Open to Data Engineering and related opportunities in the United States.")
    st.write(
        "If my background matches your Data Engineering, Databricks, PySpark, AWS, Cloud Data Platform, or AI + Data needs, I'd be glad to connect."
    )

render_ai_copilot(
    page_name="Contact",
    page_context=PAGE_CONTEXTS["Contact"],
)
