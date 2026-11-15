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

// Application global state
const state = {
  studentId: localStorage.getItem('ebuddy_student_id') || 'STU_EE_2026_01',
  profile: null,
  activeRoute: '#plan'
};

const routes = {
  '#onboard': { title: 'Onboarding', render: renderOnboarding },
  '#diagnostic': { title: 'Diagnostic', render: renderDiagnostic },
  '#plan': { title: 'Academic Plan', render: renderPlan },
  '#mba': { title: 'Core to MBA (Career & Prep)', render: renderMBA },
  '#learn': { title: 'Learn & Practise', render: renderLearn },
  '#progress': { title: 'Mastery Progress', render: renderProgress },
  '#mtech': { title: 'Core to M.Tech Higher Studies', render: renderMTechScreen },
  '#chat': { title: 'Buddy Chat', render: renderChat },
  '#adapt': { title: 'Adapt Simulator', render: renderAdapt },
  '#admin': { title: 'Admin & Integrity', render: renderAdmin }
};

function navigate(hash) {
  window.location.hash = hash;
}

function handleRoute() {
  const hash = window.location.hash || '#plan';
  const route = routes[hash] || routes['#plan'];
  state.activeRoute = hash;

  // Update nav highlight
  document.querySelectorAll('.nav-item a').forEach(a => {
    if (a.getAttribute('href') === hash) {
      a.classList.add('active');
    } else {
      a.classList.remove('active');
    }
  });

  // Update header title
  const titleEl = document.getElementById('screen-title');
  if (titleEl) titleEl.textContent = route.title;

  // Update student id pill
  const pillEl = document.getElementById('active-student-pill');
  if (pillEl) {
    pillEl.textContent = state.studentId ? `Student: ${state.studentId}` : 'No Student Loaded';
  }

  // Render view
  const appContainer = document.getElementById('app-screen');
  if (appContainer) {
    route.render(appContainer, state, navigate);
  }
}

window.addEventListener('hashchange', handleRoute);
window.addEventListener('DOMContentLoaded', () => {
  handleRoute();
});

