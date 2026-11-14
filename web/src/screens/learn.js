import { api } from '../api/client.js';

export function renderLearn(container, state, navigate) {
  if (!state.studentId) {
    container.innerHTML = `
      <div class="screen-card alert-warning">
        <p>Please complete onboarding first.</p>
        <button class="btn btn-primary" onclick="window.location.hash='#onboard'">Go to Onboarding</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between" style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <h2>Active Learning, Open Courseware & Skill Tasks</h2>
          <p class="subtitle">Study core modules via verified NPTEL playlists, then take check-in tasks to adaptively guide your plan.</p>
        </div>
        <button class="btn btn-outline" onclick="window.location.hash='#plan'">← View Academic Roadmap</button>
      </div>

      <div id="learn-loading" class="loading-state">Loading active modules & practice exercises...</div>
      <div id="learn-content" style="display: none;"></div>
    </div>
  `;

  loadLearnData();

  async function loadLearnData() {
    const loading = document.getElementById('learn-loading');
    const content = document.getElementById('learn-content');

    try {
      const data = await api.getLearn(state.studentId);
      loading.style.display = 'none';
      content.style.display = 'block';

      const resources = data.resources || [];
      const exercises = data.exercises || [];

      content.innerHTML = `
        <div class="learn-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
          <!-- Left Column: Open Educational Resources -->
          <div class="col-resources">
            <h3 style="margin-bottom: 16px; font-size: 17px; display: flex; align-items: center; gap: 8px;">
              <span>📺</span> Verified NPTEL & SWAYAM Video Playlists
            </h3>
            <div class="resources-list" style="display: flex; flex-direction: column; gap: 12px;">
              ${resources.map(res => `
                <div class="resource-card" style="border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; background: white;">
                  <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <strong style="font-size: 14px; color: var(--text-primary);">${res.title}</strong>
                    <span class="badge badge-success" style="font-size: 11px;">${res.coverage_status || 'Verified'}</span>
                  </div>
                  <p class="text-muted" style="font-size: 12.5px; margin: 6px 0 10px 0;">Provider: ${res.platform || 'NPTEL'} • Instructor: IIT Faculty</p>
                  <a href="${res.url || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-outline" style="font-size: 12px; padding: 4px 10px; display: inline-flex; align-items: center; gap: 4px;">
                    Open Video Lectures ↗
                  </a>
                </div>
              `).join('')}
            </div>
          </div>

          <!-- Right Column: Micro-Tasks & Check-in Quizzes -->
          <div class="col-tasks">
            <h3 style="margin-bottom: 16px; font-size: 17px; display: flex; align-items: center; gap: 8px;">
              <span>✍️</span> Continuous Skill Tasks & Quizzes
            </h3>
            <div class="exercises-list" style="display: flex; flex-direction: column; gap: 16px;">
              ${exercises.slice(0, 4).map((ex, idx) => `
                <div class="exercise-card" style="border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 16px; background: white;">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span class="badge badge-info" style="font-size: 11px;">Task ${idx + 1}</span>
                    <span class="badge badge-neutral" style="font-size: 11px;">${ex.skill_id.replace('SKILL_', '')}</span>
                  </div>
                  <p style="font-size: 14px; font-weight: 500; margin-bottom: 12px;">${ex.prompt}</p>
                  <form class="micro-task-form" data-ex-id="${ex.exercise_id}" data-skill-id="${ex.skill_id}">
                    <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                      ${(ex.options || []).map((opt, oIdx) => `
                        <label style="display: flex; align-items: center; gap: 8px; font-size: 13.5px; cursor: pointer;">
                          <input type="radio" name="ans_${ex.exercise_id}" value="${opt}" ${oIdx === 0 ? 'checked' : ''} />
                          <span>${opt}</span>
                        </label>
                      `).join('')}
                    </div>
                    <button type="submit" class="btn btn-primary" style="font-size: 12.5px; padding: 6px 14px;">Complete Task & Adapt Plan →</button>
                  </form>
                  <div class="feedback-area" id="fb_${ex.exercise_id}" style="display: none; margin-top: 12px; padding: 10px; border-radius: 6px; font-size: 13px;"></div>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;

      // Attach task submission listeners
      document.querySelectorAll('.micro-task-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const exId = form.getAttribute('data-ex-id');
          const skillId = form.getAttribute('data-skill-id');
          const sel = form.querySelector(`input[name="ans_${exId}"]:checked`);
          if (!sel) return;

          const fbEl = document.getElementById(`fb_${exId}`);
          try {
            const res = await api.submitExercise(state.studentId, {
              skill_id: skillId,
              exercise_id: exId,
              student_answer: sel.value
            });

            fbEl.style.display = 'block';
            if (res.passed) {
              fbEl.style.background = '#dcfce7';
              fbEl.style.color = '#15803d';
              fbEl.innerHTML = `<strong>✓ Topic Mastered!</strong> ${res.feedback}<br/><small>Roadmap updated: ${res.diff_summary || 'Accelerated forward.'}</small>`;
            } else {
              fbEl.style.background = '#fee2e2';
              fbEl.style.color = '#b91c1c';
              fbEl.innerHTML = `<strong>✕ Remediation Added!</strong> ${res.feedback}<br/><small>Roadmap updated: ${res.diff_summary || 'Review drills inserted.'}</small>`;
            }
          } catch (err) {
            alert(`Task evaluation failed: ${err.message}`);
          }
        });
      });
    } catch (err) {
      loading.innerHTML = `<p class="text-error">Error loading active learning data: ${err.message}</p>`;
    }
  }
}
