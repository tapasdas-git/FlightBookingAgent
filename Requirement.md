Find the cheapest flight to Paris for next Tuesday, and if it's under $500, book it."

LLM (Reasoning): "First, I need to look up flights."

Action 1: Calls search_flights(destination="CDG", date="2026-07-07").

Observation 1: Tool returns a list. The cheapest flight is $450.

LLM (Reasoning): "The cheapest flight is $450. This is under the user's $500 limit. Now I need to proceed with booking."

Action 2: Calls book_flight(flight_id="AF123", passenger_details="...").

Observation 2: Tool returns Booking Confirmed: Code XY789.

LLM (Final Answer): "I found a flight for $450 and successfully booked it for you. Your confirmation code is XY789."

Why it's an Agent: The LLM actively evaluated the result of the first tool call ($450), checked it against a rule ($500), changed its state, and autonomously decided to trigger a second, completely different tool call to finish the job.