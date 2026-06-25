import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { api, getUser, setSession } from '../api/client.js';

// Skill suggestions per course
const COURSE_SKILLS = {
  'Computer Science':          ['Python', 'JavaScript', 'React', 'Node.js', 'SQL', 'Git', 'Java', 'Docker', 'Machine Learning', 'TypeScript', 'Linux', 'REST APIs'],
  'Data Science & Analytics':  ['Python', 'R', 'SQL', 'Machine Learning', 'TensorFlow', 'Tableau', 'Power BI', 'Pandas', 'Statistics', 'Excel', 'Data Visualisation', 'Scikit-learn'],
  'Business Administration':   ['Excel', 'Project Management', 'Financial Analysis', 'SAP', 'CRM', 'PowerPoint', 'Business Strategy', 'Leadership', 'Market Research'],
  'International Management':  ['Project Management', 'Leadership', 'CRM', 'Excel', 'Cross-cultural Communication', 'Business Strategy', 'Negotiation', 'Supply Chain'],
  'Marketing Management':      ['Google Analytics', 'SEO', 'Social Media Marketing', 'Content Marketing', 'Adobe Creative Suite', 'CRM', 'Email Marketing', 'Copywriting'],
  'Finance & Accounting':      ['Excel', 'SAP', 'Financial Modeling', 'Bloomberg Terminal', 'SQL', 'Power BI', 'Accounting', 'Tax Planning', 'Risk Analysis'],
  'Digital Business':          ['Python', 'SQL', 'Digital Marketing', 'UX Design', 'Agile', 'E-commerce', 'Analytics', 'Product Management', 'Figma'],
  'Project Management':        ['Agile', 'Scrum', 'Jira', 'MS Project', 'Risk Management', 'Excel', 'Leadership', 'Stakeholder Management', 'PMP'],
  'Human Resource Management': ['HRIS', 'Excel', 'Recruitment', 'Labour Law', 'Performance Management', 'Payroll', 'Training & Development', 'Talent Acquisition'],
};
const DEFAULT_SKILLS = ['Python', 'Excel', 'SQL', 'Project Management', 'Communication', 'Leadership', 'Data Analysis', 'Microsoft Office', 'Git', 'Agile'];

const JOB_TYPES = [
  { key: 'all',        label: 'All jobs',    icon: '🌐', desc: 'Show everything' },
  { key: 'fulltime',   label: 'Full-time',   icon: '💼', desc: 'Permanent roles' },
  { key: 'internship', label: 'Internship',  icon: '🎓', desc: 'Student placements' },
  { key: 'remote',     label: 'Remote',      icon: '🏠', desc: 'Work from anywhere' },
  { key: 'parttime',   label: 'Part-time',   icon: '⏰', desc: 'Flexible hours' },
];

const COURSES = [
  'Computer Science', 'Data Science & Analytics', 'Business Administration',
  'International Management', 'Marketing Management', 'Finance & Accounting',
  'Digital Business', 'Project Management', 'Human Resource Management',
];

