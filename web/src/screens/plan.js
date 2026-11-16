import { api } from '../api/client.js';
import { esc, badge, skill, needStudent, errorBox, md, link, tagBadges } from '../ui.js';

const itemRow = (it) => {
  const r = it.reason || {};
  const label = it.item_type === 'course' ? `${it.course_id ? esc(it.course_id) + ' ' : ''}${esc(it.title || '')}` : esc(it.title || it.course_id || it.item_id);
  const rules = (r.rule_compliance || []).map((x) => `<li>${esc(x)}</li>`).join('');
  const warn = (r.rule_compliance || []).some((x) => x.includes('WARNING'));
  return `<details class="item-row"><summary>
      <span>${badge(it.item_type, it.item_type === 'remediation' ? 'error' : (it.item_type === 'course' ? 'info' : 'neutral'))} <strong>${label}</strong>
        ${it.credits ? `<span class="muted small">${it.credits} cr</span>` : ''} ${warn ? badge('warning', 'warning') : ''} ${it.planning_status === 'beyond_horizon' ? badge('does not fit before Sem 8', 'error') : ''}</span>
      <span class="muted small">${it.prep_hours_weekly != null && it.planning_status === 'current' ? `${it.prep_hours_weekly} h/wk • ` : ''}${esc(r.intent || '')} ▾</span></summary>
    <div class="why"><strong>Why:</strong> ${esc(r.why_this || '')}
      ${(r.target_skills || []).length ? `<div class="pill-row" style="margin-top:4px;">${r.target_skills.map((s) => badge(skill(s))).join(' ')}</div>` : ''}
      ${(r.prerequisite_for || []).length ? `<div>Unlocks: ${esc(r.prerequisite_for.join(', '))}</div>` : ''}
      ${rules ? `<ul style="margin:4px 0 0 18px;">${rules}</ul>` : ''}${it.url ? `<div>${link(it.url, 'Open resource')}</div>` : ''}</div></details>`;
};

