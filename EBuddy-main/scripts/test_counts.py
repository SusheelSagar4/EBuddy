import csv
import re
import json

def analyze():
    # 1. Parse curriculum
    with open("data/raw/ee/curriculum_semester_table.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        sem_rows = list(reader)

    with open("data/raw/ee/curriculum_syllabus_only.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        syllabus_only_rows = list(reader)

    with open("data/raw/ee/curriculum_notes_discrepancies.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        discrepancies_rows = list(reader)

    with open("data/raw/ee/video_playlists.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        video_rows = list(reader)

    with open("data/raw/ee/research_projects_all.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        proj_all_rows = list(reader)

    with open("data/raw/ee/research_projects_v2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        proj_v2_rows = list(reader)

    print(f"Loaded raw rows:")
    print(f"  curriculum_semester_table: {len(sem_rows)}")
    print(f"  curriculum_syllabus_only: {len(syllabus_only_rows)}")
    print(f"  curriculum_notes_discrepancies: {len(discrepancies_rows)}")
    print(f"  video_playlists: {len(video_rows)}")
    print(f"  research_projects_all: {len(proj_all_rows)}")
    print(f"  research_projects_v2: {len(proj_v2_rows)}")

if __name__ == "__main__":
    analyze()

