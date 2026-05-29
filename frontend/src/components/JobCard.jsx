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

// Source badge config — label + colour for each job origin
const SOURCE_BADGE = {
  linkedin:  { label: 'LinkedIn',   bg: '#0a66c2', color: '#fff' },
  stepstone: { label: 'StepStone',  bg: '#ff6600', color: '#fff' },
  seed:      { label: 'Featured',   bg: '#e5e7eb', color: '#374151' },
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
  const missing    = job.missingSkills || [];
  const srcBadge   = SOURCE_BADGE[job.source] || SOURCE_BADGE.seed;
  // Show apply button for any real job (linkedin/stepstone) — always has a URL
  const hasApply   = job.source === 'linkedin' || job.source === 'stepstone';

  return (
    <div className="job">
      <div className="job-icon">{ICONS[job.company] || '💼'}</div>

      <div className="job-body">
        {/* Title row: source badge + BERT badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <div className="job-title">{job.title}</div>

          {/* Source badge — LinkedIn / StepStone / Featured */}
          <span style={{
            fontSize: 10, fontWeight: 700, padding: '2px 7px',
            background: srcBadge.bg, color: srcBadge.color,
            borderRadius: 99, whiteSpace: 'nowrap', letterSpacing: '0.02em'
          }}>
            {srcBadge.label}
          </span>

          {/* BERT semantic boost badge */}
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

        {/* Required skills — yellow if missing */}
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

        {/* Skill gap hint */}
        {missing.length > 0 && (
          <div style={{ fontSize: 11, color: '#92400e', marginTop: 4 }}>
            Skill gap: learn <strong>{missing.slice(0, 3).join(', ')}</strong>
            {missing.length > 3 ? ` + ${missing.length - 3} more` : ''} to strengthen this match
          </div>
        )}

        {/* Meta row */}
        <div className="job-meta">
          {job.salary && <span>💰 {job.salary}</span>}
          <span>🕒 {timeAgo(job.postedDate)}</span>
          <span>📌 {job.jobType}</span>
        </div>
      </div>

      {/* Right column: match pill + apply button */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8, flexShrink: 0 }}>
        <div className={`match-pill ${matchClass}`}>{job.matchPercent}% match</div>

        {hasApply && (
          <a
            href={job.applyUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              display: 'inline-block',
              padding: '6px 14px',
              background: srcBadge.bg,
              color: srcBadge.color,
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 600,
              textDecoration: 'none',
              whiteSpace: 'nowrap',
            }}
          >
            Apply →
          </a>
        )}
      </div>
    </div>
  );
}
