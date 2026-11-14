import os
import re
import csv
import sys
import openpyxl

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FILE_A = "SDE_Prep_Roadmap_with_Playlists.xlsx"
FILE_B = "Top_SDE_Project_GitHub_Repos.xlsx"
OUTPUT_DIR = "output"

# ----------------------------------------------------
# 1. Fixed Phase Mapping (Steps 1 to 35)
# ----------------------------------------------------
PHASES = [
    {
        "phase_order": 1,
        "phase_id": "P1_Programming_and_Dev_Basics",
        "phase_name": "Programming & Dev Basics",
        "step_range": "1-2",
        "steps": [1, 2],
        "phase_objective": "Master foundational programming language syntax, control flow, functions, OOP basics, and standard collections alongside version control with Git and GitHub.",
        "learner_outcome": "The learner can write modular code in their chosen language and collaborate via GitHub commits, branches, and pull requests.",
        "next_phase_id": "P2_DSA_Foundations"
    },
    {
        "phase_order": 2,
        "phase_id": "P2_DSA_Foundations",
        "phase_name": "DSA Foundations",
        "step_range": "3-8",
        "steps": [3, 4, 5, 6, 7, 8],
        "phase_objective": "Understand Big-O algorithmic complexity analysis and core linear data structures including arrays, strings, hash maps, sorting algorithms, and binary search.",
        "learner_outcome": "The learner can evaluate time and space complexity and solve foundational array, string, hashing, sorting, and binary search problems.",
        "next_phase_id": "P3_DSA_Core_Techniques"
    },
    {
        "phase_order": 3,
        "phase_id": "P3_DSA_Core_Techniques",
        "phase_name": "DSA Core Techniques",
        "step_range": "9-17",
        "steps": [9, 10, 11, 12, 13, 14, 15, 16, 17],
        "phase_objective": "Learn essential algorithmic problem-solving paradigms including two pointers, sliding window, linked lists, stacks, queues, recursion, backtracking, bit manipulation, and greedy methods.",
        "learner_outcome": "The learner can identify and apply intermediate data structure techniques and recursion patterns to complex algorithmic challenges.",
        "next_phase_id": "P4_Trees_and_Graphs"
    },
    {
        "phase_order": 4,
        "phase_id": "P4_Trees_and_Graphs",
        "phase_name": "Trees & Graphs",
        "step_range": "18-24",
        "steps": [18, 19, 20, 21, 22, 23, 24],
        "phase_objective": "Master hierarchical and network structures covering binary trees, binary search trees, heaps, tries, graph traversals, shortest path algorithms, and disjoint sets.",
        "learner_outcome": "The learner can build, traverse, and query tree and graph structures and implement shortest path and minimum spanning tree algorithms.",
        "next_phase_id": "P5_Dynamic_Programming_and_Practice"
    },
    {
        "phase_order": 5,
        "phase_id": "P5_Dynamic_Programming_and_Practice",
        "phase_name": "Dynamic Programming & Practice",
        "step_range": "25-27",
        "steps": [25, 26, 27],
        "phase_objective": "Build dynamic programming mastery from 1D knapsack patterns to 2D grid and string algorithms, followed by timed mixed interview pattern practice.",
        "learner_outcome": "The learner can solve 1D and multidimensional dynamic programming problems and tackle timed technical interview sets.",
        "next_phase_id": "P6_CS_Core_Subjects"
    },
    {
        "phase_order": 6,
        "phase_id": "P6_CS_Core_Subjects",
        "phase_name": "CS Core Subjects",
        "step_range": "28-32",
        "steps": [28, 29, 30, 31, 32],
        "phase_objective": "Master fundamental computer science topics including OOP and low-level design, database management systems, relational SQL, operating systems concepts, and computer networks.",
        "learner_outcome": "The learner can answer in-depth core CS questions, write complex SQL queries, and architect class structures using SOLID design patterns.",
        "next_phase_id": "P7_System_Design_and_Backend"
    },
    {
        "phase_order": 7,
        "phase_id": "P7_System_Design_and_Backend",
        "phase_name": "System Design & Backend",
        "step_range": "33-34",
        "steps": [33, 34],
        "phase_objective": "Learn high-level system design architecture and backend engineering, covering scaling, caching, sharding, REST APIs, authentication, and Docker containerization.",
        "learner_outcome": "The learner can design distributed scalable system architectures and deploy containerized full-stack backend services with database integration.",
        "next_phase_id": "P8_Interview_Readiness"
    },
    {
        "phase_order": 8,
        "phase_id": "P8_Interview_Readiness",
        "phase_name": "Interview Readiness",
        "step_range": "35",
        "steps": [35],
        "phase_objective": "Prepare for real-world technical and behavioural interviews through STAR framework storytelling, clear communication, and timed mock evaluations.",
        "learner_outcome": "The learner can articulate technical decisions clearly under interview conditions and excel in behavioral and live coding evaluations.",
        "next_phase_id": "END"
    }
]

