-- =============================================================================
-- Adobe Personalised Learning Buddy - PostgreSQL DDL Initialization Script
-- Schemas: kb, student, plan, ops
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS kb;
CREATE SCHEMA IF NOT EXISTS student;
CREATE SCHEMA IF NOT EXISTS plan;
CREATE SCHEMA IF NOT EXISTS ops;

-- =============================================================================
-- SCHEMA: kb (Knowledge Base)
-- =============================================================================

CREATE TABLE IF NOT EXISTS kb.source (
    source_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    url TEXT,
    publisher VARCHAR(255),
    licence VARCHAR(100),
    retrieved_on DATE,
    doc_type VARCHAR(50),
    reliability VARCHAR(50),
    academic_year VARCHAR(50),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS kb.department (
    department_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS kb.programme (
    programme_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department_id VARCHAR(50) REFERENCES kb.department(department_id),
    total_credits_required NUMERIC(5, 1) NULL, -- NULL if unsourced
    duration_semesters INT NOT NULL DEFAULT 8,
    curriculum_version VARCHAR(50) DEFAULT '2016-17',
    status VARCHAR(50) DEFAULT 'verified',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.course (
    course_id VARCHAR(50) PRIMARY KEY,
    course_code VARCHAR(20) NOT NULL,
    display_code VARCHAR(20) NOT NULL,
    code_conflict BOOLEAN NOT NULL DEFAULT FALSE,
    title VARCHAR(255) NOT NULL,
    department_id VARCHAR(50),
    credits NUMERIC(4, 1) NOT NULL,
    ltp VARCHAR(20),
    mode VARCHAR(20) DEFAULT 'offline',
    level VARCHAR(20) DEFAULT 'UG',
    syllabus_text TEXT,
    learning_objectives TEXT,
    in_semester_table BOOLEAN DEFAULT TRUE,
    source_id VARCHAR(100) REFERENCES kb.source(source_id),
    is_placeholder BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS kb.course_alias (
    alias_name VARCHAR(255) PRIMARY KEY,
    target_course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS kb.course_prerequisite (
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    prereq_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    relation VARCHAR(50) DEFAULT 'required',
    PRIMARY KEY (course_id, prereq_id)
);

CREATE TABLE IF NOT EXISTS kb.course_offering (
    id SERIAL PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    semester_number INT NOT NULL,
    parity VARCHAR(10) NOT NULL, -- 'odd' / 'even'
    track VARCHAR(10) DEFAULT 'ALL', -- 'A' / 'B' / 'ALL'
    offering_basis VARCHAR(100) DEFAULT 'inferred_from_semester_table'
);

CREATE TABLE IF NOT EXISTS kb.programme_requirement (
    slot_id VARCHAR(100) PRIMARY KEY,
    programme_id VARCHAR(50) REFERENCES kb.programme(programme_id),
    semester_number INT,
    slot_name VARCHAR(255),
    slot_type VARCHAR(50), -- core, lateral, breadth, elective, common_core
    min_credits NUMERIC(4, 1) DEFAULT 0.0,
    max_credits NUMERIC(4, 1) DEFAULT 0.0,
    option_pool VARCHAR(255),
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    course_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'verified',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.slot_option (
    slot_id VARCHAR(100) REFERENCES kb.programme_requirement(slot_id) ON DELETE CASCADE,
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    PRIMARY KEY (slot_id, course_id)
);

CREATE TABLE IF NOT EXISTS kb.minor (
    minor_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    offering_department VARCHAR(50) REFERENCES kb.department(department_id),
    min_cgpa NUMERIC(4, 2) NOT NULL DEFAULT 8.00,
    min_credits NUMERIC(4, 1) NOT NULL DEFAULT 18.0,
    status VARCHAR(50) DEFAULT 'unsourced_baseline',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.minor_course (
    minor_id VARCHAR(50) REFERENCES kb.minor(minor_id) ON DELETE CASCADE,
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    is_mandatory BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (minor_id, course_id)
);

CREATE TABLE IF NOT EXISTS kb.academic_rule (
    rule_id VARCHAR(100) PRIMARY KEY,
    rule_type VARCHAR(50) NOT NULL, -- credit_cap, min_credits, minor_eligibility, prereq, online_credit, other
    parameters JSONB NOT NULL DEFAULT '{}',
    human_text TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'unsourced_baseline',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.skill (
    skill_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100) NOT NULL,
    description TEXT,
    level_scale VARCHAR(50) DEFAULT '0-100',
    status VARCHAR(50) DEFAULT 'draft_for_review',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.skill_prerequisite (
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    prereq_skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    PRIMARY KEY (skill_id, prereq_skill_id)
);

CREATE TABLE IF NOT EXISTS kb.course_skill (
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    level_taught NUMERIC(5, 2) NOT NULL, -- 0-100
    weight NUMERIC(4, 2) DEFAULT 1.0,
    mapping_method VARCHAR(50) DEFAULT 'inferred_from_course_title',
    status VARCHAR(50) DEFAULT 'draft_for_review',
    source_id VARCHAR(100) REFERENCES kb.source(source_id),
    PRIMARY KEY (course_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.module (
    module_id VARCHAR(100) PRIMARY KEY,
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    resource_id VARCHAR(100),
    title VARCHAR(255) NOT NULL,
    order_no INT NOT NULL DEFAULT 1,
    est_minutes INT DEFAULT 60,
    objectives TEXT,
    is_placeholder BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS kb.module_skill (
    module_id VARCHAR(100) REFERENCES kb.module(module_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    level_taught NUMERIC(5, 2) NOT NULL,
    PRIMARY KEY (module_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.resource (
    resource_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL, -- NPTEL, SWAYAM, MIT OCW, third-party
    url TEXT NOT NULL,
    licence VARCHAR(100),
    resource_type VARCHAR(50) DEFAULT 'playlist',
    coverage_status VARCHAR(50),
    link_verified BOOLEAN DEFAULT FALSE,
    est_hours NUMERIC(5, 1),
    difficulty VARCHAR(20),
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.resource_skill (
    resource_id VARCHAR(100) REFERENCES kb.resource(resource_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    level_taught NUMERIC(5, 2) NOT NULL,
    PRIMARY KEY (resource_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.resource_course (
    resource_id VARCHAR(100) REFERENCES kb.resource(resource_id) ON DELETE CASCADE,
    course_id VARCHAR(50) REFERENCES kb.course(course_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'primary', -- primary, backup1, backup2, lab_theory
    PRIMARY KEY (resource_id, course_id, role)
);

CREATE TABLE IF NOT EXISTS kb.exercise (
    exercise_id VARCHAR(100) PRIMARY KEY,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id),
    module_id VARCHAR(100) REFERENCES kb.module(module_id) ON DELETE SET NULL,
    kind VARCHAR(50) NOT NULL, -- mcq, numeric, short, project, case_study, mock_test
    difficulty INT NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    prompt TEXT NOT NULL,
    options JSONB,
    answer_key JSONB,
    rubric TEXT,
    est_minutes INT DEFAULT 15,
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.goal (
    goal_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- career, higher_studies, competitive_exam, startup
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft_for_review',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.goal_skill_requirement (
    goal_id VARCHAR(100) REFERENCES kb.goal(goal_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    required_level NUMERIC(5, 2) NOT NULL,
    importance NUMERIC(4, 2) DEFAULT 1.0,
    status VARCHAR(50) DEFAULT 'draft_for_review',
    source_id VARCHAR(100) REFERENCES kb.source(source_id),
    PRIMARY KEY (goal_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.goal_milestone (
    milestone_id SERIAL PRIMARY KEY,
    goal_id VARCHAR(100) REFERENCES kb.goal(goal_id) ON DELETE CASCADE,
    milestone_type VARCHAR(50) NOT NULL, -- project, internship, exam_timeline, mock_interview
    description TEXT NOT NULL,
    typical_semester INT
);

CREATE TABLE IF NOT EXISTS kb.mastery_criteria (
    criteria_id VARCHAR(100) PRIMARY KEY,
    goal_id VARCHAR(100) REFERENCES kb.goal(goal_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    criteria JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'draft_for_review',
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.research_area (
    area_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS kb.faculty (
    faculty_id VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(255) NOT NULL,
    title VARCHAR(50),
    group_name VARCHAR(255),
    is_person BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS kb.research_project (
    project_id VARCHAR(100) PRIMARY KEY,
    area_id VARCHAR(50) REFERENCES kb.research_area(area_id),
    title VARCHAR(500) NOT NULL,
    funding_agency VARCHAR(255),
    grant_lakhs NUMERIC(8, 2),
    start_year INT,
    end_year INT,
    scope_text TEXT,
    source_id VARCHAR(100) REFERENCES kb.source(source_id),
    detail_level VARCHAR(20) NOT NULL DEFAULT 'title_only',
    verified BOOLEAN DEFAULT FALSE,
    source_confidence VARCHAR(50) DEFAULT 'compiled_secondary',
    legibility VARCHAR(20) DEFAULT 'clear', -- 'clear', 'partial'
    amount_suspect BOOLEAN DEFAULT FALSE,
    duplicate_of VARCHAR(100),
    alt_value TEXT
);

CREATE TABLE IF NOT EXISTS kb.consultancy_engagement (
    engagement_id VARCHAR(100) PRIMARY KEY,
    consultant_name VARCHAR(255) NOT NULL,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id),
    client VARCHAR(255),
    amount_lakhs NUMERIC(8, 2),
    amount_raw VARCHAR(50),
    duration_years VARCHAR(50),
    start_year INT,
    end_year INT,
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.publication (
    publication_id VARCHAR(100) PRIMARY KEY,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id),
    title VARCHAR(500) NOT NULL,
    journal_or_venue VARCHAR(255),
    year INT,
    approx_citations INT,
    citations_as_of DATE DEFAULT '2026-11-13',
    selection_only BOOLEAN DEFAULT TRUE,
    doi VARCHAR(100),
    source_id VARCHAR(100) REFERENCES kb.source(source_id)
);

CREATE TABLE IF NOT EXISTS kb.project_faculty (
    project_id VARCHAR(100) REFERENCES kb.research_project(project_id) ON DELETE CASCADE,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'PI',
    PRIMARY KEY (project_id, faculty_id)
);

CREATE TABLE IF NOT EXISTS kb.project_keyword (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) REFERENCES kb.research_project(project_id) ON DELETE CASCADE,
    keyword VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS kb.keyword_skill (
    keyword VARCHAR(255) NOT NULL,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    mapping_method VARCHAR(50) DEFAULT 'rule_heuristic',
    confidence NUMERIC(3, 2) DEFAULT 0.85,
    PRIMARY KEY (keyword, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.data_issue (
    issue_id VARCHAR(100) PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_key VARCHAR(255) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- high, medium, low
    description TEXT NOT NULL,
    resolution_notes TEXT,
    status VARCHAR(50) DEFAULT 'unresolved'
);

-- =============================================================================
-- SCHEMA: student (Profiles, Evidence, Constraints)
-- =============================================================================

CREATE TABLE IF NOT EXISTS student.student (
    student_id VARCHAR(100) PRIMARY KEY,
    programme_id VARCHAR(50) REFERENCES kb.programme(programme_id),
    year INT NOT NULL,
    current_semester INT NOT NULL,
    cgpa NUMERIC(4, 2) NOT NULL DEFAULT 8.00,
    is_synthetic BOOLEAN NOT NULL DEFAULT TRUE,
    persona_tag VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student.completed_course (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    course_id VARCHAR(50) REFERENCES kb.course(course_id),
    grade VARCHAR(5) NOT NULL,
    semester INT NOT NULL,
    is_backlog BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS student.goal (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    goal_id VARCHAR(100) REFERENCES kb.goal(goal_id),
    priority INT NOT NULL DEFAULT 1,
    target_date DATE
);

CREATE TABLE IF NOT EXISTS student.interest (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    topic VARCHAR(100) NOT NULL,
    weight NUMERIC(3, 2) DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS student.skill_evidence (
    evidence_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id),
    source_type VARCHAR(50) NOT NULL, -- diagnostic, exercise, exam, self_report
    score NUMERIC(5, 2) NOT NULL,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS student.skill_state (
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    estimated_level NUMERIC(5, 2) NOT NULL,
    confidence NUMERIC(3, 2) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (student_id, skill_id)
);

CREATE TABLE IF NOT EXISTS student.constraint (
    constraint_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    constraint_type VARCHAR(50) NOT NULL, -- max_hours_per_week, preferred_timeslot, exam_cycle
    parameters JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS student.preference (
    student_id VARCHAR(100) PRIMARY KEY REFERENCES student.student(student_id) ON DELETE CASCADE,
    preferred_learning_mode VARCHAR(50) DEFAULT 'balanced', -- video_heavy, text_heavy, project_oriented
    pace VARCHAR(20) DEFAULT 'standard'
);

-- =============================================================================
-- SCHEMA: plan (Semester Plans, Schedule Items, Diff Audits)
-- =============================================================================

CREATE TABLE IF NOT EXISTS plan.plan (
    plan_id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    version INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL DEFAULT 'draft', -- draft, active, archived
    trigger VARCHAR(50) NOT NULL, -- initial_diagnostic, manual_regen, admin_edit, grade_import
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan.plan_item (
    item_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(100) REFERENCES plan.plan(plan_id) ON DELETE CASCADE,
    semester INT NOT NULL,
    item_type VARCHAR(50) NOT NULL, -- course, project, milestone, higher_studies_prep
    entity_id VARCHAR(100) NOT NULL,
    credits NUMERIC(4, 1) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'planned'
);

CREATE TABLE IF NOT EXISTS plan.validation_report (
    report_id SERIAL PRIMARY KEY,
    plan_id VARCHAR(100) REFERENCES plan.plan(plan_id) ON DELETE CASCADE,
    passed BOOLEAN NOT NULL,
    checks_run JSONB NOT NULL,
    violations JSONB NOT NULL,
    warnings JSONB NOT NULL,
    validated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan.plan_diff (
    diff_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    old_plan_id VARCHAR(100) REFERENCES plan.plan(plan_id),
    new_plan_id VARCHAR(100) REFERENCES plan.plan(plan_id),
    trigger VARCHAR(50) NOT NULL,
    changes JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan.assessment_attempt (
    attempt_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    exercise_id VARCHAR(100) REFERENCES kb.exercise(exercise_id),
    response JSONB NOT NULL,
    score NUMERIC(5, 2) NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS plan.decision_log (
    log_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    plan_id VARCHAR(100) REFERENCES plan.plan(plan_id),
    engine_step VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    outputs JSONB NOT NULL,
    rationale TEXT NOT NULL,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- SCHEMA: ops (Operations, LLM Audit, Reprocessing Queue)
-- =============================================================================

CREATE TABLE IF NOT EXISTS ops.reprocess_queue (
    event_id SERIAL PRIMARY KEY,
    entity_type VARCHAR(100) NOT NULL,
    entity_id TEXT NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, processing, completed, failed
    enqueued_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS ops.llm_call_log (
    call_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100),
    model_name VARCHAR(100) NOT NULL,
    purpose VARCHAR(100) NOT NULL, -- assessment_gen, explanation, hint
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    cost_usd NUMERIC(8, 6) DEFAULT 0.000000,
    duration_ms INT NOT NULL,
    called_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops.conversation (
    conversation_id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops.message (
    message_id SERIAL PRIMARY KEY,
    conversation_id VARCHAR(100) REFERENCES ops.conversation(conversation_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ops.memory_summary (
    summary_id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- RE-PROCESSING TRIGGERS (Hard Rule 7 & Section 6.4)
-- Native PostgreSQL function & triggers to notify queue on direct SQL edits (Adminer / API / Admin UI)
-- =============================================================================

CREATE OR REPLACE FUNCTION ops.notify_reprocess_event()
RETURNS TRIGGER AS $$
DECLARE
    target_student VARCHAR(100);
    ent_type VARCHAR(100);
    ent_id TEXT;
BEGIN
    ent_type := TG_TABLE_SCHEMA || '.' || TG_TABLE_NAME;
    
    IF TG_TABLE_SCHEMA = 'student' THEN
        IF TG_OP = 'DELETE' THEN
            target_student := OLD.student_id;
            ent_id := OLD.student_id;
        ELSE
            target_student := NEW.student_id;
            ent_id := NEW.student_id;
        END IF;
    ELSIF TG_TABLE_NAME = 'course' THEN
        IF TG_OP = 'DELETE' THEN
            ent_id := OLD.course_id;
        ELSE
            ent_id := NEW.course_id;
        END IF;
        target_student := 'ALL';
    ELSE
        IF TG_OP = 'DELETE' THEN
            ent_id := CAST(OLD AS TEXT);
        ELSE
            ent_id := CAST(NEW AS TEXT);
        END IF;
        target_student := 'ALL';
    END IF;

    -- Enqueue into ops.reprocess_queue
    INSERT INTO ops.reprocess_queue (entity_type, entity_id, action, status)
    VALUES (ent_type, ent_id, TG_OP, 'pending');

    -- Send PostgreSQL notification event for async listener
    PERFORM pg_notify('reprocess_channel', json_build_object(
        'schema', TG_TABLE_SCHEMA,
        'table', TG_TABLE_NAME,
        'action', TG_OP,
        'student_id', target_student,
        'entity_id', ent_id,
        'timestamp', CURRENT_TIMESTAMP
    )::text);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Attach triggers to editable tables
DROP TRIGGER IF EXISTS trg_student_completed_course ON student.completed_course;
CREATE TRIGGER trg_student_completed_course
AFTER INSERT OR UPDATE OR DELETE ON student.completed_course
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_student_skill_evidence ON student.skill_evidence;
CREATE TRIGGER trg_student_skill_evidence
AFTER INSERT OR UPDATE OR DELETE ON student.skill_evidence
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_student_goal ON student.goal;
CREATE TRIGGER trg_student_goal
AFTER INSERT OR UPDATE OR DELETE ON student.goal
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_student_constraint ON student.constraint;
CREATE TRIGGER trg_student_constraint
AFTER INSERT OR UPDATE OR DELETE ON student.constraint
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_kb_course ON kb.course;
CREATE TRIGGER trg_kb_course
AFTER INSERT OR UPDATE OR DELETE ON kb.course
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_kb_academic_rule ON kb.academic_rule;
CREATE TRIGGER trg_kb_academic_rule
AFTER INSERT OR UPDATE OR DELETE ON kb.academic_rule
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

-- =============================================================================
-- CORE TO CORE SCHEMA EXTENSIONS (Section 5)
-- =============================================================================

CREATE TABLE IF NOT EXISTS kb.academic_calendar (
    id SERIAL PRIMARY KEY,
    semester VARCHAR(20) NOT NULL,
    week_number INT NOT NULL,
    week_start DATE NOT NULL,
    week_type VARCHAR(50) NOT NULL, -- teaching, midsem, endsem, break, holiday
    calendar_factor NUMERIC(3, 2) NOT NULL DEFAULT 1.0,
    source_url TEXT,
    verified BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS student.student_enrollment (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    course_code VARCHAR(50) NOT NULL,
    semester INT NOT NULL,
    status VARCHAR(20) NOT NULL, -- current, completed
    grade VARCHAR(5),
    grade_source VARCHAR(50) DEFAULT 'institute_transcript'
);

CREATE TABLE IF NOT EXISTS kb.area_skill (
    area_id VARCHAR(50) REFERENCES kb.research_area(area_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    required_level NUMERIC(5, 2) NOT NULL,
    PRIMARY KEY (area_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.faculty_area (
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE CASCADE,
    area_id VARCHAR(50) REFERENCES kb.research_area(area_id) ON DELETE CASCADE,
    weight NUMERIC(3, 2) DEFAULT 1.0,
    PRIMARY KEY (faculty_id, area_id)
);

CREATE TABLE IF NOT EXISTS kb.paper (
    paper_id VARCHAR(100) PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    year INT,
    venue VARCHAR(255),
    doi_or_url TEXT,
    abstract TEXT,
    open_access BOOLEAN DEFAULT FALSE,
    licence VARCHAR(100),
    fulltext_path TEXT,
    source_url TEXT,
    retrieved_on DATE,
    verified BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS kb.paper_author (
    id SERIAL PRIMARY KEY,
    paper_id VARCHAR(100) REFERENCES kb.paper(paper_id) ON DELETE CASCADE,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE SET NULL,
    author_name VARCHAR(255) NOT NULL,
    author_order INT NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS kb.paper_chunk (
    chunk_id SERIAL PRIMARY KEY,
    paper_id VARCHAR(100) REFERENCES kb.paper(paper_id) ON DELETE CASCADE,
    page INT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    embedding JSONB
);

CREATE TABLE IF NOT EXISTS kb.paper_skill (
    paper_id VARCHAR(100) REFERENCES kb.paper(paper_id) ON DELETE CASCADE,
    skill_id VARCHAR(100) REFERENCES kb.skill(skill_id) ON DELETE CASCADE,
    level NUMERIC(5, 2) NOT NULL,
    reviewed BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (paper_id, skill_id)
);

CREATE TABLE IF NOT EXISTS kb.taster_task (
    id VARCHAR(100) PRIMARY KEY,
    area_id VARCHAR(50) REFERENCES kb.research_area(area_id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL, -- read_abstract, solve_problem, short_writeup
    prompt TEXT NOT NULL,
    rubric TEXT NOT NULL,
    est_minutes INT DEFAULT 30
);

CREATE TABLE IF NOT EXISTS plan.weekly_focus (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    budget_hours NUMERIC(4, 1) NOT NULL,
    focus_items JSONB NOT NULL DEFAULT '[]',
    version INT NOT NULL DEFAULT 1,
    created_by VARCHAR(50) DEFAULT 'system'
);

CREATE TABLE IF NOT EXISTS student.reflection (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    worked TEXT,
    didnt_work TEXT,
    self_rating INT CHECK (self_rating BETWEEN 1 AND 5),
    hours_spent NUMERIC(4, 1)
);

CREATE TABLE IF NOT EXISTS student.interest_signal (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    area_id VARCHAR(50) REFERENCES kb.research_area(area_id) ON DELETE CASCADE,
    kind VARCHAR(50) NOT NULL, -- stated, taster_score, quiz, project
    value NUMERIC(5, 2) NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS student.faculty_match (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE CASCADE,
    score NUMERIC(5, 2) NOT NULL,
    score_breakdown JSONB NOT NULL,
    reasons JSONB NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    rank INT NOT NULL
);

CREATE TABLE IF NOT EXISTS student.approach (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'drafting', -- drafting, sent, replied, meeting, accepted, declined, no_reply
    sent_on DATE,
    last_update TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS student.project (
    id VARCHAR(100) PRIMARY KEY,
    student_id VARCHAR(100) REFERENCES student.student(student_id) ON DELETE CASCADE,
    faculty_id VARCHAR(100) REFERENCES kb.faculty(faculty_id) ON DELETE SET NULL,
    title VARCHAR(500) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    started_on DATE DEFAULT CURRENT_DATE
);

CREATE TABLE IF NOT EXISTS student.project_milestone (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) REFERENCES student.project(id) ON DELETE CASCADE,
    order_no INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    due_week INT NOT NULL,
    checkpoint_kind VARCHAR(50) NOT NULL,
    rubric TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS student.research_log (
    id SERIAL PRIMARY KEY,
    project_id VARCHAR(100) REFERENCES student.project(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    done TEXT,
    blockers TEXT,
    next TEXT
);

CREATE TABLE IF NOT EXISTS kb.industry_milestone (
    id VARCHAR(100) PRIMARY KEY,
    department VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL, -- exam, tool_skill, club, internship
    typical_timing VARCHAR(100),
    related_exam_id VARCHAR(100),
    source_url TEXT
);

-- Triggers for Core-to-Core updates
DROP TRIGGER IF EXISTS trg_student_approach ON student.approach;
CREATE TRIGGER trg_student_approach
AFTER INSERT OR UPDATE OR DELETE ON student.approach
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();

DROP TRIGGER IF EXISTS trg_student_reflection ON student.reflection;
CREATE TRIGGER trg_student_reflection
AFTER INSERT OR UPDATE OR DELETE ON student.reflection
FOR EACH ROW EXECUTE FUNCTION ops.notify_reprocess_event();
