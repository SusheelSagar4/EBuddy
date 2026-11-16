/**
 * Core to M.Tech Comprehensive Higher Studies Screen (§13)
 * Mobile-friendly, vanilla JS & CSS, zero external CDN scripts/fonts.
 */

import { api } from '../api/client.js';
import { esc, needStudent } from '../ui.js';

// The app keeps the selected student under state.profile; this screen used to read state.programmeId / state.cgpa,
// which do not exist, so every student was shown as EE with "CGPA: 7.5".
const profileOf = (state) => state.profile || {};
const branchOf = (state) => profileOf(state).programme_id || "BTECH_EE";
const cgpaOf = (state) => (typeof profileOf(state).cgpa === "number" ? profileOf(state).cgpa : null);
const yearOf = (state) => profileOf(state).year || (profileOf(state).current_semester ? Math.ceil(profileOf(state).current_semester / 2) : null);

// Tabs below still show fixed illustration figures: there is no student-facing M.Tech API for mocks, topic
// mastery or the shortlist yet. Say so on screen instead of presenting them as this student's results.
const SAMPLE_NOTE = `<div class="alert alert-warning" style="margin-bottom:14px;"><strong>Sample figures.</strong>
  The numbers on this tab are a fixed illustration, not computed from your evidence yet. Use the Adapt Simulator's
  M.Tech scenarios for computed results.</div>`;

function weeksUntil(isoDate) {
  const ms = new Date(isoDate + "T00:00:00") - new Date();
  return Math.max(0, Math.round(ms / (7 * 24 * 3600 * 1000)));
}

export function renderMTechScreen(container, state, navigate) {
  if (!state.studentId) { needStudent(container); return; }
  const branch = branchOf(state);
  const paperCode = branch.includes("EE") ? "EE" : "MT";
  const studentId = state.studentId;

  container.innerHTML = `
    <div class="screen-card">
      <div class="screen-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <div>
            <h2>Core to M.Tech & Higher Studies Hub</h2>
            <p class="subtitle">Pathway: B.Tech ${branch.replace('BTECH_', '')} → GATE ${paperCode} → M.Tech / MS(R) / Direct PhD / PSU</p>
          </div>
          <span class="badge" style="background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; font-size: 0.85rem; padding: 4px 10px; border-radius: 6px;">
            Target Cycle: GATE 2027 (~${weeksUntil("2027-02-06")} weeks to the 6 Feb 2027 date in the knowledge base; date not verified)
          </span>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div style="display: flex; gap: 8px; border-bottom: 2px solid #e2e8f0; margin-bottom: 20px; overflow-x: auto; padding-bottom: 4px;">
        <button class="tab-btn active" data-tab="tab-overview" style="padding: 8px 16px; border: none; background: #2563eb; color: white; border-radius: 6px; cursor: pointer; font-weight: 500;">Weekly Plan & Focus</button>
        <button class="tab-btn" data-tab="tab-eligibility" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Eligibility & Route Fit</button>
        <button class="tab-btn" data-tab="tab-mastery" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Topic Mastery Map</button>
        <button class="tab-btn" data-tab="tab-mocks" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Mocks & Score Band</button>
        <button class="tab-btn" data-tab="tab-shortlist" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Programmes Shortlist</button>
        <button class="tab-btn" data-tab="tab-tracker" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Tracker & Conflicts</button>
        <button class="tab-btn" data-tab="tab-interview" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Interview & SOP</button>
        <button class="tab-btn" data-tab="tab-postresult" style="padding: 8px 16px; border: none; background: #f1f5f9; color: #475569; border-radius: 6px; cursor: pointer; font-weight: 500;">Post-Result Re-Plan</button>
      </div>

      <!-- Tab Content Area -->
      <div id="mtech-tab-content">
        <!-- Rendered dynamically -->
      </div>
    </div>
  `;

  const contentArea = container.querySelector("#mtech-tab-content");
  const tabButtons = container.querySelectorAll(".tab-btn");

  function switchTab(tabId) {
    tabButtons.forEach(btn => {
      if (btn.dataset.tab === tabId) {
        btn.style.background = "#2563eb";
        btn.style.color = "white";
      } else {
        btn.style.background = "#f1f5f9";
        btn.style.color = "#475569";
      }
    });

    if (tabId === "tab-overview") renderOverviewTab(contentArea, state);
    else if (tabId === "tab-eligibility") renderEligibilityTab(contentArea, state);
    else if (tabId === "tab-mastery") renderMasteryTab(contentArea, state);
    else if (tabId === "tab-mocks") renderMocksTab(contentArea, state);
    else if (tabId === "tab-shortlist") renderShortlistTab(contentArea, state);
    else if (tabId === "tab-tracker") renderTrackerTab(contentArea, state);
    else if (tabId === "tab-interview") renderInterviewTab(contentArea, state);
    else if (tabId === "tab-postresult") renderPostResultTab(contentArea, state);
  }

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => switchTab(btn.dataset.tab));
  });

  // Default to overview tab
  switchTab("tab-overview");
}

