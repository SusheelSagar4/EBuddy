from typing import Optional, Dict, Any, Literal
from datetime import datetime
from app.contracts.base import BaseContract

ProposalStatus = Literal[
    'pending_student_approval',
    'approved',
    'rejected',
    'committed',
    'validation_failed'
]

ProposalType = Literal[
    'resource_swap',
    'remediation_insertion',
    'workload_reduction',
    'pace_change',
    'schedule_shift',
    'goal_pivot'
]

ProposerAgent = Literal[
    'agent_2_resource',
    'agent_3_assessment',
    'agent_4_query'
]

class ChangeProposal(BaseContract):
    proposal_id: str
    student_id: str
    proposer_agent: str # agent_2_resource, agent_3_assessment, agent_4_query
    proposal_type: str # resource_swap, remediation_insertion, workload_reduction, pace_change, schedule_shift, goal_pivot
    status: ProposalStatus = 'pending_student_approval'
    reasoning: str
    target_week: Optional[int] = None
    target_semester: Optional[int] = None
    proposed_modifications: Dict[str, Any]
    impact_summary: str
    student_feedback: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

