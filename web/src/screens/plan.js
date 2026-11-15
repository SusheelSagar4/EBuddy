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

  let activeView = 'weekly'; // 'weekly' or 'semester'
  let currentWeekNum = 1;

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between">
        <div>
          <h2>Academic Roadmap & Adaptive Schedule</h2>
          <p class="subtitle">Maintained exclusively by <strong>Agent 1 (Roadmap Planner)</strong> with single-writer guarantees.</p>
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-outline" id="btn-toggle-view">Switch to Semestral View</button>
          <button class="btn btn-primary" id="btn-refresh-plan">Refresh</button>
        </div>
      </div>

      <!-- Pending Change Proposals Banner -->
      <div id="proposal-banner-container" style="display:none; margin-bottom: 20px;"></div>

      <div id="plan-loading" class="loading-state">Loading verified roadmap & weekly tasks...</div>
      <div id="plan-content" style="display: none;"></div>
    </div>
  `;

  document.getElementById('btn-refresh-plan').addEventListener('click', loadAllData);
  document.getElementById('btn-toggle-view').addEventListener('click', () => {
    activeView = activeView === 'weekly' ? 'semester' : 'weekly';
    document.getElementById('btn-toggle-view').textContent = activeView === 'weekly' ? 'Switch to Semestral View' : 'Switch to Weekly Schedule';
    loadAllData();
  });

  loadAllData();

  async function loadAllData() {
    const loading = document.getElementById('plan-loading');
    const content = document.getElementById('plan-content');
    loading.style.display = 'block';
    content.style.display = 'none';

    try {
      // 1. Check for pending change proposals
      const propData = await api.getProposals(state.studentId).catch(() => ({ proposals: [] }));
      renderProposalsBanner(propData.proposals || []);

      // 2. Load plan & version history
      const planData = await api.getPlan(state.studentId);
      const plan = planData.plan || planData;
      const validation = plan.validation_report || { passed: true, messages: [] };

      // 3. Load weekly roadmap if in weekly view
      let weeklyData = null;
      if (activeView === 'weekly') {
        weeklyData = await api.getWeeklyRoadmap(state.studentId, currentWeekNum).catch(() => null);
      }

      loading.style.display = 'none';
      content.style.display = 'block';

      if (activeView === 'weekly' && weeklyData) {
        renderWeeklyView(content, plan, weeklyData, validation);
      } else {
        renderSemestralView(content, plan, validation);
      }
    } catch (err) {
      loading.innerHTML = `<p class="text-danger">Failed to load plan: ${err.message}</p>`;
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
          🔔 Pending Roadmap Adaptation Proposal (${proposals.length})
        </h4>
        <p style="margin-bottom: 12px; font-size: 0.9em; color: #555;">
          Under the <strong>Single-Writer Rule</strong>, other agents cannot modify your roadmap directly. Review the proposed change below:
        </p>
        ${proposals.map(p => `
          <div style="background: white; border: 1px solid #ffd54f; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
            <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
              <span class="badge badge-info">${p.proposer_agent.replace('_', ' ').toUpperCase()}</span>
              <span class="badge badge-neutral">${p.proposal_type}</span>
            </div>
            <p><strong>Reasoning:</strong> ${p.reasoning}</p>
            <p style="color: #2e7d32;"><strong>Proposed Effect:</strong> ${p.impact_summary}</p>
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
}
