import { api } from '../api/client.js';

export function renderProgress(container, state, navigate) {
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
      <div class="screen-header">
        <h2>Goal Mastery & Competency Matrix</h2>
        <p class="subtitle">Evidence-backed evaluation: "Completed Coursework" vs "Demonstrated Proficiency".</p>
      </div>

      <div id="prog-loading" class="loading-state">Evaluating competency evidence ledger...</div>
      <div id="prog-content" style="display: none;"></div>
    </div>
  `;

  loadProgress();

  async function loadProgress() {
    const loading = document.getElementById('prog-loading');
    const content = document.getElementById('prog-content');

    try {
      const data = await api.getProgress(state.studentId);
      loading.style.display = 'none';
      content.style.display = 'block';

      const skills = data.skills || [];
      const evidence = data.evidence || [];
      const goalMastery = data.goal_mastery || { percentage: 0, status: 'IN_PROGRESS' };

      content.innerHTML = `
        <div class="mastery-banner">
          <div class="mastery-metric-big">
            <span class="label">Demonstrated Goal Mastery</span>
            <span class="value">${(goalMastery.percentage * 100).toFixed(0)}%</span>
            <span class="sub">${goalMastery.status}</span>
          </div>
          <div class="mastery-explanation">
            <p><strong>Mastery Criteria Philosophy:</strong> Course attendance alone does not constitute competency. Every skill level upgrade requires verified evidence from diagnostics, proctored mock assessments, or verified project milestones.</p>
          </div>
        </div>

        <div class="two-col-layout" style="margin-top: 24px;">
          <div class="col-main">
            <h3>Skill Competency Breakdown</h3>
            <div class="skill-matrix-list">
              ${skills.length === 0 ? `<p class="text-muted">No skill evaluations recorded yet.</p>` : skills.map(sk => {
                const levelPct = { NOVICE: 20, BEGINNER: 40, COMPETENT: 60, PROFICIENT: 80, EXPERT: 100 }[sk.current_level] || 10;
                return `
                  <div class="skill-row">
                    <div class="skill-row-info">
                      <span class="skill-title"><strong>${sk.skill_id}</strong></span>
                      <span class="skill-badge badge badge-neutral">${sk.current_level}</span>
                    </div>
                    <div class="progress-bar-container">
                      <div class="progress-bar-fill" style="width: ${levelPct}%;"></div>
                    </div>
                    <div class="skill-row-meta text-muted">
                      <span>Confidence: ${(sk.confidence * 100).toFixed(0)}%</span>
                      <span>Target Level: ${sk.required_level || 'PROFICIENT'}</span>
                    </div>
                  </div>
                `;
              }).join('')}
            </div>
          </div>

          <div class="col-side">
            <h3>Evidence Ledger</h3>
            <div class="evidence-timeline">
              ${evidence.length === 0 ? `<p class="text-muted">No evidence events logged.</p>` : evidence.map(ev => `
                <div class="evidence-item">
                  <div class="ev-top">
                    <span class="ev-type badge badge-info">${ev.source_type}</span>
                    <span class="ev-score">Score: ${(ev.score * 100).toFixed(0)}%</span>
                  </div>
                  <p class="ev-desc"><strong>${ev.skill_id}</strong> - ${ev.notes || 'Assessment record'}</p>
                  <span class="ev-time text-muted">${new Date(ev.recorded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              `).join('')}
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      loading.innerHTML = `<p class="text-error">Failed to load progress: ${err.message}</p>`;
    }
  }
}

