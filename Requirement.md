# Flight Booking Agent Requirements

## 1. Purpose

`FlightAgent.py` shall provide a command-line, LLM-driven flight booking demonstration. The agent shall interpret a user's request, use native Groq function calling to search for flights or book a known flight, and present the final outcome.

The current implementation uses static mock flight and booking data; it does not connect to airline, travel-provider, payment, or reservation systems.

## 2. Prerequisites

- Python 3.10 or later.
- The `groq` and `python-dotenv` packages installed.
- A Groq API key supplied through the `GROQ_API_KEY` environment variable, optionally loaded from a `.env` file in the working directory.
- Access to the configured Groq-compatible model (`openai/gpt-oss-20b` by default).

## 3. Functional Requirements

### FR-1: Agent initialization

- The application shall expose a `NativeFlightBookingAgent` class.
- The class shall accept a model name, a mapping of executable tools, and matching native Groq tool schemas.
- The agent shall initialize conversation memory with a system instruction that identifies it as a flight booking agent.

### FR-2: User-request processing

- `run(task, max_loops=5)` shall add the supplied task to the conversation memory and request a chat completion from Groq.
- Each completion request shall include the current memory, configured tool schemas, `tool_choice="auto"`, and a low temperature (`0.1`).
- The agent shall run for at most `max_loops` iterations.

### FR-3: Flight search

- The agent shall use `search_flights(destination, date)` when a flight ID is not already known and the user asks to find or search for flights.
- `destination` shall accept a city name or airport code.
- `date` shall be supplied in `YYYY-MM-DD` format.
- The search tool shall return JSON containing the mock flight options, including flight ID, airline, price, and departure time.

### FR-4: Flight booking

- When a user request includes a specific flight ID, the agent shall invoke `book_flight(flight_id)` directly rather than searching first.
- The booking tool shall return JSON containing the requested flight ID, a `Confirmed` status, and the mock confirmation code `FLY-XY789`.
- The tool does not validate that the supplied flight ID is present in the search results.

### FR-5: Tool-execution cycle

- When Groq returns tool calls, the agent shall append the assistant message to memory, execute each requested mapped function with its JSON arguments, and append the result as a `tool` message associated with that tool-call ID.
- When the model returns no tool calls, the agent shall print the model's response as the final result and stop processing.
- The application shall print task, loop, tool-call, observation, and final-response information to standard output for demonstration and troubleshooting.

## 4. Tool Contract

| Tool | Required inputs | Output |
| --- | --- | --- |
| `search_flights` | `destination` (string), `date` (string) | JSON array of mock available flights |
| `book_flight` | `flight_id` (string) | JSON booking confirmation |

## 5. Example Invocation

Run the script directly:

```bash
python FlightAgent.py
```

The bundled example asks the agent to find the cheapest flight to Paris (CDG) on `2026-07-15` and book it when the price is below `$500`.

## 6. Current Constraints and Out of Scope

- Flight availability, prices, and confirmations are hard-coded sample data.
- The application does not independently determine or enforce the user's price condition; it relies on the model to select the appropriate tool actions.
- No input validation, authentication beyond the Groq API key, payment processing, passenger details, cancellation, modification, or persistent booking storage is implemented.
- Unknown tool names, invalid tool JSON, Groq API failures, and loop-limit exhaustion are not explicitly handled by the script.
- Conversation memory remains in process only and is retained for the lifetime of the agent instance.
