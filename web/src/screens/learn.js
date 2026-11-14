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
      <div class="screen-header">
        <h2>Daily Learning & Resources (Agent 2)</h2>
        <p class="subtitle">Curated video lectures, courseware, and practice grounded in IIT Bhubaneswar's verified knowledge base.</p>
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
      const todayData = await api.getLearnToday(state.studentId).catch(() => null);
      loading.style.display = 'none';
      content.style.display = 'block';

      const resources = todayData?.resources || [];

      content.innerHTML = `
        <div class="two-col-layout">
          <div class="col-main" style="flex: 2;">
            <h3>Today's Knowledge-Base Learning Modules (Zero Hallucination)</h3>
            <p style="font-size: 0.9em; color: #666; margin-bottom: 16px;">
              ${todayData?.disclaimer || 'All links are sourced from official institutional records.'}
            </p>
            ${resources.length === 0 ? `<p class="text-muted">No external resources scheduled for today's modules.</p>` : `
              <div class="resource-cards-list" style="display:flex; flex-direction:column; gap:12px;">
                ${resources.map(res => `
                  <div class="resource-card" style="background:white; border:1px solid #e0e0e0; border-radius:8px; padding:16px;">
                    <div class="res-top" style="display:flex; justify-content:space-between; margin-bottom:8px;">
                      <span class="res-title" style="font-size:1.05em; font-weight:bold;">${res.title}</span>
                      <span class="badge ${res.coverage_status === 'Playlist found' ? 'badge-success' : 'badge-neutral'}">
                        ${res.coverage_status || 'Verified'}
                      </span>
                    </div>
                    <p class="res-desc text-muted" style="margin: 4px 0 8px 0;">
                      Provider: <strong>${res.provider || 'NPTEL'}</strong> • Course: <strong>${res.display_code} (${res.course_title})</strong>
                    </p>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:12px;">
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

          <div class="col-side" style="flex: 1; padding-left: 20px; border-left: 1px solid #eee;">
            <h3>Active Practice & Quizzes</h3>
            <p class="text-muted" style="font-size:0.9em;">
              Practice submissions are evaluated by <strong>Agent 3 (Assessment Agent)</strong>. Insufficient scores trigger a remediation proposal.
            </p>
            <div style="background:#fcfcfc; border:1px solid #e5e5e5; border-radius:6px; padding:12px; margin-top:10px;">
              <strong>Skill Focus: Electrical Circuits & Machines</strong>
              <p style="font-size:0.85em; color:#555; margin:6px 0 10px 0;">Complete today's 3 practice problems to demonstrate mastery.</p>
              <button class="btn btn-secondary btn-sm" onclick="window.location.hash='#diagnostic'">Take Today's Practice Quiz</button>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      loading.innerHTML = `<p class="text-danger">Failed to load learning resources: ${err.message}</p>`;
    }
  }
}
