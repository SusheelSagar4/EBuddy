import os
import re
import pandas as pd

ee_sem = pd.read_csv('data/raw/ee/curriculum_semester_table.csv')
ee_syl = pd.read_csv('data/raw/ee/curriculum_syllabus_only.csv')
mme_sem = pd.read_csv('data/raw/mme/curriculum_semester_table.csv')
kb_courses = pd.read_csv('data/seed/kb/course.csv')
pr = pd.read_csv('data/seed/kb/programme_requirement.csv')
so = pd.read_csv('data/seed/kb/slot_option.csv')

# Build course to semester mapping from PR / slot_option
sem_map = {}
for idx, r in pr.iterrows():
    if pd.notna(r.get('course_id')):
        sem_map[r['course_id']] = r['semester_number']
# for slot options
pr_sem = pr.set_index('slot_id')['semester_number'].to_dict()
for idx, r in so.iterrows():
    cid = r['course_id']
    sid = r['slot_id']
    if cid not in sem_map and sid in pr_sem:
        sem_map[cid] = pr_sem[sid]

def parse_semester(sem_str):
    if pd.isna(sem_str): return None
    s = str(sem_str).strip()
    m = re.search(r'Sem\s*([I|V|X]+)', s)
    if m:
        r_map = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8}
        return r_map.get(m.group(1))
    return None

# Parse raw entries
raw_by_code = {}

for df, src_name in [(ee_sem, 'EE_SEM'), (ee_syl, 'EE_SYL'), (mme_sem, 'MME_SEM')]:
    for idx, r in df.iterrows():
        c_code_raw = str(r['Course Code']).strip() if pd.notna(r['Course Code']) else ''
        c_name_raw = str(r['Course Name']).strip() if pd.notna(r['Course Name']) else ''
        creds_raw = str(r['Credits']).strip() if pd.notna(r['Credits']) else ''
        ltp_raw = str(r['L-T-P']).strip() if pd.notna(r['L-T-P']) else ''
        sem_raw = parse_semester(r['Semester'])
        course_type = str(r.get('Course Type', '')).strip()

        # Handle slash-separated codes: e.g. PH1L001 / CY1L001
        codes = [re.sub(r'[^A-Z0-9_]', '', x) for x in re.split(r'[/,]|\bor\b', c_code_raw) if x.strip()]
        names = [x.strip() for x in re.split(r'[/]|\bor\b', c_name_raw) if x.strip()]
        credits_list = [x.strip() for x in re.split(r'[/]', creds_raw) if x.strip()]
        ltp_list = [x.strip() for x in re.split(r'[/]', ltp_raw) if x.strip()]

        for i, code in enumerate(codes):
            if not code: continue
            title = names[i] if i < len(names) else c_name_raw
            try:
                c_val = float(credits_list[i]) if i < len(credits_list) else (float(credits_list[0]) if credits_list else None)
            except:
                c_val = None
            ltp_val = ltp_list[i] if i < len(ltp_list) else ltp_raw

            if code not in raw_by_code:
                raw_by_code[code] = []
            raw_by_code[code].append({
                'source': src_name,
                'raw_code': c_code_raw,
                'code': code,
                'title': title,
                'credits': c_val,
                'ltp': ltp_val,
                'semester': sem_raw,
                'course_type': course_type
            })

print(f"Total distinct raw codes found: {len(raw_by_code)}")
print(f"Total courses in kb.course: {len(kb_courses)}")

# Specific courses to explain
specific_targets = [
    'EE6L002', 'EE6L005', 'EE6L006', 'EE6L010', 'EE6L014',
    'EC6L016', 'EC6L018',
    'ML2L001', 'ML2L003',
    'ML3L001', 'ML3L002', 'ML3L003', 'ML3L004',
    'ML3P004', 'ML3P005', 'ML3P006', 'ML3P007'
]

print("\n=== SPECIFIC COURSES AUDIT ===")
for target in specific_targets:
    in_kb = kb_courses[kb_courses['course_id'] == target]
    in_raw = raw_by_code.get(target, [])
    print(f"\n--- {target} ---")
    if len(in_kb) > 0:
        row = in_kb.iloc[0]
        print(f"  In kb.course: title='{row['title']}', credits={row['credits']}, dept='{row['department_id']}', status='{row.get('status', 'N/A')}', source='{row['source_id']}'")
    else:
        print(f"  In kb.course: NOT PRESENT")
    
    if in_raw:
        for entry in in_raw:
            print(f"  In raw ({entry['source']}): title='{entry['title']}', credits={entry['credits']}, sem={entry['semester']}, ltp='{entry['ltp']}'")
    else:
        print(f"  In raw: NOT FOUND IN ANY RAW SOURCE")

# Row by row diff of kb.course vs raw
print("\n=== ROW BY ROW DIFF (kb.course vs raw) ===")
mismatches = []
unsourced = []

for idx, r in kb_courses.iterrows():
    cid = r['course_id']
    code = r['course_code']
    dcode = r['display_code']
    title = str(r['title']).strip()
    creds = float(r['credits'])
    dept = str(r['department_id']).strip()
    sem_kb = sem_map.get(cid)

    # find in raw
    raw_entries = raw_by_code.get(code) or raw_by_code.get(dcode) or raw_by_code.get(cid)
    if not raw_entries:
        unsourced.append(cid)
        mismatches.append({
            'course_id': cid,
            'field': 'PRESENCE',
            'kb_value': 'Present in kb.course',
            'raw_value': 'MISSING FROM RAW DATA',
            'detail': f"Title: {title}"
        })
        continue

    # Match against raw entry
    raw_match = raw_entries[0]
    raw_title = raw_match['title']
    raw_credits = raw_match['credits']
    raw_sem = raw_match['semester']

    # check title similarity
    if raw_title.lower() != title.lower():
        mismatches.append({
            'course_id': cid,
            'field': 'TITLE',
            'kb_value': title,
            'raw_value': raw_title,
            'detail': f"Code: {code}"
        })

    # check credits
    if raw_credits is not None and abs(raw_credits - creds) > 0.01:
        mismatches.append({
            'course_id': cid,
            'field': 'CREDITS',
            'kb_value': creds,
            'raw_value': raw_credits,
            'detail': f"Code: {code}"
        })

    # check semester
    if raw_sem is not None and sem_kb is not None and raw_sem != sem_kb:
        mismatches.append({
            'course_id': cid,
            'field': 'SEMESTER',
            'kb_value': sem_kb,
            'raw_value': raw_sem,
            'detail': f"Code: {code}"
        })

print(f"\nTotal Mismatches found: {len(mismatches)}")
for m in mismatches:
    print(f"[{m['course_id']}] {m['field']}: kb='{m['kb_value']}' vs raw='{m['raw_value']}' ({m['detail']})")

print(f"\nTotal Unsourced courses: {len(unsourced)}")
for u in unsourced:
    print(f"  {u}")
