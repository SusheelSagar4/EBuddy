import { api } from '../api/client.js';

export function renderPlan(container, state, navigate) {
  if (!state.studentId) {
    container.innerHTML = `
      <div class="screen-card alert-warning">
        <p>No active student profile found. Please complete onboarding first.</p>
        <button class="btn btn-primary" onclick="window.location.hash='#onboard'">Go to Onboarding</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between">
        <div>
          <h2>Adaptive Academic Plan</h2>
          <p class="subtitle">Semestral course schedule tailored to your goal and validated against IIT BBS curriculum regulations.</p>
        </div>
        <div>
          <button class="btn btn-outline" id="btn-refresh-plan">Re-generate / Validate</button>
        </div>
      </div>

      <div id="plan-loading" class="loading-state">Generating verified academic plan...</div>
      <div id="plan-content" style="display: none;"></div>
    </div>
  `;

  document.getElementById('btn-refresh-plan').addEventListener('click', loadPlan);
  loadPlan();

  async function loadPlan() {
    const loading = document.getElementById('plan-loading');
    const content = document.getElementById('plan-content');
    loading.style.display = 'block';
    content.style.display = 'none';

    try {
      const data = await api.getPlan(state.studentId);
      loading.style.display = 'none';
      content.style.display = 'block';

      const plan = data.plan;
      const validation = data.validation || { passed: true, checks: [] };

      // Render validation status bar
      const statusBadge = validation.passed 
        ? `<span class="badge badge-success">✓ ALL REGULATORY CHECKS PASSED</span>`
        : `<span class="badge badge-error">✕ VALIDATION FAILED (${validation.violations?.length || 0} issues)</span>`;

      // Group plan items by semester
      const semGroups = {};
      (plan.items || []).forEach(item => {
        const sem = item.semester || 1;
        if (!semGroups[sem]) semGroups[sem] = [];
        semGroups[sem].push(item);
      });

      content.innerHTML = `
        <div class="plan-summary-bar">
          <div class="summary-metric">
            <span class="metric-label">Goal ID</span>
            <span class="metric-val">${plan.goal_id || 'N/A'}</span>
          </div>
          <div class="summary-metric">
            <span class="metric-label">Plan Version</span>
            <span class="metric-val">v${plan.version || 1}</span>
          </div>
          <div class="summary-metric">
            <span class="metric-label">Planned Credits</span>
            <span class="metric-val">${plan.total_credits || 0} cr</span>
          </div>
          <div class="summary-metric">
            <span class="metric-label">Status</span>
            <span class="metric-val">${statusBadge}</span>
          </div>
        </div>

        ${!validation.passed ? `
          <div class="alert-box alert-error">
            <strong>Rule Violations Detected:</strong>
            <ul>
              ${(validation.violations || []).map(v => `<li>${v}</li>`).join('')}
            </ul>
          </div>
        ` : ''}

        <div class="schedule-container">
          ${Object.keys(semGroups).sort((a,b) => a-b).map(sem => {
            const items = semGroups[sem];
            const semCredits = items.reduce((sum, it) => sum + (it.credits || 0), 0);
            return `
              <div class="semester-block">
                <div class="semester-header">
                  <h3>Semester ${sem}</h3>
                  <span class="badge badge-neutral">${semCredits} Credits</span>
                </div>
                <div class="course-cards-list">
                  ${items.map(item => `
                    <div class="course-card ${item.code_conflict ? 'has-conflict' : ''}">
                      <div class="course-card-top">
                        <div class="course-identity">
                          <span class="course-code">${item.display_code || item.course_id}</span>
                          <span class="course-name">${item.title || item.course_id}</span>
                        </div>
                        <div class="course-badges">
                          ${item.code_conflict ? `<span class="badge badge-warning" title="Clashing code in catalog">⚠️ Code Conflict</span>` : ''}
                          <span class="badge ${item.status === 'verified' ? 'badge-success' : 'badge-warning'}">
                            ${item.status || 'verified'}
                          </span>
                          <span class="badge badge-info">${item.credits || 3} cr</span>
                        </div>
                      </div>

                      ${item.reason ? `
                        <div class="course-why">
                          <strong>Why this?</strong> ${item.reason}
                        </div>
                      ` : ''}

                      ${item.target_skills && item.target_skills.length ? `
                        <div class="course-skills">
                          <span class="skills-label">Develops:</span>
                          ${item.target_skills.map(sk => `<span class="tag-skill">${sk}</span>`).join(' ')}
                        </div>
                      ` : ''}
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } catch (err) {
      loading.innerHTML = `<p class="text-error">Failed to load plan: ${err.message}</p>`;
    }
  }
}

