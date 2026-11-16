import csv

def inspect_all_prereqs():
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows += list(reader)

    all_prereq_entries = []
    for r in rows:
        if not r or not any(r):
            continue
        sem = r[0].strip()
        if sem.startswith("SEMESTER –") or sem.startswith("▸"):
            continue
        name = r[1].strip() if len(r) > 1 else ""
        code = r[2].strip() if len(r) > 2 else ""
        prereq = r[7].strip() if len(r) > 7 else ""
        if code in ["(no code in source)", "(see options)", "(see pool)"]:
            continue
        if prereq and prereq not in ["—", "None"]:
            all_prereq_entries.append((code, name, prereq))

    print(f"Courses with non-empty prereqs: {len(all_prereq_entries)}")
    for c, n, p in all_prereq_entries:
        print(f"{c:30s} | {p}")

if __name__ == "__main__":
    inspect_all_prereqs()

