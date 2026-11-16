# Verification of all 75 student profiles

**Run:** 2026-11-16 09:14:44 UTC - offline, deterministic engine, no LLM, no database  
**Result:** 75 / 75 profiles pass every applicable check; 0 failed check(s).  
**Scope:** 75 multi-semester plans, 326 planned semesters, 2024 course placements (112 distinct course codes, all present in `kb.course`), 283 resource references.

## Checks

| Check | What is verified | Pass | Fail | Not applicable |
|---|---|---|---|---|
| C01 | validator passed | 75 | 0 | 0 |
| C02 | course codes exist | 75 | 0 | 0 |
| C03 | resource ids exist | 75 | 0 | 0 |
| C04 | prerequisites | 75 | 0 | 0 |
| C05 | no duplicates | 75 | 0 | 0 |
| C06 | multi-semester | 75 | 0 | 0 |
| C07 | credit cap | 6 | 0 | 69 |
| C08 | weekly hours cap | 75 | 0 | 0 |
| C09 | baseline warning labelled | 9 | 0 | 66 |
| C10 | deterministic | 75 | 0 | 0 |
| C11 | backlog first | 8 | 0 | 67 |
| C12 | CGPA cutoffs | 11 | 0 | 64 |
| C13 | interest vs evidence | 8 | 0 | 67 |
| C14 | goal switch | 9 | 0 | 66 |
| C15 | tight caps explained | 14 | 0 | 61 |
| C16 | goal skills covered | 75 | 0 | 0 |

`Not applicable` means the profile does not have that constraint or edge case (for example C07 applies only to students who stated a credit cap).

## Per profile

