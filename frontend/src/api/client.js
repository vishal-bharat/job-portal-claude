// In Docker / production the nginx container proxies /api/* to the backend,
// so we use a relative URL ("" + "/api/..."). For `npm run dev` (no proxy)
// override by setting VITE_API_URL=http://localhost:8080 in a .env.local file.
const BASE_URL = import.meta.env.VITE_API_URL || '';

function getToken() {
  return localStorage.getItem('cc_token');
}

export function setSession(token, user) {
  localStorage.setItem('cc_token', token);
  localStorage.setItem('cc_user', JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem('cc_token');
  localStorage.removeItem('cc_user');
}

export function getUser() {
  const u = localStorage.getItem('cc_user');
  return u ? JSON.parse(u) : null;
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  };
  const res = await fetch(BASE_URL + path, { ...options, headers });
  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg = body?.detail || body?.error || `Request failed (${res.status})`;
    throw new Error(msg);
  }
  return body;
}

// Login fetches profile after auth so we can store course in session
async function loginAndStore(email, password) {
  const res = await request('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
  setSession(res.token, { email: res.email, name: res.name });
  // Fetch profile to get course for sidebar
  try {
    const profile = await request('/api/profile');
    setSession(res.token, { email: res.email, name: res.name, course: profile.course });
  } catch (_) {}
  return res;
}

export const api = {
  login: loginAndStore,
  signup: (data) =>
    request('/api/auth/signup', { method: 'POST', body: JSON.stringify(data) }),
  getProfile: () => request('/api/profile'),
  updateProfile: (data) =>
    request('/api/profile', { method: 'PUT', body: JSON.stringify(data) }),
  allSkills: () => request('/api/skills'),
  addSkill: (name) =>
    request('/api/skills', { method: 'POST', body: JSON.stringify({ name }) }),
  removeSkill: (name) =>
    request(`/api/skills/${encodeURIComponent(name)}`, { method: 'DELETE' }),
  recommendedJobs: (filter = 'all') =>
    request(`/api/jobs/recommended?filter=${encodeURIComponent(filter)}`),
  searchJobs: (q) =>
    request(`/api/jobs/search?q=${encodeURIComponent(q)}`),
  skillGap: () => request('/api/jobs/skill-gap'),
  trends: () => request('/api/jobs/trends'),

  // CV skill extraction (multipart upload — no JSON Content-Type)
  extractCV: (file) => {
    const token = getToken();
    const formData = new FormData();
    formData.append('file', file);
    return fetch(BASE_URL + '/api/skills/extract-cv', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: formData,
    }).then(async res => {
      const text = await res.text();
      const body = text ? JSON.parse(text) : null;
      if (!res.ok) {
        const msg = body?.detail || body?.error || `Upload failed (${res.status})`;
        throw new Error(msg);
      }
      return body;
    });
  },

  // Applications tracker
  listApplications: () => request('/api/applications'),
  saveApplication: (job) =>
    request('/api/applications', { method: 'POST', body: JSON.stringify(job) }),
  updateApplicationStatus: (id, status, notes) =>
    request(`/api/applications/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, notes }),
    }),
  deleteApplication: (id) =>
    request(`/api/applications/${id}`, { method: 'DELETE' }),
};