STEP_TO_PHASE = {}
for p in PHASES:
    for s in p["steps"]:
        STEP_TO_PHASE[s] = p

TIER_METADATA = {
    "A": ("Standard introduction", "Start here"),
    "B": ("Conceptual / alternative explanation", "Use if A is unclear"),
    "C": ("Practice-oriented", "Spend most time here with real problems")
}

# ----------------------------------------------------
# 2. Key Concepts & Skills Derived (for File 2)
# ----------------------------------------------------
STEP_KEY_CONCEPTS = {
    1: "Master language syntax and control flow; Implement modular functions; Apply basic object-oriented programming principles; Utilize standard library collections and data structures; Perform file input/output operations",
    2: "Track changes with Git commits; Create and switch development branches; Merge branch histories resolving conflicts; Collaborate via GitHub pull requests",
    3: "Differentiate time and space complexity; Evaluate best, worst, and average case performance; Analyze iterative loops mathematically; Derive recurrence relations for recursive algorithms",
    4: "Traverse multi-dimensional arrays; Compute prefix sum queries; Apply Kadane's algorithm for maximum subarray; Manipulate 2D matrix data; Perform in-place array transformations",
    5: "Verify palindromes and string properties; Detect anagram frequencies; Apply KMP and Rabin-Karp pattern matching; Efficiently construct strings with string builders",
    6: "Understand hash functions and collision resolution; Build frequency maps for counts; Solve two-sum lookup problems; Apply hash sets for constant-time membership checks",
    7: "Implement elementary sorts (bubble, selection, insertion); Implement divide-and-conquer sorts (merge, quick); Implement heap sort and counting sort; Analyze sorting algorithm stability and runtime",
    8: "Implement classic binary search on sorted sequences; Determine lower and upper bounds; Search across rotated sorted arrays; Apply binary search on monotonic answer spaces",
    9: "Apply opposite-end two pointer scans; Implement same-direction fast-slow pointers; Find target pairs in sorted arrays; Reduce quadratic nested loops to linear time",
    10: "Maintain fixed-size sliding windows; Adjust dynamic variable-length windows; Track window state using hash maps; Apply monotonic deques for sliding window extrema",
    11: "Manipulate singly, doubly, and circular linked lists; Reverse linked list segments; Apply fast and slow pointer cycle detection; Merge sorted linked lists; Implement LRU cache eviction logic",
    12: "Understand LIFO stack mechanics; Validate balanced parenthesis expressions; Build monotonic stacks for next greater element; Implement constant-time min stack structures",
    13: "Understand FIFO queue semantics; Implement circular queue buffers; Utilize double-ended queues (deques); Implement queues using stack primitives; Prepare queue structures for BFS traversals",
    14: "Define robust recursive base cases; Visualize execution trees; Apply divide-and-conquer problem decomposition; Formulate memoisation state transitions",
    15: "Generate power sets and subsets; Formulate permutation search trees; Compute combination sequences; Solve N-Queens constraint satisfaction; Implement backtracking search for Sudoku",
    16: "Execute bitwise AND, OR, XOR, and bit shifts; Set, clear, and toggle specific bit positions; Apply XOR properties for element cancellation; Construct bitmasks for subset enumeration",
    17: "Prove greedy choices via exchange arguments; Solve interval scheduling problems; Implement activity selection algorithms; Construct optimal prefix trees using Huffman coding",
    18: "Execute DFS and BFS binary tree traversals; Calculate binary tree height and diameter; Find lowest common ancestors (LCA); Reconstruct trees from traversal orders",
    19: "Perform binary search tree insertions, deletions, and lookups; Validate BST invariant ordering; Leverage inorder traversal monotonicity; Understand self-balancing tree concepts",
    20: "Maintain min-heap and max-heap invariants; Implement in-place heapify procedures; Extract top-K frequent and extreme elements; Merge K sorted lists efficiently; Compute running median over dynamic streams",
    21: "Construct prefix trees (tries); Implement prefix insertion and lookup; Build prefix autocomplete features; Solve word search II grid problems",
    22: "Construct adjacency lists and matrix graph representations; Execute breadth-first and depth-first searches; Identify connected graph components; Detect cycles in directed and undirected graphs; Perform topological sorting on DAGs",
    23: "Compute single-source shortest paths via Dijkstra; Handle negative weights with Bellman-Ford; Compute all-pairs shortest paths via Floyd-Warshall; Find minimum spanning trees using Prim; Construct MSTs using Kruskal",
    24: "Implement disjoint set union (DSU); Apply union by rank optimization; Accelerate find queries with path compression; Execute Kruskal's algorithm with DSU; Count dynamic connected components",
    25: "Differentiate top-down memoisation from bottom-up tabulation; Formulate 1D dynamic programming state transitions; Solve 0/1 and unbounded knapsack variations; Optimize DP auxiliary space complexity",
    26: "Compute longest common subsequence (LCS); Calculate string edit distances; Count unique grid paths with obstacles; Solve interval dynamic programming problems; Implement dynamic programming over tree structures",
    27: "Recognize algorithmic patterns rapidly under timed conditions; Formulate optimal solutions across mixed problem types; Revise core DSA templates; Execute timed technical interview sets",
    28: "Apply SOLID object-oriented design principles; Implement Gang of Four design patterns; Architect modular class schemas; Solve machine coding low-level design problems",
    29: "Design relational entity-relationship (ER) models; Perform database table normalization; Manage database transactions under ACID guarantees; Optimize query performance using database indexes",
    30: "Execute relational inner, left, right, and full joins; Aggregate grouped data with HAVING clauses; Compute rankings and running totals with window functions; Formulate correlated subqueries; Optimize SQL execution plans",
    31: "Differentiate operating system processes and threads; Analyze CPU scheduling algorithms; Identify and prevent deadlock conditions; Understand virtual memory, paging, and page replacement; Analyze file system architectures",
    32: "Differentiate OSI and TCP/IP layered network models; Compare TCP reliability with UDP latency; Understand HTTP/HTTPS request-response cycles; Trace DNS resolution hierarchies; Implement network socket communication",
    33: "Design scalable distributed architectures; Implement multi-tier caching strategies; Configure load balancers and database sharding; Leverage asynchronous message queues; Evaluate trade-offs under the CAP theorem; Present architectural case studies",
    34: "Build RESTful API endpoints; Implement user authentication and authorization; Integrate persistent relational databases; Containerize applications using Docker and Docker Compose; Deploy full-stack services to production",
    35: "Structure behavioural responses using the STAR method; Communicate architectural and algorithmic thought processes clearly; Conduct timed live coding mock interviews; Practice technical system design mock interviews"
}

