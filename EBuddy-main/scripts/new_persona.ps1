param (
    [Parameter(Mandatory=$true, Position=0)]
    [string]$PersonaId
)

$targetDir = "app\personas\$PersonaId"
$seedDir = "data\seed\personas\$PersonaId"

if (Test-Path $targetDir) {
    Write-Error "Persona folder '$targetDir' already exists!"
    exit 1
}

New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
New-Item -ItemType Directory -Force -Path "$targetDir\prompts" | Out-Null
New-Item -ItemType Directory -Force -Path $seedDir | Out-Null

function Write-Utf8NoBom {
    param($FilePath, $Content)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($FilePath, $Content, $utf8NoBom)
}

# 1. persona.yaml
$personaYaml = @"
persona_id: "$PersonaId"
goal_id: "GOAL_$($PersonaId.ToUpper())"
description: "TODO: Describe the student archetype and career trajectory."
applicable_programmes:
  - "BTECH_EE"
target_semester_range: [3, 8]
eligibility_notes: "TODO: Minimum CGPA or prerequisite requirements."
planner_weights:
  cgpa_protection: 0.7
  skill_acceleration: 0.8
  workload_smoothing: 0.6
status: "draft_for_review"
"@
Write-Utf8NoBom "$targetDir\persona.yaml" $personaYaml

# 2. requirements.yaml
$reqYaml = @"
- skill_id: "SKILL_CIRCUIT_ANALYSIS"
  required_level: 80.0
  importance: 1.0
- skill_id: "SKILL_POWER_ELECTRONICS"
  required_level: 75.0
  importance: 0.9
"@
Write-Utf8NoBom "$targetDir\requirements.yaml" $reqYaml

# 3. mastery.yaml
$masteryYaml = @"
criteria_id: "MASTERY_$($PersonaId.ToUpper())"
goal_id: "GOAL_$($PersonaId.ToUpper())"
criteria:
  min_skill_level: 75.0
  required_project_milestones: 1
  required_timed_assessments: 2
  min_diagnostic_score: 70.0
"@
Write-Utf8NoBom "$targetDir\mastery.yaml" $masteryYaml

# 4. milestones.yaml
$milestonesYaml = @"
- semester_target: 5
  title: "Core Domain Mini-Project"
  description: "Complete independent design and simulation project."
- semester_target: 7
  title: "Industry Internship / Capstone Selection"
  description: "Secure domain-relevant summer internship."
"@
Write-Utf8NoBom "$targetDir\milestones.yaml" $milestonesYaml

# 5. diagnostic.yaml
$diagYaml = @"
blueprint:
  target_skills:
    - "SKILL_CIRCUIT_ANALYSIS"
    - "SKILL_POWER_ELECTRONICS"
  item_counts: 5
  difficulty_range: [40.0, 85.0]
"@
Write-Utf8NoBom "$targetDir\diagnostic.yaml" $diagYaml

# 6. policy.py
$policyPy = @"
from app.personas.policy import PersonaPolicy

class CustomPersonaPolicy(PersonaPolicy):
    """Custom policy hooks for $PersonaId."""
    pass
"@
Write-Utf8NoBom "$targetDir\policy.py" $policyPy

# 7. README.md
$readmeMd = @"
# Persona Specification: $PersonaId

## 1. Who This Persona Is
TODO: Characterize this student persona, background, motivations, and pain points.

## 2. Institutional Survey Evidence
TODO: Reference findings from student surveys and batch data.

## 3. Curricular Trade-Offs & Decisions
TODO: Document academic trade-offs between core CGPA protection vs elective exploration.

## 4. Known Gaps
TODO: Any pending course syllabi or missing elective offerings.
"@
Write-Utf8NoBom "$targetDir\README.md" $readmeMd

Write-Host "Scaffolded persona plugin successfully at $targetDir"
Write-Host "Created persona seed directory at $seedDir"