| Student | Prog | Sem | CGPA | Goal | Edge cases | Credits per planned semester | C01 | C02 | C03 | C04 | C05 | C06 | C07 | C08 | C09 | C10 | C11 | C12 | C13 | C14 | C15 | C16 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `CONF_STU_EE_POWER_01` | EE | 5 | 8.20 | EE_CORE_POWER | - | S5:27.0 S6:24.0 S7:21.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | - | - | - | - | ok |
| `CONF_STU_EE_POWER_02` | EE | 4 | 7.50 | EE_CORE_POWER | - | S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_EE_POWER_03` | EE | 3 | 8.80 | EE_CORE_POWER | - | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_EE_EDGE_BACKLOG` | EE | 5 | 6.80 | EE_CORE_POWER | ACTIVE_BACKLOG | S5:28.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | ok | - | - | - | - | ok |
| `CONF_STU_EE_EDGE_CGPA_CUTOFF` | EE | 5 | 7.95 | EE_CORE_POWER | CGPA_ON_MINOR_CUTOFF | S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | - | - | - | ok |
| `CONF_STU_EE_EDGE_GOAL_PIVOT` | EE | 4 | 8.40 | EE_CORE_POWER | MID_DEGREE_GOAL_SWITCH | S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `CONF_STU_EE_EDGE_CONFLICT` | EE | 3 | 7.60 | EE_CORE_POWER | INTEREST_EVIDENCE_CLASH | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `CONF_STU_MME_PROCESS_01` | MM | 5 | 8.25 | MM_PROCESS_ENGINEER | - | S5:22.0 S6:17.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_MME_PROCESS_02` | MM | 4 | 7.80 | MM_PROCESS_ENGINEER | - | S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_MME_PROCESS_03` | MM | 3 | 8.60 | MM_ADVANCED_MATERIALS | - | S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_UPSC_01` | EE | 3 | 8.20 | UPSC_CSE | - | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_UPSC_02` | MM | 6 | 7.40 | UPSC_CSE | - | S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_UPSC_03` | EE | 8 | 7.90 | UPSC_CSE | - | S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_STARTUP_01` | EE | 3 | 8.20 | STARTUP_FOUNDER | - | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_STARTUP_02` | MM | 6 | 7.40 | STARTUP_FOUNDER | - | S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `CONF_STU_STARTUP_03` | EE | 8 | 7.90 | STARTUP_FOUNDER | - | S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S1_001` | EE | 1 | 8.60 | EE_CORE_POWER | - | S1:23.0 S2:24.0 S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S2_002` | EE | 2 | 7.20 | EE_CORE_POWER | TIGHT_WEEKLY_HOURS | S2:24.0 S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_EE_S6_003` | EE | 6 | 8.00 | EE_CORE_VLSI | CGPA_ON_MINOR_CUTOFF | S6:27.0 S7:21.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | ok | - | - | - | ok |
| `SYN_EE_S7_004` | EE | 7 | 6.40 | EE_CORE_POWER | ACTIVE_BACKLOG | S7:22.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | ok | - | - | - | - | ok |
| `SYN_EE_S8_005` | EE | 8 | 9.10 | EE_CORE_VLSI | - | S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S1_006` | MM | 1 | 7.90 | MM_ADVANCED_MATERIALS | - | S1:24.0 S2:23.0 S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S2_007` | MM | 2 | 8.40 | MM_PROCESS_ENGINEER | - | S2:24.0 S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S6_008` | MM | 6 | 7.99 | MM_ADVANCED_MATERIALS | CGPA_ON_MINOR_CUTOFF | S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | - | - | - | ok |
| `SYN_MM_S7_009` | MM | 7 | 6.10 | MM_PROCESS_ENGINEER | ACTIVE_BACKLOG, TIGHT_CREDIT_CAP | S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | ok | - | - | - | ok | ok |
| `SYN_MM_S8_010` | MM | 8 | 8.70 | MM_ADVANCED_MATERIALS | - | S8:15.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S5_011` | MM | 5 | 7.00 | MM_ADVANCED_MATERIALS | INTEREST_EVIDENCE_CLASH | S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_EE_S1_012` | EE | 1 | 8.90 | TRACK_SDE | - | S1:24.0 S2:23.0 S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S3_013` | EE | 3 | 8.30 | TRACK_SDE | INTEREST_EVIDENCE_CLASH | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_EE_S4_014` | EE | 4 | 7.60 | TRACK_SDE | MID_DEGREE_GOAL_SWITCH | S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `SYN_EE_S5_015` | EE | 5 | 8.00 | TRACK_SDE | CGPA_ON_MINOR_CUTOFF | S5:27.0 S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | ok | - | - | - | ok |
| `SYN_EE_S6_016` | EE | 6 | 6.90 | TRACK_SDE | ACTIVE_BACKLOG | S6:27.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | ok | - | - | - | - | ok |
| `SYN_EE_S7_017` | EE | 7 | 8.50 | TRACK_SDE | CGPA_ON_OVERLOAD_CUTOFF, TIGHT_WEEKLY_HOURS | S7:21.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | - | - | ok | ok |
| `SYN_MM_S2_018` | MM | 2 | 7.40 | TRACK_SDE | - | S2:23.0 S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S4_019` | MM | 4 | 8.10 | TRACK_SDE | MID_DEGREE_GOAL_SWITCH | S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `SYN_MM_S5_020` | MM | 5 | 7.70 | TRACK_SDE | TIGHT_WEEKLY_HOURS | S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S8_021` | MM | 8 | 8.20 | TRACK_SDE | TIGHT_CREDIT_CAP | S8:15.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_EE_S2_022` | EE | 2 | 7.80 | TRACK_DA | TIGHT_CREDIT_CAP | S2:24.0 S3:22.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_EE_S3_023` | EE | 3 | 6.70 | TRACK_DA | INTEREST_EVIDENCE_CLASH | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_EE_S5_024` | EE | 5 | 8.01 | TRACK_DA | CGPA_ON_MINOR_CUTOFF | S5:27.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | ok | - | - | - | ok |
| `SYN_EE_S6_025` | EE | 6 | 7.30 | TRACK_DA | MID_DEGREE_GOAL_SWITCH | S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `SYN_MM_S3_026` | MM | 3 | 8.50 | TRACK_DA | CGPA_ON_OVERLOAD_CUTOFF | S3:18.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | - | - | - | ok |
| `SYN_MM_S4_027` | MM | 4 | 7.10 | TRACK_DA | TIGHT_WEEKLY_HOURS | S4:21.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S6_028` | MM | 6 | 6.50 | TRACK_DA | ACTIVE_BACKLOG | S6:18.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | ok | - | - | - | - | ok |
| `SYN_MM_S7_029` | MM | 7 | 8.30 | TRACK_DA | MID_DEGREE_GOAL_SWITCH | S7:19.0 S8:15.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `SYN_EE_S1_030` | EE | 1 | 9.30 | TRACK_AIML | - | S1:24.0 S2:23.0 S3:25.0 S4:25.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S4_031` | EE | 4 | 8.80 | TRACK_AIML | - | S4:24.0 S5:25.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S5_032` | EE | 5 | 7.99 | TRACK_AIML | CGPA_ON_MINOR_CUTOFF, INTEREST_EVIDENCE_CLASH | S5:24.0 S6:25.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | ok | - | - | ok |
| `SYN_EE_S7_033` | EE | 7 | 7.50 | TRACK_AIML | MID_DEGREE_GOAL_SWITCH, TIGHT_WEEKLY_HOURS | S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | ok | ok |
| `SYN_MM_S2_034` | MM | 2 | 8.00 | TRACK_AIML | - | S2:24.0 S3:17.0 S4:20.0 S5:20.0 S6:15.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S3_035` | MM | 3 | 7.20 | TRACK_AIML | INTEREST_EVIDENCE_CLASH | S3:17.0 S4:20.0 S5:20.0 S6:15.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_MM_S5_036` | MM | 5 | 8.60 | TRACK_AIML | TIGHT_CREDIT_CAP | S5:16.0 S6:17.0 S7:16.0 S8:15.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S8_037` | MM | 8 | 6.80 | TRACK_AIML | ACTIVE_BACKLOG | S8:15.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | ok | - | - | - | - | ok |
| `SYN_EE_S3_038` | EE | 3 | 9.00 | EE_RES_HIGHER_STUDIES | - | S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S5_039` | EE | 5 | 8.49 | EE_RES_HIGHER_STUDIES | CGPA_ON_OVERLOAD_CUTOFF | S5:27.0 S6:24.0 S7:21.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | ok | - | - | - | ok |
| `SYN_EE_S6_040` | EE | 6 | 7.70 | EE_RES_HIGHER_STUDIES | INTEREST_EVIDENCE_CLASH | S6:24.0 S7:18.0 S8:21.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_EE_S7_041` | EE | 7 | 8.40 | EE_RES_HIGHER_STUDIES | TIGHT_WEEKLY_HOURS | S7:21.0 S8:23.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S4_042` | MM | 4 | 8.90 | MM_RES_HIGHER_STUDIES | - | S4:20.0 S5:20.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S5_043` | MM | 5 | 8.00 | MM_RES_HIGHER_STUDIES | CGPA_ON_MINOR_CUTOFF | S5:22.0 S6:18.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | ok | - | - | - | ok |
| `SYN_MM_S6_044` | MM | 6 | 7.40 | MM_RES_HIGHER_STUDIES | MID_DEGREE_GOAL_SWITCH | S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | ok | - | ok |
| `SYN_MM_S8_045` | MM | 8 | 8.10 | MM_RES_HIGHER_STUDIES | - | S8:15.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S4_046` | EE | 4 | 7.90 | MBA_CAT | - | S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S5_047` | EE | 5 | 8.20 | MBA_CAT | MID_DEGREE_GOAL_SWITCH | S5:27.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | - | - | ok | - | ok |
| `SYN_EE_S7_048` | EE | 7 | 7.00 | MBA_CAT | TIGHT_WEEKLY_HOURS | S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_EE_S8_049` | EE | 8 | 8.60 | MBA_CAT | - | S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S3_050` | MM | 3 | 7.60 | MBA_CAT | INTEREST_EVIDENCE_CLASH | S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | ok | - | - | ok |
| `SYN_MM_S6_051` | MM | 6 | 6.60 | MBA_CAT | ACTIVE_BACKLOG | S6:17.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | ok | - | - | - | - | ok |
| `SYN_MM_S7_052` | MM | 7 | 8.40 | MBA_CAT | TIGHT_CREDIT_CAP | S7:16.0 S8:15.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_EE_S1_053` | EE | 1 | 8.10 | UPSC_CSE | - | S1:23.0 S2:24.0 S3:25.0 S4:24.0 S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_EE_S5_054` | EE | 5 | 7.20 | UPSC_CSE | TIGHT_WEEKLY_HOURS | S5:24.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S2_055` | MM | 2 | 7.00 | UPSC_CSE | - | S2:24.0 S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
| `SYN_MM_S4_056` | MM | 4 | 6.30 | UPSC_CSE | ACTIVE_BACKLOG | S4:23.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | ok | - | - | - | - | ok |
| `SYN_EE_S5_057` | EE | 5 | 8.50 | STARTUP_FOUNDER | CGPA_ON_OVERLOAD_CUTOFF, MID_DEGREE_GOAL_SWITCH | S5:27.0 S6:24.0 S7:18.0 S8:20.0 | ok | ok | ok | ok | ok | ok | - | ok | ok | ok | - | ok | - | ok | - | ok |
| `SYN_MM_S3_058` | MM | 3 | 7.80 | STARTUP_FOUNDER | TIGHT_CREDIT_CAP | S3:17.0 S4:17.0 S5:16.0 S6:17.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | ok | ok | - | ok | - | - | - | - | ok | ok |
| `SYN_MM_S1_059` | MM | 1 | 8.30 | STARTUP_FOUNDER | - | S1:23.0 S2:24.0 S3:17.0 S4:20.0 S5:19.0 S6:14.0 S7:16.0 S8:12.0 | ok | ok | ok | ok | ok | ok | - | ok | - | ok | - | - | - | - | - | ok |
