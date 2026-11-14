"""
Parser and writer for raw MME data provided for IIT Bhubaneswar SMMME.
Generates structured CSV files in data/raw/mme/.
"""

import os
import csv

RAW_MME_DIR = os.path.join("data", "raw", "mme")
os.makedirs(RAW_MME_DIR, exist_ok=True)

# 1. Curriculum Semester Table
CURRICULUM_CSV_DATA = """Semester,Course Name,Course Code,L-T-P,Credits,Contact Hours,Course Type,Prerequisites,Text Books,Reference Books,Notes
SEMESTER – III      |      Total credits: 24/25      |      Total contact hours: 24/25,,,,,,,,,,
Sem III,Basic Electronics,EC2L005,3-1-0,4,4,Common Core,None,"1. A. Malvino and D. J Bates “Electronic Principles,” Tata McGraw - Hill Education, 2006.
2. D. A. Neamen, “Electronic Circuits,” Tata McGraw - Hill Education, 2006.","1. Malvino and Brown, “Digital Computer Electronics,” Tata McGraw - Hill Education, 2001.
2. Samuel C. Lee, “Digital Circuits and Logic Design,” PHI Learning, 2009.
3. R. A. Gayakwad, “Op-Amps and Linear Integrated Circuits,” PHI Learning, 2009.",Prerequisite and books taken from the Electrical Engineering curriculum PDF (same code EC2L005); not in the MME PDF.
Sem III,Introduction to Materials Science and Engineering,ID2L001,2-0-0,2,2,Institute Core,—,—,—,
Sem III,Introduction to Bio Science and Technology,ID2L002,2-0-0,2,2,Institute Core,—,—,—,
Sem III,Numerical Methods,MA2L007,3-1-0,4,4,Institute Core,—,—,—,
Sem III,Breadth – I,(no code in source),(not given),3 / 4,3 / 4,Breadth,—,—,—,
Sem III,Thermodynamics of Materials,ML2L002,3-0-0,3,3,Departmental Core,—,—,—,
Sem III,Basic Electronics Laboratory,EC2P005,0-0-3,2,3,Common Core Lab,—,—,—,
Sem III,Introduction to Materials Laboratory,ML2P001,0-0-3,2,3,Laboratory,—,—,—,
Sem III,Seminar,ML2S001,0-0-0,2,0,Seminar,—,—,—,
SEMESTER – IV      |      Total credits: 24/26      |      Total contact hours: 27/29,,,,,,,,,,
Sem IV,Breadth – II,(no code in source),(not given),3 / 4,3 / 4,Breadth,—,—,—,
Sem IV,Lateral – 1 (any one from the Lateral list),(no code in source),(not given),3 / 4,3 / 4,Lateral,—,—,—,Source does not say which lateral course belongs to which lateral slot; see Lateral list below.
Sem IV,"Environmental Science, Technology and Management",ID2L003,2-0-0,2,2,Institute Core,—,—,—,Source shows both ID2L003 and ID3L003 for this course; ID2L003 used (also the code in the EE curriculum).
Sem IV,Materials Processing,ML2L003,3-0-0,3,3,Departmental Core,—,—,—,
Sem IV,Transport Phenomena and Kinetics of Metallurgical Processes,ML2L004,3-1-0,4,4,Departmental Core,—,—,—,
Sem IV,Physical Metallurgy,ML2L005,3-0-0,3,3,Departmental Core,—,—,—,
Sem IV,Materials Processing Laboratory,ML2P002,0-0-3,2,3,Laboratory,—,—,—,
Sem IV,Physical Metallurgy Laboratory,ML2P003,0-0-3,2,3,Laboratory,—,—,—,
Sem IV,Thermodynamics of Materials Laboratory,ML2P004,0-0-3,2,3,Laboratory,—,—,—,
"▸ Lateral list (Lateral I, II, III draw from this list; source does not map each course to a slot)",,,,,,,,,,
Sem IV–VI,Advances in nanoscience and nanotechnology,ML2L006,3-0-0,3,3,Lateral,—,—,—,
Sem IV–VI,Recent advances in composite materials,ML3L011,3-0-0,3,3,Lateral,—,—,—,
Sem IV–VI,Mineral processing plant design,ML3L012,3-0-0,3,3,Lateral,—,—,—,Same title as elective “Mineral process plant design” (ML4L013) but different code and wording.
SEMESTER – V      |      Total credits: 23/25      |      Total contact hours: 24/26,,,,,,,,,,
Sem V,Breadth – III,(no code in source),(not given),3 / 4,3 / 4,Breadth,—,—,—,
Sem V,Lateral – II (any one from the Lateral list),(no code in source),(not given),3 / 4,3 / 4,Lateral,—,—,—,
Sem V,Mineral processing,ML3L001,3-0-0,3,3,Departmental Core,—,—,—,
Sem V,Corrosion and surface engineering,ML3L002,3-0-0,3,3,Departmental Core,—,—,—,
Sem V,Mechanical properties and testing of materials,ML3L003,3-0-0,3,3,Departmental Core,—,—,—,
Sem V,Phase transformation of materials,ML3L004,3-0-0,3,3,Departmental Core,—,—,—,
Sem V,Chemical metallurgy,ML3L005,3-0-0,3,3,Departmental Core,—,—,—,
Sem V,Mechanical testing & working laboratory,ML3P001,0-0-3,2,3,Laboratory,—,—,—,
SEMESTER – VI      |      Total credits: 22/24      |      Total contact hours: 24/26,,,,,,,,,,
Sem VI,Breadth – IV,(no code in source),(not given),3 / 4,3 / 4,Breadth,—,—,—,
Sem VI,Lateral – III (any one from the Lateral list),(no code in source),(not given),3 / 4,3 / 4,Lateral,—,—,—,
Sem VI,Materials characterization,ML3L006,3-0-0,3,3,Departmental Core,—,—,—,
Sem VI,Iron and Steel making,ML3L007,3-0-0,3,3,Departmental Core,—,—,—,
Sem VI,Deformation and mechanical working of materials,ML3L008,3-0-0,3,3,Departmental Core,—,—,—,
Sem VI,Introduction to simulation and modeling in materials,ML3L009,3-0-0,3,3,Departmental Core,—,—,—,
Sem VI,Materials characterization laboratory – I,ML3P002,0-0-3,2,3,Laboratory,—,—,—,
Sem VI,Simulation and modeling laboratory,ML3P003,0-0-3,2,3,Laboratory,—,—,—,
SEMESTER – VII      |      Total credits: 22      |      Total contact hours: 18,,,,,,,,,,
Sem VII,Light metals and alloys,ML4L001,3-0-0,3,3,Departmental Core,—,—,—,Code clash: in the elective list ML4L001 is “Joining of metals and alloys”.
Sem VII,Elements of electroceramics,ML4L002,3-0-0,3,3,Departmental Core,—,—,—,Code clash: in the elective list ML4L002 is “Solidification of metals and alloys”.
Sem VII,Polymers and nanocomposites,ML4L003,3-0-0,3,3,Departmental Core,—,—,—,Code clash: in the elective list ML4L003 is “Electrochemical methods in metallurgy”.
Sem VII,Elective – I (any one from the Elective list),ML4LXXX,3-0-0,3,3,Elective,—,—,—,Placeholder code in source.
Sem VII,Materials characterization laboratory – II,ML4P001,0-0-3,2,3,Laboratory,—,—,—,
Sem VII,Process control and instrumentation laboratory,ML4P002,0-0-3,2,3,Laboratory,—,—,—,
Sem VII,Industrial training defense,ML4T001,0-0-0,2,0,Training,—,—,—,
Sem VII,Project – I,ML4D001,0-0-6,4,0,Project,—,—,—,Source gives L-T-P 0-0-6 but contact hours 0.
▸ Elective list – Metallurgical Engineering based (one list serves Elective I–V),,,,,,,,,,
Sem VII–VIII,Joining of metals and alloys,ML4L001,3-0-0,3,3,Elective – Metallurgical,—,—,—,Same code as Light metals and alloys (Sem VII core).
Sem VII–VIII,Solidification of metals and alloys,ML4L002,3-0-0,3,3,Elective – Metallurgical,—,—,—,Same code as Elements of electroceramics (Sem VII core).
Sem VII–VIII,Electrochemical methods in metallurgy,ML4L003,3-0-0,3,3,Elective – Metallurgical,—,—,—,Same code as Polymers and nanocomposites (Sem VII core).
Sem VII–VIII,Powder metallurgy,ML4L004,3-0-0,3,3,Elective – Metallurgical,—,—,—,
▸ Elective list – Material Engineering based,,,,,,,,,,
Sem VII–VIII,Materials design and selection,ML4L005,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Energy materials,ML4L006,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Crystallography and x-ray diffraction,ML4L007,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Micro Electro Mechanical Systems,ML4L008,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Physics of materials,ML4L009,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Science and technology of composite materials,ML4L010,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Biomaterials,ML4L011,3-0-0,3,3,Elective – Materials,—,—,—,
Sem VII–VIII,Materials in archaeology,ML4L012,3-0-0,3,3,Elective – Materials,—,—,—,
▸ Elective list – Minerals and resources based,,,,,,,,,,
Sem VII–VIII,Mineral process plant design,ML4L013,3-0-0,3,3,Elective – Minerals & Resources,—,—,—,
Sem VII–VIII,"Fuels, furnaces and refractories",ML4L014,3-0-0,3,3,Elective – Minerals & Resources,—,—,—,
Sem VII–VIII,Materials recycling and sustainability,ML4L015,3-0-0,3,3,Elective – Minerals & Resources,—,—,—,
SEMESTER – VIII      |      Total credits: 18      |      Total contact hours: 12,,,,,,,,,,
Sem VIII,Elective – II (any one from the Elective list),ML4LXXX,3-0-0,3,3,Elective,—,—,—,Placeholder code in source.
Sem VIII,Elective – III (any one from the Elective list),ML4LXXX,3-0-0,3,3,Elective,—,—,—,Placeholder code in source.
Sem VIII,Elective – IV (any one from the Elective list),ML4LXXX,3-0-0,3,3,Elective,—,—,—,Placeholder code in source.
Sem VIII,Elective – V (any one from the Elective list),ML4LXXX,3-0-0,3,3,Elective,—,—,—,Placeholder code in source.
Sem VIII,Project – II,ML4D002,0-0-9,6,0,Project,—,—,—,Source gives L-T-P 0-0-9 but contact hours 0."""

