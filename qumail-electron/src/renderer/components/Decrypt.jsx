export default function Decrypt({ message, decryptedContent, loading, onDecrypt }) {
  return (
    <section className="card">
      <h3>Decrypt Message</h3>
      <p><strong>Subject:</strong> {message.subject}</p>
      <p><strong>From:</strong> {message.from}</p>
      <div className="actions" style={{ margin: '1rem 0' }}>
        <button onClick={onDecrypt} disabled={loading} style={{ background: '#22c55e', color: '#052e16' }}>
          {loading ? 'Decrypting…' : 'Decrypt' }
        </button>
      </div>
      {decryptedContent ? (
        <pre style={{ background: '#020617', padding: '1rem', borderRadius: '8px', whiteSpace: 'pre-wrap' }}>{decryptedContent.body || JSON.stringify(decryptedContent, null, 2)}</pre>
      ) : (
        <pre style={{ background: '#0f172a', padding: '1rem', borderRadius: '8px', color: '#94a3b8' }}>{message.body || 'Encrypted content displayed until decryption.'}</pre>
      )}
    </section>
  );
}
