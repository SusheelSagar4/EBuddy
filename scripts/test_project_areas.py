import csv

def verify_project_areas():
    with open("data/raw/ee/research_projects_all.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)

    area_counts = {}
    for r in all_rows:
        area = r["Research Area"].strip()
        area_counts[area] = area_counts.get(area, 0) + 1

    print("Project counts per research area:")
    for a, c in area_counts.items():
        print(f"  {a:35s}: {c}")
    print(f"Total projects: {sum(area_counts.values())}")

if __name__ == "__main__":
    verify_project_areas()

