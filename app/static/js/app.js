/* ==============================================================================
   EBuddy Web UI Shell — Frontend Vanilla JS
   Zero Outbound / Relative Paths Only / Traceable KB Codes
   ============================================================================== */

const EBuddy = {
  // Active student & goal management
  getActiveStudentId() {
    return localStorage.getItem("ebuddy_active_student_id") || "CONF_STU_EE_POWER_01";
  },

  setActiveStudentId(studentId) {
    localStorage.setItem("ebuddy_active_student_id", studentId);
    window.location.reload();
  },

  getActiveGoalId(studentId) {
    return localStorage.getItem("ebuddy_active_goal_" + studentId) || "";
  },

  setActiveGoalId(studentId, goalId) {
    if (goalId) {
      localStorage.setItem("ebuddy_active_goal_" + studentId, goalId);
    }
  },

  switchRoadmapTab(tab) {
    const tabs = ['gantt', 'academics', 'today', 'list'];
    tabs.forEach(t => {
      const content = document.getElementById(`tab-content-${t}`);
      const btn = document.getElementById(`tab-btn-${t}`);
      if (content) content.style.display = (t === tab) ? 'block' : 'none';
      if (btn) {
        btn.className = (t === tab) ? 'btn btn-sm btn-primary' : 'btn btn-sm btn-secondary';
      }
    });
  },

  showItemModal(item) {
    const modal = document.getElementById("item-modal");
    const titleEl = document.getElementById("modal-title");
    const catEl = document.getElementById("modal-category");
    const bodyEl = document.getElementById("modal-body");
    if (!modal || !bodyEl) return;

    catEl.textContent = `${item.item_type || 'COURSE'} • Semester ${item.semester_number || 1}`;
    titleEl.textContent = item.title || item.kb_code;

    const badges = [];
    if (item.status_badge) badges.push(`<span class="badge badge-info">${item.status_badge}</span>`);
    if (item.status) badges.push(`<span class="badge badge-${item.status === 'verified' ? 'verified' : 'draft'}">${item.status}</span>`);
    if (item.is_indicative) badges.push(`<span class="badge badge-warning">Indicative (Assumed)</span>`);

    bodyEl.innerHTML = `
      <div style="display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; align-items: center;">
        <span class="badge badge-code">${item.kb_code}</span>
        ${badges.join(" ")}
        <span style="font-weight: 700; color: var(--text-secondary); margin-left: auto;">
          ${item.hours_per_week ? `${item.hours_per_week} hrs/wk` : ''} ${item.credits ? `• ${item.credits} Credits` : ''}
        </span>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Skill Gap Reason</div>
        <p style="font-size: 0.95rem; color: var(--text-primary); margin-top: 2px;">
          ${item.skill_gap_reason || item.reason?.why_this || 'Mandatory degree curriculum requirement'}
        </p>
      </div>

      ${item.goal_emphasis ? `
        <div style="margin-bottom: 14px; background: #eff6ff; border-left: 3px solid #2563eb; padding: 10px 14px; border-radius: var(--radius-sm);">
          <div style="font-size: 0.8rem; font-weight: 700; color: #1e40af;">GOAL EMPHASIS NOTE</div>
          <div style="font-size: 0.9rem; color: #1e3a8a; margin-top: 2px;">${item.goal_emphasis}</div>
        </div>
      ` : ''}

      <div style="margin-bottom: 14px;">
        <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Rationale & Alignment</div>
        <p style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 2px;">
          ${item.reason?.why_this || item.reason?.intent || 'Official curriculum allocation'}
        </p>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border-light); font-size: 0.85rem;">
        <div>
          <span style="color: var(--text-muted);">Cited KB Codes:</span>
          <div>${(item.cited_kb_codes && item.cited_kb_codes.length) ? item.cited_kb_codes.map(c => `<code>${c}</code>`).join(", ") : `<code>${item.kb_code}</code>`}</div>
        </div>
        <div>
          <span style="color: var(--text-muted);">Rule Compliance:</span>
          <div>${(item.reason?.rule_compliance && item.reason.rule_compliance.length) ? item.reason.rule_compliance.join("; ") : 'Academic curriculum verified'}</div>
        </div>
      </div>
    `;

    modal.style.display = "flex";
  },

  setupGoalIntake(inputId, btnId, feedbackId, onConfirmed) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    const feedback = document.getElementById(feedbackId);
    if (!input || !btn || !feedback) return;

    btn.onclick = async () => {
      const text = input.value.trim();
      if (!text) return alert("Please enter your target goal or aspiration.");
      const studentId = this.getActiveStudentId();

      btn.disabled = true;
      btn.textContent = "Routing...";
      feedback.style.display = "block";
      feedback.innerHTML = `<div style="color: var(--text-muted);">Analyzing goal intent via Intent Router...</div>`;

      try {
        const res = await fetch("/api/goals/route", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: studentId, goal_text: text })
        });
        const rData = await res.json();

        const confGoal = rData.goal_id || rData.canonical_goal_id || rData.primary_goal_id;
        const confSentence = rData.confirmation_sentence || `I understood your goal as ${confGoal}. Is that right?`;
        const alts = (rData.alternatives || []).map(a => a.goal_id || a) || rData.alternative_goal_ids || [];

        feedback.innerHTML = `
          <div class="alert alert-info" style="border: 2px solid var(--color-accent); padding: 14px 16px;">
            <div style="font-size: 1.05rem; font-weight: 600; color: var(--color-primary); margin-bottom: 10px;">
              💬 "${confSentence}"
            </div>
            <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
              <button id="btn-confirm-routed-goal-${btnId}" class="btn btn-sm btn-primary" style="font-weight: 700;">
                ✓ Yes, Confirm & Build Roadmap (${confGoal})
              </button>
            </div>
            ${alts.length ? `
              <div style="margin-top: 10px; font-size: 0.85rem; color: var(--text-muted);">
                Or choose an alternative route:
                <div style="display: inline-flex; gap: 6px; margin-left: 6px; flex-wrap: wrap;">
                  ${alts.map(a => `<button type="button" class="btn btn-sm btn-outline alt-choice-btn" data-goal="${a}" style="padding: 2px 8px; font-size: 0.8rem;">${a}</button>`).join(" ")}
                </div>
              </div>
            ` : ''}
          </div>
        `;

        const confirmBtn = document.getElementById(`btn-confirm-routed-goal-${btnId}`);
        if (confirmBtn) {
          confirmBtn.onclick = async () => {
            confirmBtn.disabled = true;
            confirmBtn.textContent = "Generating Roadmap...";
            await onConfirmed(confGoal);
          };
        }

        feedback.querySelectorAll(".alt-choice-btn").forEach(b => {
          b.onclick = async (e) => {
            const altGoal = e.target.getAttribute("data-goal");
            b.disabled = true;
            await onConfirmed(altGoal);
          };
        });

      } catch (e) {
        feedback.innerHTML = `<div class="alert alert-danger">Routing error: ${e.message}</div>`;
      } finally {
        btn.disabled = false;
        btn.textContent = (btnId === "btn-route-goal") ? "Route My Goal" : "Switch Goal";
      }
    };
  },

  async initNavbar() {
    const selector = document.getElementById("nav-student-select");
    if (!selector) return;

    try {
      const res = await fetch("/api/students");
      const data = await res.json();
      const current = this.getActiveStudentId();

      selector.innerHTML = "";
      (data.students || []).forEach(stu => {
        const opt = document.createElement("option");
        opt.value = stu.student_id;
        opt.textContent = `${stu.name} (${stu.programme_id}, Sem ${stu.current_semester})`;
        if (stu.student_id === current) opt.selected = true;
        selector.appendChild(opt);
      });

      selector.addEventListener("change", (e) => {
        this.setActiveStudentId(e.target.value);
      });
    } catch (err) {
      console.error("Failed to populate student selector:", err);
    }
  },

  // ---------------------------------------------------------------------------
  // Page 1: Home
  // ---------------------------------------------------------------------------
  async initHome() {
    const studentId = this.getActiveStudentId();
    const infoEl = document.getElementById("student-profile-info");
    const coursesEl = document.getElementById("completed-courses-list");
    if (!infoEl) return;

    try {
      const res = await fetch(`/api/students/${studentId}`);
      if (!res.ok) throw new Error("Student not found");
      const data = await res.json();

      infoEl.innerHTML = `
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px;">
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">STUDENT ID</div>
            <div style="font-size: 1.1rem; font-weight: 700; font-family: var(--font-mono);">${data.student_id}</div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">NAME</div>
            <div style="font-size: 1.1rem; font-weight: 600;">${data.name}</div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">PROGRAMME</div>
            <div><span class="badge badge-info">${data.programme_id}</span></div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">SEMESTER</div>
            <div style="font-size: 1.1rem; font-weight: 600;">Semester ${data.current_semester}</div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">CGPA</div>
            <div style="font-size: 1.1rem; font-weight: 700; color: #15803d;">${data.cgpa || 8.0}</div>
          </div>
          <div>
            <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">ACTIVE BACKLOGS</div>
            <div style="font-size: 1.1rem; font-weight: 600;">${data.backlogs || 0}</div>
          </div>
        </div>
      `;

      if (coursesEl) {
        if (!data.completed_courses || data.completed_courses.length === 0) {
          coursesEl.innerHTML = `<span style="color: var(--text-muted);">None recorded (First Year Common Curriculum completed)</span>`;
        } else {
          coursesEl.innerHTML = data.completed_courses.map(c => `
            <span class="badge badge-code" style="margin: 4px; display: inline-block;">
              ✓ ${c}
            </span>
          `).join(" ");
        }
      }
    } catch (err) {
      infoEl.innerHTML = `<div class="alert alert-danger">Error loading student profile: ${err.message}</div>`;
    }
  },

  // ---------------------------------------------------------------------------
  // Page 2: Goals
  // ---------------------------------------------------------------------------
  async initGoals() {
    const studentId = this.getActiveStudentId();
    const container = document.getElementById("goals-container");
    if (!container) return;

    // Intelligent Goal Intake Setup
    this.setupGoalIntake("goal-intake-input", "btn-route-goal", "goal-route-feedback", async (goalId) => {
      try {
        const buildRes = await fetch("/api/goals/confirm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: studentId, goal_id: goalId })
        });
        if (!buildRes.ok) throw new Error("Failed to confirm goal");
        this.setActiveGoalId(studentId, goalId);
        window.location.href = "/roadmap";
      } catch (e) {
        alert("Error setting goal: " + e.message);
      }
    });

    try {
      const sRes = await fetch(`/api/students/${studentId}`);
      const student = await sRes.json();
      const prog = student.programme_id || "BTECH_EE";

      const gRes = await fetch(`/api/goals?programme_id=${prog}`);
      const gData = await gRes.json();
      const activeGoal = this.getActiveGoalId(studentId) || (student.goal_id || "");

      container.innerHTML = (gData.goals || []).map((g, idx) => {
        const isChecked = activeGoal ? (g.goal_id === activeGoal) : (idx === 0);
        return `
        <div class="card" style="margin-bottom: 16px; border: 2px solid ${isChecked ? 'var(--color-accent)' : 'var(--border-light)'};">
          <label style="display: flex; gap: 16px; cursor: pointer; align-items: flex-start;">
            <input type="radio" name="selected_goal" value="${g.goal_id}" ${isChecked ? 'checked' : ''} style="margin-top: 6px; width: 18px; height: 18px;">
            <div style="flex: 1;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span class="badge badge-code">${g.goal_id}</span>
                <span class="badge badge-${g.status === 'verified' ? 'verified' : 'draft'}">${g.status}</span>
                <span class="badge badge-info">${g.category}</span>
              </div>
              <h3 style="font-size: 1.15rem; color: var(--color-primary); margin-bottom: 4px;">${g.name}</h3>
              <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 8px;">${g.description}</p>
              <div style="font-size: 0.8rem; color: var(--text-muted);">
                Target Skill Requirements: <strong>${g.skill_requirements_count}</strong> | Source: <code>${g.source_id}</code>
              </div>
            </div>
          </label>
        </div>
      `;
      }).join("");

      const btn = document.getElementById("btn-build-roadmap");
      if (btn) {
        btn.onclick = async () => {
          const checked = document.querySelector('input[name="selected_goal"]:checked');
          if (!checked) return alert("Please select a target goal.");
          const goalId = checked.value;

          btn.disabled = true;
          btn.textContent = "Building Roadmap with Agent 1...";

          try {
            const buildRes = await fetch("/api/goals/confirm", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ student_id: studentId, goal_id: goalId })
            });
            if (!buildRes.ok) throw new Error("Failed to generate plan");
            this.setActiveGoalId(studentId, goalId);
            window.location.href = "/roadmap";
          } catch (e) {
            alert("Error building roadmap: " + e.message);
            btn.disabled = false;
            btn.textContent = "🚀 Build My Roadmap";
          }
        };
      }
    } catch (err) {
      container.innerHTML = `<div class="alert alert-danger">Error loading goals: ${err.message}</div>`;
    }
  },

  // ---------------------------------------------------------------------------
  // Page 3: Roadmap
  // ---------------------------------------------------------------------------
  async initRoadmap() {
    const studentId = this.getActiveStudentId();
    const activeGoalId = this.getActiveGoalId(studentId);

    const ganttContainer = document.getElementById("gantt-chart-container");
    const academicsContainer = document.getElementById("locked-academics-container");
    const todayContainer = document.getElementById("today-tasks-container");
    const container = document.getElementById("roadmap-container");
    const warningsEl = document.getElementById("roadmap-warnings");
    const proposalsEl = document.getElementById("roadmap-proposals");
    const activeCtxEl = document.getElementById("active-context-display");

    // Quick Goal Switcher setup
    this.setupGoalIntake("roadmap-quick-goal", "btn-quick-route-goal", "roadmap-quick-feedback", async (goalId) => {
      try {
        const buildRes = await fetch("/api/goals/confirm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: studentId, goal_id: goalId })
        });
        if (!buildRes.ok) throw new Error("Failed to switch goal");
        this.setActiveGoalId(studentId, goalId);
        window.location.reload();
      } catch (e) {
        alert("Error switching goal: " + e.message);
      }
    });

    try {
      // 1. Fetch Student Profile
      const sRes = await fetch(`/api/students/${studentId}`);
      const student = await sRes.json();

      // 2. Fetch Roadmap
      const url = `/api/roadmap/${studentId}${activeGoalId ? '?goal_id=' + activeGoalId : ''}`;
      const res = await fetch(url);
      if (!res.ok) {
        if (ganttContainer) {
          ganttContainer.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
              <h3>No Roadmap Generated Yet</h3>
              <p style="color: var(--text-muted); margin: 12px 0;">Build your personalized curriculum roadmap by selecting your target goal.</p>
              <a href="/goals" class="btn btn-primary">Select Goal & Build Roadmap</a>
            </div>
          `;
        }
        return;
      }
      const data = await res.json();
      if (data.goal_id) {
        this.setActiveGoalId(studentId, data.goal_id);
      }

      // Active Context Display
      if (activeCtxEl) {
        activeCtxEl.innerHTML = `
          <span>${student.name || studentId}</span>
          <span class="badge badge-info" style="margin-left: 6px;">${student.programme_id || ''} Sem ${student.current_semester || ''}</span>
          <span style="color: var(--text-muted); margin: 0 8px;">•</span>
          <span>Target Goal: <strong>${data.goal_name || data.goal_id || 'None'}</strong></span>
          <span class="badge badge-code" style="margin-left: 6px;">${data.goal_id || 'NO_GOAL'}</span>
        `;
      }

      // Warnings
      if (warningsEl) {
        const warns = data.warnings || [];
        if (warns.length > 0) {
          warningsEl.innerHTML = warns.map(w => `
            <div class="alert alert-warning" style="margin-bottom: 8px;">
              <strong>⚠️ Advisory Notice:</strong> ${w}
            </div>
          `).join("");
        } else {
          warningsEl.innerHTML = "";
        }
      }

      // Version badge
      const verEl = document.getElementById("roadmap-version-badge");
      if (verEl) {
        verEl.innerHTML = `
          <span class="badge badge-info" style="font-size: 0.9rem; padding: 6px 12px;">
            Roadmap Version ${data.version} (${data.committed_by})
          </span>
          <span style="font-size: 0.85rem; color: var(--text-muted); margin-left: 12px;">
            Total Planned Credits: <strong>${data.total_credits}</strong> across ${data.total_items} items
          </span>
        `;
      }

      // Pending proposals
      if (proposalsEl) {
        const props = data.pending_proposals || [];
        if (props.length > 0) {
          proposalsEl.innerHTML = `
            <div class="alert alert-info" style="display: flex; justify-content: space-between; align-items: center;">
              <div>
                <strong>⚖ ${props.length} Pending Change Proposal(s) awaiting your decision.</strong>
              </div>
              <a href="/approvals" class="btn btn-sm btn-primary">Review Proposals</a>
            </div>
          `;
        } else {
          proposalsEl.innerHTML = "";
        }
      }

      // Flatten items from all semesters for Gantt and Academics
      const allSemesters = data.semesters || [];
      const allItems = [];
      allSemesters.forEach(s => {
        (s.items || []).forEach(it => {
          allItems.push({ ...it, semester_number: it.semester_number || s.semester_number });
        });
      });

      // -----------------------------------------------------------------------
      // TAB 1: RENDER GANTT CHART
      // -----------------------------------------------------------------------
      if (ganttContainer) {
        const numCols = Math.max(1, allSemesters.length);
        const swimlanes = [
          {
            id: "academics",
            label: "Academics (Degree Core)",
            desc: "Locked Curriculum Commitments",
            filter: it => it.item_type === "REQUIRED_COURSE" || it.status_badge === "LOCKED" || it.item_type === "course",
            barClass: "bar-academics"
          },
          {
            id: "goal_prep",
            label: "Goal Prep & Electives",
            desc: "Career & Domain Specialization",
            filter: it => ["ELECTIVE_PICK", "RESOURCE", "PROJECT", "RESEARCH_TASTER"].includes(it.item_type) && it.status_badge !== "LOCKED",
            barClass: "bar-goal-prep"
          },
          {
            id: "practice",
            label: "Practice & Exercises",
            desc: "Skill Gaps & Problem Drills",
            filter: it => ["EXERCISE_SET", "exercise"].includes(it.item_type),
            barClass: "bar-practice"
          },
          {
            id: "milestones",
            label: "Milestones & Exam Gates",
            desc: "Assessments & Entrance Dates",
            filter: it => ["CHECKPOINT", "BUFFER_EXAM_WEEK", "milestone"].includes(it.item_type) || ["CHECKPOINT", "PROJECTED_INDICATIVE"].includes(it.status_badge),
            barClass: "bar-milestones"
          }
        ];

        let ganttHtml = `
          <div class="gantt-wrapper" style="--gantt-cols: ${numCols};">
            <!-- Header Row: Semesters -->
            <div class="gantt-header-row">
              <div class="gantt-header-cell">Swimlanes / Horizon</div>
              ${allSemesters.map(s => `
                <div class="gantt-header-cell">
                  <div>Semester ${s.semester_number}</div>
                  <div style="font-size: 0.75rem; font-weight: normal; color: var(--text-muted);">${s.semester_name || ''}</div>
                </div>
              `).join("")}
            </div>
        `;

        // Render each swimlane
        swimlanes.forEach(lane => {
          ganttHtml += `
            <div class="gantt-lane-row">
              <div class="gantt-lane-label">
                <div>${lane.label}</div>
                <div style="font-size: 0.75rem; font-weight: normal; color: var(--text-muted);">${lane.desc}</div>
              </div>
              ${allSemesters.map(s => {
                const laneItems = (s.items || []).filter(lane.filter);
                return `
                  <div class="gantt-lane-cell">
                    ${laneItems.length ? laneItems.map(it => {
                      const badgeClass = it.status_badge === 'LOCKED' ? 'badge-locked' :
                                         it.status_badge === 'PROJECTED_INDICATIVE' ? 'badge-projected' :
                                         it.status_badge === 'CHECKPOINT' ? 'badge-checkpoint' : 'badge-code';
                      return `
                        <div class="gantt-bar ${lane.barClass}" data-item-id="${it.item_id}" title="Click to view complete syllabus and prerequisite evidence">
                          <div style="display: flex; justify-content: space-between; align-items: center; gap: 4px;">
                            <span class="badge ${badgeClass}" style="font-size: 0.7rem; padding: 2px 6px;">${it.kb_code}</span>
                            <span style="font-size: 0.7rem; color: var(--text-muted); font-weight: 700;">${it.hours_per_week || it.estimated_hours || 4}h/w</span>
                          </div>
                          <div style="font-size: 0.8rem; font-weight: 600; line-height: 1.2; margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${it.title}
                          </div>
                        </div>
                      `;
                    }).join("") : `<span style="color: #cbd5e1; font-size: 0.75rem; text-align: center;">—</span>`}
                  </div>
                `;
              }).join("")}
            </div>
          `;
        });

        ganttHtml += `</div>`;
        ganttContainer.innerHTML = ganttHtml;

        // Attach click listener for modal
        ganttContainer.querySelectorAll(".gantt-bar").forEach(el => {
          el.onclick = () => {
            const iid = el.getAttribute("data-item-id");
            const it = allItems.find(x => x.item_id === iid);
            if (it) EBuddy.showItemModal(it);
          };
        });
      }

      // -----------------------------------------------------------------------
      // TAB 2: LOCKED ACADEMICS CONTEXT
      // -----------------------------------------------------------------------
      if (academicsContainer) {
        const lockedCourses = allItems.filter(it => it.item_type === "REQUIRED_COURSE" || it.status_badge === "LOCKED");
        academicsContainer.innerHTML = `
          <div class="card" style="margin-bottom: 24px;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 12px; border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
              <span style="font-size: 1.4rem;">🔒</span>
              <div>
                <h3 style="color: var(--color-primary); font-size: 1.15rem; margin: 0;">Institutional Curriculum: Mandatory Degree Requirements</h3>
                <p style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 2px;">
                  These mandatory degree core courses represent locked institutional commitments. They are displayed for transparent workload accounting and are <strong>never</strong> presented as elective recommendations.
                </p>
              </div>
            </div>

            <table>
              <thead>
                <tr>
                  <th>Semester</th>
                  <th>Course Code</th>
                  <th>Course Title</th>
                  <th>Credits</th>
                  <th>Est. Weekly Study</th>
                  <th>Status</th>
                  <th>Goal Emphasis / Mastery Focus</th>
                </tr>
              </thead>
              <tbody>
                ${lockedCourses.map(c => `
                  <tr>
                    <td><strong>Sem ${c.semester_number}</strong></td>
                    <td><code>${c.kb_code}</code></td>
                    <td><strong>${c.title}</strong></td>
                    <td>${c.credits || 4.0}</td>
                    <td>${c.hours_per_week || 4.0} hrs/wk</td>
                    <td><span class="badge badge-locked">LOCKED CORE</span></td>
                    <td style="font-size: 0.85rem; color: var(--text-secondary);">
                      ${c.goal_emphasis || (c.reason?.intent || 'Mandatory Degree Core Requirement')}
                    </td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          </div>
        `;
      }

      // -----------------------------------------------------------------------
      // TAB 3: WEEK 1 DAILY TASKS ("TODAY" VIEW)
      // -----------------------------------------------------------------------
      if (todayContainer) {
        try {
          const wRes = await fetch(`/api/roadmap/${studentId}/weekly?week_number=1${data.goal_id ? '&goal_id=' + data.goal_id : ''}`);
          if (wRes.ok) {
            const wData = await wRes.json();
            const daily = wData.daily_tasks || [];

            todayContainer.innerHTML = `
              <div class="card" style="margin-bottom: 24px;">
                <div style="background: #f0fdf4; border: 1px solid #86efac; border-radius: var(--radius-md); padding: 14px 18px; margin-bottom: 18px;">
                  <div style="font-weight: 700; color: #166534; font-size: 0.95rem;">
                    ✓ Zero REQUIRED_COURSE lecture tasks in Daily Plan
                  </div>
                  <div style="font-size: 0.85rem; color: #15803d; margin-top: 2px;">
                    Mandatory academic coursework remains as locked background context. All daily actionable tasks focus strictly on active goal preparation, practice problem sets, critical reading, and exam simulations.
                  </div>
                </div>

                <h3 style="color: var(--color-primary); font-size: 1.15rem; margin-bottom: 14px;">
                  Week 1 Structured Daily Schedule (${data.goal_name || data.goal_id})
                </h3>

                <div style="display: flex; flex-direction: column; gap: 12px;">
                  ${daily.map(d => {
                    const typeBadge = d.task_type === 'practice_exercise' ? 'badge-verified' :
                                      d.task_type === 'reading' ? 'badge-info' :
                                      d.task_type === 'quiz' ? 'badge-draft' : 'badge-code';
                    return `
                      <div style="border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 14px; background: #ffffff; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                        <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                          <div style="font-weight: 700; font-size: 0.9rem; color: var(--color-primary); min-width: 65px;">
                            Day ${d.day_number}
                          </div>
                          <div>
                            <div style="display: flex; align-items: center; gap: 8px;">
                              <span class="badge ${typeBadge}">${d.task_type}</span>
                              <strong style="font-size: 0.95rem; color: var(--text-primary);">${d.title}</strong>
                            </div>
                            <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 4px;">
                              Focus Skill: <code>${d.skill_id || 'General Competency'}</code> ${d.exercise_id ? `| Exercise: <code>${d.exercise_id}</code>` : ''}
                            </div>
                          </div>
                        </div>
                        <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary);">
                          ${d.estimated_minutes} mins
                        </div>
                      </div>
                    `;
                  }).join("")}
                </div>
              </div>
            `;
          }
        } catch (we) {
          todayContainer.innerHTML = `<div class="alert alert-warning">Could not load weekly schedule: ${we.message}</div>`;
        }
      }

      // -----------------------------------------------------------------------
      // TAB 4: FULL SEMESTER CARD LIST
      // -----------------------------------------------------------------------
      if (container) {
        container.innerHTML = allSemesters.map(sem => `
          <div class="card" style="margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 12px; margin-bottom: 16px;">
              <div>
                <h3 style="font-size: 1.2rem; color: var(--color-primary);">Semester ${sem.semester_number}</h3>
                <span style="font-size: 0.85rem; color: var(--text-muted);">${sem.semester_name || ''}</span>
              </div>
              <span class="badge badge-info" style="font-size: 0.85rem;">
                Credits: ${sem.semester_credits}
              </span>
            </div>

            <div style="display: flex; flex-direction: column; gap: 12px;">
              ${sem.items.map(it => `
                <div style="border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 14px; background: #fafafa; cursor: pointer;" onclick='EBuddy.showItemModal(${JSON.stringify(it).replace(/'/g, "&#39;")})'>
                  <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                      <span class="badge badge-code" style="font-size: 0.85rem;">${it.kb_code}</span>
                      <span class="badge badge-${it.status === 'verified' ? 'verified' : 'draft'}">${it.status}</span>
                      <span class="badge badge-info">${it.item_type}</span>
                      <strong style="font-size: 1.05rem; margin-left: 8px; color: var(--text-primary);">${it.title}</strong>
                    </div>
                    <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary);">${it.credits} Credits</span>
                  </div>

                  <div style="margin-top: 8px; font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5;">
                    <strong>Why this item:</strong> ${it.skill_gap_reason || it.reason?.why_this || it.reason?.intent || 'Curriculum Requirement'}
                  </div>

                  ${it.reason?.target_skills?.length ? `
                    <div style="margin-top: 6px; font-size: 0.8rem; color: var(--text-muted);">
                      Skills: ${it.reason.target_skills.map(s => `<code>${s}</code>`).join(", ")}
                    </div>
                  ` : ''}
                </div>
              `).join("")}
            </div>
          </div>
        `).join("");
      }

    } catch (err) {
      if (ganttContainer) {
        ganttContainer.innerHTML = `<div class="alert alert-danger">Error loading roadmap: ${err.message}</div>`;
      }
    }
  },

  // ---------------------------------------------------------------------------
  // Page 4: Diagnostic
  // ---------------------------------------------------------------------------
  async initDiagnostic() {
    const studentId = this.getActiveStudentId();
    const container = document.getElementById("diagnostic-container");
    if (!container) return;

    const loadQuestion = async () => {
      try {
        const res = await fetch(`/api/diagnostic/${studentId}/next`);
        const data = await res.json();

        if (data.complete) {
          const st = data.state || {};
          container.innerHTML = `
            <div class="card" style="text-align: center; padding: 36px;">
              <span class="badge badge-verified" style="font-size: 1rem; padding: 6px 16px; margin-bottom: 16px;">
                ✓ ASSESSMENT COMPLETE
              </span>
              <h2 style="margin: 16px 0; color: var(--color-primary);">Adaptive Ability Assessment Concluded</h2>
              <div style="font-size: 2.5rem; font-weight: 800; color: var(--color-accent); margin-bottom: 8px;">
                ${st.ability_estimate || 50.0} <span style="font-size: 1.2rem; color: var(--text-muted);">/ 100</span>
              </div>
              <p style="color: var(--text-secondary); margin-bottom: 20px;">
                Confidence Spread Rating: <strong>${st.confidence >= 0.84 ? 'High Confidence (Converged)' : 'Moderate Confidence'}</strong> (${st.confidence || 0.85})
              </p>
              <div style="display: flex; justify-content: center; gap: 12px;">
                <a href="/roadmap" class="btn btn-primary">View Adapted Roadmap</a>
                <button id="btn-restart-diag" class="btn btn-secondary">Retake Assessment</button>
              </div>
            </div>
          `;
          const restartBtn = document.getElementById("btn-restart-diag");
          if (restartBtn) {
            restartBtn.onclick = async () => {
              await fetch("/api/diagnostic/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ student_id: studentId })
              });
              loadQuestion();
            };
          }
          return;
        }

        const ex = data.exercise;
        const st = data.state || {};
        const qNum = (st.answers_count || 0) + 1;

        container.innerHTML = `
          <div class="card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid var(--border-light); padding-bottom: 12px;">
              <div>
                <span class="badge badge-code">${ex.exercise_id}</span>
                <span class="badge badge-${ex.status === 'verified' ? 'verified' : 'draft'}">${ex.status}</span>
                <span class="badge badge-info">${ex.skill_id}</span>
              </div>
              <span style="font-weight: 700; font-size: 0.9rem; color: var(--text-secondary);">
                Question ${qNum} of max ${st.max_items || 8}
              </span>
            </div>

            <h3 style="font-size: 1.15rem; line-height: 1.6; margin-bottom: 20px; color: var(--text-primary);">
              ${ex.question_text}
            </h3>

            <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 24px;">
              ${(ex.options || []).map((opt, i) => `
                <label style="display: flex; gap: 12px; align-items: center; padding: 12px 16px; border: 1px solid var(--border-light); border-radius: var(--radius-md); cursor: pointer; background: #fafafa;">
                  <input type="radio" name="diag_opt" value="${opt}" style="width: 18px; height: 18px;">
                  <span style="font-size: 0.95rem;">${opt}</span>
                </label>
              `).join("")}
            </div>

            <div id="diag-feedback" style="margin-bottom: 16px;"></div>

            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-size: 0.85rem; color: var(--text-muted);">
                Estimated Running Ability: <strong>${st.ability_estimate || 50.0}</strong>
              </span>
              <button id="btn-submit-answer" class="btn btn-primary">Submit Answer</button>
            </div>
          </div>
        `;

        const submitBtn = document.getElementById("btn-submit-answer");
        submitBtn.onclick = async () => {
          const sel = document.querySelector('input[name="diag_opt"]:checked');
          if (!sel) return alert("Please select an answer.");
          
          submitBtn.disabled = true;
          submitBtn.textContent = "Grading...";

          try {
            const ansRes = await fetch(`/api/diagnostic/${studentId}/answer`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                exercise_id: ex.exercise_id,
                skill_id: ex.skill_id,
                student_answer: sel.value
              })
            });
            const ansData = await ansRes.json();
            
            const fbEl = document.getElementById("diag-feedback");
            fbEl.innerHTML = `
              <div class="alert ${ansData.is_correct ? 'alert-info' : 'alert-warning'}">
                <strong>${ansData.is_correct ? '✓ Correct!' : '✗ Incorrect'}</strong> — Score: ${ansData.score}/100. ${ansData.feedback || ''}
              </div>
            `;

            setTimeout(() => {
              loadQuestion();
            }, 1200);
          } catch (err) {
            alert("Error submitting answer: " + err.message);
            submitBtn.disabled = false;
            submitBtn.textContent = "Submit Answer";
          }
        };

      } catch (err) {
        container.innerHTML = `<div class="alert alert-danger">Error loading diagnostic: ${err.message}</div>`;
      }
    };

    loadQuestion();
  },

  // ---------------------------------------------------------------------------
  // Page 5: Tutor Chat
  // ---------------------------------------------------------------------------
  async initChat() {
    const studentId = this.getActiveStudentId();
    const messagesEl = document.getElementById("chat-messages");
    const inputEl = document.getElementById("chat-input");
    const sendBtn = document.getElementById("btn-chat-send");
    if (!messagesEl || !inputEl || !sendBtn) return;

    const appendMessage = (sender, text, meta = null) => {
      const bubble = document.createElement("div");
      bubble.className = `chat-bubble ${sender}`;

      let metaHtml = "";
      if (meta && meta.cited_codes && meta.cited_codes.length > 0) {
        metaHtml = `
          <div style="margin-top: 8px; padding-top: 6px; border-top: 1px dashed rgba(0,0,0,0.15); font-size: 0.8rem;">
            <strong>Cited KB Entities:</strong> ${meta.cited_codes.map(c => `<span class="badge badge-code">${c}</span>`).join(" ")}
          </div>
        `;
      }

      if (meta && meta.intent) {
        metaHtml = `
          <div style="margin-bottom: 4px; font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">
            Intent: <strong>${meta.intent}</strong>
          </div>
        ` + metaHtml;
      }

      bubble.innerHTML = `<div>${text.replace(/\n/g, '<br>')}</div>${metaHtml}`;
      messagesEl.appendChild(bubble);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    };

    // Welcome greeting
    appendMessage("buddy", "Hello! I am your IIT Bhubaneswar academic learning buddy. Ask me questions regarding your course requirements, prerequisites, study schedule adjustments, or workload constraints.");

    const sendMessage = async () => {
      const text = inputEl.value.trim();
      if (!text) return;

      appendMessage("student", text);
      inputEl.value = "";
      sendBtn.disabled = true;

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ student_id: studentId, message: text })
        });
        const data = await res.json();
        appendMessage("buddy", data.response || "No response generated.", {
          intent: data.inferred_intent,
          cited_codes: data.cited_kb_codes
        });
      } catch (err) {
        appendMessage("buddy", "Error connecting to tutor service: " + err.message);
      } finally {
        sendBtn.disabled = false;
      }
    };

    sendBtn.onclick = sendMessage;
    inputEl.onkeydown = (e) => {
      if (e.key === "Enter") sendMessage();
    };

    // Quick prompt buttons
    document.querySelectorAll(".quick-prompt-btn").forEach(b => {
      b.onclick = () => {
        inputEl.value = b.getAttribute("data-prompt");
        sendMessage();
      };
    });
  },

  // ---------------------------------------------------------------------------
  // Page 6: Approvals
  // ---------------------------------------------------------------------------
  async initApprovals() {
    const studentId = this.getActiveStudentId();
    const container = document.getElementById("approvals-container");
    if (!container) return;

    try {
      const res = await fetch(`/api/proposals/${studentId}`);
      const data = await res.json();
      const proposals = data.proposals || [];

      if (proposals.length === 0) {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 40px;">
            <h3>No Pending Change Proposals</h3>
            <p style="color: var(--text-muted); margin-top: 8px;">
              Proposals created by Agent 2 (Learning Resources), Agent 3 (Assessment Remediation), or Agent 4 (Workload/Credit Adjustments) will appear here for your approval.
            </p>
          </div>
        `;
        return;
      }

      container.innerHTML = proposals.map(p => `
        <div class="card" style="margin-bottom: 20px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
            <div>
              <span class="badge badge-code">${p.proposal_id}</span>
              <span class="badge badge-draft">AWAITING APPROVAL</span>
              <span class="badge badge-info">${p.proposer_agent}</span>
            </div>
            <span style="font-size: 0.85rem; font-weight: 700; color: var(--color-primary);">${p.proposal_type}</span>
          </div>

          <h3 style="font-size: 1.1rem; color: var(--color-primary); margin-bottom: 6px;">${p.impact_summary}</h3>
          <p style="color: var(--text-secondary); font-size: 0.95rem; margin-bottom: 12px; line-height: 1.5;">
            <strong>Reasoning:</strong> ${p.reasoning}
          </p>

          <div style="background: var(--bg-subtle); padding: 12px; border-radius: var(--radius-sm); font-size: 0.85rem; margin-bottom: 16px;">
            <strong>Proposed Modifications:</strong>
            <pre style="margin-top: 4px; font-family: var(--font-mono); white-space: pre-wrap;">${JSON.stringify(p.proposed_modifications, null, 2)}</pre>
          </div>

          <div style="display: flex; gap: 12px; justify-content: flex-end;">
            <button class="btn btn-danger btn-sm btn-reject-prop" data-id="${p.proposal_id}">✗ Reject</button>
            <button class="btn btn-success btn-sm btn-approve-prop" data-id="${p.proposal_id}">✓ Approve (Re-plan via Agent 1)</button>
          </div>
        </div>
      `).join("");

      // Action Handlers
      container.querySelectorAll(".btn-approve-prop").forEach(btn => {
        btn.onclick = async () => {
          const propId = btn.getAttribute("data-id");
          btn.disabled = true;
          btn.textContent = "Agent 1 Re-planning...";

          try {
            const decRes = await fetch(`/api/proposals/${studentId}/${propId}/decide`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ approve: true, feedback: "Approved via Web UI" })
            });
            const decData = await decRes.json();
            alert(decData.message || "Proposal approved! New roadmap version committed.");
            window.location.reload();
          } catch (e) {
            alert("Error: " + e.message);
            btn.disabled = false;
          }
        };
      });

      container.querySelectorAll(".btn-reject-prop").forEach(btn => {
        btn.onclick = async () => {
          const propId = btn.getAttribute("data-id");
          btn.disabled = true;

          try {
            await fetch(`/api/proposals/${studentId}/${propId}/decide`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ approve: false, feedback: "Rejected via Web UI" })
            });
            alert("Proposal rejected. Current roadmap remains unchanged.");
            window.location.reload();
          } catch (e) {
            alert("Error: " + e.message);
            btn.disabled = false;
          }
        };
      });

    } catch (err) {
      container.innerHTML = `<div class="alert alert-danger">Error loading proposals: ${err.message}</div>`;
    }
  },

  // ---------------------------------------------------------------------------
  // Page 7: Admin
  // ---------------------------------------------------------------------------
  async initAdmin() {
    const statusEl = document.getElementById("admin-status-panel");
    const tableSelect = document.getElementById("admin-table-select");
    const previewEl = document.getElementById("admin-table-preview");
    const reloadBtn = document.getElementById("btn-reload-seed");
    if (!statusEl) return;

    // Load status
    const loadStatus = async () => {
      try {
        const res = await fetch("/api/admin/status");
        const data = await res.json();
        
        statusEl.innerHTML = `
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
            <div>
              <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">DATABASE HEALTH</div>
              <div><span class="badge badge-${data.db_healthy ? 'verified' : 'draft'}">${data.db_healthy ? 'HEALTHY & CONNECTED' : 'DEGRADED'}</span></div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">LLM CONFIGURATION</div>
              <div><span class="badge badge-${data.llm_configured ? 'verified' : 'draft'}">${data.llm_configured ? 'CONFIGURED' : 'UNCONFIGURED (PLACEHOLDER)'}</span></div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">CONFIGURED MODEL</div>
              <div style="font-family: var(--font-mono); font-size: 0.95rem;">${data.configured_llm_model}</div>
            </div>
            <div>
              <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 700;">ADMINER PORT</div>
              <div style="font-family: var(--font-mono); font-size: 0.95rem;">${data.adminer_port || 8080}</div>
            </div>
          </div>

          <div style="margin-top: 20px; border-top: 1px solid var(--border-light); padding-top: 16px;">
            <div style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary); margin-bottom: 8px;">CORE ROW COUNTS:</div>
            <div style="display: flex; flex-wrap: wrap; gap: 8px;">
              ${Object.entries(data.counts || {}).map(([k, v]) => `
                <span class="badge badge-code">${k}: <strong>${v}</strong></span>
              `).join(" ")}
            </div>
          </div>
        `;
      } catch (err) {
        statusEl.innerHTML = `<div class="alert alert-danger">Error loading status: ${err.message}</div>`;
      }
    };

    loadStatus();

    // Table viewer
    if (tableSelect && previewEl) {
      const loadTableData = async (tbl) => {
        previewEl.innerHTML = `<div style="padding: 20px; color: var(--text-muted);">Loading ${tbl}...</div>`;
        try {
          const res = await fetch(`/api/admin/tables/${tbl}`);
          const data = await res.json();
          
          if (!data.rows || data.rows.length === 0) {
            previewEl.innerHTML = `<div style="padding: 20px; color: var(--text-muted);">Table ${tbl} is empty.</div>`;
            return;
          }

          const cols = data.columns || [];
          previewEl.innerHTML = `
            <div style="padding: 12px; font-size: 0.85rem; color: var(--text-muted); border-bottom: 1px solid var(--border-light);">
              Showing first <strong>${data.count}</strong> rows of <code>${data.table}</code>
            </div>
            <div class="table-responsive">
              <table>
                <thead>
                  <tr>${cols.map(c => `<th>${c}</th>`).join("")}</tr>
                </thead>
                <tbody>
                  ${data.rows.map(row => `
                    <tr>${cols.map(c => `<td>${row[c] !== null ? String(row[c]).slice(0, 80) : '<em style="color:#94a3b8">null</em>'}</td>`).join("")}</tr>
                  `).join("")}
                </tbody>
              </table>
            </div>
          `;
        } catch (err) {
          previewEl.innerHTML = `<div class="alert alert-danger">Error fetching table data: ${err.message}</div>`;
        }
      };

      tableSelect.addEventListener("change", (e) => {
        loadTableData(e.target.value);
      });

      loadTableData(tableSelect.value);
    }

    // Reload seed button
    if (reloadBtn) {
      reloadBtn.onclick = async () => {
        if (!confirm("Are you sure you want to reset and reload all knowledge base seeds?")) return;
        reloadBtn.disabled = true;
        reloadBtn.textContent = "Reloading Seeds...";

        try {
          const res = await fetch("/api/admin/reload-seed", { method: "POST" });
          const data = await res.json();
          alert(data.message || "Seed reset successful.");
          loadStatus();
          if (tableSelect) tableSelect.dispatchEvent(new Event("change"));
        } catch (err) {
          alert("Error reloading seeds: " + err.message);
        } finally {
          reloadBtn.disabled = false;
          reloadBtn.textContent = "Reload Seed Data";
        }
      };
    }
  }
};

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  EBuddy.initNavbar();
});