# ----------------------------------------------------
# 3. Checkpoint Classification (for File 3)
# ----------------------------------------------------
STEP_CHECKPOINTS_METADATA = {
    1: ("PROBLEM_SET", 30, 30, "Pass when 30 basic problems are solved correctly in the chosen language."),
    2: ("BUILD_OR_SHIP", 1, 1, "Pass when a project is committed to GitHub and at least one pull request is successfully opened."),
    3: ("EXPLAIN_CONCEPT", 20, 20, "Pass when the time and space complexity of 20 code snippets is accurately determined without execution."),
    4: ("PROBLEM_SET", 30, 30, "Pass when 30 easy to medium array problems are solved."),
    5: ("PROBLEM_SET", 20, 20, "Pass when 20 string problems are solved."),
    6: ("PROBLEM_SET", 20, 20, "Pass when 20 hash map and set problems are solved."),
    7: ("PROBLEM_SET", 10, 10, "Pass when 5 sorting algorithms are implemented from scratch and 10 sorting problems are solved."),
    8: ("PROBLEM_SET", 25, 25, "Pass when 25 binary search problems are solved."),
    9: ("PROBLEM_SET", 15, 15, "Pass when 15 two-pointer problems are solved."),
    10: ("PROBLEM_SET", 15, 15, "Pass when 15 sliding window problems are solved."),
    11: ("PROBLEM_SET", 20, 20, "Pass when 20 linked list problems are solved."),
    12: ("PROBLEM_SET", 15, 15, "Pass when 15 stack problems are solved."),
    13: ("PROBLEM_SET", 10, 10, "Pass when 10 queue and deque problems are solved."),
    14: ("PROBLEM_SET", 15, 15, "Pass when 15 recursion problems are solved."),
    15: ("PROBLEM_SET", 15, 15, "Pass when 15 backtracking problems are solved."),
    16: ("PROBLEM_SET", 12, 12, "Pass when 12 bit manipulation problems are solved."),
    17: ("PROBLEM_SET", 15, 15, "Pass when 15 greedy algorithm problems are solved."),
    18: ("PROBLEM_SET", 25, 25, "Pass when 25 binary tree problems are solved."),
    19: ("PROBLEM_SET", 10, 10, "Pass when 10 binary search tree problems are solved."),
    20: ("PROBLEM_SET", 12, 12, "Pass when 12 heap and priority queue problems are solved."),
    21: ("PROBLEM_SET", 6, 6, "Pass when a trie data structure is implemented and 6 trie problems are solved."),
    22: ("PROBLEM_SET", 20, 20, "Pass when 20 graph traversal problems are solved."),
    23: ("PROBLEM_SET", 8, 8, "Pass when 8 shortest path and minimum spanning tree problems are solved."),
    24: ("PROBLEM_SET", 6, 6, "Pass when 6 disjoint set union problems are solved."),
    25: ("PROBLEM_SET", 25, 25, "Pass when 25 foundational dynamic programming problems are solved."),
    26: ("PROBLEM_SET", 25, 25, "Pass when 25 advanced multi-dimensional dynamic programming problems are solved."),
    27: ("MOCK_OR_TIMED", 75, 150, "Pass when 75 to 150 mixed interview problems are completed and followed by timed mock assessments."),
    28: ("BUILD_OR_SHIP", 4, 4, "Pass when 4 complete low-level design machine coding problems are coded."),
    29: ("EXPLAIN_CONCEPT", None, None, "Pass when database indexing mechanics and transaction isolation levels are accurately explained from memory."),
    30: ("PROBLEM_SET", 40, 40, "Pass when 40 SQL problems including window functions are solved."),
    31: ("EXPLAIN_CONCEPT", 40, 40, "Pass when the top 40 operating systems interview questions are correctly answered."),
    32: ("EXPLAIN_CONCEPT", None, None, "Pass when the end-to-end network lifecycle of typing a URL into a browser is accurately traced."),
    33: ("BUILD_OR_SHIP", 8, 8, "Pass when 8 distributed systems architectures are designed on paper."),
    34: ("BUILD_OR_SHIP", 1, 1, "Pass when a containerized full-stack project is shipped with a live demo."),
    35: ("MOCK_OR_TIMED", 6, None, "Pass when at least 6 mock technical and behavioural interviews are completed.")
}

