function formatDate(value) {
  const date = new Date(value);
  return date.toLocaleString();
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
            <div className="badge">🔒 Level {message.security_level || '?'} </div>
          </article>
        ))}
        {messages.length === 0 && <p>No encrypted emails yet.</p>}
      </div>
    </section>
  );
}