function renderOverviewTab(container, state) {
  const branch = branchOf(state);
  const paper = branch.includes("EE") ? "EE" : "MT";

  container.innerHTML = `${SAMPLE_NOTE}
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 20px;">
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
        <span style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase;">Study Budget Allocation</span>
        <div style="font-size: 1.5rem; font-weight: 700; color: #1e293b; margin: 4px 0;">15.0 hrs / week</div>
        <p style="font-size: 0.85rem; color: #475569; margin: 0;">10.5 hrs GATE Core Prep | 4.5 hrs Semester Course Protection</p>
      </div>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
        <span style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase;">Current Phase</span>
        <div style="font-size: 1.3rem; font-weight: 700; color: #1e293b; margin: 4px 0;">Phase 1: Foundation & High-Yield Core</div>
        <p style="font-size: 0.85rem; color: #0284c7; margin: 0;">Checkpoint: Diagnostic mastery >= 0.50 on foundational concepts</p>
      </div>

      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px;">
        <span style="font-size: 0.8rem; font-weight: 600; color: #64748b; text-transform: uppercase;">Zero-Timetable Guarantee</span>
        <div style="font-size: 1.1rem; font-weight: 600; color: #059669; margin: 4px 0;">Flexible Weekly Focus</div>
        <p style="font-size: 0.85rem; color: #475569; margin: 0;">No rigid daily time-slots. You choose when to accomplish weekly study goals.</p>
      </div>
    </div>

    <h3>This Week's Priority Guidance Cards</h3>
    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 12px;">
      <div style="border: 1px solid #cbd5e1; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 16px; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="display: inline-block; padding: 2px 8px; background: #eff6ff; color: #1d4ed8; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Core Subjects</span>
            <span style="display: inline-block; padding: 2px 8px; background: #ecfdf5; color: #047857; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">⚡ Double Benefit: Covers EE2L001 / ML2L001</span>
            <h4 style="margin: 6px 0 4px 0; color: #0f172a;">${paper === 'EE' ? 'Electric Circuits & Network Theorems' : 'Thermodynamics & Solution Equilibria'}</h4>
          </div>
          <span style="font-weight: 700; color: #334155; font-size: 0.9rem;">4.0 hrs suggested</span>
        </div>
        <p style="margin: 6px 0; font-size: 0.9rem; color: #334155;"><strong>What:</strong> Master Thevenin/Norton conversions and maximum power transfer under sinusoidal excitation.</p>
        <p style="margin: 6px 0; font-size: 0.9rem; color: #475569;"><strong>How:</strong> Active recall on governing mesh equations, followed by 10 past GATE PYQs.</p>
        <p style="margin: 6px 0; font-size: 0.85rem; color: #64748b;"><strong>Why:</strong> High frequency topic (9 marks 5-yr avg). Tested mastery currently at 45%.</p>
        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button disabled title="Not connected yet" style="opacity:0.6; cursor:not-allowed; padding: 6px 12px; background: #059669; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">✓ Mark Done</button>
          <button disabled title="Not connected yet" style="opacity:0.6; cursor:not-allowed; padding: 6px 12px; background: #f1f5f9; color: #475569; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Skip for Now</button>
          <button disabled title="Not connected yet" style="opacity:0.6; cursor:not-allowed; padding: 6px 12px; background: #f1f5f9; color: #64748b; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Not Useful</button>
        </div>
      </div>

      <div style="border: 1px solid #cbd5e1; border-left: 4px solid #8b5cf6; border-radius: 8px; padding: 16px; background: white;">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
          <div>
            <span style="display: inline-block; padding: 2px 8px; background: #f5f3ff; color: #6d28d9; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">Engineering Mathematics</span>
            <h4 style="margin: 6px 0 4px 0; color: #0f172a;">Linear Algebra & Eigenvalue Decomposition</h4>
          </div>
          <span style="font-weight: 700; color: #334155; font-size: 0.9rem;">3.5 hrs suggested</span>
        </div>
        <p style="margin: 6px 0; font-size: 0.9rem; color: #334155;"><strong>What:</strong> Solve characteristic equations, rank-nullity problems, and Cayley-Hamilton theorem calculations.</p>
        <p style="margin: 6px 0; font-size: 0.9rem; color: #475569;"><strong>How:</strong> Timed sectional problem set (25 mins for 10 problems) + NAT precision drill.</p>
        <p style="margin: 6px 0; font-size: 0.85rem; color: #64748b;"><strong>Why:</strong> Foundational prerequisite for control/signals. Guaranteed 3-4 marks on paper.</p>
        <div style="display: flex; gap: 8px; margin-top: 10px;">
          <button disabled title="Not connected yet" style="opacity:0.6; cursor:not-allowed; padding: 6px 12px; background: #059669; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">✓ Mark Done</button>
          <button disabled title="Not connected yet" style="opacity:0.6; cursor:not-allowed; padding: 6px 12px; background: #f1f5f9; color: #475569; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">Skip for Now</button>
        </div>
      </div>
    </div>
  `;
}

