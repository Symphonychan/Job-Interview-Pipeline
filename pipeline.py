from typing import Callable

from langchain.agents import create_agent
from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse, before_model
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from state import ApplicationState
from config import STEP_CONFIG
from tools import ALL_TOOLS

from langchain.messages import ToolMessage, AIMessage, HumanMessage
from langgraph.runtime import Runtime

# ===========================================
# MIDDLEWARE
# ===========================================

HANDOFF_TOOLS = [
    "record_applicant_info",
    "record_assessment",
    "make_decision",
    "request_reassessment",
]

@wrap_model_call
def apply_step_config(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    
    """Middleware that configures the agent based on current step.
    
    This is the heart of the Handoffs pattern implementation.
    It reads the current_step from state and applies the corresponding
    prompt and tools, effectively changing the agent's "persona".
    """

    current_step = request.state.get("current_step", "intake")

    step_config = STEP_CONFIG.get(current_step, STEP_CONFIG["intake"])

    # Validate requried state fields exist
    for required_field in step_config.get("requires", []):
        if request.state.get(required_field) is None:
            raise ValueError(
                f"Missing required field '{required_field}' for step '{current_step}'. This usually means a previous step didn't complete properly"
            )
        
    prompt_template = step_config["prompt"]

    try:
        formatted_prompt = prompt_template.format(
            applicant_name=request.state.get("applicant_name", "the applicant"),
            role=request.state.get("role", "the position"),
            years_experience=request.state.get("years_experience", "N/A"),
            background_summary=request.state.get("background_summary", "Not provided"),
            skill_score=request.state.get("skill_score", "Not assessed"),
            assessment_notes=request.state.get("assessment_notes", "No notes"),
            decision=request.state.get("decision", "Pending"),
            feedback=request.state.get("feedback", ""),
        )
    except KeyError:
        formatted_prompt = prompt_template

    # Override request with step-specific configuration
    request = request.override(
        system_prompt = formatted_prompt,
        tools = step_config["tools"]
    )

    return handler(request)

@before_model(can_jump_to=["end"])
def end_turn_after_handoff(state, runtime: Runtime):
    messages = state["messages"]
    print(f"[gate] called, last msg type: {type(messages[-1]).__name__}")

    tool_call_ids_in_this_turn = set()
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            break
        if isinstance(msg, ToolMessage):
            tool_call_ids_in_this_turn.add(msg.tool_call_id)

    print(f"[gate] tool_call_ids in turn: {tool_call_ids_in_this_turn}")

    if not tool_call_ids_in_this_turn:
        return None

    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            break
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                print(f"[gate] checking tc name={tc['name']} id={tc['id']}")
                if tc["id"] in tool_call_ids_in_this_turn and tc["name"] in HANDOFF_TOOLS:
                    print(f"[gate] >>> JUMPING TO END <<<")
                    return {"jump_to": "end"}

    print(f"[gate] no handoff matched, continuing")
    return None

def create_application_pipeline(
        model_name: str = "openai:gpt-4o-mini",
        use_memory: bool = True
):
    """Create the job application pipeline agent.
    
    Args:
        model_name: The LLM to use (e.g., "openai:gpt-4o-mini", "anthropic:claude-3-sonnet")
        use_memory: Whether to enable conversation memory via checkpointing
        
    Returns:
        Configured agent that handles the full application pipeline
    """

    model = init_chat_model(model_name)

    pipeline = create_agent(
        model, 
        tools = ALL_TOOLS,
        state_schema = ApplicationState,
        middleware= [apply_step_config, end_turn_after_handoff],
        checkpointer = InMemorySaver() if use_memory else None
    )

    return pipeline


def get_current_state(pipeline, thread_id: str = "default") -> dict:
    """Get the current state of an interview.
    
    Args:
        pipeline: The pipeline instance
        thread_id: Conversation thread ID
        
    Returns:
        Current state dictionary
    """

    config = {"configurable": {"thread_id": thread_id}}

    state = pipeline.get_state(config)

    return state.values if state else {}


def print_state_summary(state: dict): 
    """Print a summary of the current application state."""
    print("\n" + "=" * 50)
    print("APPLICATION STATE SUMMARY")
    print("=" * 50)
    print(f"Current Step: {state.get('current_step', 'intake')}")
    print("-" * 50)
    
    if state.get("applicant_name"):
        print(f"Applicant: {state.get('applicant_name')}")
        print(f"Role: {state.get('role')}")
        print(f"Experience: {state.get('years_experience')} years")
        print(f"Background: {state.get('background_summary', 'N/A')[:100]}...")
    
    if state.get("skill_score"):
        print("-" * 50)
        print(f"Skill Score: {state.get('skill_score')}/10")
        print(f"Assessment: {state.get('assessment_notes', 'N/A')[:100]}...")
    
    if state.get("decision"):
        print("-" * 50)
        print(f"Decision: {state.get('decision', 'N/A').upper()}")
        print(f"Feedback: {state.get('feedback', 'N/A')[:100]}...")
    
    print("=" * 50 + "\n")