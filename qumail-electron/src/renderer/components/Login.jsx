export default function Login({ loading, onLogin, error }) {
  return (
    <div className="dashboard" style={{ placeItems: 'center', display: 'grid' }}>
      <div className="card" style={{ width: 420 }}>
        <h2>QuMail Secure Desktop</h2>
        <p>Sign in with Google to access your quantum-encrypted mailbox.</p>
        <button onClick={onLogin} disabled={loading} style={{ width: '100%', background: '#2563eb', color: 'white' }}>
          {loading ? 'Connecting…' : 'Sign in with Google'}
        </button>
        {error && <p style={{ color: '#f87171' }}>{error}</p>}
      </div>
    </div>
  );
}
