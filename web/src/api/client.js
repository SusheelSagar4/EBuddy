/**
 * API Client for Personalised Learning Buddy (IIT Bhubaneswar)
 * Zero external CDN dependencies - standard browser Fetch API.
 */
class ApiClient {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  async _request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };
    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorBody.detail || `HTTP Error ${response.status}`);
      }
      return await response.json();
    } catch (err) {
      console.error(`API Request failed: ${endpoint}`, err);
      throw err;
    }
  }

  // Student Endpoints
  async onboard(studentData) {
    return this._request('/api/student/onboard', {
      method: 'POST',
      body: JSON.stringify(studentData)
    });
  }

  async getDiagnostic(studentId) {
    return this._request(`/api/student/${studentId}/diagnostic`);
  }

  async submitDiagnostic(studentId, submission) {
    return this._request(`/api/student/${studentId}/diagnostic`, {
      method: 'POST',
      body: JSON.stringify(submission)
    });
  }

  async getPlan(studentId) {
    return this._request(`/api/student/${studentId}/plan`);
  }

  async getWeeklyRoadmap(studentId, week = 1) {
    return this._request(`/api/student/${studentId}/roadmap/weekly?week=${encodeURIComponent(week)}`);
  }

  async getRoadmapVersions(studentId) {
    return this._request(`/api/student/${studentId}/roadmap/versions`);
  }

  async getLearnToday(studentId) {
    return this._request(`/api/student/${studentId}/learn/today`);
  }

  async getProposals(studentId) {
    return this._request(`/api/student/${studentId}/proposals`);
  }

  async decideProposal(studentId, proposalId, approve, feedback = null) {
    return this._request(`/api/student/${studentId}/proposals/${proposalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ approve, feedback })
    });
  }

  async validatePlan(studentId, plan) {
    return this._request(`/api/student/${studentId}/plan/validate`, {
      method: 'POST',
      body: JSON.stringify(plan)
    });
  }

  async getLearn(studentId, skillId = null) {
    const q = skillId ? `?skill_id=${encodeURIComponent(skillId)}` : '';
    return this._request(`/api/student/${studentId}/learn${q}`);
  }

  async submitExercise(studentId, submission) {
    return this._request(`/api/student/${studentId}/learn/submit`, {
      method: 'POST',
      body: JSON.stringify(submission)
    });
  }

  async getProgress(studentId) {
    return this._request(`/api/student/${studentId}/progress`);
  }

  async chat(studentId, message) {
    return this._request(`/api/student/${studentId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  }

  // Simulation Endpoints
  async simulateQuiz(studentId, quizData) {
    return this._request(`/api/sim/${studentId}/quiz`, {
      method: 'POST',
      body: JSON.stringify(quizData)
    });
  }

  // Admin Endpoints
  async getPersonas() {
    return this._request('/api/admin/personas');
  }

  async getKbStats() {
    return this._request('/api/admin/kb-stats');
  }

  async getHealth() {
    return this._request('/health');
  }
}

export const api = new ApiClient();

