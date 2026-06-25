from typing import Literal
from typing_extensions import NotRequired
from langchain.agents import AgentState

ApplicationStep = Literal["intake", "assessment", "decision", "complete"]

HiringDecision = Literal["hire", "reject", "hold"]

class ApplicationState(AgentState):

    current_step: ApplicationStep = "intake"

    # Intake data (set by Recruiter)
    applicant_name: NotRequired[str]
    role: NotRequired[str]
    years_experience: NotRequired[int]
    background_summary: NotRequired[str]

    # Assessment data (set by Technical Assessor)
    skill_score: NotRequired[int]
    assessment_notes: NotRequired[str]

    # Decision data (set by Hiring Manager)
    decision: NotRequired[HiringDecision]
    feedback: NotRequired[str]
    reason: NotRequired[str]