const ICONS = {
  'Siemens': '⚙️',
  'HelloFresh': '🥗',
  'Delivery Hero': '🛵',
  'Zalando': '👗',
  'BMW Group': '🚗',
  'N26': '🏦',
  'Trivago': '🏨',
  'SAP': '☁️',
  'Booking.com': '🌍',
  'Spotify': '🎧',
  'About You': '👕',
  'Flink': '⚡'
};

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const days = Math.round((Date.now() - d.getTime()) / 86400000);
  if (days <= 0) return 'today';
  if (days === 1) return '1 day ago';
  return `${days} days ago`;
}

export default function JobCard({ job }) {
  const matchClass = job.matchPercent >= 50 ? '' : 'match-low';
  const missing = job.missingSkills || [];

  return (
    <div className="job">
      <div className="job-icon">{ICONS[job.company] || '💼'}</div>

      <div className="job-body">
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <div className="job-title">{job.title}</div>
          {/* BERT semantic boost badge — shown when BERT found hidden compatibility */}
          {job.semanticBoost && (
            <span style={{
              fontSize: 10, fontWeight: 600, padding: '2px 6px',
              background: '#e0f2fe', color: '#0369a1',
              borderRadius: 99, whiteSpace: 'nowrap'
            }}>
              BERT match
            </span>
          )}
        </div>

        <div className="job-company">{job.company} · {job.location}</div>

        {/* Required skills — green if student has it, gray if missing */}
        <div className="job-tags">
          {job.requiredSkills.map((s) => {
            const isMissing = missing.includes(s);
            return (
              <span
                key={s}
                className="job-tag"
                style={isMissing ? { background: '#fef3c7', color: '#92400e', border: '1px solid #fcd34d' } : {}}
                title={isMissing ? `You don't have ${s} yet` : `You have ${s}`}
              >
                {isMissing ? '⚠ ' : ''}{s}
              </span>
            );
          })}
        </div>

        {/* Skill gap row */}
        {missing.length > 0 && (
          <div style={{ fontSize: 11, color: '#92400e', marginTop: 4 }}>
            Skill gap: learn <strong>{missing.slice(0, 3).join(', ')}</strong>
            {missing.length > 3 ? ` + ${missing.length - 3} more` : ''} to strengthen this match
          </div>
        )}

        <div className="job-meta">
          {job.salary && <span>💰 {job.salary}</span>}
          <span>🕒 {timeAgo(job.postedDate)}</span>
          <span>📌 {job.jobType}</span>
        </div>
      </div>

      <div className={`match-pill ${matchClass}`}>{job.matchPercent}% match</div>
    </div>
  );
}