function renderEligibilityTab(container, state) {
  const branch = branchOf(state);
  const paper = branch.includes("EE") ? "EE" : "MT";
  const allowedSecond = branch.includes("EE") ? "IN, EC, DA" : "ME, XE, PI";
  const cgpa = cgpaOf(state);
  const year = yearOf(state);
  const eligibleNow = year !== null && year >= 3;

  container.innerHTML = `
    <h3>Deterministic Eligibility & Approved Route Fit</h3>
    ${eligibleNow
      ? `<div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
          <h4 style="margin: 0 0 6px 0; color: #065f46;">✓ Year ${esc(year)}: eligible to sit GATE (3rd year or above)</h4>`
      : `<div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
          <h4 style="margin: 0 0 6px 0; color: #92400e;">${year ? `Year ${esc(year)}: not eligible yet` : 'Year not recorded'}. GATE needs a student in the 3rd year or above.</h4>`}
      <p style="margin: 0; font-size: 0.9rem; color: #475569;">
        Rule used by this app: 3rd year or above. Confirm against the official GATE 2027 information brochure. The two-paper list below is sample data.
      </p>
    </div>

    <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
      <thead>
        <tr style="background: #f1f5f9; text-align: left; font-size: 0.85rem;">
          <th style="padding: 10px; border: 1px solid #e2e8f0;">Route / Paper Dimension</th>
          <th style="padding: 10px; border: 1px solid #e2e8f0;">Your Profile Criteria</th>
          <th style="padding: 10px; border: 1px solid #e2e8f0;">Official Rule Status</th>
          <th style="padding: 10px; border: 1px solid #e2e8f0;">Rule Citation</th>
        </tr>
      </thead>
      <tbody style="font-size: 0.85rem;">
        <tr>
          <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Primary Paper</strong></td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">GATE ${paper}</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0; color: ${eligibleNow ? '#059669' : '#d97706'}; font-weight: 600;">${eligibleNow ? 'Eligible now' : 'From 3rd year'}</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">gate2027.iitm.ac.in/papers</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Two-Paper Combination</strong></td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">Allowed: ${allowedSecond}</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0; color: #059669; font-weight: 600;">Permitted Combination</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">gate2027.iitm.ac.in/two_paper_combinations</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>Direct PhD Route</strong></td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">CGPA: ${cgpa === null ? 'not recorded' : esc(cgpa.toFixed(2))}</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0; color: ${cgpa !== null && cgpa >= 8.0 ? '#059669' : '#d97706'}; font-weight: 600;">
            ${cgpa === null ? 'Cannot assess without a CGPA' : (cgpa >= 8.0 ? 'Meets the 8.0 guideline used here' : 'Below the 8.0 guideline used here (M.Tech first recommended)')}
          </td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">iisc.ac.in/admissions/phd</td>
        </tr>
        <tr>
          <td style="padding: 10px; border: 1px solid #e2e8f0;"><strong>PSU Recruitment</strong></td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">Discipline: ${esc(branch)}</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0; color: #059669; font-weight: 600;">Eligible (POWERGRID, NTPC, SAIL)</td>
          <td style="padding: 10px; border: 1px solid #e2e8f0;">careers.psu.gov.in</td>
        </tr>
      </tbody>
    </table>
  `;
}