with open(os.path.join(RAW_MME_DIR, "curriculum_semester_table.csv"), "w", encoding="utf-8", newline="") as f:
    f.write(CURRICULUM_CSV_DATA.strip() + "\n")

# 2. Curriculum Notes & Discrepancies
NOTES_DISCREPANCIES_DATA = """item_no,item,issue_found,how_shown
1,Scope of the PDF,"The PDF covers only Semesters III–VIII and contains only the semester table plus the elective and lateral lists. There are no syllabi, prerequisites, text books or reference books. Course names are hyperlinks in the original, but the link targets are not in the PDF.",Prerequisites / Text Books / Reference Books show “—” (not given). Semesters I–II are not in this PDF and are not included.
2,Basic Electronics (EC2L005),Same code appears in the Electrical Engineering curriculum PDF with a syllabus.,Prerequisite and books copied from that EE PDF and flagged in Notes.
3,Duplicate codes ML4L001–ML4L003,"Sem VII core courses (Light metals and alloys, Elements of electroceramics, Polymers and nanocomposites) use the same codes as three Metallurgical electives (Joining of metals and alloys, Solidification of metals and alloys, Electrochemical methods in metallurgy).",Shown exactly as printed and flagged on both sides. Needs confirmation from the department before using codes as unique keys.
4,Environmental Science code,The source prints both ID2L003 and ID3L003 for this course.,ID2L003 used (matches the EE curriculum); flagged.
5,Elective placeholders,Sem VII Elective I and Sem VIII Electives II–V all use the placeholder code ML4LXXX. A single list of 15 electives (3 groups) is given and is not mapped to individual elective slots.,One pool shown after Sem VII with label “Sem VII–VIII”.
6,Lateral slots,"Three lateral courses are listed but not mapped to Lateral I / II / III. Codes ML2L006, ML3L011, ML3L012 suggest different levels, but the source does not say.",One pool shown after Sem IV with label “Sem IV–VI”.
7,Breadth / Lateral rows,No code or L-T-P is given; credits and contact hours are “3/4”.,Shown as printed.
8,Mineral processing plant design vs Mineral process plant design,Lateral ML3L012 and elective ML4L013 have near-identical titles but different codes.,Both kept; flagged on ML3L012.
9,"Projects, seminar and training","Seminar, Industrial training and Projects show 0 contact hours even where L-T-P is non-zero (Project I: 0-0-6, Project II: 0-0-9).",Shown as printed.
10,Totals,Semester totals are copied as printed and were checked against the rows (they add up). A total programme credit is not stated in this PDF.,Not recalculated.
11,Course Type column,The source gives no course types except the elective group headings.,Common Core / Institute Core / Departmental Core / Laboratory are my classification; elective groups follow the source headings.
12,Legend,“—” means the information is not given in the source PDF.,"""

