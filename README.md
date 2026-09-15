<div align="center">

#  Autonomous Lead Enrichment Agent

**An asynchronous, evidence-grounded corporate intelligence engine using Playwright web automation, BeautifulSoup content cleaning, Groq LLMs, and SerpAPI enrichment.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Playwright](https://img.shields.io/badge/Playwright-Chromium-green.svg)](https://playwright.dev/python/)
[![Groq API](https://img.shields.io/badge/Groq-openai%2Fgpt--oss--120b-orange.svg)](https://groq.com/)
[![SerpAPI](https://img.shields.io/badge/SerpAPI-Search--Enrichment-purple.svg)](https://serpapi.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.6-red.svg)](https://docs.pydantic.dev/)

</div>

---

##  Overview

The **Autonomous Lead Enrichment Agent** accepts an array of company domains, autonomously navigates their websites via headless Chromium, discovers relevant subpages (About, Team, Products, Pricing, Careers, Contact), extracts cleaned DOM content, and leverages Groq LLMs to produce structured, evidence-grounded corporate intelligence.

If key information (such as leadership) is missing from the website, the agent conditionally triggers external searches via **SerpAPI**, validating search results before merging.

- 🎬 **Video Demo:** [Watch 2-3 Minute Loom Video Demo](https://www.loom.com/share/your-loom-link-here) *(Placeholder)*
- 📄 **Walkthrough Script:** [`WALKTHROUGH_SCRIPT.md`](./WALKTHROUGH_SCRIPT.md)

---

##  Quick Start

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

### 3. Execution

Define target domains in `domains.txt` and run the agent:
```bash
python main.py domains.txt
```

Generated outputs:
- **`output.json`**: Full structured Pydantic dataset with source URL evidence.
- **`output.csv`**: Flattened tabular spreadsheet format.

---

##  Key Features

- **🌐 Autonomous Link Discovery:** Dynamically prioritizes key pages (`/about`, `/team`, `/pricing`, `/careers`, `/contact`).
- **🧹 Boilerplate Cleaning:** Strips scripts, styles, nav, and footers for ~95% token savings.
- **🛡️ Pydantic Normalization:** Pre-validates LLM JSON output to enforce exact schema compliance.
- **🔍 Hybrid SerpAPI Enrichment:** Fallback enrichment for missing leadership names and LinkedIn profiles.
- **⚡ Async Concurrency:** Controlled parallel domain processing via `asyncio.Semaphore`.

---

## 📚 Project Documentation

Detailed documentation is available in the [`docs/`](./docs/) directory:

- 🏛️ **[System Architecture & Workflow](./docs/ARCHITECTURE.md)** – Detailed pipeline flowchart, component details, and heuristic link scoring.
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
├── tests/                # Pytest unit tests
├── .env.example          # Environment template
├── domains.txt           # Input domain list
├── main.py               # CLI entry point
├── output.csv            # Tabular output dataset
├── output.json           # JSON structured dataset
├── README.md             # High-level overview
└── WALKTHROUGH_SCRIPT.md # Loom video narration guide
```

---

## 📜 License

Distributed under the MIT License.
