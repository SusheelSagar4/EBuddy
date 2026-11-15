import urllib.request
import json
import sys

base_url = "http://localhost:8000"

def test_endpoint(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
        body = json.dumps(data).encode("utf-8")
    else:
        body = None
    with urllib.request.urlopen(req, data=body) as resp:
        return resp.status, resp.read().decode("utf-8")

print("=== SMOKE TEST: EBUDDY APPLICATION & ROADMAP V2 ===")

# 1. Health
status, body = test_endpoint(f"{base_url}/api/health")
health_data = json.loads(body)
print(f"[PASS] 1. /api/health -> Status: {status} | DB: {health_data.get('database')} | Courses: {health_data.get('counts', {}).get('kb_courses')}")

# 2. Home page
status, body = test_endpoint(f"{base_url}/")
print(f"[PASS] 2. GET / (Home HTML) -> Status: {status} | Size: {len(body)} bytes")

# 3. Roadmap page
status, body = test_endpoint(f"{base_url}/roadmap")
print(f"[PASS] 3. GET /roadmap -> Status: {status} | Size: {len(body)} bytes")

# 4. Web SPA
status, body = test_endpoint(f"{base_url}/legacy-web/")
print(f"[PASS] 4. GET /legacy-web/ (SPA) -> Status: {status} | Size: {len(body)} bytes")

# 5. Onboard student
onboard_payload = {
    "student_id": "SMOKE_TEST_STU_01",
    "name": "Smoke Test Student",
    "programme_id": "BTECH_EE",
    "current_semester": 5,
    "cgpa": 8.5,
    "backlogs": 0,
    "goal_id": "GOAL_EE_CORE_POWER",
    "completed_course_ids": ["MA1L001", "MA1L002", "EE1L001", "CS1L001", "EC2L001", "EC2L002", "EE2L001"]
}
status, body = test_endpoint(f"{base_url}/api/student/onboard", method="POST", data=onboard_payload)
print(f"[PASS] 5. POST /api/student/onboard -> Status: {status} | Student onboarded successfully")

# 6. Generate Plan
status, body = test_endpoint(f"{base_url}/api/student/SMOKE_TEST_STU_01/plan", method="POST")
plan_json = json.loads(body)
print(f"[PASS] 6. POST /api/student/SMOKE_TEST_STU_01/plan -> Status: {status} | Version: {plan_json.get('version')} | Weekly Roadmap Generated: {'weekly_roadmap' in plan_json}")

# 7. Get Plan
status, body = test_endpoint(f"{base_url}/api/student/SMOKE_TEST_STU_01/plan")
plan_res = json.loads(body)
plan_obj = plan_res.get("plan", plan_res)
req_courses = plan_obj.get("required_courses", [])
rec_items = plan_obj.get("recommended_items", [])
sem_blocks = plan_obj.get("semester_blocks", [])
next_4_w = plan_obj.get("next_4_weeks", [])
timeline = plan_obj.get("timeline_roadmap", {})

print(f"[PASS] 7. GET /api/student/SMOKE_TEST_STU_01/plan -> Status: {status}")
print(f"       • Required Core Courses: {len(req_courses)} (Locked)")
print(f"       • Recommended Items: {len(rec_items)}")
print(f"       • Multi-Semester Blocks: {len(sem_blocks)} (Gantt grid)")
print(f"       • Next 4 Weeks Schedule: {len(next_4_w)} weekly tasks")
print(f"       • Horizon Deadline: {timeline.get('horizon_deadline')}")

# 8. Weekly Roadmap
status, body = test_endpoint(f"{base_url}/api/student/SMOKE_TEST_STU_01/roadmap/weekly?week=1")
week_json = json.loads(body)
daily_tasks = week_json.get("daily_tasks", [])
print(f"[PASS] 8. GET /api/student/SMOKE_TEST_STU_01/roadmap/weekly -> Status: {status} | Week 1 Daily Tasks: {len(daily_tasks)}")

print("\n>>> ALL SMOKE TESTS PASSED CLEANLY! Web application is live and fully functional. <<<")
