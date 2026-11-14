import csv
import re

def inspect_prof_names():
    with open("data/raw/ee/research_projects_v2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, r in enumerate(reader, 1):
            prof = r["Prof. Name (PI / Co-PI)"].strip()
            print(f"{i:2d}: {prof}")

if __name__ == "__main__":
    inspect_prof_names()

