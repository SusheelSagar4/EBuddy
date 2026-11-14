import csv
import os

courses = {}
with open('data/seed/kb/course.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        courses[r['course_id']] = r

goals = {}
with open('data/seed/kb/goal.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        goals[r['goal_id']] = r

course_skills = {}
with open('data/seed/kb/course_skill.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        cid = r['course_id']
        sid = r['skill_id']
        lvl = float(r['level_taught'])
        course_skills.setdefault(cid, {})[sid] = lvl

goal_skills = {}
with open('data/seed/kb/goal_skill_requirement.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        gid = r['goal_id']
        sid = r['skill_id']
        lvl = float(r['required_level'])
        imp = float(r['importance'])
        goal_skills.setdefault(gid, {})[sid] = (lvl, imp)

rel_rows = []
foundational_courses = {
    'MA1L001', 'MA1L002', 'CS1L001', 'CS1P001',
    'PH1L001', 'PH1P001', 'CH1L001', 'CH1P001',
    'EE1L001', 'EE1P001'
}

for cid in sorted(courses.keys()):
    c_info = courses[cid]
    c_sk = course_skills.get(cid, {})
    
    for gid in sorted(goals.keys()):
        g_info = goals[gid]
        g_sk = goal_skills.get(gid, {})

        matching = []
        strength = 0.0
        for sid, c_lvl in c_sk.items():
            if sid in g_sk:
                req_lvl, imp = g_sk[sid]
                contrib = (c_lvl / 100.0) * (req_lvl / 100.0) * imp
                strength += contrib
                matching.append(sid)

        matches_str = ", ".join(matching)

        if strength > 0:
            if strength >= 0.50 or any(g_sk.get(s, (0, 0))[1] >= 0.95 for s in matching):
                score = 3
                rationale = f"Essential competency match for {matches_str} (overlap strength {strength:.2f})"
            elif strength >= 0.15:
                score = 2
                rationale = f"Useful elective supporting {matches_str} (overlap strength {strength:.2f})"
            else:
                score = 1
                rationale = f"Foundational competency supporting {matches_str} (overlap strength {strength:.2f})"
        else:
            if cid in foundational_courses:
                score = 1
                rationale = "Foundational science and mathematics core"
            elif gid.startswith("GOAL_EE_") and (cid.startswith("EE") or cid.startswith("EC")):
                score = 1
                rationale = "General electrical/electronics engineering curriculum"
            elif gid.startswith("GOAL_MM_") and (cid.startswith("ML") or cid.startswith("MM")):
                score = 1
                rationale = "General metallurgical & materials engineering curriculum"
            else:
                score = 0
                rationale = "Non-overlapping cross-department course"

        rel_rows.append({
            'course_id': cid,
            'goal_id': gid,
            'relevance_score': score,
            'rationale': rationale,
            'status': 'draft_for_review',
            'source_id': 'AI_DRAFT'
        })

rel_path = 'data/seed/kb/relevance_tags.csv'
with open(rel_path, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=['course_id', 'goal_id', 'relevance_score', 'rationale', 'status', 'source_id'])
    w.writeheader()
    w.writerows(rel_rows)

print(f"Regenerated relevance_tags.csv: {len(rel_rows)} rows (derived deterministically from course_skill & goal_skill_requirement).")

