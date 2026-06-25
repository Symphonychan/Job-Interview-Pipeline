from langchain.tools import tool, ToolRuntime
from langchain.messages import ToolMessage
from langgraph.types import Command

from state import ApplicationState

@tool
def record_applicant_info(
    name: str,
    role: str,
    years_experience: int,
    background_summary: str,
    runtime: ToolRuntime[None, ApplicationState]
) -> Command:
    """Record applicant information and transfer to technical assessment.
    
    Use this tool once you have gathered all the required information
    from the applicant. This will save their details and connect them
    with the technical assessor.
    
    Args:
        name: Applicant's full name
        role: Position they're applying for
        years_experience: Years of relevant experience
        background_summary: Brief summary of their background and key skills
    """

    return Command(
        update = {
            "applicant_name": name,
            "role": role,
            "years_experience": years_experience,
            "background_summary": background_summary,
            "current_step": "assessment",
            "messages": [
                ToolMessage(
                    content = f"Recorded information for {name} applying for {role}. Transferring to technical assessment",
                    tool_call_id=runtime.tool_call_id
                )
            ]
        }
    )


INTAKE_TOOLS = [record_applicant_info]