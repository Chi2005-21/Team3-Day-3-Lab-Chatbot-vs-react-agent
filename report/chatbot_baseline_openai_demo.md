# Chatbot Baseline — OpenAI Demo Run

## Setup

| Key | Value |
|---|---|
| Provider | OpenAI |
| Model | `gpt-5-nano` |
| Script | `python3 -m src.agent.chatbot` |

---

## Test Query

> **Find the cheapest flight from Paris to Austin and tell me the total price with 10% tax**

Same deliberate multi-step query used in the Gemini baseline — requires live data access and chained calculation.

---

## Chatbot Response

> I can't pull live flight data or guarantee the cheapest option right now. I can, however, help you plan and estimate what a "10% tax" total would look like and guide you to find the cheapest options.
>
> **What I need from you to tailor an answer**
> - Travel dates (depart date and return date if round-trip)
> - Number of passengers
> - Cabin preference (economy, premium economy, business)
> - Willingness to have connections (likely required Paris→Austin; nonstop options are rare)
> - Any airport preferences (Paris CDG or ORY; Austin AUS)
>
> **How to estimate the total price with 10% tax**
> - If you have a base fare per person (price before tax/fees), the total price with 10% tax is: Total = BaseFare × 1.10
> - Example calculations:
>   - Base fare 350 EUR → total = 385 EUR
>   - Base fare 500 USD → total = 550 USD
>   - Base fare 680 EUR → total = 748 EUR
>
> **Notes and tips to find a cheap Paris → Austin flight**
> - Be flexible with dates: midweek departures and avoiding holidays often yield cheaper fares.
> - Check multiple Paris airports (CDG and ORY) and consider a mix of carriers and one-stop itineraries.
> - Use price alerts and compare across a few aggregators, then verify on the airline's site (sometimes cheaper there).
> - Expect one-stop itineraries; nonstop options from Paris to Austin are uncommon.
> - Book a bit in advance for typical savings, but also watch for last-minute deals in some cases.
>
> If you share your dates, party size, and preferences, I can:
> - Outline plausible cheapest options you could target (routes and approximate price ranges)
> - Show how to estimate the total with 10% tax for those options
> - Help you compare a couple of concrete itineraries you find
>
> Would you like me to run through a sample with assumed dates, or would you rather provide your dates and I tailor a plan?

---

## Telemetry (from JSON logs)

```json
{"event": "CHATBOT_INPUT",    "data": {"input": "Find the cheapest flight from Paris to Austin and tell me the total price with 10% tax", "model": "gpt-5-nano"}}
{"event": "LLM_METRIC",       "data": {"provider": "openai", "model": "gpt-5-nano", "prompt_tokens": 77, "completion_tokens": 3365, "total_tokens": 3442, "latency_ms": 30396, "cost_estimate": 0.03442}}
{"event": "CHATBOT_RESPONSE", "data": {"latency_ms": 30396, "total_tokens": 3442}}
```

| Metric | Value |
|---|---|
| Prompt tokens | 77 |
| Completion tokens | 3 365 |
| Total tokens | 3 442 |
| Latency | 30 396 ms |
| Estimated cost | $0.034 |

---

## Provider Comparison — Same Query

| Metric | Gemini 2.5 Flash | GPT-5 Nano |
|---|---|---|
| Prompt tokens | 75 | 77 |
| Completion tokens | 280 | 3 365 |
| Total tokens | 621 | 3 442 |
| Latency | 4 124 ms | 30 396 ms |
| Est. cost | $0.006 | $0.034 |
| Response style | Short, redirects to external tools | Long, asks clarifying questions + gives formula examples |

---

## Analysis

Both models correctly **refuse to hallucinate** a live price, honouring the system prompt constraint. However their strategies differ:

- **Gemini 2.5 Flash** — brief, defers immediately to booking sites. Faster and cheaper (4s, $0.006), but less useful on its own.
- **GPT-5 Nano** — verbose, asks for clarification and demonstrates the tax calculation formula with examples. Slower and more expensive (30s, $0.034), but gives the user more to work with within the conversation.

Neither model can complete the task — both hit the same fundamental wall: **no tools, no live data**. GPT-5 Nano's longer response burns ~5× the tokens and takes ~7× longer than Gemini for the same outcome.

This confirms the baseline limitation is provider-agnostic: adding a ReAct agent with `search_flights()` and `calculate_tax()` tools is the only path to a grounded answer.
