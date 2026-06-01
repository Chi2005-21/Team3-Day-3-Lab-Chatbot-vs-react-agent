# import os
# api_key = os.getenv("OPENAI_ROUTER") or os.getenv("GEMINI_API_KEY")
# print(api_key)

# import os
# import time
# from typing import Dict, Any, List, Optional, Generator
# from openai import OpenAI
# from src.core.llm_provider import LLMProvider

# class OpenAIProvider(LLMProvider):
#     def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
#         if not api_key:
#             api_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
#         super().__init__(model_name, api_key)
#         self.client = OpenAI(api_key=self.api_key)

#     def generate(self, prompt: str, system_prompt: Optional[str] = None, stop: Optional[List[str]] = None) -> Dict[str, Any]:
#         start_time = time.time()
        
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})

#         response = self.client.chat.completions.create(
#             model=self.model_name,
#             messages=messages,
#             stop=stop
#         )

#         end_time = time.time()
#         latency_ms = int((end_time - start_time) * 1000)

#         # Extraction from OpenAI response
#         content = response.choices[0].message.content
#         usage = {
#             "prompt_tokens": response.usage.prompt_tokens,
#             "completion_tokens": response.usage.completion_tokens,
#             "total_tokens": response.usage.total_tokens
#         }

#         return {
#             "content": content,
#             "usage": usage,
#             "latency_ms": latency_ms,
#             "provider": "openai"
#         }

#     def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
#         messages = []
#         if system_prompt:
#             messages.append({"role": "system", "content": system_prompt})
#         messages.append({"role": "user", "content": prompt})

#         stream = self.client.chat.completions.create(
#             model=self.model_name,
#             messages=messages,
#             stream=True
#         )

#         for chunk in stream:
#             if chunk.choices[0].delta.content:
#                 yield chunk.choices[0].delta.content


# if __name__ == "__main__":
#     # Test script for checking if OpenAI key is valid
#     print("=" * 60)
#     print("           OPENAI API KEY VALIDATION RUNNER")
#     print("=" * 60)

#     # Key provided from env
#     env_key = os.getenv("OPENAI_API_KEY")

#     if not env_key:
#         print("[ERROR] No OPENAI_API_KEY environment variable is currently set.")
#         print("[*] Please set the OPENAI_API_KEY environment variable and try again.")
#         print("=" * 60)
#     else:
#         print(f"[*] Testing API key from environment:")
#         print(f"    Prefix: {env_key[:12]}...")
#         print(f"    Suffix: ...{env_key[-12:]}")

#         print("-" * 60)
#         print("[*] Initializing OpenAIProvider...")
#         try:
#             provider = OpenAIProvider(model_name="gpt-4o", api_key=env_key)
#             prompt = "Hello! Please give a 1-sentence greeting for a flight assistant traveler tool."
#             print(f"[*] Prompt: '{prompt}'")
#             print("[*] Generating response...")
            
#             result = provider.generate(
#                 prompt=prompt,
#                 system_prompt="You are a friendly digital nomad travel assistant."
#             )
            
#             print("-" * 60)
#             print("[SUCCESS] OpenAI connection verified! The key is VALID.")
#             print(f"[SUCCESS] Response Content: {result['content']}")
#             print(f"[SUCCESS] Usage: {result['usage']}")
#             print(f"[SUCCESS] Latency: {result['latency_ms']} ms")
#             print("=" * 60)
#         except Exception as e:
#             print("-" * 60)
#             print("[ERROR] OpenAI API verification FAILED.")
#             print(f"[ERROR] Exception Details: {e}")
#             print("[ERROR] Please check if the key is correct, has expired, is inactive, or has usage/billing limits.")
#             print("=" * 60)

import os
from typing import Optional
from dotenv import load_dotenv

from src.core.llm_provider import LLMProvider
from src.core.gemini_provider import GeminiProvider
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker

load_dotenv()

SYSTEM_PROMPT = """You are a helpful flight assistant. You can answer questions about flights,
travel planning, pricing estimates, and booking advice. You rely entirely on your own knowledge
to answer — you do not have access to live flight data or external tools."""


class Chatbot:
    """
    Simple single-pass LLM chatbot with no tools and no reasoning loop.
    Serves as the baseline to compare against the ReAct agent.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm
        self.conversation_history: list[dict] = []

    def chat(self, user_input: str) -> str:
        logger.log_event("CHATBOT_INPUT", {"input": user_input, "model": self.llm.model_name})

        # Build a prompt that includes prior turns for multi-turn context
        prompt = self._build_prompt(user_input)

        result = self.llm.generate(prompt, system_prompt=SYSTEM_PROMPT)

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )

        response_text = result["content"]

        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response_text})

        logger.log_event("CHATBOT_RESPONSE", {
            "response": response_text,
            "latency_ms": result.get("latency_ms"),
            "total_tokens": result.get("usage", {}).get("total_tokens"),
        })

        return response_text

    def _build_prompt(self, user_input: str) -> str:
        if not self.conversation_history:
            return user_input

        lines = []
        for turn in self.conversation_history:
            role = "User" if turn["role"] == "user" else "Assistant"
            lines.append(f"{role}: {turn['content']}")
        lines.append(f"User: {user_input}")
        return "\n".join(lines)

    def reset(self):
        self.conversation_history.clear()


def build_chatbot() -> Chatbot:
    """Factory that reads DEFAULT_PROVIDER from .env and returns a ready Chatbot."""
    provider = os.getenv("DEFAULT_PROVIDER", "google").lower()
    model = os.getenv("DEFAULT_MODEL", "google/gemini-3.1-flash-lite")

    if provider == "google":
        llm = GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    elif provider == "openai":
        llm = OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    else:
        raise ValueError(f"Unsupported provider '{provider}'. Set DEFAULT_PROVIDER to 'google' or 'openai'.")

    return Chatbot(llm)


if __name__ == "__main__":
    import sys
    bot = build_chatbot()
    
    print("=" * 60)
    print("            FLIGHT CHATBOT TERMINAL TESTER")
    print("=" * 60)
    
    test_query = "Find the top productivity-friendly flight options from CDG to AUS."
    print(f"[*] Test Question: '{test_query}'")
    print("[*] Generating chatbot baseline response...")
    print("-" * 60)
    
    try:
        response = bot.chat(test_query)
        print(f"Bot Answer:\n{response}")
        print("=" * 60)
    except Exception as e:
        print(f"[ERROR] Chatbot execution failed: {e}")
        print("=" * 60)
