import { api } from '../api/client.js';

export function renderPlan(container, state, navigate) {
  if (!state.studentId) {
    container.innerHTML = `
      <div class="screen-card alert-warning">
        <p>Please complete onboarding first.</p>
        <button class="btn btn-primary" onclick="window.location.hash='#onboard'">Go to Onboarding</button>
      </div>
    `;
    return;
  }

  let activeView = 'phases'; // 'phases', 'weekly', 'semester', or 'electives'
  let currentWeekNum = 1;

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h2>Phase-Wise Academic Roadmap & Adaptive Schedule</h2>
          <p class="subtitle">Maintained exclusively by <strong>Agent 1 (Roadmap Planner)</strong> with single-writer guarantees, verified against IIT BBS curriculum regulations.</p>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button class="btn btn-outline" id="btn-toggle-view">Switch to Weekly Schedule</button>
          <button class="btn btn-outline" id="btn-refresh-plan">Refresh</button>
          <button class="btn btn-primary" id="btn-goto-learn">Begin Study & Check-in Tasks →</button>
        </div>
      </div>

      <!-- Pending Change Proposals Banner -->
      <div id="proposal-banner-container" style="display: none; margin-bottom: 20px;"></div>

      <div id="plan-loading" class="loading-state">Synthesizing verified phase-wise roadmap...</div>
      <div id="plan-content" style="display: none;"></div>
    </div>
  `;

  document.getElementById('btn-refresh-plan').addEventListener('click', loadAllData);
  document.getElementById('btn-goto-learn').addEventListener('click', () => navigate('#learn'));
  document.getElementById('btn-toggle-view').addEventListener('click', () => {
    if (activeView === 'phases') {
      activeView = 'weekly';
      document.getElementById('btn-toggle-view').textContent = 'Switch to Semestral View';
    } else if (activeView === 'weekly') {
      activeView = 'semester';
      document.getElementById('btn-toggle-view').textContent = 'Switch to Recommended Electives';
    } else if (activeView === 'semester') {
      activeView = 'electives';
      document.getElementById('btn-toggle-view').textContent = 'Switch to Phase-Wise Roadmap';
    } else {
      activeView = 'phases';
      document.getElementById('btn-toggle-view').textContent = 'Switch to Weekly Schedule';
    }
    loadAllData();
  });

  loadAllData();

  async function loadAllData() {
    const loading = document.getElementById('plan-loading');
    const content = document.getElementById('plan-content');
    loading.style.display = 'block';
    content.style.display = 'none';

    try {
      const [planData, weeklyData, proposalsData] = await Promise.all([
        api.getPlan(state.studentId).catch(() => null),
        api.getWeeklyRoadmap(state.studentId, currentWeekNum).catch(() => null),
        api.getProposals(state.studentId).catch(() => ({ proposals: [] }))
      ]);

      if (!planData) {
        throw new Error("Unable to retrieve roadmap. Please try regenerating.");
      }

      const plan = planData.plan || planData;
      const validation = planData.validation || { passed: true, checks: [] };
      const proposals = proposalsData?.proposals || [];

      renderProposalsBanner(proposals);

      loading.style.display = 'none';
      content.style.display = 'block';

      if (activeView === 'weekly' && weeklyData) {
        renderWeeklyView(content, plan, weeklyData, validation);
      } else if (activeView === 'semester') {
        renderSemestralView(content, plan, validation);
      } else if (activeView === 'electives') {
        renderElectivesView(content);
      } else {
        renderPhaseView(content, plan, validation);
      }
    } catch (err) {
      loading.innerHTML = `
        <div class="alert alert-error">
          <p>Failed to load plan: ${err.message}</p>
          <button class="btn btn-primary" onclick="location.reload()">Try Again</button>
        </div>
      `;
    }
  }

  function renderProposalsBanner(proposals) {
    const banner = document.getElementById('proposal-banner-container');
    if (!proposals || proposals.length === 0) {
      banner.style.display = 'none';
      return;
    }

    banner.style.display = 'block';
    banner.innerHTML = `
      <div style="background: #fff8e1; border: 1px solid #ffe082; border-radius: 8px; padding: 16px;">
        <h4 style="margin-top:0; color: #b78103; display:flex; align-items:center; gap:8px;">
          🔔 Pending Roadmap Adaptation Proposals (${proposals.length})
        </h4>
        <p style="margin-bottom: 12px; font-size: 0.9em; color: #555;">
          Under the <strong>Single-Writer Rule</strong>, other agents cannot modify your roadmap directly. Review the proposed changes below:
        </p>
        ${proposals.map(p => `
          <div style="background: white; border: 1px solid #ffd54f; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span class="badge badge-info">${(p.proposer_agent || 'AGENT').replace('_', ' ').toUpperCase()}</span>
              <span class="badge badge-neutral">${p.proposal_type || 'CHANGE'}</span>
            </div>
            <p><strong>Reasoning:</strong> ${p.reasoning}</p>
            <p style="color: #2e7d32;"><strong>Proposed Effect:</strong> ${p.impact_summary || 'Updates study milestones'}</p>
            <div style="display:flex; gap: 8px; margin-top: 10px;">
              <button class="btn btn-primary btn-sm btn-approve-prop" data-id="${p.proposal_id}">✓ Approve & Commit v${(state.planVersion || 1) + 1}</button>
              <button class="btn btn-outline btn-sm btn-reject-prop" data-id="${p.proposal_id}">✕ Reject Change</button>
            </div>
          </div>
        `).join('')}
      </div>
    `;

    banner.querySelectorAll('.btn-approve-prop').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const pid = e.target.getAttribute('data-id');
        e.target.disabled = true;
        e.target.textContent = 'Committing...';
        await api.decideProposal(state.studentId, pid, true, "Approved by student via Plan screen.");
        loadAllData();
      });
    });

    banner.querySelectorAll('.btn-reject-prop').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const pid = e.target.getAttribute('data-id');
        e.target.disabled = true;
        e.target.textContent = 'Rejecting...';
        await api.decideProposal(state.studentId, pid, false, "Rejected by student.");
        loadAllData();
      });
    });
  }

  function renderPhaseView(content, plan, validation) {
    const phases = {
      'Phase 1: Foundation & Prerequisite Gaps': [],
      'Phase 2: Core Coursework & Practical Application': [],
      'Phase 3: Applied Mastery & Capstone': []
    };

    let totalWeeklyHours = 0;
    (plan.items || []).forEach(it => {
      const p = it.phase || 'Phase 2: Core Coursework & Practical Application';
      if (!phases[p]) {
        phases[p] = [];
      }
      phases[p].push(it);
      totalWeeklyHours += (it.prep_hours_weekly || 4.0);
    });

    const validationBadge = validation.passed 
      ? `<span class="badge badge-success" style="font-size: 13px;">✓ CURRICULUM COMPLIANT</span>`
      : `<span class="badge badge-error" style="font-size: 13px;">✕ CONFLICTS DETECTED</span>`;

    content.innerHTML = `
      <div class="roadmap-summary" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px; padding: 16px; background: rgba(0,0,0,0.02); border-radius: 8px;">
        <div>
          <div class="text-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Student Target Track</div>
          <div style="font-size: 16px; font-weight: 600; margin-top: 4px;">${plan.goal_id ? plan.goal_id.replace('GOAL_', '') : 'Core Track'}</div>
        </div>
        <div>
          <div class="text-muted" style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px;">Roadmap Version</div>
          <div style="font-size: 16px; font-weight: 600; margin-top: 4px;">v${plan.version || 1}</div>
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

      ${plan.mismatch_warning ? `
        <div class="alert alert-warning" style="margin-bottom: 24px; border-left: 5px solid #f59e0b; background: #fffbeb; padding: 16px; border-radius: 6px;">
          <h4 style="margin: 0 0 6px 0; color: #b45309; display: flex; align-items: center; gap: 8px;">
            ⚠️ Interest vs. Diagnostic Evidence Mismatch Detected
          </h4>
          <p style="margin: 0 0 8px 0; font-size: 13.5px; color: #78350f;">${plan.mismatch_warning.explanation || 'Prerequisite diagnostic gap identified.'}</p>
          <div style="font-size: 12.5px; font-weight: 500; color: #92400e;">
            <strong>Autonomous Engine Action:</strong> ${plan.mismatch_warning.tradeoff || 'Injected prerequisite remediation in Phase 1 before specialized electives.'}
          </div>
        </div>
      ` : ''}

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
                  <span class="badge" style="background: white; border: 1px solid var(--border-color, #e5e7eb); font-size: 12px;">${items.length} Modules / Tasks</span>
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
  }

  function renderWeeklyView(container, plan, weekly, validation) {
    container.innerHTML = `
      <div class="plan-summary-bar">
        <div class="summary-metric">
          <span class="metric-label">Roadmap Version</span>
          <span class="metric-val">v${plan.version || 1}</span>
        </div>
        <div class="summary-metric">
          <span class="metric-label">Active Week</span>
          <span class="metric-val">Week ${weekly.week_number} of 16</span>
        </div>
        <div class="summary-metric">
          <span class="metric-label">Weekly Workload</span>
          <span class="metric-val">${weekly.total_estimated_hours} hrs</span>
        </div>
        <div class="summary-metric">
          <span class="metric-label">Validation Status</span>
          <span class="metric-val">
            ${validation.passed ? '<span class="badge badge-success">✓ ALL RULES COMPLIANT</span>' : '<span class="badge badge-error">✕ VALIDATION ISSUES</span>'}
          </span>
        </div>
      </div>

      <div style="margin: 20px 0; background: #f0f7ff; border: 1px solid #cce3ff; border-radius: 8px; padding: 14px;">
        <h4 style="margin:0 0 6px 0; color: #004494;">🎯 Week ${weekly.week_number} Objective</h4>
        <p style="margin:0; color: #333;">${weekly.weekly_objective}</p>
        <div style="margin-top: 8px; display:flex; gap: 6px; flex-wrap: wrap;">
          ${(weekly.focus_skills || []).map(s => `<span class="badge badge-info">${s}</span>`).join('')}
        </div>
      </div>

      <h3>7-Day Structured Schedule (Agent 1 Output)</h3>
      <div class="weekly-tasks-grid" style="display: flex; flex-direction: column; gap: 10px;">
        ${weekly.daily_tasks.map(t => `
          <div style="background: white; border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; display:flex; justify-content:space-between; align-items:center;">
            <div>
              <span class="badge ${t.task_type === 'quiz' ? 'badge-error' : t.task_type === 'practice_exercise' ? 'badge-warning' : 'badge-neutral'}" style="margin-right: 8px;">
                ${t.task_type.toUpperCase()}
              </span>
              <strong>${t.title}</strong>
              ${t.resource_url ? `<div style="font-size:0.85em; margin-top:4px;"><a href="${t.resource_url}" target="_blank" rel="noopener">🔗 ${t.resource_title || 'Open Learning Resource'} ↗</a></div>` : ''}
            </div>
            <div style="text-align: right; color: #666; font-size: 0.9em;">
              <span>⏱ ${t.estimated_minutes} mins</span>
            </div>
          </div>
        `).join('')}
      </div>
    `;
  }

  function renderSemestralView(container, plan, validation) {
    const semGroups = {};
    (plan.items || []).forEach(item => {
      const sem = item.semester_number || 1;
      if (!semGroups[sem]) semGroups[sem] = [];
      semGroups[sem].push(item);
    });

    container.innerHTML = `
      <div class="plan-summary-bar">
        <div class="summary-metric">
          <span class="metric-label">Goal ID</span>
          <span class="metric-val">${plan.goal_id || 'N/A'}</span>
        </div>
        <div class="summary-metric">
          <span class="metric-label">Roadmap Version</span>
          <span class="metric-val">v${plan.version || 1}</span>
        </div>
        <div class="summary-metric">
          <span class="metric-label">Planned Items</span>
          <span class="metric-val">${(plan.items || []).length} items</span>
        </div>
      </div>

      <div class="schedule-container">
        ${Object.keys(semGroups).sort((a,b) => a-b).map(sem => {
          const items = semGroups[sem];
          return `
            <div class="semester-block" style="margin-top: 18px;">
              <div class="semester-header" style="background:#f9f9f9; padding:8px 12px; border-radius:4px; font-weight:bold;">
                Semester ${sem} (${items.length} Modules/Courses)
              </div>
              <div style="margin-top: 8px; display:flex; flex-direction:column; gap:6px;">
                ${items.map(it => `
                  <div style="padding: 10px; border: 1px solid #eee; border-radius: 4px;">
                    <strong>${it.course_id || it.item_type}</strong>
                    <div style="font-size:0.85em; color:#666;">${it.reason?.why_this || 'Planned core progression.'}</div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;
  }

  async function renderElectivesView(container) {
    container.innerHTML = '<div class="loading-state">Evaluating course eligibility and self-study redundancy...</div>';
    try {
      const recData = await api.getRecommendedCourses(state.studentId);
      const recs = recData.recommendations || [];
      container.innerHTML = `
        <div class="screen-header">
          <h3>Course & Elective Recommendations</h3>
          <p class="subtitle">Evaluated deterministically against institutional prerequisite rules, CGPA thresholds, and self-study velocity redundancy.</p>
        </div>
        <div style="display:flex; flex-direction:column; gap:12px; margin-top:16px;">
          ${recs.map(r => `
            <div style="border:1px solid ${r.is_recommended ? '#81c784' : '#e0e0e0'}; background:${r.is_recommended ? '#f1f8e9' : 'white'}; border-radius:8px; padding:16px;">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <h4 style="margin:0;">${r.course_id}: ${r.title}</h4>
                <div style="display:flex; gap:6px;">
                  ${(r.rule_badges || []).map(b => `
                    <span class="badge ${b === 'RECOMMENDED' ? 'badge-success' : b === 'REDUNDANT' ? 'badge-warning' : b === 'INELIGIBLE' ? 'badge-error' : 'badge-neutral'}">${b}</span>
                  `).join('')}
                </div>
              </div>
              <div style="font-size:0.9em; color:#555; margin-bottom:6px;">
                <strong>Credits:</strong> ${r.credits} | <strong>Semester Offered:</strong> ${r.semester_offered}
              </div>
              <div style="font-size:0.9em; color:${r.is_recommended ? '#2e7d32' : '#c62828'};">
                ${r.why_recommended}
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="alert alert-error">Failed to load electives: ${err.message}</div>`;
    }
  }
}
