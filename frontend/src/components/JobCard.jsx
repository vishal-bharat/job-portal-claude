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
  return (
    <div className="job">
      <div className="job-icon">{ICONS[job.company] || '💼'}</div>
      <div className="job-body">
        <div className="job-title">{job.title}</div>
        <div className="job-company">{job.company} · {job.location}</div>
        <div className="job-tags">
          {job.requiredSkills.map((s) => <span key={s} className="job-tag">{s}</span>)}
        </div>
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
