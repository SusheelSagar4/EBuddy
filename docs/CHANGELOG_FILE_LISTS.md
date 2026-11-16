# Changelog: file lists

Compared `61be6e33-EBuddy-main_2.zip` (original upload) with the repository by sha256.

| ADDED | MODIFIED | DELETED | MOVED/RENAMED |
|---|---|---|---|
| 66 | 79 | 116 | 36 |

## ADDED (66)

### app (45)

- `app/api/buddy.py`
- `app/db/persistence.py`
- `app/kb/track_repo.py`
- `app/llm/guardrails.py`
- `app/llm/prompts/answerer_v1.txt`
- `app/llm/prompts/clarifier_v1.txt`
- `app/llm/prompts/grader_v1.txt`
- `app/llm/prompts/question_gen_v1.txt`
- `app/llm/tasks/answerer.py`
- `app/personas/aiml_career/README.md`
- `app/personas/aiml_career/diagnostic.yaml`
- `app/personas/aiml_career/mastery.yaml`
- `app/personas/aiml_career/milestones.yaml`
- `app/personas/aiml_career/persona.yaml`
- `app/personas/aiml_career/policy.py`
- `app/personas/aiml_career/requirements.yaml`
- `app/personas/core_higher_studies/README.md`
- `app/personas/core_higher_studies/diagnostic.yaml`
- `app/personas/core_higher_studies/mastery.yaml`
- `app/personas/core_higher_studies/milestones.yaml`
- `app/personas/core_higher_studies/persona.yaml`
- `app/personas/core_higher_studies/policy.py`
- `app/personas/core_higher_studies/requirements.yaml`
- `app/personas/core_to_mba/README.md`
- `app/personas/core_to_mba/diagnostic.yaml`
- `app/personas/core_to_mba/mastery.yaml`
- `app/personas/core_to_mba/milestones.yaml`
- `app/personas/core_to_mba/persona.yaml`
- `app/personas/core_to_mba/policy.py`
- `app/personas/core_to_mba/requirements.yaml`
- `app/personas/da_career/README.md`
- `app/personas/da_career/diagnostic.yaml`
- `app/personas/da_career/mastery.yaml`
- `app/personas/da_career/milestones.yaml`
- `app/personas/da_career/persona.yaml`
- `app/personas/da_career/policy.py`
- `app/personas/da_career/requirements.yaml`
- `app/personas/sde_career/README.md`
- `app/personas/sde_career/diagnostic.yaml`
- `app/personas/sde_career/mastery.yaml`
- `app/personas/sde_career/milestones.yaml`
- `app/personas/sde_career/persona.yaml`
- `app/personas/sde_career/policy.py`
- `app/personas/sde_career/requirements.yaml`
- `app/services/reprocess_service.py`

### data (14)

- `data/seed/kb/track_phase_skill.csv`
- `data/seed/personas/aiml_career/students.csv`
- `data/seed/personas/core_higher_studies/students.csv`
- `data/seed/personas/core_to_mba/students.csv`
- `data/seed/personas/da_career/students.csv`
- `data/seed/personas/sde_career/students.csv`
- `data/seed/student/completed_course.csv`
- `data/seed/student/constraint.csv`
- `data/seed/student/interest.csv`
- `data/seed/student/preference.csv`
- `data/seed/student/profile_manifest.json`
- `data/seed/student/skill_evidence.csv`
- `data/seed/student/student.csv`
- `data/seed/student/student_goal.csv`

### docker (1)

- `docker/wait_for_db.py`

### docs (2)

- `docs/evaluation/verify_75_profiles_report.json`
- `docs/evaluation/verify_75_profiles_report.md`

### scripts (2)

- `scripts/generate_75_student_profiles.py`
- `scripts/verify_all_75_profiles.py`

### tests (1)

- `tests/test_inter_iit_upgrade.py`

### web (1)

- `web/src/ui.js`

## MODIFIED (79)

### (root) (3)

- `.dockerignore`
- `Makefile`
- `docker-compose.yml`

### aiml (2)

- `aiml/scripts/build_csvs.py`
- `aiml/scripts/build_events_csvs.py`

### app (28)