# ----------------------------------------------------
# 4. Repo Step Requirements & Extra Skills (for File 4)
# ----------------------------------------------------
REPO_REQUIREMENTS_METADATA = {
    1: ([1, 2, 6, 31, 32, 34], "Network sockets & protocols; Systems programming; Concurrency"),
    2: ([1, 2], "Framework-specific project workflows; Language ecosystem tools"),
    3: ([1, 2, 34], "Frontend UI basics; REST API design"),
    4: ([1, 2, 32], "Socket programming; Web scraping basics"),
    5: ([1, 2, 28, 29, 30, 34], "REST API consumption; JWT authentication; Frontend integration; Unit and integration testing"),
    6: ([1, 2, 29, 32, 33, 34], "Distributed caching (Redis/Memcached); Rate limiting algorithms (Token bucket)"),
    7: ([1, 32, 33], "Microservices architecture; Cloud system diagrams"),
    8: ([1, 6, 32, 33], "Asynchronous messaging; In-memory data store architecture"),
    9: ([29, 31, 32, 33], "High-throughput architectures; Cloud infrastructure"),
    10: ([29, 32, 33, 35], "Technical whiteboard presentation"),
    11: ([1, 2, 28], "Design patterns (Factory, Strategy, Observer); Unit testing frameworks (JUnit/pytest)"),
    12: ([1, 2, 3, 4, 7, 8, 11, 22], "Long-term study habits; Self-directed CS learning"),
    13: ([1, 2, 34], "Frontend basics; DevOps fundamentals"),
    14: ([1, 2], "REST API consumption; JSON parsing; HTTP clients"),
    15: ([1, 2, 30, 34], "HTML/CSS/JavaScript; Responsive web design; Node.js/Express"),
    16: ([1, 2, 3, 29, 31, 32], "Compiler design; Theory of computation"),
    17: ([1, 2], "HTML/CSS/JavaScript; DOM manipulation; CSS animations"),
    18: ([1, 2], "HTML/CSS/JavaScript; Web browser APIs"),
    19: ([1, 2, 29, 34], "Docker Compose multi-container orchestration; Reverse proxy (Nginx); Environment isolation"),
    20: ([2, 31, 34], "CI/CD pipelines (GitHub Actions); Linux sysadmin; Kubernetes basics"),
    21: ([1, 2, 34], "Open-source contribution workflow; Self-hosting configuration"),
    22: ([1, 2, 3, 4, 7, 8, 18, 22], "Algorithm visualization techniques; Unit testing algorithm correctness"),
    23: ([1, 2, 3, 4, 7, 8, 11, 22], "Algorithm visualization techniques; Java testing frameworks"),
    24: ([1, 2, 3, 4, 7, 8, 18, 22], "HTML/CSS/JavaScript; DOM rendering for visualizers"),
    25: ([1, 3, 4, 6, 11, 12, 18], "Jupyter notebooks; Interactive test-driven problem solving"),
    26: ([1, 2], "Open-source contribution workflow; Git fork-and-pull model; Code review etiquette"),
    27: ([1, 2], "Open-source contribution workflow; Navigating large codebases; Issue tracking"),
    28: ([1, 2, 28, 29, 30, 31, 34], "Spring Boot framework; JVM internals; Redis caching"),
    29: ([2, 31], "Bash shell scripting; Unix CLI utilities (grep, sed, awk, curl)"),
    30: ([1, 2, 34], "LLM APIs & embeddings; Vector databases (Chroma/Pinecone); RAG pipeline design; LangChain/LlamaIndex"),
    31: ([1, 2, 34], "LLM APIs & embeddings; Autonomous agent architectures; Tool use and function calling"),
    32: ([1, 2], "LLM APIs & embeddings; Prompt engineering; Generative AI fundamentals"),
    33: ([1, 2], "ML basics; Scikit-Learn; Data preprocessing; Model evaluation"),
    34: ([1, 2], "LLM fine-tuning (PEFT/LoRA); Model quantization; GPU acceleration; Hugging Face"),
    35: ([1, 2], "Python idiomatic style; CLI application packaging")
}

