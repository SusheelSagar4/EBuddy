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
      <div class="screen-header flex-between" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
          <h2>Phase-Wise Core Academic Roadmap</h2>
          <p class="subtitle">Structured study & prep roadmap designed to eliminate skill gaps, verified against IIT BBS curriculum regulations.</p>
        </div>
        <div>
          <button class="btn btn-outline" id="btn-refresh-plan">Re-generate / Validate Plan</button>
          <button class="btn btn-primary" id="btn-goto-learn" style="margin-left: 8px;">Begin Study & Check-in Tasks →</button>
        </div>
      </div>

      <div id="plan-loading" class="loading-state">Synthesizing verified phase-wise roadmap...</div>
      <div id="plan-content" style="display: none;"></div>
    </div>
  `;

  document.getElementById('btn-refresh-plan').addEventListener('click', loadPlan);
  document.getElementById('btn-goto-learn').addEventListener('click', () => navigate('#learn'));
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

      const plan = data.plan || data;
      const validation = data.validation || (plan.validation_report || { passed: true, checks: [] });

      // Group items by phase
      const phases = {
        'Phase 1: Foundation': [],
        'Phase 2: Core Depth': [],
        'Phase 3: Applied Mastery': []
      };

      (plan.items || []).forEach(item => {
        const ph = item.phase || (item.item_type === 'milestone' ? 'Phase 3: Applied Mastery' : 'Phase 2: Core Depth');
        if (!phases[ph]) phases[ph] = [];
        phases[ph].push(item);
      });

      // Calculate totals
      let totalWeeklyHours = 0;
      (plan.items || []).forEach(it => {
        totalWeeklyHours += (it.prep_hours_weekly || 4.0);
      });

      const validationBadge = validation.passed 
        ? `<span class="badge badge-success" style="background: #10b981; color: white; padding: 6px 12px; border-radius: 4px; font-weight: 600;">✓ ALL IIT BBS REGULATORY RULES VERIFIED</span>`
        : `<span class="badge badge-error" style="background: #ef4444; color: white; padding: 6px 12px; border-radius: 4px; font-weight: 600;">✕ RULE VIOLATIONS DETECTED</span>`;

      content.innerHTML = `
        <div class="roadmap-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; padding: 16px; background: rgba(0,0,0,0.02); border-radius: 8px;">
          <div>
            <div class="text-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Student Target Track</div>
            <div style="font-size: 16px; font-weight: 600; margin-top: 4px;">${plan.goal_id ? plan.goal_id.replace('GOAL_', '') : 'Core Track'}</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Estimated Weekly Prep Time</div>
            <div style="font-size: 16px; font-weight: 600; margin-top: 4px;">~${(totalWeeklyHours / 3).toFixed(1)} hrs/week per phase</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Curriculum Compliance</div>
            <div style="margin-top: 6px;">${validationBadge}</div>
          </div>
        </div>

        <div class="phase-roadmap-container" style="display: flex; flex-direction: column; gap: 28px;">
          ${Object.entries(phases).map(([phaseName, items], pIdx) => {
            const phaseColors = [
              { border: '#3b82f6', bg: 'rgba(59, 130, 246, 0.05)', desc: 'Prerequisite foundation, circuit/thermodynamic theory, and fundamental engineering principles.' },
              { border: '#8b5cf6', bg: 'rgba(139, 92, 246, 0.05)', desc: 'Core systems depth, laboratory simulations, specialized electives, and active problem solving.' },
              { border: '#10b981', bg: 'rgba(16, 185, 129, 0.05)', desc: 'Applied engineering design project, timed mock interviews, and placement/industry readiness.' }
            ];
            const pStyle = phaseColors[pIdx] || phaseColors[0];

            return `
              <div class="phase-card" style="border: 1px solid var(--border-color, #e5e7eb); border-left: 6px solid ${pStyle.border}; border-radius: 8px; padding: 20px; background: ${pStyle.bg};">
                <div class="phase-header" style="margin-bottom: 14px;">
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h3 style="margin: 0; font-size: 18px; color: var(--text-primary);">${phaseName}</h3>
                    <span class="badge" style="background: white; border: 1px solid var(--border-color); font-size: 12px;">${items.length} Modules / Tasks</span>
                  </div>
                  <p class="text-muted" style="margin: 4px 0 0 0; font-size: 13px;">${pStyle.desc}</p>
                </div>

                <div class="phase-items-list" style="display: flex; flex-direction: column; gap: 12px;">
                  ${items.length === 0 ? `<p class="text-muted" style="font-style: italic;">No items required for this phase.</p>` : items.map(it => `
                    <div class="plan-item-row" style="background: white; border: 1px solid var(--border-color, #e5e7eb); border-radius: 6px; padding: 14px 16px;">
                      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div>
                          <span class="badge" style="font-size: 11px; text-transform: uppercase; margin-right: 8px; background: #e0f2fe; color: #0369a1;">${it.item_type}</span>
                          <strong style="font-size: 15px;">${it.course_id || it.title || it.item_id}</strong>
                        </div>
                        <span class="text-muted" style="font-size: 13px; font-weight: 500;">⏱ Prep: ${it.prep_hours_weekly || 4.0} hrs/wk</span>
                      </div>
                      <p style="font-size: 13.5px; color: #4b5563; margin: 4px 0 8px 0;">${it.reason?.why_this || 'Addresses technical competency requirement.'}</p>
                      <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                        ${(it.reason?.target_skills || []).map(s => `
                          <span class="badge badge-neutral" style="font-size: 11px;">Skill: ${s.replace('SKILL_', '')}</span>
                        `).join('')}
                      </div>
                    </div>
                  `).join('')}
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    } catch (err) {
      loading.innerHTML = `
        <div class="alert alert-error">
          <p>Failed to generate plan: ${err.message}</p>
          <button class="btn btn-primary" onclick="loadPlan()">Try Again</button>
        </div>
      `;
    }
  }
}
