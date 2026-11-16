import { renderOnboarding } from './screens/onboarding.js';
import { renderDiagnostic } from './screens/diagnostic.js';
import { renderPlan } from './screens/plan.js';
import { renderLearn } from './screens/learn.js';
import { renderProgress } from './screens/progress.js';
import { renderChat } from './screens/chat.js';
import { renderAdapt } from './screens/adapt.js';
import { renderAdmin } from './screens/admin.js';
import { renderMBA } from './screens/mba.js';
import { renderMTechScreen } from './screens/mtech.js';
import { api } from './api/client.js';

const state = { studentId: localStorage.getItem('ebuddy_student_id') || null, profile: null, activeRoute: '#onboard' };

const routes = {
  '#onboard': { title: 'Profiles & Goals', render: renderOnboarding },
  '#diagnostic': { title: 'Adaptive Diagnostic', render: renderDiagnostic },
  '#plan': { title: 'Roadmap (all remaining semesters)', render: renderPlan },
  '#learn': { title: 'Learn & Practise', render: renderLearn },
  '#adapt': { title: 'Adaptation Simulator', render: renderAdapt },
  '#progress': { title: 'Mastery: completed vs demonstrated', render: renderProgress },
  '#chat': { title: 'Buddy Chat', render: renderChat },
  '#mba': { title: 'Core to MBA (Career & Prep)', render: renderMBA },
  '#mtech': { title: 'Core to M.Tech Higher Studies', render: renderMTechScreen },
  '#admin': { title: 'Admin & Data', render: renderAdmin }
};

function navigate(hash) { window.location.hash = hash; }

export function refreshPill() {
  const pill = document.getElementById('active-student-pill');
  if (!pill) return;
  const p = state.profile;
  pill.textContent = p ? `${p.name} • ${p.programme_id.replace('BTECH_', '')} Sem ${p.current_semester} • ${p.goal_family}` : (state.studentId || 'No student selected');
}
state.refreshPill = refreshPill;

async function handleRoute() {
  const hash = window.location.hash || (state.studentId ? '#plan' : '#onboard');
  const route = routes[hash] || routes['#onboard'];
  state.activeRoute = hash;
  document.querySelectorAll('.nav-item a').forEach((a) => a.classList.toggle('active', a.getAttribute('href') === hash));
  const titleEl = document.getElementById('screen-title');
  if (titleEl) titleEl.textContent = route.title;
  if (state.studentId && !state.profile) {
    try { state.profile = await api.selectStudent(state.studentId); }
    catch (e) { state.studentId = null; localStorage.removeItem('ebuddy_student_id'); }
  }
  refreshPill();
  route.render(document.getElementById('app-screen'), state, navigate);
}

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', handleRoute);
