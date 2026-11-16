import { api } from '../api/client.js';

export function renderDiagnostic(container, state, navigate) {
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
        <h2>Adaptive Knowledge Diagnostic</h2>
        <p class="subtitle">Quick adaptive assessment to establish your baseline skill proficiency without redundant coursework.</p>
      </div>
      <div id="diagnostic-loading" class="loading-state">Loading adaptive diagnostic questions...</div>
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
          <p>No diagnostic questions found for this goal. Baseline set to NOVICE.</p>
          <button class="btn btn-primary" id="btn-proceed">Generate Personalised Plan</button>
        `;
        document.getElementById('btn-proceed').addEventListener('click', () => navigate('#plan'));
        return;
      }

      content.innerHTML = `
        <form id="diag-form">
          <div class="questions-list">
            ${questions.map((q, idx) => `
              <div class="question-card">
                <div class="q-header">
                  <span class="badge badge-info">Question ${idx + 1}</span>
                  <span class="badge badge-neutral">Skill: ${q.skill_id}</span>
                  <span class="badge badge-neutral">Difficulty: ${(q.difficulty * 10).toFixed(1)}/10</span>
                </div>
                <p class="q-prompt"><strong>${q.prompt}</strong></p>
                <div class="q-options">
                  ${(q.options || ['A', 'B', 'C', 'D']).map((opt, oIdx) => `
                    <label class="option-label">
                      <input type="radio" name="q_${q.exercise_id}" value="${opt}" ${oIdx === 0 ? 'checked' : ''} />
                      <span>${opt}</span>
                    </label>
                  `).join('')}
                </div>
              </div>
            `).join('')}
          </div>
          <div class="form-actions" style="margin-top: 24px;">
            <button type="submit" class="btn btn-primary">Submit Diagnostic & Build Plan</button>
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
          alert(`Diagnostic submitted! Score: ${(res.score * 100).toFixed(1)}%. Skill states updated.`);
          navigate('#plan');
        } catch (err) {
          alert(`Error submitting diagnostic: ${err.message}`);
        }
      });
    } catch (err) {
      document.getElementById('diagnostic-loading').innerHTML = `
        <p class="text-error">Error loading diagnostic: ${err.message}</p>
        <button class="btn btn-secondary" onclick="window.location.hash='#plan'">Skip to Plan</button>
      `;
    }
  }
}

