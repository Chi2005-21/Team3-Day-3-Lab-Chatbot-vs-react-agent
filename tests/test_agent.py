import os
import sys
from dotenv import load_dotenv

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import get_fallback_provider
from src.agent.agent import ReActAgent

def test_flight_agent():
    # Load env variables (ensures API keys are parsed)
    load_dotenv()
    
    print("=== Initializing Fallback LLM Provider ===")
    try:
        # Build Fallback Chain: OpenAI -> Gemini -> Local
        llm = get_fallback_provider()
        print(f"Fallback Provider chain built successfully. Initial model: {llm.model_name}")
    except Exception as e:
        print(f"[ERROR] Error initializing LLM Provider: {e}")
        return

    # Define tools metadata for the ReAct Agent's system instructions
    tools_metadata = [
        {
            "name": "find_productivity_flights",
            "description": "Scores and ranks flight routes from the database based on productivity-enabling comforts (Wi-Fi, power, legroom, layovers)."
        },
        {
            "name": "time_until_flight",
            "description": "Calculates the duration remaining (or elapsed) until a specific flight departs. Usage: time_until_flight(flight_number, current_time_str)"
        },
        {
            "name": "parse_flight_details",
            "description": "Parses segment-by-segment itinerary, layover details, carbon footprint, and pricing for a specific flight route. Usage: parse_flight_details(flight_number)"
        },
        {
            "name": "get_current_time",
            "description": "Returns the current local date and time of the system in 'YYYY-MM-DD HH:MM' format. Use this to get the exact reference time."
        }
    ]

    print("\n=== Initializing ReAct Agent ===")
    agent = ReActAgent(llm=llm, tools=tools_metadata, max_steps=10)
    
    # Combined complex user request matching our use case
    user_query = (
        "Find the top productivity-friendly flight options from CDG to AUS. "
        "Also, retrieve the complete itinerary details for flight 'BA 191', "
        "and calculate how much time is left before flight 'BA 303' departs if the current reference time is '2026-03-03 08:30'."
    )
    
    print(f"\nUser Query: {user_query}")
    print("\n--- Running Agentic Loop ---")
    
    try:
        final_answer = agent.run(user_query)
        print("\n================ FINAL AGENT ANSWER ================")
        print(final_answer)
        print("====================================================")
        print("\n[SUCCESS] ReAct Agent loop executed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Error during ReAct loop execution: {e}")

if __name__ == "__main__":
    test_flight_agent()
