import axios from 'axios';
// Configure base API URL
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
class QuantumService {
    getAuthHeaders() {
        const token = localStorage.getItem('authToken');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }
    /**
     * Get quantum system status
     */
    async getQuantumStatus() {
        try {
            const response = await axios.get(`${baseURL}/api/v1/quantum/status`, {
                headers: this.getAuthHeaders()
            });
            return response.data;
        }
        catch (error) {
            console.error('Failed to fetch quantum status:', error);
            throw error;
        }
    }
    /**
     * Get available quantum keys
     */
    async getAvailableKeys() {
        try {
            const response = await axios.get(`${baseURL}/api/v1/quantum/keys/available`, {
                headers: this.getAuthHeaders()
            });
            return response.data;
        }
        catch (error) {
            console.error('Failed to fetch available quantum keys:', error);
            throw error;
        }
    }
    /**
     * Test connection to a KME server
     */
    async testConnection(kmeId = 1) {
        try {
            const response = await axios.post(`${baseURL}/api/v1/quantum/test/connection`, { kme_id: kmeId }, { headers: this.getAuthHeaders() });
            return response.data;
        }
        catch (error) {
            console.error(`Failed to test connection to KME ${kmeId}:`, error);
            throw error;
        }
    }
    /**
     * Exchange quantum key between KME servers
     */
    async exchangeKey(senderKmeId = 1, recipientKmeId = 2) {
        try {
            const response = await axios.post(`${baseURL}/api/v1/quantum/key/exchange`, {
                sender_kme_id: senderKmeId,
                recipient_kme_id: recipientKmeId
            }, { headers: this.getAuthHeaders() });
            return response.data;
        }
        catch (error) {
            console.error('Failed to exchange quantum key:', error);
            throw error;
        }
    }
    /**
     * Generate new quantum keys on KME servers
     */
    async generateKeys(count = 10, kmeIds = [1, 2]) {
        try {
            const response = await axios.post(`${baseURL}/api/v1/quantum/generate-keys`, {
                count: count,
                kme_ids: kmeIds
            }, { headers: this.getAuthHeaders() });
            return response.data;
        }
        catch (error) {
            console.error('Failed to generate quantum keys:', error);
            throw error;
        }
    }
}
export const quantumService = new QuantumService();
export default quantumService;
