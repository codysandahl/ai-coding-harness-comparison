#!/usr/bin/env python3
"""Demo script to test basic functionality without running the full server."""

import asyncio
import httpx
import json
from pathlib import Path

async def demo():
    """Run a quick self-check of the system."""
    print("Local AI Image Explorer - Self Check")
    print("=" * 50)
    
    # Test API connectivity
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/models")
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                print(f"✓ Connected to API. Found {len(models)} models.")
                print(f"✓ Sample models: {[m['id'] for m in models[:3]]}")
            else:
                print(f"✗ API returned status {response.status_code}")
    except Exception as e:
        print(f"✗ Failed to connect to API: {e}")
        print("  (Server may not be running)")
        return
    
    print("\n" + "=" * 50)
    print("System is ready for stateless operation.")

if __name__ == "__main__":
    asyncio.run(demo())
