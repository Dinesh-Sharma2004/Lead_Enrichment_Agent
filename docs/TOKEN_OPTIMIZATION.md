# Token Usage & Cost Optimization

By default, sending full web page HTML DOM trees directly to LLMs results in massive token consumption, high latency, and frequent rate limit errors.

## DOM Stripping Benchmark

The BeautifulSoup cleaning engine in `src/extraction.py` strips non-content tags:
- `<script>`, `<style>`, `<svg>`, `<nav>`, `<footer>`, `<header>`, `<aside>`, `<iframe>`, `<meta>`, `<link>`.

### Typical Page Token Savings

| Data Format | Raw HTML per Page | Cleaned Text per Page | Token Reduction % |
| :--- | :--- | :--- | :--- |
| Single Subpage | ~150 KB - 500 KB (~35,000 tokens) | ~2 KB - 10 KB (~1,200 tokens) | **~95% Savings** |
| Full 5-Page Domain | ~1.5 MB (~150,000 tokens) | ~20 KB - 40 KB (~5,000 tokens) | **~96.5% Savings** |

## Cost Impact
This pre-extraction content cleaning significantly reduces LLM API costs (estimated ~95% token savings based on stripping heavy script/style tags), while improving LLM extraction speed and precision. Note: Token reduction figures are estimated averages based on typical HTML payloads and may vary per domain structure.