- `app/agents/agent_1_planner.py`
- `app/agents/agent_4_query.py`
- `app/api/admin.py`
- `app/api/simulator.py`
- `app/api/student.py`
- `app/api/ui_routes.py`
- `app/contracts/VERSION`
- `app/contracts/persona.py`
- `app/contracts/plan.py`
- `app/contracts/student.py`
- `app/engine/diagnostic.py`
- `app/engine/mastery.py`
- `app/engine/planner.py`
- `app/engine/rules.py`
- `app/engine/skill_state.py`
- `app/engine/validator.py`
- `app/llm/client.py`
- `app/llm/tasks/intent_router.py`
- `app/main.py`
- `app/personas/registry.py`
- `app/services/adapt_service.py`
- `app/services/chat_service.py`
- `app/services/diagnostic_service.py`
- `app/services/mastery_service.py`
- `app/services/onboarding_service.py`
- `app/services/plan_service.py`
- `app/services/roadmap_orchestrator.py`
- `app/templates/base.html`

### da (3)

- `da/scripts/build_da_csvs.py`
- `da/scripts/build_da_events_csvs.py`
- `da/scripts/build_da_quiz_csvs.py`

### data (12)

- `data/seed/core_to_mtech/course_topic_map.csv`
- `data/seed/kb/goal.csv`
- `data/seed/kb/goal_skill_requirement.csv`
- `data/seed/kb/module.csv`
- `data/seed/kb/programme_requirement.csv`
- `data/seed/kb/relevance_tags.csv`
- `data/seed/kb/skill.csv`
- `data/seed/kb/source.csv`
- `data/seed/personas/btech_upsc/students.csv`
- `data/seed/personas/ee_power_core/students.csv`
- `data/seed/personas/mme_materials_core/students.csv`
- `data/seed/personas/student_startup/students.csv`

### docker (3)

- `docker/Dockerfile`
- `docker/entrypoint.sh`
- `docker/init.sql`

### docs (7)

- `docs/core_to_core_scorecard.md`
- `docs/core_to_mba_data_quality_report.md`
- `docs/core_to_mba_scorecard.md`
- `docs/core_to_mtech_data_quality_report.md`
- `docs/core_to_mtech_scorecard.md`
- `docs/data_quality_report.md`
- `docs/evaluation/conformance_report.md`

### scripts (2)

- `scripts/generate_core_to_mtech_seeds.py`
- `scripts/seed_loader.py`

### sde (3)

- `sde/scripts/build_sde_csvs.py`
- `sde/scripts/build_sde_events_csvs.py`
- `sde/scripts/build_sde_quiz_csvs.py`

### tests (4)

- `tests/conftest.py`
- `tests/integration/test_curriculum_and_relevance.py`
- `tests/unit/test_startup_plan_adjustments.py`
- `tests/unit/test_upsc_plan_adjustments.py`

### web (12)

- `web/index.html`
- `web/src/api/client.js`
- `web/src/app.js`
- `web/src/design/style.css`
- `web/src/screens/adapt.js`
- `web/src/screens/admin.js`
- `web/src/screens/chat.js`
- `web/src/screens/diagnostic.js`
- `web/src/screens/learn.js`
- `web/src/screens/onboarding.js`
- `web/src/screens/plan.js`
- `web/src/screens/progress.js`

## DELETED (116)

### (root) (17)

- `Data_Analyst_Questions.xlsx`
- `Data_Analyst_Roadmap.xlsx`
- `Data_Analytics_Hackathons.xlsx`
- `LeetCode_DSA_Easy.xlsx`
- `LeetCode_DSA_Hard.xlsx`
- `LeetCode_DSA_Medium.xlsx`
- `build_csvs.py`
- `build_da_csvs.py`
- `build_da_events_csvs.py`
- `build_da_quiz_csvs.py`
- `build_data_analyst_csvs.py`
- `build_data_analyst_events_csvs.py`
- `build_events_csvs.py`
- `build_sde_csvs.py`
- `build_sde_events_csvs.py`
- `build_sde_quiz_csvs.py`
- `docsteamFOUNDATION_PROMPT.md.md`

### ai_ml (1)

- `ai_ml/README.md`

### da (9)

- `da/output/01_events_master.csv`
- `da/output/01_question_bank.csv`
- `da/output/02_phase_eligibility.csv`
- `da/output/02_skills_phase_map.csv`
- `da/output/03_recommendation_rules.csv`
- `da/output/03_related_skills.csv`
- `da/output/04_skill_difficulty_pool.csv`
- `da/output/05_quiz_checkpoints.csv`
- `da/output/06_quiz_rules.csv`

### data_analyst (34)

