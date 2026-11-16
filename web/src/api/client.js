/**
 * API client for the Personalised Learning Buddy (IIT Bhubaneswar).
 * Zero external dependencies - browser Fetch API only, same-origin requests.
 */
class ApiClient {
  constructor(baseUrl = '') { this.baseUrl = baseUrl; }

  async _request(endpoint, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
    const response = await fetch(`${this.baseUrl}${endpoint}`, { ...options, headers });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: response.statusText }));
      const detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
      throw new Error(detail || `HTTP ${response.status}`);
    }
    return response.json();
  }
  _get(p) { return this._request(p); }
  _send(method, p, body) { return this._request(p, { method, body: JSON.stringify(body || {}) }); }

  // Profiles, goals, tracks
  listStudents() { return this._get('/api/v2/students'); }
  listGoals(programmeId) { return this._get(`/api/v2/goals${programmeId ? `?programme_id=${encodeURIComponent(programmeId)}` : ''}`); }
  listTracks() { return this._get('/api/v2/tracks'); }
  selectStudent(id, goalId = null) { return this._send('POST', `/api/v2/students/${encodeURIComponent(id)}/select`, { goal_id: goalId }); }
  createStudent(data) { return this._send('POST', '/api/v2/students', data); }
  getOverview(id) { return this._get(`/api/v2/students/${encodeURIComponent(id)}/overview`); }

  // Plan, learn, progress
  getPlanV2(id) { return this._get(`/api/v2/students/${encodeURIComponent(id)}/plan`); }
  getLearnV2(id) { return this._get(`/api/v2/students/${encodeURIComponent(id)}/learn`); }
  getProgress(id) { return this._get(`/api/v2/students/${encodeURIComponent(id)}/progress`); }
  submitPractice(id, questionId, answer) { return this._send('POST', `/api/v2/students/${encodeURIComponent(id)}/practice`, { question_id: questionId, answer }); }
  addEvidence(id, data) { return this._send('POST', `/api/v2/students/${encodeURIComponent(id)}/evidence`, data); }
  getWeeklyRoadmap(id, week = 1) { return this._get(`/api/student/${encodeURIComponent(id)}/roadmap/weekly?week=${week}`); }
  getProposals(id) { return this._get(`/api/student/${encodeURIComponent(id)}/proposals`); }
  decideProposal(id, proposalId, approve, feedback = null) {
    return this._send('POST', `/api/student/${encodeURIComponent(id)}/proposals/${encodeURIComponent(proposalId)}/decide`, { approve, feedback });
  }

  // Adaptive diagnostic
  startDiagnostic(id) { return this._send('POST', '/api/diagnostic/start', { student_id: id }); }
  nextDiagnostic(id) { return this._get(`/api/diagnostic/${encodeURIComponent(id)}/next`); }
  answerDiagnostic(id, exerciseId, skillId, answer) {
    return this._send('POST', `/api/diagnostic/${encodeURIComponent(id)}/answer`, { exercise_id: exerciseId, skill_id: skillId, student_answer: answer });
  }

  // Chat
  chat(id, message) { return this._send('POST', '/api/chat', { student_id: id, message }); }

  // Adaptation simulator
  runPreset(id, preset, body = {}) { return this._send('POST', `/api/sim/${encodeURIComponent(id)}/preset/${preset}`, body); }

  // Admin
  adminOverview() { return this._get('/api/admin/overview'); }
  adminStudent(id) { return this._get(`/api/admin/students/${encodeURIComponent(id)}`); }
  adminEditStudent(id, data) { return this._send('PATCH', `/api/admin/students/${encodeURIComponent(id)}`, data); }
  adminEditEvidence(id, data) { return this._send('PATCH', `/api/admin/students/${encodeURIComponent(id)}/evidence`, data); }
  adminCourses(q) { return this._get(`/api/admin/courses?q=${encodeURIComponent(q || '')}`); }
  adminEditCourse(courseId, data) { return this._send('PATCH', `/api/admin/courses/${encodeURIComponent(courseId)}`, data); }
  adminRules() { return this._get('/api/admin/rules'); }
  adminEditRule(ruleId, parameters) { return this._send('PATCH', `/api/admin/rules/${encodeURIComponent(ruleId)}`, { parameters }); }
  adminReset() { return this._send('POST', '/api/admin/reset', {}); }
  adminReprocessLog() { return this._get('/api/admin/reprocess-log'); }
  getPersonas() { return this._get('/api/admin/personas'); }
  getHealth() { return this._get('/health'); }
}

export const api = new ApiClient();
