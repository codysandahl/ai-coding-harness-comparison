import asyncio
from backend.providers.openai_client import OpenAIClient

async def test():
    client = OpenAIClient()
    print("Base URL:", client.base_url)
    print("API Key:", client.api_key[:10] + "...")
    
    try:
        models = await client.list_models()
        print("Models found:", len(models))
        for model in models[:5]:
            print(f"  - {model.get('id')} ({model.get('owned_by')})")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    asyncio.run(test())
