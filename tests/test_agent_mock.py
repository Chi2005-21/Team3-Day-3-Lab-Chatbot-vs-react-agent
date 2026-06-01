import os
import sys

# Add src directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.llm_provider import LLMProvider
from src.agent.agent import ReActAgent

class MockLLMProvider(LLMProvider):
    def __init__(self):
        super().__init__(model_name="mock-react-llm")
        self.step_count = 0

    def generate(self, prompt: str, system_prompt: str = None) -> dict:
        self.step_count += 1
        
        if self.step_count == 1:
            content = (
                "Thought: The user wants to find comfort/productivity flight options, details for 'BA 191', and countdown for 'BA 303'. "
                "First, I must find the most productivity-friendly flight options.\n"
                "Action: find_productivity_flights()"
            )
        elif self.step_count == 2:
            content = (
                "Thought: Now I need to retrieve the complete itinerary details for flight 'BA 191'.\n"
                "Action: parse_flight_details(flight_number=\"BA 191\")"
            )
        elif self.step_count == 3:
            content = (
                "Thought: Now I need to calculate how much time is left before flight 'BA 303' departs if the current reference time is '2026-03-03 08:30'.\n"
                "Action: time_until_flight(flight_number=\"BA 303\", current_time_str=\"2026-03-03 08:30\")"
            )
        else:
            content = (
                "Thought: I have gathered all flight details and solved all parts of the user request.\n"
                "Final Answer: Here is the comprehensive travel summary:\n\n"
                "1. **Productivity Flights**: The top comfort flight scored 250 (Air France / Delta segments) offering Wi-Fi and in-seat power.\n"
                "2. **Itinerary for BA 191**: This is a British Airways route with two legs (CDG -> LHR on BA 301, and LHR -> AUS on BA 191 using an Airbus A350).\n"
                "3. **Departure countdown**: Flight BA 303 departing from CDG is in 3 hours and 25 minutes relative to the 2026-03-03 08:30 reference time."
            )
            
        return {
            "content": content,
            "latency_ms": 150,
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200
            }
        }

    def stream(self, prompt: str, system_prompt: str = None):
        yield "Not implemented"

def test_mock_agent():
    print("=== Initializing Mock LLM Provider ===")
    llm = MockLLMProvider()
    
    tools_metadata = [
        {
            "name": "find_productivity_flights",
            "description": "Scores and ranks flight routes from the database based on productivity-enabling comforts."
        },
        {
            "name": "time_until_flight",
            "description": "Calculates the duration remaining until a flight departs. Usage: time_until_flight(flight_number, current_time_str)"
        },
        {
            "name": "parse_flight_details",
            "description": "Parses segment itinerary details. Usage: parse_flight_details(flight_number)"
        },
        {
            "name": "get_current_time",
            "description": "Returns the current local date and time."
        }
    ]

    print("\n=== Initializing ReAct Agent ===")
    agent = ReActAgent(llm=llm, tools=tools_metadata, max_steps=10)
    
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
        print("\n[SUCCESS] ReAct Agent Mock loop executed successfully!")
    except Exception as e:
        print(f"\n[ERROR] Error during ReAct loop execution: {e}")

if __name__ == "__main__":
    test_mock_agent()
