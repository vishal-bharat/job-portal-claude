import { useEffect, useState, useMemo } from 'react';
import Sidebar from '../components/Sidebar.jsx';
import JobCard from '../components/JobCard.jsx';
import { api } from '../api/client.js';

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'fulltime', label: 'Full-time' },
  { key: 'internship', label: 'Internship' },
  { key: 'remote', label: 'Remote' },
  { key: 'parttime', label: 'Part-time' },
];

const TRENDING = [
  { role: 'ML Engineer', openings: '1,240 openings', change: '+34%' },
  { role: 'Product Designer', openings: '890 openings', change: '+22%' },
  { role: 'Data Analyst', openings: '2,110 openings', change: '+19%' },
  { role: 'Full Stack Dev', openings: '3,450 openings', change: '+15%' },
  { role: 'Cybersecurity Analyst', openings: '670 openings', change: '+41%' },
];

// Normalise a raw job object from the Python backend (snake_case → camelCase)
function normaliseJob(job) {
  return {
    ...job,
    matchPercent:   job.match_percent   ?? job.matchPercent   ?? 0,
    requiredSkills: job.required_skills ?? job.requiredSkills ?? [],
    missingSkills:  job.missing_skills  ?? job.missingSkills  ?? [],
    semanticBoost:  job.semantic_boost  ?? job.semanticBoost  ?? false,
    postedDate:     job.posted_date     ?? job.postedDate,
    jobType:        job.job_type        ?? job.jobType,
  };
}

