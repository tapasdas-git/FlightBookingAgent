import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
# Initialize Groq client
#client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client=Groq(api_key=os.getenv('GROQ_API_KEY'))

# =====================================================================
# 1. DEFINE THE FLIGHT FUNCTIONS
# =====================================================================
def search_flights(destination: str, date: str) -> str:
    print(f"   [Tool Executing] Searching flights to {destination} on {date}...")
    return json.dumps([
        {"flight_id": "AF-102", "airline": "Air France", "price": 450.00, "departure": "10:00 AM"},
        {"flight_id": "UA-904", "airline": "United", "price": 620.00, "departure": "2:30 PM"},
        {"flight_id": "IAF-905", "airline": "British Airways", "price": 440.00, "departure": "11:30 AM"}
        
    ])

def book_flight(flight_id: str) -> str:
    print(f"   [Tool Executing] Booking flight {flight_id}...")
    return json.dumps({"status": "Confirmed", "confirmation_code": "FLY-XY789", "flight_id": flight_id})

# Dynamic execution mapper
available_tools = {
    "search_flights": search_flights,
    "book_flight": book_flight
}

# =====================================================================
# 2. DEFINE NATIVE GROQ TOOL SCHEMAS
# =====================================================================
groq_tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": "Searches for available flights to a destination on a specific date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "The airport code or city name, e.g., CDG or Paris"},
                    "date": {"type": "string", "description": "The date of travel in YYYY-MM-DD format"}
                },
                "required": ["destination", "date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "book_flight",
            "description": "Books a flight using its specific flight ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_id": {"type": "string", "description": "The unique identifier of the flight to book"}
                },
                "required": ["flight_id"]
            }
        }
    }
]

# =====================================================================
# 3. DEFINE THE NATIVE FLIGHT AGENT
# =====================================================================
class NativeFlightBookingAgent:
    def __init__(self, model_name: str, tools: dict, tools_schema: list):
        self.model_name = model_name
        self.tools = tools
        self.tools_schema = tools_schema
        self.system_prompt = (
            "You are an autonomous Flight Booking Agent. Your goal is to help users find and book flights. "
            "CRITICAL DIRECTIVE:\n"
            "- If the user's request already contains a specific Flight ID (e.g., 'UA-904'), "
            "do NOT call search_flights. Proceed directly to calling book_flight using that ID.\n"
            "- Only use search_flights if no flight ID is known yet. or the user request is to search or find for flights.\n"
            "proceed to book it. When completely done, summarize your final outcome to the user."
        )
        self.memory = [{"role": "system", "content": self.system_prompt}]

    def run(self, task: str, max_loops: int = 5):
        print(f"🤖 Flight Agent Initialized.\n🚀 Task: {task}\n" + "="*60)
        self.memory.append({"role": "user", "content": task})
        
        for step in range(1, max_loops + 1):
            print(f"\n--- [LOOP ITERATION {step}] ---")
            
            # 1. Ask the LLM Brain (Passing tools via the native tools parameter!)
            response = client.chat.completions.create(
                model=self.model_name,
                messages=self.memory,
                tools=self.tools_schema,
                tool_choice="auto",
                temperature=0.1
            )
            
            response_message = response.choices[0].message
            print(f"🤖 Response Message.\n🚀 Response: {response_message}\n" + "="*60)
            tool_calls = response_message.tool_calls
            print(f"🤖 Tool Call.\n🚀 Tool: {response_message.tool_calls}\n" + "="*60)
            
            # 2. REASON / THINK: Check if the model wants to call a tool
            if tool_calls:
                # Add assistant message containing the tool calls request to memory
                self.memory.append(response_message)
                
                # 3. ACT: Execute the requested tool calls
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool map
                    observation = self.tools[function_name](**function_args)
                    print(f"📊 OBSERVATION (Result): {observation}")
                    
                    # Send the tool result back into the memory using native tool role
                    self.memory.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": observation,
                    })
            else:
                # No more tools called -> This is our Final Answer
                print(f"\n✅ Success! Task completed in {step} loops.")
                print(f"📢 FINAL RESPONSE:\n{response_message.content}")
                break

# =====================================================================
# 4. EXECUTION
# =====================================================================
if __name__ == "__main__":
    agent = NativeFlightBookingAgent(
        model_name="openai/gpt-oss-20b", 
        tools=available_tools, 
        tools_schema=groq_tools_schema
    )
    
    user_request = "Find the cheapest flight to Paris (CDG) for 2026-07-15. If it's under $500, go ahead and book it."
    #user_request = "book a flight to Paris (CDG) for 2026-07-15. flight ID UA-904."
    agent.run(task=user_request)