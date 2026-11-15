import { api } from '../api/client.js';

export function renderDiagnostic(container, state, navigate) {
  if (!state.studentId) {
    container.innerHTML = `
      <div class="screen-card alert-warning">
        <p>Please complete onboarding first to set up your core engineering goals.</p>
        <button class="btn btn-primary" onclick="window.location.hash='#onboard'">Go to Onboarding</button>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header">
        <h2>Technical Skills Baseline Diagnostic Test</h2>
        <p class="subtitle">Real technical assessment to analyze your baseline proficiency in core skills, so your buddy does not assign redundant coursework.</p>
      </div>
      <div id="diagnostic-loading" class="loading-state">Selecting technical skill diagnostic questions for your core engineering path...</div>
      <div id="diagnostic-content" style="display: none;"></div>
    </div>
  `;

  loadQuestions();

  async function loadQuestions() {
    try {
      const data = await api.getDiagnostic(state.studentId);
      const loading = document.getElementById('diagnostic-loading');
      const content = document.getElementById('diagnostic-content');
      if (loading) loading.style.display = 'none';
      if (!content) return;
      content.style.display = 'block';

      const questions = data.questions || [];
      if (questions.length === 0) {
        content.innerHTML = `
          <div class="alert alert-info">
            <p>Diagnostic complete or baseline established for your profile.</p>
            <button class="btn btn-primary" id="btn-proceed">View Phase-wise Personalised Plan →</button>
          </div>
        `;
        document.getElementById('btn-proceed').addEventListener('click', () => navigate('#plan'));
        return;
      }

      content.innerHTML = `
        <div class="diagnostic-intro" style="margin-bottom: 20px; padding: 12px 16px; background: rgba(59, 130, 246, 0.08); border-left: 4px solid var(--accent-primary, #2563eb); border-radius: 4px;">
          <strong>Target Discipline:</strong> ${data.goal_name || 'Core Engineering Track'}<br/>
          <small class="text-muted">Answer these 5 technical questions to benchmark your foundation. Unattempted questions will default to baseline proficiency.</small>
        </div>
        <form id="diag-form">
          <div class="questions-list">
            ${questions.map((q, idx) => `
              <div class="question-card" style="margin-bottom: 20px; padding: 16px; border: 1px solid var(--border-color, #e5e7eb); border-radius: 8px;">
                <div class="q-header" style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center;">
                  <span class="badge badge-info">Q${idx + 1}</span>
                  <span class="badge badge-neutral">Skill: ${q.skill_id.replace('SKILL_', '')}</span>
                  <span class="badge badge-neutral">Est. Difficulty: ${q.difficulty_level || 'Intermediate'}</span>
                </div>
                <p class="q-prompt" style="font-size: 15px; font-weight: 500; margin-bottom: 14px;">${q.prompt || q.question_text}</p>
                <div class="q-options" style="display: flex; flex-direction: column; gap: 10px;">
                  ${(q.options || []).map((opt, oIdx) => `
                    <label class="option-label" style="display: flex; align-items: center; gap: 10px; cursor: pointer; padding: 8px 12px; border-radius: 6px; background: rgba(0,0,0,0.02);">
                      <input type="radio" name="q_${q.exercise_id}" value="${opt}" ${oIdx === 0 ? 'checked' : ''} />
                      <span style="font-size: 14px;">${opt}</span>
                    </label>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
          <div class="form-actions" style="margin-top: 24px;">
            <button type="submit" class="btn btn-primary" style="padding: 10px 24px; font-size: 15px;">Analyze My Technical Skills & Build Phase-wise Plan →</button>
          </div>
        </form>
      `;

      document.getElementById('diag-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const answers = {};
        questions.forEach(q => {
          const sel = document.querySelector(`input[name="q_${q.exercise_id}"]:checked`);
          if (sel) answers[q.exercise_id] = sel.value;
        });

        try {
          const res = await api.submitDiagnostic(state.studentId, { answers });
          const avgScore = res.score ? (res.score * 100).toFixed(1) : (res.average_score || 70).toFixed(1);
          alert(`Technical skills analyzed!\nDiagnostic Baseline Score: ${avgScore}%\nPlan will now be synthesized in structured phases.`);
          navigate('#plan');
        } catch (err) {
          alert(`Error submitting diagnostic: ${err.message}`);
        }
      });
    } catch (err) {
      document.getElementById('diagnostic-loading').innerHTML = `
        <p class="text-error">Error loading diagnostic: ${err.message}</p>
        <button class="btn btn-secondary" onclick="window.location.hash='#plan'">Skip directly to Plan</button>
      `;
    }
  }
}
