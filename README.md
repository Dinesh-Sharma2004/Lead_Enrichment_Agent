<div align="center">

# 🤖 Autonomous Lead Enrichment Agent

**An asynchronous, evidence-grounded corporate intelligence engine with Streamlit Web UI, Playwright web automation, BeautifulSoup content cleaning, Groq LLMs, and SerpAPI enrichment.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-v1.31-red.svg)](https://streamlit.io/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/python/)
[![Groq API](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--120b-orange.svg)](https://groq.com/)
[![SerpAPI](https://img.shields.io/badge/SerpAPI-Search--Enrichment-purple.svg)](https://serpapi.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.6-red.svg)](https://docs.pydantic.dev/)

</div>

---

## 📌 Overview

The **Autonomous Lead Enrichment Agent** accepts company domains, autonomously navigates their websites via headless Chromium, discovers relevant subpages (About, Team, Products, Pricing, Careers, Contact), extracts cleaned DOM content, and leverages Groq LLMs to produce structured, evidence-grounded corporate intelligence.

If key information (such as leadership) is missing from the website, the agent conditionally triggers external searches via **SerpAPI**, validating search results before merging.

### Interfaces
- **🖥️ Streamlit Web App (`app.py`):** Interactive UI for custom domain input, fallback to `domains.txt`, dynamic data visualization, and instant JSON/CSV downloads.
- **💻 Command-Line Interface (`main.py domains.txt`):** Batch CLI processing with `output.json` and `output.csv` export.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/Dinesh-Sharma2004/Lead_Enrichment_Agent.git
cd Lead_Enrichment_Agent

# Install dependencies & Playwright Chromium
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your API keys:
```bash
cp .env.example .env
```

```env
GROQ_API_KEY=gsk_your_groq_api_key_here
SERPAPI_API_KEY=your_serpapi_api_key_here
ENABLE_SERPAPI=True
```

### 3. Execution Options

#### Option A: Streamlit Web UI (Interactive)
```bash
streamlit run app.py
```
- Enter target domains in the text area (e.g. `stripe.com`, `supabase.com`).
- If left empty, clicking **Start Lead Enrichment** automatically uses default domains from `domains.txt`.
- View interactive metrics, tables, and download JSON/CSV files.

#### Option B: Command Line Interface (CLI)
```bash
python main.py domains.txt
```

Generated outputs:
- **`output.json`**: Full structured Pydantic dataset with source URL evidence.
- **`output.csv`**: Flattened tabular spreadsheet format.

---

## ✨ Key Features

- **📊 Interactive Streamlit Web UI:** Multi-domain text input with `domains.txt` fallback and live dataset visualization.
- **🌐 Autonomous Link Discovery:** Dynamically prioritizes key pages (`/about`, `/team`, `/pricing`, `/careers`, `/contact`).
- **🧹 Boilerplate Cleaning:** Strips scripts, styles, nav, and footers for ~95% token savings.
- **🛡️ Pydantic Normalization:** Pre-validates LLM JSON output to enforce exact schema compliance.
- **🔍 Hybrid SerpAPI Enrichment:** Fallback enrichment for missing leadership names and LinkedIn profiles.
- **⚡ Async Concurrency:** Controlled parallel domain processing via `asyncio.Semaphore`.

---

## 📚 Project Documentation

Detailed documentation is available in the [`docs/`](./docs/) directory:

- 🏛️ **[System Architecture & Workflow](./docs/ARCHITECTURE.md)** – Detailed pipeline flowchart, component details, Streamlit integration, and heuristic link scoring.
- ⚙️ **[Configuration Reference](./docs/CONFIGURATION.md)** – Complete `.env` variables table and performance tuning.
- 💰 **[Token Optimization & Cost Control](./docs/TOKEN_OPTIMIZATION.md)** – DOM stripping efficiency benchmarks (~95% token reduction).
- 🔍 **[Troubleshooting Guide](./docs/TROUBLESHOOTING.md)** – Solving API 401s, Playwright Linux dependencies, and timeouts.
- 📊 **[Operational Impact & Benchmark](./docs/OPERATIONAL_IMPACT.md)** – Manual operations reduction (~80-85% automation).

---

## 🧪 Running Unit Tests

```bash
pytest tests/
```

---

## 📂 Repository Structure

```text
Lead_Enrichment_Agent/
├── docs/                 # Detailed documentation modules
│   ├── ARCHITECTURE.md
│   ├── CONFIGURATION.md
│   ├── OPERATIONAL_IMPACT.md
│   ├── TOKEN_OPTIMIZATION.md
│   └── TROUBLESHOOTING.md
├── src/                  # Core agent implementation modules
│   ├── agent.py          # Orchestration workflow
│   ├── browser.py        # Playwright browser manager
│   ├── config.py         # Environment configuration
│   ├── discovery.py      # Heuristic link scoring
│   ├── extraction.py     # BeautifulSoup DOM cleaning
│   ├── llm.py            # Groq LLM extraction & pre-normalization
│   ├── logger.py         # Logging setup
│   ├── schemas.py        # Pydantic data schemas
│   └── search.py         # SerpAPI leadership fallback
├── tests/                # Pytest unit tests
├── app.py                # Streamlit Web UI application
├── main.py               # CLI entry point
├── .env.example          # Environment template
├── domains.txt           # Input domain list default
├── output.csv            # Tabular output dataset
├── output.json           # JSON structured dataset
├── README.md             # High-level overview
└── WALKTHROUGH_SCRIPT.md # Loom video narration guide
```

---

## 📜 License

Distributed under the MIT License.
