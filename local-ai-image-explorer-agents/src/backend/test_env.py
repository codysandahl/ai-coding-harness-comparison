import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=PROJECT_ROOT / '.env')

print("PROVIDER_BASE_URL:", os.getenv("PROVIDER_BASE_URL"))
print("PROVIDER_API_KEY:", os.getenv("PROVIDER_API_KEY")[:10] + "..." if os.getenv("PROVIDER_API_KEY") else None)