// Styles
const S = {
  wrap: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #1a2238 0%, #2a3454 100%)',
    padding: '24px 16px',
  },
  card: {
    width: '100%',
    maxWidth: 560,
    background: '#fff',
    borderRadius: 20,
    padding: '36px 40px',
    boxShadow: '0 16px 48px rgba(0,0,0,0.18)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 28,
  },
  logo: {
    display: 'flex', alignItems: 'center', gap: 10,
  },
  logoMark: {
    width: 36, height: 36, borderRadius: 8,
    background: '#c9f04d', color: '#1a2238',
    fontWeight: 800, fontSize: 18,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  logoName: { fontWeight: 700, fontSize: 15, color: '#1a2238' },
  skip: {
    background: 'none', border: 'none', color: '#9ca3af',
    fontSize: 13, cursor: 'pointer', padding: '4px 8px',
  },
  progress: {
    display: 'flex', gap: 6, marginBottom: 32,
  },
  progressBar: (active, done) => ({
    height: 4, flex: 1, borderRadius: 2,
    background: done ? '#1a2238' : active ? '#c9f04d' : '#e1e5ee',
    transition: 'background 0.3s',
  }),
  stepLabel: {
    fontSize: 12, color: '#9ca3af', marginBottom: 8, fontWeight: 500,
  },
  title: { fontSize: 22, fontWeight: 700, color: '#1a2238', margin: '0 0 6px' },
  subtitle: { fontSize: 14, color: '#6b7494', margin: '0 0 28px', lineHeight: 1.5 },
  label: { fontSize: 12, color: '#6b7494', display: 'block', marginBottom: 6, fontWeight: 500 },
  input: {
    width: '100%', padding: '12px 14px',
    borderRadius: 10, border: '1px solid #e1e5ee',
    fontSize: 14, outline: 'none', marginBottom: 16,
    boxSizing: 'border-box',
  },
  select: {
    width: '100%', padding: '12px 14px',
    borderRadius: 10, border: '1px solid #e1e5ee',
    fontSize: 14, outline: 'none', marginBottom: 16,
    background: '#fff', boxSizing: 'border-box', cursor: 'pointer',
  },
  row: { display: 'flex', gap: 14 },
  chips: { display: 'flex', flexWrap: 'wrap', gap: 8, margin: '0 0 20px' },
  chip: (selected) => ({
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '7px 14px', borderRadius: 999,
    fontSize: 13, cursor: 'pointer', transition: 'all 0.15s',
    background: selected ? '#1a2238' : '#f0f2f8',
    color: selected ? '#fff' : '#1a2238',
    border: selected ? '1px solid #1a2238' : '1px solid transparent',
    fontWeight: selected ? 600 : 400,
  }),
  addedChip: {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '6px 12px', borderRadius: 999, fontSize: 13,
    background: '#c9f04d', color: '#1a2238', fontWeight: 600,
  },
  skillInput: { display: 'flex', gap: 8, marginBottom: 20 },
  skillInputField: {
    flex: 1, padding: '11px 14px',
    borderRadius: 10, border: '1px solid #e1e5ee',
    fontSize: 14, outline: 'none',
  },
  addBtn: {
    background: '#1a2238', color: '#fff', border: 'none',
    padding: '11px 18px', borderRadius: 10,
    fontWeight: 600, fontSize: 14, cursor: 'pointer', whiteSpace: 'nowrap',
  },
  jobTypeGrid: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 28,
  },
  jobTypeCard: (selected) => ({
    border: selected ? '2px solid #1a2238' : '2px solid #e1e5ee',
    borderRadius: 12, padding: '14px 16px', cursor: 'pointer',
    background: selected ? '#f5f7fb' : '#fff',
    transition: 'all 0.15s',
  }),
  jobTypeIcon: { fontSize: 22, marginBottom: 6 },
  jobTypeLabel: { fontWeight: 600, fontSize: 14, color: '#1a2238' },
  jobTypeDesc: { fontSize: 12, color: '#6b7494', marginTop: 2 },
  footer: {
    display: 'flex', justifyContent: 'space-between',
    alignItems: 'center', marginTop: 8,
  },
  backBtn: {
    background: 'none', border: '1px solid #e1e5ee', color: '#1a2238',
    padding: '12px 22px', borderRadius: 10, fontWeight: 600,
    fontSize: 14, cursor: 'pointer',
  },
  nextBtn: {
    background: '#1a2238', color: '#fff', border: 'none',
    padding: '12px 28px', borderRadius: 10, fontWeight: 600,
    fontSize: 14, cursor: 'pointer', marginLeft: 'auto',
  },
  profileRow: {
    display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24,
    padding: 16, background: '#f5f7fb', borderRadius: 12,
  },
  avatar: {
    width: 54, height: 54, borderRadius: '50%',
    background: '#c9f04d', color: '#1a2238',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontWeight: 700, fontSize: 18, flexShrink: 0,
  },
  sectionLabel: {
    fontSize: 11, letterSpacing: 1, color: '#9ca3af',
    textTransform: 'uppercase', fontWeight: 600, marginBottom: 10,
  },
  error: { color: '#c0392b', fontSize: 13, marginBottom: 14 },
};