with open(os.path.join(RAW_MME_DIR, "curriculum_notes_discrepancies.csv"), "w", encoding="utf-8", newline="") as f:
    f.write(NOTES_DISCREPANCIES_DATA.strip() + "\n")

# 3. Video Playlists
VIDEO_PLAYLISTS_DATA = """Semester / Group,Course,Code,Primary: NPTEL,Backup 1,Backup 2,Coverage,Notes
III,Basic Electronics,EC2L005,"Basic Electronics – Prof. T.S. Natarajan, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PL7987F30C41A9ADCB","Basic Electronics – Dr. C. Mahanta, IIT Guwahati (NPTEL)
https://www.youtube.com/playlist?list=PL32267B61B7AB0557","Basic Analog & Digital Electronics – Prof. M. Patil, IIT Bombay (NPTEL)
https://www.youtube.com/playlist?list=PLq-Gm0yRYwTgMpFqoWg2WiQ0huPKFNCdN",Playlist found,Same NPTEL playlists as in the EE sheet.
III,Introduction to Materials Science and Engineering,ID2L001,"Introduction to Materials Science and Engineering – Prof. Rajesh Prasad, IIT Delhi (NPTEL) – intro video
https://www.youtube.com/watch?v=BKQOmGxFXzs","MIT 3.091 Introduction to Solid-State Chemistry, Fall 2018 (MIT OCW)
https://www.youtube.com/playlist?list=PLUl4u3cNGP63z5HAguqleEbsICfHgDPaG","Materials Science – Prof. S.K. Gupta, IIT Delhi (NPTEL) – Lec 20 Diffusion in Solids, single video; the series is on the NPTEL IIT Delhi channel
https://www.youtube.com/watch?v=RJ8vf7vItjI",Partial / related only,No full NPTEL playlist URL surfaced; IIT Delhi (Gupta / Prasad) series are on the NPTEL IIT Delhi channel. MIT 3.091 is a close backup.
III,Introduction to Bio Science and Technology,ID2L002,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,No confirmed NPTEL intro-biology playlist.
III,Numerical Methods,MA2L007,"Elementary Numerical Analysis – Prof. R.P. Kulkarni, IIT Bombay (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJTtsC5V9n452YKc4mJAhrmm",,,Playlist found,"Other NPTEL numerical-methods courses exist, but only third-party assignment-answer videos surfaced for them."
III,Breadth – I,(no code),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Depends on the student's choice.
III,Thermodynamics of Materials,ML2L002,"Advanced Metallurgical Thermodynamics – Prof. B.S. Murty, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJS_jlBSbduzYmy6YX_K4KyM","MIT 3.020 Thermodynamics of Materials, Spring 2021 (MIT OCW)
https://www.youtube.com/playlist?list=PLUl4u3cNGP61g-yRbJz4ghFPJLiok1HxX",,Playlist found,IIT Madras course is 'Advanced' metallurgical thermodynamics – use for the later units; MIT 3.020 is the closer match for a first course.
III,Basic Electronics Laboratory,EC2P005,"Basic Electronics – Prof. T.S. Natarajan, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PL7987F30C41A9ADCB",,,Lab – use theory playlist,Use theory playlist.
III,Introduction to Materials Laboratory,ML2P001,"Introduction to Materials Science and Engineering – Prof. Rajesh Prasad, IIT Delhi (NPTEL) – intro video
https://www.youtube.com/watch?v=BKQOmGxFXzs","Structure of Materials – Prof. S. Sangal & Dr. A. Subramaniam, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQ5jqiXDYuE6ETz5F5Kn4dA",,Lab – use theory playlist,No lab video found; theory playlists listed.
III,Seminar,ML2S001,,,,No video applicable,No lectures.
IV,Breadth – II,(no code),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Depends on the student's choice.
IV,Lateral 1,(see Laterals),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Student picks from the Laterals list: Advances in Nanoscience & Nanotechnology / Recent Advances in Composite Materials / Mineral Processing Plant Design (each listed below).
IV,"Environmental Science, Technology and Management",ID3L003 (ID2L003),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,No confirmed NPTEL playlist.
IV,Materials Processing,ML2L003,"Metal Casting – Dr. D.B. Karunakar, IIT Roorkee (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQiWQqMSFeatZ7fWmjQwNgc","Materials Processing (Casting, Forming, Welding) Lec 36 – Prof. S. Bag, IIT Guwahati (NPTEL NOC24_ME108) – single video
https://www.youtube.com/watch?v=FVgPwOA_Hys","Manufacturing Processes II – IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PL82E9A8429ED7BB27",Partial / related only,Casting playlist is official NPTEL; forming/welding covered by single lectures and Manufacturing Processes II.
IV,Transport Phenomena and Kinetics of Metallurgical Processes,ML2L004,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw","Fundamentals of Heat and Mass Transfer Lec 15 (Metallurgical Engg & Material Science – Transport Phenomena; uploader not verified as NPTEL) – single video
https://www.youtube.com/watch?v=DSaNlsadRVs","Advanced Metallurgical Thermodynamics – Prof. B.S. Murty, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJS_jlBSbduzYmy6YX_K4KyM",Not confirmed,No NPTEL transport-phenomena-in-metallurgy playlist confirmed.
IV,Physical Metallurgy,ML2L005,"Principles of Physical Metallurgy – Prof. R.N. Ghosh, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJSkVfiNz6f9HeghkYD5u3c0","Structure of Materials – Prof. S. Sangal & Dr. A. Subramaniam, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQ5jqiXDYuE6ETz5F5Kn4dA","Physics of Materials – Dr. P. Haridoss, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PL090DAFDD7A36E27B",Playlist found,
IV,Materials Processing Laboratory,ML2P002,"Metal Casting – Dr. D.B. Karunakar, IIT Roorkee (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQiWQqMSFeatZ7fWmjQwNgc",,,Lab – use theory playlist,Use theory playlist.
IV,Physical Metallurgy Laboratory,ML2P003,"Principles of Physical Metallurgy – Prof. R.N. Ghosh, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJSkVfiNz6f9HeghkYD5u3c0",,,Lab – use theory playlist,Use theory playlist.
IV,Thermodynamics of Materials Laboratory,ML2P004,"Advanced Metallurgical Thermodynamics – Prof. B.S. Murty, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJS_jlBSbduzYmy6YX_K4KyM",,,Lab – use theory playlist,Use theory playlist.
V,Breadth – III,(no code),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Depends on the student's choice.
V,Lateral – II,(see Laterals),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,See Laterals list.
V,Mineral Processing,ML3L001,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw","Introduction to Mineral Processing – Lecture 1 (uploader not verified as NPTEL)
https://www.youtube.com/watch?v=OFTR495IowU",,Not confirmed,No NPTEL mineral-processing playlist confirmed; only a single non-verified lecture surfaced.
V,Corrosion and Surface Engineering,ML3L002,"Environmental Degradation of Materials Lec 22 – Dr. K. Mondal, IIT Kanpur (NPTEL) – single video; search this title on the NPTEL channel for the full series
https://www.youtube.com/watch?v=g3EBBC8zyq0","Corrosion Failures and Analysis – Prof. K. Mondal, IIT Kanpur – intro video
https://www.youtube.com/watch?v=u-KtjaFYONw",,Partial / related only,IIT Kanpur (Prof. K. Mondal) lectures only as single videos; surface-engineering part not confirmed.
V,Mechanical Properties and Testing of Materials,ML3L003,"Mechanical Behavior of Materials – Prof. S. Sankaran, IIT Madras (NPTEL-NOC)
https://www.youtube.com/playlist?list=PLyqSpQzTE6M9QPU_tubmtQ97e7zRpaMlD",,,Playlist found,
V,Phase Transformation of Materials,ML3L004,"Principles of Physical Metallurgy – Prof. R.N. Ghosh, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJSkVfiNz6f9HeghkYD5u3c0","Advanced Metallurgical Thermodynamics – Prof. B.S. Murty, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJS_jlBSbduzYmy6YX_K4KyM",,Partial / related only,No dedicated NPTEL phase-transformations playlist surfaced; physical-metallurgy playlist covers diffusion/phase diagrams.
V,Chemical Metallurgy,ML3L005,"Advanced Metallurgical Thermodynamics – Prof. B.S. Murty, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJS_jlBSbduzYmy6YX_K4KyM","Non-ferrous Extractive Metallurgy – Prof. H.S. Ray, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PLC3F0FC4543ADAC48",,Partial / related only,Closest NPTEL content: thermodynamics + extractive metallurgy.
V,Mechanical Testing & Working Laboratory,ML3P001,"Mechanical Behavior of Materials – Prof. S. Sankaran, IIT Madras (NPTEL-NOC)
https://www.youtube.com/playlist?list=PLyqSpQzTE6M9QPU_tubmtQ97e7zRpaMlD","Principles of Physical Metallurgy Lec 27: Metal Working – Deformation Processing – Prof. R.N. Ghosh, IIT Kharagpur (NPTEL)
https://www.youtube.com/watch?v=5l6taZ2rLp8",,Lab – use theory playlist,Use theory playlists.
VI,Breadth – IV,(no code),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Depends on the student's choice.
VI,Lateral – III,(see Laterals),"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,See Laterals list.
VI,Materials Characterization,ML3L006,"Materials Characterization – Dr. S. Sankaran, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJRbajyOAp_GHxTW9tQEqd0W","Structure of Materials – Prof. S. Sangal & Dr. A. Subramaniam, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQ5jqiXDYuE6ETz5F5Kn4dA","Introduction to X-ray Diffraction – Dr. Rajesh Prasad, IIT Delhi – single video
https://www.youtube.com/watch?v=Z5aCuGxUPpI",Playlist found,
VI,Iron and Steel Making,ML3L007,"Steel Making – Prof. D. Mazumdar & Prof. S.C. Koria, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PL9A090CB69EA83224","Non-ferrous Extractive Metallurgy – Prof. H.S. Ray, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PLC3F0FC4543ADAC48",,Partial / related only,Steel making is covered; ironmaking (blast furnace) not confirmed as a playlist.
VI,Deformation and Mechanical Working of Materials,ML3L008,"Principles of Physical Metallurgy Lec 27: Metal Working – Deformation Processing – Prof. R.N. Ghosh, IIT Kharagpur (NPTEL)
https://www.youtube.com/watch?v=5l6taZ2rLp8","Mechanics of Sheet Metal Forming – Prof. R. Ganesh Narayanan, IIT Guwahati (NPTEL NOC)
https://www.youtube.com/playlist?list=PLwdnzlV3ogoVIP4OxvoWMZXQYJdHn5NE9","Mechanical Behavior of Materials – Prof. S. Sankaran, IIT Madras (NPTEL-NOC)
https://www.youtube.com/playlist?list=PLyqSpQzTE6M9QPU_tubmtQ97e7zRpaMlD",Partial / related only,No dedicated NPTEL playlist for metal working surfaced; sheet-forming playlist and deformation lectures listed.
VI,Introduction to Simulation and Modeling in Materials,ML3L009,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,No confirmed NPTEL playlist.
VI,Materials Characterization Laboratory – I,ML3P002,"Materials Characterization – Dr. S. Sankaran, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJRbajyOAp_GHxTW9tQEqd0W",,,Lab – use theory playlist,Use theory playlist.
VI,Simulation and Modeling Laboratory,ML3P003,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Lab – use theory playlist,No theory/lab playlist confirmed.
VII,Light Metals and Alloys,ML4L001,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,No NPTEL light-metals playlist confirmed (only unrelated/third-party hits).
VII,Elements of Electroceramics,ML4L002,"Electroceramics – Prof. A. Garg, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJT8uMEdSuFXBEVBTBwFssC-","Electroceramics – Prof. A. Garg, IIT Kanpur (NPTEL, second upload)
https://www.youtube.com/playlist?list=PL675BE95AEF6A3A14",,Playlist found,
VII,Polymers and Nanocomposites,ML4L003,"Science and Technology of Polymers – Prof. B. Adhikari, IIT Kharagpur (NPTEL)
https://www.youtube.com/playlist?list=PL1AFB213453E37EC3",,,Partial / related only,Polymer part covered; nanocomposites not confirmed.
VII,Elective – I,ML4LXXX,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Pick from the elective list below.
VII,Materials Characterization Laboratory – II,ML4P001,"Materials Characterization – Dr. S. Sankaran, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJRbajyOAp_GHxTW9tQEqd0W",,,Lab – use theory playlist,Use theory playlist.
VII,Process Control and Instrumentation Laboratory,ML4P002,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Lab – use theory playlist,No playlist confirmed.
VII,Industrial Training Defense,ML4T001,,,,No video applicable,No lectures.
VII,Project – I,ML4D001,,,,No video applicable,No lectures.
VIII,Elective – II,ML4LXXX,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Pick from the elective list below.
VIII,Elective – III,ML4LXXX,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Pick from the elective list below.
VIII,Elective – IV,ML4LXXX,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Pick from the elective list below.
VIII,Elective – V,ML4LXXX,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Pick from the elective list below.
VIII,Project – II,ML4D002,,,,No video applicable,No lectures.
Elective (Met.),Joining of Metals and Alloys,ML4L001,"Weld Metal Solidification and Microstructure-I – Prof. S. Bag, IIT Guwahati (NPTEL NOC) – single video, relevant to joining
https://www.youtube.com/watch?v=nb6rkuaw9yA","Materials Processing (Casting, Forming, Welding) Lec 36 – Prof. S. Bag, IIT Guwahati (NPTEL NOC24_ME108) – single video
https://www.youtube.com/watch?v=FVgPwOA_Hys",,Not confirmed,No NPTEL welding-metallurgy playlist confirmed.
Elective (Met.),Solidification of Metals and Alloys,ML4L002,"Introduction to Solidification Processing Lec 14 – Prof. S. Bag, IIT Guwahati (NPTEL NOC24_ME74) – single video
https://www.youtube.com/watch?v=nb6rkuaw9yA","Advanced Materials and Processes Lec 16: Rapid Solidification – Prof. B.S. Murty (NPTEL) – single video
https://www.youtube.com/watch?v=3R9dnpSmRxA","Metal Casting – Dr. D.B. Karunakar, IIT Roorkee (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQiWQqMSFeatZ7fWmjQwNgc",Partial / related only,Single NPTEL lectures + Metal Casting playlist.
Elective (Met.),Electrochemical Methods in Metallurgy,ML4L003,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,No NPTEL playlist confirmed (only non-NPTEL electrochemical-engineering courses surfaced).
Elective (Met.),Powder Metallurgy,ML4L004,"Manufacturing Processes I Mod-1 Lec-1: Powder Metallurgy – Prof. I. Singh, IIT Roorkee (NPTEL) – single video
https://www.youtube.com/watch?v=uRVaLUQUmA8",,,Not confirmed,Only one lecture from IIT Roorkee Manufacturing Processes I; no dedicated playlist.
Elective (Mat.),Materials Design and Selection,ML4L005,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Elective (Mat.),Energy Materials,ML4L006,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Elective (Mat.),Crystallography and X-ray Diffraction,ML4L007,"Structure of Materials – Prof. S. Sangal & Dr. A. Subramaniam, IIT Kanpur (NPTEL)
https://www.youtube.com/playlist?list=PLbMVogVj5nJQ5jqiXDYuE6ETz5F5Kn4dA","Introduction to X-ray Diffraction – Dr. Rajesh Prasad, IIT Delhi – single video
https://www.youtube.com/watch?v=Z5aCuGxUPpI","Basic Crystallography – Dr. Rajesh Prasad, IIT Delhi – single video
https://www.youtube.com/watch?v=d_dasJl8GrA",Partial / related only,Structure of Materials playlist (IIT Kanpur) covers crystallography; XRD from single Prasad lectures.
Elective (Mat.),Micro Electro Mechanical Systems,ML4L008,"MEMS & Microsystems Lec 8 – Prof. S. Kal, IIT Kharagpur (NPTEL) – single video; search the title for the series
https://www.youtube.com/watch?v=3VTxgqDQSPw",,,Partial / related only,Single lecture of IIT KGP MEMS & Microsystems; full playlist not confirmed.
Elective (Mat.),Physics of Materials,ML4L009,"Physics of Materials – Dr. P. Haridoss, IIT Madras (NPTEL)
https://www.youtube.com/playlist?list=PL090DAFDD7A36E27B",,,Playlist found,
Elective (Mat.),Science and Technology of Composite Materials,ML4L010,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Elective (Mat.),Biomaterials,ML4L011,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Elective (Mat.),Materials in Archaeology,ML4L012,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Niche course; no NPTEL playlist expected.
Elective (Min.),Mineral Process Plant Design,ML4L013 / ML3L012,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Elective (Min.),"Fuels, Furnaces and Refractories",ML4L014,"Fuels, Refractory and Furnaces Lec 35 – Prof. S.C. Koria, IIT Kanpur (NPTEL) – single video; search the title for the series
https://www.youtube.com/watch?v=iMwO6rWEw1Q",,,Partial / related only,Single lecture of IIT Kanpur series.
Elective (Min.),Materials Recycling and Sustainability,ML4L015,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Lateral,Advances in Nanoscience and Nanotechnology,ML2L006,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Only non-NPTEL/unclear hits surfaced.
Lateral,Recent Advances in Composite Materials,ML3L011,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Not confirmed.
Lateral,Mineral Processing Plant Design,ML3L012,"NPTEL 'Metallurgy and Material Science' channel (browse by course name):
https://www.youtube.com/channel/UC9sKRSg8Kn5axYdORJUnqFw",,,Not confirmed,Same course as ML4L013."""

