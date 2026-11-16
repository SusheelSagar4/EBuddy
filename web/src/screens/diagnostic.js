import { api } from '../api/client.js';
import { esc, badge, skill, needStudent, errorBox, md } from '../ui.js';

export function renderDiagnostic(container, state) {
  if (!state.studentId) return needStudent(container);
  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header"><h2>Adaptive diagnostic</h2>
        <p class="subtitle">5 to 8 questions, one at a time. Difficulty starts from your assessed evidence (grades, earlier tests) - self-ratings carry no weight here - and moves up or down with each answer.</p></div>
      <div class="filters"><button class="btn btn-primary" id="dg-start">Start a new diagnostic</button></div>
      <div id="dg-body"></div>
    </div>`;
  const body = document.getElementById('dg-body');
  document.getElementById('dg-start').addEventListener('click', async () => {
    try { await api.startDiagnostic(state.studentId); next(); } catch (err) { body.innerHTML = errorBox(err); }
  });

  async function next(lastFeedback = '') {
    body.innerHTML = '<div class="loading-state">Selecting the next question...</div>';
    try {
      const d = await api.nextDiagnostic(state.studentId);
      const st = d.state; const pr = d.prior || {};
      const priorBox = `<div class="alert alert-info small"><strong>Starting point: difficulty ${pr.start_difficulty} (${esc(pr.basis || '')}).</strong>
        ${(pr.used || []).length ? ` Used: ${pr.used.map((u) => `${skill(u.skill_id)} ${u.level} (${u.basis}, weight ${u.weight})`).join('; ')}.` : ''}
        ${(pr.ignored_self_declared || []).length ? ` Ignored (self-declared, weight 0): ${pr.ignored_self_declared.map((u) => `${skill(u.skill_id)} ${u.level}`).join('; ')}.` : ''}
        ${(d.uncovered_skills || []).length ? `<br/>No verified question bank yet for: ${d.uncovered_skills.map(skill).join(', ')} - these are not tested here and nothing is generated.` : ''}</div>`;
      if (d.complete) {
        body.innerHTML = `${lastFeedback}${priorBox}<div class="alert alert-success"><strong>${esc(d.message)}</strong><br/>Answered ${st.answers_count} • ability estimate ${st.ability_estimate} • confidence ${st.confidence}</div>
          <div class="filters"><a class="btn btn-primary" href="#plan">See the roadmap</a><a class="btn btn-outline" href="#progress">See mastery</a></div>`;
        return;
      }
      const ex = d.exercise;
      body.innerHTML = `${lastFeedback}${priorBox}
        <div class="card"><div class="pill-row">${badge(`Question ${st.answers_count + 1} of ${st.min_items}-${st.max_items}`, 'info')} ${badge(skill(ex.skill_id))} ${badge(`difficulty ${ex.difficulty_0_100}`)} ${badge(ex.status.replace(/_/g, ' '), 'warning')}</div>
          <p style="margin:10px 0;">${esc(ex.question_text)}</p>
          ${ex.options.map((o) => `<label style="display:block;margin:5px 0;"><input type="radio" name="dg-opt" value="${esc(o)}"> ${esc(o)}</label>`).join('')}
          <div class="filters"><button class="btn btn-primary" id="dg-submit">Submit answer</button><span class="small muted">Ability estimate so far: ${st.ability_estimate} (confidence ${st.confidence})</span></div></div>`;
      document.getElementById('dg-submit').addEventListener('click', async () => {
        const sel = body.querySelector('input[name="dg-opt"]:checked');
        if (!sel) return;
        try {
          const r = await api.answerDiagnostic(state.studentId, ex.exercise_id, ex.skill_id, sel.value);
          const fb = `<div class="alert ${r.is_correct ? 'alert-success' : 'alert-error'} small">${r.is_correct ? 'Correct - the next question is harder.' : 'Incorrect - the next question is easier.'} ${esc(r.feedback || '')}
            ${r.replanned ? `<br/><strong>Roadmap re-planned to v${r.replanned.version}.</strong><br/>${md(r.replanned.what_changed_and_why || '')}` : ''}</div>`;
          next(fb);
        } catch (err) { body.insertAdjacentHTML('beforeend', errorBox(err)); }
      });
    } catch (err) { body.innerHTML = errorBox(err); }
  }
}
