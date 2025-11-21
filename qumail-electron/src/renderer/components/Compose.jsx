import { useState } from 'react';

const securityLevels = [
  { value: 1, label: 'Level 1 · OTP' },
  { value: 2, label: 'Level 2 · AES-256-GCM' },
  { value: 3, label: 'Level 3 · PQC' },
  { value: 4, label: 'Level 4 · Hybrid RSA' }
];

export default function Compose({ loading, onSend }) {
  const [form, setForm] = useState({ to: '', subject: '', body: '', securityLevel: 2 });

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSend(form);
  }

  return (
    <section className="card">
      <h3>Compose Encrypted Email</h3>
      <form onSubmit={handleSubmit}>
        <label>Recipient</label>
        <input type="email" required value={form.to} onChange={(e) => updateField('to', e.target.value)} />

        <label>Subject</label>
        <input type="text" required value={form.subject} onChange={(e) => updateField('subject', e.target.value)} />

        <label>Body</label>
        <textarea rows="4" required value={form.body} onChange={(e) => updateField('body', e.target.value)} />

        <label>Security Level</label>
        <select value={form.securityLevel} onChange={(e) => updateField('securityLevel', Number(e.target.value))}>
          {securityLevels.map((level) => (
            <option key={level.value} value={level.value}>{level.label}</option>
          ))}
        </select>

        <button type="submit" disabled={loading} style={{ width: '100%', marginTop: '0.75rem', background: '#0ea5e9', color: 'white' }}>
          {loading ? 'Encrypting…' : 'Send Encrypted'}
        </button>
      </form>
    </section>
  );
}
