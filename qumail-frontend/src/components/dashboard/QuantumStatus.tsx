import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';

const REFRESH_INTERVAL = 30000; // 30 seconds

interface KmeServer {
  name?: string;
  status?: string;
  keysAvailable?: number;
  latency?: number;
}

interface EncryptionStats {
  quantum_otp?: number;
  quantum_aes?: number;
  post_quantum?: number;
  standard_rsa?: number;
}

interface StatusData {
  systemStatus?: string;
  kmeStatus?: KmeServer[];
  quantumKeysAvailable?: number;
  entropyStatus?: string;
  averageEntropy?: number;
  encryptionStats?: EncryptionStats;
}

const QuantumStatus = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<StatusData | null>(null);
  const [kmeServers, setKmeServers] = useState<KmeServer[]>([]);
  const [systemStatus, setSystemStatus] = useState('unknown');
  const [quantumKeysAvailable, setQuantumKeysAvailable] = useState(0);
  const [entropyStatus, setEntropyStatus] = useState('unknown');
  
  // Function to fetch status data
  const fetchStatusData = async () => {
    try {
      setLoading(true);
      
      // Call the encryption/status endpoint
      const response = await axios.get('/encryption/status');
      const data = response.data;
      
      // Update state with the data
      setStatusData(data as StatusData);
      setKmeServers(data.kmeStatus || []);
      setSystemStatus(data.systemStatus || 'unknown');
      setQuantumKeysAvailable(data.quantumKeysAvailable || 0);
      setEntropyStatus(data.entropyStatus || 'unknown');
      setError(null);
      
    } catch (err) {
      console.error('Error fetching quantum status:', err as Error);
      setError('Failed to load quantum encryption status');
    } finally {
      setLoading(false);
    }
  };
  
  // Fetch data on component mount and set up interval
  useEffect(() => {
    fetchStatusData();
    
    // Set up interval to refresh data
    const intervalId = setInterval(fetchStatusData, REFRESH_INTERVAL);
    
    // Clean up interval on unmount
    return () => clearInterval(intervalId);
  }, []);
  
  // Get appropriate color for system status
  const getStatusColor = (status: string | undefined): string => {
    switch (status?.toLowerCase()) {
      case 'operational':
      case 'excellent':
      case 'connected':
      case 'online':
        return 'bg-green-500';
      case 'degraded':
      case 'warning':
      case 'good':
        return 'bg-yellow-500';
      case 'critical':
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  // Get appropriate icon for KME server status
  const getServerIcon = (status: string | undefined): string => {
    switch (status?.toLowerCase()) {
      case 'connected':
      case 'online':
        return '🟢';
      case 'degraded':
      case 'warning':
        return '🟡';
      case 'error':
      case 'offline':
      case 'critical':
        return '🔴';
      default:
        return '⚪';
    }
  };
  
  if (loading && !statusData) {
    return (
      <Card className="p-4 mb-4">
        <h2 className="text-lg font-semibold mb-2">Quantum Encryption Status</h2>
        <div className="text-gray-500">Loading quantum security status...</div>
      </Card>
    );
  }
  
  if (error) {
    return (
      <Card className="p-4 mb-4 border-red-300">
        <h2 className="text-lg font-semibold mb-2">Quantum Encryption Status</h2>
        <div className="text-red-500">{error}</div>
        <button 
          onClick={fetchStatusData}
          className="mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm"
        >
          Retry
        </button>
      </Card>
    );
  }
  
  return (
    <Card className="p-4 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Quantum Encryption Status</h2>
        <Badge className={getStatusColor(systemStatus)}>
          {systemStatus?.charAt(0).toUpperCase() + systemStatus?.slice(1) || 'Unknown'}
        </Badge>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-sm text-gray-500">Quantum Keys Available</div>
          <div className="text-xl font-semibold">{quantumKeysAvailable}</div>
        </div>
        
        <div>
          <div className="text-sm text-gray-500">Entropy Quality</div>
          <div className="flex items-center">
            <Badge className={getStatusColor(entropyStatus)} size="sm">
              {entropyStatus?.charAt(0).toUpperCase() + entropyStatus?.slice(1) || 'Unknown'}
            </Badge>
            {statusData?.averageEntropy && (
              <span className="ml-2 text-sm">
                ({statusData.averageEntropy!.toFixed(2)} bits/byte)
              </span>
            )}
          </div>
        </div>
      </div>
      
      <h3 className="font-semibold text-sm text-gray-700 mb-2">KME Servers</h3>
      <div className="space-y-2">
        {kmeServers.length === 0 ? (
          <div className="text-gray-500 text-sm">No KME servers detected</div>
        ) : (
          kmeServers.map((server, index) => (
            <div key={index} className="flex items-center justify-between text-sm border-b pb-2">
              <div className="flex items-center">
                <span className="mr-2">{getServerIcon(server.status)}</span>
                <span>{server.name || `KME Server ${index+1}`}</span>
              </div>
              <div className="flex items-center">
                {server.keysAvailable !== undefined && (
                  <span className="mr-3">{server.keysAvailable} keys</span>
                )}
                {server.latency && (
                  <span className="text-gray-500">{server.latency}ms</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
      
      {statusData?.encryptionStats && (
        <>
          <h3 className="font-semibold text-sm text-gray-700 my-2">Encryption Distribution</h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className="flex justify-between">
              <span>Quantum OTP:</span>
              <span className="font-medium">{statusData.encryptionStats.quantum_otp || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Quantum AES:</span>
              <span className="font-medium">{statusData.encryptionStats.quantum_aes || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Post-Quantum:</span>
              <span className="font-medium">{statusData.encryptionStats.post_quantum || 0}</span>
            </div>
            <div className="flex justify-between">
              <span>Standard RSA:</span>
              <span className="font-medium">{statusData.encryptionStats.standard_rsa || 0}</span>
            </div>
          </div>
        </>
      )}
      
      <div className="text-right mt-4">
        <button 
          onClick={fetchStatusData}
          className="px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-xs"
        >
          Refresh
        </button>
      </div>
    </Card>
  );
};

export default QuantumStatus;