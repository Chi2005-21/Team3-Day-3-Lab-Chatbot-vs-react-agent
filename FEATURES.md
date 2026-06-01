## Use Case & Tools
### Use Case

**Alex, a digital nomad and software engineer**, is currently working out of a cafe in Paris (CDG) and needs to fly to Austin, Texas (AUS) for an upcoming conference. He has three core needs:
1. **Comfort & Connectivity**: He must work during the journey, so he wants a flight with robust Wi-Fi, USB or power outlets, and comfortable legroom (no cramped seating).
2. **Itinerary Auditing**: He needs to review detailed flight schedules, aircraft models, layovers, and total price to ensure his travel expenses will be approved by his company.
3. **Time Management**: On the day of departure, he wants to track exactly how much time he has left in his current location before his flight departs so he can manage his coding tasks.

**How the Agent Assistant resolves Alex's problem**:
* **Step 1: Finding Productivity Flights**: Alex asks the agent to find comfort-optimized flights. The agent calls `find_productivity_flights()` to score flights based on Wi-Fi, power, legroom, and layovers. It recommends a British Airways option (Score: 85/100) due to in-seat power, Wi-Fi accessibility, and average legroom.
* **Step 2: Checking Itinerary Specifics**: Alex asks to see the segment breakdown of the recommended route. The agent calls `parse_flight_details(flight_number="BA 191")` to present a clean, detailed breakdown of the Heathrow (LHR) layover, total travel time, and aircraft type.
* **Step 3: Departure Countdown**: On departure morning, Alex asks the agent, *"How much time do I have left before my flight BA 303 departs?"* The agent runs `time_until_flight(flight_number="BA 303", current_time_str="2026-03-03 08:30")` and responds, *"Your flight BA 303 departs in 3 hours and 25 minutes (at 11:55 AM), giving you ample time to wrap up your morning standup."*

### [NEW] [flight_tools.py](d:/Personlich/AIO/AIO2025%20-%20Main/_2026_Research/VIN%20Practitioner/Team3-Day-3-Lab-Chatbot-vs-react-agent/src/tools/flight_tools.py)
We will implement three specialized, robust Python functions decorated or marked for Agent tool usage:

1. **`find_productivity_flights(local_data_path: str = "data.json") -> str`**
   - **Purpose**: "Digital Nomad's Productivity Finder".
   - **Algorithm**: Inspects the `extensions` array for each leg of a flight:
     - `Free Wi-Fi` (+30 pts), `Wi-Fi for a fee` (+15 pts)
     - `In-seat power` or `USB` outlets (+30 pts)
     - `Legroom` (+15 pts for >30", -15 pts for <30")
     - Penalizes overnight layovers (`overnight: true`, -30 pts) and long layovers.
   - **Return**: A formatted JSON list of flights sorted by their comfort/productivity score.

2. **`time_until_flight(flight_number: str, current_time_str: str = "2026-03-03 06:00", local_data_path: str = "data.json") -> str`**
   - **Purpose**: Calculate how much time is left until departure.
   - **Logic**: Searches for `flight_number` (e.g., `BA 301`) in the dataset. Computes the time difference between the flight departure time and the reference `current_time_str`.
   - **Return**: A human-friendly explanation of time remaining (or elapsed if in the past).

3. **`parse_flight_details(flight_number: str, local_data_path: str = "data.json") -> str`**
   - **Purpose**: Extract full routing, aircraft, price, layover details, and emissions for a selected flight number.
   - **Return**: Detailed breakdown of the flight segments, airports, and price.
