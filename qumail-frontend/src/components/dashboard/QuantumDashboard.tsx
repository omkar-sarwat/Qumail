import { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { quantumService, QuantumStatus, QuantumKey, KeyExchangeResult } from '../../services/quantumService';

// Status indicator component
const StatusIndicator = ({ status }: { status: string }) => {
  const getStatusColor = () => {
    switch (status.toLowerCase()) {
      case 'operational':
      case 'connected':
      case 'success':
        return 'bg-green-500';
      case 'degraded':
      case 'warning':
      case 'partial':
        return 'bg-yellow-500';
      case 'critical':
      case 'error':
      case 'disconnected':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  return (
    <div className="flex items-center">
      <div className={`w-3 h-3 rounded-full ${getStatusColor()} mr-2`}></div>
      <span className="text-sm font-medium text-gray-900">{status}</span>
    </div>
  );
};

const QuantumDashboard = () => {
  const [systemStatus, setSystemStatus] = useState<QuantumStatus | null>(null);
  const [keys, setKeys] = useState<QuantumKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusLoading, setStatusLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exchangeResult, setExchangeResult] = useState<KeyExchangeResult | null>(null);
  const [isExchanging, setIsExchanging] = useState(false);

  // Fetch quantum system status
  const fetchStatus = async () => {
    try {
      setStatusLoading(true);
      const data = await quantumService.getQuantumStatus();
      setSystemStatus(data);
    } catch (err) {
      console.error('Error fetching quantum system status:', err);
    } finally {
      setStatusLoading(false);
    }
  };

  // Fetch available quantum keys
  const fetchKeys = async () => {
    try {
      setLoading(true);
      const data = await quantumService.getAvailableKeys();
      setKeys(data.keys || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching quantum keys:', err);
      setError('Failed to load quantum keys');
    } finally {
      setLoading(false);
    }
  };

  // Exchange quantum keys between KME servers
  const exchangeKeys = async () => {
    try {
      setIsExchanging(true);
      setExchangeResult(null);

      const result = await quantumService.exchangeKey();
      setExchangeResult(result);

      // If successful, refresh keys
      if (result.status === 'success') {
        await fetchKeys();
        await fetchStatus();
      }
    } catch (err) {
      console.error('Error exchanging keys:', err);
      setExchangeResult({
        status: 'error',
        error: 'Failed to exchange keys. Please try again.',
        timestamp: new Date().toISOString(),
      });
    } finally {
      setIsExchanging(false);
    }
  };

  // Test connection to KME servers
  const testKmeConnection = async (kmeId: number) => {
    try {
      await quantumService.testConnection(kmeId);
      await fetchStatus();
    } catch (err) {
      console.error(`Error testing KME${kmeId} connection:`, err);
    }
  };

  // Generate quantum keys
  const generateKeys = async (count: number = 10) => {
    try {
      setLoading(true);
      const result = await quantumService.generateKeys(count, [1, 2]);
      console.log('Key generation result:', result);
      await fetchKeys();
      await fetchStatus();
    } catch (err) {
      console.error('Error generating quantum keys:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchKeys();
  }, []);

  return (
    <div className="space-y-6">
      {/* System Status Card */}
      <Card className="p-5">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Quantum System Status</h2>
          <Button onClick={fetchStatus} disabled={statusLoading} size="sm">
            {statusLoading ? 'Refreshing...' : 'Refresh Status'}
          </Button>
        </div>

        {statusLoading ? (
          <div className="animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        ) : systemStatus ? (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="mb-2">
                  <span className="text-sm text-gray-600">System Status:</span>
                  <div className="mt-1">
                    <StatusIndicator status={systemStatus.system_status} />
                  </div>
                </div>
                <div className="mb-2">
                  <span className="text-sm text-gray-600">Available Keys:</span>
                  <div className="font-medium text-gray-900">{systemStatus.total_available_keys || 0}</div>
                </div>
                <div className="mb-2">
                  <span className="text-sm text-gray-600">Healthy Servers:</span>
                  <div className="font-medium text-gray-900">
                    {systemStatus.healthy_servers}/{systemStatus.total_servers}
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600">Average Entropy:</span>
                  <div className="font-medium text-gray-900">
                    {systemStatus.average_entropy?.toFixed(2) || 'N/A'}
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="mb-2">
                  <span className="text-sm text-gray-600">KME Server 1:</span>
                  <div className="mt-1 flex justify-between items-center">
                    <StatusIndicator status={systemStatus.qkd_clients?.kme1?.status || 'unknown'} />
                    <Button onClick={() => testKmeConnection(1)} size="sm" variant="outline">
                      Test Connection
                    </Button>
                  </div>
                </div>
                <div>
                  <span className="text-sm text-gray-600">KME Server 2:</span>
                  <div className="mt-1 flex justify-between items-center">
                    <StatusIndicator status={systemStatus.qkd_clients?.kme2?.status || 'unknown'} />
                    <Button onClick={() => testKmeConnection(2)} size="sm" variant="outline">
                      Test Connection
                    </Button>
                  </div>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                  Last Updated:{' '}
                  {systemStatus.qkd_clients?.kme1?.timestamp
                    ? new Date(systemStatus.qkd_clients.kme1.timestamp).toLocaleString()
                    : 'Never'}
                </div>
              </div>
            </div>

            {/* Detailed QKD Client Information */}
            {systemStatus && systemStatus.qkd_clients && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* KME1 Details */}
                <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
                  <h4 className="font-medium text-blue-800 mb-2">🔐 KME1 Quantum Details</h4>
                  <div className="space-y-1 text-sm text-blue-700">
                    <div>
                      Keys Stored:{' '}
                      <span className="font-medium text-blue-900">
                        {systemStatus.qkd_clients.kme1.stored_key_count}
                      </span>
                    </div>
                    <div>
                      Total Size:{' '}
                      <span className="font-medium text-blue-900">
                        {(systemStatus.qkd_clients.kme1.total_key_size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                    <div>
                      Entropy:{' '}
                      <span className="font-medium text-blue-900">
                        {systemStatus.qkd_clients.kme1.average_entropy.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      Generation Rate:{' '}
                      <span className="font-medium text-blue-900">
                        {systemStatus.qkd_clients.kme1.key_generation_rate} bits/s
                      </span>
                    </div>
                  </div>
                </div>

                {/* KME2 Details */}
                <div className="bg-green-50 p-3 rounded-lg border border-green-200">
                  <h4 className="font-medium text-green-800 mb-2">🔑 KME2 Quantum Details</h4>
                  <div className="space-y-1 text-sm text-green-700">
                    <div>
                      Keys Stored:{' '}
                      <span className="font-medium text-green-900">
                        {systemStatus.qkd_clients.kme2.stored_key_count}
                      </span>
                    </div>
                    <div>
                      Total Size:{' '}
                      <span className="font-medium text-green-900">
                        {(systemStatus.qkd_clients.kme2.total_key_size / 1024).toFixed(1)} KB
                      </span>
                    </div>
                    <div>
                      Entropy:{' '}
                      <span className="font-medium text-green-900">
                        {systemStatus.qkd_clients.kme2.average_entropy.toFixed(3)}
                      </span>
                    </div>
                    <div>
                      Generation Rate:{' '}
                      <span className="font-medium text-green-900">
                        {systemStatus.qkd_clients.kme2.key_generation_rate} bits/s
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="text-center py-4 text-gray-500">No system status available</div>
        )}
      </Card>

      {/* Key Management Card */}
      <Card className="p-5">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Quantum Key Management</h2>
          <Button onClick={fetchKeys} disabled={loading} size="sm">
            {loading ? 'Loading...' : 'Refresh Keys'}
          </Button>
        </div>

        {/* Key Generation and Exchange Section */}
        <div className="mb-6 space-y-4">
          {/* Key Generation */}
          <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
            <h3 className="text-md font-medium mb-2 text-purple-800">🔑 Generate Quantum Keys</h3>
            <p className="text-sm text-purple-700 mb-3">
              Generate new quantum keys on both KME servers. These keys are created using real quantum hardware.
            </p>

            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <Button
                onClick={() => generateKeys()}
                disabled={loading}
                className="bg-purple-600 hover:bg-purple-700 text-white"
              >
                {loading ? 'Generating...' : 'Generate 10 New Keys'}
              </Button>

              <span className="text-sm text-purple-600">
                Keys will be generated on both KME Server 1 and KME Server 2
              </span>
            </div>
          </div>

          {/* Key Exchange */}
          <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
            <h3 className="text-md font-medium mb-2 text-indigo-800">🔄 Quantum Key Exchange</h3>
            <p className="text-sm text-indigo-700 mb-3">
              Exchange quantum keys between KME Server 1 and KME Server 2 for secure email encryption.
            </p>

            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <Button
                onClick={exchangeKeys}
                disabled={isExchanging || statusLoading}
                className="bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                {isExchanging ? 'Exchanging...' : 'Exchange Keys'}
              </Button>

              {exchangeResult && (
                <div
                  className={`mt-2 sm:mt-0 px-3 py-2 rounded text-sm ${
                    exchangeResult.status === 'success'
                      ? 'bg-green-50 text-green-800'
                      : 'bg-red-50 text-red-800'
                  }`}
                >
                  {exchangeResult.status === 'success'
                    ? `✅ Successfully exchanged key: ${exchangeResult.key_id} (${exchangeResult.key_length} bytes)`
                    : `❌ Exchange failed: ${exchangeResult.error || 'Unknown error'}`}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Available Keys Section */}
        <div>
          <h3 className="text-md font-medium mb-2 text-gray-900">Available Quantum Keys</h3>

          {loading ? (
            <div className="animate-pulse space-y-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-8 bg-gray-100 rounded"></div>
              ))}
            </div>
          ) : error ? (
            <div className="text-center py-4">
              <span className="text-red-500">{error}</span>
            </div>
          ) : keys.length === 0 ? (
            <div className="text-center py-4">
              <span className="text-gray-500">No quantum keys available</span>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Key ID
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      KME Server
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {keys.map((key, index) => (
                    <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900">
                        {key.id}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                        {key.kme}
                      </td>
                      <td className="px-3 py-2 whitespace-nowrap text-sm text-gray-500">
                        {key.type}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default QuantumDashboard;