// Component
export default function Onboarding() {
  const nav = useNavigate();
  const user = getUser();

  // If already onboarded, skip straight to dashboard
  useEffect(() => {
    if (localStorage.getItem('cc_onboarded')) nav('/', { replace: true });
  }, [nav]);

  const [step, setStep] = useState(1); // 1, 2, 3
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Step 1 — Profile
  const [form, setForm] = useState({
    name: user?.name || '',
    course: user?.course || '',
    year: '',
    university: 'GISMA University of Applied Sciences',
  });

  // Step 2 — Skills
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [customSkill, setCustomSkill] = useState('');

  // Step 3 — Preferences
  const [jobType, setJobType] = useState('all');

  // Suggestions based on chosen course
  const suggestions = (COURSE_SKILLS[form.course] || DEFAULT_SKILLS).filter(
    s => !selectedSkills.includes(s)
  );

  const initials = form.name
    ? form.name.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase()
    : '?';

  // Handlers

  const toggleSkill = (s) => {
    setSelectedSkills(prev =>
      prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s]
    );
  };

  const addCustomSkill = () => {
    const t = customSkill.trim();
    if (!t || selectedSkills.includes(t)) return;
    setSelectedSkills(prev => [...prev, t]);
    setCustomSkill('');
  };

  const skip = () => {
    localStorage.setItem('cc_onboarded', '1');
    nav('/');
  };

  const next = async () => {
    setError('');

    if (step === 1) {
      // Save profile changes
      if (!form.name.trim()) { setError('Please enter your name.'); return; }
      setLoading(true);
      try {
        await api.updateProfile({ ...form, year: form.year ? Number(form.year) : null });
        const token = localStorage.getItem('cc_token');
        const u = getUser();
        if (u) setSession(token, { ...u, name: form.name, course: form.course });
        setStep(2);
      } catch (e) { setError(e.message); }
      finally { setLoading(false); }

    } else if (step === 2) {
      // Batch save skills
      if (selectedSkills.length === 0) { setError('Add at least one skill to get personalised matches.'); return; }
      setLoading(true);
      try {
        for (const s of selectedSkills) {
          await api.addSkill(s);
        }
        setStep(3);
      } catch (e) { setError(e.message); }
      finally { setLoading(false); }

    } else if (step === 3) {
      // Save preferences and finish
      localStorage.setItem('cc_prefs', JSON.stringify({ jobType }));
      localStorage.setItem('cc_onboarded', '1');
      nav('/');
    }
  };

  const back = () => setStep(s => s - 1);

  // Render
  return (
    <div style={S.wrap}>
      <div style={S.card}>
        {/* Header */}
        <div style={S.header}>
          <div style={S.logo}>
            <div style={S.logoMark}>G</div>
            <span style={S.logoName}>Career Connect</span>
          </div>
          <button style={S.skip} onClick={skip}>Skip for now</button>
        </div>

        {/* Progress */}
        <div style={S.progress}>
          {[1, 2, 3].map(n => (
            <div key={n} style={S.progressBar(n === step, n < step)} />
          ))}
        </div>

        {error && <div style={S.error}>{error}</div>}

        {/* Step 1: Profile */}
        {step === 1 && (
          <>
            <div style={S.stepLabel}>Step 1 of 3</div>
            <h2 style={S.title}>Confirm your profile</h2>
            <p style={S.subtitle}>We'll use this to personalise your job recommendations.</p>

            {/* Avatar row */}
            <div style={S.profileRow}>
              <div style={S.avatar}>{initials}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 15 }}>{form.name || 'Your name'}</div>
                <div style={{ color: '#6b7494', fontSize: 13 }}>{user?.email || ''}</div>
                <div style={{ color: '#9ca3af', fontSize: 12, marginTop: 2 }}>
                  {form.university}
                </div>
              </div>
            </div>

            <label style={S.label}>Full name</label>
            <input
              style={S.input}
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              placeholder="Alex Schmidt"
            />

            <label style={S.label}>Course / Programme</label>
            <select
              style={S.select}
              value={form.course}
              onChange={e => setForm({ ...form, course: e.target.value })}
            >
              <option value="">Select your course</option>
              {COURSES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>

            <div style={S.row}>
              <div style={{ flex: 1 }}>
                <label style={S.label}>Year of study</label>
                <input
                  style={{ ...S.input, marginBottom: 0 }}
                  type="number" min="1" max="6"
                  value={form.year}
                  onChange={e => setForm({ ...form, year: e.target.value })}
                  placeholder="e.g. 1"
                />
              </div>
              <div style={{ flex: 2 }}>
                <label style={S.label}>University</label>
                <input
                  style={{ ...S.input, marginBottom: 0 }}
                  value={form.university}
                  onChange={e => setForm({ ...form, university: e.target.value })}
                />
              </div>
            </div>

            <div style={{ ...S.footer, marginTop: 28 }}>
              <button style={S.nextBtn} onClick={next} disabled={loading}>
                {loading ? 'Saving…' : 'Continue →'}
              </button>
            </div>
          </>
        )}

        {/* Step 2: Skills */}
        {step === 2 && (
          <>
            <div style={S.stepLabel}>Step 2 of 3</div>
            <h2 style={S.title}>Add your skills</h2>
            <p style={S.subtitle}>
              We match you to jobs using these skills.
              {form.course && ` Top picks for ${form.course}:`}
            </p>

            {/* Custom skill input */}
            <div style={S.skillInput}>
              <input
                style={S.skillInputField}
                placeholder="Type a skill and press Enter…"
                value={customSkill}
                onChange={e => setCustomSkill(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addCustomSkill(); } }}
              />
              <button style={S.addBtn} onClick={addCustomSkill}>+ Add</button>
            </div>

            {/* Selected skills */}
            {selectedSkills.length > 0 && (
              <>
                <div style={S.sectionLabel}>Your skills ({selectedSkills.length})</div>
                <div style={S.chips}>
                  {selectedSkills.map(s => (
                    <span key={s} style={S.addedChip}>
                      {s}
                      <span
                        style={{ cursor: 'pointer', opacity: 0.7, fontSize: 15 }}
                        onClick={() => toggleSkill(s)}
                      >×</span>
                    </span>
                  ))}
                </div>
              </>
            )}

            {/* Suggestions */}
            {suggestions.length > 0 && (
              <>
                <div style={S.sectionLabel}>
                  {form.course ? `Suggested for ${form.course}` : 'Popular skills'}
                </div>
                <div style={S.chips}>
                  {suggestions.map(s => (
                    <span key={s} style={S.chip(false)} onClick={() => toggleSkill(s)}>
                      + {s}
                    </span>
                  ))}
                </div>
              </>
            )}

            <div style={S.footer}>
              <button style={S.backBtn} onClick={back}>← Back</button>
              <button style={S.nextBtn} onClick={next} disabled={loading}>
                {loading ? 'Saving…' : `Continue with ${selectedSkills.length} skill${selectedSkills.length !== 1 ? 's' : ''} →`}
              </button>
            </div>
          </>
        )}

        {/* Step 3: Preferences */}
        {step === 3 && (
          <>
            <div style={S.stepLabel}>Step 3 of 3</div>
            <h2 style={S.title}>What are you looking for?</h2>
            <p style={S.subtitle}>
              We'll use this to filter your job feed by default. You can always change it later.
            </p>

            <div style={S.sectionLabel}>Job type</div>
            <div style={S.jobTypeGrid}>
              {JOB_TYPES.map(jt => (
                <div
                  key={jt.key}
                  style={S.jobTypeCard(jobType === jt.key)}
                  onClick={() => setJobType(jt.key)}
                >
                  <div style={S.jobTypeIcon}>{jt.icon}</div>
                  <div style={S.jobTypeLabel}>{jt.label}</div>
                  <div style={S.jobTypeDesc}>{jt.desc}</div>
                </div>
              ))}
            </div>

            {/* Ready summary */}
            <div style={{
              background: '#f0fdf4', border: '1px solid #bbf7d0',
              borderRadius: 12, padding: '14px 16px', marginBottom: 28,
              display: 'flex', alignItems: 'center', gap: 12,
            }}>
              <span style={{ fontSize: 22 }}>🎉</span>
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, color: '#15803d' }}>You're all set!</div>
                <div style={{ fontSize: 13, color: '#166534', marginTop: 2 }}>
                  {selectedSkills.length} skill{selectedSkills.length !== 1 ? 's' : ''} added ·{' '}
                  {JOB_TYPES.find(j => j.key === jobType)?.label} preference saved
                </div>
              </div>
            </div>

            <div style={S.footer}>
              <button style={S.backBtn} onClick={back}>← Back</button>
              <button style={{ ...S.nextBtn, background: '#16a34a' }} onClick={next}>
                Start exploring jobs 🚀
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
