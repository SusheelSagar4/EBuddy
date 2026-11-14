import { api } from '../api/client.js';

export function renderChat(container, state, navigate) {
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
    <div class="screen-card chat-wrapper">
      <div class="screen-header flex-between">
        <div>
          <h2>Academic & Personal Buddy Chat (Agent 4)</h2>
          <p class="subtitle">Air-gapped conversation grounded in IIT BBS curriculum regulations. Agent 4 proposes adaptations for your approval.</p>
        </div>
        <div>
          <button class="btn btn-outline btn-sm" id="btn-toggle-context">Toggle Context Card</button>
        </div>
      </div>

      <div id="context-card-drawer" class="context-drawer" style="display:none; background:#f9f9f9; padding:12px; border-radius:6px; margin-bottom:12px;">
        <h4>Active LLM Context Card (Zero Fabrication Boundary)</h4>
        <div class="context-body" style="font-size:0.9em; color:#444;">
          <p><strong>Student ID:</strong> ${state.studentId}</p>
          <p><strong>Programme:</strong> ${state.profile?.programme_id || 'BTECH_EE'}</p>
          <p><strong>Rules Enforced:</strong> Prerequisite chain compliance, 16–26 credit cap, Semester parity</p>
          <p class="text-muted"><small>Dates, cut-offs, or fees are never stated unless verified in official statutes.</small></p>
        </div>
      </div>

      <div class="chat-feed" id="chat-feed" style="min-height:300px; max-height:450px; overflow-y:auto; padding:10px; border:1px solid #eee; border-radius:6px; background:#fafafa;">
        <div class="chat-msg msg-assistant">
          <div class="msg-bubble" style="background:white; border:1px solid #e0e0e0; padding:10px 14px; border-radius:8px; margin-bottom:8px;">
            <span class="sender-name" style="font-weight:bold; color:#0052cc;">Agent 4 (Query Assistant)</span>
            <p>Hello! I am your IIT Bhubaneswar academic buddy. I can explain your course schedule, clarify syllabus questions, or adjust your study workload if you have busy exam weeks. What would you like to explore?</p>
            <div class="msg-meta">
              <span class="badge badge-info">Intent: GREETING</span>
            </div>
          </div>
        </div>
      </div>

      <form id="chat-form" class="chat-input-bar" style="display:flex; gap:8px; margin-top:12px;">
        <input type="text" id="chat-input" placeholder="Ask a doubt or say 'I have exams this week, reduce my workload'..." required autocomplete="off" style="flex:1; padding:10px; border-radius:4px; border:1px solid #ccc;" />
        <button type="submit" class="btn btn-primary" id="btn-send">Send</button>
      </form>
    </div>
  `;

  document.getElementById('btn-toggle-context').addEventListener('click', () => {
    const drawer = document.getElementById('context-card-drawer');
    drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
  });

  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatFeed = document.getElementById('chat-feed');

  chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const query = chatInput.value.trim();
    if (!query) return;

    appendMessage('You', query, 'msg-user');
    chatInput.value = '';
    chatInput.disabled = true;

    try {
      const res = await api.chat(state.studentId, query);
      appendMessage('Agent 4', res.response, 'msg-assistant', res.inferred_intent, res.disclaimer, res.proposal);
    } catch (err) {
      appendMessage('System', `Error communicating with buddy service: ${err.message}`, 'msg-assistant');
    } finally {
      chatInput.disabled = false;
      chatInput.focus();
    }
  });

  function appendMessage(sender, text, cssClass, intent = null, disclaimer = null, proposal = null) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${cssClass}`;

    let proposalHtml = '';
    if (proposal) {
      proposalHtml = `
        <div style="margin-top: 10px; background: #fffde7; border: 1px solid #fff59d; border-radius: 6px; padding: 12px;">
          <strong style="color: #f57f17;">📋 Generated Change Proposal (${proposal.proposal_type})</strong>
          <p style="margin: 4px 0; font-size: 0.9em;"><strong>Reasoning:</strong> ${proposal.reasoning}</p>
          <p style="margin: 4px 0; font-size: 0.9em; color: #2e7d32;"><strong>Effect:</strong> ${proposal.impact_summary}</p>
          <div style="margin-top: 8px; display:flex; gap:8px;" id="prop-actions-${proposal.proposal_id}">
            <button class="btn btn-primary btn-sm btn-appr" data-id="${proposal.proposal_id}">Approve Proposal</button>
            <button class="btn btn-outline btn-sm btn-rej" data-id="${proposal.proposal_id}">Reject Proposal</button>
          </div>
          <div id="prop-status-${proposal.proposal_id}" style="display:none; margin-top:6px; font-weight:bold;"></div>
        </div>
      `;
    }

    let intentHtml = intent ? `<span class="badge badge-info">Intent: ${intent}</span>` : '';
    let disclaimerHtml = disclaimer ? `<p style="font-size:0.8em; color:#777; margin-top:8px;"><em>${disclaimer}</em></p>` : '';

    msgDiv.innerHTML = `
      <div class="msg-bubble" style="background:white; border:1px solid #e0e0e0; padding:10px 14px; border-radius:8px; margin-bottom:8px;">
        <span class="sender-name" style="font-weight:bold; color:${sender === 'You' ? '#333' : '#0052cc'};">${sender}</span>
        <p style="white-space: pre-wrap; margin:6px 0;">${text}</p>
        ${proposalHtml}
        ${disclaimerHtml}
        ${intentHtml ? `<div class="msg-meta" style="margin-top:4px;">${intentHtml}</div>` : ''}
      </div>
    `;

    chatFeed.appendChild(msgDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;

    if (proposal) {
      const actionsDiv = msgDiv.querySelector(`#prop-actions-${proposal.proposal_id}`);
      const statusDiv = msgDiv.querySelector(`#prop-status-${proposal.proposal_id}`);

      msgDiv.querySelector('.btn-appr')?.addEventListener('click', async () => {
        actionsDiv.style.display = 'none';
        statusDiv.style.display = 'block';
        statusDiv.style.color = '#2e7d32';
        statusDiv.textContent = 'Submitting approval to Agent 1...';
        try {
          const res = await api.decideProposal(state.studentId, proposal.proposal_id, true, "Approved via chat.");
          statusDiv.textContent = `✓ Committed! Agent 1 created Roadmap Version ${res.new_version}.`;
        } catch (err) {
          statusDiv.style.color = '#c62828';
          statusDiv.textContent = `Error: ${err.message}`;
        }
      });

      msgDiv.querySelector('.btn-rej')?.addEventListener('click', async () => {
        actionsDiv.style.display = 'none';
        statusDiv.style.display = 'block';
        statusDiv.style.color = '#555';
        try {
          await api.decideProposal(state.studentId, proposal.proposal_id, false, "Rejected via chat.");
          statusDiv.textContent = `✕ Rejected. Current roadmap remains unchanged.`;
        } catch (err) {
          statusDiv.style.color = '#c62828';
          statusDiv.textContent = `Error: ${err.message}`;
        }
      });
    }
  }
}
