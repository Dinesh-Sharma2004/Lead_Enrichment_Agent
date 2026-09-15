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
