import { api } from '../api/client.js';
import { esc, badge, tagBadges, TAG_LABELS, errorBox } from '../ui.js';

export function renderOnboarding(container, state, navigate) {
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header">
        <h2>Choose a student profile and a goal</h2>
        <p class="subtitle">75 synthetic, anonymised IIT Bhubaneswar B.Tech EE and MME profiles (Years 1-4). Career tracks (SDE, Data Analyst, AI/ML), core, higher studies, MBA, UPSC and startup are all first-class goals.</p>
      </div>
      <div id="ob-body" class="loading-state">Loading profiles...</div>
    </div>`;
  load();

  async function load() {
    const body = document.getElementById('ob-body');
    try {
      const [data, goals] = await Promise.all([api.listStudents(), api.listGoals()]);
      const students = data.students;
      const families = [...new Set(students.map((s) => s.goal_family))].sort();
      body.className = '';
      body.innerHTML = `
        <div class="grid-3">
          <div class="card"><div class="muted small">Profiles</div><div class="kpi">${data.count}</div></div>
          <div class="card"><div class="muted small">EE / MME</div><div class="kpi">${students.filter((s) => s.programme_id === 'BTECH_EE').length} / ${students.filter((s) => s.programme_id !== 'BTECH_EE').length}</div></div>
          <div class="card"><div class="muted small">Edge-case profiles</div><div class="pill-row small">${Object.entries(data.edge_case_counts).map(([k, v]) => badge(`${TAG_LABELS[k] || k}: ${v}`, 'warning')).join(' ')}</div></div>
        </div>
        <div class="filters">
          <select id="f-prog"><option value="">All branches</option><option value="BTECH_EE">EE</option><option value="BTECH_MM">MME</option></select>
          <select id="f-year"><option value="">All years</option>${[1, 2, 3, 4].map((y) => `<option value="${y}">Year ${y}</option>`).join('')}</select>
          <select id="f-family"><option value="">All goals</option>${families.map((f) => `<option>${esc(f)}</option>`).join('')}</select>
          <select id="f-tag"><option value="">All edge cases</option>${Object.keys(data.edge_case_counts).map((t) => `<option value="${t}">${esc(TAG_LABELS[t] || t)}</option>`).join('')}</select>
          <input id="f-text" placeholder="Search name or id" />
        </div>
        <div style="overflow-x:auto;"><table class="table"><thead><tr><th>Student</th><th>Branch</th><th>Sem</th><th>CGPA</th><th>Goal</th><th>Caps</th><th>Edge cases</th><th></th></tr></thead><tbody id="ob-rows"></tbody></table></div>
        <div id="ob-picked" style="margin-top:18px;"></div>
        <details style="margin-top:18px;"><summary><strong>Or onboard a new student</strong></summary>
          <form id="new-form" class="form-grid" style="margin-top:12px;">
            <div class="form-group"><label>Student id *</label><input id="n-id" required value="NEW_STU_001" /></div>
            <div class="form-group"><label>Name *</label><input id="n-name" required value="New Student" /></div>
            <div class="form-group"><label>Branch *</label><select id="n-prog"><option value="BTECH_EE">B.Tech EE</option><option value="BTECH_MM">B.Tech MME</option></select></div>
            <div class="form-group"><label>Current semester *</label><select id="n-sem">${[1, 2, 3, 4, 5, 6, 7, 8].map((s) => `<option ${s === 3 ? 'selected' : ''}>${s}</option>`).join('')}</select></div>
            <div class="form-group"><label>CGPA</label><input id="n-cgpa" type="number" step="0.01" min="0" max="10" value="8.00" /></div>
            <div class="form-group"><label>Active backlogs</label><input id="n-back" type="number" min="0" max="10" value="0" /></div>
            <div class="form-group"><label>Goal *</label><select id="n-goal"></select></div>
            <div class="form-group"><label>Weekly self-study cap (hours)</label><input id="n-hours" type="number" min="2" max="60" value="16" /></div>
            <div class="form-group"><label>Credit cap (optional)</label><input id="n-cap" type="number" min="8" max="32" placeholder="none" /></div>
            <div class="form-group"><label>Declared interests (comma separated; weak evidence)</label><input id="n-int" placeholder="e.g. Machine learning, Power electronics" /></div>
            <div class="form-group full-width"><label>Completed course codes (comma separated; leave blank if no backlog)</label><input id="n-done" placeholder="e.g. MA1L001, EE1L001" /></div>
            <div class="form-actions full-width"><button class="btn btn-primary" type="submit">Create profile and build roadmap</button></div>
          </form><div id="new-msg"></div>
        </details>`;

      const goalOpts = (prog) => goals.goals.filter((g) => !(prog === 'BTECH_EE' && g.goal_id.startsWith('GOAL_MM_')) && !(prog !== 'BTECH_EE' && g.goal_id.startsWith('GOAL_EE_')) && !g.legacy)
        .map((g) => `<option value="${g.goal_id}">${esc(g.family)} - ${esc(g.name)}${g.track_id ? ' (career track)' : ''}</option>`).join('');
      const nProg = document.getElementById('n-prog');
      const fillGoals = () => { document.getElementById('n-goal').innerHTML = goalOpts(nProg.value); };
      nProg.addEventListener('change', fillGoals); fillGoals();

      const rowsEl = document.getElementById('ob-rows');
      const draw = () => {
        const fp = document.getElementById('f-prog').value, fy = document.getElementById('f-year').value;
        const ff = document.getElementById('f-family').value, ft = document.getElementById('f-tag').value;
        const fx = document.getElementById('f-text').value.toLowerCase();
        const list = students.filter((s) => (!fp || s.programme_id === fp) && (!fy || String(s.year) === fy) && (!ff || s.goal_family === ff)
          && (!ft || s.edge_case_tags.includes(ft)) && (!fx || (s.name + s.student_id).toLowerCase().includes(fx)));
        rowsEl.innerHTML = list.map((s) => `<tr class="clickable" data-id="${esc(s.student_id)}">
          <td><strong>${esc(s.name)}</strong><br/><span class="muted small">${esc(s.student_id)}</span></td>
          <td>${s.programme_id === 'BTECH_EE' ? 'EE' : 'MME'}</td><td>${s.current_semester}</td><td>${Number(s.cgpa).toFixed(2)}${s.backlogs ? ` ${badge(s.backlogs + ' backlog', 'error')}` : ''}</td>
          <td>${badge(s.goal_family, 'info')}<br/><span class="small">${esc(s.goal_name)}</span></td>
          <td class="small">${s.weekly_hours_cap ?? '-'} h/wk${s.credit_cap ? `<br/>${s.credit_cap} cr` : ''}</td>
          <td>${tagBadges(s.edge_case_tags)}</td><td><button class="btn btn-primary btn-sm">Select</button></td></tr>`).join('')
          || '<tr><td colspan="8" class="muted">No profile matches these filters.</td></tr>';
        rowsEl.querySelectorAll('tr.clickable').forEach((tr) => tr.addEventListener('click', () => pick(tr.dataset.id)));
      };
      ['f-prog', 'f-year', 'f-family', 'f-tag'].forEach((id) => document.getElementById(id).addEventListener('change', draw));
      document.getElementById('f-text').addEventListener('input', draw);
      draw();

      async function pick(id, goalId = null) {
        const box = document.getElementById('ob-picked');
        box.innerHTML = '<div class="loading-state">Loading profile and building a validated roadmap...</div>';
        try {
          const p = await api.selectStudent(id, goalId);
          state.studentId = id; state.profile = p; localStorage.setItem('ebuddy_student_id', id); state.refreshPill();
          box.innerHTML = `<div class="card">
            <h3>${esc(p.name)} <span class="muted small">${esc(p.student_id)}</span></h3>
            <p>${esc(p.programme_id)} • Year ${p.year}, Semester ${p.current_semester} • CGPA ${Number(p.cgpa).toFixed(2)} • ${p.completed_count} courses completed${p.backlog_courses.length ? ` • backlog: ${esc(p.backlog_courses.join(', '))}` : ''}</p>
            <p>Goal: <strong>${esc(p.goal_name)}</strong> ${badge(p.goal_family, 'info')} ${p.previous_goal_ids.length ? `<span class="muted small">(previously ${esc(p.previous_goal_ids.join(', '))})</span>` : ''}</p>
            <p class="small">Evidence ledger: ${badge(p.evidence_by_tier.strong + ' strong', 'success')} ${badge(p.evidence_by_tier.medium + ' medium', 'info')} ${badge(p.evidence_by_tier.weak + ' weak (self-declared)', 'warning')} • Weekly cap ${p.weekly_hours_cap ?? 'not set'} h${p.credit_cap ? ` • Credit cap ${p.credit_cap}` : ''} • Roadmap v${p.plan_version}</p>
            <p class="pill-row" style="margin:6px 0;">${tagBadges(p.edge_case_tags)}</p>
            <div class="filters"><select id="sw-goal">${goalOpts(p.programme_id)}</select><button class="btn btn-outline" id="sw-btn">Switch goal (keeps evidence)</button>
              <a class="btn btn-primary" href="#plan">Open roadmap →</a><a class="btn btn-outline" href="#diagnostic">Take diagnostic</a></div></div>`;
          document.getElementById('sw-goal').value = p.goal_id;
          document.getElementById('sw-btn').addEventListener('click', () => pick(id, document.getElementById('sw-goal').value));
        } catch (err) { box.innerHTML = errorBox(err); }
      }
      if (state.studentId) pick(state.studentId);

      document.getElementById('new-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const val = (id) => document.getElementById(id).value.trim();
        const msg = document.getElementById('new-msg');
        try {
          const p = await api.createStudent({
            student_id: val('n-id'), name: val('n-name'), programme_id: val('n-prog'), current_semester: parseInt(val('n-sem'), 10),
            cgpa: parseFloat(val('n-cgpa')) || null, backlogs: parseInt(val('n-back'), 10) || 0, goal_id: val('n-goal'),
            weekly_hours_cap: parseFloat(val('n-hours')) || null, credit_cap: parseFloat(val('n-cap')) || null,
            interests: val('n-int') ? val('n-int').split(',').map((x) => x.trim()).filter(Boolean) : [],
            completed_course_ids: val('n-done') ? val('n-done').split(',').map((x) => x.trim().toUpperCase()).filter(Boolean) : null,
            aims: val('n-int') ? `Interested in ${val('n-int')}` : null
          });
          state.studentId = p.student_id; state.profile = p; localStorage.setItem('ebuddy_student_id', p.student_id); state.refreshPill();
          navigate('#plan');
        } catch (err) { msg.innerHTML = errorBox(err); }
      });
    } catch (err) { body.innerHTML = errorBox(err); }
  }
}
