// Small shared rendering helpers (no dependencies).
export const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
export const skill = (s) => esc(String(s || '').replace('SKILL_', '').replace(/_/g, ' ').toLowerCase());
export const badge = (text, kind = 'neutral') => `<span class="badge badge-${kind}">${esc(text)}</span>`;
export const TAG_LABELS = {
  ACTIVE_BACKLOG: 'Active backlog', CGPA_ON_MINOR_CUTOFF: 'CGPA on minor cutoff', CGPA_ON_OVERLOAD_CUTOFF: 'CGPA on overload cutoff',
  INTEREST_EVIDENCE_CLASH: 'Interest vs evidence clash', MID_DEGREE_GOAL_SWITCH: 'Mid-degree goal switch',
  TIGHT_WEEKLY_HOURS: 'Tight weekly hours', TIGHT_CREDIT_CAP: 'Tight credit cap'
};
export const tagBadges = (tags) => (tags || []).map((t) => badge(TAG_LABELS[t] || t, 'warning')).join(' ');
export const needStudent = (container) => {
  container.innerHTML = `<div class="screen-card"><p>Choose a student profile first.</p>
    <p style="margin-top:12px;"><a class="btn btn-primary" href="#onboard">Go to Profiles</a></p></div>`;
};
export const link = (url, label) => url ? `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>` : `<span class="text-muted">${esc(label)} (no link in knowledge base)</span>`;
export const errorBox = (err) => `<div class="alert alert-error"><p>${esc(err.message || err)}</p></div>`;
export const md = (text) => esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br/>');
export const tierBadge = (tier) => badge(`${tier} evidence`, tier === 'strong' ? 'success' : (tier === 'weak' ? 'warning' : 'info'));
