export function renderMBA(container, state, navigate) {
  const studentId = state.studentId || 'STU_EE_2026_01';
  let activeTab = 'decide';
  let studentBranch = 'EE';

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header flex-between" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border-color); padding-bottom: 16px;">
        <div>
          <h2>Core to MBA: Management Pathway & Prep Buddy</h2>
          <p class="subtitle" style="color: var(--text-muted); margin: 4px 0 0 0;">
            Guiding B.Tech EE & MM undergraduates considering management careers. Built around your engineering advantage.
          </p>
        </div>
        <div style="display: flex; gap: 8px;">
          <select id="mba-branch-select" class="form-select" style="padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border-color);">
            <option value="EE" selected>B.Tech Electrical Engineering (EE)</option>
            <option value="MM">B.Tech Metallurgical & Materials (MM)</option>
          </select>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="tab-nav" style="display: flex; gap: 8px; border-bottom: 2px solid var(--border-color); margin-bottom: 20px; overflow-x: auto;">
        <button class="tab-btn active" data-tab="decide" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; border-bottom: 2px solid #1e3a8a; color: #1e3a8a;">1. Decide (5 Options)</button>
        <button class="tab-btn" data-tab="careermap" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">2. Career Map</button>
        <button class="tab-btn" data-tab="diagnostic" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">3. Diagnostic & Profile</button>
        <button class="tab-btn" data-tab="guidance" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">4. Weekly Guidance</button>
        <button class="tab-btn" data-tab="story" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">5. Story Builder</button>
        <button class="tab-btn" data-tab="shortlist" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">6. Mocks & Shortlist</button>
        <button class="tab-btn" data-tab="interview" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">7. PI & WAT</button>
        <button class="tab-btn" data-tab="replan" style="padding: 10px 16px; background: none; border: none; font-weight: 600; cursor: pointer; color: var(--text-muted);">8. Re-Plan & Pivot</button>
      </div>

      <!-- Tab Content Area -->
      <div id="mba-tab-content">
        <div class="loading-state">Loading Core to MBA pathway data...</div>
      </div>
    </div>
  `;

  // Attach event listeners for tabs and branch selector
  const branchSelect = document.getElementById('mba-branch-select');
  branchSelect.addEventListener('change', (e) => {
    studentBranch = e.target.value;
    loadActiveTab();
  });

  const tabButtons = container.querySelectorAll('.tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => {
        b.classList.remove('active');
        b.style.borderBottom = 'none';
        b.style.color = 'var(--text-muted)';
      });
      btn.classList.add('active');
      btn.style.borderBottom = '2px solid #1e3a8a';
      btn.style.color = '#1e3a8a';
      activeTab = btn.getAttribute('data-tab');
      loadActiveTab();
    });
  });

  loadActiveTab();

  async function loadActiveTab() {
    const content = document.getElementById('mba-tab-content');
    content.innerHTML = '<div class="loading-state">Loading...</div>';

    try {
      if (activeTab === 'decide') {
        await renderDecideTab(content);
      } else if (activeTab === 'careermap') {
        await renderCareerMapTab(content);
      } else if (activeTab === 'diagnostic') {
        await renderDiagnosticTab(content);
      } else if (activeTab === 'guidance') {
        await renderGuidanceTab(content);
      } else if (activeTab === 'story') {
        await renderStoryTab(content);
      } else if (activeTab === 'shortlist') {
        await renderShortlistTab(content);
      } else if (activeTab === 'interview') {
        await renderInterviewTab(content);
      } else if (activeTab === 'replan') {
        await renderReplanTab(content);
      }
    } catch (err) {
      content.innerHTML = `<div class="alert alert-error">Error loading tab content: ${err.message}</div>`;
    }
  }

  // 1. Decide Tab
  async function renderDecideTab(target) {
    const res = await fetch('/api/mba/decision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        student_year: 3,
        student_sem: 6,
        student_branch: studentBranch,
        student_cgpa: 8.0,
        backlogs: 0
      })
    });
    const data = await res.json();
    const options = data.options || [];

    let html = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">Side-by-Side Career Pathways Comparison</h3>
        <p style="color: var(--text-muted); font-size: 0.95rem;">
          Compare 5 distinct routes grounded strictly in verified institutional timelines.
          The buddy maintains strict neutrality and never pushes an MBA over core engineering.
        </p>
      </div>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
    `;

    options.forEach(opt => {
      html += `
        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white; display: flex; flex-direction: column; justify-content: space-between;">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
              <h4 style="margin: 0; color: #1e3a8a; font-size: 1.05rem;">${opt.name}</h4>
              <span class="badge badge-info" style="font-size: 0.75rem;">${opt.option}</span>
            </div>
            <div style="background: #f8fafc; padding: 10px; border-radius: 6px; margin: 8px 0; font-size: 0.85rem;">
              <strong>Current Phase:</strong> ${opt.timeline.current_phase}<br>
              <strong>Next Milestone:</strong> ${opt.timeline.next_milestone}<br>
              <strong>Capstone:</strong> ${opt.timeline.capstone}
            </div>
            <p style="font-size: 0.85rem; color: #334155; margin: 8px 0;"><strong>Trade-offs:</strong> ${opt.tradeoffs}</p>
            <div style="font-size: 0.82rem; color: #475569;">
              <strong>Requirements:</strong>
              <ul style="margin: 4px 0; padding-left: 18px;">
                ${opt.requirements.map(r => `<li>${r}</li>`).join('')}
              </ul>
            </div>
            ${opt.clashes && opt.clashes.length ? `
              <div style="margin-top: 8px; padding: 6px 10px; background: #fff1f2; border-left: 3px solid #e11d48; border-radius: 4px; font-size: 0.8rem; color: #9f1239;">
                <strong>Academic Clash Alert:</strong> ${opt.clashes.join('; ')}
              </div>
            ` : ''}
          </div>
          <button class="btn btn-outline btn-sm record-choice-btn" data-choice="${opt.option}" style="margin-top: 14px; width: 100%;">Select & Generate Roadmap</button>
        </div>
      `;
    });

    html += `</div>`;
    target.innerHTML = html;

    target.querySelectorAll('.record-choice-btn').forEach(btn => {
      btn.addEventListener('click', async (e) => {
        const choice = e.target.getAttribute('data-choice');
        const rRes = await fetch('/api/mba/decision', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            student_id: studentId,
            student_branch: studentBranch,
            chosen_option: choice
          })
        });
        const rData = await rRes.json();
        alert(`Decision recorded: ${choice}. Study plan regenerated!`);
        activeTab = 'guidance';
        loadActiveTab();
      });
    });
  }

  // 2. Career Map Tab
  async function renderCareerMapTab(target) {
    const res = await fetch(`/api/mba/career-map?branch=${studentBranch}&include_general=true`);
    const data = await res.json();
    const adv = data.engineering_advantage || {};

    let html = `
      <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
        <h4 style="margin: 0 0 6px 0; color: #1e3a8a;">Engineering Advantage: ${adv.branch || studentBranch}</h4>
        <p style="margin: 0 0 8px 0; font-size: 0.9rem; color: #1e293b;">${adv.management_translation || ''}</p>
        <div style="font-size: 0.85rem; color: #1e40af;">
          <strong>Core Strengths:</strong> ${adv.core_strengths ? adv.core_strengths.join(' • ') : ''}
        </div>
      </div>

      <h3 style="color: #1e3a8a; margin-bottom: 12px;">Verified Management Career Pathways</h3>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
    `;

    (data.paths || []).forEach(p => {
      html += `
        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <h4 style="margin: 0; color: #1e3a8a;">${p.name}</h4>
            <span class="badge badge-neutral" style="font-size: 0.75rem;">${p.branch}</span>
          </div>
          <p style="font-size: 0.88rem; color: #334155; margin: 8px 0;">${p.description}</p>
          <div style="font-size: 0.82rem; margin-bottom: 6px;"><strong>Typical Roles:</strong> ${p.typical_roles}</div>
          <div style="font-size: 0.82rem; margin-bottom: 6px;"><strong>Valued Skills:</strong> ${p.skills_valued}</div>
          <div style="font-size: 0.82rem; color: #475569;"><strong>Sectors:</strong> ${p.sectors}</div>
          <div style="font-size: 0.75rem; color: #94a3b8; margin-top: 8px; border-top: 1px solid #f1f5f9; padding-top: 6px;">Reviewed by: ${p.reviewed_by || 'Faculty Committee'}</div>
        </div>
      `;
    });

    html += `</div>`;
    target.innerHTML = html;
  }

  // 3. Diagnostic & Profile Tab
  async function renderDiagnosticTab(target) {
    target.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <h3 style="color: #1e3a8a; margin-top: 0;">Adaptive Aptitude Diagnostic</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted);">
            Short, adaptive check across QA, DILR, and VARC (max 15 items). Evaluates verbal gap and calculates estimated percentile.
          </p>
          <div id="diag-run-area" style="margin-top: 16px;">
            <button id="btn-start-diag" class="btn btn-primary" style="width: 100%;">Start Adaptive Diagnostic Check</button>
          </div>
        </div>

        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <h3 style="color: #1e3a8a; margin-top: 0;">Comprehensive Profile Audit</h3>
          <p style="font-size: 0.85rem; color: var(--text-muted);">
            Scores profile across 6 criteria against 4-level descriptive benchmarks in official rubrics.
          </p>
          <div id="profile-audit-results" style="margin-top: 16px;">
            <button id="btn-run-audit" class="btn btn-outline" style="width: 100%;">Evaluate Current Profile</button>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-start-diag').addEventListener('click', async () => {
      const area = document.getElementById('diag-run-area');
      area.innerHTML = '<div class="loading-state">Initializing test session...</div>';
      const sRes = await fetch('/api/mba/diagnostic/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ student_id: studentId, exam_id: 'MBA-EX-CAT' })
      });
      const sData = await sRes.json();
      renderDiagQuestion(area, sData);
    });

    document.getElementById('btn-run-audit').addEventListener('click', async () => {
      const pArea = document.getElementById('profile-audit-results');
      pArea.innerHTML = '<div class="loading-state">Evaluating profile rubrics...</div>';
      const aRes = await fetch('/api/mba/profile-audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          branch: studentBranch,
          cgpa: 8.1,
          backlogs: 0,
          projects: [{ title: 'Autonomous Power Flow Inverter', is_flagship: true }],
          internships: [{ title: 'Grid Operations Intern', duration_weeks: 8 }],
          leadership_roles: ['Technical Club Coordinator'],
          extracurriculars: ['Inter-college podium in Robotics'],
          work_ex_plan: 'Targeting 2-3 years in energy operations consulting before executive MBA'
        })
      });
      const aData = await aRes.json();
      renderAuditReport(pArea, aData);
    });

    function renderDiagQuestion(area, data) {
      if (data.completed) {
        area.innerHTML = `
          <div class="alert alert-success" style="padding: 12px; border-radius: 6px; font-size: 0.88rem;">
            <strong>Diagnostic Completed!</strong><br>
            Estimated Band: <strong>${data.estimated_percentile_band}</strong><br>
            Accuracy: ${data.overall_accuracy}%<br>
            Verbal Gap Flag: <strong>${data.verbal_gap_detected ? 'Active (Remediation Required)' : 'None'}</strong>
          </div>
        `;
        return;
      }
      const q = data.next_question;
      if (!q) return;

      area.innerHTML = `
        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; font-size: 0.88rem;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span class="badge badge-info">${q.section} • ${q.topic}</span>
            <span style="font-size: 0.75rem; color: #64748b;">Difficulty: ${q.difficulty}/3</span>
          </div>
          <p style="margin: 8px 0; font-weight: 500;">${q.stem}</p>
          ${q.option_a ? `
            <div style="display: flex; flex-direction: column; gap: 6px; margin: 10px 0;">
              <button class="btn btn-outline btn-sm diag-ans-btn" data-ans="a">A) ${q.option_a}</button>
              <button class="btn btn-outline btn-sm diag-ans-btn" data-ans="b">B) ${q.option_b}</button>
              <button class="btn btn-outline btn-sm diag-ans-btn" data-ans="c">C) ${q.option_c}</button>
              <button class="btn btn-outline btn-sm diag-ans-btn" data-ans="d">D) ${q.option_d}</button>
            </div>
          ` : `
            <div style="display: flex; gap: 8px; margin: 10px 0;">
              <input type="text" id="diag-numeric-input" class="form-input" placeholder="Enter answer..." style="padding: 6px 10px; border-radius: 4px; border: 1px solid #cbd5e1; flex: 1;">
              <button id="btn-submit-numeric" class="btn btn-primary btn-sm">Submit</button>
            </div>
          `}
        </div>
      `;

      area.querySelectorAll('.diag-ans-btn').forEach(b => {
        b.addEventListener('click', async (e) => {
          submitDiag(e.target.getAttribute('data-ans'));
        });
      });

      const numBtn = document.getElementById('btn-submit-numeric');
      if (numBtn) {
        numBtn.addEventListener('click', () => {
          const val = document.getElementById('diag-numeric-input').value;
          submitDiag(val);
        });
      }

      async function submitDiag(ans) {
        area.innerHTML = '<div class="loading-state">Evaluating answer...</div>';
        const aRes = await fetch('/api/mba/diagnostic/answer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: data.session_id,
            question_id: q.id,
            user_answer: ans
          })
        });
        const nextData = await aRes.json();
        renderDiagQuestion(area, nextData);
      }
    }

    function renderAuditReport(target, aData) {
      let h = `
        <div style="background: #f8fafc; border-radius: 6px; padding: 12px; margin-bottom: 12px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <strong style="color: #1e3a8a;">Composite Profile Rating:</strong>
            <span class="badge badge-success">${aData.total_score} / ${aData.max_score}</span>
          </div>
          <div style="font-size: 0.85rem; color: #334155; margin-top: 4px;"><strong>Tier:</strong> ${aData.tier}</div>
        </div>
        <div style="font-size: 0.8rem; display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      `;
      for (const [crit, cinfo] of Object.entries(aData.criteria_scores || {})) {
        h += `
          <div style="border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px 8px; background: white;">
            <strong>${crit}: Level ${cinfo.level}/4</strong>
            <div style="color: #64748b; font-size: 0.75rem; margin-top: 2px;">${cinfo.benchmark}</div>
          </div>
        `;
      }
      h += `</div>`;
      target.innerHTML = h;
    }
  }

  // 4. Weekly Guidance Tab
  async function renderGuidanceTab(target) {
    const res = await fetch('/api/mba/plan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        student_id: studentId,
        branch: studentBranch,
        current_cgpa: 8.0,
        backlogs: 0,
        free_hours_per_week: 14.0,
        total_weeks: 16,
        verbal_gap: true
      })
    });
    const plan = await res.json();
    const weeks = plan.weekly_schedule || [];

    let html = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">16-Week Balanced Preparation Plan (No Rigid Timetables)</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          Weekly focus goals and hours budgets that automatically adjust around mid-sems and end-sems to protect your CGPA.
        </p>
      </div>
      <div style="display: flex; flex-direction: column; gap: 12px;">
    `;

    weeks.forEach(w => {
      const isExam = w.is_exam_week;
      const bColor = isExam ? '#fff1f2' : '#ffffff';
      const borderC = isExam ? '#f43f5e' : 'var(--border-color)';

      html += `
        <div class="card" style="border: 1px solid ${borderC}; border-radius: 8px; padding: 14px; background: ${bColor};">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <strong style="color: #1e3a8a; font-size: 0.98rem;">Week ${w.week_number}: ${w.phase_name}</strong>
            ${isExam ? '<span class="badge badge-error" style="font-size: 0.75rem;">Exam Week (CGPA Protection)</span>' : '<span class="badge badge-info" style="font-size: 0.75rem;">Standard Week</span>'}
          </div>
          ${w.alert ? `<div style="background: #ffe4e6; color: #9f1239; padding: 6px 10px; border-radius: 4px; font-size: 0.8rem; margin-bottom: 8px;">${w.alert}</div>` : ''}
          <div style="display: flex; gap: 16px; font-size: 0.85rem; color: #475569; margin-bottom: 8px; background: #f8fafc; padding: 6px 10px; border-radius: 4px;">
            <span>Core Courses: <strong>${w.hours_budget.core_courses}h</strong></span>
            <span>QA: <strong>${w.hours_budget.qa}h</strong></span>
            <span>DILR: <strong>${w.hours_budget.dilr}h</strong></span>
            <span>VARC: <strong>${w.hours_budget.varc}h</strong></span>
            <span>Mocks: <strong>${w.hours_budget.mocks}h</strong></span>
          </div>
          <div style="font-size: 0.85rem;">
            <strong>Weekly Focus Goals:</strong>
            <ul style="margin: 4px 0; padding-left: 18px;">
              ${w.focus_goals.map(g => `<li>${g}</li>`).join('')}
            </ul>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    target.innerHTML = html;
  }

  // 5. Story Builder Tab
  async function renderStoryTab(target) {
    target.innerHTML = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">Story Builder & Interview Narrative Coaching</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          Turn technical projects into quantifiable business narratives.
          <strong>Strict Coaching Rule:</strong> The buddy scores and probes; you author your own narrative (zero ghostwriting).
        </p>
      </div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <label style="display: block; font-weight: 600; margin-bottom: 6px; font-size: 0.9rem;">Story Prompt</label>
          <select id="story-kind-select" class="form-select" style="width: 100%; padding: 8px; border-radius: 6px; margin-bottom: 12px; border: 1px solid var(--border-color);">
            <option value="why_mba">Why MBA after Engineering? (Motivation & Transition)</option>
            <option value="why_not_core">Why not stay in Core Engineering? (Domain Logic)</option>
            <option value="project_story">Engineering Project to Business Impact (STAR)</option>
          </select>
          <label style="display: block; font-weight: 600; margin-bottom: 6px; font-size: 0.9rem;">Your Draft</label>
          <textarea id="story-text-input" rows="8" class="form-input" style="width: 100%; padding: 10px; border-radius: 6px; border: 1px solid var(--border-color); font-family: inherit;" placeholder="Draft your story here... Include problem, action, tangible numbers, and engineering context."></textarea>
          <button id="btn-eval-story" class="btn btn-primary" style="margin-top: 10px; width: 100%;">Evaluate Draft & Get Probing Feedback</button>
        </div>
        <div id="story-eval-result" class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <div style="color: var(--text-muted); font-size: 0.9rem;">Submit a draft to receive rubric feedback and probing questions.</div>
        </div>
      </div>
    `;

    document.getElementById('btn-eval-story').addEventListener('click', async () => {
      const kind = document.getElementById('story-kind-select').value;
      const text = document.getElementById('story-text-input').value;
      const resArea = document.getElementById('story-eval-result');
      if (!text || text.trim().length < 10) {
        alert('Please enter at least a few sentences to evaluate.');
        return;
      }
      resArea.innerHTML = '<div class="loading-state">Scoring against interview rubric...</div>';

      const res = await fetch('/api/mba/story/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          kind: kind,
          text: text,
          branch: studentBranch
        })
      });
      const data = await res.json();
      renderStoryFeedback(resArea, data);
    });

    function renderStoryFeedback(target, d) {
      let h = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <strong style="color: #1e3a8a;">Rubric Score: ${d.total_score} / ${d.max_score}</strong>
          <span class="badge badge-info">Version ${d.version}</span>
        </div>
        <div style="font-size: 0.82rem; margin-bottom: 12px; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
      `;
      for (const [crit, sc] of Object.entries(d.scores || {})) {
        h += `<div style="background: #f8fafc; padding: 4px 8px; border-radius: 4px;"><strong>${crit}:</strong> ${sc}/4</div>`;
      }
      h += `
        </div>
        <div style="background: #eff6ff; border-left: 3px solid #3b82f6; padding: 10px; border-radius: 4px; margin-bottom: 12px;">
          <strong style="color: #1e40af; font-size: 0.85rem;">Probing Questions to Answer in Next Draft:</strong>
          <ul style="margin: 6px 0; padding-left: 18px; font-size: 0.82rem; color: #1e293b;">
            ${(d.probing_questions || []).map(q => `<li>${q}</li>`).join('')}
          </ul>
        </div>
        <div style="font-size: 0.78rem; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 8px;">
          ${d.coaching_notice}
        </div>
      `;
      target.innerHTML = h;
    }
  }

  // 6. Shortlist & Mocks Tab
  async function renderShortlistTab(target) {
    const sRes = await fetch(`/api/mba/shortlist/${studentId}?category=GEN&preliminary_percentile=94.0`);
    const sData = await sRes.json();

    let html = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">Mocks & Verified Shortlist Tiering</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          Calibrated percentile band requires $\\ge 2$ full mocks. Tiers into Reach, Target, and Safe based strictly on verified cutoffs.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <h4 style="margin-top: 0; color: #1e3a8a;">Log Full Mock Result</h4>
          <input type="text" id="mock-name-input" class="form-input" placeholder="Mock Name (e.g. AIMCAT 2026-03)" style="width: 100%; padding: 6px 10px; margin-bottom: 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
          <input type="number" id="mock-score-input" class="form-input" placeholder="Raw Score (e.g. 85)" style="width: 100%; padding: 6px 10px; margin-bottom: 8px; border: 1px solid #cbd5e1; border-radius: 4px;">
          <input type="number" id="mock-p-input" class="form-input" placeholder="Percentile (e.g. 96.5)" style="width: 100%; padding: 6px 10px; margin-bottom: 12px; border: 1px solid #cbd5e1; border-radius: 4px;">
          <button id="btn-save-mock" class="btn btn-primary" style="width: 100%;">Record Mock & Recalibrate</button>
        </div>

        <div>
          <div style="background: #f8fafc; border-radius: 6px; padding: 12px; margin-bottom: 16px; border: 1px solid #e2e8f0;">
            <div style="display: flex; justify-content: space-between;">
              <span>Predicted Score Band: <strong>${sData.estimated_band}</strong></span>
              <span class="badge ${sData.calibrated ? 'badge-success' : 'badge-neutral'}">${sData.calibrated ? 'Calibrated (Empirical)' : 'Preliminary'}</span>
            </div>
            <div style="font-size: 0.78rem; color: #64748b; margin-top: 4px;">${sData.disclaimer}</div>
          </div>

          <!-- Tiers -->
          <div style="display: flex; flex-direction: column; gap: 12px;">
            <div style="border-left: 4px solid #ef4444; background: white; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 6px;">
              <strong style="color: #dc2626;">Reach Tier (High-Band Match):</strong>
              <div style="font-size: 0.85rem; margin-top: 6px;">
                ${(sData.reach || []).map(r => `<div>• <strong>${r.institution_name}</strong> (${r.programme_name}) - Cutoff: ${r.cutoff_percentile}%ile</div>`).join('') || 'None in range'}
              </div>
            </div>
            <div style="border-left: 4px solid #3b82f6; background: white; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 6px;">
              <strong style="color: #2563eb;">Target Tier (Band Spans Cutoff):</strong>
              <div style="font-size: 0.85rem; margin-top: 6px;">
                ${(sData.target || []).map(r => `<div>• <strong>${r.institution_name}</strong> (${r.programme_name}) - Cutoff: ${r.cutoff_percentile}%ile</div>`).join('') || 'None in range'}
              </div>
            </div>
            <div style="border-left: 4px solid #10b981; background: white; padding: 10px 14px; border: 1px solid #e2e8f0; border-radius: 6px;">
              <strong style="color: #059669;">Safe Tier (Low-Band Exceeds Cutoff):</strong>
              <div style="font-size: 0.85rem; margin-top: 6px;">
                ${(sData.safe || []).map(r => `<div>• <strong>${r.institution_name}</strong> (${r.programme_name}) - Cutoff: ${r.cutoff_percentile}%ile</div>`).join('') || 'None in range'}
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    target.innerHTML = html;
    document.getElementById('btn-save-mock').addEventListener('click', async () => {
      const name = document.getElementById('mock-name-input').value;
      const score = parseFloat(document.getElementById('mock-score-input').value) || 0;
      const p = parseFloat(document.getElementById('mock-p-input').value) || 0;
      if (!p) {
        alert('Please enter percentile.');
        return;
      }
      await fetch('/api/mba/mocks/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          exam_id: 'MBA-EX-CAT',
          mock_name: name || 'Mock Test',
          raw_score: score,
          percentile: p
        })
      });
      alert('Mock logged. Recalibrating band and shortlist...');
      renderShortlistTab(target);
    });
  }

  // 7. Interview & WAT Tab
  async function renderInterviewTab(target) {
    const res = await fetch(`/api/mba/interview/topics?branch=${studentBranch}`);
    const data = await res.json();

    let html = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">Branch Technical Viva & General Interview Preparation</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          B-School panels expect engineers to understand fundamental engineering concepts in techno-commercial terms.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div>
          <h4 style="color: #1e3a8a; margin-top: 0;">${studentBranch} Technical Interview Topics</h4>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${(data.topics || []).map(t => `
              <div style="background: white; border: 1px solid var(--border-color); border-radius: 6px; padding: 10px;">
                <strong style="color: #1e293b; font-size: 0.9rem;">${t.topic}</strong>
                <div style="font-size: 0.8rem; color: #64748b; margin-top: 2px;">${t.subtopics || ''}</div>
                <div style="font-size: 0.78rem; color: #0284c7; margin-top: 4px;">${t.interview_level_notes || ''}</div>
              </div>
            `).join('')}
          </div>
        </div>

        <div>
          <h4 style="color: #1e3a8a; margin-top: 0;">Written Ability Test (WAT) Practice</h4>
          <div style="display: flex; flex-direction: column; gap: 8px;">
            ${(data.wat_topics || []).map(w => `
              <div style="background: white; border: 1px solid var(--border-color); border-radius: 6px; padding: 10px;">
                <strong style="font-size: 0.88rem;">${w.question}</strong>
                <div style="font-size: 0.8rem; color: #475569; margin-top: 4px;"><strong>Target Benchmark:</strong> ${w.what_good_looks_like}</div>
              </div>
            `).join('')}
          </div>
        </div>
      </div>
    `;
    target.innerHTML = html;
  }

  // 8. Re-Plan & Pivot Tab
  async function renderReplanTab(target) {
    target.innerHTML = `
      <div style="margin-bottom: 16px;">
        <h3 style="color: #1e3a8a;">Post-Result Analysis & Lateral Switch-Back to Core</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">
          When entrance results arrive, formulate realistic paths without sugarcoating or despair.
          Or seamlessly pivot back to Core Engineering with <strong>100% of your diagnostic and test evidence preserved</strong>.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <h4 style="color: #1e3a8a; margin-top: 0;">Analyze Actual Exam Result</h4>
          <label style="display: block; font-size: 0.85rem; margin-bottom: 4px;">Actual CAT Percentile Achieved</label>
          <input type="number" id="actual-p-input" class="form-input" placeholder="e.g. 84.5" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #cbd5e1; margin-bottom: 12px;">
          <button id="btn-eval-result" class="btn btn-outline" style="width: 100%;">Formulate Strategic Options</button>
          <div id="replan-result-area" style="margin-top: 14px;"></div>
        </div>

        <div class="card" style="border: 1px solid var(--border-color); border-radius: 8px; padding: 16px; background: white;">
          <h4 style="color: #1e3a8a; margin-top: 0;">Lateral Switch-Back to Core Route</h4>
          <p style="font-size: 0.85rem; color: #475569;">
            Decided to prioritize core engineering campus placements or higher studies?
            The system switches your active track, shifts focus goals, and generates an official plan version diff.
          </p>
          <select id="switch-target-select" class="form-select" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #cbd5e1; margin-bottom: 12px;">
            <option value="core_industry">Core Engineering Industry & PSU Placement Track</option>
            <option value="core_research">Core Research Mentorship Track</option>
            <option value="core_mtech">GATE -> M.Tech Higher Studies Track</option>
          </select>
          <button id="btn-switch-core" class="btn btn-primary" style="width: 100%;">Execute Switch (100% Evidence Preserved)</button>
          <div id="switch-diff-area" style="margin-top: 14px;"></div>
        </div>
      </div>
    `;

    document.getElementById('btn-eval-result').addEventListener('click', async () => {
      const p = parseFloat(document.getElementById('actual-p-input').value);
      if (!p) {
        alert('Enter actual percentile.');
        return;
      }
      const rArea = document.getElementById('replan-result-area');
      rArea.innerHTML = '<div class="loading-state">Analyzing options...</div>';
      const res = await fetch('/api/mba/replan/result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          exam_id: 'MBA-EX-CAT',
          actual_percentile: p,
          category: 'GEN'
        })
      });
      const d = await res.json();
      rArea.innerHTML = `
        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; font-size: 0.85rem;">
          <strong style="color: #1e3a8a;">${d.status}</strong>
          <p style="margin: 6px 0; color: #334155;">${d.recommendation}</p>
          <div style="font-weight: 600; margin-top: 6px;">Strategic Actions:</div>
          <ul style="margin: 4px 0; padding-left: 18px;">
            ${(d.recommended_actions || []).map(a => `<li>${a}</li>`).join('')}
          </ul>
        </div>
      `;
    });

    document.getElementById('btn-switch-core').addEventListener('click', async () => {
      const route = document.getElementById('switch-target-select').value;
      const sArea = document.getElementById('switch-diff-area');
      sArea.innerHTML = '<div class="loading-state">Pivoting track & generating version diff...</div>';
      const res = await fetch('/api/mba/replan/switch-back', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          student_id: studentId,
          target_route: route,
          current_plan_version: 1,
          reason: 'Student decided to prioritize core engineering placement after exam results.'
        })
      });
      const d = await res.json();
      sArea.innerHTML = `
        <div class="alert alert-success" style="padding: 12px; border-radius: 6px; font-size: 0.85rem;">
          <strong>${d.message}</strong>
          <div style="margin-top: 6px; font-weight: 600;">Plan Version Diff (What Changed & Why):</div>
          <ul style="margin: 4px 0; padding-left: 18px;">
            ${(d.diff.what_changed || []).map(c => `<li>${c}</li>`).join('')}
          </ul>
        </div>
      `;
    });
  }
}
