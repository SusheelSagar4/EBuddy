import { api } from '../api/client.js';
import { esc, badge, errorBox, md, tagBadges } from '../ui.js';

const result = (r) => `<div class="alert alert-success"><strong>Re-processed immediately:</strong> roadmap v${r.old_version} → v${r.new_version} ${r.validation_passed === false ? badge('validation failed', 'error') : badge('validated', 'success')}<br/>${md(r.what_changed_and_why || r.summary || '')}</div>`;

export function renderAdmin(container, state) {
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header"><h2>Admin and data</h2>
        <p class="subtitle">View and edit student profiles, diagnostic scores and course data. Every edit re-runs the deterministic pipeline at once and stores a new roadmap version with the reason. Edits made in Adminer are picked up within about 2 seconds.</p></div>
      <div id="ad-status" class="loading-state">Loading system status...</div>
      <div class="filters"><a class="btn btn-outline" href="/adminer" target="_blank" rel="noopener">Open Adminer (database) ↗</a><a class="btn btn-outline" href="/docs" target="_blank" rel="noopener">API docs ↗</a>
        <button class="btn btn-danger" id="ad-reset">Reset everything to the original seed</button></div>
      <div id="ad-reset-msg"></div>

      <h3 style="margin-top:16px;">Student profile and scores</h3>
      <div class="filters"><select id="ad-student"></select><button class="btn btn-outline" id="ad-load">Load</button></div>
      <div id="ad-student-body"></div>

      <h3 style="margin-top:16px;">Course data</h3>
      <div class="filters"><input id="ad-course-q" class="inline-input" placeholder="Search course code or title" /><button class="btn btn-outline" id="ad-course-search">Search</button></div>
      <div id="ad-courses"></div>

      <h3 style="margin-top:16px;">Academic rules (unsourced baselines)</h3>
      <div id="ad-rules"></div>

      <h3 style="margin-top:16px;">Re-processing log</h3>
      <div class="filters"><button class="btn btn-outline btn-sm" id="ad-log-refresh">Refresh</button></div>
      <div id="ad-log"></div>
    </div>`;

  const $ = (id) => document.getElementById(id);

  async function status() {
    try {
      const o = await api.adminOverview();
      const rc = o.database.row_counts || {};
      $('ad-status').className = '';
      $('ad-status').innerHTML = `<div class="grid-3">
        <div class="card"><div class="muted small">Database</div><div>${o.database.available ? badge('connected', 'success') : badge('not reachable - running from seed files', 'warning')}</div>
          <div class="small muted">${Object.entries(rc).map(([k, v]) => `${esc(k)}: ${v}`).join(' • ') || 'no row counts'}</div></div>
        <div class="card"><div class="muted small">LLM (via LiteLLM)</div><div>${o.llm.mode === 'live' ? badge('live: ' + o.llm.model, 'success') : badge('offline deterministic mode', 'warning')}</div>
          <div class="small muted">timeout ${o.llm.timeout_seconds}s • retries ${o.llm.max_retries} • breaker ${o.llm.circuit_breaker_open ? 'OPEN' : 'closed'} • model, key and endpoint come from the environment only</div></div>
        <div class="card"><div class="muted small">Knowledge base</div><div class="small">${o.kb.courses} courses • ${o.kb.skills} skills • ${o.kb.goals} goals • ${o.kb.personas} personas</div>
          <div class="small muted">${Object.entries(o.tracks).map(([k, v]) => `${esc(k)}: ${v.phases} phases, ${v.resources} resources, ${v.events} events`).join(' • ')}</div></div>
        <div class="card"><div class="muted small">Profiles</div><div class="small">${o.profiles.total_profiles || '-'} synthetic • loaded in memory ${o.memory.students_loaded} • plans ${o.memory.plans}</div>
          <div class="small muted">${Object.entries(o.profiles.edge_case_counts || {}).map(([k, v]) => `${esc(k)}: ${v}`).join(' • ')}</div></div></div>`;
    } catch (err) { $('ad-status').innerHTML = errorBox(err); }
  }

  async function students() {
    const d = await api.listStudents();
    $('ad-student').innerHTML = d.students.map((s) => `<option value="${esc(s.student_id)}" ${s.student_id === state.studentId ? 'selected' : ''}>${esc(s.name)} - ${esc(s.student_id)} (${esc(s.goal_family)})</option>`).join('');
  }

  async function loadStudent(msg = '') {
    const id = $('ad-student').value; const box = $('ad-student-body');
    box.innerHTML = '<div class="loading-state">Loading...</div>';
    try {
      const [d, goals] = await Promise.all([api.adminStudent(id), api.listGoals()]);
      const s = d.student;
      box.innerHTML = `${msg}<div class="card">
        <div class="pill-row"><strong>${esc(s.name)}</strong> ${badge(s.programme_id)} ${badge('roadmap v' + d.plan_version)} ${tagBadges(s.edge_case_tags)}</div>
        <div class="form-grid" style="margin-top:10px;">
          <div class="form-group"><label>CGPA</label><input id="e-cgpa" type="number" step="0.01" min="0" max="10" value="${s.cgpa ?? ''}" /></div>
          <div class="form-group"><label>Active backlogs</label><input id="e-back" type="number" min="0" max="10" value="${s.backlogs}" /></div>
          <div class="form-group"><label>Current semester</label><input id="e-sem" type="number" min="1" max="8" value="${s.current_semester}" /></div>
          <div class="form-group"><label>Weekly hours cap</label><input id="e-hours" type="number" min="1" max="60" value="${d.weekly_hours_cap ?? ''}" /></div>
          <div class="form-group"><label>Credit cap (blank = none)</label><input id="e-cap" type="number" min="8" max="32" value="${d.credit_cap ?? ''}" /></div>
          <div class="form-group"><label>Goal</label><select id="e-goal">${goals.goals.filter((g) => !g.legacy).map((g) => `<option value="${g.goal_id}" ${g.goal_id === d.goal_id ? 'selected' : ''}>${esc(g.family)} - ${esc(g.name)}</option>`).join('')}</select></div>
        </div><div class="filters"><button class="btn btn-primary" id="e-save">Save profile and re-process</button></div></div>
        <details open style="margin-top:10px;"><summary><strong>Diagnostic and assessment scores (${d.evidence.length})</strong></summary>
          <div style="overflow-x:auto;max-height:340px;overflow-y:auto;"><table class="table"><tr><th>Skill</th><th>Source</th><th>Tier</th><th>Score</th><th></th></tr>
          ${d.evidence.map((e) => `<tr><td>${esc(e.skill_name)}<br/><span class="small muted">${esc(e.notes || '')}</span></td><td>${esc(e.source_type)}</td><td>${badge(e.reliability_tier, e.reliability_tier === 'strong' ? 'success' : 'warning')}</td>
            <td><input type="number" min="0" max="100" step="0.1" value="${e.score}" class="inline-input" style="width:80px;" data-ev="${esc(e.evidence_id)}" /></td><td><button class="btn btn-outline btn-sm" data-save-ev="${esc(e.evidence_id)}">Save</button></td></tr>`).join('')}</table></div></details>
        <details style="margin-top:8px;"><summary><strong>Transcript (${d.transcript.length} rows)</strong></summary><div class="small">${d.transcript.map((t) => `${esc(t.course_id)} ${t.is_backlog ? badge('backlog F', 'error') : esc(t.grade)}`).join(' • ') || 'No transcript rows (new or first-semester student).'}</div></details>`;
      $('e-save').addEventListener('click', async () => {
        const num = (id) => { const v = $(id).value; return v === '' ? null : parseFloat(v); };
        const payload = { cgpa: num('e-cgpa'), backlogs: num('e-back'), current_semester: num('e-sem'), weekly_hours_cap: num('e-hours'), goal_id: $('e-goal').value };
        if (num('e-cap') !== null) payload.credit_cap = num('e-cap'); else if (d.credit_cap != null) payload.clear_credit_cap = true;
        try { const r = await api.adminEditStudent(id, payload); if (id === state.studentId) { state.profile = await api.getOverview(id); state.refreshPill(); } await loadStudent(result(r.reprocess)); log(); status(); }
        catch (err) { box.insertAdjacentHTML('afterbegin', errorBox(err)); }
      });
      box.querySelectorAll('button[data-save-ev]').forEach((b) => b.addEventListener('click', async () => {
        const inp = box.querySelector(`input[data-ev="${b.dataset.saveEv}"]`);
        try { const r = await api.adminEditEvidence(id, { evidence_id: b.dataset.saveEv, score: parseFloat(inp.value) }); await loadStudent(result(r.reprocess)); log(); }
        catch (err) { box.insertAdjacentHTML('afterbegin', errorBox(err)); }
      }));
    } catch (err) { box.innerHTML = errorBox(err); }
  }

  async function courses(msg = '') {
    const box = $('ad-courses');
    try {
      const d = await api.adminCourses($('ad-course-q').value);
      box.innerHTML = `${msg}<div style="overflow-x:auto;"><table class="table"><tr><th>Code</th><th>Title</th><th>Credits</th><th></th></tr>
        ${d.courses.slice(0, 12).map((c) => `<tr><td>${esc(c.course_id)}</td><td>${esc(c.title)}</td><td><input type="number" min="0.5" max="12" step="0.5" value="${c.credits}" class="inline-input" style="width:80px;" data-c="${esc(c.course_id)}" /></td>
          <td><button class="btn btn-outline btn-sm" data-save-c="${esc(c.course_id)}">Save and re-process</button></td></tr>`).join('')}</table></div><p class="small muted">${d.count} match(es); showing up to 12.</p>`;
      box.querySelectorAll('button[data-save-c]').forEach((b) => b.addEventListener('click', async () => {
        try {
          const r = await api.adminEditCourse(b.dataset.saveC, { credits: parseFloat(box.querySelector(`input[data-c="${b.dataset.saveC}"]`).value) });
          courses(`<div class="alert alert-success"><strong>${esc(r.course_id)}</strong> updated (${esc(JSON.stringify(r.changes))}). ${r.students_reprocessed} loaded student plan(s) re-processed immediately.
            ${r.affected.map((a) => `<br/>${esc(a.student_id)}: v${a.old_version} → v${a.new_version}`).join('')}</div>`); log();
        } catch (err) { box.insertAdjacentHTML('afterbegin', errorBox(err)); }
      }));
    } catch (err) { box.innerHTML = errorBox(err); }
  }

  async function rules(msg = '') {
    const box = $('ad-rules');
    try {
      const d = await api.adminRules();
      box.innerHTML = msg + d.rules.map((r) => `<div class="card" style="margin-bottom:8px;"><strong>${esc(r.rule_id)}</strong> ${badge(r.status, 'warning')}<div class="small">${esc(r.human_text)}</div>
        <div class="filters"><input class="inline-input" style="flex:1;min-width:260px;" data-r="${esc(r.rule_id)}" value='${esc(JSON.stringify(r.parameters))}' /><button class="btn btn-outline btn-sm" data-save-r="${esc(r.rule_id)}">Save and re-process all</button></div></div>`).join('');
      box.querySelectorAll('button[data-save-r]').forEach((b) => b.addEventListener('click', async () => {
        try {
          const params = JSON.parse(box.querySelector(`input[data-r="${b.dataset.saveR}"]`).value);
          const r = await api.adminEditRule(b.dataset.saveR, params);
          rules(`<div class="alert alert-success">${esc(r.rule_id)} updated. ${r.students_reprocessed} loaded student plan(s) re-processed.</div>`); log();
        } catch (err) { box.insertAdjacentHTML('afterbegin', errorBox(err)); }
      }));
    } catch (err) { box.innerHTML = errorBox(err); }
  }

  async function log() {
    try {
      const d = await api.adminReprocessLog();
      $('ad-log').innerHTML = `<p class="small muted">Background worker for database edits: ${d.worker_running ? 'running' : 'not running'} (polls every ${d.poll_seconds}s) • database ${d.db_available ? 'connected' : 'not reachable'}</p>
        <div style="overflow-x:auto;"><table class="table"><tr><th>When (UTC)</th><th>Source</th><th>Target</th><th>What</th><th>Result</th></tr>
        ${d.recent.map((e) => `<tr><td class="small">${esc(e.at.slice(11, 19))}</td><td>${badge(e.source)}</td><td>${esc(e.kind)}: ${esc(e.target)}</td><td class="small">${esc(e.detail)}</td>
          <td class="small">${e.new_version ? `v${e.old_version} → v${e.new_version}. ${esc(e.summary || '')}` : (e.students_reprocessed != null ? `${e.students_reprocessed} plan(s) rebuilt` : '')}</td></tr>`).join('') || '<tr><td colspan="5" class="muted">No edits yet.</td></tr>'}</table></div>
        ${d.db_queue.length ? `<details><summary class="small">Database queue (ops.reprocess_queue), latest ${d.db_queue.length}</summary><table class="table">${d.db_queue.map((q) => `<tr><td>${q.event_id}</td><td>${esc(q.entity_type)}</td><td>${esc(q.action)}</td><td>${badge(q.status)}</td><td class="small">${esc(q.result || '')}</td></tr>`).join('')}</table></details>` : ''}`;
    } catch (err) { $('ad-log').innerHTML = errorBox(err); }
  }

  $('ad-load').addEventListener('click', () => loadStudent());
  $('ad-course-search').addEventListener('click', () => courses());
  $('ad-log-refresh').addEventListener('click', log);
  $('ad-reset').addEventListener('click', async () => {
    if (!window.confirm('Restore the database and all in-memory state to the original seed? All edits and generated plans are discarded.')) return;
    $('ad-reset-msg').innerHTML = '<div class="loading-state">Resetting...</div>';
    try {
      const r = await api.adminReset();
      state.profile = null;
      $('ad-reset-msg').innerHTML = `<div class="alert alert-success"><strong>Reset complete.</strong> ${r.students_in_seed} seed profiles available. Database: ${esc(r.database.detail)}</div>`;
      status(); students().then(() => { $('ad-student-body').innerHTML = ''; }); courses(); rules(); log();
    } catch (err) { $('ad-reset-msg').innerHTML = errorBox(err); }
  });

  status(); students().then(() => { if (state.studentId) loadStudent(); }); courses(); rules(); log();
}
