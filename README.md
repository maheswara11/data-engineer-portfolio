Maheswara Reddy Varra — Data Engineering + AI Portfolio

A modern Streamlit portfolio focused on Data Engineering, Cloud, Data Quality, and AI-assisted engineering.

Highlights

Modern light/dark portfolio UI

Responsive top navigation

Recruiter-friendly Home, Projects, Resume, About, and Contact pages

Floating AI Portfolio Copilot on every page

Local Ollama / Qwen integration for development

Deterministic Data Quality engine

Human-approved remediation

Direct row editing and bulk correction

Smart column detection

Custom data-quality rules

Schema contract and schema-drift detection

Reusable cleaning recipes

Safe automatic fixes with revalidation

Final cleaning summary and audit report

Direct website contact form using Formspree

Project Structure

maheswara_modern_portfolio/
├── app.py
├── requirements.txt
├── retail_data_quality_test.csv
├── .gitignore
│
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml              # local only — never commit
│
├── assets/
│   ├── ai_bot.png
│   └── resumes/
│       └── Maheswara_Reddy_Varra_Data_Engineer_Resume.pdf
│
├── knowledge/
│   ├── profile.json
│   └── projects.json
│
├── src/
│   ├── __init__.py
│   ├── ai_engine.py
│   ├── ai_widget.py
│   ├── data_loader.py
│   ├── industry_rules.py
│   ├── knowledge_search.py
│   ├── page_contexts.py
│   ├── quality_engine.py
│   ├── quality_features.py
│   ├── remediation.py
│   └── ui.py
│
└── pages/
    ├── 1_Projects.py
    ├── 2_Data_Quality_Copilot.py
    ├── 3_Resume.py
    ├── 4_Contact.py
    └── 5_About.py

Requirements

requirements.txt

streamlit>=1.41,<2.0
pandas>=2.1,<3.0
requests>=2.31,<3.0
PyMuPDF>=1.24,<2.0

Install dependencies:

pip install -r requirements.txt

Run Locally

Start Ollama and install the local model:

ollama pull qwen2.5:3b

Run the portfolio:

streamlit run app.py

The default local AI configuration is:

OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=qwen2.5:3b
OLLAMA_TIMEOUT=90
OLLAMA_KEEP_ALIVE=30m
OLLAMA_NUM_PREDICT=150
OLLAMA_NUM_CTX=2048

AI Copilot

The AI Portfolio Copilot can answer questions about:

Skills

Projects

Current portfolio page

Uploaded datasets

Data-quality scores

Detected issues

Recommendations

Approved remediation history

The application uses deterministic answers first for common dataset/profile questions and sends only questions that need generation to Ollama.

The floating AI launcher is approximately:

Desktop: 72 × 72 px

Mobile: 56 × 56 px

Data Quality Copilot

The Data Quality Copilot supports:

CSV and JSON uploads

General, Retail, Healthcare, and Banking rule packs

Primary-key validation

Missing values

Blank strings

Duplicate rows

Duplicate primary keys

Email, phone, date, quantity, price, age, amount, and sequence validation

Smart column detection

Custom rules

Schema contracts

Schema-drift detection

Reusable cleaning recipes

Human-approved remediation

Direct row editing

Bulk correction

Undo

Before/after validation

Safe batch fixes

Final audit report

Clean CSV / JSON export

The original uploaded file is never modified. Cleaning happens only on a protected working copy.

Test the Data Quality Copilot

Upload:

retail_data_quality_test.csv

Recommended settings:

Industry: Retail
Primary Key: customer_id

Then run the analysis.

Example AI questions:

What is wrong with my dataset?

What should I fix first?

Are there duplicates?

What is my quality score?

Which rows have problems?

Explain the highest-severity issue.

Direct Contact Form

The Contact page includes LinkedIn, GitHub, Email, and a direct website message form.

Visitors can send a message without opening their own email application.

Local setup

Create:

.streamlit/secrets.toml

Add:

FORMSPREE_URL = "https://formspree.io/f/YOUR_FORM_ID"

Add this to .gitignore:

.streamlit/secrets.toml

Never commit secrets to GitHub.

Streamlit Community Cloud

In the deployed app:

Settings → Secrets

Add:

FORMSPREE_URL = "https://formspree.io/f/YOUR_FORM_ID"

Deployment Note for Ollama

localhost:11434 works only when Ollama is running on the same machine as Streamlit.

When deployed to Streamlit Community Cloud, localhost refers to the cloud server — not your laptop.

The portfolio and deterministic Data Quality features can still run without Ollama. For deployed generative AI, configure OLLAMA_URL to a secure remote model endpoint or move the AI backend to a hosted provider later.

Do not expose an unsecured Ollama server directly to the public internet.

Deployment Checklist

Before deployment:

app.py runs locally

requirements.txt is in the repository root

All files under src/ are committed

All pages are committed

Resume PDF exists under assets/resumes/

assets/ai_bot.png exists

.streamlit/secrets.toml is ignored by Git

Formspree secret is added in Streamlit Cloud

Data Quality upload and remediation work

Contact form sends a real test message

Desktop layout is tested

Mobile layout is tested

Run

streamlit run app.py

Author

Maheswara Reddy Varra

Data Engineering | Python | SQL | PySpark | Databricks | Snowflake | AWS | Azure | GCP | Data Quality | GenAI