function renderMasteryTab(container, state) {
  const branch = branchOf(state);
  const paper = branch.includes("EE") ? "EE" : "MT";

  container.innerHTML = `
${SAMPLE_NOTE}
    <h3>GATE ${paper} Syllabus Topic Mastery & Weightage Map</h3>
    <p style="font-size: 0.85rem; color: #64748b;">
      Mastery is calculated via multi-weight Bayesian evidence. Self-declaration (0.2 weight) alone cannot achieve mastery.
    </p>

    <div style="overflow-x: auto; margin-top: 12px;">
      <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
        <thead>
          <tr style="background: #f1f5f9; text-align: left;">
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Syllabus Section</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Topic Name</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">5-Yr Weightage</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Tested Mastery</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Evidence Confidence</th>
            <th style="padding: 8px; border: 1px solid #e2e8f0;">Curriculum Link</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">General Aptitude</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Quantitative & Verbal Reasoning</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">15.0 Marks</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;"><span style="color: #059669; font-weight: 600;">72% (Proficient)</span></td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">88% (Tested)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">General Foundation</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Engineering Maths</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Linear Algebra & Calculus</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">13.0 Marks</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;"><span style="color: #0284c7; font-weight: 600;">64% (Developing)</span></td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">75% (Tested)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">MA1L001 / MA1L002</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Core Technical</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? 'Electric Circuits & Network Analysis' : 'Thermodynamics & Kinetics'}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? '9.5 Marks' : '14.0 Marks'}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;"><span style="color: #d97706; font-weight: 600;">48% (Focus Needed)</span></td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">60% (Mixed)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? 'EE2L001' : 'ML2L001'} (Full Match)</td>
          </tr>
          <tr>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">Core Technical</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? 'Power Electronics & Drives' : 'Physical Metallurgy & Transformations'}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? '9.0 Marks' : '15.0 Marks'}</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;"><span style="color: #dc2626; font-weight: 600;">35% (Weak)</span></td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">50% (Tested)</td>
            <td style="padding: 8px; border: 1px solid #e2e8f0;">${paper === 'EE' ? 'EE3L004' : 'ML2L002'}</td>
          </tr>
        </tbody>
      </table>
    </div>
  `;
}

