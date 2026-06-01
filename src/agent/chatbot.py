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
    model = os.getenv("DEFAULT_MODEL", "gemini-1.5-flash")

    if provider == "google":
        llm = GeminiProvider(model_name=model, api_key=os.getenv("GEMINI_API_KEY"))
    elif provider == "openai":
        llm = OpenAIProvider(model_name=model, api_key=os.getenv("OPENAI_API_KEY"))
    else:
        raise ValueError(f"Unsupported provider '{provider}'. Set DEFAULT_PROVIDER to 'google' or 'openai'.")

    return Chatbot(llm)


if __name__ == "__main__":
    bot = build_chatbot()
    print("Flight Chatbot (type 'quit' to exit)\n")
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ("quit", "exit"):
            break
        if not user_input:
            continue
        response = bot.chat(user_input)
        print(f"Bot: {response}\n")
