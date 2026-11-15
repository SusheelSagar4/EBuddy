/* ==============================================================================
   EBuddy Web UI Shell — Frontend Vanilla JS
   Zero Outbound / Relative Paths Only / Traceable KB Codes
   ============================================================================== */

const EBuddy = {
  // Active student management
  getActiveStudentId() {
    return localStorage.getItem("ebuddy_active_student_id") || "CONF_STU_EE_POWER_01";
  },

  setActiveStudentId(studentId) {
    localStorage.setItem("ebuddy_active_student_id", studentId);
    window.location.reload();
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

    try {
      const sRes = await fetch(`/api/students/${studentId}`);
      const student = await sRes.json();
      const prog = student.programme_id || "BTECH_EE";

      const gRes = await fetch(`/api/goals?programme_id=${prog}`);
      const gData = await gRes.json();

      container.innerHTML = (gData.goals || []).map((g, idx) => `
        <div class="card" style="margin-bottom: 16px; border: 2px solid ${idx === 0 ? 'var(--color-accent)' : 'var(--border-light)'};">
          <label style="display: flex; gap: 16px; cursor: pointer; align-items: flex-start;">
            <input type="radio" name="selected_goal" value="${g.goal_id}" ${idx === 0 ? 'checked' : ''} style="margin-top: 6px; width: 18px; height: 18px;">
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
      `).join("");

      const btn = document.getElementById("btn-build-roadmap");
      if (btn) {
        btn.onclick = async () => {
          const checked = document.querySelector('input[name="selected_goal"]:checked');
          if (!checked) return alert("Please select a target goal.");
          const goalId = checked.value;

          btn.disabled = true;
          btn.textContent = "Building Roadmap with Agent 1...";

          try {
            const buildRes = await fetch("/api/roadmap/generate", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ student_id: studentId, goal_id: goalId })
            });
            if (!buildRes.ok) throw new Error("Failed to generate plan");
            window.location.href = "/roadmap";
          } catch (e) {
            alert("Error building roadmap: " + e.message);
            btn.disabled = false;
            btn.textContent = "Build my roadmap";
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
    const container = document.getElementById("roadmap-container");
    const warningsEl = document.getElementById("roadmap-warnings");
    const proposalsEl = document.getElementById("roadmap-proposals");
    if (!container) return;

    try {
      const res = await fetch(`/api/roadmap/${studentId}`);
      if (!res.ok) {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 40px;">
            <h3>No Roadmap Generated Yet</h3>
            <p style="color: var(--text-muted); margin: 12px 0;">Build your personalized curriculum roadmap by selecting your target goal.</p>
            <a href="/goals" class="btn btn-primary">Select Goal & Build Roadmap</a>
          </div>
        `;
        return;
      }
      const data = await res.json();

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

      // Semesters
      container.innerHTML = (data.semesters || []).map(sem => `
        <div class="card" style="margin-bottom: 24px;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 12px; margin-bottom: 16px;">
            <h3 style="font-size: 1.2rem; color: var(--color-primary);">Semester ${sem.semester_number}</h3>
            <span class="badge badge-info" style="font-size: 0.85rem;">
              Credits: ${sem.semester_credits}
            </span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 12px;">
            ${sem.items.map(it => `
              <div style="border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 14px; background: #fafafa;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                  <div>
                    <span class="badge badge-code" style="font-size: 0.85rem;">${it.kb_code}</span>
                    <span class="badge badge-${it.status === 'verified' ? 'verified' : 'draft'}">${it.status}</span>
                    <strong style="font-size: 1.05rem; margin-left: 8px; color: var(--text-primary);">${it.title}</strong>
                  </div>
                  <span style="font-size: 0.85rem; font-weight: 700; color: var(--text-secondary);">${it.credits} Credits</span>
                </div>

                <div style="margin-top: 8px; font-size: 0.875rem; color: var(--text-secondary); line-height: 1.5;">
                  <strong>Why this course:</strong> ${it.reason?.why_this || it.reason?.intent || 'Curriculum Requirement'}
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

    } catch (err) {
      container.innerHTML = `<div class="alert alert-danger">Error loading roadmap: ${err.message}</div>`;
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