# ----------------------------------------------------
# 5. Portfolio Requirements & Extra Skills (for File 5)
# ----------------------------------------------------
PORTFOLIO_REQUIREMENTS_METADATA = {
    1: ([1, 2, 6, 31, 32, 34], "Network sockets & protocols; In-memory data persistence; Concurrency"),
    2: ([1, 2, 29, 32, 33, 34], "Distributed caching (Redis); Rate limiting algorithms (Token bucket)"),
    3: ([1, 2, 28, 29, 30, 34], "JWT authentication; Frontend framework integration; Automated API testing"),
    4: ([1, 2, 28], "Design patterns (Factory, Strategy, State); Unit testing frameworks"),
    5: ([1, 2, 29, 31, 34], "CI/CD pipelines (GitHub Actions); Docker Compose orchestration; Cloud deployment"),
    6: ([1, 2, 34], "LLM APIs & embeddings; Vector databases (Chroma/Pinecone); RAG pipeline design"),
    7: ([1, 2], "Open-source contribution workflow; Code review etiquette; Remote issue triage"),
    8: ([1, 2, 3, 4, 7, 8, 18, 22], "HTML/CSS/JavaScript; Canvas / DOM animation rendering")
}

def get_latest_phase(steps):
    phases = [STEP_TO_PHASE[s] for s in steps]
    max_p = max(phases, key=lambda p: p["phase_order"])
    return max_p["phase_id"]

