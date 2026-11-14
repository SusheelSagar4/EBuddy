# Higher Studies Database: Clueless (IIT Bhubaneswar)

Higher Studies Database: Clueless (IIT Bhubaneswar)

Seed data for the AI learning buddy's higher-studies guidance: M.Tech, MS (Research), PhD (India and abroad), MS abroad, MBA. Exported from the doc 'Higher Studies Survey and Database', as of 2026-11-14.

How to use this workbook

Each sheet named in lower_case is one database table. Export each sheet to CSV into /data/seed/higher_studies/<sheet>.csv; the app loads them at startup and the reset command restores them.

Survey and Schema sheets describe the questionnaire and every table's fields.

Colour legend

Yellow cell = not yet confirmed from an official page; check the official brochure, then set verified = TRUE and clear the '(verify)' note.

Green row = EXAMPLE row showing the expected format. Replace or delete it once real rows are added.

White cell = taken from the source linked in that row (opened 2026-11-14).

Rules for every fact row

Every row that states a date, fee, cut-off or pattern must have source_url, retrieved_on, cycle and verified. Aggregator sites (Careers360, Cracku, TalkDrill) are leads only; verified = TRUE needs an official page or brochure.

The AI never states a date, cut-off or fee that is not in a verified row; if none exists it says 'not confirmed yet' and links the official site.

Checks

template_check sheet: every template's phase shares must total 100%.
