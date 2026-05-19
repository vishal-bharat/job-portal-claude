import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar.jsx';
import { api, setSession, getUser } from '../api/client.js';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ name: '', university: '', course: '', year: '' });
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.getProfile().then(p => {
      setProfile(p);
      setForm({
        name: p.name || '',
        university: p.university || '',
        course: p.course || '',
        year: p.year || ''
      });
    }).catch(e => setError(e.message));
  }, []);

  const save = async () => {
    setMsg(''); setError('');
    try {
      const updated = await api.updateProfile({
        ...form,
        year: form.year ? Number(form.year) : null
      });
      setProfile(updated);
      // keep header in sync
      const u = getUser();
      if (u) setSession(localStorage.getItem('cc_token'), { ...u, name: updated.name });
      setMsg('Profile saved.');
    } catch (e) { setError(e.message); }
  };

  const handleRemoveSkill = async (s) => {
    try {
      const updated = await api.removeSkill(s);
      setProfile(updated);
    } catch (e) { setError(e.message); }
  };

  if (!profile) return <div className="app"><Sidebar /><div className="main"><p>Loading…</p></div></div>;

  return (
    <div className="app">
      <Sidebar />
      <div className="main" style={{ gridTemplateColumns: '1fr' }}>
        <div>
          <h1 className="page-title">My Profile</h1>
          {error && <div className="error">{error}</div>}
          {msg && <div style={{ color: '#2a9d8f', fontSize: 13, marginBottom: 10 }}>{msg}</div>}

          <div className="card">
            <h2 className="section-title">Account</h2>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 14 }}>
              <div className="avatar" style={{ width: 56, height: 56, fontSize: 20 }}>
                {profile.name.split(' ').map(p => p[0]).join('').slice(0,2)}
              </div>
              <div>
                <div style={{ fontWeight: 700 }}>{profile.name}</div>
                <div style={{ color: '#6b7494', fontSize: 13 }}>{profile.email}</div>
              </div>
            </div>

            <div className="profile-grid">
              <div className="profile-field">
                <label>Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="profile-field">
                <label>University</label>
                <input value={form.university} onChange={(e) => setForm({ ...form, university: e.target.value })} />
              </div>
              <div className="profile-field">
                <label>Course</label>
                <input value={form.course} onChange={(e) => setForm({ ...form, course: e.target.value })} />
              </div>
              <div className="profile-field">
                <label>Year</label>
                <input type="number" min="1" max="6" value={form.year} onChange={(e) => setForm({ ...form, year: e.target.value })} />
              </div>
            </div>
            <button className="btn-primary" style={{ marginTop: 16 }} onClick={save}>Save changes</button>
          </div>

          <div className="card">
            <h2 className="section-title">Skills</h2>
            <div style={{ fontSize: 13, color: '#6b7494', marginBottom: 10 }}>
              Manage skills here or on the Opportunities page. Removing a skill instantly updates recommendations.
            </div>
            <div className="chips">
              {profile.skills.map((s) => (
                <span key={s} className="chip">
                  {s} <span className="x" onClick={() => handleRemoveSkill(s)} title="Remove">×</span>
                </span>
              ))}
              {profile.skills.length === 0 && <div style={{ fontSize: 13, color: '#6b7494' }}>No skills added yet.</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