export default function Dashboard() {
  const [profile, setProfile] = useState(null);
  const [allSkills, setAllSkills] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [skillGap, setSkillGap] = useState(null);   // { top_missing, learning_path }
  const [filter, setFilter] = useState('all');
  const [newSkill, setNewSkill] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const refresh = async (currentFilter = filter) => {
    setError('');
    try {
      const [p, s, j, gap] = await Promise.all([
        api.getProfile(),
        api.allSkills(),
        api.recommendedJobs(currentFilter),
        api.skillGap(),
      ]);
      setProfile(p);
      setAllSkills(s);
      setJobs(j.map(normaliseJob));
      setSkillGap(gap);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); /* eslint-disable-next-line */ }, []);

  const handleAddSkill = async (name) => {
    if (!name.trim()) return;
    setNewSkill('');
    try {
      await api.addSkill(name);
      await refresh();
    } catch (e) { setError(e.message); }
  };

  const handleRemoveSkill = async (name) => {
    try {
      await api.removeSkill(name);
      await refresh();
    } catch (e) { setError(e.message); }
  };

  const handleFilter = (key) => {
    setFilter(key);
    refresh(key);
  };

  // Per-skill: how many jobs require it
  const skillStats = useMemo(() => {
    if (!profile) return [];
    return profile.skills.map((s) => ({
      name: s,
      count: jobs.filter((j) => j.requiredSkills.some((rs) => rs.toLowerCase() === s.toLowerCase())).length
    }));
  }, [profile, jobs]);

  // Suggested skills the student doesn't have yet
  const suggested = useMemo(() => {
    if (!profile) return [];
    return allSkills.filter((s) => !profile.skills.includes(s)).slice(0, 10);
  }, [allSkills, profile]);

  // Count BERT-boosted jobs for the banner
  const semanticBoostCount = useMemo(
    () => jobs.filter(j => j.semanticBoost).length,
    [jobs]
  );

  if (loading) return <div className="app"><Sidebar /><div className="main"><p>Loading…</p></div></div>;

  return (
    <div className="app">
      <Sidebar />
      <div className="main">
        <div>
          <h1 className="page-title">Opportunities</h1>

          {error && <div className="error">{error}</div>}

          {/* BERT info banner */}
          {semanticBoostCount > 0 && (
            <div style={{
              background: '#eff6ff', border: '1px solid #bfdbfe',
              borderRadius: 8, padding: '8px 14px', marginBottom: 12,
              fontSize: 13, color: '#1d4ed8'
            }}>
              🧠 <strong>BERT semantic matching</strong> found {semanticBoostCount} extra job
              {semanticBoostCount > 1 ? 's' : ''} you may not have matched with keyword search alone.
              Look for the <span style={{ background: '#e0f2fe', padding: '1px 5px', borderRadius: 4 }}>BERT match</span> badge.
            </div>
          )}

          {/* Skills card */}
          <div className="card">
            <div className="skill-input">
              <input
                placeholder="e.g. Python, UI/UX, Data Analysis…"
                value={newSkill}
                onChange={(e) => setNewSkill(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleAddSkill(newSkill); } }}
              />
              <button className="btn-primary" onClick={() => handleAddSkill(newSkill)}>+ Add Skill</button>
            </div>

            <div className="chips">
              {profile.skills.map((s) => (
                <span key={s} className="chip">
                  {s} <span className="x" onClick={() => handleRemoveSkill(s)} title="Remove">×</span>
                </span>
              ))}
              {profile.skills.length === 0 && (
                <div style={{ fontSize: 13, color: '#6b7494' }}>Add a skill to start seeing matched opportunities.</div>
              )}
            </div>

            <div className="suggested-label">SUGGESTED SKILLS</div>
            <div className="chips">
              {suggested.map((s) => (
                <span key={s} className="chip chip-suggested" onClick={() => handleAddSkill(s)}>{s}</span>
              ))}
            </div>
          </div>

          {/* Filter tabs */}
          <div className="tabs">
            {FILTERS.map((f) => (
              <button key={f.key}
                      className={`tab ${filter === f.key ? 'active' : ''}`}
                      onClick={() => handleFilter(f.key)}>{f.label}</button>
            ))}
          </div>

          {/* Jobs */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h2 className="section-title" style={{ margin: 0 }}>Matched Opportunities</h2>
              <span style={{ fontSize: 12, color: '#6b7494' }}>{jobs.length} results</span>
            </div>
            {jobs.length === 0
              ? <div style={{ fontSize: 13, color: '#6b7494' }}>No matching opportunities. Try adding more skills.</div>
              : jobs.map((j) => <JobCard key={j.id} job={j} />)}
          </div>
        </div>

        {/* Right column */}
        <div className="right-col">
          <div className="card">
            <h2 className="section-title">Your Skills · Job Matches</h2>
            {skillStats.length === 0 && <div style={{ fontSize: 13, color: '#6b7494' }}>No skills yet.</div>}
            {skillStats.map((s) => (
              <div key={s.name} style={{ marginBottom: 8 }}>
                <div className="label-row" style={{ borderBottom: 'none', padding: '2px 0' }}>
                  <span>{s.name}</span>
                  <span style={{ color: '#6b7494' }}>{s.count} jobs</span>
                </div>
                <div className="bar"><span style={{ width: `${Math.min(100, s.count * 25)}%` }} /></div>
              </div>
            ))}
          </div>

          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
              <h2 className="section-title" style={{ margin: 0 }}>Trending Roles</h2>
              <span style={{ fontSize: 12, color: '#6b7494' }}>View more</span>
            </div>
            {TRENDING.map((t) => (
              <div key={t.role} className="label-row">
                <div>
                  <div style={{ fontWeight: 600 }}>{t.role}</div>
                  <div style={{ fontSize: 11, color: '#6b7494' }}>{t.openings}</div>
                </div>
                <div style={{ color: '#2a9d8f', fontWeight: 600 }}>↑ {t.change}</div>
              </div>
            ))}
          </div>

          {/* Skill Gap card — powered by the backend's greedy set-cover algorithm */}
          <div className="card">
            <h2 className="section-title">🎓 Your Skill Gap Analysis</h2>

            {skillGap && skillGap.learning_path && skillGap.learning_path.length > 0 ? (
              <>
                <div style={{ fontSize: 12, color: '#6b7494', marginBottom: 8 }}>
                  Recommended learning order to unlock the most jobs:
                </div>
                {skillGap.learning_path.map((skill, i) => {
                  const item = skillGap.top_missing?.find(m => m.skill === skill);
                  return (
                    <div key={skill} className="label-row" style={{ alignItems: 'center' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{
                          width: 20, height: 20, borderRadius: '50%',
                          background: '#e0f2fe', color: '#0369a1',
                          fontSize: 11, fontWeight: 700,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          flexShrink: 0
                        }}>{i + 1}</span>
                        <span style={{ fontWeight: 500 }}>{skill}</span>
                      </div>
                      <span style={{ color: '#2a9d8f', fontWeight: 600, fontSize: 12 }}>
                        +{item?.unlocks_jobs ?? '?'} jobs
                      </span>
                    </div>
                  );
                })}
              </>
            ) : (
              <div style={{ fontSize: 13, color: '#6b7494' }}>
                You're well matched! Add more skills to unlock more opportunities.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
