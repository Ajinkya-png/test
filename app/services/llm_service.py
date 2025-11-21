# import json
# import logging
# from typing import Dict, List, Optional, Any, AsyncGenerator
# from ..core.config import settings

# # Note: SDK names and async clients vary; these imports assume the presence of
# # `anthropic` and `openai` libraries with async clients. Adjust per your environment.
# import anthropic
# import openai

# logger = logging.getLogger(__name__)


# class LLMService:
#     """
#     LLM orchestration wrapper supporting a primary (Anthropic Claude) and fallback (OpenAI).
#     Provides synchronous create-style calls and a streaming helper.
#     """

#     def __init__(self):
#         # These client constructors may differ between SDK versions; adjust if needed.
#         self.anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
#         self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
#         self.primary_provider = "anthropic"  # Preferred provider
#         self.fallback_provider = "openai"    # Fallback provider

#     async def generate_response(
#         self,
#         messages: List[Dict[str, str]],
#         tools: List[Dict] = None,
#         tool_choice: Dict = None,
#         model: str = None,
#         temperature: float = 0.3,
#         max_tokens: int = 1000
#     ) -> Dict[str, Any]:
#         """
#         Generate a text response from the configured providers.
#         It tries primary provider first, then the fallback.
#         Returns a dict with keys: 'content' (str) and 'tool_calls' (list).
#         """
#         providers = [self.primary_provider, self.fallback_provider]

#         for provider in providers:
#             try:
#                 if provider == "anthropic":
#                     return await self._call_anthropic(
#                         messages, tools, tool_choice, model, temperature, max_tokens
#                     )
#                 elif provider == "openai":
#                     return await self._call_openai(
#                         messages, tools, tool_choice, model, temperature, max_tokens
#                     )
#             except Exception as e:
#                 logger.warning(f"LLM provider {provider} failed: {e}")
#                 continue

#         raise Exception("All LLM providers failed")

#     async def _call_anthropic(
#         self,
#         messages: List[Dict[str, str]],
#         tools: List[Dict] = None,
#         tool_choice: Dict = None,
#         model: str = None,
#         temperature: float = 0.3,
#         max_tokens: int = 1000
#     ) -> Dict[str, Any]:
#         """Call Anthropic Claude API (async)."""
#         if model is None:
#             model = "claude-3-5-sonnet-20241022"

#         # Convert to Anthropic message format: many SDKs take system + messages separately.
#         system_message = None
#         conversation_messages = []

#         for msg in messages:
#             if msg.get("role") == "system":
#                 system_message = msg.get("content")
#             else:
#                 conversation_messages.append(msg)

#         response = await self.anthropic_client.messages.create(
#             model=model,
#             system=system_message,
#             messages=conversation_messages,
#             tools=tools,
#             tool_choice=tool_choice,
#             temperature=temperature,
#             max_tokens=max_tokens
#         )

#         # Parse response (SDK shape may vary)
#         result = {
#             "content": response.content[0].text if getattr(response, "content", None) else "",
#             "tool_calls": []
#         }

#         # Extract tool calls if returned in content
#         for content in getattr(response, "content", []) or []:
#             if hasattr(content, "type") and content.type == "tool_use":
#                 result["tool_calls"].append({
#                     "id": getattr(content, "id", None),
#                     "name": getattr(content, "name", None),
#                     "arguments": getattr(content, "input", None)
#                 })

#         return result

#     async def _call_openai(
#         self,
#         messages: List[Dict[str, str]],
#         tools: List[Dict] = None,
#         tool_choice: Dict = None,
#         model: str = None,
#         temperature: float = 0.3,
#         max_tokens: int = 1000
#     ) -> Dict[str, Any]:
#         """Call OpenAI API (async)"""
#         if model is None:
#             model = "gpt-4o-mini"

#         response = await self.openai_client.chat.completions.create(
#             model=model,
#             messages=messages,
#             tools=tools,
#             tool_choice=tool_choice,
#             temperature=temperature,
#             max_tokens=max_tokens
#         )

#         message = response.choices[0].message
#         result = {
#             "content": message.content or "",
#             "tool_calls": []
#         }

#         # Extract tool calls if present (SDK-specific structure)
#         if getattr(message, "tool_calls", None):
#             for tool_call in message.tool_calls:
#                 try:
#                     result["tool_calls"].append({
#                         "id": tool_call.id,
#                         "name": tool_call.function.name,
#                         "arguments": json.loads(tool_call.function.arguments)
#                     })
#                 except Exception:
#                     # Fallback: store raw
#                     result["tool_calls"].append({
#                         "id": getattr(tool_call, "id", None),
#                         "name": getattr(tool_call, "function", {}).get("name") if getattr(tool_call, "function", None) else None,
#                         "arguments": getattr(tool_call, "function", {}).get("arguments") if getattr(tool_call, "function", None) else None
#                     })

#         return result

#     async def stream_response(
#         self,
#         messages: List[Dict[str, str]],
#         model: str = None,
#         temperature: float = 0.3,
#         max_tokens: int = 1000
#     ) -> AsyncGenerator[str, None]:
#         """Stream LLM response for lower latency. Yields text fragments."""
#         try:
#             if self.primary_provider == "anthropic":
#                 async with self.anthropic_client.messages.stream(
#                     model=model or "claude-3-5-sonnet-20241022",
#                     messages=messages,
#                     temperature=temperature,
#                     max_tokens=max_tokens
#                 ) as stream:
#                     async for text in stream.text_stream:
#                         yield text
#             else:
#                 # OpenAI streaming - SDK semantics may vary
#                 response = await self.openai_client.chat.completions.create(
#                     model=model or "gpt-4o-mini",
#                     messages=messages,
#                     temperature=temperature,
#                     max_tokens=max_tokens,
#                     stream=True
#                 )

#                 async for chunk in response:
#                     if chunk.choices[0].delta.content:
#                         yield chunk.choices[0].delta.content

#         except Exception as e:
#             logger.error(f"LLM streaming error: {e}")
#             yield "I apologize, but I'm having trouble responding right now."


# app/services/llm_service.py
import logging
import openai
from typing import Optional

logger = logging.getLogger(__name__)

class LLMService:
    """
    Simple wrapper for conversational reply generation.
    Uses OpenAI chat completion (gpt-4o-mini/gpt-4) — swap as needed.
    """
    def __init__(self, api_key: Optional[str] = None):
        from ..core.config import settings
        self.api_key = api_key or settings.OPENAI_API_KEY
        openai.api_key = self.api_key

        # model selection can be a setting
        self.model = "gpt-4o-mini" if self.api_key else "gpt-3.5-turbo"

    async def generate_reply(self, prompt: str) -> str:
        try:
            # Use synchronous call inside async wrapper for simplicity
            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=[{"role":"system","content":"You are a helpful food-delivery voice assistant."},
                          {"role":"user","content": prompt}],
                max_tokens=200,
                temperature=0.2,
            )
            text = resp["choices"][0]["message"]["content"].strip()
            logger.debug(f"LLM reply: {text[:120]}")
            return text
        except Exception as e:
            logger.exception(f"LLM generation error: {e}")
            return "Sorry — I'm having trouble responding right now."
