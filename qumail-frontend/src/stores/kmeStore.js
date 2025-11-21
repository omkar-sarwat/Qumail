import { create } from 'zustand';
import { apiService } from '../services/api';
export const useKMEStore = create((set, get) => {
    let monitoringInterval = null;
    return {
        // Initial state
        kmeServers: [],
        quantumKeysAvailable: 0,
        encryptionStats: {
            quantum_otp: 0,
            quantum_aes: 0,
            post_quantum: 0,
            standard_rsa: 0,
        },
        isLoading: false,
        lastUpdate: undefined,
        error: null,
        overallStatus: 'critical',
        connectionQuality: 'offline',
        // Fetch KME status from Next Door Key Simulator
        fetchKMEStatus: async () => {
            try {
                set({ isLoading: true, error: null });
                // Fetch KME details plus encryption stats in parallel so the UI can show real data
                const kmStatusPromise = apiService.getKMStatus();
                const emailStatsPromise = apiService.getEmailStats('day').catch((err) => {
                    console.warn('Failed to fetch encryption statistics:', err);
                    return null;
                });
                const [kmStatusData, emailStats] = await Promise.all([kmStatusPromise, emailStatsPromise]);
                // Transform real KM data to our store format
                const kmeServers = [
                    {
                        id: 'kme1',
                        name: 'Next Door KME 1',
                        status: kmStatusData.kme_servers.kme1.status === 'online' ? 'connected' : 'disconnected',
                        url: kmStatusData.kme_servers.kme1.url,
                        latency: undefined, // Real latency will be measured during connection tests
                        lastCheck: new Date(kmStatusData.kme_servers.kme1.last_check),
                        keysAvailable: kmStatusData.kme_servers.kme1.available_keys,
                        keysUsed: 0, // KME doesn't track used keys directly
                        errorMessage: kmStatusData.kme_servers.kme1.error,
                    },
                    {
                        id: 'kme2',
                        name: 'Next Door KME 2',
                        status: kmStatusData.kme_servers.kme2.status === 'online' ? 'connected' : 'disconnected',
                        url: kmStatusData.kme_servers.kme2.url,
                        latency: undefined, // Real latency will be measured during connection tests
                        lastCheck: new Date(kmStatusData.kme_servers.kme2.last_check),
                        keysAvailable: kmStatusData.kme_servers.kme2.available_keys,
                        keysUsed: 0, // KME doesn't track used keys directly
                        errorMessage: kmStatusData.kme_servers.kme2.error,
                    }
                ];
                // Map system health to our status types
                let overallStatus;
                let connectionQuality;
                switch (kmStatusData.summary.system_health) {
                    case 'healthy':
                        overallStatus = 'healthy';
                        connectionQuality = 'excellent';
                        break;
                    case 'degraded':
                        overallStatus = 'degraded';
                        connectionQuality = 'good';
                        break;
                    case 'offline':
                    default:
                        overallStatus = 'critical';
                        connectionQuality = 'offline';
                        break;
                }
                // Try to use real encryption statistics when available
                const encryptionStats = emailStats?.encryptionBreakdown ?? {
                    quantum_otp: 0,
                    quantum_aes: 0,
                    post_quantum: 0,
                    standard_rsa: 0,
                };
                set({
                    kmeServers,
                    quantumKeysAvailable: kmStatusData.summary.total_available_keys,
                    encryptionStats,
                    isLoading: false,
                    lastUpdate: new Date(kmStatusData.timestamp),
                    overallStatus,
                    connectionQuality,
                });
            }
            catch (error) {
                console.error('Failed to fetch KME status from Next Door Key Simulator:', error);
                const errorMessage = error.response?.data?.detail || 'Failed to fetch KME status from Next Door Key Simulator';
                set({
                    error: errorMessage,
                    isLoading: false,
                    overallStatus: 'critical',
                    connectionQuality: 'offline',
                });
            }
        },
        // Fetch detailed quantum key information
        fetchAvailableKeys: async () => {
            try {
                const keysData = await apiService.getAvailableKeys();
                // Update KME servers with latest key counts
                const currentState = get();
                const updatedServers = currentState.kmeServers.map(server => {
                    const kmeData = keysData.kme_keys[server.id];
                    if (kmeData) {
                        return {
                            ...server,
                            keysAvailable: kmeData.available_keys,
                            lastCheck: new Date(),
                        };
                    }
                    return server;
                });
                // Calculate total available keys
                const totalKeys = Object.values(keysData.kme_keys).reduce((sum, kme) => sum + kme.available_keys, 0);
                set({
                    kmeServers: updatedServers,
                    quantumKeysAvailable: totalKeys,
                    lastUpdate: new Date(keysData.timestamp),
                });
            }
            catch (error) {
                console.error('Failed to fetch available quantum keys:', error);
            }
        },
        // Test key request functionality
        requestTestKeys: async (count = 10) => {
            try {
                const result = await apiService.requestTestKeys(count);
                // Show success notification or update UI
                console.log(`Test key request successful: Requested ${result.requested_keys}, received ${result.received_keys}`);
                // Refresh the key counts after test request
                const state = get();
                await state.fetchAvailableKeys();
                return result;
            }
            catch (error) {
                console.error('Failed to request test keys:', error);
                throw error;
            }
        },
        // Test individual KME connection
        testKMEConnection: async (kmeId) => {
            try {
                // Update server status to testing
                set(state => ({
                    kmeServers: state.kmeServers.map(server => server.id === kmeId
                        ? { ...server, status: 'connected', lastCheck: new Date() }
                        : server),
                }));
                // Perform real connection test by fetching KM status
                const startTime = Date.now();
                try {
                    const kmStatus = await apiService.getKMStatus();
                    const endTime = Date.now();
                    const latency = endTime - startTime;
                    // Check if the specific KME is online
                    const kmeData = kmeId === 'kme1' ? kmStatus.kme_servers.kme1 : kmStatus.kme_servers.kme2;
                    const isConnected = kmeData.status === 'online';
                    set(state => ({
                        kmeServers: state.kmeServers.map(server => server.id === kmeId
                            ? {
                                ...server,
                                status: isConnected ? 'connected' : 'disconnected',
                                latency: isConnected ? latency : undefined,
                                lastCheck: new Date(),
                                errorMessage: isConnected ? undefined : kmeData.error || 'Connection failed',
                                keysAvailable: kmeData.available_keys
                            }
                            : server),
                    }));
                    return isConnected;
                }
                catch (error) {
                    set(state => ({
                        kmeServers: state.kmeServers.map(server => server.id === kmeId
                            ? {
                                ...server,
                                status: 'error',
                                latency: undefined,
                                lastCheck: new Date(),
                                errorMessage: error.message || 'Connection test failed',
                            }
                            : server),
                    }));
                    return false;
                }
            }
            catch (error) {
                console.error(`Failed to test KME ${kmeId}:`, error);
                set(state => ({
                    kmeServers: state.kmeServers.map(server => server.id === kmeId
                        ? {
                            ...server,
                            status: 'error',
                            lastCheck: new Date(),
                            errorMessage: 'Test failed',
                        }
                        : server),
                }));
                return false;
            }
        },
        // Refresh status - fetch both KM status and available keys
        refreshStatus: async () => {
            const state = get();
            await Promise.all([
                state.fetchKMEStatus(),
                state.fetchAvailableKeys()
            ]);
        },
        // Start monitoring (poll every 30 seconds)
        startMonitoring: () => {
            if (monitoringInterval) {
                clearInterval(monitoringInterval);
            }
            // Initial fetch
            const state = get();
            state.refreshStatus();
            // Set up periodic updates
            monitoringInterval = setInterval(() => {
                const state = get();
                state.refreshStatus();
            }, 30000); // 30 seconds
        },
        // Stop monitoring
        stopMonitoring: () => {
            if (monitoringInterval) {
                clearInterval(monitoringInterval);
                monitoringInterval = null;
            }
        },
        // Clear error
        clearError: () => {
            set({ error: null });
        },
    };
});
