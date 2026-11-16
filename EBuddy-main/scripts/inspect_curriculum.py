import csv

def inspect_curriculum_rows():
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, 1):
            if not row or not any(row):
                continue
            sem = row[0].strip()
            name = row[1].strip() if len(row) > 1 else ""
            code = row[2].strip() if len(row) > 2 else ""
            print(f"{i:3d} | {sem:10s} | {code:25s} | {name}")

if __name__ == "__main__":
    inspect_curriculum_rows()

