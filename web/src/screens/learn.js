import { api } from '../api/client.js';
import { esc, badge, skill, needStudent, errorBox, link, md, codeWarning, courseNotes } from '../ui.js';

export function renderLearn(container, state) {
  if (!state.studentId) return needStudent(container);
  container.innerHTML = `<div class="screen-card"><div id="learn-body" class="loading-state">Loading resources from the knowledge base...</div></div>`;
  load();

  async function load() {
    const body = document.getElementById('learn-body');
    try {
      const d = await api.getLearnV2(state.studentId);
      const t = d.track; const ph = t && t.current_phase; const ps = d.persona;
      body.className = '';
      body.innerHTML = `
        <div class="screen-header"><h2>Learn &amp; practise - ${esc(d.goal_name)}</h2><p class="subtitle">${esc(d.disclaimer)}</p></div>
        ${d.remediation.length ? `<h3>Remedial foundation first</h3>${d.remediation.map((r) => `<div class="alert alert-warning"><strong>${esc(r.title)}</strong><br/><span class="small">${esc(r.reason.why_this)}</span>${r.url ? `<div>${link(r.url, 'Open the course lectures')}</div>` : ''}</div>`).join('')}` : ''}

        ${t ? `<h3 style="margin-top:8px;">${esc(t.track_name)} track ${ph ? `- phase ${ph.order}: ${esc(ph.name)}` : '- all phases demonstrated'}</h3>
          ${ph ? `<p class="small">${esc(ph.objective)} <span class="muted">(~${ph.est_hours} h${ph.hours_basis !== 'source' ? ', design default' : ''}; checkpoint pass mark ${ph.pass_threshold_pct}%)</span></p>
          <div class="grid-2">
            <div><h4>Resource cards</h4>${ph.resources.map((r) => `<div class="card" style="margin-bottom:8px;"><strong>${esc(r.title)}</strong>
              <div class="small muted">${esc(r.provider || 'provider not stated')} • ${esc(r.topic || '')} ${r.tier ? badge(r.tier) : ''}</div><div class="small">${esc((r.usage_guidance || '').slice(0, 140))}</div><div>${link(r.url, 'Open')}</div></div>`).join('') || '<p class="muted">No resources for this phase.</p>'}</div>
            <div><h4>Checkpoints (how you demonstrate it)</h4><ul style="margin-left:18px;">${ph.checkpoints.map((c) => `<li class="small">${esc(c.text)} ${c.type ? badge(c.type) : ''}</li>`).join('')}</ul>
              ${ph.projects.length ? `<h4 style="margin-top:10px;">Portfolio projects</h4>${ph.projects.map((p) => `<div class="card" style="margin-bottom:8px;"><strong>${esc(p.title)}</strong><div class="small">${esc(p.why)}</div>${(p.rubric || []).length ? `<div class="small muted">Rubric: ${esc(p.rubric.join('; '))}</div>` : ''}</div>`).join('')}` : ''}
              ${t.practice_problems.length ? `<h4 style="margin-top:10px;">Practice problems</h4><ul style="margin-left:18px;">${t.practice_problems.map((p) => `<li class="small">${link(p.url, p.title)} ${badge(p.difficulty)} <span class="muted">${esc(p.topic)}</span></li>`).join('')}</ul>` : ''}</div>
          </div>` : ''}
          ${t.practice_questions.length ? `<h4 style="margin-top:12px;">Quick check (graded; counts as assessed evidence)</h4>${t.practice_questions.map((q) => `<div class="card" style="margin-bottom:8px;" id="q-${esc(q.question_id)}">
            <div class="small muted">${esc(q.skill)} • difficulty ${q.difficulty_num}/3</div><p>${esc(q.stem)}</p>
            ${q.options.map((o) => `<label style="display:block;margin:3px 0;"><input type="radio" name="${esc(q.question_id)}" value="${esc(o)}"> ${esc(o)}</label>`).join('')}
            <button class="btn btn-secondary btn-sm" data-q="${esc(q.question_id)}">Submit</button><div class="fb small"></div></div>`).join('')}` : (t.question_bank_note ? `<p class="small muted">${esc(t.question_bank_note)}</p>` : '')}
          <h4 style="margin-top:12px;">Hackathons, competitions and fests unlocked for you</h4><p class="small muted">${esc(t.events.message || '')} (${t.events.locked_count} more unlock with later phases)</p>
          <div class="grid-2">${t.events.events.map((e) => `<div class="card"><strong>${esc(e.name)}</strong> ${badge(e.category)} ${e.is_home_campus ? badge('IIT Bhubaneswar', 'success') : ''}
            <div class="small muted">${esc(e.organiser)} • expected ${esc(e.window || 'window not stated')}</div><div class="small">Dates are expected windows, not confirmed - check the organiser's page.</div></div>`).join('') || '<p class="muted">Nothing unlocked yet.</p>'}</div>` : ''}

        ${ps ? `<h3 style="margin-top:18px;">${ps.persona_id === 'student_startup' ? 'Startup roadmap' : 'UPSC roadmap'}</h3>
          ${ps.advisories.map((a) => `<div class="alert alert-info">${esc(a)}</div>`).join('')}
          ${ps.incubation_and_club_pointers.length ? `<h4>Incubation and institute pointers</h4><div class="grid-2">${ps.incubation_and_club_pointers.map((r) => `<div class="card"><strong>${esc(r.title)}</strong><div class="small muted">${esc(r.provider)}</div><div>${link(r.url, 'Open official page')}</div><div class="small">${esc(r.note || '')}</div></div>`).join('')}</div>` : ''}
          <h4 style="margin-top:10px;">Phase-wise milestones</h4><table class="table">${ps.milestones.map((m) => `<tr><td>Sem ${m.semester_target}</td><td><strong>${esc(m.title)}</strong><br/><span class="small">${esc(m.description)}</span></td></tr>`).join('')}</table>
          <h4 style="margin-top:10px;">Resource cards</h4><div class="grid-2">${ps.resources.map((r) => `<div class="card"><strong>${esc(r.title)}</strong> ${r.verified ? badge('verified', 'success') : badge('not confirmed yet', 'warning')}
            <div class="small muted">${esc(r.provider || '')} • ${skill(r.target_skill)}</div><div>${r.verified ? link(r.url, 'Open') : ''}</div><div class="small">${esc(r.note || '')}</div></div>`).join('')}</div>` : ''}

        <h3 style="margin-top:18px;">This semester's courses</h3>
        <div class="grid-2">${d.courses.map((c) => `<div class="card"><strong>${esc(c.display_code || c.course_id || '')} ${esc(c.title || '')}</strong> <span class="small muted">${c.credits ?? ''} cr • ${c.weekly_hours ?? '-'} h/wk</span>
          ${codeWarning(c.course_notes)}${courseNotes(c.course_notes)}
          <div class="pill-row">${(c.skills || []).map((s) => badge(skill(s))).join(' ')}</div>
          ${c.primary ? `<div>${link(c.primary.url, c.primary.title)} <span class="small muted">${esc(c.primary.provider)} • ${esc(c.primary.coverage_status)}</span></div>` : '<div class="small muted">No lecture resource in the knowledge base for this course.</div>'}
          ${c.backups.length ? `<details><summary class="small">Alternative resources (${c.backups.length})</summary>${c.backups.map((b) => `<div class="small">${link(b.url, b.title)}</div>`).join('')}</details>` : ''}</div>`).join('') || '<p class="muted">No courses this semester.</p>'}</div>`;

      body.querySelectorAll('button[data-q]').forEach((b) => b.addEventListener('click', async () => {
        const qid = b.dataset.q; const sel = body.querySelector(`input[name="${qid}"]:checked`);
        const fb = b.parentElement.querySelector('.fb');
        if (!sel) { fb.textContent = 'Choose an option first.'; return; }
        b.disabled = true;
        try {
          const r = await api.submitPractice(state.studentId, qid, sel.value);
          fb.innerHTML = `<div class="alert ${r.is_correct ? 'alert-success' : 'alert-error'}">${r.is_correct ? 'Correct.' : `Not quite. Answer: ${esc(r.correct_answer)}.`} ${esc(r.explanation || '')}<br/>Roadmap v${r.old_version} → v${r.new_version}.<br/>${md(r.what_changed_and_why || '')}</div>`;
        } catch (err) { fb.innerHTML = errorBox(err); b.disabled = false; }
      }));
    } catch (err) { body.className = ''; body.innerHTML = errorBox(err); }
  }
}