function renderMocksTab(container, state) {
  container.innerHTML = `
${SAMPLE_NOTE}
    <h3>Mock Performance & Predicted Score Band</h3>
    
    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
        <div>
          <span style="font-size: 0.8rem; font-weight: 600; color: #475569; text-transform: uppercase;">Calibrated Score Band Estimate</span>
          <div style="font-size: 1.8rem; font-weight: 800; color: #1e3a8a;">670 – 745</div>
        </div>
        <span style="background: #e0f2fe; color: #0369a1; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: 600;">Derived from 3 Full Mocks</span>
      </div>
      <p style="font-size: 0.85rem; color: #64748b; margin-top: 8px;">
        <em>Uncertainty Note:</em> Score band is an advisory estimate derived from historical mock-to-actual calibration. 
        Actual GATE score depends on exam-day normalization and distribution. Never an admission guarantee.
      </p>
    </div>

    <h4>Error Log Mistake Breakdown</h4>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; margin-top: 10px;">
      <div style="background: #fef2f2; border: 1px solid #fecaca; padding: 12px; border-radius: 6px; text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #991b1b;">18%</div>
        <span style="font-size: 0.75rem; color: #7f1d1d; font-weight: 600;">Conceptual Gaps</span>
      </div>
      <div style="background: #fffbeb; border: 1px solid #fef3c7; padding: 12px; border-radius: 6px; text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #92400e;">42%</div>
        <span style="font-size: 0.75rem; color: #78350f; font-weight: 600;">Calculation / NAT Slip</span>
      </div>
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #334155;">24%</div>
        <span style="font-size: 0.75rem; color: #475569; font-weight: 600;">Question Misreading</span>
      </div>
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 700; color: #334155;">16%</div>
        <span style="font-size: 0.75rem; color: #475569; font-weight: 600;">Time Pressure</span>
      </div>
    </div>
  `;
}

function renderShortlistTab(container, state) {
  container.innerHTML = `
${SAMPLE_NOTE}
    <h3>Reach, Target & Safe Programme Shortlist</h3>
    <p style="font-size: 0.85rem; color: #64748b;">
      Tiering is computed by comparing your calibrated score band [670 - 745] against official past closing ranges.
      Unverified demonstration rows are explicitly tagged.
    </p>

    <div style="display: flex; flex-direction: column; gap: 12px; margin-top: 14px;">
      <!-- Reach -->
      <div style="border: 1px solid #fed7aa; background: #fffaf5; border-radius: 8px; padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="margin: 0; color: #c2410c;">[Reach] Indian Institute of Science Bangalore - Signal Processing / Microelectronics</h4>
          <span style="background: #ffedd5; color: #9a3412; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">Closing: 840–860</span>
        </div>
        <p style="margin: 6px 0; font-size: 0.85rem; color: #431407;">
          Ambitious target. Closing range is above current score band. Requires ~90-point increase on full mocks.
        </p>
        <div style="font-size: 0.75rem; color: #78350f;">Selection: Direct GATE score via COAP | Source: coap.iitm.ac.in (2024–2026 data)</div>
      </div>

      <!-- Target -->
      <div style="border: 1px solid #bfdbfe; background: #f8fbff; border-radius: 8px; padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="margin: 0; color: #1d4ed8;">[Target] IIT Bombay - Power Electronics & Power Systems</h4>
          <span style="background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">Closing: 730–775</span>
        </div>
        <p style="margin: 6px 0; font-size: 0.85rem; color: #1e3a8a;">
          Strongly competitive. Your score band directly overlaps historical closing rounds. High conversion chance.
        </p>
        <div style="font-size: 0.75rem; color: #1e40af;">Selection: COAP | Verified Deadline: Not confirmed yet (Check gate.iitb.ac.in)</div>
      </div>

      <!-- Safe -->
      <div style="border: 1px solid #bbf7d0; background: #f6fef9; border-radius: 8px; padding: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <h4 style="margin: 0; color: #15803d;">[Safe] NIT Tiruchirappalli - Power Systems Engineering</h4>
          <span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">Closing: 620–660</span>
        </div>
        <p style="margin: 6px 0; font-size: 0.85rem; color: #14532d;">
          High certainty backup. Current score band comfortably exceeds past round cutoffs.
        </p>
        <div style="font-size: 0.75rem; color: #166534;">Selection: CCMT Counselling | MHRD Assistantship: Rs. 12,400/month</div>
      </div>
    </div>
  `;
}

