import { useEffect, useState } from 'react';
import Sidebar from '../components/Sidebar.jsx';
import Loader  from '../components/Loader.jsx';
import { api } from '../api/client.js';

const STEP_COLORS = ['#0369a1', '#7c3aed', '#15803d', '#b45309', '#b91c1c'];

const RESOURCES = {
  'Python':           'https://www.python.org/doc/',
  'JavaScript':       'https://developer.mozilla.org/en-US/docs/Web/JavaScript',
  'SQL':              'https://www.w3schools.com/sql/',
  'Machine Learning': 'https://www.coursera.org/learn/machine-learning',
  'Data Analysis':    'https://www.kaggle.com/learn/pandas',
  'React':            'https://react.dev/learn',
  'Docker':           'https://docs.docker.com/get-started/',
  'AWS':              'https://aws.amazon.com/training/',
  'Excel':            'https://support.microsoft.com/en-us/excel',
  'Tableau':          'https://www.tableau.com/learn/training',
  'Power BI':         'https://learn.microsoft.com/en-us/power-bi/',
  'SAP':              'https://learning.sap.com/',
  'Figma':            'https://help.figma.com/hc/en-us/categories/360002051613-Get-started',
  'Java':             'https://dev.java/learn/',
  'TypeScript':       'https://www.typescriptlang.org/docs/',
  'Node.js':          'https://nodejs.org/en/learn',
  'Git':              'https://git-scm.com/doc',
  'Agile':            'https://www.atlassian.com/agile',
};

export default function SkillGap() {
  const [gap, setGap]         = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState('');

  useEffect(() => {
    Promise.all([api.skillGap(), api.getProfile()])
      .then(([g, p]) => { setGap(g); setProfile(p); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="app"><Sidebar />
      <div className="main" style={{ gridTemplateColumns: '1fr' }}>
        <Loader fullPage text="Analysing your skill gaps…" />
      </div>
    </div>
  );

  const learningPath = gap?.learning_path || [];
  const topMissing   = gap?.top_missing   || [];
  const currentSkills = profile?.skills || [];

  return (
    <div className="app">
      <Sidebar />
      <div className="main">
        <div>
          <h1 className="page-title">🧩 Skill Gap Analysis</h1>
          {error && <div className="error">{error}</div>}

          {/* Current skills */}
          <div className="card">
            <h2 className="section-title">Your Current Skills</h2>
            <div className="chips">
              {currentSkills.length === 0
                ? <span style={{ color: '#6b7494', fontSize: 13 }}>No skills yet — add them on the Opportunities page.</span>
                : currentSkills.map(s => <span key={s} className="chip">✓ {s}</span>)
              }
            </div>
          </div>

          {/* Recommended learning path */}
          <div className="card">
            <h2 className="section-title">📚 Recommended Learning Path</h2>
            <p style={{ fontSize: 13, color: '#6b7494', marginTop: 0 }}>
              Ranked by our <strong>GISMABERT Semantic Similarity</strong> engine — skills demanded by your
              closest-matching jobs appear first. Upload your CV on the{' '}
              <a href="/profile" style={{ color: '#0369a1' }}>Profile page</a> to auto-populate your skills.
            </p>

            {learningPath.length === 0 ? (
              <div style={{ color: '#2a9d8f', fontWeight: 600 }}>
                🎉 You're well-matched! No critical skill gaps detected.
              </div>
            ) : (
              <div style={{ position: 'relative' }}>
                {/* Vertical timeline line */}
                <div style={{
                  position: 'absolute', left: 18, top: 24, bottom: 24,
                  width: 2, background: '#e1e5ee', zIndex: 0,
                }} />
                {learningPath.map((skill, i) => {
                  const item = topMissing.find(m => m.skill === skill);
                  const color = STEP_COLORS[i % STEP_COLORS.length];
                  const resource = RESOURCES[skill];
                  return (
                    <div key={skill} style={{
                      display: 'flex', alignItems: 'flex-start', gap: 14,
                      marginBottom: 20, position: 'relative', zIndex: 1,
                    }}>
                      <div style={{
                        width: 36, height: 36, borderRadius: '50%',
                        background: color, color: '#fff',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontWeight: 700, fontSize: 14, flexShrink: 0,
                      }}>{i + 1}</div>
                      <div style={{
                        flex: 1, background: '#f8faff',
                        border: '1px solid #e1e5ee', borderRadius: 12, padding: '12px 16px',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 700, fontSize: 15 }}>{skill}</span>
                          <span style={{ color: '#2a9d8f', fontWeight: 600, fontSize: 13 }}>
                            +{item?.unlocks_jobs ?? '?'} jobs unlocked
                          </span>
                        </div>
                        {resource && (
                          <a href={resource} target="_blank" rel="noopener noreferrer"
                            style={{ fontSize: 12, color: '#0369a1', marginTop: 6, display: 'inline-block' }}>
                            📖 Start learning →
                          </a>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Right col */}
        <div className="right-col">
          <div className="card">
            <h2 className="section-title">Top Missing Skills</h2>
            <p style={{ fontSize: 12, color: '#6b7494', marginTop: 0 }}>
              Ranked by how many additional jobs each skill unlocks.
            </p>
            {topMissing.slice(0, 10).map((item, i) => (
              <div key={item.skill} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
                  <span style={{ fontWeight: 500 }}>#{i + 1} {item.skill}</span>
                  <span style={{ color: '#2a9d8f', fontWeight: 600 }}>+{item.unlocks_jobs} jobs</span>
                </div>
                <div className="bar">
                  <span style={{ width: `${Math.min(100, item.unlocks_jobs * 10)}%` }} />
                </div>
              </div>
            ))}
            {topMissing.length === 0 && (
              <div style={{ color: '#2a9d8f', fontSize: 13 }}>No skill gaps — great work!</div>
            )}
          </div>

          <div className="card">
            <h2 className="section-title">💡 How it works</h2>
            <p style={{ fontSize: 13, color: '#6b7494', lineHeight: 1.6 }}>
              Skills are matched against live job postings using{' '}
              <strong>GISMABERT Semantic Similarity</strong> — our domain-fine-tuned BERT model
              selected after comparing four approaches: Greedy Set Cover, GISMABERT Semantic,
              RAG-Inspired Retrieval, and Collaborative Filtering. GISMABERT Semantic achieved
              the highest domain precision (65%) and coverage (48.8%) in evaluation.
            </p>
            <p style={{ fontSize: 13, color: '#6b7494', lineHeight: 1.6, marginBottom: 12 }}>
              Missing skills are weighted by how closely the jobs that require them match
              your profile — skills demanded by your best-matched roles rank highest.
            </p>
            <a href="/profile" style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              fontSize: 13, color: '#0369a1', fontWeight: 600,
              textDecoration: 'none',
              background: '#f0f7ff', border: '1px solid #bfdbfe',
              borderRadius: 8, padding: '8px 14px',
            }}>
              📄 Upload CV to auto-fill skills →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
