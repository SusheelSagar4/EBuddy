# ADR-0003: Deterministic Engine Core vs Generative LLM Separation

## Status
Accepted (2026-11-14)

## Context
Generative LLMs are prone to hallucinations, non-deterministic plan generation, and subtle rule violations when attempting to schedule complex university degree curricula with recursive prerequisites and strict credit limits.

## Decision
1. All core academic planning, rule checking, prerequisite DAG resolution, and credit calculations are delegated to deterministic Python engine modules in `app/engine/`:
   - `rules.py` (RuleEngine)
   - `planner.py` (Planner)
   - `validator.py` (PlanValidator)
   - `skill_state.py` (SkillStateUpdater)
   - `mastery.py` (MasteryEvaluator)
2. The LLM is restricted to human interaction tasks: intent classification, generating conversational explanations, and evaluating free-text student responses against rubrics.
3. Every LLM output is schema-validated; any course code returned by an LLM is validated against `kb.course`.

## Consequences
### Positive
- Academic plans are 100% compliant with IIT BBS curriculum rules and mathematically sound.
- Testing is rapid, deterministic, and free of token expenditures.

### Negative
- Requires maintaining explicit algorithmic implementations for curriculum scheduling and prerequisite traversal.