export function renderPlan(container, state) {
  if (!state.studentId) return needStudent(container);
  container.innerHTML = `<div class="screen-card"><div id="plan-body" class="loading-state">Loading validated roadmap...</div></div>`;
  load();

  async function load() {
    const body = document.getElementById('plan-body');
    try {
      const [p, props] = await Promise.all([api.getPlanV2(state.studentId), api.getProposals(state.studentId).catch(() => ({ proposals: [] }))]);
      const v = p.validation || { passed: true, checks: [] };
      const h = p.horizon || {}; const wb = h.weekly_budget || {}; const tr = h.track;
      const es = p.evidence_summary || { skills: [] };
      body.className = '';
      body.innerHTML = `
        <div class="screen-header"><h2>${esc(p.goal_name)} ${badge(p.goal_family, 'info')}</h2>
          <p class="subtitle">Version ${p.version} • built by the deterministic planner (Agent 1), checked by the validator. The LLM does not choose courses.</p></div>
        <div class="grid-3">
          <div class="card"><div class="muted small">Validation</div><div>${v.passed ? badge('All hard checks passed', 'success') : badge('Hard check failed', 'error')}</div>
            <div class="small muted">${(v.checks || []).filter((c) => c.severity === 'warning').length} labelled warning(s)</div></div>
          <div class="card"><div class="muted small">Credits by semester</div><div class="small">${Object.entries(h.credits_by_semester || {}).map(([s, c]) => `S${s}: <strong>${c}</strong>`).join(' • ')}</div>
            <div class="small muted">Your cap: ${h.student_credit_cap ?? 'none'} • Institute baseline: ${h.institute_credit_cap}</div></div>
          <div class="card"><div class="muted small">This semester, hours per week</div><div class="kpi">${wb.allocated_hours ?? '-'} <span class="small muted">/ cap ${wb.cap_hours ?? 'not set'}</span></div>
            <div class="small muted">courses ${wb.academic_hours} • practice ${wb.practice_hours} • remediation ${wb.remediation_hours} • goal prep ${wb.goal_prep_hours}${wb.compressed ? ' • compressed to fit your cap' : ''}</div></div>
        </div>
        ${p.mismatch_warning ? `<div class="alert alert-warning"><strong>Interest vs evidence (${esc(p.mismatch_warning.severity || 'gap')}):</strong> ${esc(p.mismatch_warning.explanation)}<br/><span class="small"><strong>Trade-off:</strong> ${esc(p.mismatch_warning.tradeoff)}</span></div>` : ''}
        ${(p.advisories || []).map((a) => `<div class="alert alert-info">${esc(a)}</div>`).join('')}
        ${p.version > 1 && p.what_changed_and_why ? `<div class="alert alert-success"><strong>What changed in this version, and why</strong><br/>${md(p.what_changed_and_why)}</div>` : ''}
        <div id="prop-box"></div>

        ${tr ? `<h3 style="margin-top:18px;">Career track: ${esc(tr.track_name)}</h3>
          <div style="overflow-x:auto;"><table class="table"><thead><tr><th>Phase</th><th>Status</th><th>Hours</th><th>Planned in</th><th>Needs (assessed)</th></tr></thead><tbody>
          ${tr.phase_status.map((ph) => { const sc = (tr.schedule || []).find((x) => x.phase_id === ph.phase_id);
            return `<tr><td>${ph.order}. ${esc(ph.name)}</td><td>${badge(ph.status.replace('_', ' '), ph.status === 'demonstrated' ? 'success' : (ph.status === 'in_progress' ? 'info' : 'neutral'))}</td>
              <td>${sc ? sc.est_hours : '-'}</td><td>${sc ? (sc.status === 'beyond_horizon' ? badge('after Sem 8 / breaks', 'error') : `Sem ${sc.start_semester}${sc.end_semester !== sc.start_semester ? '-' + sc.end_semester : ''}`) : 'tested out'}</td>
              <td class="small">${ph.skills.map((s) => `${skill(s.skill_id)} ≥ ${s.required_level} (${s.assessed_level ?? 'no evidence'})`).join('; ')}</td></tr>`; }).join('')}
          </tbody></table></div>` : ''}

        <h3 style="margin-top:18px;">Semester-by-semester roadmap</h3>
        ${p.semesters.map((s) => `<div class="sem-block ${s.is_current ? 'current' : ''}">
          <div class="sem-head"><h4>Semester ${s.semester_number} ${s.is_current ? badge('current', 'success') : badge('planned')}</h4>
            <span class="small muted">${s.credits} credits • ${s.courses.length} courses${s.goal_items.length ? ` • ${s.goal_items.length} goal items` : ''}</span></div>
          ${s.remediation.map(itemRow).join('')}${s.courses.map(itemRow).join('')}
          ${s.goal_items.length ? `<div class="small muted" style="margin-top:8px;">Goal preparation and milestones</div>${s.goal_items.map(itemRow).join('')}` : ''}
          ${s.practice.length ? `<details class="item-row"><summary><span>${badge('practice')} ${s.practice.length} practice set(s)</span><span class="muted small">show ▾</span></summary>${s.practice.map(itemRow).join('')}</details>` : ''}
        </div>`).join('')}

        ${(p.proposals || []).length ? `<h3 style="margin-top:18px;">Not in the default plan (needs your decision) and explanations</h3>
          ${p.proposals.map((x) => `<div class="alert ${x.status.includes('explanation') ? 'alert-info' : 'alert-warning'}"><strong>${esc(x.course_id || x.title || 'Note')}</strong> ${x.title && x.course_id ? esc(x.title) : ''} ${badge(x.status.replace(/_/g, ' '))}<br/>${esc(x.reason)}</div>`).join('')}` : ''}

        ${p.official_pointers.length ? `<h3 style="margin-top:18px;">Official pointers for this goal</h3><div class="grid-2">
          ${p.official_pointers.map((r) => `<div class="card"><strong>${esc(r.title)}</strong><div class="small muted">${esc(r.provider || '')}</div>
            <div>${r.verified ? link(r.url, 'Open official page') : '<span class="muted">not confirmed yet</span>'}</div><div class="small">${esc(r.note || '')}</div></div>`).join('')}</div>` : ''}

        <h3 style="margin-top:18px;">Evidence the plan relies on</h3>
        <p class="small muted">${esc(es.rule || '')}</p>
        <div style="overflow-x:auto;"><table class="table"><thead><tr><th>Goal skill</th><th>Target</th><th>Estimate</th><th>Evidence</th><th>Planner treatment</th></tr></thead><tbody>
          ${es.skills.map((s) => `<tr><td>${esc(s.skill_name)}</td><td>${s.target_level ?? '-'}</td><td>${s.estimated_level ?? '-'}</td>
            <td>${badge(s.strong_evidence + ' strong', 'success')} ${badge(s.weak_evidence + ' weak', 'warning')} <span class="small muted">${esc((s.sources || []).join(', '))}</span></td><td class="small">${esc(s.planner_treatment)}</td></tr>`).join('')}
        </tbody></table></div>
        <details style="margin-top:14px;"><summary><strong>Validator checks (${(v.checks || []).length})</strong></summary>
          <table class="table">${(v.checks || []).map((c) => `<tr><td>${c.passed ? '✓' : '✕'} ${esc(c.check_name)}</td><td>${badge(c.severity, c.severity === 'error' ? 'error' : (c.severity === 'warning' ? 'warning' : 'neutral'))}</td><td class="small">${esc(c.message)}</td></tr>`).join('')}</table></details>
        <details style="margin-top:8px;"><summary><strong>Version history (${p.versions.length})</strong></summary>
          <table class="table"><tr><th>v</th><th>Trigger</th><th>Summary</th></tr>${p.versions.slice().reverse().map((x) => `<tr><td>${x.version}</td><td>${esc(x.trigger)}</td><td class="small">${esc(x.summary)}${(x.reasons || []).length ? '<br/><em>' + esc(x.reasons.join(' ')) + '</em>' : ''}</td></tr>`).join('')}</table></details>
        <div class="filters"><a class="btn btn-primary" href="#learn">Learn &amp; practise →</a><a class="btn btn-outline" href="#adapt">Try an adaptation</a></div>`;

      const pb = document.getElementById('prop-box');
      if ((props.proposals || []).length) {
        pb.innerHTML = `<div class="alert alert-warning"><strong>Pending change proposals (${props.proposals.length})</strong> - other agents can only propose; Agent 1 commits after your approval.
          ${props.proposals.map((x) => `<div class="card" style="margin-top:8px;"><div>${badge(x.proposer_agent)} ${badge(x.proposal_type)}</div><div class="small">${esc(x.reasoning)}</div>
            <div class="small"><strong>Effect:</strong> ${esc(x.impact_summary)}</div><div class="filters"><button class="btn btn-primary btn-sm" data-p="${esc(x.proposal_id)}" data-a="1">Approve</button><button class="btn btn-outline btn-sm" data-p="${esc(x.proposal_id)}" data-a="0">Reject</button></div></div>`).join('')}</div>`;
        pb.querySelectorAll('button[data-p]').forEach((b) => b.addEventListener('click', async () => {
          b.disabled = true;
          try { await api.decideProposal(state.studentId, b.dataset.p, b.dataset.a === '1', 'Decided on the roadmap screen'); load(); }
          catch (err) { pb.insertAdjacentHTML('beforeend', errorBox(err)); }
        }));
      }
    } catch (err) { body.className = ''; body.innerHTML = errorBox(err); }
  }
}
