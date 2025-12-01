function formatDate(value) {
  const date = new Date(value);
  return date.toLocaleString();
}

function getSecurityBadge(level) {
  if (!level || level === 0 || level === 4) return null;
  
  const badges = {
    1: { color: '#9333ea', bg: '#f3e8ff', label: 'Level 1: Quantum OTP', icon: '⚡' },
    2: { color: '#2563eb', bg: '#dbeafe', label: 'Level 2: Quantum AES', icon: '⚡' },
    3: { color: '#059669', bg: '#d1fae5', label: 'Level 3: Post-Quantum', icon: '⚡' }
  };
  
  const badge = badges[level];
  if (!badge) return null;
  
  return (
    <div style={{ 
      display: 'inline-flex', 
      alignItems: 'center', 
      gap: '4px',
      padding: '4px 8px', 
      borderRadius: '6px', 
      fontSize: '11px', 
      fontWeight: 'bold',
      color: badge.color,
      backgroundColor: badge.bg,
      border: `1px solid ${badge.color}40`,
      marginTop: '8px'
    }}>
      <span>{badge.icon}</span>
      <span>{badge.label}</span>
    </div>
  );
}

export default function Inbox({ messages, onSelect }) {
  return (
    <section className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>Encrypted Inbox</h3>
        <span className="badge">{messages.length} messages</span>
      </div>
      <div className="inbox-list">
        {messages.map((message) => (
          <article key={message.id} className="inbox-item" onClick={() => onSelect(message)} style={{ cursor: 'pointer' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <strong>{message.subject || 'Encrypted Message'}</strong>
              <small>{formatDate(message.timestamp || Date.now())}</small>
            </div>
            <p style={{ color: '#8ea5ce', margin: '0.35rem 0' }}>{message.preview || '-----BEGIN QUMAIL ENCRYPTED MESSAGE-----'}</p>
            {getSecurityBadge(message.security_level)}
          </article>
        ))}
        {messages.length === 0 && <p>No encrypted emails yet.</p>}
      </div>
    </section>
  );
}
