
import asyncio
import os
import logging
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load .env directly
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenRouterTest")

async def test_openrouter():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("❌ No OPENROUTER_API_KEY found in .env")
        return

    logger.info(f"🔑 Found API Key: {api_key[:10]}...")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1"
    )
    
    logger.info("⏳ Sending test request to OpenRouter (model: openai/gpt-4o-2024-08-06)...")
    
    try:
        response = await client.chat.completions.create(
            model="openai/gpt-4o-2024-08-06",
            messages=[
                {"role": "user", "content": "Hello! Reply with 'OK' if you receive this."}
            ],
            extra_headers={
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "TestScript"
            }
        )
        content = response.choices[0].message.content
        logger.info(f"✅ Success! Response: {content}")
        
    except Exception as e:
        logger.error(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_openrouter())
