import asyncio
from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

response = client.get("/api/models")
print("Status:", response.status_code)
data = response.json()
print("Models:", len(data.get("models", [])))
for model in data.get("models", [])[:5]:
    print(f"  - {model.get('id')} ({model.get('owned_by')})")
