import { api } from '../api/client.js';

export function renderAdapt(container, state, navigate) {
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
        <h2>Adaptive Simulator ("What Changed?")</h2>
        <p class="subtitle">Simulate real-time performance shocks (e.g. ace a test to skip, or struggle and receive remediation) and inspect deterministic plan diffs.</p>
      </div>

      <div class="simulator-controls-card">
        <h3>Trigger Quiz Performance Event</h3>
        <form id="sim-form" class="form-grid">
          <div class="form-group">
            <label for="sim-skill">Target Skill</label>
            <select id="sim-skill">
              <option value="SKILL_CIRCUIT_ANALYSIS" selected>SKILL_CIRCUIT_ANALYSIS (Circuit Analysis)</option>
              <option value="SKILL_SIGNALS_SYSTEMS">SKILL_SIGNALS_SYSTEMS (Signals & Systems)</option>
              <option value="SKILL_ELECTRICAL_MACHINES">SKILL_ELECTRICAL_MACHINES (Electrical Machines)</option>
              <option value="SKILL_CONTROL_SYSTEMS">SKILL_CONTROL_SYSTEMS (Control Systems)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="sim-score">Quiz Score</label>
            <select id="sim-score">
              <option value="0.95">0.95 (High Mastery - Accelerate / Test Out)</option>
              <option value="0.75">0.75 (Competent - Standard Progress)</option>
              <option value="0.30">0.30 (Weak Performance - Trigger Remediation)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="sim-source">Assessment Type</label>
            <select id="sim-source">
              <option value="PROCTORED_QUIZ" selected>Proctored Quiz (Weight: 1.0)</option>
              <option value="HOMEWORK_EXERCISE">Homework Practice (Weight: 0.6)</option>
              <option value="DIAGNOSTIC_TEST">Diagnostic Item (Weight: 0.8)</option>
            </select>
          </div>

          <div class="form-actions full-width">
            <button type="submit" class="btn btn-secondary">Simulate Assessment & Re-plan</button>
          </div>
        </form>
      </div>

      <div id="diff-container" style="display: none; margin-top: 24px;">
        <h3>Adaptation Diff Report</h3>
        <div id="diff-content"></div>
      </div>
    </div>
  `;

  document.getElementById('sim-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const skill = document.getElementById('sim-skill').value;
    const score = parseFloat(document.getElementById('sim-score').value);
    const source = document.getElementById('sim-source').value;

    const diffContainer = document.getElementById('diff-container');
    const diffContent = document.getElementById('diff-content');
    diffContainer.style.display = 'block';
    diffContent.innerHTML = `<div class="loading-state">Running simulation and computing plan diff...</div>`;

    try {
      const res = await api.simulateQuiz(state.studentId, {
        skill_id: skill,
        score: score,
        source_type: source,
        notes: `Simulated event for ${skill}`
      });

      const diff = res.diff || { added: [], removed: [], modified: [] };
      const explanation = res.explanation || 'Plan adapted according to performance delta.';

      diffContent.innerHTML = `
        <div class="diff-summary-card">
          <div class="diff-version-info">
            <span>Previous Version: <strong>v${res.old_version || 1}</strong></span>
            <span>➜</span>
            <span>New Version: <strong>v${res.new_version || 2}</strong></span>
          </div>
          <div class="diff-explanation">
            <strong>Engine Rationale:</strong>
            <p>${explanation}</p>
          </div>
        </div>

        <div class="diff-columns">
          <div class="diff-col added-col">
            <h4>+ Added / Remedial Items (${diff.added?.length || 0})</h4>
            ${(!diff.added || diff.added.length === 0) ? `<p class="text-muted">None</p>` : `
              <ul>
                ${diff.added.map(it => `<li><strong>${it.course_id || it.title}</strong>: ${it.reason || 'Added'}</li>`).join('')}
              </ul>
            `}
          </div>

          <div class="diff-col removed-col">
            <h4>- Removed / Accelerated Items (${diff.removed?.length || 0})</h4>
            ${(!diff.removed || diff.removed.length === 0) ? `<p class="text-muted">None</p>` : `
              <ul>
                ${diff.removed.map(it => `<li><strong>${it.course_id || it.title}</strong>: ${it.reason || 'Skipped'}</li>`).join('')}
              </ul>
            `}
          </div>
        </div>

        <div style="margin-top: 16px;">
          <button class="btn btn-primary" onclick="window.location.hash='#plan'">View Updated Full Schedule</button>
        </div>
      `;
    } catch (err) {
      diffContent.innerHTML = `<p class="text-error">Simulation error: ${err.message}</p>`;
    }
  });
}

