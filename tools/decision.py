from typing import Literal

from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command

from state import ApplicationState

@tool
def make_decision(
    decision: Literal["hire", "reject", "hold"],
    feedback: str,
    runtime: ToolRuntime[None, ApplicationState],
) -> Command:
    """Make the final hiring decision and conclude the interview process.
    
    Use this tool to record your final decision after reviewing all
    the applicant's information and assessment results.
    
    Args:
        decision: Your final decision
                 - "hire": Extend an offer to the candidate
                 - "reject": Do not proceed with the candidate
                 - "hold": Keep candidate in consideration for later
        feedback: Constructive feedback for the applicant explaining
                 the decision and any suggestions for improvement
    """

    decision_messages = {
        "hire": "Congratulations! The candidate has been approved for hire",
        "reject": "The candidate has not been selected to proceed",
        "hold": "The candidate has been placed on hold for future consideration."
    }

    return Command(
        update = {
            "decision": decision,
            "feedback": feedback,
            "current_step": "complete",
            "messages": [
                ToolMessage(
                    content=f"Decision recorded: {decision.upper()}. {decision_messages[decision]}",tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )


@tool
def request_reassessment(
    reason: str,
    runtime: ToolRuntime[None, ApplicationState],
) -> Command:
    """Request additional technical assessment before making a decision.
    
    Use this tool if you need more information to make a fair decision.
    The candidate will be transferred back to the technical assessor
    for additional evaluation.
    
    Args:
        reason: Why additional assessment is needed (e.g., "Need to evaluate frontend skills" or "Want to clarify system design approach")
    """

    return Command(
        update={
            "reason": reason,
            "current_step" : "assessment",
            "messages": [
                ToolMessage(
                    content = f"Reassessmen requested: {reason}. Returning to technical assessment for additional evaluation",
                    tool_call_id = runtime.tool_call_id
                )
            ]
        }
    )


DECISION_TOOLS = [make_decision, request_reassessment]