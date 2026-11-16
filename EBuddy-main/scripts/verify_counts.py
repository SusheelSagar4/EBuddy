import csv

def verify_all_counts():
    counts = {}
    files = [
        "course.csv", "course_alias.csv", "course_offering.csv",
        "course_prerequisite.csv", "data_issue.csv", "faculty.csv",
        "programme_requirement.csv", "project_faculty.csv", "project_keyword.csv",
        "research_area.csv", "research_project.csv", "resource.csv",
        "resource_course.csv", "slot_option.csv"
    ]
    for fn in files:
        with open(f"data/seed/kb/{fn}", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            rows = list(reader)
            counts[fn] = len(rows)

    print("=== Generated KB Table Row Counts ===")
    for k, v in counts.items():
        print(f"  {k:30s}: {v}")

    # Inspect faculty persons vs groups
    with open("data/seed/kb/faculty.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fac = list(reader)
        persons = [x for x in fac if x["is_person"].lower() == "true"]
        groups = [x for x in fac if x["is_person"].lower() == "false"]
        print(f"\nFaculty Entities Total: {len(fac)}")
        print(f"  Persons: {len(persons)}")
        print(f"  Groups:  {len(groups)}")

    # Inspect research projects by detail level and area
    with open("data/seed/kb/research_project.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        projs = list(reader)
        full_projs = [x for x in projs if x["detail_level"] == "full"]
        title_only = [x for x in projs if x["detail_level"] == "title_only"]
        print(f"\nResearch Projects Total: {len(projs)}")
        print(f"  Detail level 'full': {len(full_projs)}")
        print(f"  Detail level 'title_only': {len(title_only)}")

    # Inspect resources by coverage status
    with open("data/seed/kb/resource.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        res = list(reader)
        cov_counts = {}
        for r in res:
            cov = r["coverage_status"]
            cov_counts[cov] = cov_counts.get(cov, 0) + 1
        print(f"\nResources Total: {len(res)}")
        print(f"  By Coverage Status:")
        for cov, cnt in sorted(cov_counts.items(), key=lambda x: -x[1]):
            print(f"    {cov:30s}: {cnt}")

    # Inspect data issues
    with open("data/seed/kb/data_issue.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        issues = list(reader)
        print(f"\nData Issues Total: {len(issues)}")
        for i in issues:
            if i["status"] == "unresolved":
                print(f"  [UNRESOLVED - {i['severity'].upper()}] {i['entity_key']}: {i['description']}")

if __name__ == "__main__":
    verify_all_counts()

