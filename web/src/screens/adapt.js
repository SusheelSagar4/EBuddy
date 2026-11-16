import { api } from '../api/client.js';
import { esc, badge, needStudent, errorBox, md } from '../ui.js';

const PRESETS = [
  { id: 'strong_quiz', title: 'Strong quiz (≥ 85%)', text: 'Timed quiz at 92% on a goal skill. Expect practice to be tested out and pacing accelerated.' },
  { id: 'weak_quiz', title: 'Weak quiz (< 40%)', text: 'Timed quiz at 28% on the top-priority goal skill. Expect a remedial prerequisite block.' },
  { id: 'course_rejection', title: 'Course rejection', text: 'Reject a recommended elective. Expect the next-best option of the same slot.' },
  { id: 'goal_switch', title: 'Goal switch', text: 'Switch goal mid-degree. Evidence and completed courses are kept; electives and goal prep are re-ranked.' }
];
const label = (it) => it.item_type === 'course' && it.course_id ? `${it.course_id} ${it.title || ''}` : (it.title || it.course_id || it.item_id);

export function renderAdapt(container, state) {
  if (!state.studentId) return needStudent(container);
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header"><h2>Adaptation simulator</h2>
        <p class="subtitle">One click applies an event, re-plans deterministically (no LLM) and shows the plan diff with the reason for every change.</p></div>
      <div class="preset-grid">${PRESETS.map((p) => `<button class="preset-btn" data-preset="${p.id}"><strong>${esc(p.title)}</strong><span class="small">${esc(p.text)}</span></button>`).join('')}</div>
      <details style="margin-top:12px;"><summary class="small">Optional overrides</summary>
        <div class="filters"><input id="ov-skill" class="inline-input" placeholder="skill id (quiz presets)" /><input id="ov-score" class="inline-input" type="number" min="0" max="100" placeholder="score" />
          <input id="ov-course" class="inline-input" placeholder="course code (rejection)" /><select id="ov-goal" class="inline-input"><option value="">goal (switch): automatic</option></select></div></details>
      <div id="sim-out" style="margin-top:16px;"></div>
    </div>`;
  api.listGoals(state.profile && state.profile.programme_id).then((g) => {
    document.getElementById('ov-goal').insertAdjacentHTML('beforeend', g.goals.filter((x) => !x.legacy).map((x) => `<option value="${x.goal_id}">${esc(x.family)} - ${esc(x.name)}</option>`).join(''));
  }).catch(() => {});

  container.querySelectorAll('.preset-btn').forEach((b) => b.addEventListener('click', async () => {
    const out = document.getElementById('sim-out');
    out.innerHTML = '<div class="loading-state">Applying event and re-planning...</div>';
    const body = {};
    const sk = document.getElementById('ov-skill').value.trim(); const sc = document.getElementById('ov-score').value;
    const co = document.getElementById('ov-course').value.trim().toUpperCase(); const go = document.getElementById('ov-goal').value;
    if (sk) body.skill_id = sk; if (sc !== '') body.score = parseFloat(sc); if (co) body.course_id = co; if (go) body.goal_id = go;
    try {
      const r = await api.runPreset(state.studentId, b.dataset.preset, body);
      const d = r.plan_diff || { added_items: [], removed_items: [], modified_items: [] };
      const ev = r.event;
      const evText = ev.skill_id ? `${esc(ev.skill_name)}: timed quiz ${ev.score}% (strong evidence; level before ${ev.level_before ?? 'no evidence'})`
        : (ev.course_id ? `Rejected ${esc(ev.course_id)} ${esc(ev.title || '')} (Semester ${ev.semester})` : `${esc(ev.from_goal_name)} → ${esc(ev.to_goal_name)}`);
      if (r.preset === 'goal_switch') { state.profile = await api.getOverview(state.studentId); state.refreshPill(); }
      out.innerHTML = `
        <div class="card"><h3>${esc(r.label)}</h3>
          <p><strong>Event:</strong> ${evText}</p>
          <p>Roadmap <strong>v${r.old_version} → v${r.new_version}</strong> ${r.validation.passed ? badge('validated', 'success') : badge('validation failed', 'error')} ${badge('deterministic, no LLM')}
            ${badge('+' + r.diff_counts.added + ' added', 'success')} ${badge('−' + r.diff_counts.removed + ' removed', 'error')} ${badge(r.diff_counts.modified + ' re-paced', 'warning')}</p>
          <h4 style="margin-top:8px;">Why the plan changed</h4><ul style="margin-left:18px;">${r.why.map((w) => `<li>${esc(w)}</li>`).join('')}</ul>
          ${r.diff_counts.added + r.diff_counts.removed + r.diff_counts.modified === 0 ? '<div class="alert alert-info">No item changed: the plan already reflected this situation (for example a remedial block was already scheduled). The new evidence is recorded and the version is stored.</div>' : ''}
        </div>
        <div class="diff-cols">
          <div class="card diff-add"><h4>Added (${d.added_items.length})</h4>${d.added_items.map((it) => `<div class="item-row"><strong>${esc(label(it))}</strong> <span class="muted small">Sem ${it.semester_number ?? '-'} • ${esc(it.item_type)}</span><div class="why">${esc(it.reason.why_this)}</div></div>`).join('') || '<p class="muted">None</p>'}</div>
          <div class="card diff-rem"><h4>Removed (${d.removed_items.length})</h4>${d.removed_items.map((it) => { const w = (r.why_items.find((x) => x.change === 'removed' && x.item === label(it).trim()) || {}).why;
            return `<div class="item-row"><strong>${esc(label(it))}</strong> <span class="muted small">Sem ${it.semester_number ?? '-'} • ${esc(it.item_type)}</span><div class="why">${esc(w || 'No longer required after re-planning.')}</div></div>`; }).join('') || '<p class="muted">None</p>'}</div>
          <div class="card diff-mod"><h4>Re-paced (${d.modified_items.length})</h4>${d.modified_items.slice(0, 14).map((m) => `<div class="item-row"><strong>${esc(m.label)}</strong><div class="why">${Object.entries(m.changes).map(([k, v]) => `${esc(k)}: ${esc(v[0])} → ${esc(v[1])}`).join('; ')}</div></div>`).join('') || '<p class="muted">None</p>'}</div>
        </div>
        ${r.mismatch_warning ? `<div class="alert alert-warning">${esc(r.mismatch_warning.explanation)}</div>` : ''}
        <div class="filters"><a class="btn btn-primary" href="#plan">Open the updated roadmap</a><a class="btn btn-outline" href="#progress">See mastery</a></div>`;
    } catch (err) { out.innerHTML = errorBox(err); }
  }));
}
