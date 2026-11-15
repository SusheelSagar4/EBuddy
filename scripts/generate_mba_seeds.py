import os
import csv

def generate_all_seeds():
    mba_dir = os.path.join("data", "seed", "mba")
    c2m_dir = os.path.join("data", "seed", "core_to_mba")
    os.makedirs(mba_dir, exist_ok=True)
    os.makedirs(c2m_dir, exist_ok=True)

    # 1. mba_routes.csv
    with open(os.path.join(mba_dir, "mba_routes.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "description", "typical_timing"])
        writer.writerow(["MBA-RT1", "MBA in India right after B.Tech", "Take CAT and other entrance tests in final year and join a two-year programme straight after graduation.", "Entrance tests in 4th year (Nov to Jan); programme starts after graduation"])
        writer.writerow(["MBA-RT2", "MBA in India after work experience", "Work for some years after B.Tech, then apply; many programmes give weight to work experience.", "Entrance tests after 1 to 3+ years of work"])
        writer.writerow(["MBA-RT3", "MBA abroad", "Apply with GMAT or GRE scores, usually after several years of work experience.", "Usually after 2 to 5 years of work"])
        writer.writerow(["MBA-RT4", "Masters in Management abroad", "Pre-experience management masters for recent graduates, usually with GMAT or GRE.", "Final year or soon after graduation"])

    # 2. mba_exams.csv
    with open(os.path.join(mba_dir, "mba_exams.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "conducting_body", "route_ids", "pattern", "total_questions", "total_minutes", "marking_scheme", "score_scale", "attempts_rule", "eligibility", "official_url", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-EX-CAT", "CAT", "IIMs (convening IIM for 2026 not officially confirmed on source page)", "MBA-RT1;MBA-RT2", "3 sections: VARC, DILR, QA; 40 minutes per section", "68 (expected 24/22/22; not fixed)", "120", "+3 per correct answer; -1 per wrong MCQ; no negative marking on non-MCQ", "", "", "Bachelor's degree with at least 50% (45% SC/ST); final-year students may apply; no age limit", "https://iimcat.ac.in", "https://www.careers360.com/mba/articles/cat-2026-registration-date-official-website-syllabus-eligibility-admit-card-result-cutoff-mba-admission-2027-29", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "XAT", "XLRI", "MBA-RT1;MBA-RT2", "Verbal Ability and Logical Reasoning, Decision Making, Quantitative Aptitude and Data Interpretation, General Knowledge; no sectional time limits", "About 95", "180", "Skip limit before penalty stated as both 8 and 12 on the official page; confirm in bulletin", "", "", "Not stated on source page", "https://xatonline.in", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "SNAP", "Symbiosis International (Deemed University)", "MBA-RT1;MBA-RT2", "General English, Analytical and Logical Reasoning, Quantitative/Data Interpretation/Data Sufficiency, Ethics/Morality/Values; four options per question", "60", "60", "Wrong answer carries 25% negative marking", "", "Up to 3 attempts; higher score used for final percentile", "Graduates with at least 50% (45% SC/ST); final-year candidates may apply if the programme allows", "https://www.snaptest.org", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-NMAT", "NMAT", "GMAC", "MBA-RT1;MBA-RT2", "108 multiple-choice questions", "108", "120", "", "36 to 360 (scaled)", "Up to 3 attempts in a testing cycle; only first attempt considered for NMIMS Mumbai admissions", "Bachelor's degree in any discipline with at least 50%; final-year students can apply; no work experience or age limit", "https://www.mba.com", "https://www.careers360.com/mba/articles/nmat-2026-registration-date-fees-eligibility-exam-dates-top-mba-colleges", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-CMAT", "CMAT", "National Testing Agency (NTA)", "MBA-RT1;MBA-RT2", "Not covered on source page", "", "", "", "", "", "Final-year graduation students generally eligible per source; confirm in official notification", "https://cmat.nta.nic.in", "https://cracku.in/cmat-2027-notification/", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-GMAT", "GMAT Focus Edition", "GMAC", "MBA-RT1;MBA-RT3;MBA-RT4", "Quantitative Reasoning, Verbal Reasoning, Data Insights; sections in any order; one optional 10-minute break", "64", "135", "", "Total 205 to 805 in steps of 10 (all end in 5); sections 60 to 90; scores valid 5 years", "", "", "https://www.mba.com", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "official", "2026-11-15", "FALSE", ""])

    # 3. mba_exam_cycles.csv
    with open(os.path.join(mba_dir, "mba_exam_cycles.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["exam_id", "cycle", "organiser", "reg_open", "reg_close", "exam_dates", "admit_card_date", "result_date", "fee", "notes", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-EX-CAT", "2026", "Not officially confirmed", "2026-08-03", "2026-09-22", "2026-11-29", "2026-11-04", "Expected around 2026-12-20", "", "Source headline says registration extended without a new date; another aggregator gave result as first week of Jan 2027. Confirm on iimcat.ac.in", "https://www.careers360.com/mba/articles/cat-2026-registration-date-official-website-syllabus-eligibility-admit-card-result-cutoff-mba-admission-2027-29", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "2027", "XLRI", "2026-07-15", "2026-12-06", "2027-01-03 (2:00 pm to 5:00 pm)", "2026-12-20 (tentative)", "", "", "", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "2026", "Symbiosis International (Deemed University)", "", "2026-11-25", "2026-12-13; 2026-12-19; 2026-12-26", "", "2027-01-12", "", "", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-NMAT", "2026", "GMAC", "2026-08-20", "2026-10-10", "Window 2026-11-02 to 2026-12-20", "7 days before the chosen test date", "Within 48 to 72 hours of each attempt", "Rs 3000 plus taxes", "Later headlines on source say registration deadline extended to Oct 25 then Oct 31; confirm with GMAC", "https://www.careers360.com/mba/articles/nmat-2026-registration-date-fees-eligibility-exam-dates-top-mba-colleges", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-CMAT", "2027", "National Testing Agency (NTA)", "", "", "2027-02-07 (NTA calendar; tentative)", "", "Expected 2027-02-20", "", "Registration dates on source are expected, not official", "https://cracku.in/cmat-2027-notification/", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-GMAT", "Year-round", "GMAC", "Rolling", "Rolling", "Year-round", "", "", "", "", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "official", "2026-11-15", "FALSE", ""])

    # 4. mba_exam_sections.csv
    with open(os.path.join(mba_dir, "mba_exam_sections.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["exam_id", "section", "questions", "minutes", "notes", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-EX-CAT", "Verbal Ability and Reading Comprehension (VARC)", "24 (expected)", "40", "", "https://www.careers360.com/mba/articles/cat-2026-registration-date-official-website-syllabus-eligibility-admit-card-result-cutoff-mba-admission-2027-29", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-CAT", "Data Interpretation and Logical Reasoning (DILR)", "22 (expected)", "40", "", "https://www.careers360.com/mba/articles/cat-2026-registration-date-official-website-syllabus-eligibility-admit-card-result-cutoff-mba-admission-2027-29", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-CAT", "Quantitative Aptitude (QA)", "22 (expected)", "40", "", "https://www.careers360.com/mba/articles/cat-2026-registration-date-official-website-syllabus-eligibility-admit-card-result-cutoff-mba-admission-2027-29", "aggregator", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "Verbal Ability and Logical Reasoning", "About 26", "", "No sectional time limits", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "Decision Making", "About 21", "", "", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "Quantitative Aptitude and Data Interpretation", "About 28", "", "", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-XAT", "General Knowledge", "About 20", "", "About 8 static and 12 current affairs", "https://xatonline.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "General English", "10", "", "", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "Analytical and Logical Reasoning", "20", "", "", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "Quantitative, Data Interpretation and Data Sufficiency", "20", "", "", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-SNAP", "Ethics, Morality and Values", "10", "", "", "https://www.snaptest.org/blogs/all-you-need-to-know-about-this-mba-entrance-exam", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-GMAT", "Quantitative Reasoning", "21", "45", "Section score 60 to 90", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-GMAT", "Verbal Reasoning", "23", "45", "Section score 60 to 90", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-EX-GMAT", "Data Insights", "20", "45", "Section score 60 to 90", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "official", "2026-11-15", "FALSE", ""])

    # 5. mba_syllabus_topics.csv
    with open(os.path.join(mba_dir, "mba_syllabus_topics.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "exam_id", "section", "topic", "subtopics", "source_type", "verified", "verified_by"])
        writer.writerow(["MBA-TP01", "MBA-EX-CAT", "QA", "Arithmetic", "Percentages, profit and loss, ratio and proportion, averages, mixtures, simple and compound interest, time and work, time speed distance", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP02", "MBA-EX-CAT", "QA", "Algebra", "Linear and quadratic equations, inequalities, functions, logarithms, progressions", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP03", "MBA-EX-CAT", "QA", "Number systems", "Divisibility, HCF and LCM, remainders, factors", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP04", "MBA-EX-CAT", "QA", "Geometry and mensuration", "Triangles, circles, polygons, coordinate geometry, areas and volumes", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP05", "MBA-EX-CAT", "QA", "Modern maths", "Permutations and combinations, probability, set theory", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP06", "MBA-EX-CAT", "DILR", "Data interpretation", "Tables, bar and line charts, pie charts, caselets", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP07", "MBA-EX-CAT", "DILR", "Logical reasoning", "Arrangements, scheduling, games and tournaments, Venn diagrams, selection and distribution puzzles", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP08", "MBA-EX-CAT", "VARC", "Reading comprehension", "Main idea, inference, tone, specific detail", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP09", "MBA-EX-CAT", "VARC", "Verbal ability", "Para summary, para jumbles, odd sentence out", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP10", "MBA-EX-XAT", "Decision Making", "Decision making", "Case-based choices in business and ethical situations", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP11", "MBA-EX-XAT", "General Knowledge", "General knowledge", "Static GK and current affairs", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP12", "MBA-EX-SNAP", "Ethics, Morality and Values", "Ethics", "Values-based situational questions", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP13", "MBA-EX-GMAT", "Data Insights", "Data insights", "Data sufficiency, multi-source reasoning, table analysis, graphics interpretation, two-part analysis", "team_curated", "FALSE", ""])
        writer.writerow(["MBA-TP14", "MBA-EX-GMAT", "Verbal Reasoning", "Verbal reasoning", "Reading comprehension, critical reasoning", "team_curated", "FALSE", ""])

    # 6. mba_institutions.csv
    with open(os.path.join(mba_dir, "mba_institutions.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "type", "city", "official_url", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-IN-IIMA", "Indian Institute of Management Ahmedabad", "IIM", "Ahmedabad", "https://www.iima.ac.in", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-IIMB", "Indian Institute of Management Bangalore", "IIM", "Bengaluru", "https://www.iimb.ac.in", "https://www.iimb.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-IIMC", "Indian Institute of Management Calcutta", "IIM", "Kolkata", "https://www.iimcal.ac.in", "https://www.iimcal.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-IIML", "Indian Institute of Management Lucknow", "IIM", "Lucknow", "https://www.iiml.ac.in", "https://www.iiml.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-IIMK", "Indian Institute of Management Kozhikode", "IIM", "Kozhikode", "https://iimk.ac.in", "https://iimk.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-IIMI", "Indian Institute of Management Indore", "IIM", "Indore", "https://www.iimidr.ac.in", "https://www.iimidr.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-ISB", "Indian School of Business", "B-school", "Hyderabad and Mohali", "https://www.isb.edu", "https://www.isb.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-FMS", "Faculty of Management Studies, University of Delhi", "University department", "New Delhi", "https://fms.edu", "https://fms.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-XLRI", "XLRI", "B-school", "Jamshedpur", "https://www.xlri.ac.in", "https://www.xlri.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-SPJIMR", "S.P. Jain Institute of Management and Research", "B-school", "Mumbai", "https://www.spjimr.org", "https://www.spjimr.org", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-MDI", "Management Development Institute", "B-school", "Gurugram", "https://www.mdi.ac.in", "https://www.mdi.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-JBIMS", "Jamnalal Bajaj Institute of Management Studies", "University institute", "Mumbai", "https://jbims.edu", "https://jbims.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-IN-DMSIITD", "Department of Management Studies, IIT Delhi", "IIT department", "New Delhi", "https://dms.iitd.ac.in", "https://dms.iitd.ac.in", "official", "2026-11-15", "FALSE", ""])

    # 7. mba_programmes.csv
    with open(os.path.join(mba_dir, "mba_programmes.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "institution_id", "programme_name", "degree", "duration_months", "exams_accepted", "work_ex_policy", "selection_process", "application_deadline", "fees", "official_url", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-PG-IIMA", "MBA-IN-IIMA", "MBA (also referred to as PGP)", "MBA", "24", "MBA-EX-CAT", "Fresher eligible", "CAT + AWT + PI", "2026-09-22", "", "https://www.iima.ac.in", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-IIMC", "MBA-IN-IIMC", "MBA", "MBA", "24", "MBA-EX-CAT", "Fresher eligible", "CAT + WAT + PI", "2026-09-22", "", "https://www.iimcal.ac.in", "https://www.iimcal.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-ISB", "MBA-IN-ISB", "Post Graduate Programme in Management (PGP)", "PGP", "12", "MBA-EX-GMAT", "Minimum 24 months work experience", "GMAT + Essays + PI", "2026-12-01", "", "https://www.isb.edu", "https://www.isb.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-FMS", "MBA-IN-FMS", "Full-time MBA", "MBA", "24", "MBA-EX-CAT", "Fresher eligible", "CAT + Extempore + PI", "2026-12-15", "", "https://fms.edu", "https://fms.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-XLRI", "MBA-IN-XLRI", "PGDM (Business Management)", "PGDM", "24", "MBA-EX-XAT", "Fresher eligible", "XAT + GD/PI", "2026-12-06", "", "https://www.xlri.ac.in", "https://www.xlri.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-DMSIITD", "MBA-IN-DMSIITD", "MBA", "MBA", "24", "MBA-EX-CAT", "Fresher eligible (Engineering degree preferred)", "CAT + PI", "2027-01-31", "", "https://dms.iitd.ac.in", "https://dms.iitd.ac.in", "official", "2026-11-15", "FALSE", ""])

    # 8. mba_admission_stats.csv
    with open(os.path.join(mba_dir, "mba_admission_stats.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["programme_id", "year", "category", "stage", "cutoff_value", "cutoff_type", "source_url", "source_type", "retrieved_on", "verified", "verified_by"])
        writer.writerow(["MBA-PG-IIMA", "2024", "GEN", "shortlist", "99.0", "percentile", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-IIMA", "2024", "NC-OBC", "shortlist", "94.0", "percentile", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-IIMA", "2024", "SC", "shortlist", "85.0", "percentile", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-IIMA", "2024", "ST", "shortlist", "75.0", "percentile", "https://www.iima.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-IIMC", "2024", "GEN", "shortlist", "99.2", "percentile", "https://www.iimcal.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-FMS", "2024", "GEN", "shortlist", "98.5", "percentile", "https://fms.edu", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-XLRI", "2024", "GEN", "shortlist", "95.0", "percentile", "https://www.xlri.ac.in", "official", "2026-11-15", "FALSE", ""])
        writer.writerow(["MBA-PG-DMSIITD", "2024", "GEN", "shortlist", "96.0", "percentile", "https://dms.iitd.ac.in", "official", "2026-11-15", "FALSE", ""])

    # 9. mba_milestones.csv
    with open(os.path.join(mba_dir, "mba_milestones.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "route_id", "name", "typical_timing", "depends_on", "exam_id"])
        writer.writerow(["MBA-MS01", "MBA-RT1", "Start CAT preparation", "At least 3 to 12 months before the exam, by chosen template", "", ""])
        writer.writerow(["MBA-MS02", "MBA-RT1", "CAT registration", "Aug to Sep (dates from exam_cycles)", "MBA-MS01", "MBA-EX-CAT"])
        writer.writerow(["MBA-MS03", "MBA-RT1", "NMAT testing window", "Nov to Dec (dates from exam_cycles)", "", "MBA-EX-NMAT"])
        writer.writerow(["MBA-MS04", "MBA-RT1", "CAT exam", "Late Nov (dates from exam_cycles)", "MBA-MS02", "MBA-EX-CAT"])
        writer.writerow(["MBA-MS05", "MBA-RT1", "SNAP tests", "Dec (dates from exam_cycles)", "", "MBA-EX-SNAP"])
        writer.writerow(["MBA-MS06", "MBA-RT1", "XAT exam", "Early Jan (dates from exam_cycles)", "", "MBA-EX-XAT"])
        writer.writerow(["MBA-MS07", "MBA-RT1", "CAT result and institute shortlists", "Dec to Feb", "MBA-MS04", "MBA-EX-CAT"])
        writer.writerow(["MBA-MS08", "MBA-RT1", "Written ability test and personal interview rounds", "Feb to Apr", "MBA-MS07", ""])
        writer.writerow(["MBA-MS09", "MBA-RT1", "Final admission offers", "Apr to May", "MBA-MS08", ""])
        writer.writerow(["MBA-MS10", "MBA-RT1", "Clash check: end-semester exams", "Nov to Dec", "", ""])
        writer.writerow(["MBA-MS11", "MBA-RT1", "Clash check: campus placements", "Dec to Jan (team sets exact window)", "", ""])
        writer.writerow(["MBA-MS12", "MBA-RT2", "Decide target intake year and build work profile", "During work years", "", ""])
        writer.writerow(["MBA-MS13", "MBA-RT3", "GMAT or GRE attempt", "6 to 12 months before application rounds", "", "MBA-EX-GMAT"])
        writer.writerow(["MBA-MS14", "MBA-RT3", "Essays, recommendations and applications", "By each school's round deadline (from programmes)", "MBA-MS13", ""])

    # 10. mba_prep_templates.csv
    with open(os.path.join(mba_dir, "mba_prep_templates.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "exam_id", "speed_months", "weekly_hours", "phases_summary", "readiness_rule"])
        writer.writerow(["MBA-T-CAT12", "MBA-EX-CAT", "12", "6", "Foundations, building, mocks, revision", "Last 5 full mocks at or above the student's target band; no section below 60% accuracy in the last 3 mocks"])
        writer.writerow(["MBA-T-CAT6", "MBA-EX-CAT", "6", "12", "Foundations, building, mocks, revision", "Last 5 full mocks at or above the student's target band; no section below 60% accuracy in the last 3 mocks"])
        writer.writerow(["MBA-T-CAT3", "MBA-EX-CAT", "3", "24", "Foundations, building, mocks, revision", "Last 5 full mocks at or above the student's target band; no section below 60% accuracy in the last 3 mocks"])
        writer.writerow(["MBA-T-XAT1", "MBA-EX-XAT", "1", "8", "Decision making practice, GK, XAT-pattern mocks (add-on to a CAT template)", "Two XAT-pattern mocks at or above target band"])
        writer.writerow(["MBA-T-SNAP1", "MBA-EX-SNAP", "1", "6", "Speed drills and SNAP-pattern mocks (add-on to a CAT template)", "Two SNAP-pattern mocks at or above target band"])
        writer.writerow(["MBA-T-GMAT3", "MBA-EX-GMAT", "3", "12", "Diagnostic, section review, Data Insights practice, official practice tests", "Official practice test at or above target"])
        writer.writerow(["MBA-T-PI2", "", "2", "8", "Written ability test and personal interview preparation", "Two mock interviews scored at least 3 of 4 on every rubric criterion"])

    # 11. mba_template_phases.csv
    with open(os.path.join(mba_dir, "mba_template_phases.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["template_id", "order", "name", "share_of_weeks", "sections", "checkpoint"])
        writer.writerow(["MBA-T-CAT12", "1", "Foundations: QA basics, reading habit, LR basics", "0.25", "QA;VARC;DILR", "Topic tests of at least 60%"])
        writer.writerow(["MBA-T-CAT12", "2", "Building: sectional tests, DILR set practice, RC volume", "0.25", "QA;VARC;DILR", "Sectional tests of at least 60%"])
        writer.writerow(["MBA-T-CAT12", "3", "Mocks: full-length mocks with analysis", "0.35", "QA;VARC;DILR", "Mock percentile trend over the last 5 mocks"])
        writer.writerow(["MBA-T-CAT12", "4", "Revision and exam strategy", "0.15", "QA;VARC;DILR", "Final 2 mocks within target band"])
        writer.writerow(["MBA-T-CAT6", "1", "Foundations: QA basics, reading habit, LR basics", "0.25", "QA;VARC;DILR", "Topic tests of at least 60%"])
        writer.writerow(["MBA-T-CAT6", "2", "Building: sectional tests, DILR set practice, RC volume", "0.25", "QA;VARC;DILR", "Sectional tests of at least 60%"])
        writer.writerow(["MBA-T-CAT6", "3", "Mocks: full-length mocks with analysis", "0.35", "QA;VARC;DILR", "Mock percentile trend over the last 5 mocks"])
        writer.writerow(["MBA-T-CAT6", "4", "Revision and exam strategy", "0.15", "QA;VARC;DILR", "Final 2 mocks within target band"])
        writer.writerow(["MBA-T-CAT3", "1", "Foundations: QA basics, reading habit, LR basics", "0.25", "QA;VARC;DILR", "Topic tests of at least 60%"])
        writer.writerow(["MBA-T-CAT3", "2", "Building: sectional tests, DILR set practice, RC volume", "0.25", "QA;VARC;DILR", "Sectional tests of at least 60%"])
        writer.writerow(["MBA-T-CAT3", "3", "Mocks: full-length mocks with analysis", "0.35", "QA;VARC;DILR", "Mock percentile trend over the last 5 mocks"])
        writer.writerow(["MBA-T-CAT3", "4", "Revision and exam strategy", "0.15", "QA;VARC;DILR", "Final 2 mocks within target band"])
        writer.writerow(["MBA-T-XAT1", "1", "Decision making cases", "0.4", "Decision Making", "Case set accuracy"])
        writer.writerow(["MBA-T-XAT1", "2", "GK static and current affairs reading", "0.2", "General Knowledge", "GK quiz"])
        writer.writerow(["MBA-T-XAT1", "3", "XAT-pattern mocks", "0.4", "All", "Mock score"])
        writer.writerow(["MBA-T-SNAP1", "1", "Speed drills", "0.5", "All", "Timed drill accuracy"])
        writer.writerow(["MBA-T-SNAP1", "2", "SNAP-pattern mocks", "0.5", "All", "Mock score"])
        writer.writerow(["MBA-T-GMAT3", "1", "Diagnostic", "0.05", "All", "Official practice test"])
        writer.writerow(["MBA-T-GMAT3", "2", "Quant and Verbal review", "0.35", "Quantitative Reasoning;Verbal Reasoning", "Section quizzes"])
        writer.writerow(["MBA-T-GMAT3", "3", "Data Insights practice", "0.3", "Data Insights", "Section quizzes"])
        writer.writerow(["MBA-T-GMAT3", "4", "Official practice tests and review", "0.3", "All", "Practice test score"])
        writer.writerow(["MBA-T-PI2", "1", "Profile story: why MBA, why now, goals", "0.25", "PI", "Story reviewed"])
        writer.writerow(["MBA-T-PI2", "2", "Academic and branch fundamentals revision", "0.25", "PI", "Mock technical questions"])
        writer.writerow(["MBA-T-PI2", "3", "Written ability test practice", "0.2", "WAT", "Essay rubric score"])
        writer.writerow(["MBA-T-PI2", "4", "Mock interviews with feedback", "0.3", "PI", "Rubric score"])

    # 12. mba_practice_items.csv
    items = [
        ("MBA-Q001", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "A price rises by 20% and then falls by 20%. What is the net percentage change? (negative for a fall)", "", "", "", "", "-4", "1.2 x 0.8 = 0.96, a 4% fall.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q002", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "A can finish a job in 10 days and B in 15 days. In how many days can they finish it together?", "", "", "", "", "6", "Combined rate 1/10 + 1/15 = 1/6 per day.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q003", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "A 150 m long train runs at 54 km/h. How many seconds does it take to pass a pole?", "", "", "", "", "10", "54 km/h = 15 m/s; 150 / 15 = 10 s.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q004", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "What is the simple interest on Rs 5000 at 8% per year for 3 years (in Rs)?", "", "", "", "", "1200", "5000 x 0.08 x 3 = 1200.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q005", "MBA-EX-CAT", "QA", "Arithmetic", "2", "numeric", "What is the compound interest on Rs 10000 at 10% per year for 2 years, compounded annually (in Rs)?", "", "", "", "", "2100", "Amount = 10000 x 1.1 x 1.1 = 12100; interest = 2100.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q006", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "Rs 640 is divided in the ratio 3:5. What is the larger share (in Rs)?", "", "", "", "", "400", "640 x 5/8 = 400.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q007", "MBA-EX-CAT", "QA", "Arithmetic", "2", "numeric", "The average of 5 numbers is 20. After removing one number, the average of the rest is 18. What number was removed?", "", "", "", "", "28", "Total 100; remaining total 72; removed 28.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q008", "MBA-EX-CAT", "QA", "Arithmetic", "1", "numeric", "An item bought for Rs 400 is sold for Rs 500. What is the profit percentage?", "", "", "", "", "25", "Profit 100 on cost 400 = 25%.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q009", "MBA-EX-CAT", "QA", "Arithmetic", "2", "numeric", "20 litres of a mixture has 25% alcohol. After adding 5 litres of water, what is the alcohol percentage?", "", "", "", "", "20", "Alcohol 5 L in 25 L = 20%.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q010", "MBA-EX-CAT", "QA", "Arithmetic", "2", "numeric", "A car goes from P to Q at 60 km/h and returns at 40 km/h. What is the average speed for the round trip (km/h)?", "", "", "", "", "48", "Harmonic mean: 2 x 60 x 40 / 100 = 48.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q011", "MBA-EX-CAT", "QA", "Arithmetic", "2", "numeric", "Pipe A fills a tank in 6 hours; pipe B empties it in 12 hours. With both open, how many hours to fill the empty tank?", "", "", "", "", "12", "Net rate 1/6 - 1/12 = 1/12 per hour.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q012", "MBA-EX-CAT", "QA", "Number systems", "1", "numeric", "What is the HCF of 36 and 48?", "", "", "", "", "12", "36 = 2^2 x 3^2, 48 = 2^4 x 3; HCF = 2^2 x 3 = 12.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q013", "MBA-EX-CAT", "QA", "Number systems", "1", "numeric", "What is the LCM of 36 and 48?", "", "", "", "", "144", "2^4 x 3^2 = 144.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q014", "MBA-EX-CAT", "QA", "Number systems", "2", "numeric", "How many positive divisors does 72 have?", "", "", "", "", "12", "72 = 2^3 x 3^2, so (3+1)(2+1) = 12.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q015", "MBA-EX-CAT", "QA", "Number systems", "2", "numeric", "What is the remainder when 2^10 is divided by 7?", "", "", "", "", "2", "2^3 = 8 leaves 1, so 2^9 leaves 1 and 2^10 leaves 2.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q016", "MBA-EX-CAT", "QA", "Algebra", "1", "numeric", "The roots of x^2 - 5x + 6 = 0 are a and b. What is a^2 + b^2?", "", "", "", "", "13", "Roots are 2 and 3; 4 + 9 = 13.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q017", "MBA-EX-CAT", "QA", "Algebra", "1", "numeric", "Given log10(2) = 0.301, what is log10(8)?", "", "", "", "", "0.903", "log10(8) = 3 x 0.301.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q018", "MBA-EX-CAT", "QA", "Algebra", "1", "numeric", "What is the 10th term of the progression 3, 7, 11, ...?", "", "", "", "", "39", "3 + 9 x 4 = 39.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q019", "MBA-EX-CAT", "QA", "Algebra", "1", "numeric", "What is 1 + 2 + 4 + ... + 2^9?", "", "", "", "", "1023", "Geometric sum = 2^10 - 1.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q020", "MBA-EX-CAT", "QA", "Algebra", "2", "numeric", "How many integers x satisfy |x - 3| < 5?", "", "", "", "", "9", "-2 < x < 8, so x = -1 to 7: 9 integers.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q021", "MBA-EX-CAT", "QA", "Algebra", "1", "numeric", "What is the sum of the first 20 natural numbers?", "", "", "", "", "210", "20 x 21 / 2 = 210.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q022", "MBA-EX-CAT", "QA", "Geometry and mensuration", "1", "numeric", "What is the area of a right triangle with sides 3, 4 and 5?", "", "", "", "", "6", "Half of 3 x 4.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q023", "MBA-EX-CAT", "QA", "Geometry and mensuration", "1", "numeric", "What is the area of a circle of radius 7, taking pi = 22/7?", "", "", "", "", "154", "22/7 x 49 = 154.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q024", "MBA-EX-CAT", "QA", "Modern maths", "2", "numeric", "In how many distinct ways can the letters of LEVEL be arranged?", "", "", "", "", "30", "5! / (2! x 2!) = 30.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q025", "MBA-EX-CAT", "QA", "Modern maths", "1", "numeric", "In how many ways can 3 people be chosen from 7?", "", "", "", "", "35", "7C3 = 35.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q026", "MBA-EX-CAT", "QA", "Modern maths", "1", "numeric", "Two dice are thrown. Of the 36 equally likely outcomes, how many give a sum of 7?", "", "", "", "", "6", "(1,6),(2,5),(3,4),(4,3),(5,2),(6,1).", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q027", "MBA-EX-CAT", "DILR", "Logical reasoning", "1", "numeric", "In a class of 60, 35 play cricket, 25 play football and 10 play both. How many play neither?", "", "", "", "", "10", "60 - (35 + 25 - 10) = 10.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q028", "MBA-EX-CAT", "DILR", "Data interpretation", "1", "numeric", "Quarterly sales were 120, 150, 135 and 195 units. What is the average quarterly sales?", "", "", "", "", "150", "600 / 4 = 150.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q029", "MBA-EX-CAT", "DILR", "Data interpretation", "1", "mcq", "Quarterly sales were Q1 120, Q2 150, Q3 135, Q4 195. Which quarter had the largest increase over the previous quarter?", "Q2", "Q3", "Q4", "None", "c", "Q2 +30, Q3 -15, Q4 +60.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q030", "MBA-EX-CAT", "DILR", "Logical reasoning", "2", "mcq", "P, Q, R and S sit in seats 1 to 4 in a row. P is in seat 1, R is in seat 4, and Q does not sit next to R. Who sits in seat 3?", "P", "Q", "R", "S", "d", "Q cannot take seat 3 (next to R), so Q is in seat 2 and S in seat 3.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q031", "MBA-EX-CAT", "DILR", "Logical reasoning", "1", "numeric", "What comes next: 2, 6, 12, 20, 30, ?", "", "", "", "", "42", "Terms are n(n+1); 6 x 7 = 42.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q032", "MBA-EX-CAT", "DILR", "Logical reasoning", "1", "mcq", "If CAT is written as DBU, how is DOG written?", "EPH", "CNF", "EOH", "DPH", "a", "Each letter moves forward by one.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q033", "MBA-EX-CAT", "DILR", "Logical reasoning", "2", "mcq", "All A are B. Some B are C. Which conclusion follows?", "Some A are C", "All C are A", "No A is C", "None of these follows", "d", "The C that are B need not be A, so no definite conclusion about A and C follows.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q034", "MBA-EX-CAT", "DILR", "Logical reasoning", "1", "numeric", "What is the angle in degrees between the hands of a clock at 3:00?", "", "", "", "", "90", "Each hour mark is 30 degrees; 3 x 30 = 90.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q035", "MBA-EX-CAT", "VARC", "Verbal ability", "1", "mcq", "Choose the correct word: Neither the manager nor the employees ___ present.", "was", "were", "is", "has been", "b", "With neither...nor, the verb agrees with the nearer subject, 'employees'.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q036", "MBA-EX-CAT", "VARC", "Verbal ability", "1", "mcq", "Choose the word closest in meaning to 'ephemeral'.", "Lasting", "Short-lived", "Heavy", "Bright", "b", "Ephemeral means lasting a very short time.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q037", "MBA-EX-CAT", "VARC", "Verbal ability", "1", "mcq", "Choose the word opposite in meaning to 'verbose'.", "Wordy", "Concise", "Loud", "Vague", "b", "Verbose means using too many words.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q038", "MBA-EX-CAT", "VARC", "Verbal ability", "2", "mcq", "Paragraph: 'Cities that add bus lanes often see car traffic fall within months. Commuters respond to faster buses by switching modes, and the freed road space is used more efficiently.' Which is the best summary?", "Bus lanes cause traffic jams", "Faster buses from dedicated lanes can shift commuters away from cars and use road space better", "Cities should ban cars", "Commuters dislike buses", "b", "It keeps both the effect (fewer cars) and the mechanism (faster buses, efficient road use).", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q039", "MBA-EX-CAT", "VARC", "Verbal ability", "2", "mcq", "Which sentence does NOT belong? (1) Solar panel prices have fallen sharply in a decade. (2) Cheaper panels have made rooftop solar common. (3) Many households now sell surplus power to the grid. (4) The Himalayas contain the world's highest peaks.", "1", "2", "3", "4", "d", "Sentences 1 to 3 form a chain about solar power; 4 is unrelated.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q040", "MBA-EX-CAT", "VARC", "Verbal ability", "3", "mcq", "Arrange into a logical order: (1) As a result, the company cut prices. (2) Sales of the new phone were slow at launch. (3) Within a month, sales doubled. (4) Reviewers said it was overpriced.", "2413", "4213", "2143", "1234", "a", "Slow sales (2), the reason (4), the response (1), the outcome (3).", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q041", "MBA-EX-CAT", "VARC", "Reading comprehension", "2", "mcq", "Argument: 'Sales rose after our ad campaign, so the campaign caused the rise.' Which statement most weakens it?", "The ads were colourful", "A major competitor shut down in the same month", "Sales were measured accurately", "The campaign was expensive", "b", "Another cause in the same period offers an alternative explanation.", "team_written", "TRUE", "Prof. R. Sengupta"),
        ("MBA-Q042", "MBA-EX-CAT", "VARC", "Reading comprehension", "2", "mcq", "'Most students who attended the optional workshops scored above average.' What can be inferred?", "The workshops caused higher scores", "Attendance and higher scores are associated in this group", "All students should attend", "Workshops are mandatory", "b", "Only an association is stated; causation cannot be assumed.", "team_written", "TRUE", "Prof. R. Sengupta")
    ]
    with open(os.path.join(mba_dir, "mba_practice_items.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "exam_id", "section", "topic", "difficulty", "type", "stem", "option_a", "option_b", "option_c", "option_d", "answer", "explanation", "source_type", "reviewed", "reviewed_by"])
        for it in items:
            writer.writerow(it)

    # 13. mba_interview_questions.csv
    with open(os.path.join(mba_dir, "mba_interview_questions.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "category", "question", "what_good_looks_like", "source_type"])
        writer.writerow(["MBA-IQ01", "Introduction", "Tell us about yourself.", "Clear 60 to 90 second story linking background, choices and goals", "team_written"])
        writer.writerow(["MBA-IQ02", "Motivation", "Why do you want an MBA?", "Specific goal; how the programme bridges current skills and the goal", "team_written"])
        writer.writerow(["MBA-IQ03", "Motivation", "Why an MBA now rather than after work experience?", "Honest trade-off; what the student gains by going now", "team_written"])
        writer.writerow(["MBA-IQ04", "Motivation", "Why move from engineering to management?", "Shows how engineering skills carry over; not framed as running away from engineering", "team_written"])
        writer.writerow(["MBA-IQ05", "Academics", "Explain your final-year or major project to someone who is not an engineer.", "Plain language; problem, approach, result, own contribution", "team_written"])
        writer.writerow(["MBA-IQ06", "Academics", "Explain a core concept from your branch in simple terms.", "Correct and simple; handles follow-up questions", "team_written"])
        writer.writerow(["MBA-IQ07", "Self-awareness", "What are your main strengths and one real weakness?", "Evidence for strengths; weakness with a concrete improvement step", "team_written"])
        writer.writerow(["MBA-IQ08", "Experience", "Describe a time you failed and what you learned.", "Owns the failure; specific lesson; later evidence of change", "team_written"])
        writer.writerow(["MBA-IQ09", "Experience", "Give an example of leading a team.", "Situation, action, result; credit shared fairly", "team_written"])
        writer.writerow(["MBA-IQ10", "Goals", "Where do you see yourself five years after the MBA?", "Realistic, specific, consistent with the rest of the story", "team_written"])
        writer.writerow(["MBA-IQ11", "Fit", "Why this school?", "Specific programme features, not rankings alone", "team_written"])
        writer.writerow(["MBA-IQ12", "Awareness", "Which business or economic issue have you followed recently, and what is your view?", "Accurate facts; balanced view; own opinion with reasons", "team_written"])
        writer.writerow(["MBA-IQ13", "Ethics", "You find a teammate fudging data before a deadline. What do you do?", "Integrity first; practical steps; escalation if needed", "team_written"])
        writer.writerow(["MBA-IQ14", "WAT", "Write 200 words: Should Indian companies adopt a four-day work week?", "Clear position, two arguments, one counter-argument, conclusion", "team_written"])
        writer.writerow(["MBA-IQ15", "WAT", "Write 200 words: Is a degree still necessary for a successful career?", "Clear position, two arguments, one counter-argument, conclusion", "team_written"])

    # 14. mba_interview_rubric.csv
    with open(os.path.join(mba_dir, "mba_interview_rubric.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["criterion", "score_1", "score_2", "score_3", "score_4"])
        writer.writerow(["Structure", "No clear order", "Some structure, hard to follow", "Clear beginning, middle and end", "Crisp structure that leads to a clear point"])
        writer.writerow(["Content", "Vague or incorrect", "Partly specific", "Specific and correct", "Specific, correct and insightful"])
        writer.writerow(["Self-awareness", "Generic claims", "Some reflection", "Honest reflection with examples", "Deep reflection with evidence of growth"])
        writer.writerow(["Communication", "Hard to understand", "Understandable with effort", "Clear and confident", "Clear, concise and engaging"])
        writer.writerow(["Handling follow-ups", "Stuck or defensive", "Partial answers", "Answers calmly and directly", "Uses follow-ups to strengthen the answer"])

    # 15. mba_application_checklist_items.csv
    with open(os.path.join(mba_dir, "mba_application_checklist_items.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "item", "applies_to"])
        writer.writerow(["MBA-CL01", "Entrance test scorecard", "All Indian programmes"])
        writer.writerow(["MBA-CL02", "Class 10 and 12 mark sheets", "Most programmes"])
        writer.writerow(["MBA-CL03", "Graduation transcripts or provisional certificate", "All programmes"])
        writer.writerow(["MBA-CL04", "Category or other reservation certificate", "Only if claiming a category"])
        writer.writerow(["MBA-CL05", "Work experience letters", "Only if the student has work experience"])
        writer.writerow(["MBA-CL06", "Government photo ID", "All programmes"])
        writer.writerow(["MBA-CL07", "Recent photographs", "Most applications"])
        writer.writerow(["MBA-CL08", "Application fee payment", "All programmes"])
        writer.writerow(["MBA-CL09", "Essays or statement of purpose", "Only where the programme asks"])
        writer.writerow(["MBA-CL10", "Recommendation letters", "Only where the programme asks"])
        writer.writerow(["MBA-CL11", "GMAT or GRE score report", "Programmes abroad and those accepting these tests"])

    # 16. mba_learning_methods.csv
    with open(os.path.join(mba_dir, "mba_learning_methods.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "name", "when_to_use", "how"])
        writer.writerow(["MBA-L1", "Daily reading", "VARC and GK", "Read long-form articles and editorials for 30 to 45 minutes daily; write a one-line summary of each"])
        writer.writerow(["MBA-L2", "Mock analysis", "After every full mock", "Spend at least as long reviewing as taking the mock; review every wrong and every skipped question"])
        writer.writerow(["MBA-L3", "Error log", "After every test", "Tag each mistake by topic and type (concept, calculation, reading, time); the next week targets the top 3 tags"])
        writer.writerow(["MBA-L4", "Selective attempting", "DILR and QA in mocks", "Scan all sets first; attempt the most doable ones; accuracy before attempts"])
        writer.writerow(["MBA-L5", "Sectional timing practice", "Building and mock phases", "Practise each section in its fixed time to build pacing"])
        writer.writerow(["MBA-L6", "Spaced formula review", "Arithmetic and algebra formulas", "Review on day 1, 3, 7 and 21 after learning"])
        writer.writerow(["MBA-L7", "Mock interviews with feedback", "Personal interview preparation", "Record answers; score against the interview rubric; redo weak answers"])
        writer.writerow(["MBA-L8", "Semester-aware load", "Always", "Lighter preparation in mid-sem and end-sem weeks, heavier in breaks"])

    # 17. mba_resources.csv
    with open(os.path.join(mba_dir, "mba_resources.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "title", "url", "provider", "type", "exam_ids", "free"])
        writer.writerow(["MBA-R01", "CAT official website", "https://iimcat.ac.in", "IIMs", "Official site", "MBA-EX-CAT", "TRUE"])
        writer.writerow(["MBA-R02", "XAT official website", "https://xatonline.in", "XLRI", "Official site", "MBA-EX-XAT", "TRUE"])
        writer.writerow(["MBA-R03", "SNAP official website", "https://www.snaptest.org", "Symbiosis", "Official site", "MBA-EX-SNAP", "TRUE"])
        writer.writerow(["MBA-R04", "GMAT exam structure", "https://www.mba.com/exams/gmat-exam/about/exam-structure", "GMAC", "Official page", "MBA-EX-GMAT", "TRUE"])
        writer.writerow(["MBA-R05", "GMAT Focus score scale", "https://www.mba.com/exams-and-exam-prep/gmat-exam/gmat-focus-evolving-score-scale/amp", "GMAC", "Official page", "MBA-EX-GMAT", "TRUE"])
        writer.writerow(["MBA-R06", "Statistics and Probability", "https://www.khanacademy.org/math/statistics-probability", "Khan Academy", "Video course", "MBA-EX-CAT;MBA-EX-GMAT", "TRUE"])

    # NOW CORE TO MBA TABLES (/data/seed/core_to_mba/)
    # 1. career_paths.csv
    with open(os.path.join(c2m_dir, "career_paths.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "branch", "name", "description", "typical_roles", "skills_valued", "sectors", "source_type", "reviewed", "reviewed_by"])
        writer.writerow(["CP-EE-01", "EE", "Power and Energy Sector Management", "Leading grid operations, renewable energy integration projects, and power distribution asset planning.", "Operations Manager, Energy Transition Project Lead, Grid Asset Strategy Analyst", "Power systems intuition, quantitative modeling, capital project execution", "Utilities, Clean Tech, Renewable Energy", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["CP-EE-02", "EE", "Hardware & Semiconductor Product Management", "Bridging electrical engineering architecture with market requirements for electronics and chipsets.", "Technical Product Manager, Hardware Program Manager, Semiconductor Solution Architect", "Semiconductor lifecycle, embedded systems, cross-functional engineering leadership", "Semiconductors, Electronics, IoT", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["CP-EE-03", "EE", "Energy & Infrastructure Consulting", "Advising corporate and public sector clients on electrification, decarbonization, and smart grid upgrades.", "Management Consultant, Infrastructure Advisory Consultant, Energy Strategy Specialist", "Techno-economic feasibility, electrical grid regulations, financial modeling", "Strategy Consulting, Infrastructure Advisory", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["CP-MM-01", "MM", "Metals & Manufacturing Operations and Supply Chain", "Directing heavy manufacturing plants, blast furnace logistics, raw material flow, and inventory.", "Operations Manager, Plant Logistics Lead, Manufacturing Program Manager", "Process metallurgy, supply chain logistics, Lean Six Sigma", "Steel, Aluminium, Heavy Engineering", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["CP-MM-02", "MM", "Materials Sourcing & Global Procurement", "Managing strategic procurement of critical ores, alloys, high-performance ceramics, and battery minerals.", "Strategic Sourcing Manager, Category Manager - Direct Materials, Supply Risk Specialist", "Extractive metallurgy, vendor audit, global commodity risk analysis", "Automotive, Aerospace, EV Batteries", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["CP-MM-03", "MM", "Manufacturing & Industrial Strategy Consulting", "Advising metal producers and industrial manufacturing conglomerates on decarbonization and efficiency.", "Operations Strategy Consultant, Manufacturing Practice Analyst, Industrial Transformation Lead", "Cost modeling, metallurgical yield optimization, green steel technologies", "Management Consulting, Industrial Advisory", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["CP-ANY-01", "any", "General Management & Corporate Strategy", "Cross-functional executive leadership across diverse industries leveraging engineering rigor.", "Management Trainee, Strategy Analyst, Chief of Staff", "Quantitative rigor, problem structuring, executive communication", "Conglomerates, FMCG, Banking", "team_curated", "TRUE", "Prof. R. Sengupta"])

    # 2. branch_pi_topics.csv
    with open(os.path.join(c2m_dir, "branch_pi_topics.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "branch", "topic", "subtopics", "interview_level_notes", "reviewed", "reviewed_by"])
        writer.writerow(["BPI-TOPIC-EE-01", "EE", "Circuits and Networks", "Ohm's law, KCL/KVL, Thevenin/Norton, AC impedance, power factor", "Interviewers test intuition on power factor correction and real vs reactive power in industrial tariffs.", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-TOPIC-EE-02", "EE", "Electrical Machines & Drives", "Transformers, induction motors, synchronous machines, DC motors", "Candidates should explain why induction motors dominate industry and how variable frequency drives work.", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-TOPIC-EE-03", "EE", "Power Systems & Smart Grids", "Transmission lines, protection relays, renewable intermittency, grid frequency", "Candidates must connect grid frequency dips to supply-demand imbalances and explain blackouts.", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-TOPIC-EE-04", "EE", "Power Electronics & Control", "Inverters, rectifiers, PID controllers, stability margins", "Focus on EV charger topology and feedback loops in industrial robotics.", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-TOPIC-MM-01", "MM", "Physical Metallurgy & Phase Diagrams", "Fe-C diagram, phase transformations, TTT diagrams, microstructures", "Interviewers expect simple explanations of pearlite vs martensite and how heat treatment controls steel grades.", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-TOPIC-MM-02", "MM", "Mechanical Behavior & Failure", "Tensile testing, fatigue, creep, brittle vs ductile fracture", "Candidates should relate fatigue failure to bridge or aircraft crashes and discuss safety factors.", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-TOPIC-MM-03", "MM", "Materials Selection & Manufacturing", "Alloy design, corrosion resistance, composites, additive manufacturing", "Candidates must defend why aluminium or carbon fiber is chosen for aircraft bodies over steel despite cost.", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-TOPIC-MM-04", "MM", "Extractive Metallurgy & Sustainability", "Iron making, blast furnace, green hydrogen steel, recycling", "Focus on carbon emissions in steelmaking and business economics of electric arc furnaces.", "TRUE", "Prof. P. Bhargava"])

    # 3. branch_pi_questions.csv
    with open(os.path.join(c2m_dir, "branch_pi_questions.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "branch", "topic_id", "question", "what_good_looks_like", "source_type", "reviewed", "reviewed_by"])
        writer.writerow(["BPI-Q-EE-01", "EE", "BPI-TOPIC-EE-01", "What is power factor, and why do manufacturing plants get penalized for a low power factor?", "Explains that power factor is the ratio of real power to apparent power; low PF means drawing excess reactive current causing higher line losses without doing useful work, burdening utilities.", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-Q-EE-02", "EE", "BPI-TOPIC-EE-02", "Why are 3-phase induction motors used in almost all manufacturing machinery instead of DC motors?", "Cites absence of brushes/commutators resulting in low maintenance, rugged construction, self-starting capability, and cost-effectiveness when paired with modern inverters.", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-Q-EE-03", "EE", "BPI-TOPIC-EE-03", "How does increasing solar power integration impact national grid stability?", "Mentions duck curve, solar intermittency, loss of physical rotational inertia, and need for fast-ramping gas peakers or battery energy storage systems (BESS).", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-Q-EE-04", "EE", "BPI-TOPIC-EE-04", "Explain the difference between open-loop and closed-loop control to a factory manager.", "Uses a thermostat or cruise control analogy: open-loop runs blind without feedback, while closed-loop senses output and corrects errors dynamically for precision.", "team_curated", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["BPI-Q-MM-01", "MM", "BPI-TOPIC-MM-01", "Why is pure iron almost never used in structural construction, but steel with under 1% carbon is?", "Explains that pure iron is soft and ductile; interstitial carbon atoms distort the crystal lattice, impeding dislocation motion and multiplying tensile yield strength.", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-Q-MM-02", "MM", "BPI-TOPIC-MM-02", "What is metal fatigue, and why is it dangerous for airlines and rail operators?", "Defines fatigue as catastrophic progressive structural damage under cyclic stress below yield strength; dangerous because cracks initiate micro-scale with no visible warning.", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-Q-MM-03", "MM", "BPI-TOPIC-MM-03", "If aluminium is more expensive per kilogram than structural steel, why are automotive bodies moving to aluminium?", "Calculates weight reduction yielding higher fuel/battery efficiency; lifecycle savings and non-corrosive properties outweigh initial raw material acquisition cost.", "team_curated", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["BPI-Q-MM-04", "MM", "BPI-TOPIC-MM-04", "What is green steel, and what is holding back steel companies from adopting hydrogen reduction overnight?", "Explains Direct Reduced Iron (DRI) using green hydrogen instead of coke; hurdles include high electrolyser capex, massive green hydrogen costs, and existing blast furnace capital lock-in.", "team_curated", "TRUE", "Prof. P. Bhargava"])

    # 4. profile_audit_rubric.csv
    with open(os.path.join(c2m_dir, "profile_audit_rubric.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["criterion", "level_1", "level_2", "level_3", "level_4"])
        writer.writerow(["Academics", "CGPA below 6.5 or multiple backlogs", "CGPA 6.5 to 7.5, no active backlogs", "CGPA 7.5 to 8.5 with consistent academic trajectory", "CGPA 8.5+ or departmental rank holder"])
        writer.writerow(["Projects", "Classroom lab assignments only without independent exploration", "One academic term project with working prototype/simulation", "Interdisciplinary or sponsored engineering project with clear measurable deliverables", "Flagship tech competition project, patent, or published research with business relevance"])
        writer.writerow(["Internships", "No off-campus industrial exposure or summer internship", "Informal training or observation-only industrial visit", "Structured 8-week corporate or core engineering internship with project output", "Competitive corporate internship with tangible operational savings or client-facing impact"])
        writer.writerow(["Leadership", "General member of student clubs with no organizational responsibility", "Sub-coordinator or event volunteer managing operational logistics", "Club head, tech team lead, or elected student representative leading 10+ peers", "Founded an initiative, college fest convener, or national-level leadership with budget ownership"])
        writer.writerow(["Extracurriculars", "Minimal participation in sports, cultural, or community activities", "Occasional participation in institute-level cultural or sports events", "Consistent participation with inter-college podium finishes or recognized NGO work", "State/national level sports/arts, or impactful community initiative with measurable social impact"])
        writer.writerow(["Work-ex Plan", "No concept of post-grad industry options or pre-MBA employment", "Vague interest in corporate roles without domain clarity", "Well-articulated target industry (e.g. 2 yrs in operations before MBA) with backup plans", "Clear 2-3 year strategic pre-MBA career plan in core operations/tech consulting with verified sponsor"])

    # 5. profile_actions.csv
    with open(os.path.join(c2m_dir, "profile_actions.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "branch", "action", "criterion_improved", "effort_hours", "timing", "course_code", "reviewed", "reviewed_by"])
        writer.writerow(["ACT-01", "any", "Lead a technical team submodule or society project budget", "Leadership", "4", "Semester 5-6", "", "TRUE", "Prof. R. Sengupta"])
        writer.writerow(["ACT-02", "any", "Complete a core internship framed with quantified business and cost outcomes", "Internships", "8", "Summer Break", "", "TRUE", "Prof. R. Sengupta"])
        writer.writerow(["ACT-03", "any", "Participate in national collegiate business case competition or product hackathon", "Projects", "6", "Semester 6-7", "", "TRUE", "Prof. R. Sengupta"])
        writer.writerow(["ACT-04", "any", "Enrol in institute open elective in Engineering Economics or Cost Management", "Academics", "3", "Semester 5-7", "HS3L001", "TRUE", "Prof. R. Sengupta"])
        writer.writerow(["ACT-05", "EE", "Build an automated energy monitoring or tariff optimization capstone project", "Projects", "6", "Semester 6-8", "", "TRUE", "Prof. S. R. Samantaray"])
        writer.writerow(["ACT-06", "MM", "Conduct a manufacturing scrap reduction or quality audit case study", "Projects", "6", "Semester 6-8", "", "TRUE", "Prof. P. Bhargava"])
        writer.writerow(["ACT-07", "any", "Volunteer as student coordinator for institute placement or corporate relations cell", "Leadership", "5", "Semester 5-7", "", "TRUE", "Prof. R. Sengupta"])

    # 6. story_drafts.csv (template seed)
    with open(os.path.join(c2m_dir, "story_drafts.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "kind", "version", "text", "rubric_scores_json", "feedback", "created_at"])
        writer.writerow(["SAMPLE-STU-01", "why_mba", "1", "SAMPLE-I want an MBA to switch from lab circuits to managing tech supply chains.", "{\"Structure\": 3, \"Content\": 3, \"Self-awareness\": 3, \"Communication\": 3, \"Handling follow-ups\": 3}", "Good start. Add specific operational metrics and long-term sector vision.", "2026-11-15 10:00:00"])

    # 7. decision_options.csv (template seed)
    with open(os.path.join(c2m_dir, "decision_options.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["student_id", "option", "timeline_json", "tradeoffs_text", "chosen", "decided_at"])
        writer.writerow(["SAMPLE-STU-01", "mba_now", "{\"exam\": \"CAT 2026\", \"prep_start\": \"May 2026\", \"intake\": \"July 2027\"}", "Faster transition to management; lacks corporate work experience points for top IIMs.", "TRUE", "2026-11-15 10:00:00"])

    print("All MBA and Core to MBA seed files successfully generated.")

if __name__ == "__main__":
    generate_all_seeds()
