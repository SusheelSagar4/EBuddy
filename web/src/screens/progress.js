import { api } from '../api/client.js';
import { esc, badge, skill, needStudent, errorBox, tierBadge, md } from '../ui.js';

const STATUS = {
  demonstrated: ['Demonstrated', 'success'], course_completed_only: ['Course completed, not yet demonstrated', 'warning'],
  in_progress: ['In progress', 'info'], self_declared_only: ['Self-declared only', 'warning'], no_evidence: ['No evidence yet', 'neutral']
};

export function renderProgress(container, state) {
  if (!state.studentId) return needStudent(container);
  container.innerHTML = `<div class="screen-card"><div id="pg-body" class="loading-state">Evaluating the evidence ledger...</div></div>`;
  load();

  async function load() {
    const body = document.getElementById('pg-body');
    try {
      const d = await api.getProgress(state.studentId);
      const cc = d.course_completion; const pf = d.proficiency; const th = pf.thresholds;
      body.className = '';
      body.innerHTML = `
        <div class="screen-header"><h2>${esc(d.goal_name)}</h2>
          <p class="subtitle">Two separate ledgers. Passing a course is recorded on the left. Mastery is only what you have demonstrated under assessment, on the right.</p></div>
        <div class="two-ledgers">
          <div class="card"><h3>1. Course enrolment and completion</h3>
            <div class="grid-3" style="margin:8px 0;"><div><div class="muted small">Courses passed</div><div class="kpi">${cc.completed_courses}</div></div>
              <div><div class="muted small">Registered now</div><div class="kpi">${cc.registered_this_semester}</div></div>
              <div><div class="muted small">Goal-relevant passed</div><div class="kpi">${cc.goal_relevant_completed.length}</div></div></div>
            <p class="small muted">${esc(cc.note)}</p>
            <table class="table"><tr><th>Goal-relevant course</th><th>State</th></tr>
              ${cc.goal_relevant_completed.map((c) => `<tr><td>${esc(c.course_id)} ${esc(c.title)}<br/><span class="small muted">${c.skills.map(skill).join(', ')}</span></td><td>${badge('passed', 'success')}</td></tr>`).join('')}
              ${cc.goal_relevant_in_progress.map((c) => `<tr><td>${esc(c.course_id)} ${esc(c.title)}<br/><span class="small muted">${c.skills.map(skill).join(', ')}</span></td><td>${badge('registered', 'info')}</td></tr>`).join('')}
              ${cc.goal_relevant_completed.length + cc.goal_relevant_in_progress.length === 0 ? '<tr><td colspan="2" class="muted">No degree course maps to this goal\'s skills; the goal is pursued through its own roadmap.</td></tr>' : ''}</table></div>
          <div class="card"><h3>2. Demonstrated proficiency</h3>
            <div class="grid-3" style="margin:8px 0;"><div><div class="muted small">Skills demonstrated</div><div class="kpi">${pf.skills_demonstrated} / ${pf.skills_total}</div></div>
              <div><div class="muted small">Goal mastery</div><div>${pf.goal_demonstrated ? badge('Demonstrated', 'success') : badge('Not yet', 'warning')}</div></div>
              <div><div class="muted small">Thresholds</div><div class="small">timed quiz ${th.timed_quiz}% • project ${th.rubric_project}% • mock interview ${th.mock_interview}%</div></div></div>
            <table class="table"><tr><th>Goal-level criterion</th><th>Have / need</th><th></th></tr>
              ${pf.goal_level.map((g) => `<tr><td>${esc(g.name)}</td><td>${g.achieved} / ${g.required}</td><td>${g.met ? badge('met', 'success') : badge('open', 'warning')}</td></tr>`).join('')}</table>
            ${pf.completed_but_not_demonstrated.length ? `<div class="alert alert-warning small"><strong>Completed ≠ mastered:</strong> ${pf.completed_but_not_demonstrated.map(skill).join(', ')} - the course is passed but no timed assessment at ${th.timed_quiz}% or better is on record.</div>` : ''}</div>
        </div>
        <h3 style="margin-top:18px;">Skill by skill</h3>
        ${pf.skills.map((s) => { const [txt, kind] = STATUS[s.status] || [s.status, 'neutral']; const e = s.evidence;
          return `<div class="card" style="margin-bottom:8px;"><div class="sem-head"><strong>${esc(s.skill_name)}</strong><span>${badge(txt, kind)} ${s.evidence_basis ? tierBadge(s.evidence_basis === 'mixed' ? 'strong' : s.evidence_basis) : ''}</span></div>
            <div class="bar"><span style="width:${Math.min(100, s.estimated_level)}%"></span><i style="left:${Math.min(100, s.required_level)}%"></i></div>
            <div class="small muted">evidence-weighted level ${s.estimated_level} • required ${s.required_level} (red mark)</div>
            <div class="small">Timed assessment: <strong>${e.timed_assessment_best ?? '-'}</strong> • Rubric project: <strong>${e.project_rubric_best ?? '-'}</strong> • Mock interview: <strong>${e.mock_interview_best ?? '-'}</strong>
              • From course grade: ${e.course_grade_based ?? '-'} • Self-declared: ${e.self_declared ?? '-'} <span class="muted">(does not count)</span></div></div>`; }).join('') || '<p class="muted">This goal has no skill requirements in the knowledge base.</p>'}

        <h3 style="margin-top:18px;">Log demonstrated evidence</h3>
        <div class="filters"><select id="ev-skill">${pf.skills.map((s) => `<option value="${s.skill_id}">${esc(s.skill_name)}</option>`).join('')}</select>
          <select id="ev-type"><option value="timed_quiz">Timed quiz</option><option value="project_rubric">Rubric-scored project</option><option value="mock_interview">Mock interview</option><option value="self_declaration">Self-rating (weak)</option></select>
          <input id="ev-score" type="number" min="0" max="100" value="80" class="inline-input" style="width:90px;" /><button class="btn btn-primary" id="ev-add">Record and re-plan</button></div>
        <div id="ev-msg"></div>

        <h3 style="margin-top:18px;">Evidence ledger (latest ${d.evidence.length})</h3>
        <p class="small muted">Tier weights: strong ${d.evidence_weights.tier_weights.strong}, medium ${d.evidence_weights.tier_weights.medium}, weak ${d.evidence_weights.tier_weights.weak}. Self-declared evidence alone is capped at level 40.</p>
        <div style="overflow-x:auto;"><table class="table"><tr><th>Skill</th><th>Source</th><th>Score</th><th>Reliability</th><th>Note</th></tr>
          ${d.evidence.map((e) => `<tr><td>${esc(e.skill_name)}</td><td>${esc(e.source_type)}</td><td>${e.score}</td><td>${tierBadge(e.reliability_tier)}</td><td class="small muted">${esc(e.notes || '')}</td></tr>`).join('')}</table></div>`;
      const btn = document.getElementById('ev-add');
      if (btn) btn.addEventListener('click', async () => {
        const msg = document.getElementById('ev-msg');
        try {
          const r = await api.addEvidence(state.studentId, { skill_id: document.getElementById('ev-skill').value, source_type: document.getElementById('ev-type').value, score: parseFloat(document.getElementById('ev-score').value) });
          await load();
          document.getElementById('ev-msg').innerHTML = `<div class="alert alert-success">Recorded as ${esc(r.reliability_tier)} evidence. Roadmap v${r.old_version} → v${r.new_version}.<br/>${md(r.what_changed_and_why || '')}</div>`;
        } catch (err) { msg.innerHTML = errorBox(err); }
      });
    } catch (err) { body.className = ''; body.innerHTML = errorBox(err); }
  }
}
