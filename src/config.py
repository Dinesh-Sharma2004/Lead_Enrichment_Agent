import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
ENABLE_SERPAPI = os.getenv("ENABLE_SERPAPI", "False").lower() in ("true", "1", "yes")
MAX_CONCURRENT_DOMAINS = int(os.getenv("MAX_CONCURRENT_DOMAINS", "3"))
MAX_PAGES_PER_DOMAIN = int(os.getenv("MAX_PAGES_PER_DOMAIN", "5"))
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "30"))
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

NETWORK_IDLE_TIMEOUT_MS = int(os.getenv("NETWORK_IDLE_TIMEOUT_MS", "5000"))
PAGE_HYDRATION_TIMEOUT_MS = int(os.getenv("PAGE_HYDRATION_TIMEOUT_MS", "1000"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
TOTAL_CONTEXT_CHAR_BUDGET = int(os.getenv("TOTAL_CONTEXT_CHAR_BUDGET", "16000"))
