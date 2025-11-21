const axios = require('axios');
const storage = require('./storage');
const config = require('../../config');

const API_BASE_URL = process.env.QUMAIL_API_BASE_URL || config.apiBaseUrl;

function getAuthHeaders() {
  const session = storage.loadSession();
  const headers = { 'Content-Type': 'application/json' };
  if (session?.jwt) {
    headers.Authorization = `Bearer ${session.jwt}`;
  }
  return headers;
}

async function sendEncryptedEmail(to, subject, body, securityLevel) {
  const response = await axios.post(`${API_BASE_URL}/messages/send`, {
    to,
    subject,
    body,
    security_level: securityLevel
  }, { headers: getAuthHeaders() });
  return response.data;
}

async function getInbox() {
  const response = await axios.get(`${API_BASE_URL}/messages/inbox`, {
    headers: getAuthHeaders()
  });
  return response.data;
}

async function decryptEmail(messageId) {
  const response = await axios.post(`${API_BASE_URL}/messages/${messageId}/decrypt`, {}, {
    headers: getAuthHeaders()
  });
  return response.data;
}

module.exports = { sendEncryptedEmail, getInbox, decryptEmail };
