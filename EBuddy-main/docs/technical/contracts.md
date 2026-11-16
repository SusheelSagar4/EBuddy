# Domain Contracts & Schemas Specification (v1.0.0)

This document formalizes the frozen, immutable domain contracts defined in `app/contracts/`.

## Governance Rules
1. **Contract Immutability:** Contracts are frozen Pydantic v2 models. Any structural modification requires a PR labelled `contract-change`, a version bump in `app/contracts/VERSION`, and an entry in `docs/CHANGELOG.md`.
2. **Knowledge Base Attribution:** Every contract wrapping data from the knowledge base (`Course`, `AcademicRule`, `Skill`, `Goal`, `Resource`, `ResearchProject`) carries `status` (`verified`, `draft_for_review`, `unsourced_baseline`), `source_id`, and `verified: bool`.
3. **Course Identity Citation:** Systems and planners communicate internally using unique surrogate `course_id`. When presenting to students, they cite `display_code` + `title`. Clashing course codes (e.g. `ML4L001`) cite both titles with a visible `[NOTE: Code conflict]` indicator.
4. **Institutional Guardrail:** The buddy strictly refuses to hallucinate dates, fees, cut-offs, or credit limits that are not present in a `verified` record. Any unverified item is surfaced as an advisory or `not confirmed yet`, referencing the official IIT Bhubaneswar administration.

---

## Contract Inventory

| Category | Contract Name | Module | JSON Schema | Description |
|---|---|---|---|---|
| **Student** | `StudentProfile` | `app.contracts.student` | [`StudentProfile.json`](../contracts/StudentProfile.json) | Core student record (programme, semester, CGPA, backlogs, synthetic flag). |
| | `EvidenceItem` | `app.contracts.student` | [`EvidenceItem.json`](../contracts/EvidenceItem.json) | Append-only ledger record for assessments, quizzes, and grade evidence. |
| | `SkillState` | `app.contracts.student` | [`SkillState.json`](../contracts/SkillState.json) | Current estimated mastery level and confidence for a specific skill. |
| | `Constraint` | `app.contracts.student` | [`Constraint.json`](../contracts/Constraint.json) | Hard/soft limits on weekly study hours, credit overloads, or timing. |
| | `Preference` | `app.contracts.student` | [`Preference.json`](../contracts/Preference.json) | Student learning preferences (e.g. video vs textbook, paced vs intensive). |
| **Goal** | `Goal` | `app.contracts.goal` | [`Goal.json`](../contracts/Goal.json) | Career track, higher studies path, competitive exam, or startup goal. |
| | `GoalRequirement` | `app.contracts.goal` | [`GoalRequirement.json`](../contracts/GoalRequirement.json) | Skill level targets and relative importance required to achieve a goal. |
| | `MasteryCriteria` | `app.contracts.goal` | [`MasteryCriteria.json`](../contracts/MasteryCriteria.json) | Quantitative standards distinguishing 'completion' from demonstrated proficiency. |
| | `Milestone` | `app.contracts.goal` | [`Milestone.json`](../contracts/Milestone.json) | Semester-wise project, internship, or exam milestone. |
| **Knowledge Base** | `Course` | `app.contracts.kb` | [`Course.json`](../contracts/Course.json) | Course entity with surrogate `course_id`, `display_code`, and `code_conflict`. |
| | `Module` | `app.contracts.kb` | [`Module.json`](../contracts/Module.json) | Syllabus breakdown module linked to courses. |
| | `Resource` | `app.contracts.kb` | [`Resource.json`](../contracts/Resource.json) | NPTEL / open learning resources with coverage status and link verification. |
| | `Exercise` | `app.contracts.kb` | [`Exercise.json`](../contracts/Exercise.json) | Active practice questions (MCQ, numeric, short-answer, projects). |
| | `AcademicRule` | `app.contracts.kb` | [`AcademicRule.json`](../contracts/AcademicRule.json) | Ordinance rules governing credit caps, overloading, and minors. |
| | `ResearchProject` | `app.contracts.kb` | [`ResearchProject.json`](../contracts/ResearchProject.json) | Institutional research projects with detail level and grant scope. |
| | `Skill` | `app.contracts.kb` | [`Skill.json`](../contracts/Skill.json) | Skill taxonomy definition with 0-100 level scale and domain. |
| **Planning** | `StructuredReason` | `app.contracts.plan` | — | Structured justification for every plan recommendation. |
| | `PlanItem` | `app.contracts.plan` | [`PlanItem.json`](../contracts/PlanItem.json) | Individual scheduled course, exercise, resource, or remediation item. |
| | `ValidationReport` | `app.contracts.plan` | [`ValidationReport.json`](../contracts/ValidationReport.json) | Deterministic validator output containing per-rule checks and status. |
| | `PlanDiff` | `app.contracts.plan` | [`PlanDiff.json`](../contracts/PlanDiff.json) | Explainable diff between previous and newly adapted study plan. |
| | `Plan` | `app.contracts.plan` | [`Plan.json`](../contracts/Plan.json) | Full versioned learning plan. |
| **Conversation** | `Intent` | `app.contracts.chat` | — | Enumeration of classified student conversation intents. |
| | `ContextCard` | `app.contracts.chat` | [`ContextCard.json`](../contracts/ContextCard.json) | Structured payload supplied to LLM containing facts, gaps, and strict disclaimers. |
| | `ChatTurn` | `app.contracts.chat` | [`ChatTurn.json`](../contracts/ChatTurn.json) | Single audited interaction turn with student. |
| | `Explanation` | `app.contracts.chat` | [`Explanation.json`](../contracts/Explanation.json) | Plain-language rationales and citations. |
| **Plugin** | `PersonaSpec` | `app.contracts.persona` | [`PersonaSpec.json`](../contracts/PersonaSpec.json) | Self-contained specification defining a persona plugin. |

