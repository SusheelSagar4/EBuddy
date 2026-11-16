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
          <h2>Daily Learning & Resources (Agent 2)</h2>
          <p class="subtitle">Study core modules via verified NPTEL playlists, then take check-in tasks to adaptively guide your plan.</p>
        </div>
        <button class="btn btn-outline" onclick="window.location.hash='#plan'">← View Academic Roadmap</button>
      </div>

      <div id="learn-loading" class="loading-state">Loading today's curated materials from Knowledge Base...</div>
      <div id="learn-content" style="display: none;"></div>
    </div>
  `;

  loadLearnData();

  async function loadLearnData() {
    const loading = document.getElementById('learn-loading');
    const content = document.getElementById('learn-content');

    try {
      const [todayData, learnData] = await Promise.all([
        api.getLearnToday(state.studentId).catch(() => null),
        api.getLearn(state.studentId).catch(() => null)
      ]);

      loading.style.display = 'none';
      content.style.display = 'block';

      const resources = todayData?.resources || learnData?.video_resources || [];
      const exercises = todayData?.exercises || learnData?.practice_exercises || [];

      content.innerHTML = `
        <div class="learn-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px;">
          <!-- Left Column: Open Educational Resources -->
          <div class="col-resources">
            <h3 style="margin-bottom: 16px; font-size: 17px; display: flex; align-items: center; gap: 8px;">
              <span>📺</span> Verified NPTEL & SWAYAM Video Playlists
            </h3>
            <p style="font-size: 0.9em; color: #666; margin-bottom: 16px;">
              ${todayData?.disclaimer || 'All links are sourced from official institutional records (zero hallucination).'}
            </p>
            ${resources.length === 0 ? `<p class="text-muted">No external resources scheduled for today's modules.</p>` : `
              <div class="resources-list" style="display: flex; flex-direction: column; gap: 12px;">
                ${resources.map(res => `
                  <div class="resource-card" style="border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 14px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                      <strong style="font-size: 14px; color: var(--text-primary);">${res.title}</strong>
                      <span class="badge ${res.coverage_status === 'Playlist found' ? 'badge-success' : 'badge-neutral'}" style="font-size: 11px;">
                        ${res.coverage_status || 'Verified'}
                      </span>
                    </div>
                    <p class="text-muted" style="font-size: 12.5px; margin: 6px 0 10px 0;">
                      Provider: <strong>${res.provider || res.platform || 'NPTEL'}</strong> • Course: <strong>${res.display_code || res.course_title || 'Core Requirement'}</strong>
                    </p>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                      <a href="${res.url || '#'}" target="_blank" rel="noopener noreferrer" class="btn btn-outline btn-sm">
                        Open Lecture Playlist ↗
                      </a>
                      <span class="badge badge-info">${res.difficulty || 'Intermediate'}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <!-- Right Column: Micro-Tasks & Check-in Quizzes -->
          <div class="col-tasks">
            <h3 style="margin-bottom: 16px; font-size: 17px; display: flex; align-items: center; gap: 8px;">
              <span>✍️</span> Continuous Skill Tasks & Quizzes
            </h3>
            <p class="text-muted" style="font-size:0.9em; margin-bottom: 12px;">
              Practice submissions are evaluated by <strong>Agent 3 (Assessment Agent)</strong>. Insufficient scores trigger a remediation proposal.
            </p>
            ${exercises.length > 0 ? `
              <div class="exercises-list" style="display: flex; flex-direction: column; gap: 16px;">
                ${exercises.slice(0, 4).map((ex, idx) => `
                  <div class="exercise-card" style="border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px; padding: 16px; background: white;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                      <span class="badge badge-info" style="font-size: 11px;">Task ${idx + 1}</span>
                      <span class="badge badge-neutral" style="font-size: 11px;">${(ex.skill_id || '').replace('SKILL_', '')}</span>
                    </div>
                    <p style="font-size: 14px; font-weight: 500; margin-bottom: 12px;">${ex.prompt || ex.question_text || 'Demonstrate mastery in core concepts.'}</p>
                    <form class="micro-task-form" data-ex-id="${ex.exercise_id}" data-skill-id="${ex.skill_id}">
                      ${ex.options && ex.options.length > 0 ? `
                        <div style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;">
                          ${ex.options.map((opt, oIdx) => `
                            <label style="display: flex; align-items: center; gap: 8px; font-size: 13.5px; cursor: pointer;">
                              <input type="radio" name="ans_${ex.exercise_id}" value="${opt}" ${oIdx === 0 ? 'checked' : ''} />
                              <span>${opt}</span>
                            </label>
                          `).join('')}
                        </div>
                      ` : `
                        <input type="text" name="ans_${ex.exercise_id}" class="form-control" placeholder="Enter your response..." style="margin-bottom:12px; width:100%;" required />
                      `}
                      <button type="submit" class="btn btn-primary" style="font-size: 12.5px; padding: 6px 14px;">Complete Task & Adapt Plan →</button>
                    </form>
                    <div class="feedback-area" id="fb_${ex.exercise_id}" style="display: none; margin-top: 12px; padding: 10px; border-radius: 6px; font-size: 13px;"></div>
                  </div>
                `).join('')}
              </div>
            ` : `
              <div style="background:#fcfcfc; border:1px solid #e5e5e5; border-radius:6px; padding:16px;">
                <strong>Skill Focus: Active Practice</strong>
                <p style="font-size:0.85em; color:#555; margin:6px 0 12px 0;">Complete diagnostic and check-in tasks to demonstrate mastery.</p>
                <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#diagnostic'">Take Practice Diagnostic</button>
              </div>
            `}
          </div>
        </div>
      `;

      // Attach task submission listeners
      document.querySelectorAll('.micro-task-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const exId = form.getAttribute('data-ex-id');
          const skillId = form.getAttribute('data-skill-id');
          const radioSel = form.querySelector(`input[name="ans_${exId}"]:checked`);
          const textInput = form.querySelector(`input[name="ans_${exId}"][type="text"]`);
          const answerVal = radioSel ? radioSel.value : (textInput ? textInput.value : '');
          if (!answerVal) return;

          const fbEl = document.getElementById(`fb_${exId}`);
          try {
            const res = await api.submitExercise(state.studentId, {
              skill_id: skillId,
              exercise_id: exId,
              student_answer: answerVal
            });

            fbEl.style.display = 'block';
            if (res.passed || res.status === 'success') {
              fbEl.style.background = '#dcfce7';
              fbEl.style.color = '#15803d';
              fbEl.innerHTML = `<strong>✓ Topic Mastered!</strong> ${res.feedback || 'Response verified.'}<br/><small>Roadmap updated: ${res.diff_summary || 'Accelerated forward.'}</small>`;
            } else {
              fbEl.style.background = '#fee2e2';
              fbEl.style.color = '#b91c1c';
              fbEl.innerHTML = `<strong>✕ Remediation Added!</strong> ${res.feedback || 'Foundational gap identified.'}<br/><small>Roadmap updated: ${res.diff_summary || 'Review drills inserted.'}</small>`;
            }
          } catch (err) {
            alert(`Task evaluation failed: ${err.message}`);
          }
        });
      });
    } catch (err) {
      loading.innerHTML = `<p class="text-danger">Failed to load learning resources: ${err.message}</p>`;
    }
  }
}
