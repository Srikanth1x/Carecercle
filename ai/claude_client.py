import anthropic
from config.settings import ANTHROPIC_API_KEY

_client = None

def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    return _client

async def call_claude(prompt: str, system: str = None) -> str:
    client = get_client()
    for attempt in range(2):
        try:
            messages = [{"role": "user", "content": prompt}]
            kwargs = {"model": "claude-sonnet-4-6", "max_tokens": 1024, "messages": messages}
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            if attempt == 1:
                raise
    return ""
