import axios from 'axios';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
// Create axios instance with default config
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});
// Add auth token to requests if available
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('authToken') || localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
class EmailService {
    /**
     * Send quantum-encrypted email
     */
    async sendQuantumEmail(emailData) {
        try {
            const response = await apiClient.post('/api/v1/emails/send/quantum', emailData);
            return response.data;
        }
        catch (error) {
            console.error('Error sending quantum email:', error);
            throw new Error(error.response?.data?.detail || 'Failed to send quantum email');
        }
    }
    /**
     * Decrypt quantum-secured email
     */
    async decryptEmail(emailId) {
        try {
            const response = await apiClient.post(`/api/v1/emails/email/${String(emailId)}/decrypt`);
            return response.data;
        }
        catch (error) {
            console.error('Error decrypting email:', error);
            throw new Error(error.response?.data?.detail || 'Failed to decrypt email');
        }
    }
    /**
     * Get email details (encrypted content only)
     */
    async getEmailDetails(emailId) {
        try {
            const response = await apiClient.get(`/api/v1/emails/email/${emailId}`);
            return response.data;
        }
        catch (error) {
            console.error('Error getting email details:', error);
            throw new Error(error.response?.data?.detail || 'Failed to get email details');
        }
    }
    /**
     * Get list of emails in folder
     */
    async getEmails(folder, pageToken, maxResults) {
        try {
            const params = new URLSearchParams();
            if (pageToken)
                params.append('page_token', pageToken);
            if (maxResults)
                params.append('max_results', maxResults.toString());
            const response = await apiClient.get(`/api/v1/emails/${folder}?${params.toString()}`);
            return response.data;
        }
        catch (error) {
            console.error('Error getting emails:', error);
            throw new Error(error.response?.data?.detail || 'Failed to get emails');
        }
    }
    /**
     * Get encryption system status
     */
    async getEncryptionStatus() {
        try {
            const response = await apiClient.get('/api/v1/emails/encryption/status');
            return response.data;
        }
        catch (error) {
            console.error('Error getting encryption status:', error);
            throw new Error(error.response?.data?.detail || 'Failed to get encryption status');
        }
    }
    /**
     * Get email folders
     */
    async getEmailFolders() {
        try {
            const response = await apiClient.get('/api/v1/emails/folders');
            return response.data;
        }
        catch (error) {
            console.error('Error getting email folders:', error);
            throw new Error(error.response?.data?.detail || 'Failed to get email folders');
        }
    }
    /**
     * Mark email as read/unread
     */
    async markEmailAsRead(emailId, isRead = true) {
        try {
            await apiClient.patch(`/api/v1/emails/email/${emailId}`, {
                is_read: isRead
            });
        }
        catch (error) {
            console.error('Error marking email as read:', error);
            throw new Error(error.response?.data?.detail || 'Failed to update email status');
        }
    }
    /**
     * Star/unstar email
     */
    async starEmail(emailId, isStarred = true) {
        try {
            await apiClient.patch(`/api/v1/emails/email/${emailId}`, {
                is_starred: isStarred
            });
        }
        catch (error) {
            console.error('Error starring email:', error);
            throw new Error(error.response?.data?.detail || 'Failed to update email status');
        }
    }
}
export const emailService = new EmailService();
export default emailService;
