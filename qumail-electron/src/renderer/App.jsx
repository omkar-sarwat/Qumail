import { useEffect, useState } from 'react';
import Login from './components/Login.jsx';
import Compose from './components/Compose.jsx';
import Inbox from './components/Inbox.jsx';
import Decrypt from './components/Decrypt.jsx';
import SessionStatus from './components/SessionStatus.jsx';

export default function App() {
  const [session, setSession] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [inbox, setInbox] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [decryptedContent, setDecryptedContent] = useState(null);

  useEffect(() => {
    async function loadSession() {
      const cached = await window.qumail.loadSession();
      if (cached) {
        setSession(cached);
        fetchInbox();
      }
    }
    loadSession();
  }, []);

  function handleError(message) {
    setError(message);
    setTimeout(() => setError(''), 5000);
  }

  async function handleLogin() {
    try {
      setLoading(true);
      const result = await window.qumail.loginWithGoogle();
      setSession(result.user);
      await fetchInbox();
    } catch (err) {
      handleError(err?.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  }

  async function fetchInbox() {
    try {
      setLoading(true);
      const messages = await window.qumail.getInbox();
      setInbox(messages || []);
    } catch (err) {
      handleError('Unable to load inbox');
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(payload) {
    try {
      setLoading(true);
      await window.qumail.sendEncryptedEmail(payload);
      await fetchInbox();
    } catch (err) {
      handleError('Failed to send encrypted email');
    } finally {
      setLoading(false);
    }
  }

  async function handleDecrypt(messageId) {
    try {
      setLoading(true);
      const plaintext = await window.qumail.decryptEmail(messageId);
      setDecryptedContent(plaintext);
    } catch (err) {
      handleError('Decryption failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleLogout() {
    await window.qumail.clearSession();
    setSession(null);
    setInbox([]);
    setSelectedMessage(null);
    setDecryptedContent(null);
  }

  if (!session) {
    return <Login loading={loading} onLogin={handleLogin} error={error} />;
  }

  return (
    <div className="dashboard">
      <aside className="sidebar">
        <SessionStatus session={session} loading={loading} onRefresh={fetchInbox} onLogout={handleLogout} />
        <Compose loading={loading} onSend={handleSend} />
      </aside>
      <main className="content">
        {error && <div className="card" style={{ borderColor: '#f87171', color: '#f87171' }}>{error}</div>}
        <Inbox
          messages={inbox}
          onSelect={(msg) => {
            setSelectedMessage(msg);
            setDecryptedContent(null);
          }}
        />
        {selectedMessage && (
          <Decrypt
            message={selectedMessage}
            decryptedContent={decryptedContent}
            loading={loading}
            onDecrypt={() => handleDecrypt(selectedMessage.id)}
          />
        )}
      </main>
    </div>
  );
}
