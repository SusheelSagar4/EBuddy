import { api } from '../api/client.js';

export function renderOnboarding(container, state, navigate) {
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header">
        <h2>Student Onboarding & Core Ambitions</h2>
        <p class="subtitle">Tell your buddy about your aims, technical aspirations, target timeline, and academic constraints.</p>
      </div>

      <form id="onboard-form" class="form-grid">
        <div class="form-group">
          <label for="student-id">Student Roll / ID *</label>
          <input type="text" id="student-id" value="${state.studentId || '24EE01001'}" required />
          <span class="field-hint">Institute roll number or handle</span>
        </div>

        <div class="form-group">
          <label for="full-name">Full Name *</label>
          <input type="text" id="full-name" value="Shriya Panda" required />
        </div>

        <div class="form-group">
          <label for="programme">Branch / Programme *</label>
          <select id="programme">
            <option value="BTECH_EE" selected>B.Tech Electrical Engineering (EE)</option>
            <option value="BTECH_MM">B.Tech Metallurgical & Materials Engineering (MME)</option>
          </select>
        </div>

        <div class="form-group">
          <label for="current-sem">Current Academic Semester *</label>
          <select id="current-sem">
            <option value="1">Semester I</option>
            <option value="2">Semester II</option>
            <option value="3" selected>Semester III</option>
            <option value="4">Semester IV</option>
            <option value="5">Semester V</option>
            <option value="6">Semester VI</option>
            <option value="7">Semester VII</option>
            <option value="8">Semester VIII</option>
          </select>
        </div>

        <div class="form-group full-width">
          <label for="aims-aspirations">Aims and Aspirations *</label>
          <textarea id="aims-aspirations" rows="2" placeholder="e.g. Aiming for high-impact core engineering role at top power utilities, grid operations, or primary metallurgical research (Tata Steel, SAIL, DRDO)..." required>Lead core engineering initiatives and secure high-impact technical placement in core industry.</textarea>
          <span class="field-hint">What do you want to accomplish as a core engineer?</span>
        </div>

        <div class="form-group">
          <label for="target-goal">Core Technical Goal *</label>
          <select id="target-goal">
            <!-- Dynamically populated based on programme -->
          </select>
          <span class="field-hint">Verified IIT Bhubaneswar curriculum competency tree</span>
        </div>

        <div class="form-group">
          <label for="target-timeline">Target Achievement Timeline *</label>
          <select id="target-timeline">
            <option value="By Semester 6 (Pre-placement & Internships)" selected>By Semester 6 (Pre-placement & Internships)</option>
            <option value="By Semester 7 (Campus Placement Season)">By Semester 7 (Campus Placement Season)</option>
            <option value="By Semester 8 (Graduation & Industry Ready)">By Semester 8 (Graduation & Industry Ready)</option>
            <option value="Within 1 Year (Intensive Acceleration)">Within 1 Year (Intensive Acceleration)</option>
          </select>
        </div>

        <div class="form-group">
          <label for="field-of-interest">Field of Interest *</label>
          <select id="field-of-interest">
            <option value="FIELD_SDE" selected>Software Development Engineering (SDE)</option>
            <option value="FIELD_AIML">AI & Machine Learning (AI/ML)</option>
            <option value="FIELD_DA">Data Analytics (DA)</option>
            <option value="FIELD_GATE_MTECH">Higher Studies (GATE → M.Tech / MS / PSU)</option>
            <option value="FIELD_CAT_MBA">Core to MBA (CAT Fresher / Executive)</option>
            <option value="FIELD_UPSC">Civil Services (UPSC CSE / ESE)</option>
            <option value="FIELD_CORE_RESEARCH">Core Engineering Research Track</option>
            <option value="FIELD_CORE_INDUSTRY">Core Engineering Industry & PSUs</option>
            <option value="FIELD_STARTUP">Student Entrepreneurship & Startup</option>
          </select>
          <span class="field-hint">Your primary career & academic focus track</span>
        </div>

        <div class="form-group">
          <label for="cgpa">Current Cumulative CGPA</label>
          <input type="number" id="cgpa" step="0.01" min="0" max="10" value="8.40" />
        </div>

        <div class="form-group">
          <label for="study-hours">Weekly Prep & Study Time Available (Hours)</label>
          <input type="number" id="study-hours" min="5" max="50" value="18" />
          <span class="field-hint">Hours per week outside class timetable</span>
        </div>

        <div class="form-group full-width">
          <label for="completed-courses">Completed Courses (Course codes, comma-separated)</label>
          <input type="text" id="completed-courses" value="MA1L001, PH1L001, EE1L001, CS1L001" />
          <span class="field-hint">Courses completed prior to planning horizon</span>
        </div>

        <div class="form-actions full-width">
          <button type="submit" class="btn btn-primary">Save Profile & Begin Technical Skills Diagnostic Test →</button>
        </div>
      </form>
    </div>
  `;

  const progSelect = document.getElementById('programme');
  const goalSelect = document.getElementById('target-goal');
  const compInput = document.getElementById('completed-courses');

  function updateGoalOptions() {
    const p = progSelect.value;
    if (p === 'BTECH_EE') {
      goalSelect.innerHTML = `
        <option value="GOAL_EE_CORE_POWER" selected>Power Systems, Smart Grid & Renewable Energy (EE Core)</option>
        <option value="GOAL_EE_CORE_VLSI">Core VLSI, Semiconductor & Embedded Hardware (EE Core)</option>
      `;
      if (!compInput.value.includes('ML')) {
        compInput.value = 'MA1L001, PH1L001, EE1L001, CS1L001';
      }
    } else {
      goalSelect.innerHTML = `
        <option value="GOAL_MM_ADVANCED_MATERIALS" selected>Advanced Materials R&D & Physical Metallurgy (MME Core)</option>
        <option value="GOAL_MM_PROCESS_ENGINEER">Process Metallurgist - Iron & Steelmaking / Primary Metals (MME Core)</option>
      `;
      compInput.value = 'MA1L001, PH1L001, CY1L001, ME1L001';
    }
  }

  progSelect.addEventListener('change', updateGoalOptions);
  updateGoalOptions();

  document.getElementById('onboard-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const completedStr = document.getElementById('completed-courses').value;
    const completedList = completedStr.split(',').map(s => s.trim()).filter(Boolean);

    const payload = {
      student_id: document.getElementById('student-id').value,
      name: document.getElementById('full-name').value,
      full_name: document.getElementById('full-name').value,
      programme_id: document.getElementById('programme').value,
      current_semester: parseInt(document.getElementById('current-sem').value, 10),
      cgpa: parseFloat(document.getElementById('cgpa').value),
      goal_id: document.getElementById('target-goal').value,
      target_goal_id: document.getElementById('target-goal').value,
      aims_and_aspirations: document.getElementById('aims-aspirations').value,
      target_timeline: document.getElementById('target-timeline').value,
      field_of_interest: document.getElementById('field-of-interest').value,
      completed_course_ids: completedList,
      constraints: [
        { type: "weekly_study_hours", value: parseInt(document.getElementById('study-hours').value, 10) },
        { type: "max_credits_per_sem", value: 25 }
      ],
      preferences: [
        { type: "learning_style", value: "hands_on_problem_solving" },
        { type: "pace", value: "steady" }
      ]
    };

    try {
      const res = await api.onboard(payload);
      state.studentId = payload.student_id;
      state.profile = res.student || payload;
      localStorage.setItem('ebuddy_student_id', payload.student_id);

      if (res.brief_roadmap) {
        state.briefRoadmap = res.brief_roadmap;
        const b = res.brief_roadmap;
        container.innerHTML = `
          <div class="screen-card">
            <div class="screen-header">
              <h2>Career Field Selected: ${b.field_name}</h2>
              <p class="subtitle">${b.description || 'Structured academic roadmap grounded in verified IIT Bhubaneswar curriculum and industry milestones.'}</p>
            </div>
            <div class="metric-row" style="display:flex; gap:1.5rem; margin-bottom:1.5rem;">
              <div class="metric-box"><strong>Total Phases:</strong> ${b.total_phases}</div>
              <div class="metric-box"><strong>Est. Effort:</strong> ${b.total_estimated_hours} Hours</div>
            </div>
            <h3>Curriculum Phases</h3>
            <div class="phases-list" style="margin-bottom:2rem;">
              ${(b.phases || []).map(p => `
                <div class="card" style="margin-bottom:0.75rem; padding:1rem; border:1px solid #e2e8f0; border-radius:6px;">
                  <h4 style="margin:0 0 0.25rem 0;">Phase ${p.phase_order}: ${p.phase_name}</h4>
                  <p style="margin:0; font-size:0.9rem; color:#4a5568;">${p.phase_objective || ''} (Est. ${p.estimated_hours}h)</p>
                </div>
              `).join('')}
            </div>
            <div class="form-actions" style="display:flex; gap:1rem;">
              <button id="btn-pk-test" class="btn btn-primary">Take Prior-Knowledge Test (Skip Topics) →</button>
              <button id="btn-view-plan" class="btn btn-secondary">Go Directly to Weekly Schedule →</button>
            </div>
          </div>
        `;
        document.getElementById('btn-pk-test').addEventListener('click', () => navigate('#diagnostic'));
        document.getElementById('btn-view-plan').addEventListener('click', () => navigate('#plan'));
        return;
      }
      navigate('#diagnostic');
    } catch (err) {
      alert(`Onboarding failed: ${err.message}`);
    }
  });
}
