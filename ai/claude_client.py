import anthropic
from config.settings import ANTHROPIC_API_KEY

_client = None

def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
    return _client

async def call_claude(prompt: str, system: str = None) -> str:
    client = get_client()
    messages = [{"role": "user", "content": prompt}]
    kwargs = {"model": "claude-sonnet-4-6", "max_tokens": 1024, "messages": messages}
    if system:
        kwargs["system"] = system

    for attempt in range(3):
        try:
            response = await client.messages.create(**kwargs)
            return response.content[0].text
        except anthropic.RateLimitError:
            if attempt < 2:
                await __import__("asyncio").sleep(2 ** attempt)
                continue
            raise
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < 2:
                await __import__("asyncio").sleep(2 ** attempt)
                continue
            raise
    return ""
