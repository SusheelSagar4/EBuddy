"""
Ingestion and structuring script for:
1. Library Publications Data -> data/raw/library/
2. Higher Studies Database -> data/raw/higher_studies/ & data/seed/higher_studies/
"""

import os
import re
import csv
import html
import zipfile
import xml.etree.ElementTree as ET

# Paths
SRC_LIB_XLS = "C:/Users/SUSHEEL SAGAR/.gemini/antigravity/brain/8a3159a0-6f9f-46f9-b7aa-060120871c03/.user_uploaded/media_1794647707354_f8b30e84.xls"
SRC_HS_XLSX = "C:/Users/SUSHEEL SAGAR/.gemini/antigravity/brain/8a3159a0-6f9f-46f9-b7aa-060120871c03/.user_uploaded/media_1794647743389_24fb1e07.xlsx"

DATA_RAW_LIB = os.path.join("data", "raw", "library")
DATA_RAW_HS = os.path.join("data", "raw", "higher_studies")
DATA_SEED_HS = os.path.join("data", "seed", "higher_studies")

os.makedirs(DATA_RAW_LIB, exist_ok=True)
os.makedirs(DATA_RAW_HS, exist_ok=True)
os.makedirs(DATA_SEED_HS, exist_ok=True)

# -------------------------------------------------------------------------
# Part 1: Process Library Publications Data
# -------------------------------------------------------------------------
def process_library_data():
    print(">>> Processing Library Publications Data...")
    with open(SRC_LIB_XLS, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    tr_matches = re.findall(r'<tr[^>]*>(.*?)</tr>', content, re.DOTALL | re.IGNORECASE)
    print(f"Total HTML rows found: {len(tr_matches)}")

    publications = []
    ee_pubs = []
    mme_pubs = []
    schools_count = {}
    doc_types_count = {}

    for tr in tr_matches[2:]:  # skip banner and header
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.DOTALL | re.IGNORECASE)
        cleaned = [html.unescape(re.sub(r'<[^>]+>', '', c)).strip() for c in cells]
        if len(cleaned) >= 9:
            row = {
                "sn": cleaned[0],
                "authors": cleaned[1],
                "title": cleaned[2],
                "source_title": cleaned[3],
                "document_type": cleaned[4],
                "institute_author": cleaned[5],
                "pub_type": cleaned[6],
                "school": cleaned[7],
                "doi": cleaned[8]
            }
            publications.append(row)
            
            # School breakdown
            school = row["school"]
            schools_count[school] = schools_count.get(school, 0) + 1
            doc_types_count[row["document_type"]] = doc_types_count.get(row["document_type"], 0) + 1

            if "Electrical" in school:
                ee_pubs.append(row)
            elif "Metallurgical" in school or "Materials" in school:
                mme_pubs.append(row)

    # 1. Full publications CSV
    pub_headers = ["sn", "authors", "title", "source_title", "document_type", "institute_author", "pub_type", "school", "doi"]
    with open(os.path.join(DATA_RAW_LIB, "publications.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pub_headers)
        writer.writeheader()
        writer.writerows(publications)

    # 2. Programme-specific subsets
    with open(os.path.join(DATA_RAW_LIB, "publications_electrical.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pub_headers)
        writer.writeheader()
        writer.writerows(ee_pubs)

    with open(os.path.join(DATA_RAW_LIB, "publications_metallurgy.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=pub_headers)
        writer.writeheader()
        writer.writerows(mme_pubs)

    # 3. Summary breakdown CSV
    with open(os.path.join(DATA_RAW_LIB, "publications_summary.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["dimension", "category", "count"])
        for s, c in sorted(schools_count.items(), key=lambda x: -x[1]):
            writer.writerow(["School", s, c])
        for dt, c in sorted(doc_types_count.items(), key=lambda x: -x[1]):
            writer.writerow(["Document Type", dt, c])

    print(f"Library Publications parsed: {len(publications)} total (EE: {len(ee_pubs)}, MME: {len(mme_pubs)})")

# -------------------------------------------------------------------------
# Part 2: Process Higher Studies Database
# -------------------------------------------------------------------------
def col_to_idx(col_str):
    exp = 0
    idx = 0
    for char in reversed(col_str):
        idx += (ord(char) - ord('A') + 1) * (26 ** exp)
        exp += 1
    return idx - 1

def parse_sheet_cells(sheet_xml):
    root = ET.fromstring(sheet_xml)
    rows_data = []
    ns = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
    for row in root.iter(f'{ns}row'):
        row_cells = {}
        for c in row.iter(f'{ns}c'):
            ref = c.attrib.get('r', '')
            col_letters = ''.join(filter(str.isalpha, ref))
            col_idx = col_to_idx(col_letters) if col_letters else 0
            
            val = ''
            t = c.attrib.get('t', '')
            if t == 'inlineStr':
                is_node = c.find(f'{ns}is')
                if is_node is not None:
                    val = ''.join(t_node.text or '' for t_node in is_node.iter(f'{ns}t'))
            else:
                v_node = c.find(f'{ns}v')
                if v_node is not None:
                    val = v_node.text or ''
            row_cells[col_idx] = val
        if row_cells:
            max_col = max(row_cells.keys())
            row_list = [row_cells.get(i, '') for i in range(max_col + 1)]
            rows_data.append(row_list)
    return rows_data

def process_higher_studies_data():
    print(">>> Processing Higher Studies Database...")
    zf = zipfile.ZipFile(SRC_HS_XLSX)
    tree = ET.fromstring(zf.read('xl/workbook.xml'))
    sheets = [node.attrib['name'] for node in tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet')]

    for i, sname in enumerate(sheets, 1):
        raw_rows = parse_sheet_cells(zf.read(f'xl/worksheets/sheet{i}.xml'))
        if not raw_rows:
            continue

        # Detect if row 0 is an introductory note and row 1 is empty
        start_row = 0
        if len(raw_rows) > 2 and raw_rows[0] and not raw_rows[1][0] and len(raw_rows[0]) == 1:
            start_row = 2
        elif sname in ["Survey", "syllabus_topics", "institutions", "programmes", "admission_stats", 
                       "milestones", "prep_templates", "template_phases", "resources", "students", 
                       "evidence", "study_plans", "applications", "survey_responses"]:
            # Find the header row (first row with multiple non-empty entries)
            for r_idx, r in enumerate(raw_rows):
                non_empty = [c for c in r if c.strip()]
                if len(non_empty) > 1 and ("id" in non_empty or "exam_id" in non_empty or "section" in non_empty or "template_id" in non_empty or "source" in non_empty or "student_id" in non_empty or "programme_id" in non_empty or "response_id" in non_empty):
                    start_row = r_idx
                    break

        table_rows = raw_rows[start_row:]
        if not table_rows:
            table_rows = raw_rows

        # Target directory:
        # Lowercase sheet names are database tables -> data/seed/higher_studies/ & data/raw/higher_studies/
        # Uppercase/TitleCase (README, Survey, Schema, Sources) -> data/raw/higher_studies/
        target_csv_raw = os.path.join(DATA_RAW_HS, f"{sname}.csv")
        with open(target_csv_raw, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(table_rows)

        if sname == sname.lower() and sname not in ["readme", "sources", "schema"]:
            target_csv_seed = os.path.join(DATA_SEED_HS, f"{sname}.csv")
            with open(target_csv_seed, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(table_rows)

    # Generate README.md in data/raw/higher_studies/
    readme_rows = parse_sheet_cells(zf.read('xl/worksheets/sheet1.xml'))
    readme_lines = ["# Higher Studies Database: Clueless (IIT Bhubaneswar)\n"]
    for r in readme_rows:
        if r and r[0].strip():
            readme_lines.append(r[0].strip() + "\n")
    with open(os.path.join(DATA_RAW_HS, "README.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines))

    print(f"Higher Studies Database processed: 22 sheets extracted to {DATA_RAW_HS} and {DATA_SEED_HS}.")

if __name__ == "__main__":
    process_library_data()
    process_higher_studies_data()

