# Chatbot Baseline — Demo Run

## Setup

| Key | Value |
|---|---|
| Provider | Google Gemini |
| Model | `gemini-2.5-flash` |
| Script | `python3 -m src.agent.chatbot` |

---

## Test Query

> **Find the cheapest flight from Paris to Austin and tell me the total price with 10% tax**

This is a deliberate multi-step task that requires live data access and chained calculation — the kind of query the chatbot is expected to fail on.

---

## Chatbot Response

> As a helpful flight assistant, I can offer general advice and information about travel, but I don't have access to live flight data or real-time pricing information. This means I can't find the cheapest flight or calculate a specific total price for you.
>
> Flight prices from Paris to Austin can vary significantly based on many factors, including:
> - **Time of year:** Peak travel seasons are more expensive.
> - **How far in advance you book:** Generally, booking several months ahead can be cheaper.
> - **Specific dates and times:** Weekends and popular travel times are often pricier.
> - **Airline and connections:** Direct flights are usually more expensive than those with layovers.
> - **Demand:** Prices fluctuate based on how many people are looking to book.
>
> To find the cheapest flight and calculate the total price with tax, I recommend using a reputable online flight comparison website (like Google Flights, Skyscanner, Kayak, Expedia, etc.) or checking directly with airlines that fly this route. These tools allow you to input your desired dates and will show you current prices and various options.
>
> Once you have a base fare, you can then easily add your 10% tax to get your estimated total.
>
> Let me know if you have any other general questions about travel planning, common routes, or tips for finding good deals!

---

## Telemetry (from JSON logs)

```json
{"event": "CHATBOT_INPUT",    "data": {"input": "Find the cheapest flight from Paris to Austin and tell me the total price with 10% tax", "model": "gemini-2.5-flash"}}
{"event": "LLM_METRIC",       "data": {"provider": "google", "model": "gemini-2.5-flash", "prompt_tokens": 75, "completion_tokens": 280, "total_tokens": 621, "latency_ms": 4124, "cost_estimate": 0.00621}}
{"event": "CHATBOT_RESPONSE", "data": {"latency_ms": 4124, "total_tokens": 621}}
```

| Metric | Value |
|---|---|
| Prompt tokens | 75 |
| Completion tokens | 280 |
| Total tokens | 621 |
| Latency | 4 124 ms |
| Estimated cost | $0.006 |

---

## Analysis

The chatbot **correctly admits** it cannot fulfil the request rather than hallucinating a price. This is good behaviour from the system prompt (`"You do not have access to live flight data or external tools"`), but it also reveals the core limitation:

- It **cannot search** for real flights.
- It **cannot calculate** a tax-inclusive price on an actual fare.
- It **redirects** the user to external tools (Google Flights, Skyscanner) instead of acting.

A single-pass LLM with no tools is fundamentally unable to complete data-dependent, multi-step tasks. This result is the motivation for building the ReAct agent, which can call `search_flights()` and `calculate_tax()` as actual tool calls and return a grounded answer.
