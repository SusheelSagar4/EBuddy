# Central Library Publications Catalog — Documentation

**Source:** `media_1794647707354_f8b30e84.xls` (`Library_Books_Data.xls`)  
**Publisher:** Central Library, IIT Bhubaneswar  
**Total Publications:** 3,000 records  
**Database Status:** **NOT LOADED INTO POSTGRESQL** (Stored in `data/raw/library/` for institutional reference).

---

## 1. Subset Filtering Methodology

The full 3,000-record institutional repository was partitioned into discipline-specific subsets using keyword classification on the `school` column:

| File Path | Filter Rule Applied | Matching School String | Count | Classification Method |
|---|---|---|---|---|
| `data/raw/library/publications_electrical.csv` | `"Electrical" in school` | School of Electrical Sciences (SECS) | 765 rows | `keyword` |
| `data/raw/library/publications_metallurgy.csv` | `"Metallurgical" in school OR "Materials" in school` | School of Minerals, Metallurgical and Materials Engineering (SMMME) | 176 rows | `keyword` |
| `data/raw/library/publications.csv` | *All records* | All IIT BBS academic schools | 3,000 rows | `unfiltered` |

---

## 2. Compliance Notice

1. **No Database Contamination:** Table `kb.publication` in PostgreSQL contains only the 103 selected key publications extracted from the SMMME Faculty Research Profiles PDF. The 3,000 Central Library publications remain strictly in `data/raw/library/` as raw reference data.
2. **Classification Method:** Every record in the discipline subsets is explicitly tagged with `classification_method = 'keyword'` to distinguish rule-based school string matching from verified author ORCID/Scopus affiliations.

