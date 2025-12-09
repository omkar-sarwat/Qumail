import axios from 'axios';

// Configure base API URL - use localhost backend
const baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Types
export interface QuantumKey {
  id: string;
  kme: string;
  type: string;
  path: string;
}

export interface QuantumStatus {
  system_status: string;
  servers: Array<{
    id: number;
    name: string;
    status: string;
    available_keys: number;
    entropy: number;
    message?: string;
  }>;
  healthy_servers: number;
  total_servers: number;
  total_available_keys: number;
  average_entropy: number;
  qkd_clients: {
    kme1: {
      sae_id: number;
      kme_zone: string;
      status: string;
      stored_key_count: number;
      total_key_size: number;
      average_entropy: number;
      key_generation_rate: number;
      max_key_size: number;
      key_details: Array<{
        file: string;
        size: number;
        entropy: number;
      }>;
      timestamp: string;
    };
    kme2: {
      sae_id: number;
      kme_zone: string;
      status: string;
      stored_key_count: number;
      total_key_size: number;
      average_entropy: number;
      key_generation_rate: number;
      max_key_size: number;
      key_details: Array<{
        file: string;
        size: number;
        entropy: number;
      }>;
      timestamp: string;
    };
  };
}

export interface KeyExchangeResult {
  status: 'success' | 'error';
  key_id?: string;
  key_length?: number;
  error?: string;
  sender_kme_id?: number;
  recipient_kme_id?: number;
  timestamp: string;
}

export interface ConnectionTestResult {
  status: 'connected' | 'error';
  kme_id: number;
  sae_id?: number;
  stored_key_count?: number;
  total_entropy?: number;
  encryption_keys_available?: boolean;
  timestamp: string;
  error?: string;
}

class QuantumService {
  private getAuthHeaders() {
    const token = localStorage.getItem('authToken');
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  /**
   * Get quantum system status
   */
  async getQuantumStatus(): Promise<QuantumStatus> {
    try {
      const response = await axios.get(`${baseURL}/api/v1/quantum/status`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch quantum status:', error);
      throw error;
    }
  }

  /**
   * Get available quantum keys
   */
  async getAvailableKeys(): Promise<{ keys: QuantumKey[], count: number, available: boolean }> {
    try {
      const response = await axios.get(`${baseURL}/api/v1/quantum/keys/available`, {
        headers: this.getAuthHeaders()
      });
      return response.data;
    } catch (error) {
      console.error('Failed to fetch available quantum keys:', error);
      throw error;
    }
  }

  /**
   * Test connection to a KME server
   */
  async testConnection(kmeId: number = 1): Promise<ConnectionTestResult> {
    try {
      const response = await axios.post(
        `${baseURL}/api/v1/quantum/test/connection`,
        { kme_id: kmeId },
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error(`Failed to test connection to KME ${kmeId}:`, error);
      throw error;
    }
  }

  /**
   * Exchange quantum key between KME servers
   */
  async exchangeKey(
    senderKmeId: number = 1,
    recipientKmeId: number = 2
  ): Promise<KeyExchangeResult> {
    try {
      const response = await axios.post(
        `${baseURL}/api/v1/quantum/key/exchange`,
        {
          sender_kme_id: senderKmeId,
          recipient_kme_id: recipientKmeId
        },
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to exchange quantum key:', error);
      throw error;
    }
  }

  /**
   * Generate new quantum keys on KME servers
   */
  async generateKeys(count: number = 10, kmeIds: number[] = [1, 2]): Promise<any> {
    try {
      const response = await axios.post(
        `${baseURL}/api/v1/quantum/generate-keys`,
        {
          count: count,
          kme_ids: kmeIds
        },
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to generate quantum keys:', error);
      throw error;
    }
  }
}

export const quantumService = new QuantumService();
export default quantumService;