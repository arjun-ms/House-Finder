import asyncio
import os
from dotenv import load_dotenv
from browser_use import Agent

async def test_groq():
    load_dotenv()
    from langchain_groq import ChatGroq
    
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        print("[-] No GROQ_API_KEY found.")
        return
        
    print(f"[+] API Key: {key[:5]}...{key[-5:]}")
    
    # Initialize ChatGroq and patch provider
    llm = ChatGroq(model="llama-3.3-70b-versatile")
    setattr(type(llm), 'provider', property(lambda self: 'groq'))
    
    print(f"[+] ChatGroq initialized.")
    
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
    asyncio.run(test_groq())
