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

  let activeView = 'timeline'; // 'timeline', 'next4weeks', or 'phases'

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h2>Academic Roadmap v2 & Multi-Semester Horizon</h2>
          <p class="subtitle">Deterministic timeline maintained exclusively by <strong>Agent 1 (Roadmap Planner)</strong> with single-writer guarantees.</p>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          <button class="btn ${activeView === 'timeline' ? 'btn-primary' : 'btn-outline'}" id="btn-view-timeline">Timeline View (Gantt)</button>
          <button class="btn ${activeView === 'next4weeks' ? 'btn-primary' : 'btn-outline'}" id="btn-view-next4weeks">Next 4 Weeks Schedule</button>
          <button class="btn ${activeView === 'phases' ? 'btn-primary' : 'btn-outline'}" id="btn-view-phases">Phase-Wise View</button>
          <button class="btn btn-outline" id="btn-refresh-plan">Refresh</button>
          <button class="btn btn-primary" id="btn-goto-learn">Daily Tasks →</button>
        </div>
      </div>

      <!-- Pending Change Proposals Banner -->
      <div id="proposal-banner-container" style="display: none; margin-bottom: 20px;"></div>

      <div id="plan-loading" class="loading-state">Synthesizing verified multi-semester timeline roadmap...</div>
      <div id="plan-content" style="display: none;"></div>

      <!-- Item Detail Modal Container -->
      <div id="item-detail-modal" class="detail-modal-backdrop" style="display: none;">
        <div class="detail-modal-dialog">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px; border-bottom:1px solid #e2e8f0; padding-bottom:10px;">
            <div>
              <span id="modal-item-badge" class="badge" style="font-size:11px; margin-bottom:4px;"></span>
              <h3 id="modal-item-title" style="margin:0; font-size:18px;"></h3>
            </div>
            <button id="btn-close-modal" class="btn btn-outline btn-sm" style="font-size:16px; line-height:1; padding:4px 8px;">✕</button>
          </div>
          <div id="modal-item-body" style="font-size:14px; color:#334155; display:flex; flex-direction:column; gap:10px;"></div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('btn-refresh-plan').addEventListener('click', loadAllData);
  document.getElementById('btn-goto-learn').addEventListener('click', () => navigate('#learn'));
  document.getElementById('btn-close-modal').addEventListener('click', closeModal);
  document.getElementById('item-detail-modal').addEventListener('click', (e) => {
    if (e.target.id === 'item-detail-modal') closeModal();
  });

  const btnTimeline = document.getElementById('btn-view-timeline');
  const btnNext4 = document.getElementById('btn-view-next4weeks');
  const btnPhases = document.getElementById('btn-view-phases');

  function updateViewButtons() {
    btnTimeline.className = activeView === 'timeline' ? 'btn btn-primary' : 'btn btn-outline';
    btnNext4.className = activeView === 'next4weeks' ? 'btn btn-primary' : 'btn btn-outline';
    btnPhases.className = activeView === 'phases' ? 'btn btn-primary' : 'btn btn-outline';
  }

  btnTimeline.addEventListener('click', () => { activeView = 'timeline'; updateViewButtons(); loadAllData(); });
  btnNext4.addEventListener('click', () => { activeView = 'next4weeks'; updateViewButtons(); loadAllData(); });
  btnPhases.addEventListener('click', () => { activeView = 'phases'; updateViewButtons(); loadAllData(); });

  loadAllData();

  async function loadAllData() {
    const loading = document.getElementById('plan-loading');
    const content = document.getElementById('plan-content');
    loading.style.display = 'block';
    content.style.display = 'none';

    try {
      const [planData, proposalsData] = await Promise.all([
        api.getPlan(state.studentId).catch(() => null),
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

      if (activeView === 'timeline') {
        renderTimelineView(content, plan, validation);
      } else if (activeView === 'next4weeks') {
        renderNext4WeeksView(content, plan, validation);
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

  function renderTimelineView(container, plan, validation) {
    const horizon = plan.timeline_roadmap?.horizon_deadline || "Degree Completion (2028)";
    const semesterBlocks = plan.semester_blocks || plan.timeline_roadmap?.semester_blocks || [];
    const assumptions = plan.timeline_roadmap?.assumptions || {};

    container.innerHTML = `
      <!-- Horizon Banner -->
      <div class="timeline-horizon-banner">
        <div>
          <div class="text-muted" style="font-size: 11px; text-transform: uppercase;">Planning Horizon</div>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a;">Today → ${horizon}</div>
        </div>
        <div style="display:flex; gap:12px; align-items:center;">
          <div>
            <div class="text-muted" style="font-size: 11px; text-transform: uppercase;">Roadmap Version</div>
            <div style="font-weight: 600;">v${plan.version || 1} (Single-Writer)</div>
          </div>
          <div>
            <div class="text-muted" style="font-size: 11px; text-transform: uppercase;">Curriculum Gate</div>
            <div>${validation.passed ? '<span class="badge badge-success">✓ COMPLIANT</span>' : '<span class="badge badge-error">✕ ISSUES</span>'}</div>
          </div>
        </div>
      </div>

      <!-- Planning Assumptions Banner (Indicative) -->
      <div class="timeline-assumptions-banner">
        <strong>ℹ️ Active Planning Assumptions (indicative):</strong> 
        Exam-week extra load factor: <code>0.4×</code> | Base study load: <code>1.0 hr/credit</code> | 
        <em>Indicative dates & pool tags applied where academic calendar or departmental pool selection rules are pending.</em>
      </div>

      <!-- Workload Cap Explanation if exceeded -->
      ${plan.workload_cap_explanation ? `
        <div class="alert alert-warning" style="margin-bottom: 20px; border-left: 5px solid #d97706; background: #fffbeb; padding: 14px; border-radius: 6px;">
          <h4 style="margin: 0 0 4px 0; color: #b45309;">⚠️ Weekly Study Workload Limit Applied</h4>
          <p style="margin: 0; font-size: 13.5px; color: #92400e;">${plan.workload_cap_explanation}</p>
        </div>
      ` : ''}

      <!-- Conflict or Mismatch Warning -->
      ${plan.mismatch_warning ? `
        <div class="alert alert-warning" style="margin-bottom: 20px; border-left: 5px solid #f59e0b; background: #fffbeb; padding: 14px; border-radius: 6px;">
          <h4 style="margin: 0 0 4px 0; color: #b45309;">⚠️ Diagnostic vs. Interest Flag</h4>
          <p style="margin: 0; font-size: 13px; color: #78350f;">${plan.mismatch_warning.explanation || 'Prerequisite diagnostic gap identified.'}</p>
        </div>
      ` : ''}

      <!-- Semester Blocks (Gantt Grid) -->
      <div class="semester-blocks-list">
        ${semesterBlocks.length === 0 ? `<p class="text-muted">No semester blocks scheduled.</p>` : semesterBlocks.map(block => {
          const reqCourses = block.required_courses || [];
          const elecPicks = block.elective_picks || [];
          const isInd = block.is_indicative;

          return `
            <div class="semester-block-card">
              <div class="semester-block-header">
                <div>
                  <h3 style="margin: 0; font-size: 17px; display:inline-block; vertical-align:middle;">${block.semester_name}</h3>
                  ${isInd ? `<span class="badge badge-warning" style="font-size:10px; margin-left:8px; vertical-align:middle;">indicative dates</span>` : `<span class="badge badge-neutral" style="font-size:10px; margin-left:8px; vertical-align:middle; background:#334155; color:white;">verified calendar</span>`}
                </div>
                <div style="font-size: 13px; color: #cbd5e1;">
                  <span>📅 ${block.start_date || 'TBD'} to ${block.end_date || 'TBD'}</span> | 
                  <span>🎓 ${block.total_credits} Credits Total</span>
                </div>
              </div>

              <!-- 4-Month Gantt-Style Themes Grid -->
              <div class="timeline-gantt-grid">
                ${(block.monthly_themes || []).map(theme => {
                  const isExam = theme.exam_buffer_notice !== null && theme.exam_buffer_notice !== undefined;
                  return `
                    <div class="month-theme-card ${isExam ? 'exam-month' : ''}">
                      <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-weight:700; font-size:13px; color:#1e293b;">Month ${theme.month_index}: ${theme.theme_title}</span>
                        <span class="badge ${isExam ? 'badge-warning' : 'badge-neutral'}" style="font-size:10px;">
                          ${theme.weekly_hours_cap}h cap
                        </span>
                      </div>
                      <p style="margin:0; font-size:12px; color:#64748b;">${theme.focus_description}</p>
                      ${isExam ? `<div style="font-size:11px; font-weight:600; color:#b45309;">⚠️ ${theme.exam_buffer_notice}</div>` : ''}
                    </div>
                  `;
                }).join('')}
              </div>

              <!-- Semester Courses: Required (Locked) vs Electives (Recommended) -->
              <div style="padding: 16px; border-top: 1px solid var(--border-color);">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;">
                  
                  <!-- Locked Required Courses Column -->
                  <div>
                    <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #0f172a; display: flex; align-items: center; gap: 6px;">
                      🔒 Locked Required Degree Core (${reqCourses.length})
                    </h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                      ${reqCourses.length === 0 ? `<p class="text-muted" style="font-size:12px; font-style:italic;">No core courses scheduled.</p>` : reqCourses.map(it => `
                        <div class="item-card-locked js-item-click" data-item='${JSON.stringify(it).replace(/'/g, "&apos;")}'>
                          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                              <span class="badge" style="background:#0f172a; color:white; font-size:10px; margin-right:4px;">LOCKED CORE</span>
                              <strong style="font-size:14px; color:#0f172a;">${it.course_id || it.item_id}</strong>
                            </div>
                            <span style="font-size:12px; font-weight:600; color:#475569;">${it.hours_per_week || it.estimated_hours} hrs/wk</span>
                          </div>
                          ${it.goal_emphasis ? `<div style="font-size:12px; color:#0369a1; margin-top:4px; font-weight:500;">🎯 ${it.goal_emphasis}</div>` : ''}
                          <p style="margin:4px 0 0 0; font-size:12px; color:#64748b;">${it.reason?.why_this || 'Mandatory curriculum requirement.'}</p>
                        </div>
                      `).join('')}
                    </div>
                  </div>

                  <!-- Recommended Elective Slots Column -->
                  <div>
                    <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #15803d; display: flex; align-items: center; gap: 6px;">
                      ★ Recommended Elective Slots (${elecPicks.length})
                    </h4>
                    <div style="display: flex; flex-direction: column; gap: 8px;">
                      ${elecPicks.length === 0 ? `<p class="text-muted" style="font-size:12px; font-style:italic;">No elective slot candidates scheduled for this semester.</p>` : elecPicks.map(it => `
                        <div class="item-card-recommended js-item-click" data-item='${JSON.stringify(it).replace(/'/g, "&apos;")}'>
                          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                              <span class="badge badge-success" style="font-size:10px; margin-right:4px;">ELECTIVE PICK</span>
                              <strong style="font-size:14px; color:#15803d;">${it.course_id || it.slot_id}</strong>
                            </div>
                            <span style="font-size:12px; font-weight:600; color:#15803d;">${it.hours_per_week || it.estimated_hours} hrs/wk</span>
                          </div>
                          ${it.pool_rule_status ? `<div style="margin-top:4px;"><span class="badge badge-warning" style="font-size:10px;">⚠️ ${it.pool_rule_status}</span></div>` : ''}
                          <div style="font-size:12px; color:#166534; margin-top:4px;">Fills: <strong>${it.slot_id || 'Elective Slot'}</strong></div>
                          <p style="margin:4px 0 0 0; font-size:12px; color:#64748b;">${it.reason?.why_this || 'Recommended to close technical gap.'}</p>
                        </div>
                      `).join('')}
                    </div>
                  </div>

                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    attachItemClickListeners(container);
  }

  function renderNext4WeeksView(container, plan, validation) {
    const next4 = plan.next_4_weeks || [];
    const studentWeeklyCap = 20.0; // indicative cap
    const weeksMap = { 1: [], 2: [], 3: [], 4: [] };

    next4.forEach(it => {
      const w = it.week_index || 1;
      if (weeksMap[w]) weeksMap[w].push(it);
    });

    container.innerHTML = `
      <div class="timeline-horizon-banner">
        <div>
          <div class="text-muted" style="font-size: 11px; text-transform: uppercase;">Upcoming Operational Window</div>
          <div style="font-size: 16px; font-weight: 700; color: #0f172a;">Next 4 Weeks Weekly Plan</div>
        </div>
        <div>
          <span class="badge badge-neutral">Weeks 1 - 4</span>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 20px;">
        ${[1, 2, 3, 4].map(wNum => {
          const items = weeksMap[wNum];
          const totalHours = items.reduce((acc, it) => acc + (it.hours_per_week || 0.0), 0.0);
          const pct = Math.min(100, Math.round((totalHours / studentWeeklyCap) * 100));
          const statusClass = pct > 90 ? 'warning' : 'normal';

          return `
            <div style="background: white; border: 1px solid var(--border-color); border-radius: 8px; padding: 18px;">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <h4 style="margin: 0; font-size: 16px;">Week ${wNum}</h4>
                <div style="font-size: 13px; font-weight: 600; color: #475569;">
                  Total Workload: ${totalHours.toFixed(1)}h / Cap: ${studentWeeklyCap}h/wk (${pct}%)
                </div>
              </div>

              <!-- Workload Bar -->
              <div class="workload-bar-container">
                <div class="workload-bar-track">
                  <div class="workload-bar-fill ${statusClass}" style="width: ${pct}%;"></div>
                </div>
              </div>

              <!-- Weekly Items -->
              <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 12px;">
                ${items.length === 0 ? `<p class="text-muted" style="font-size: 13px;">No items scheduled for Week ${wNum}.</p>` : items.map(it => `
                  <div class="js-item-click" data-item='${JSON.stringify(it).replace(/'/g, "&apos;")}' style="display: flex; justify-content: space-between; align-items: center; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 14px; cursor: pointer;">
                    <div>
                      <span class="badge ${it.item_type === 'REQUIRED_COURSE' ? 'badge-neutral' : it.item_type === 'CHECKPOINT' ? 'badge-warning' : 'badge-info'}" style="font-size: 10px; margin-right: 6px;">
                        ${it.item_type}
                      </span>
                      <strong style="font-size: 14px;">${it.title}</strong>
                      ${it.is_indicative ? `<span class="badge badge-warning" style="font-size: 9px; margin-left: 6px;">indicative</span>` : ''}
                    </div>
                    <div style="text-align: right;">
                      <span style="font-weight: 600; font-size: 13px; color: #1e293b;">${it.hours_per_week} hrs</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `;

    attachItemClickListeners(container);
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
      if (!phases[p]) phases[p] = [];
      phases[p].push(it);
      totalWeeklyHours += (it.prep_hours_weekly || 4.0);
    });

    content.innerHTML = `
      <div class="phase-roadmap-container" style="display: flex; flex-direction: column; gap: 20px;">
        ${Object.entries(phases).map(([phaseName, items]) => `
          <div class="phase-card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 18px; background: white;">
            <h3 style="margin: 0 0 12px 0; font-size: 16px;">${phaseName} (${items.length} Modules)</h3>
            <div style="display: flex; flex-direction: column; gap: 8px;">
              ${items.length === 0 ? `<p class="text-muted" style="font-size:12px;">No items in this phase.</p>` : items.map(it => `
                <div class="js-item-click" data-item='${JSON.stringify(it).replace(/'/g, "&apos;")}' style="padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; background: #f8fafc;">
                  <div style="display: flex; justify-content: space-between;">
                    <strong>${it.course_id || it.title || it.item_id}</strong>
                    <span style="font-size: 12px; color: #64748b;">${it.prep_hours_weekly || 4.0} hrs/wk</span>
                  </div>
                  <p style="margin: 4px 0 0 0; font-size: 12px; color: #64748b;">${it.reason?.why_this || 'Core learning item.'}</p>
                </div>
              `).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    `;

    attachItemClickListeners(content);
  }

  function attachItemClickListeners(container) {
    container.querySelectorAll('.js-item-click').forEach(el => {
      el.addEventListener('click', () => {
        try {
          const itemJson = el.getAttribute('data-item');
          if (itemJson) {
            const it = JSON.parse(itemJson);
            openItemDetailModal(it);
          }
        } catch (err) {
          console.error("Failed to parse item JSON", err);
        }
      });
    });
  }

  function openItemDetailModal(item) {
    const modal = document.getElementById('item-detail-modal');
    const titleEl = document.getElementById('modal-item-title');
    const badgeEl = document.getElementById('modal-item-badge');
    const bodyEl = document.getElementById('modal-item-body');

    titleEl.textContent = item.course_id || item.title || item.item_id;
    badgeEl.textContent = item.status_badge || item.item_type || 'PLAN ITEM';
    badgeEl.className = `badge ${item.status_badge === 'LOCKED' ? 'badge-neutral' : 'badge-success'}`;

    const citedCodes = (item.cited_kb_codes || []).map(c => `<code>${c}</code>`).join(' ') || 'None';
    const whyThis = item.reason?.why_this || item.skill_gap_reason || 'Academic curriculum requirement.';
    const targetSkills = (item.reason?.target_skills || []).map(s => `<span class="badge badge-info">${s}</span>`).join(' ') || 'None';

    bodyEl.innerHTML = `
      <div><strong>Item Type:</strong> ${item.item_type || 'Course/Task'}</div>
      <div><strong>Weekly Hours:</strong> ${item.hours_per_week || item.estimated_hours || 3.0} hrs/week</div>
      ${item.semester_number ? `<div><strong>Semester:</strong> Semester ${item.semester_number}</div>` : ''}
      <div><strong>Cited KB Codes:</strong> ${citedCodes}</div>
      ${item.pool_rule_status ? `<div style="color: #b45309;"><strong>Pool Selection Status:</strong> ⚠️ ${item.pool_rule_status}</div>` : ''}
      ${item.goal_emphasis ? `<div style="background: #e0f2fe; padding: 8px; border-radius: 4px; color: #0369a1;"><strong>Goal Emphasis:</strong> ${item.goal_emphasis}</div>` : ''}
      <div><strong>Structured Rationale:</strong><p style="margin: 4px 0; color: #475569;">${whyThis}</p></div>
      <div><strong>Target Skills:</strong><div style="margin-top: 4px; display:flex; gap:4px; flex-wrap:wrap;">${targetSkills}</div></div>
      <div style="border-top: 1px solid #e2e8f0; padding-top: 8px; margin-top: 6px;">
        <strong>Resources & Exercises:</strong>
        <p style="margin: 4px 0; font-size: 13px; color: #64748b;">Associated study materials and problem sets can be launched directly from the Daily Tasks view.</p>
      </div>
    `;

    modal.style.display = 'flex';
  }

  function closeModal() {
    document.getElementById('item-detail-modal').style.display = 'none';
  }
}
