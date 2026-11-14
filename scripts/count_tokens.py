import csv
import re

def count_all_tokens():
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows += list(reader)

    tokens = []
    for r in rows:
        if not r or not any(r):
            continue
        sem = r[0].strip()
        if sem.startswith("SEMESTER –") or sem.startswith("▸"):
            continue
        code = r[2].strip() if len(r) > 2 else ""
        if code in ["(no code in source)", "(see options)", "(see pool)"]:
            continue
        prereq = r[7].strip() if len(r) > 7 else ""
        # split lines
        for line in prereq.split("\n"):
            line = line.strip()
            if not line:
                continue
            if ":" in line and not line.startswith("http"):
                _, line = line.split(":", 1)
                line = line.strip()
            for part in line.split(","):
                part = part.strip()
                if part:
                    tokens.append((code, part))

    print(f"Total prerequisite tokens found (including None/—): {len(tokens)}")
    non_none_tokens = [t for t in tokens if t[1] not in ["None", "—"]]
    print(f"Total non-None tokens: {len(non_none_tokens)}")
    
    # What if we include syllabus-only vs only semester table?
    # What if we don't duplicate Sem I / Sem II paired rows?
    print("\nBreakdown of token values:")
    token_counts = {}
    for c, t in tokens:
        token_counts[t] = token_counts.get(t, 0) + 1
    for t, cnt in sorted(token_counts.items(), key=lambda x: -x[1]):
        print(f"  {t:50s}: {cnt}")

if __name__ == "__main__":
    count_all_tokens()

