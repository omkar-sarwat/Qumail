export default function SessionStatus({ session, loading, onRefresh, onLogout }) {
  return (
    <section className="card">
      <h3>Session</h3>
      <p>{session.email}</p>
      <p style={{ color: '#94a3b8' }}>Last login: {session.lastLogin ? new Date(session.lastLogin).toLocaleString() : 'Active'}</p>
      <div className="actions">
        <button onClick={onRefresh} disabled={loading} style={{ background: '#38bdf8', color: '#082f49' }}>Refresh Inbox</button>
        <button onClick={onLogout} style={{ background: '#f87171', color: '#450a0a' }}>Logout</button>
      </div>
    </section>
  );
}
