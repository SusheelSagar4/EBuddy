from app.contracts.student import StudentProfile, EvidenceItem, SkillState, Constraint, Preference
from app.contracts.goal import Goal, GoalRequirement, MasteryCriteria, Milestone
from app.contracts.kb import Course, Module, Resource, Exercise, AcademicRule, ResearchProject, Skill
from app.contracts.plan import StructuredReason, PlanItem, ValidationCheck, ValidationReport, PlanDiff, Plan
from app.contracts.chat import Intent, ContextCard, ChatTurn, Explanation
from app.contracts.persona import PersonaSpec
from app.contracts.proposal import ChangeProposal
from app.contracts.roadmap import DailyTask, WeeklyRoadmap, RoadmapVersionRecord

__all__ = [
    "StudentProfile", "EvidenceItem", "SkillState", "Constraint", "Preference",
    "Goal", "GoalRequirement", "MasteryCriteria", "Milestone",
    "Course", "Module", "Resource", "Exercise", "AcademicRule", "ResearchProject", "Skill",
    "StructuredReason", "PlanItem", "ValidationCheck", "ValidationReport", "PlanDiff", "Plan",
    "Intent", "ContextCard", "ChatTurn", "Explanation",
    "PersonaSpec",
    "ChangeProposal", "DailyTask", "WeeklyRoadmap", "RoadmapVersionRecord"
]
