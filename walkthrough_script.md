# Autonomous Lead Enrichment Agent - 2 to 3 Minute Loom Walkthrough Script

This script is structured for a concise, professional 2-3 minute video demonstration of the project.

---

### **[0:00 - 0:45] Section 1: Overview & Project Structure**

**Visual:** Open your IDE showing the project directory tree (`src/`, `tests/`, `domains.txt`, `main.py`, `.env`).

**Script / Voiceover:**
> *"Hi everyone! Today I'm demonstrating our Autonomous Lead Enrichment Agent built in Python. This agent autonomously navigates company websites using headless Chromium via Playwright, extracts and cleans text, discovers relevant subpages like About and Careers, and uses Groq LLMs to produce structured, evidence-grounded corporate intelligence."*

> *"Let's take a quick look at the modular code architecture:"*
> - **`src/browser.py`**: Handles Playwright asynchronous browser initialization, navigation, and concurrency controls using semaphores.
> - **`src/discovery.py` & `src/extraction.py`**: Analyzes links to prioritize key pages like `/about` or `/pricing`, and strips HTML noise like `<nav>`, `<footer>`, `<script>`, and `<style>` tags using BeautifulSoup.
> - **`src/schemas.py`**: Defines canonical Pydantic models for structured output, tracking exact field names, source URLs, confidence scores, and extraction statuses.
> - **`src/llm.py`**: Integrates Groq (`openai/gpt-oss-120b`) and includes a custom `normalize_llm_json` pre-parser that guarantees schema compliance and handles LLM output variations.
> - **`src/search.py` & `src/agent.py`**: Orchestrates the hybrid workflow—crawling sites first, and fallback enriching leadership via SerpAPI if missing on the website.

---

### **[0:45 - 1:30] Section 2: Terminal Execution & Unit Tests**

**Visual:** Open the terminal window in VS Code / IDE.

**Script / Voiceover:**
> *"First, let's verify our core utility unit tests for HTML cleaning and link discovery heuristics:"*

```bash
pytest tests/
```
*(Point out the 5 passed tests in ~0.5s).*

> *"Now, let's execute the agent on our three target domains: `postman.com`, `supabase.com`, and `vapi.ai`, configured in `domains.txt`."*

```bash
python main.py domains.txt
```

**Visual:** Highlight the live terminal logs as domains are processed concurrently.

> *"Notice the terminal logging in real time:"*
> 1. Playwright initializes Chromium and launches context sessions concurrently.
> 2. The discovery engine ranks links and navigates top subpages (like `/company/about-postman`, `/careers`, `/pricing`).
> 3. Cleaned text payload is sent to Groq.
> 4. For `supabase.com`, leadership was not found directly on the site, so the agent automatically performed a SerpAPI fallback search for 'Supabase' leadership, enriching the result dynamically without crashing.

---

### **[1:30 - 2:30] Section 3: Inspecting Extracted Output**

**Visual:** Open `output.json` and `output.csv` in the editor.

**Script / Voiceover:**
> *"Now let's examine the generated outputs in `output.json` and `output.csv`."*

> *"Here in `output.csv`:"*
> - **Postman (`postman.com`)**: Successfully extracted 2-sentence company overview, target audience (*"Developers, engineering teams, and enterprises"*), products (*Postman API Platform*), contact emails (`info@postman.com`), leadership (*Abhinav Asthana, CEO & Co-founder*), and exact `source_url` citations with a confidence score of 1.0.
> - **Supabase (`supabase.com`)**: Extracted full product suite (*Postgres, Auth, Edge Functions, Realtime*), contact points, and dynamically enriched leadership (*Paul Copplestone, CEO*) via SerpAPI with a status of `Leadership enriched via SerpAPI`.
> - **Vapi (`vapi.ai`)**: Extracted full voice AI platform data, pricing packages, contact emails, and leadership with 1.0 confidence.

> *"Every field is grounded with evidence URLs, valid Pydantic types, and no fabricated data. Thank you for watching!"*