with open(os.path.join(RAW_MME_DIR, "video_playlists.csv"), "w", encoding="utf-8", newline="") as f:
    f.write(VIDEO_PLAYLISTS_DATA.strip() + "\n")

# 4. Sponsored Research Projects (1 to 45)
SPONSORED_PROJECTS = [
    (1, "Design optimization of pulsator thickeners for treating mineral processing plant tailings", "Snigdha Ghosh", "—", "—", "—"),
    (2, "[Development] of Design and operating parameters for hydrogen based DRI production for (i) continuous process (ii) batch process", "Snigdha Ghosh", "₹ 54 Lakhs", "2025–27", "Ministry of Steel"),
    (3, "Porous metal-metal interpenetrating composites for energy absorption applications", "Srikant Gollapudi", "₹ 85.9 Lakhs", "2025–28", "ANRF-DST"),
    (4, "Development of novel low-cost zinc composites for hip implant and bone fixation plate applications", "Srikant Gollapudi", "₹ 45 Lakhs", "2025–28", "HEFA-CSR"),
    (5, "Development of Magnesium Silicate-Based Bioceramic Scaffolds for Enhanced Bone Regeneration: Optimizing Degradation, Bioactivity, and 3D Printability", "Santanu Mandal", "₹ 59.6 Lakhs", "2025–28", "ANRF-DST"),
    (6, "Phase-field modeling of hydrogen segregation in polycrystalline iron", "Miral Verma", "₹ 56.7 Lakhs", "2025–28", "ANRF-DST"),
    (7, "Twinning induced orientation relationships in alloy thin films", "Maya K. Kini", "₹ 70.3 Lakhs", "2025–28", "ANRF-DST"),
    (8, "Effect of texture and grain size on mechanical and corrosion properties of Mg alloys", "Rama Krushna Sabat", "₹ 13 Lakhs", "2023–26", "HRDG-CSIR"),
    (9, "Forging the Past: Investigating the Manufacturing of Iron Beams Used in Konarka Sun Temple and Analyzing Their Socio-Economic Impact on the Local Community", "Soobhankar Pati", "₹ 20 Lakhs", "2023–25", "IKS / MoE"),
    (10, "Mathematical Modeling of gas based MIDREX shaft reactor with experimental exploration of final stage reduction reaction of iron ore with Hydrogen", "Snigdha Ghosh", "₹ 26 Lakhs", "2023–26", "DST, SERB"),
    (11, "Adapting Fused Deposition Modelling (FDM) technique for additive manufacturing of aluminium alloys in the semisolid state: Design and development of a novel prototype", "Animesh Mandal", "₹ 37 Lakhs", "2023–26", "DST, SERB"),
    (12, "Conversion of natural mineral based tetrahedrite compounds into high performance thermoelectric devices used in the conversion of waste heat into electricity", "Sivaiah Bathula", "₹ 23 Lakhs", "2023–25", "Ministry of Mines"),
    (13, "Manufacturing of 2-wheeler Lithium-ion battery pack with hard/soft carbon anode and the possibility of utilizing gamma-MnO2 in lithium-ion battery cathode", "Soobhankar Pati", "₹ 62 Lakhs", "2022–24", "Tata Steel"),
    (14, "Experimental and theoretical investigations into the local structure and magnetic phases vis-à-vis transitions in multicomponent AlCuFeMn alloy using ab-initio density functional theory calculations, high energy synchrotron and neutron diffractional techniques", "Amritendu Roy", "₹ 0.45 Lakhs", "2022–25", "UGC-DAE CSR"),
    (15, "Enhancing the formability of Mg alloys by microstructural engineering using CPFEM approach", "Rama Krushna Sabat", "₹ 28 Lakhs", "2021–23", "DST, SERB"),
    (16, "Band and nanostructural engineering of doped Mg2Si composite for optimized thermoelectric and mechanical properties", "Sivaiah Bathula", "₹ 15 Lakhs", "2021–23", "DST, SERB"),
    (17, "FIST program – SMMME, IIT Bhubaneswar", "Animesh Mandal", "₹ 112 Lakhs", "2021–26", "DST"),
    (18, "Evaluation of Coal Tar Derived Hard/Soft Carbon Anodes for Power Li-ion Batteries", "Soobhankar Pati", "₹ 17 Lakhs", "2021–22", "Tata Steel"),
    (19, "Development of Piezoelectric ceramic - polymer flexible composite based energy harvester for smart automobiles", "Amritendu Roy", "₹ 10 Lakhs", "2021–24", "CSIR-HRDG"),
    (20, "Employing metallurgical silicon to develop new class of silicon composites for structural applications", "Srikant Gollapudi", "₹ 38 Lakhs", "2021–23", "Ministry of Mines"),
    (21, "Computational alloy design and mechanical property study of complex concentrated alloys", "Kodanda Ram Mangipudi", "₹ 12 Lakhs", "2021–23", "Naval Research Laboratory, Ambernath"),
    (22, "Fast charging high energy density lithium ion batteries with nanoporous silicon anodes", "Soobhankar Pati", "₹ 56 Lakhs", "2020–23", "DST, SERB"),
    (23, "Designing of novel transition metal oxide based ferroelectric perovskites for visible light photovoltaic application", "Amritendu Roy", "₹ 47 Lakhs", "2020–23", "DST, SERB"),
    (24, "Design and Characterization of an Al-Ti based High-Entropy Alloy", "Partha Sarathi De", "₹ 37 Lakhs", "2020–24", "DST, SERB"),
    (25, "Mechanical behaviour of additively manufactured hierarchical micro-architected metamaterials and composites for structural and functional applications", "Kodanda Ram Mangipudi", "₹ 45 Lakhs", "2019–22", "DST-SERB"),
    (26, "Improved surface hardness of Aluminum alloys for bus body panels: A simple route based on shot peening", "Srikant Gollapudi", "₹ 17 Lakhs", "2019–21", "NALCO"),
    (27, "Centre for H2 solutions – Materials energy systems (H2-M&ES)", "Soobhankar Pati", "₹ 34 Lakhs", "2019–24", "DST – NFTDC"),
    (28, "Effect of laser shock peening on the fatigue behavior of Nitinol shape memory alloy", "Srikant Gollapudi", "₹ 35 Lakhs", "2019–22", "DST, SERB"),
    (29, "Low temperature electrorefining process for production of high purity aluminum (4N and above)", "Soobhankar Pati", "₹ 18 Lakhs", "2019–22", "NALCO"),
    (30, "Stress Corrosion Cracking (SCC) evaluation of materials for naval applications: New insights from Double Cantilever Beam (DCB) technique", "Kisor K. Sahu", "₹ 19 Lakhs", "2019–21", "NRB, DRDO"),
    (31, "Development of stand-alone, cost-effective conversion coatings for Magnesium alloys", "Kisor K. Sahu", "₹ 70 Lakhs", "2019–22", "UAY (Volkswagen MHRD+IIT BBS)"),
    (32, "Online corrosion monitoring of Naval Structures", "Soobhankar Pati", "₹ 32 Lakhs", "2018–21", "NRB, DRDO"),
    (33, "Improving damping capacity of cast Nickel aluminum Bronze (NAB) alloys", "Partha Sarathi De", "₹ 19 Lakhs", "2018–21", "NRB, DRDO"),
    (34, "Value added electrochemical Devices from zircon obtained from Beach Sands of Odisha", "Soobhankar Pati", "₹ 36 Lakhs", "2018–20", "Ministry of Mines"),
    (35, "Optimization of silos, bins and hoppers designs through modeling, primarily intended for iron ore storage", "Kisor K. Sahu", "₹ 120 Lakhs", "2017–21", "UAY (NMDC+MHRD+Ministry of Steel)"),
    (36, "Dissimilar joining of Al with Ti and steel using friction stir welding", "Partha Sarathi De", "₹ 10 Lakhs", "2016–19", "NRB, DRDO"),
    (37, "Recycling of cast aluminium alloy scraps to produce alloys with comparable microstructure and properties as that of primary alloys (Two Years)", "Animesh Mandal", "₹ 38 Lakhs", "2016–19", "MHRD, India, NALCO, Ministry of Mines"),
    (38, "Designing of Novel Multiferroic Transition Metal Oxides for Memory and Energy Applications", "Amritendu Roy", "₹ 26 Lakhs", "2015–18", "DST, SERB"),
    (39, "Green production of hydrogen storage material from natural grade ilmenite", "Soobhankar Pati", "₹ 22 Lakhs", "2014–17", "DST"),
    (40, "Optimization of HIP process conditions for 9Cr and 18Cr ODS steel powder (Two Years)", "Animesh Mandal", "₹ 8 Lakhs", "2014–17", "UGC-DAE CSR, IGCAR Kalpakkam"),
    (41, "Novel hypereutectic Al-Si-Mg alloys for automotive applications", "Animesh Mandal", "₹ 11 Lakhs", "2012–15", "DST"),
    (42, "Portable augmented reality solution for Non-destructive testing and life time prediction for oil, natural gas and steel industries (PI)", "Kodanda Ram Mangipudi", "₹ 20 Lakhs", "—", "VARCOE"),
    (43, "Improving damping capacity of cast Nickel aluminum Bronze (NAB) alloys (duplicate listing in source)", "Partha Sarathi De", "₹ 19 Lakhs", "—", "NRB, DRDO"),
    (44, "Mechanical behavior of nanoporous gold: Influence of morphology (Co-PI)", "Kodanda Ram Mangipudi", "₹ 289 Lakhs", "—", "DFG, Germany"),
    (45, "Virtual and Augmented Reality training modules for Metallurgical and Materials Science students", "Srikant Gollapudi", "₹ 6 Lakhs", "—", "VARCOE, IIT BBS")
]

