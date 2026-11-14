import csv

def list_data_issues():
    with open("data/raw/ee/curriculum_notes_discrepancies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        issues = list(reader)

    print(f"Loaded {len(issues)} official discrepancy issues:")
    for r in issues:
        print(f"Issue #{r['#']}: {r['Course / Item']}")
        print(f"  Source PDF issue: {r['Issue found in the source PDF']}")
        print(f"  Workbook treatment: {r['How it is shown in this workbook']}\n")

if __name__ == "__main__":
    list_data_issues()