- `data_analyst/README.md`
- `data_analyst/data/Data_Analyst_Questions.xlsx`
- `data_analyst/data/Data_Analyst_Roadmap.xlsx`
- `data_analyst/data/Data_Analytics_Hackathons.xlsx`
- `data_analyst/output/01_da_events_master.csv`
- `data_analyst/output/01_da_question_bank.csv`
- `data_analyst/output/01_da_roadmap_overview.csv`
- `data_analyst/output/01_events_master.csv`
- `data_analyst/output/01_question_bank.csv`
- `data_analyst/output/02_da_phase_eligibility.csv`
- `data_analyst/output/02_da_skills_phase_map.csv`
- `data_analyst/output/02_phase_eligibility.csv`
- `data_analyst/output/02_phase_modules_resources.csv`
- `data_analyst/output/02_skills_phase_map.csv`
- `data_analyst/output/03_da_recommendation_rules.csv`
- `data_analyst/output/03_da_related_skills.csv`
- `data_analyst/output/03_recommendation_rules.csv`
- `data_analyst/output/03_related_skills.csv`
- `data_analyst/output/03_skills_catalog.csv`
- `data_analyst/output/04_da_skill_difficulty_pool.csv`
- `data_analyst/output/04_phase_summary_readiness_checkpoints.csv`
- `data_analyst/output/04_skill_difficulty_pool.csv`
- `data_analyst/output/05_da_quiz_checkpoints.csv`
- `data_analyst/output/05_projects.csv`
- `data_analyst/output/05_quiz_checkpoints.csv`
- `data_analyst/output/06_da_quiz_rules.csv`
- `data_analyst/output/06_project_rubric_items.csv`
- `data_analyst/output/06_quiz_rules.csv`
- `data_analyst/output/07_pacing_templates.csv`
- `data_analyst/output/08_milestones.csv`
- `data_analyst/output/09_learning_methods.csv`
- `data_analyst/scripts/build_da_csvs.py`
- `data_analyst/scripts/build_da_events_csvs.py`
- `data_analyst/scripts/build_da_quiz_csvs.py`

### output (38)

- `output/01_aiml_events_master.csv`
- `output/01_da_events_master.csv`
- `output/01_da_question_bank.csv`
- `output/01_da_roadmap_overview.csv`
- `output/01_events_master.csv`
- `output/01_question_bank.csv`
- `output/01_roadmap.csv`
- `output/01_sde_problem_bank_raw.csv`
- `output/02_aiml_phase_eligibility.csv`
- `output/02_da_phase_eligibility.csv`
- `output/02_da_skills_phase_map.csv`
- `output/02_phase_eligibility.csv`
- `output/02_phase_modules_resources.csv`
- `output/02_phase_resources.csv`
- `output/02_sde_problems_unique.csv`
- `output/02_skills_phase_map.csv`
- `output/03_aiml_recommendation_rules.csv`
- `output/03_da_recommendation_rules.csv`
- `output/03_da_related_skills.csv`
- `output/03_prerequisites.csv`
- `output/03_recommendation_rules.csv`
- `output/03_related_skills.csv`
- `output/03_skills_catalog.csv`
- `output/03_topics_roadmap_map.csv`
- `output/04_aiml_domain_to_phase_map.csv`
- `output/04_da_skill_difficulty_pool.csv`
- `output/04_domain_to_phase_map.csv`
- `output/04_phase_summary_readiness_checkpoints.csv`
- `output/04_skill_difficulty_pool.csv`
- `output/05_da_quiz_checkpoints.csv`
- `output/05_projects.csv`
- `output/05_quiz_checkpoints.csv`
- `output/06_da_quiz_rules.csv`
- `output/06_project_rubric_items.csv`
- `output/06_quiz_rules.csv`
- `output/07_pacing_templates.csv`
- `output/08_milestones.csv`
- `output/09_learning_methods.csv`

### sde (17)

- `sde/output/01_events_master.csv`
- `sde/output/01_problem_bank_raw.csv`
- `sde/output/01_sde_events_master.csv`
- `sde/output/01_sde_problem_bank_raw.csv`
- `sde/output/01_sde_roadmap_overview.csv`
- `sde/output/02_phase_eligibility.csv`
- `sde/output/02_phase_learning_content.csv`
- `sde/output/02_problems_unique.csv`
- `sde/output/02_sde_phase_eligibility.csv`
- `sde/output/02_sde_problems_unique.csv`
- `sde/output/03_recommendation_rules.csv`
- `sde/output/03_sde_recommendation_rules.csv`
- `sde/output/03_sde_topics_roadmap_map.csv`
- `sde/output/03_topic_checkpoints.csv`
- `sde/output/03_topics_roadmap_map.csv`
- `sde/output/04_project_repos.csv`
- `sde/output/05_portfolio_projects.csv`