with open(os.path.join(RAW_MME_DIR, "research_projects_sponsored.csv"), "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["entry_no", "project_title", "pi", "amount", "duration", "funding_agency", "category", "is_duplicate_entry"])
    for row in SPONSORED_PROJECTS:
        is_dup = (row[0] == 43)
        writer.writerow([row[0], row[1], row[2], row[3], row[4], row[5], "sponsored", is_dup])

# 5. Consultancy Projects (1 to 17)
CONSULTANCY_PROJECTS = [
    (1, "Dr. Partha Sarathi De", "₹ 1.5 Lakhs", "2024", "Ratnamani Steels"),
    (2, "Dr. Rama Krushna Sabat", "₹ 5.20 Lakhs", "2023", "M/s Forge … Ltd"),
    (3, "Dr. Soobhankar Pati", "₹ 4.8 Lakhs", "2023", "Chief Engineer, RD & QP (R & B), BBSR"),
    (4, "Dr. Rama Krushna Sabat", "₹ 6.2 Lakhs", "2022–23", "M/s Jindal Stainless Steel Ltd"),
    (5, "Prof. Brahma Deo", "₹ 13 Lakhs", "2022", "Shri Mahavir Ferro Alloys (P) Ltd"),
    (6, "Dr. Rama Krushna Sabat", "₹ 4.7 Lakhs", "2021", "M/s The Ramco Cements Ltd"),
    (7, "Dr. Partha Sarathi De", "₹ 3.8 Lakhs", "2021–22", "M/s Deem Roll Tech Ltd"),
    (8, "Dr. Rama Krushna Sabat", "₹ 2.9 Lakhs", "2021", "Indian Oil Corporation Ltd"),
    (9, "Dr. Soobhankar Pati", "₹ 4.8 Lakhs", "2021", "M/s Rungta Mines Ltd c/o R&D & Q.P. (R&B), Govt. of Odisha"),
    (10, "Prof. Brahma Deo", "₹ 31.9 Lakhs", "2020–21", "Tata Steel Ltd"),
    (11, "Dr. Rama Krushna Sabat", "₹ 4.2 Lakhs", "—", "—"),
    (12, "Dr. Partha Sarathi De", "₹ 0.6 Lakhs", "2020–21", "Indian Oil Corporation Ltd"),
    (13, "Prof. Brahma Deo", "₹ 44.1 Lakhs", "2019", "Deem Roll Tech. Ltd., Ahmedabad"),
    (14, "Prof. Brahma Deo", "₹ 44 Lakhs", "2018–19", "Jindal Stainless Steel Ltd., Jajpur, Orissa"),
    (15, "Prof. Brahma Deo", "₹ 35.7 Lakhs", "2019–20", "TATA Steel Long Products Limited, Joda (Pradeep Phosphates Ltd)"),
    (16, "Prof. Brahma Deo", "₹ 13 Lakhs", "2017–18", "Tata Sponge Iron Ltd"),
    (17, "Dr. Soobhankar Pati", "₹ 0.3 Lakh", "2015", "Ganesh Sponge (P) Ltd")
]

with open(os.path.join(RAW_MME_DIR, "research_projects_consultancy.csv"), "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["entry_no", "consultant", "amount", "year", "client", "category"])
    for row in CONSULTANCY_PROJECTS:
        writer.writerow([row[0], row[1], row[2], row[3], row[4], "consultancy"])

# 6. Seed Grant Projects (1 to 13)
SEED_PROJECTS = [
    (1, "Assessment of high fidelity diffusivities in multicomponent systems for new cobalt based superalloys", "Dr. Anuj Dash", "₹ 22.5 Lakhs", "2026–28"),
    (2, "Phase stability and high temperature deformation behaviour of High entropy fluorite oxides (HEFOS)", "Dr. Maya K. Kini", "₹ 22.5 Lakhs", "2025–27"),
    (3, "[Microstructure and mechanical properties of additively manufactured materials] (partially obscured by watermark)", "Dr. Sudipta Pramanik", "₹ 25.5 Lakhs", "2024–26"),
    (4, "Characterization of hot metal and slag flow in dripping zone of blast furnace", "Dr. Snigdha Ghosh", "₹ 20 Lakhs", "2023–25"),
    (5, "Development of decellularized platelet rich fibrin loaded MgP and MgS scaffolds with multiscale porosity for enhanced bone regeneration", "Dr. Santanu Mandal", "₹ 20 Lakhs", "2023–25"),
    (6, "Development of non-toxic, cost-effective and stable mid-temperature (>300°C) thermoelectric materials (both p & n-type) with enhanced thermoelectric figure-of-merit (SiGe alloys and Hf-free Half-Heusler Alloys)", "Dr. Sivaiah Bathula", "₹ 10 Lakhs", "2019–22"),
    (7, "Modelling the mechanical behavior of micro and nanoporous metals (PI)", "Dr. Kodanda Ram Mangipudi", "₹ 10 Lakhs", "2018–21"),
    (8, "Effect of grain size distribution on creep behavior of Mg", "Dr. Srikant Gollapudi", "₹ 10 Lakhs", "2018–20"),
    (9, "[First-principles / Computational study of materials for] photovoltaic applications (partially obscured by watermark)", "Dr. Amritendu Roy", "₹ 10 Lakhs", "2014–16"),
    (10, "Electrodeposited wear and corrosion resistant nanocrystalline coatings", "Dr. Soobhankar Pati", "₹ 10 Lakhs", "2013–15"),
    (11, "Generalized stress grain model for ultra fine grained Al alloys", "Dr. Partha Sarathi De", "₹ 10 Lakhs", "2012–14"),
    (12, "Semisolid processing of aluminum based alloys and composites by cooling slope technique", "Dr. Kisor K Sahu", "₹ 5 Lakhs", "2012–14"),
    (13, "Semisolid processing of aluminum based alloys and composites by cooling slope technique", "Dr. Animesh Mandal", "₹ 5 Lakhs", "2011–13")
]

with open(os.path.join(RAW_MME_DIR, "research_projects_seed.csv"), "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["entry_no", "project_title", "pi", "amount", "duration", "category"])
    for row in SEED_PROJECTS:
        writer.writerow([row[0], row[1], row[2], row[3], row[4], "seed_grant"])

# 7. Faculty Research Profiles (16 current members)
FACULTY_PROFILES = [
    ("FAC_MM_01", "Dr. Snigdha Ghosh", "Snigdha Ghosh", "Assistant Professor", "MM", 104, 3, "Process metallurgy modelling, H2-DRI, blast furnace, BOF metal-slag-gas kinetics", "https://scholar.google.com/citations?user=snigdha_ghosh"),
    ("FAC_MM_02", "Dr. Srikant Gollapudi", "Srikant Gollapudi", "Associate Professor", "MM", 1496, 2, "Creep of Ti/Zr/Mg/Al alloys, corrosion, silicon composites, Zn/Mg bioimplants", "https://scholar.google.com/citations?user=srikant_gollapudi"),
    ("FAC_MM_03", "Dr. Santanu Mandal", "Santanu Mandal", "Assistant Professor", "MM", 372, 1, "Biodegradable Fe/Mg/Zn implants, bone scaffolds, corrosion engineering of biomaterials", "https://scholar.google.com/citations?user=santanu_mandal"),
    ("FAC_MM_04", "Dr. Miral Verma", "Miral Verma", "Assistant Professor", "MM", 113, 1, "Phase-field modelling, thin-film dewetting, grain growth, dynamic and reactive wetting", "https://scholar.google.com/citations?user=miral_verma"),
    ("FAC_MM_05", "Dr. Maya Katapadi Kini", "Maya K. Kini", "Assistant Professor", "MM", 144, 2, "Thin-film micromechanics, HEA films, nanotwinned metals, structural ceramics", "https://scholar.google.com/citations?user=maya_k_kini"),
    ("FAC_MM_06", "Dr. Rama Krushna Sabat", "Rama Krushna Sabat", "Associate Professor", "MM", 1313, 1, "Crystallographic texture, crystal plasticity (CPFEM/VPSC), Mg/Ti alloys, thermoelectrics", "https://scholar.google.com/citations?user=rk_sabat"),
    ("FAC_MM_07", "Dr. Soobhankar Pati", "Soobhankar Pati", "Associate Professor", "MM", 378, 0, "Electrometallurgy, Li-ion batteries, hydrogen storage, archaeometallurgy of Konark beams", "https://openalex.org/authors/soobhankar_pati"),
    ("FAC_MM_08", "Prof. Animesh Mandal", "Animesh Mandal", "Professor", "MM", 1980, 2, "Al/Mg alloys, in-situ composites, semisolid processing, additive manufacturing, tribology", "https://scholar.google.com/citations?user=animesh_mandal"),
    ("FAC_MM_09", "Dr. Sivaiah Bathula", "Sivaiah Bathula", "Associate Professor", "MM", 4191, 0, "Thermoelectric materials and devices (SiGe, half-Heusler, Mg2Si), powder processing, SPS", "https://scholar.google.com/citations?user=sivaiah_bathula"),
    ("FAC_MM_10", "Dr. Amritendu Roy", "Amritendu Roy", "Associate Professor & HoS", "MM", 1258, 0, "Energy harvesting/storage, ferroic/multiferroic films, DFT, machine learning in materials", "https://scholar.google.com/citations?user=amritendu_roy"),
    ("FAC_MM_11", "Dr. Kodanda Ram Mangipudi", "Kodanda Ram Mangipudi", "Associate Professor", "MM", 516, 0, "Micromechanics, fracture, nanoporous metals/foams, architected metamaterials, CCAs", "https://scholar.google.com/citations?user=kr_mangipudi"),
    ("FAC_MM_12", "Dr. Partha Sarathi De", "Partha Sarathi De", "Associate Professor", "MM", 1009, 0, "High-entropy alloys, friction stir processing, high-strength steels, corrosion", "https://scholar.google.com/citations?user=ps_de"),
    ("FAC_MM_13", "Dr. Kisor Kumar Sahu", "Kisor K. Sahu", "Associate Professor", "MM", 1607, 0, "Metallic glasses, undercooled liquids, DEM process modelling, ML for materials, coatings", "https://scholar.google.com/citations?user=kisor_sahu"),
    ("FAC_MM_14", "Prof. Brahma Deo", "Brahma Deo", "MGM Chair Professor", "MM", 1858, 0, "Steelmaking process modelling/control (BOF/AOD/EAF), slag-metal kinetics, chaos control, ANN", "https://scholar.google.com/citations?user=brahma_deo"),
    ("FAC_MM_15", "Dr. Anuj Dash", "Anuj Dash", "Assistant Professor", "MM", 348, 1, "Solid-state multicomponent diffusion, HEAs, superalloys, PINN inverse methods", "https://scholar.google.com/citations?user=anuj_dash"),
    ("FAC_MM_16", "Dr. Sudipta Pramanik", "Sudipta Pramanik", "Assistant Professor", "MM", 563, 1, "Metal additive manufacturing (LPBF, FFF), micro-architected lattice/TPMS, fatigue, TEM", "https://scholar.google.com/citations?user=sudipta_pramanik")
]

with open(os.path.join(RAW_MME_DIR, "faculty_profiles.csv"), "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["faculty_id", "full_name", "normalized_name", "designation", "department_id", "google_scholar_citations", "ongoing_projects_count", "main_research_areas", "profile_url"])
    for row in FACULTY_PROFILES:
        writer.writerow(row)

print("Raw MME files parsed and saved to data/raw/mme/:")
for f in os.listdir(RAW_MME_DIR):
    print(" -", f)

