"""
Chatbot baseline tests — demonstrates what the chatbot CAN and CANNOT do.

Simple tests  : single-turn factual / advisory questions the LLM handles well.
Complex tests : multi-step, live-data, or calculation tasks where the chatbot
                is expected to hallucinate or give vague answers — highlighting
                exactly why a ReAct agent is needed.

Run:
    python3 -m tests.test_chatbot
    # or individual sections:
    python3 -m tests.test_chatbot simple
    python3 -m tests.test_chatbot complex
"""

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.agent.chatbot import build_chatbot

# ── helpers ──────────────────────────────────────────────────────────────────

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner(title: str):
    print(f"\n{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'='*60}{RESET}\n")

def run_test(bot, label: str, question: str, expect_failure: bool = False, max_retries: int = 3):
    tag   = f"{YELLOW}[EXPECTED LIMITATION]{RESET}" if expect_failure else f"{GREEN}[EXPECTED PASS]{RESET}"
    print(f"{BOLD}Test:{RESET} {label}  {tag}")
    print(f"{BOLD}Q:{RESET} {question}")
    t0 = time.time()
    for attempt in range(max_retries):
        try:
            answer = bot.chat(question)
            elapsed = time.time() - t0
            print(f"{BOLD}A:{RESET} {answer.strip()}")
            print(f"   {CYAN}({elapsed:.1f}s){RESET}")
            break
        except Exception as e:
            err = str(e)
            # Parse retry delay from 429 response if present
            import re as _re
            match = _re.search(r"retry in (\d+)", err)
            wait = int(match.group(1)) + 2 if match else 20
            if "429" in err and attempt < max_retries - 1:
                print(f"   {YELLOW}Rate limited — waiting {wait}s then retrying ({attempt+1}/{max_retries-1})...{RESET}")
                time.sleep(wait)
            else:
                print(f"   {RED}ERROR: {err[:200]}{RESET}")
                break
    print()

# ── simple tests ─────────────────────────────────────────────────────────────

def run_simple_tests():
    banner("SIMPLE TESTS — single-turn, factual/advisory")
    bot = build_chatbot()

    run_test(bot,
        label="Basic airport code lookup",
        question="What is the IATA code for Paris Charles de Gaulle Airport?")

    run_test(bot,
        label="General travel advice",
        question="What documents do I need to fly from France to the United States?")

    run_test(bot,
        label="Airline baggage policy knowledge",
        question="What is the typical carry-on baggage allowance for economy class on British Airways?")

    run_test(bot,
        label="Time zone awareness",
        question="If my flight departs Paris (CDG) at 10:10 local time and lands in Austin (AUS) "
                 "after 13 hours total travel time, what is the local arrival time in Austin?")

    run_test(bot,
        label="Multi-turn conversation memory",
        question="I am planning a trip from Paris to Austin.")
    run_test(bot,
        label="  ↳ Follow-up (tests history)",
        question="What airlines typically fly that route?")
    run_test(bot,
        label="  ↳ Follow-up 2 (tests history)",
        question="Which of those would you recommend for a budget traveller?")

# ── complex tests ─────────────────────────────────────────────────────────────

def run_complex_tests():
    banner("COMPLEX TESTS — multi-step, live-data, calculations")
    bot = build_chatbot()

    run_test(bot,
        label="Live price lookup (no tools — will hallucinate)",
        question="What is the cheapest available flight from Paris CDG to Austin AUS today? "
                 "Give me the exact price in USD.",
        expect_failure=True)

    run_test(bot,
        label="Multi-step: price + tax + discount (no tools)",
        question="Find the cheapest flight from CDG to AUS on 2026-03-03. "
                 "Then calculate the total cost after adding 10% tax and applying a 5% loyalty discount.",
        expect_failure=True)

    run_test(bot,
        label="Carbon emissions comparison (no tools)",
        question="Compare the carbon emissions of all available flights from Paris to Austin "
                 "on March 3rd 2026 and tell me which flight is the most eco-friendly.",
        expect_failure=True)

    run_test(bot,
        label="Real-time seat availability (no tools)",
        question="Is seat 14A available on British Airways flight BA 303 from CDG to LHR on 2026-03-03?",
        expect_failure=True)

    run_test(bot,
        label="Conditional multi-step reasoning (no tools)",
        question="If the cheapest flight from CDG to AUS costs under $900, book it. "
                 "Otherwise, find the next cheapest option with fewer than 2 stops and "
                 "calculate how much I save compared to the most expensive option.",
        expect_failure=True)

    run_test(bot,
        label="Cross-query aggregation (no tools)",
        question="What is the average price of all one-stop flights from Paris to Austin "
                 "available this week, and which day is cheapest to fly?",
        expect_failure=True)

# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    print(f"\n{BOLD}Chatbot Baseline Capability Test{RESET}")
    print(f"Provider : {os.getenv('DEFAULT_PROVIDER', 'google')}")
    print(f"Model    : {os.getenv('DEFAULT_MODEL', 'gemini-1.5-flash')}")

    if mode in ("simple", "all"):
        run_simple_tests()
    if mode in ("complex", "all"):
        run_complex_tests()

    print(f"{BOLD}{CYAN}{'='*60}{RESET}")
    print(f"{BOLD}Done.{RESET}  Check logs/ for full JSON telemetry.\n")
