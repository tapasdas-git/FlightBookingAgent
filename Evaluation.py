import os
import json
from groq import Groq
from FlightAgent  import NativeFlightBookingAgent, available_tools, groq_tools_schema
from dotenv import load_dotenv
# Assuming your agent code from earlier is saved as flight_agent.py
# from flight_agent import NativeFlightBookingAgent, available_tools, groq_tools_schema

# Initialize the Groq Client
load_dotenv()
# Initialize Groq client
#client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
client=Groq(api_key=os.getenv('GROQ_API_KEY'))

# 2. DEFINING THE GOLDEN DATASET
GOLDEN_DATASET = [
    {
        "id": "TC_01_STANDARD_FLOW",
        "name": "Standard Flight Search and Book",
        "prompt": "Find the cheapest flight to Paris (CDG) for 2026-07-15. If it's under $500, book it.",
        "expected_behavior": "Should call search_flights, identify the $450 flight, and then call book_flight.",
        "expected_final_status": "Confirmed"
    },
    {
        "id": "TC_02_OVER_BUDGET",
        "name": "Flight Exceeds Specified Budget Limit",
        "prompt": "Find the cheapest flight to London (LHR) for 2026-08-20. If it's under $300, book it.",
        "expected_behavior": "Should call search_flights, find no flights under $300, and terminate WITHOUT booking.",
        "expected_final_status": "Not Booked"
    },
    {
        "id": "TC_03_DIRECT_BOOKING",
        "name": "Direct Booking via Flight ID (Skip Search)",
        "prompt": "book a flight to Paris (CDG) for 2026-07-15. flight ID UA-904.",
        "expected_behavior": "Should call book_flight immediately and NEVER call search_flights.",
        "expected_final_status": "Confirmed"
    }
]

# 3. THE LLM EVALUATOR JUDGE
def evaluate_with_llm_judge(task_prompt, agent_trajectory, final_response):
    """
    Uses a strong LLM to review the agent history and score compliance.
    Cleans up custom Groq message objects so they serialize flawlessly.
    """
    # Clean the trajectory to make sure it contains only serializable standard dicts
    cleaned_trajectory = []
    for msg in agent_trajectory:
        if hasattr(msg, "model_dump"):
            # Native Groq/Pydantic objects have a built-in method to convert to plain dicts
            cleaned_trajectory.append(msg.model_dump())
        elif isinstance(msg, dict):
            cleaned_trajectory.append(msg)
        else:
            cleaned_trajectory.append({"role": "unknown", "content": str(msg)})

    judge_prompt = f"""
    You are an AI Quality Assurance Inspector. Review this Flight Agent performance loop:
    
    [USER TASK]: {task_prompt}
    [AGENT TRAJECTORY]: {json.dumps(cleaned_trajectory, indent=2)}
    [FINAL RESPONSE]: {final_response}

    Output a JSON object matching this schema exactly:
    {{
        "tool_selection_score": 1 to 5,
        "constraint_respect_score": 1 to 5,
        "hallucination_detected": true/false,
        "reasoning": "Short explanation of grading"
    }}
    """
    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": judge_prompt}],
        response_format={"type": "json_object"},
        temperature=0.0
    )
    return json.loads(response.choices[0].message.content)

# 4. RUNNING THE EVALUATION WORKFLOW
def run_evaluation_suite():
    report_card = []
    
    print("📊 Starting Evaluation Suite using inherited tools from FlightAgent...")
    print("=" * 70)

    for case in GOLDEN_DATASET:
        print(f"\n▶ Running Test Case: {case['id']} - {case['name']}")
        
        # Array to capture tool execution telemetry
        tracked_tool_calls = []

        # INSTRUMENTATION LAYER: Wrap the imported tools dynamically to track usage
        spy_tools = {}
        for tool_name, original_function in available_tools.items():
            # We create a wrapper function that records the event, then fires the real tool
            def make_wrapper(name, func):
                def wrapper(*args, **kwargs):
                    tracked_tool_calls.append({"tool": name, "args": kwargs if kwargs else args})
                    return func(*args, **kwargs)
                return wrapper
            
            spy_tools[tool_name] = make_wrapper(tool_name, original_function)

        # Instantiate your actual Agent using the inherited class and schemas!
        agent = NativeFlightBookingAgent(
            model_name="openai/gpt-oss-20b", 
            tools=spy_tools,                # Pass our tracked wrapped spy tools
            tools_schema=groq_tools_schema  # Directly pass the inherited schema
        )
        
        # Execute the Agent Loop
        agent.run(task=case["prompt"], max_loops=5)
        
        # Analyze data artifacts post-execution
        full_memory = agent.memory
        final_msg = full_memory[-1].get("content", "") if isinstance(full_memory[-1], dict) else str(full_memory[-1])
        
        print(f"⚖️ Evaluating Trajectory with LLM Judge...")
        judge_metrics = evaluate_with_llm_judge(case["prompt"], full_memory, final_msg)
        
        # Document compiled metrics
        test_summary = {
            "test_id": case["id"],
            "name": case["name"],
            "total_loops_run": len([m for m in full_memory if isinstance(m, dict) and m.get('role') == 'tool']),
            "tools_called_sequence": tracked_tool_calls,
            "judge_assessment": judge_metrics
        }
        report_card.append(test_summary)

    # Print Final Dashboard Report Card
    print("\n" + "="*30 + " EVALUATION REPORT MATRIX " + "="*30)
    print(json.dumps(report_card, indent=4))

if __name__ == "__main__":
    run_evaluation_suite()