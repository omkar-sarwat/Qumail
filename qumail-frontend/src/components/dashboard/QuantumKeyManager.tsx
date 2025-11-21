import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';

const QuantumKeyManager = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [keys, setKeys] = useState<Array<{ id: string, kme: string, type: string }>>([]);
  const [exchangeStatus, setExchangeStatus] = useState<{ status: string, message: string } | null>(null);

  // Function to fetch available quantum keys
  const fetchAvailableKeys = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/quantum/keys/available');
      setKeys(response.data.keys || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching quantum keys:', err);
      setError('Failed to load quantum keys');
    } finally {
      setLoading(false);
    }
  };

  // Function to exchange quantum keys
  const exchangeKeys = async () => {
    try {
      setLoading(true);
      setExchangeStatus({ status: 'pending', message: 'Exchanging quantum keys...' });
      
      // Exchange keys between KME1 and KME2
      const response = await axios.post('/api/v1/quantum/key/exchange', {
        sender_kme_id: 1,
        recipient_kme_id: 2
      });
      
      // Update status with the result
      setExchangeStatus({
        status: response.data.status === 'success' ? 'success' : 'error',
        message: response.data.status === 'success' 
          ? `Successfully exchanged key: ${response.data.key_id}`
          : `Exchange failed: ${response.data.error || 'Unknown error'}`
      });
      
      // Refresh available keys if exchange was successful
      if (response.data.status === 'success') {
        await fetchAvailableKeys();
      }
      
    } catch (err) {
      console.error('Error exchanging quantum keys:', err);
      setExchangeStatus({
        status: 'error',
        message: `Exchange failed: ${(err as any).response?.data?.detail || (err as Error).message || 'Unknown error'}`
      });
    } finally {
      setLoading(false);
    }
  };

  // Fetch available keys on component mount
  useEffect(() => {
    fetchAvailableKeys();
  }, []);

  // Status badge component
  const StatusBadge = ({ status }: { status: string }) => {
    const colors: Record<string, string> = {
      success: 'bg-green-100 text-green-800',
      error: 'bg-red-100 text-red-800',
      pending: 'bg-yellow-100 text-yellow-800'
    };
    
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
        {status.toUpperCase()}
      </span>
    );
  };

  return (
    <Card className="p-4 mb-4">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-lg font-semibold">Quantum Key Management</h2>
        <Button 
          onClick={fetchAvailableKeys} 
          disabled={loading}
          variant="outline"
          size="sm"
        >
          Refresh
        </Button>
      </div>
      
      {/* Key Exchange Section */}
      <div className="mb-6 p-3 bg-gray-50 rounded-md">
        <h3 className="font-medium mb-2">Exchange Quantum Keys</h3>
        <p className="text-sm text-gray-600 mb-3">
          Request new quantum keys to be exchanged between KME servers
        </p>
        
        <div className="flex items-center">
          <Button 
            onClick={exchangeKeys} 
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 text-white"
          >
            Exchange Keys
          </Button>
          
          {exchangeStatus && (
            <div className="ml-3 flex items-center">
              <StatusBadge status={exchangeStatus.status} />
              <span className="ml-2 text-sm">{exchangeStatus.message}</span>
            </div>
          )}
        </div>
      </div>
      
      {/* Available Keys Section */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h3 className="font-medium">Available Quantum Keys</h3>
          <span className="text-sm text-gray-500">
            {keys.length} {keys.length === 1 ? 'key' : 'keys'} available
          </span>
        </div>
        
        {error ? (
          <div className="text-red-500 text-sm">{error}</div>
        ) : loading && keys.length === 0 ? (
          <div className="text-gray-500 text-sm">Loading quantum keys...</div>
        ) : keys.length === 0 ? (
          <div className="text-gray-500 text-sm py-3">No quantum keys available</div>
        ) : (
          <div className="border rounded-md overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Key ID
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    KME Server
                  </th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {keys.map((key, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                      {key.id}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
                      {key.kme}
                    </td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-500">
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
  );
};

export default QuantumKeyManager;