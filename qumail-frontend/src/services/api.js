import axios from 'axios';
import { useAuthStore } from '../stores/authStore';
class ApiService {
    constructor() {
        Object.defineProperty(this, "api", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "baseURL", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: void 0
        });
        Object.defineProperty(this, "token", {
            enumerable: true,
            configurable: true,
            writable: true,
            value: null
        });
        this.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        console.log('API Service initialized with baseURL:', this.baseURL);
        this.api = axios.create({
            baseURL: this.baseURL,
            timeout: 30000,
            headers: {
                'Content-Type': 'application/json',
            },
        });
        // Request interceptor to add auth token
        this.api.interceptors.request.use((config) => {
            const token = this.token ||
                useAuthStore.getState().sessionToken ||
                localStorage.getItem('authToken') ||
                'VALID_ACCESS_TOKEN'; // Test token fallback for development
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        }, (error) => {
            console.error('Request interceptor error:', error);
            return Promise.reject(error);
        });
        // Response interceptor to handle auth errors
        this.api.interceptors.response.use((response) => response, (error) => {
            if (error.response?.status === 401) {
                // Token expired or invalid
                useAuthStore.getState().logout();
                window.location.href = '/';
            }
            return Promise.reject(error);
        });
    }
    // Helper to ensure consistent API version prefix
    withPrefix(path) {
        if (path.startsWith('/api/'))
            return path; // already fully qualified
        return `/api/v1${path}`;
    }
    // Health and Status
    async getHealth() {
        const response = await this.api.get(this.withPrefix('/health'));
        return response.data;
    }
    async getDetailedHealth() {
        const response = await this.api.get(this.withPrefix('/health/detailed'));
        return response.data;
    }
    // Authentication
    async getAuthUrl() {
        const response = await this.api.get(this.withPrefix('/auth/url'));
        return response.data;
    }
    async exchangeCode(code) {
        const response = await this.api.post(this.withPrefix('/auth/callback'), {
            code,
        });
        return response.data;
    }
    async getUserProfile() {
        const response = await this.api.get(this.withPrefix('/auth/profile'));
        return response.data;
    }
    async refreshToken() {
        const response = await this.api.post(this.withPrefix('/auth/refresh'));
        return response.data;
    }
    async logout() {
        await this.api.post(this.withPrefix('/auth/logout'));
    }
    // Emails
    async getEmails(params = {}) {
        const { folder = 'inbox', pageToken, maxResults, ...rest } = params;
        const query = { ...rest };
        if (pageToken)
            query.page_token = pageToken;
        if (typeof maxResults !== 'undefined')
            query.max_results = maxResults;
        const response = await this.api.get(this.withPrefix(`/emails/${folder}`), { params: query });
        const data = response.data ?? {};
        return {
            emails: data.emails ?? [],
            nextPageToken: data.next_page_token ?? data.nextPageToken,
            totalCount: data.total_count ?? data.totalCount ?? (data.emails ? data.emails.length : 0),
        };
    }
    async getEmailDetails(emailId) {
        const response = await this.api.get(this.withPrefix(`/emails/email/${emailId}`));
        return response.data;
    }
    async markEmailAsRead(emailId, isRead) {
        await this.api.post(this.withPrefix(`/emails/${emailId}/read`), { isRead });
    }
    async toggleEmailStar(emailId, isStarred) {
        await this.api.patch(this.withPrefix(`/emails/${emailId}/star`), { isStarred });
    }
    async deleteEmail(emailId) {
        await this.api.delete(this.withPrefix(`/emails/${emailId}`));
    }
    async moveEmailToTrash(emailId) {
        await this.api.post(this.withPrefix(`/emails/${emailId}/trash`));
    }
    async archiveEmail(emailId) {
        await this.api.post(this.withPrefix(`/emails/${emailId}/archive`));
    }
    // Compose and Send
    async sendEmail(emailData) {
        const formData = new FormData();
        // Add text fields
        formData.append('to', emailData.to);
        if (emailData.cc)
            formData.append('cc', emailData.cc);
        if (emailData.bcc)
            formData.append('bcc', emailData.bcc);
        formData.append('subject', emailData.subject);
        formData.append('body', emailData.body);
        formData.append('isHtml', emailData.isHtml.toString());
        formData.append('securityLevel', emailData.securityLevel.toString());
        // Add attachments
        if (emailData.attachments) {
            emailData.attachments.forEach((file, index) => {
                formData.append(`attachment_${index}`, file);
            });
        }
        const response = await this.api.post(this.withPrefix('/emails/send'), formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
    async scheduleEmail(emailData) {
        const formData = new FormData();
        // Add all email fields
        formData.append('to', emailData.to);
        if (emailData.cc)
            formData.append('cc', emailData.cc);
        if (emailData.bcc)
            formData.append('bcc', emailData.bcc);
        formData.append('subject', emailData.subject);
        formData.append('body', emailData.body);
        formData.append('isHtml', emailData.isHtml.toString());
        formData.append('securityLevel', emailData.securityLevel.toString());
        formData.append('scheduledDate', emailData.scheduledDate);
        // Add attachments
        if (emailData.attachments) {
            emailData.attachments.forEach((file, index) => {
                formData.append(`attachment_${index}`, file);
            });
        }
        const response = await this.api.post(this.withPrefix('/emails/schedule'), formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
    // Drafts
    async getDrafts() {
        const response = await this.api.get(this.withPrefix('/drafts'));
        return response.data;
    }
    async getDraft(draftId) {
        const response = await this.api.get(this.withPrefix(`/drafts/${draftId}`));
        return response.data;
    }
    async saveDraft(draftData) {
        const formData = new FormData();
        // Add text fields
        formData.append('to', draftData.to);
        if (draftData.cc)
            formData.append('cc', draftData.cc);
        if (draftData.bcc)
            formData.append('bcc', draftData.bcc);
        formData.append('subject', draftData.subject);
        formData.append('body', draftData.body);
        formData.append('isHtml', draftData.isHtml.toString());
        formData.append('securityLevel', draftData.securityLevel.toString());
        if (draftData.scheduledDate)
            formData.append('scheduledDate', draftData.scheduledDate);
        // Add attachments
        if (draftData.attachments) {
            draftData.attachments.forEach((file, index) => {
                formData.append(`attachment_${index}`, file);
            });
        }
        const response = await this.api.post(this.withPrefix('/drafts'), formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
    async updateDraft(draftId, draftData) {
        const formData = new FormData();
        // Add all fields
        Object.keys(draftData).forEach(key => {
            if (key === 'attachments' && draftData[key]) {
                draftData[key].forEach((file, index) => {
                    formData.append(`attachment_${index}`, file);
                });
            }
            else if (draftData[key] !== undefined) {
                formData.append(key, draftData[key].toString());
            }
        });
        const response = await this.api.put(this.withPrefix(`/drafts/${draftId}`), formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    }
    async deleteDraft(draftId) {
        await this.api.delete(this.withPrefix(`/drafts/${draftId}`));
    }
    // Attachments
    async downloadAttachment(emailId, attachmentId) {
        const response = await this.api.get(this.withPrefix(`/emails/${emailId}/attachments/${attachmentId}`), {
            responseType: 'blob',
        });
        return response.data;
    }
    // Search
    async searchEmails(query, filters) {
        const response = await this.api.get(this.withPrefix('/emails/search'), {
            params: { q: query, ...filters },
        });
        return response.data;
    }
    // Real KM Status from Next Door Key Simulator
    async getKMStatus() {
        const response = await this.api.get(this.withPrefix('/km/status'));
        return response.data;
    }
    async getAvailableKeys() {
        const response = await this.api.get(this.withPrefix('/km/keys/available'));
        return response.data;
    }
    async requestTestKeys(numberOfKeys = 1) {
        const response = await this.api.post(this.withPrefix('/km/keys/request-test'), {
            number_of_keys: numberOfKeys
        });
        return response.data;
    }
    async testEncryption(level, message) {
        const response = await this.api.post(this.withPrefix('/encryption/test'), {
            level,
            message,
        });
        return response.data;
    }
    // Preferences
    async updatePreferences(preferences) {
        const response = await this.api.patch('/auth/preferences', preferences);
        return response.data;
    }
    // Notifications
    async getNotifications() {
        const response = await this.api.get(this.withPrefix('/notifications'));
        return response.data;
    }
    async markNotificationRead(notificationId) {
        await this.api.patch(this.withPrefix(`/notifications/${notificationId}/read`));
    }
    // Statistics
    async getEmailStats(period = 'week') {
        const response = await this.api.get(this.withPrefix('/stats/emails'), {
            params: { period },
        });
        return response.data;
    }
    // Authentication Helper Methods
    setAuthToken(token) {
        this.token = token;
    }
    clearAuthToken() {
        this.token = null;
    }
    async validateAuth() {
        // Reuse user profile endpoint; treat success as authenticated
        const profile = await this.getUserProfile();
        return { isAuthenticated: true, email: profile.email, name: profile.name };
    }
    async getGoogleAuthUrl() {
        try {
            const response = await this.api.get(this.withPrefix('/auth/google'));
            return { auth_url: response.data.authorization_url };
        }
        catch (error) {
            console.error('getGoogleAuthUrl error:', error);
            throw error;
        }
    }
    async handleOAuthCallback(code, state) {
        const response = await this.api.post(this.withPrefix('/auth/callback'), { code, state });
        return response.data;
    }
    // Email folders (for sidebar)
    async getEmailFolders() {
        const response = await this.api.get(this.withPrefix('/emails/folders'));
        return response.data;
    }
}
export const apiService = new ApiService();
export default apiService;