## MOVED / RENAMED (36) - identical content, new path

### aiml (7)

- `aiml/output/01_events_master.csv` -> `aiml/output/events/01_events_master.csv`
- `aiml/output/01_roadmap.csv` -> `aiml/output/curriculum/01_roadmap.csv`
- `aiml/output/02_phase_eligibility.csv` -> `aiml/output/events/02_phase_eligibility.csv`
- `aiml/output/02_phase_resources.csv` -> `aiml/output/curriculum/02_phase_resources.csv`
- `aiml/output/03_prerequisites.csv` -> `aiml/output/curriculum/03_prerequisites.csv`
- `aiml/output/03_recommendation_rules.csv` -> `aiml/output/events/03_recommendation_rules.csv`
- `aiml/output/04_domain_to_phase_map.csv` -> `aiml/output/events/04_domain_to_phase_map.csv`

### da (18)

- `da/output/01_da_events_master.csv` -> `da/output/events/01_events_master.csv`
- `da/output/01_da_question_bank.csv` -> `da/output/quiz/01_question_bank.csv`
- `da/output/01_da_roadmap_overview.csv` -> `da/output/curriculum/01_da_roadmap_overview.csv`
- `da/output/02_da_phase_eligibility.csv` -> `da/output/events/02_phase_eligibility.csv`
- `da/output/02_da_skills_phase_map.csv` -> `da/output/quiz/02_skills_phase_map.csv`
- `da/output/02_phase_modules_resources.csv` -> `da/output/curriculum/02_phase_modules_resources.csv`
- `da/output/03_da_recommendation_rules.csv` -> `da/output/events/03_recommendation_rules.csv`
- `da/output/03_da_related_skills.csv` -> `da/output/quiz/03_related_skills.csv`
- `da/output/03_skills_catalog.csv` -> `da/output/curriculum/03_skills_catalog.csv`
- `da/output/04_da_skill_difficulty_pool.csv` -> `da/output/quiz/04_skill_difficulty_pool.csv`
- `da/output/04_phase_summary_readiness_checkpoints.csv` -> `da/output/curriculum/04_phase_summary_readiness_checkpoints.csv`
- `da/output/05_da_quiz_checkpoints.csv` -> `da/output/quiz/05_quiz_checkpoints.csv`
- `da/output/05_projects.csv` -> `da/output/curriculum/05_projects.csv`
- `da/output/06_da_quiz_rules.csv` -> `da/output/quiz/06_quiz_rules.csv`
- `da/output/06_project_rubric_items.csv` -> `da/output/curriculum/06_project_rubric_items.csv`
- `da/output/07_pacing_templates.csv` -> `da/output/curriculum/07_pacing_templates.csv`
- `da/output/08_milestones.csv` -> `da/output/curriculum/08_milestones.csv`
- `da/output/09_learning_methods.csv` -> `da/output/curriculum/09_learning_methods.csv`

### sde (11)

- `output/01_problem_bank_raw.csv` -> `sde/output/quiz/01_problem_bank_raw.csv`
- `output/01_sde_events_master.csv` -> `sde/output/events/01_events_master.csv`
- `output/01_sde_roadmap_overview.csv` -> `sde/output/curriculum/01_sde_roadmap_overview.csv`
- `output/02_phase_learning_content.csv` -> `sde/output/curriculum/02_phase_learning_content.csv`
- `output/02_problems_unique.csv` -> `sde/output/quiz/02_problems_unique.csv`
- `output/02_sde_phase_eligibility.csv` -> `sde/output/events/02_phase_eligibility.csv`
- `output/03_sde_recommendation_rules.csv` -> `sde/output/events/03_recommendation_rules.csv`
- `output/03_sde_topics_roadmap_map.csv` -> `sde/output/quiz/03_topics_roadmap_map.csv`
- `output/03_topic_checkpoints.csv` -> `sde/output/curriculum/03_topic_checkpoints.csv`
- `output/04_project_repos.csv` -> `sde/output/curriculum/04_project_repos.csv`
- `output/05_portfolio_projects.csv` -> `sde/output/curriculum/05_portfolio_projects.csv`
