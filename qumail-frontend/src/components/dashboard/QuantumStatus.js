import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '../ui/Card';
import { Badge } from '../ui/Badge';
const REFRESH_INTERVAL = 30000; // 30 seconds
const QuantumStatus = () => {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [statusData, setStatusData] = useState(null);
    const [kmeServers, setKmeServers] = useState([]);
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
            setStatusData(data);
            setKmeServers(data.kmeStatus || []);
            setSystemStatus(data.systemStatus || 'unknown');
            setQuantumKeysAvailable(data.quantumKeysAvailable || 0);
            setEntropyStatus(data.entropyStatus || 'unknown');
            setError(null);
        }
        catch (err) {
            console.error('Error fetching quantum status:', err);
            setError('Failed to load quantum encryption status');
        }
        finally {
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
    const getStatusColor = (status) => {
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
    const getServerIcon = (status) => {
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
        return (_jsxs(Card, { className: "p-4 mb-4", children: [_jsx("h2", { className: "text-lg font-semibold mb-2", children: "Quantum Encryption Status" }), _jsx("div", { className: "text-gray-500", children: "Loading quantum security status..." })] }));
    }
    if (error) {
        return (_jsxs(Card, { className: "p-4 mb-4 border-red-300", children: [_jsx("h2", { className: "text-lg font-semibold mb-2", children: "Quantum Encryption Status" }), _jsx("div", { className: "text-red-500", children: error }), _jsx("button", { onClick: fetchStatusData, className: "mt-2 px-3 py-1 bg-blue-500 text-white rounded text-sm", children: "Retry" })] }));
    }
    return (_jsxs(Card, { className: "p-4 mb-4", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-lg font-semibold", children: "Quantum Encryption Status" }), _jsx(Badge, { className: getStatusColor(systemStatus), children: systemStatus?.charAt(0).toUpperCase() + systemStatus?.slice(1) || 'Unknown' })] }), _jsxs("div", { className: "grid grid-cols-2 gap-4 mb-4", children: [_jsxs("div", { children: [_jsx("div", { className: "text-sm text-gray-500", children: "Quantum Keys Available" }), _jsx("div", { className: "text-xl font-semibold", children: quantumKeysAvailable })] }), _jsxs("div", { children: [_jsx("div", { className: "text-sm text-gray-500", children: "Entropy Quality" }), _jsxs("div", { className: "flex items-center", children: [_jsx(Badge, { className: getStatusColor(entropyStatus), size: "sm", children: entropyStatus?.charAt(0).toUpperCase() + entropyStatus?.slice(1) || 'Unknown' }), statusData?.averageEntropy && (_jsxs("span", { className: "ml-2 text-sm", children: ["(", statusData.averageEntropy.toFixed(2), " bits/byte)"] }))] })] })] }), _jsx("h3", { className: "font-semibold text-sm text-gray-700 mb-2", children: "KME Servers" }), _jsx("div", { className: "space-y-2", children: kmeServers.length === 0 ? (_jsx("div", { className: "text-gray-500 text-sm", children: "No KME servers detected" })) : (kmeServers.map((server, index) => (_jsxs("div", { className: "flex items-center justify-between text-sm border-b pb-2", children: [_jsxs("div", { className: "flex items-center", children: [_jsx("span", { className: "mr-2", children: getServerIcon(server.status) }), _jsx("span", { children: server.name || `KME Server ${index + 1}` })] }), _jsxs("div", { className: "flex items-center", children: [server.keysAvailable !== undefined && (_jsxs("span", { className: "mr-3", children: [server.keysAvailable, " keys"] })), server.latency && (_jsxs("span", { className: "text-gray-500", children: [server.latency, "ms"] }))] })] }, index)))) }), statusData?.encryptionStats && (_jsxs(_Fragment, { children: [_jsx("h3", { className: "font-semibold text-sm text-gray-700 my-2", children: "Encryption Distribution" }), _jsxs("div", { className: "grid grid-cols-2 gap-2 text-sm", children: [_jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: "Quantum OTP:" }), _jsx("span", { className: "font-medium", children: statusData.encryptionStats.quantum_otp || 0 })] }), _jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: "Quantum AES:" }), _jsx("span", { className: "font-medium", children: statusData.encryptionStats.quantum_aes || 0 })] }), _jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: "Post-Quantum:" }), _jsx("span", { className: "font-medium", children: statusData.encryptionStats.post_quantum || 0 })] }), _jsxs("div", { className: "flex justify-between", children: [_jsx("span", { children: "Standard RSA:" }), _jsx("span", { className: "font-medium", children: statusData.encryptionStats.standard_rsa || 0 })] })] })] })), _jsx("div", { className: "text-right mt-4", children: _jsx("button", { onClick: fetchStatusData, className: "px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-xs", children: "Refresh" }) })] }));
};
export default QuantumStatus;
