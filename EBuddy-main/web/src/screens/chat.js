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
          <h2>Academic & Career Buddy Chat</h2>
          <p class="subtitle">Air-gapped conversation grounded strictly in IIT BBS curriculum regulations.</p>
        </div>
        <div>
          <button class="btn btn-outline btn-sm" id="btn-toggle-context">Toggle LLM Context Card</button>
        </div>
      </div>

      <div id="context-card-drawer" class="context-drawer" style="display:none;">
        <h4>Active LLM Context Card (Zero Fabrication Boundary)</h4>
        <div class="context-body">
          <p><strong>Student ID:</strong> ${state.studentId}</p>
          <p><strong>Programme:</strong> ${state.profile?.programme_id || 'BTECH_EE'}</p>
          <p><strong>Goal:</strong> ${state.profile?.target_goal_id || 'GOAL_CORE_EE'}</p>
          <p><strong>Rules Enforced:</strong> Prerequisite compliance, 25 cr cap, Semester offering match</p>
          <p class="text-muted"><small>No fees, cut-offs, or unverified regulatory dates are asserted unless sourced from official institute statutes.</small></p>
        </div>
      </div>

      <div class="chat-feed" id="chat-feed">
        <div class="chat-msg msg-assistant">
          <div class="msg-bubble">
            <span class="sender-name">Antigravity Buddy</span>
            <p>Hello! I am your IIT Bhubaneswar academic buddy. I can answer questions about your course schedule, explain why specific courses were planned, or guide your preparation for core power engineering and GATE. What would you like to explore?</p>
            <div class="msg-meta">
              <span class="badge badge-info">Intent: GREETING</span>
            </div>
          </div>
        </div>
      </div>

      <form id="chat-form" class="chat-input-bar">
        <input type="text" id="chat-input" placeholder="Ask about prerequisites, why a course was planned, or GATE alignment..." required autocomplete="off" />
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

    // Append user message
    appendMessage('You', query, 'msg-user');
    chatInput.value = '';
    chatInput.disabled = true;

    try {
      const res = await api.chat(state.studentId, query);
      appendMessage('Antigravity Buddy', res.reply, 'msg-assistant', res.intent, res.citations);
    } catch (err) {
      appendMessage('System', `Error communicating with buddy service: ${err.message}`, 'msg-assistant');
    } finally {
      chatInput.disabled = false;
      chatInput.focus();
    }
  });

  function appendMessage(sender, text, cssClass, intent = null, citations = []) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `chat-msg ${cssClass}`;
    
    let citationsHtml = '';
    if (citations && citations.length > 0) {
      citationsHtml = `
        <div class="msg-citations">
          <strong>Citations:</strong>
          ${citations.map(c => `<span class="tag-citation">${c}</span>`).join(' ')}
        </div>
      `;
    }

    let intentHtml = '';
    if (intent) {
      intentHtml = `<span class="badge badge-info">Intent: ${intent}</span>`;
    }

    msgDiv.innerHTML = `
      <div class="msg-bubble">
        <span class="sender-name">${sender}</span>
        <p>${text}</p>
        ${citationsHtml}
        ${intentHtml ? `<div class="msg-meta">${intentHtml}</div>` : ''}
      </div>
    `;

    chatFeed.appendChild(msgDiv);
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }
}