function renderTrackerTab(container, state) {
  container.innerHTML = `
${SAMPLE_NOTE}
    <h3>Application Tracker & Conflict Detection</h3>

    <div style="background: #fef2f2; border-left: 4px solid #ef4444; border-radius: 6px; padding: 14px; margin-bottom: 16px;">
      <h4 style="margin: 0 0 4px 0; color: #991b1b;">⚠️ Active Conflict Alert: Campus Placements vs. Mock Testing</h4>
      <p style="margin: 0 0 8px 0; font-size: 0.85rem; color: #7f1d1d;">
        Semester weeks 6-10 coincide with campus recruitment drives. Study hours risk fragmentation.
      </p>
      <div style="background: white; border-radius: 4px; padding: 8px; font-size: 0.8rem; color: #334155;">
        <strong>Recommended Strategy:</strong> Adopt Dual Track (12 hrs placement prep + 8 hrs high-weightage GATE topics). 
        Do not attempt full 3-hour mocks until placement testing window closes.
      </div>
    </div>

    <h4>Key Upcoming Milestones</h4>
    <ul style="font-size: 0.85rem; line-height: 1.8; color: #334155; padding-left: 20px;">
      <li><strong>2027-01-08:</strong> GATE 2027 Admit Card Download (GOAPS portal)</li>
      <li><strong>2027-02-06 to 2027-02-14:</strong> GATE 2027 Examination Weekend Sessions</li>
      <li><strong>2027-03-19:</strong> Official GATE 2027 Results & Scorecards Announcement</li>
      <li><strong>2027-05-12:</strong> COAP 2027 Round 1 Seat Allotment</li>
    </ul>
  `;
}

