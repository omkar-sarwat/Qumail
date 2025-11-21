const Store = require('electron-store');

const store = new Store({
  name: 'session',
  encryptionKey: process.env.QUMAIL_STORE_KEY || undefined
});

function saveSession(user, jwtToken) {
  store.set('user', {
    email: user.email,
    id: user.id,
    jwt: jwtToken,
    lastLogin: new Date().toISOString()
  });
}

function loadSession() {
  return store.get('user', null);
}

function clearSession() {
  store.delete('user');
}

module.exports = { saveSession, loadSession, clearSession };
