import csv

def analyze_courses_and_slots():
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    courses = {}
    slots = []
    
    # Process rows
    for r in rows:
        if not r or not any(r):
            continue
        sem = r[0].strip()
        name = r[1].strip() if len(r) > 1 else ""
        code = r[2].strip() if len(r) > 2 else ""
        ltp = r[3].strip() if len(r) > 3 else ""
        creds = r[4].strip() if len(r) > 4 else ""
        hrs = r[5].strip() if len(r) > 5 else ""
        ctype = r[6].strip() if len(r) > 6 else ""
        prereq = r[7].strip() if len(r) > 7 else ""
        notes = r[10].strip() if len(r) > 10 else ""

        if sem.startswith("SEMESTER –") or sem.startswith("▸"):
            continue

        if code in ["(no code in source)", "(see options)", "(see pool)"] or any(x in name for x in ["Breadth –", "Lateral – 1 (", "Lateral – 2 (", "Lateral – 3 (", "Elective – 1 (", "Elective – 2 (", "Elective – 3 (", "Elective – 4 (", "Elective – 5 (", "Elective – 6 ("]):
            slots.append((sem, name, code, creds))
            continue

        if " / " in code:
            parts_c = [c.strip() for c in code.split(" / ")]
            parts_n = [n.strip() for n in name.split(" / ")]
            parts_l = [l.strip() for l in ltp.split(" / ")]
            parts_cr = [cr.strip() for cr in creds.split(" / ")]
            
            for i, c in enumerate(parts_c):
                n = parts_n[i] if i < len(parts_n) else parts_n[-1]
                l = parts_l[i] if i < len(parts_l) else parts_l[-1]
                cr = parts_cr[i] if i < len(parts_cr) else parts_cr[-1]
                if " or " in c:
                    sub_c = [sc.strip() for sc in c.split(" or ")]
                    sub_n = [sn.strip() for sn in n.split(" or ")]
                    sub_l = [sl.strip() for sl in l.split(" or ")]
                    for j, sc in enumerate(sub_c):
                        sn = sub_n[j] if j < len(sub_n) else sub_n[-1]
                        sl = sub_l[j] if j < len(sub_l) else sub_l[-1]
                        if sc not in courses:
                            courses[sc] = {"name": sn, "ltp": sl, "credits": cr, "semesters": set([sem])}
                        else:
                            courses[sc]["semesters"].add(sem)
                else:
                    if c not in courses:
                        courses[c] = {"name": n, "ltp": l, "credits": cr, "semesters": set([sem])}
                    else:
                        courses[c]["semesters"].add(sem)
            continue

        if code:
            if code not in courses:
                courses[code] = {"name": name, "ltp": ltp, "credits": creds, "semesters": set([sem])}
            else:
                courses[code]["semesters"].add(sem)

    # Syllabus only
    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            code = r["Course Code"].strip()
            courses[code] = {"name": r["Course Name"].strip(), "ltp": r["L-T-P"].strip(), "credits": r["Credits"].strip(), "semesters": set(["Syllabus-only"])}

    print(f"Unique courses count: {len(courses)}")
    print(f"Slots count: {len(slots)}")
    for s in slots:
        print(f"  Slot: {s}")

    return courses, slots

if __name__ == "__main__":
    analyze_courses_and_slots()