function renderInterviewTab(container, state) {
  container.innerHTML = `
    <h3>MS(R) / PhD Interview & SOP Practice</h3>
    <p style="font-size: 0.85rem; color: #64748b;">
      Practice technical interview questions and receive rubric feedback on your research statements.
    </p>

    <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; background: white;">
      <h4>Interactive Technical Interview Prompt</h4>
      <p style="font-size: 0.9rem; color: #1e293b; background: #f8fafc; padding: 10px; border-radius: 6px;">
        <strong>Question:</strong> "Explain how the reactive power flow affects bus voltage stability in an interconnected transmission line. What is the governing equation?"
      </p>
      <textarea id="interview-resp" rows="3" style="width: 100%; border: 1px solid #cbd5e1; border-radius: 4px; padding: 8px; font-size: 0.85rem;" placeholder="Type your technical reasoning here..."></textarea>
      <button id="btn-eval-interview" style="margin-top: 8px; padding: 8px 16px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;">Submit for Rubric Evaluation</button>
      <div id="interview-feedback-box" style="margin-top: 12px; display: none;"></div>
    </div>
  `;

  const btn = container.querySelector("#btn-eval-interview");
  const fbox = container.querySelector("#interview-feedback-box");
  // Scores the typed answer with the deterministic GATE interview rubric on the server (it used to show a fixed 86/100)
  btn.addEventListener("click", async () => {
    const answer = container.querySelector("#interview-resp").value.trim();
    fbox.style.display = "block";
    if (!answer) { fbox.innerHTML = `<div class="alert alert-warning">Type an answer first.</div>`; return; }
    fbox.innerHTML = `<div class="loading-state">Scoring against the rubric...</div>`;
    btn.disabled = true;
    try {
      const r = await api.mtechInterview(state.studentId, "REACTIVE_POWER_VOLTAGE_STABILITY", answer);
      const b = r.rubric_breakdown || {};
      fbox.innerHTML = `
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; padding: 12px; border-radius: 6px;">
          <h4 style="margin: 0 0 6px 0; color: #166534;">Rubric score: ${esc(r.total_score)} / 100</h4>
          <ul style="font-size: 0.8rem; color: #14532d; padding-left: 18px; margin: 4px 0;">
            <li>Technical accuracy: ${esc(b.technical_accuracy)}/25 | Mathematical rigour: ${esc(b.mathematical_rigor)}/25</li>
            <li>Practical application: ${esc(b.practical_application)}/25 | Clarity: ${esc(b.clarity_of_expression)}/25</li>
          </ul>
          <ul style="font-size: 0.8rem; color: #15803d; padding-left: 18px; margin: 4px 0;">
            ${(r.feedback || []).map((f) => `<li>${esc(f)}</li>`).join('')}
          </ul>
          <p class="small muted" style="margin:4px 0 0;">Keyword-based rubric: it checks for technical terms, governing laws, an engineering example and length, not correctness.</p>
        </div>`;
    } catch (err) {
      fbox.innerHTML = `<div class="alert alert-error">${esc(err.message || err)}</div>`;
    } finally {
      btn.disabled = false;
    }
  });
}

function renderPostResultTab(container, state) {
  container.innerHTML = `
${SAMPLE_NOTE}
    <h3>Post-Result Re-Planner</h3>
    <p style="font-size: 0.85rem; color: #64748b;">
      Enter your official GATE score to recalculate realistic options and explore trade-offs.
    </p>

    <div style="display: flex; gap: 12px; align-items: flex-end; margin-bottom: 20px;">
      <div>
        <label style="display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 4px;">Actual GATE Score (out of 1000)</label>
        <input type="number" id="actual-score-input" value="510" style="padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; width: 140px;" />
      </div>
      <div>
        <label style="display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 4px;">All India Rank (AIR)</label>
        <input type="number" id="actual-rank-input" value="2650" style="padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px; width: 140px;" />
      </div>
      <button id="btn-replan" disabled title="Not connected yet: use the Adapt Simulator's M.Tech result scenario" style="opacity:0.6; cursor:not-allowed; "padding: 9px 18px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; font-weight: 600;">Recompute Pathways</button>
    </div>

    <div id="replan-results-box">
      <div style="background: #fffbeb; border: 1px solid #fef3c7; border-radius: 8px; padding: 14px;">
        <h4 style="margin: 0 0 6px 0; color: #92400e;">Realistic Alternatives Analysis (Score: 510)</h4>
        <p style="font-size: 0.85rem; color: #78350f; margin: 0 0 8px 0;">
          Your score is below traditional cutoffs for top-5 IIT M.Tech TA programmes. Realistic pathways available:
        </p>
        <ul style="font-size: 0.8rem; color: #78350f; padding-left: 18px; margin: 0;">
          <li><strong>MS (Research) Route:</strong> Written test & interview account for 30-50% selection weightage (IIT BBS, IIT Mandi, IIT Ropar).</li>
          <li><strong>Interdisciplinary Programmes:</strong> Energy Studies, Materials Nanotech, Reliability Engineering.</li>
          <li><strong>NIT Central Counselling (CCMT):</strong> VNIT Nagpur, NIT Rourkela, NIT Silchar.</li>
          <li><strong>Retake Strategy:</strong> Score remains valid for 3 years; prepare for GATE 2028 with 12-month template while holding backup admission.</li>
        </ul>
      </div>
    </div>
  `;
}
