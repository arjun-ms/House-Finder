import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent, ChatGoogle

async def test_chat_google():
    load_dotenv()
    
    # Ensure GOOGLE_API_KEY is set
    if not os.environ.get("GOOGLE_API_KEY") and os.environ.get("GEMINI_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
    
    key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not key:
        print("[-] No API key found.")
        return
        
    print(f"[+] API Key: {key[:5]}...{key[-5:]}")
    
    # Use browser-use's own ChatGoogle wrapper
    llm = ChatGoogle(model="gemini-2.5-flash")
    
    print(f"[+] ChatGoogle initialized.")
    print(f"    - Has provider? {hasattr(llm, 'provider')}")
    if hasattr(llm, 'provider'):
        print(f"    - provider = {llm.provider}")
    print(f"    - Has model? {hasattr(llm, 'model')}")
    if hasattr(llm, 'model'):
        print(f"    - model = {llm.model}")
    
    # Try initializing the Agent
    try:
        print("[+] Initializing browser-use Agent...")
        agent = Agent(
            task="Go to example.com and tell me the page title.",
            llm=llm
        )
        print("[+] Agent initialized successfully!")
    except Exception as e:
        print(f"[-] Agent init failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Try running
    try:
        print("[+] Running agent...")
        result = await agent.run()
        print("[+] Agent run completed!")
        if result:
            print("Result:", result.final_result())
    except Exception as e:
        print(f"[-] Agent run failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_google())
