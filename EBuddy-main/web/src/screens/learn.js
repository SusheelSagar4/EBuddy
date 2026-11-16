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
        <h2>Active Learning & Practice</h2>
        <p class="subtitle">Curated video lectures, reference materials, and targeted practice exercises.</p>
      </div>

      <div id="learn-loading" class="loading-state">Loading active modules & exercises...</div>
      <div id="learn-content" style="display: none;"></div>
    </div>
  `;

  loadLearnData();

  async function loadLearnData() {
    const loading = document.getElementById('learn-loading');
    const content = document.getElementById('learn-content');

    try {
      const data = await api.getLearn(state.studentId);
      loading.style.display = 'none';
      content.style.display = 'block';

      const resources = data.resources || [];
      const exercises = data.exercises || [];

      content.innerHTML = `
        <div class="two-col-layout">
          <div class="col-main">
            <h3>Recommended Open Courseware & Playlists</h3>
            ${resources.length === 0 ? `<p class="text-muted">No external resources mapped for this skill set yet.</p>` : `
              <div class="resource-cards-list">
                ${resources.map(res => `
                  <div class="resource-card">
                    <div class="res-top">
                      <span class="res-title">${res.title}</span>
                      <span class="badge ${res.coverage_status === 'playlist found' ? 'badge-success' : 'badge-neutral'}">
                        ${res.coverage_status || 'available'}
                      </span>
                    </div>
                    <p class="res-desc text-muted">${res.platform || 'NPTEL / YouTube'} • Channel: ${res.channel_or_instructor || 'IIT Faculty'}</p>
                    <div class="res-link">
                      <a href="${res.url || '#'}" target="_blank" rel="noopener noreferrer">Open Lecture Series ↗</a>
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>

          <div class="col-side">
            <h3>Interactive Practice Exercises</h3>
            ${exercises.length === 0 ? `<p class="text-muted">All active exercises for current milestone completed!</p>` : `
              <div class="exercise-cards-list">
                ${exercises.map(ex => `
                  <div class="exercise-card" id="ex-card-${ex.exercise_id}">
                    <div class="ex-header">
                      <span class="badge badge-info">${ex.skill_id}</span>
                      <span class="badge badge-neutral">Difficulty ${(ex.difficulty * 10).toFixed(0)}/10</span>
                    </div>
                    <p class="ex-prompt"><strong>${ex.prompt}</strong></p>
                    
                    <form class="ex-form" data-id="${ex.exercise_id}">
                      <div class="ex-input-group">
                        <input type="text" class="input-answer" placeholder="Enter numerical answer or choice..." required />
                        <button type="submit" class="btn btn-secondary btn-sm">Submit</button>
                      </div>
                    </form>
                    <div class="ex-feedback" id="feedback-${ex.exercise_id}" style="display:none;"></div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>
        </div>
      `;

      // Attach submission handlers
      document.querySelectorAll('.ex-form').forEach(form => {
        form.addEventListener('submit', async (e) => {
          e.preventDefault();
          const exId = form.getAttribute('data-id');
          const answer = form.querySelector('.input-answer').value;
          const feedbackBox = document.getElementById(`feedback-${exId}`);

          try {
            const res = await api.submitExercise(state.studentId, {
              exercise_id: exId,
              answer: answer
            });

            feedbackBox.style.display = 'block';
            feedbackBox.className = `ex-feedback ${res.correct ? 'feedback-success' : 'feedback-error'}`;
            feedbackBox.innerHTML = `
              <strong>${res.correct ? '✓ Correct!' : '✕ Needs Review'}</strong>
              <p>${res.explanation || 'Result registered in student evidence ledger.'}</p>
              <span class="score-pill">Score: ${(res.score * 100).toFixed(0)}%</span>
            `;
          } catch (err) {
            alert(`Submission error: ${err.message}`);
          }
        });
      });

    } catch (err) {
      loading.innerHTML = `<p class="text-error">Failed to load learning resources: ${err.message}</p>`;
    }
  }
}

