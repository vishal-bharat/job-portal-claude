import { useEffect, useRef, useState } from 'react';
import Sidebar from '../components/Sidebar.jsx';
import { api, setSession, getUser } from '../api/client.js';

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({ name: '', university: '', course: '', year: '' });
  const [msg, setMsg] = useState('');
  const [error, setError] = useState('');

  // CV upload state
  const [cvUploading, setCvUploading]   = useState(false);
  const [cvResult, setCvResult]         = useState(null);   // CVExtractResponse
  const [cvError, setCvError]           = useState('');
  const [dragOver, setDragOver]         = useState(false);
  const fileInputRef = useRef(null);

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

  const handleCVUpload = async (file) => {
    if (!file) return;
    if (file.type !== 'application/pdf') {
      setCvError('Please upload a PDF file.');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setCvError('File too large — maximum 10 MB.');
      return;
    }
    setCvUploading(true);
    setCvError('');
    setCvResult(null);
    try {
      const result = await api.extractCV(file);
      setCvResult(result);
      // refresh profile so the Skills card shows newly added skills
      const updated = await api.getProfile();
      setProfile(updated);
    } catch (e) {
      setCvError(e.message);
    } finally {
      setCvUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
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

          {/* ── CV Upload card ─────────────────────────────────────────── */}
          <div className="card">
            <h2 className="section-title">📄 Upload Your CV</h2>
            <p style={{ fontSize: 13, color: '#6b7494', marginTop: 0 }}>
              Upload a PDF and we'll automatically extract your skills using our three-stage
              pipeline: text extraction → taxonomy matching → GISMABERT semantic expansion.
              Extracted skills are added to your profile instantly.
            </p>

            {/* Drop zone */}
            <div
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const f = e.dataTransfer.files[0];
                if (f) handleCVUpload(f);
              }}
              style={{
                border: `2px dashed ${dragOver ? '#0369a1' : '#c7d0e0'}`,
                borderRadius: 12,
                padding: '28px 20px',
                textAlign: 'center',
                cursor: 'pointer',
                background: dragOver ? '#f0f7ff' : '#f8faff',
                transition: 'all 0.2s',
                marginBottom: 12,
              }}
            >
              <div style={{ fontSize: 32, marginBottom: 8 }}>📂</div>
              <div style={{ fontWeight: 600, fontSize: 14, color: '#1e2a4a' }}>
                {cvUploading ? 'Extracting skills…' : 'Drop your CV here or click to browse'}
              </div>
              <div style={{ fontSize: 12, color: '#6b7494', marginTop: 4 }}>PDF only · max 10 MB</div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              style={{ display: 'none' }}
              onChange={(e) => handleCVUpload(e.target.files[0])}
            />

            {cvUploading && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: 10,
                fontSize: 13, color: '#0369a1', padding: '10px 0',
              }}>
                <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⚙️</span>
                Running 3-stage extraction pipeline…
              </div>
            )}

            {cvError && (
              <div className="error" style={{ marginTop: 8 }}>{cvError}</div>
            )}

            {cvResult && (
              <div style={{
                background: '#f0fdf4', border: '1px solid #86efac',
                borderRadius: 10, padding: '14px 16px', marginTop: 8,
              }}>
                <div style={{ fontWeight: 700, fontSize: 14, color: '#15803d', marginBottom: 8 }}>
                  ✅ Extraction complete — {cvResult.auto_added.length} new skill{cvResult.auto_added.length !== 1 ? 's' : ''} added
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 12, color: '#6b7494', marginBottom: 10 }}>
                  <span>📋 Regex matched: <strong>{cvResult.regex_skills?.length ?? 0}</strong></span>
                  <span>🧠 Semantic expanded: <strong>{cvResult.semantic_skills?.length ?? 0}</strong></span>
                  <span>🔢 Total found: <strong>{cvResult.total_found}</strong></span>
                </div>
                {cvResult.all_skills?.length > 0 && (
                  <div className="chips" style={{ marginTop: 4 }}>
                    {cvResult.all_skills.map(s => (
                      <span key={s} className="chip" style={{ background: '#dcfce7', color: '#15803d' }}>
                        ✓ {s}
                      </span>
                    ))}
                  </div>
                )}
                {cvResult.cv_preview && (
                  <details style={{ marginTop: 10 }}>
                    <summary style={{ fontSize: 12, color: '#6b7494', cursor: 'pointer' }}>
                      View CV text preview
                    </summary>
                    <pre style={{
                      fontSize: 11, color: '#374151', background: '#fff',
                      border: '1px solid #e1e5ee', borderRadius: 6,
                      padding: 10, marginTop: 6, whiteSpace: 'pre-wrap',
                      maxHeight: 160, overflow: 'auto',
                    }}>{cvResult.cv_preview}</pre>
                  </details>
                )}
              </div>
            )}
          </div>

          {/* ── Skills card ────────────────────────────────────────────── */}
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
