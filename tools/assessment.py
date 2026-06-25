from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command

from state import ApplicationState


@tool
def record_assessment(
    skill_score: int,
    assessment_notes: str,
    runtime: ToolRuntime[None, ApplicationState]
) -> Command:
    """Record technical assessment results and transfer to hiring manager.
    
    Use this tool after you have asked your technical questions and
    evaluated the candidate's responses. This will save your assessment
    and connect them with the hiring manager for a final decision.
    
    Args:
        skill_score: Technical skill score from 1-10
                    (1-3: Below requirements, 4-6: Partial, 7-8: Meets, 9-10: Exceeds)
        assessment_notes: Key observations about the candidate's technical abilities, strengths, and areas of concern
    """

    # Validate score range
    if skill_score < 1:
        skill_score = 1
    elif skill_score > 10:
        skill_score = 10

    return Command(
        update = {
            "skill_score": skill_score,
            "assessment_notes": assessment_notes,
            "current_step": "decision",
            "messages": [
                ToolMessage(
                    content = f"Assessment recorded (Score: {skill_score}/10). Transferring to hiring manager for final decision",
                    tool_call_id = runtime.tool_call_id,
                )
            ]
        }
    )


ASSESSMENT_TOOLS = [record_assessment]