def build():
    print("=" * 80)
    print("Building SDE Knowledge Base CSVs for eBuddy")
    print("=" * 80)

    # 1. Load File A
    wb_a = openpyxl.load_workbook(FILE_A, data_only=False)
    ws_roadmap = wb_a["Roadmap"]
    ws_playlists = wb_a["Playlists"]

    roadmap_steps_data = {}
    for r in range(2, ws_roadmap.max_row + 1):
        step_val = ws_roadmap.cell(row=r, column=1).value
        if step_val is None:
            continue
        step_num = int(step_val)
        skill_name = str(ws_roadmap.cell(row=r, column=2).value).strip()
        what_to_cover = str(ws_roadmap.cell(row=r, column=3).value).strip()
        checkpoint = str(ws_roadmap.cell(row=r, column=4).value).strip()
        roadmap_steps_data[step_num] = {
            "step_number": step_num,
            "topic_skill": skill_name,
            "what_to_cover": what_to_cover,
            "checkpoint_text": checkpoint
        }

    # 2. Build File 1: 01_sde_roadmap_overview.csv
    file1_rows = []
    for p in PHASES:
        p_steps = p["steps"]
        topics = [roadmap_steps_data[s]["topic_skill"] for s in p_steps]
        topics_str = " | ".join(topics)
        file1_rows.append({
            "phase_order": p["phase_order"],
            "phase_id": p["phase_id"],
            "phase_name": p["phase_name"],
            "step_range": p["step_range"],
            "number_of_topics": len(p_steps),
            "topics_in_order": topics_str,
            "phase_objective": p["phase_objective"],
            "learner_outcome": p["learner_outcome"],
            "next_phase_id": p["next_phase_id"]
        })

    # 3. Build File 2: 02_phase_learning_content.csv
    file2_rows = []
    link_type_counts = {}

    for r in range(2, ws_playlists.max_row + 1):
        step_val = ws_playlists.cell(row=r, column=1).value
        if step_val is None:
            continue
        step_num = int(step_val)
        skill_name = str(ws_playlists.cell(row=r, column=2).value).strip()
        tier = str(ws_playlists.cell(row=r, column=3).value).strip()
        purpose = str(ws_playlists.cell(row=r, column=4).value).strip()
        resource_title = str(ws_playlists.cell(row=r, column=5).value).strip()
        creator = str(ws_playlists.cell(row=r, column=6).value).strip()
        
        # Link cell & hyperlink
        link_cell = ws_playlists.cell(row=r, column=7)
        url = link_cell.hyperlink.target if (link_cell.hyperlink and link_cell.hyperlink.target) else ""
        link_type = str(ws_playlists.cell(row=r, column=8).value).strip()
        notes = str(ws_playlists.cell(row=r, column=9).value or "").strip()

        # Extract extra URL in notes
        extra_urls = re.findall(r"https?://[^\s]+", notes)
        extra_url_str = extra_urls[0] if extra_urls else ""

        link_type_counts[link_type] = link_type_counts.get(link_type, 0) + 1

        phase_info = STEP_TO_PHASE[step_num]
        rm_data = roadmap_steps_data[step_num]
        tier_mean, usage = TIER_METADATA[tier]

        file2_rows.append({
            "phase_order": phase_info["phase_order"],
            "phase_id": phase_info["phase_id"],
            "step_number": step_num,
            "topic_skill": rm_data["topic_skill"],
            "what_to_learn": rm_data["what_to_cover"],
            "key_concepts_and_skills_derived": STEP_KEY_CONCEPTS[step_num],
            "tier": tier,
            "tier_meaning": tier_mean,
            "usage_guidance": usage,
            "purpose": purpose,
            "resource_title": resource_title,
            "creator": creator,
            "url": url,
            "link_type": link_type,
            "link_verified": "FALSE",
            "notes": notes,
            "extra_url_in_notes": extra_url_str
        })

    # Sort File 2 by phase_order, step_number, then tier (A, B, C)
    tier_order = {"A": 1, "B": 2, "C": 3}
    file2_rows.sort(key=lambda x: (x["phase_order"], x["step_number"], tier_order.get(x["tier"], 9)))

    # 4. Build File 3: 03_topic_checkpoints.csv
    file3_rows = []
    for step_num in range(1, 36):
        phase_info = STEP_TO_PHASE[step_num]
        rm_data = roadmap_steps_data[step_num]
        cp_type, c_min, c_max, crit_summary = STEP_CHECKPOINTS_METADATA[step_num]
        file3_rows.append({
            "phase_order": phase_info["phase_order"],
            "phase_id": phase_info["phase_id"],
            "step_number": step_num,
            "topic_skill": rm_data["topic_skill"],
            "checkpoint_text": rm_data["checkpoint_text"],
            "checkpoint_type": cp_type,
            "target_count_min": str(c_min) if c_min is not None else "",
            "target_count_max": str(c_max) if c_max is not None else "",
            "passing_criteria_summary": crit_summary
        })

    # 5. Load File B (Repos & Portfolio Path)
    wb_b = openpyxl.load_workbook(FILE_B, data_only=False)
    ws_repos = wb_b["Repos"]
    ws_pp = wb_b["Portfolio Path"]

    raw_repos = []
    for r in range(2, ws_repos.max_row + 1):
        num_val = ws_repos.cell(row=r, column=1).value
        if num_val is None:
            continue
        num = int(num_val)
        repo_name = str(ws_repos.cell(row=r, column=2).value).strip()
        cat = str(ws_repos.cell(row=r, column=3).value).strip()
        offers = str(ws_repos.cell(row=r, column=4).value).strip()
        ideas = str(ws_repos.cell(row=r, column=5).value).strip()
        diff = str(ws_repos.cell(row=r, column=6).value).strip()
        best_for = str(ws_repos.cell(row=r, column=7).value).strip()
        stars = str(ws_repos.cell(row=r, column=8).value or "").strip()
        stack = str(ws_repos.cell(row=r, column=9).value).strip()
        gh_link = str(ws_repos.cell(row=r, column=10).value).strip()

        owner, short_name = repo_name.split("/")
        raw_repos.append({
            "num": num,
            "repo_id": f"REPO-{num:02d}",
            "repository": repo_name,
            "owner": owner.lower(),
            "short_name": short_name.lower(),
            "category": cat,
            "what_it_offers": offers,
            "example_project_ideas": ideas,
            "difficulty": diff,
            "best_for": best_for,
            "stars_note": stars,
            "tech_stack": stack,
            "github_url": gh_link
        })

    # Portfolio Path parsing & resolution
    portfolio_projects_data = []
    repo_to_portfolio_projects = {rp["repo_id"]: [] for rp in raw_repos}
    token_resolution_table = {}

    for r in range(3, ws_pp.max_row + 1):
        proj_val = ws_pp.cell(row=r, column=1).value
        if proj_val is None or str(proj_val).strip() == "":
            continue
        project_name = str(proj_val).strip()
        why_impresses = str(ws_pp.cell(row=r, column=2).value).strip()
        repos_short_cell = str(ws_pp.cell(row=r, column=3).value).strip()
        skills_shown = str(ws_pp.cell(row=r, column=4).value).strip()

        tokens = [t.strip().lower() for t in repos_short_cell.split(",") if t.strip()]
        matched_repos = []
        for token in tokens:
            matches = [rp for rp in raw_repos if rp["short_name"] == token or rp["owner"] == token]
            if not matches:
                raise ValueError(f"Portfolio Path token '{token}' in project '{project_name}' did not match any repo!")
            token_resolution_table[token] = [m["repository"] for m in matches]
            for m in matches:
                if m not in matched_repos:
                    matched_repos.append(m)

        resolved_names = [m["repository"] for m in matched_repos]
        resolved_ids = [m["repo_id"] for m in matched_repos]

        for m in matched_repos:
            if project_name not in repo_to_portfolio_projects[m["repo_id"]]:
                repo_to_portfolio_projects[m["repo_id"]].append(project_name)

        port_id_num = len(portfolio_projects_data) + 1
        port_id = f"PORT-{port_id_num:02d}"

        req_steps, extra_skills = PORTFOLIO_REQUIREMENTS_METADATA[port_id_num]
        latest_phase = get_latest_phase(req_steps)

        # Derived skills: roadmap skill names plus skills_shown
        roadmap_skill_names = [roadmap_steps_data[s]["topic_skill"] for s in req_steps]
        skills_shown_items = [s.strip() for s in skills_shown.split(",") if s.strip()]
        all_skills = roadmap_skill_names + [s for s in skills_shown_items if s not in roadmap_skill_names]
        skills_derived_str = "; ".join(all_skills)

        portfolio_projects_data.append({
            "portfolio_id": port_id,
            "project_name": project_name,
            "why_it_impresses": why_impresses,
            "repos_to_use_short": repos_short_cell,
            "repos_to_use_resolved": " | ".join(resolved_names),
            "repo_ids": " | ".join(resolved_ids),
            "skills_shown": skills_shown,
            "priority": "HIGH",
            "required_roadmap_steps": ", ".join(str(s) for s in req_steps),
            "recommended_after_phase_id": latest_phase,
            "skills_required_derived": skills_derived_str,
            "extra_skills_not_in_roadmap": extra_skills
        })

    # 6. Build File 4: 04_project_repos.csv
    file4_rows = []
    for rp in raw_repos:
        num = rp["num"]
        port_projs = repo_to_portfolio_projects[rp["repo_id"]]
        priority = "HIGH" if port_projs else "NORMAL"
        port_projs_str = " | ".join(port_projs) if port_projs else ""

        req_steps, extra_skills = REPO_REQUIREMENTS_METADATA[num]
        latest_phase = get_latest_phase(req_steps)
        skill_names = [roadmap_steps_data[s]["topic_skill"] for s in req_steps]
        skills_derived_str = "; ".join(skill_names)

        file4_rows.append({
            "repo_id": rp["repo_id"],
            "repository": rp["repository"],
            "github_url": rp["github_url"],
            "category": rp["category"],
            "what_it_offers": rp["what_it_offers"],
            "example_project_ideas": rp["example_project_ideas"],
            "difficulty": rp["difficulty"],
            "best_for": rp["best_for"],
            "tech_stack": rp["tech_stack"],
            "stars_note": rp["stars_note"],
            "priority": priority,
            "portfolio_projects": port_projs_str,
            "skills_required_derived": skills_derived_str,
            "required_roadmap_steps": ", ".join(str(s) for s in req_steps),
            "recommended_after_phase_id": latest_phase,
            "extra_skills_not_in_roadmap": extra_skills,
            "source_note": "Example ideas are the compiler's suggestions"
        })

    # 7. Write CSVs
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    file1_path = os.path.join(OUTPUT_DIR, "01_sde_roadmap_overview.csv")
    file2_path = os.path.join(OUTPUT_DIR, "02_phase_learning_content.csv")
    file3_path = os.path.join(OUTPUT_DIR, "03_topic_checkpoints.csv")
    file4_path = os.path.join(OUTPUT_DIR, "04_project_repos.csv")
    file5_path = os.path.join(OUTPUT_DIR, "05_portfolio_projects.csv")

    f1_cols = [
        "phase_order", "phase_id", "phase_name", "step_range",
        "number_of_topics", "topics_in_order", "phase_objective",
        "learner_outcome", "next_phase_id"
    ]
    with open(file1_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=f1_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(file1_rows)

    f2_cols = [
        "phase_order", "phase_id", "step_number", "topic_skill",
        "what_to_learn", "key_concepts_and_skills_derived", "tier",
        "tier_meaning", "usage_guidance", "purpose", "resource_title",
        "creator", "url", "link_type", "link_verified", "notes",
        "extra_url_in_notes"
    ]
    with open(file2_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=f2_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(file2_rows)

    f3_cols = [
        "phase_order", "phase_id", "step_number", "topic_skill",
        "checkpoint_text", "checkpoint_type", "target_count_min",
        "target_count_max", "passing_criteria_summary"
    ]
    with open(file3_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=f3_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(file3_rows)

    f4_cols = [
        "repo_id", "repository", "github_url", "category",
        "what_it_offers", "example_project_ideas", "difficulty",
        "best_for", "tech_stack", "stars_note", "priority",
        "portfolio_projects", "skills_required_derived",
        "required_roadmap_steps", "recommended_after_phase_id",
        "extra_skills_not_in_roadmap", "source_note"
    ]
    with open(file4_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=f4_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(file4_rows)

    f5_cols = [
        "portfolio_id", "project_name", "why_it_impresses",
        "repos_to_use_short", "repos_to_use_resolved", "repo_ids",
        "skills_shown", "priority", "required_roadmap_steps",
        "recommended_after_phase_id", "skills_required_derived",
        "extra_skills_not_in_roadmap"
    ]
    with open(file5_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=f5_cols, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(portfolio_projects_data)

    # Sync to inner EBuddy-main/output if directory exists
    inner_output_dir = os.path.join("EBuddy-main", "output")
    if os.path.isdir("EBuddy-main"):
        os.makedirs(inner_output_dir, exist_ok=True)
        for fname in ["01_sde_roadmap_overview.csv", "02_phase_learning_content.csv", "03_topic_checkpoints.csv", "04_project_repos.csv", "05_portfolio_projects.csv"]:
            src = os.path.join(OUTPUT_DIR, fname)
            dst = os.path.join(inner_output_dir, fname)
            with open(src, "rb") as sf, open(dst, "wb") as df:
                df.write(sf.read())

    # ----------------------------------------------------
    # 8. Assertions & Verification
    # ----------------------------------------------------
    print("\n" + "=" * 80)
    print("RUNNING VALIDATION ASSERTIONS")
    print("=" * 80)

    # 8.1 Row count assertions
    assert len(file1_rows) == 8, f"Expected 8 rows in 01, got {len(file1_rows)}"
    assert len(file2_rows) == 105, f"Expected 105 rows in 02, got {len(file2_rows)}"
    assert len(file3_rows) == 35, f"Expected 35 rows in 03, got {len(file3_rows)}"
    assert len(file4_rows) == 35, f"Expected 35 rows in 04, got {len(file4_rows)}"
    assert len(portfolio_projects_data) == 8, f"Expected 8 rows in 05, got {len(portfolio_projects_data)}"
    print("[PASS] Row counts verified: 01 (8), 02 (105), 03 (35), 04 (35), 05 (8).")

    # 8.2 Each of 35 steps appears exactly 3 times in 02 and once in 03
    for s in range(1, 36):
        cnt_02 = sum(1 for r in file2_rows if r["step_number"] == s)
        assert cnt_02 == 3, f"Step {s} appears {cnt_02} times in 02 (expected 3)"
        tiers = set(r["tier"] for r in file2_rows if r["step_number"] == s)
        assert tiers == {"A", "B", "C"}, f"Step {s} tiers are {tiers} (expected A, B, C)"
        cnt_03 = sum(1 for r in file3_rows if r["step_number"] == s)
        assert cnt_03 == 1, f"Step {s} appears {cnt_03} times in 03 (expected 1)"
    print("[PASS] Each step (1-35) appears exactly 3 times in 02 (tiers A, B, C) and once in 03.")

    # 8.3 URL checks in 02
    for r in file2_rows:
        u = r["url"]
        assert u != "Open" and u != "", f"URL is invalid: '{u}' in Step {r['step_number']} Tier {r['tier']}"
        assert u.startswith("https://"), f"URL does not start with https://: '{u}'"
    print("[PASS] All 105 URLs in 02 are valid hyperlinks starting with 'https://'.")

    print("\n[Link Type Distribution in 02_phase_learning_content.csv]")
    for lt, count in sorted(link_type_counts.items()):
        print(f"  {lt:<55}: {count} rows")

    # 8.4 Step numbers & phases validation in 04 and 05
    valid_step_nums = set(range(1, 36))
    valid_phase_ids = set(p["phase_id"] for p in PHASES)
    for r in file4_rows:
        steps = [int(s.strip()) for s in r["required_roadmap_steps"].split(",") if s.strip()]
        for s in steps:
            assert s in valid_step_nums, f"Invalid step {s} in repo {r['repo_id']}"
        assert r["recommended_after_phase_id"] in valid_phase_ids, f"Invalid phase in repo {r['repo_id']}"

    for r in portfolio_projects_data:
        steps = [int(s.strip()) for s in r["required_roadmap_steps"].split(",") if s.strip()]
        for s in steps:
            assert s in valid_step_nums, f"Invalid step {s} in portfolio {r['portfolio_id']}"
        assert r["recommended_after_phase_id"] in valid_phase_ids, f"Invalid phase in portfolio {r['portfolio_id']}"
    print("[PASS] All required_roadmap_steps and recommended_after_phase_id in 04 and 05 are valid.")

    # 8.5 HIGH priority repos count & resolution table
    high_repos = [r for r in file4_rows if r["priority"] == "HIGH"]
    print(f"\n[HIGH Priority Repos Count]: {len(high_repos)} repos")
    for hr in high_repos:
        print(f"  {hr['repo_id']}: {hr['repository']:<40} (Used in: {hr['portfolio_projects']})")

    print("\n[Portfolio Path Token Resolution Table]")
    for token, resolved in sorted(token_resolution_table.items()):
        print(f"  '{token}' -> {resolved}")

    # 8.6 Spot-check exact columns against source
    for idx, rp in enumerate(raw_repos):
        r_row = file4_rows[idx]
        assert r_row["repository"] == rp["repository"]
        assert r_row["category"] == rp["category"]
        assert r_row["what_it_offers"] == rp["what_it_offers"]
        assert r_row["example_project_ideas"] == rp["example_project_ideas"]
        assert r_row["difficulty"] == rp["difficulty"]
        assert r_row["best_for"] == rp["best_for"]
        assert r_row["tech_stack"] == rp["tech_stack"]
        assert r_row["stars_note"] == rp["stars_note"]
        assert r_row["github_url"] == rp["github_url"]
    print("[PASS] All exact columns in 04 strictly match source cells.")

    print("\n[DONE] Successfully built all 5 SDE knowledge base CSV files.")

if __name__ == "__main__":
    build()
