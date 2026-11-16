import { api } from '../api/client.js';

export function renderOnboarding(container, state, navigate) {
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header">
        <h2>Student Onboarding</h2>
        <p class="subtitle">Set up your profile, academic constraints, and target career/learning goal.</p>
      </div>

      <form id="onboard-form" class="form-grid">
        <div class="form-group">
          <label for="student-id">Student ID</label>
          <input type="text" id="student-id" value="${state.studentId || 'STU_EE_2026_01'}" required />
          <span class="field-hint">Unique institute roll number or test handle</span>
        </div>

        <div class="form-group">
          <label for="full-name">Full Name</label>
          <input type="text" id="full-name" value="Aarav Sharma" required />
        </div>

        <div class="form-group">
          <label for="programme">Programme</label>
          <select id="programme">
            <option value="BTECH_EE" selected>B.Tech Electrical Engineering (EE)</option>
            <option value="BTECH_MM">B.Tech Metallurgical & Materials Engineering (MME)</option>
          </select>
        </div>

        <div class="form-group">
          <label for="current-sem">Current Semester</label>
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

        <div class="form-group">
          <label for="cgpa">Current CGPA</label>
          <input type="number" id="cgpa" step="0.01" min="0" max="10" value="8.45" />
        </div>

        <div class="form-group">
          <label for="target-goal">Primary Career / Academic Goal</label>
          <select id="target-goal">
            <option value="GOAL_CORE_EE" selected>Power Systems & Core Electrical Engineering</option>
            <option value="GOAL_GATE_EE">GATE Electrical Engineering</option>
            <option value="GOAL_SOFTWARE">Software / Data Engineering Career</option>
            <option value="GOAL_CORE_MME">Physical & Extractive Metallurgy (MME)</option>
          </select>
          <span class="field-hint">Links to verified curriculum competency trees</span>
        </div>

        <div class="form-group">
          <label for="max-credits">Max Credits Per Semester</label>
          <input type="number" id="max-credits" min="15" max="30" value="25" />
          <span class="field-hint">IIT BBS academic ceiling (default 25)</span>
        </div>

        <div class="form-group">
          <label for="study-hours">Weekly Study Hours Available</label>
          <input type="number" id="study-hours" min="5" max="50" value="20" />
        </div>

        <div class="form-group full-width">
          <label for="completed-courses">Completed Course IDs (comma-separated)</label>
          <input type="text" id="completed-courses" value="MA1L001, PH1L001, EE1L001, CS1L001" />
          <span class="field-hint">Courses completed prior to planning horizon</span>
        </div>

        <div class="form-actions full-width">
          <button type="submit" class="btn btn-primary">Save Profile & Begin Adaptive Diagnostic</button>
        </div>
      </form>
    </div>
  `;

  document.getElementById('onboard-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const completedStr = document.getElementById('completed-courses').value;
    const completedList = completedStr.split(',').map(s => s.trim()).filter(Boolean);

    const payload = {
      student_id: document.getElementById('student-id').value,
      full_name: document.getElementById('full-name').value,
      programme_id: document.getElementById('programme').value,
      current_semester: parseInt(document.getElementById('current-sem').value, 10),
      cgpa: parseFloat(document.getElementById('cgpa').value),
      target_goal_id: document.getElementById('target-goal').value,
      completed_course_ids: completedList,
      constraints: {
        max_credits_per_sem: parseInt(document.getElementById('max-credits').value, 10),
        weekly_study_hours: parseInt(document.getElementById('study-hours').value, 10)
      },
      preferences: {
        preferred_learning_style: "visual_hands_on",
        target_pace: "steady"
      }
    };

    try {
      const res = await api.onboard(payload);
      state.studentId = payload.student_id;
      state.profile = res.profile;
      localStorage.setItem('ebuddy_student_id', payload.student_id);
      navigate('#diagnostic');
    } catch (err) {
      alert(`Onboarding failed: ${err.message}`);
    }
  });
}

