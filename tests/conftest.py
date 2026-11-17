import sys
from pathlib import Path

# Ensure backend directory is in sys.path so tests can import src.* and main
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

