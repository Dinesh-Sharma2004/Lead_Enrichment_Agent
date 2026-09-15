import asyncio
import json
import os
from pathlib import Path
import pandas as pd
import streamlit as st

from src.browser import BrowserManager
from src.agent import process_domain
from src.config import MAX_CONCURRENT_DOMAINS

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="Autonomous Lead Enrichment Engine",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling for premium look & feel
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }
    .metric-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-label {
        color: #64748B;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🤖 Autonomous Lead Enrichment Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Asynchronous web discovery, web scraping, and Groq LLM corporate intelligence extraction</div>', unsafe_allow_html=True)

# Sidebar Options
st.sidebar.header("⚙️ Settings & Configuration")
domains_file_path = Path("domains.txt")

default_domains_list = []
if domains_file_path.exists():
    with open(domains_file_path, "r") as f:
        default_domains_list = [line.strip() for line in f if line.strip()]

st.sidebar.markdown(f"**Default Domains in `domains.txt` ({len(default_domains_list)}):**")
if default_domains_list:
    st.sidebar.code("\n".join(default_domains_list), language="text")
else:
    st.sidebar.warning("`domains.txt` not found or empty.")

max_concurrent = st.sidebar.slider("Max Concurrent Crawls", min_value=1, max_value=10, value=MAX_CONCURRENT_DOMAINS)

# Main Input Section
st.subheader("🌐 Input Target Domains")
user_input = st.text_area(
    "Enter target domains (one per line or comma-separated):",
    placeholder="e.g.\nstripe.com\nsupabase.com\npostman.com\n\n(Leave empty to use default domains from domains.txt)",
    height=140
)

col1, col2 = st.columns([1, 4])
with col1:
    search_button = st.button("🚀 Start Lead Enrichment", type="primary", use_container_width=True)

async def run_enrichment(domains_list: list[str], concurrency: int):
    browser_manager = BrowserManager(max_concurrent=concurrency)
    await browser_manager.start()
    try:
        tasks = [process_domain(domain, browser_manager) for domain in domains_list]
        results = await asyncio.gather(*tasks)
        return results
    finally:
        await browser_manager.stop()

if search_button:
    # Determine domains list
    raw_domains = user_input.strip()
    target_domains = []
    
    if raw_domains:
        # Split by newline or comma
        raw_list = [d.strip() for d in raw_domains.replace(',', '\n').split('\n') if d.strip()]
        # Clean domain names (remove http:// or https:// if present)
        for d in raw_list:
            clean_d = d.replace('https://', '').replace('http://', '').split('/')[0].strip()
            if clean_d and clean_d not in target_domains:
                target_domains.append(clean_d)
        st.info(f"📋 Processing **{len(target_domains)}** custom domain(s): `{', '.join(target_domains)}`")
    else:
        # Fall back to default domains.txt
        if default_domains_list:
            target_domains = default_domains_list
            st.info(f"ℹ️ No domains entered. Using **{len(target_domains)}** default domain(s) from `domains.txt`: `{', '.join(target_domains)}`")
        else:
            st.error("❌ No domains provided and `domains.txt` is empty. Please enter at least one domain.")
            st.stop()

    if target_domains:
        with st.spinner("⏳ Crawling subpages, stripping boilerplate, and running Groq AI enrichment..."):
            try:
                results = asyncio.run(run_enrichment(target_domains, max_concurrent))
                
                # Convert results to Pydantic dicts
                json_results = [res.model_dump() for res in results]
                
                # Save output.json and output.csv
                with open("output.json", "w") as f:
                    json.dump(json_results, f, indent=2)

                csv_rows = []
                for res in results:
                    row = res.model_dump()
                    row['products_services'] = "; ".join([p['name'] for p in row['products_services']])
                    row['contact_points'] = "; ".join([f"{c['type']}: {c['value']}" for c in row['contact_points']])
                    row['leadership'] = "; ".join([f"{l['name']} ({l['role']})" for l in row['leadership']])
                    row['all_processed_urls'] = ", ".join(row['all_processed_urls'])
                    csv_rows.append(row)
                
                df = pd.DataFrame(csv_rows)
                df.to_csv("output.csv", index=False)
                
                st.success("✅ Lead Enrichment Completed Successfully!")

                # Key Metric Dashboard
                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.metric("Total Processed", len(results))
                with m2:
                    complete_cnt = sum(1 for r in results if "Complete" in r.extraction_status)
                    st.metric("Complete Extractions", f"{complete_cnt}/{len(results)}")
                with m3:
                    avg_conf = sum(r.confidence_score for r in results) / len(results) if results else 0
                    st.metric("Avg Confidence", f"{avg_conf:.0%}")
                with m4:
                    leadership_cnt = sum(len(r.leadership) for r in results)
                    st.metric("Leadership Found", leadership_cnt)

                st.divider()

                # Tabular View
                st.subheader("📊 Enriched Corporate Intelligence Data")
                
                display_cols = [
                    'domain', 'company_name', 'company_overview', 
                    'products_services', 'leadership', 'contact_points', 
                    'confidence_score', 'extraction_status'
                ]
                avail_cols = [c for c in display_cols if c in df.columns]
                st.dataframe(df[avail_cols], use_container_width=True)

                st.divider()

                # Download Buttons
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    json_bytes = json.dumps(json_results, indent=2).encode('utf-8')
                    st.download_button(
                        label="📥 Download JSON Results",
                        data=json_bytes,
                        file_name="output.json",
                        mime="application/json",
                        use_container_width=True
                    )
                with col_d2:
                    csv_bytes = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download CSV Results",
                        data=csv_bytes,
                        file_name="output.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

                # Individual JSON inspection
                st.subheader("🔍 Detailed Intelligence Inspector")
                for res in results:
                    with st.expander(f"🏢 {res.company_name} ({res.domain}) - Status: {res.extraction_status}"):
                        st.json(res.model_dump())

            except Exception as e:
                st.error(f"❌ Error during lead enrichment: {str(e)}")

# Export FastAPI app instance for Vercel serverless entrypoint discovery
from main import app as app

