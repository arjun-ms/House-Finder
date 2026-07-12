import asyncio
from agents.browser_agent import run_browser_agent

async def main():
    print("Testing the deterministic fast path (browser_agent.py)...")
    properties = await run_browser_agent()
    print(f"\nTotal Properties Found: {len(properties)}")
    for p in properties:
        print(f"- {p.get('property_name', 'Unknown')} | {p.get('price', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(main())
