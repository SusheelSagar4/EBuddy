import csv
import re

def normalize_faculty():
    with open("data/raw/ee/research_projects_v2.csv", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        v2_rows = list(reader)

    persons = set()
    groups = set()

    for idx, r in enumerate(v2_rows, 1):
        prof_raw = r["Prof. Name (PI / Co-PI)"].strip()
        
        # Handle known composite group strings first or split
        # Special cases:
        # "Interdisciplinary Team (SECS & School of Infrastructure)" -> Group
        # "Dr. Anish Karmakar (SMMME) & SECS Control/Power Team" -> Person + Group
        # "Dr. Vijay Shankar Pasupureddi & SECS IoT/VLSI Team" -> Person + Group
        # "Dr. Navjeet Bagga (Co-PI, with Prof. S. Dasgupta)" -> Two persons: Dr. Navjeet Bagga, Prof. S. Dasgupta
        # "Dr. Nitya Tiwari, Dr. Himanshu Padole & Dr. Abhik Jana" -> Three persons
        # "Dr. Chandrashekhar Narayan Bhende / Dr. Chandrashekhar Perumalla" -> Two persons
        
        items = []
        if "Interdisciplinary Team" in prof_raw:
            items.append((prof_raw, False))
        else:
            # Check for with Prof. S. Dasgupta
            clean = prof_raw
            if "with Prof. S. Dasgupta" in clean:
                clean = clean.replace("(Co-PI, with Prof. S. Dasgupta)", "")
                items.append(("Prof. S. Dasgupta", True))
            
            # Split by & or , or /
            # But don't split Control/Power or IoT/VLSI
            clean = clean.replace("SECS Control/Power Team", "SECS_CONTROL_POWER_TEAM")
            clean = clean.replace("SECS IoT/VLSI Team", "SECS_IOT_VLSI_TEAM")
            
            parts = re.split(r"&|,|/", clean)
            for p in parts:
                p = p.strip()
                if not p:
                    continue
                p = p.replace("SECS_CONTROL_POWER_TEAM", "SECS Control/Power Team")
                p = p.replace("SECS_IOT_VLSI_TEAM", "SECS IoT/VLSI Team")
                p = re.sub(r"\(PI\)", "", p)
                p = re.sub(r"\(Co-PI\)", "", p)
                p = re.sub(r"\(IITBBS Lead\)", "", p)
                p = p.strip()
                if not p:
                    continue
                is_grp = any(x in p for x in ["Team", "Group", "Consortium"])
                items.append((p, not is_grp))

        for name, is_p in items:
            if is_p:
                persons.add(name)
            else:
                groups.add(name)

    print(f"Total Unique Persons: {len(persons)}")
    for p in sorted(persons):
        print(f"  Person: {p}")
    print(f"\nTotal Unique Groups: {len(groups)}")
    for g in sorted(groups):
        print(f"  Group: {g}")

    # Check rule: no faculty row with is_person=true contains "&", "Team", "Group"
    invalid_persons = [p for p in persons if any(x in p for x in ["&", "Team", "Group"])]
    print(f"\nInvalid persons containing &, Team, Group: {invalid_persons}")

if __name__ == "__main__":
    normalize_faculty()

