import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { quantumService } from '../../services/quantumService';
// Status indicator component
const StatusIndicator = ({ status }) => {
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
    return (_jsxs("div", { className: "flex items-center", children: [_jsx("div", { className: `w-3 h-3 rounded-full ${getStatusColor()} mr-2` }), _jsx("span", { className: "text-sm font-medium text-gray-900", children: status })] }));
};
const QuantumDashboard = () => {
    const [systemStatus, setSystemStatus] = useState(null);
    const [keys, setKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [statusLoading, setStatusLoading] = useState(true);
    const [error, setError] = useState(null);
    const [exchangeResult, setExchangeResult] = useState(null);
    const [isExchanging, setIsExchanging] = useState(false);
    // Fetch quantum system status
    const fetchStatus = async () => {
        try {
            setStatusLoading(true);
            const data = await quantumService.getQuantumStatus();
            setSystemStatus(data);
        }
        catch (err) {
            console.error('Error fetching quantum system status:', err);
        }
        finally {
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
        }
        catch (err) {
            console.error('Error fetching quantum keys:', err);
            setError('Failed to load quantum keys');
        }
        finally {
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
        }
        catch (err) {
            console.error('Error exchanging keys:', err);
            setExchangeResult({
                status: 'error',
                error: 'Failed to exchange keys. Please try again.',
                timestamp: new Date().toISOString(),
            });
        }
        finally {
            setIsExchanging(false);
        }
    };
    // Test connection to KME servers
    const testKmeConnection = async (kmeId) => {
        try {
            await quantumService.testConnection(kmeId);
            await fetchStatus();
        }
        catch (err) {
            console.error(`Error testing KME${kmeId} connection:`, err);
        }
    };
    // Generate quantum keys
    const generateKeys = async (count = 10) => {
        try {
            setLoading(true);
            const result = await quantumService.generateKeys(count, [1, 2]);
            console.log('Key generation result:', result);
            await fetchKeys();
            await fetchStatus();
        }
        catch (err) {
            console.error('Error generating quantum keys:', err);
        }
        finally {
            setLoading(false);
        }
    };
    useEffect(() => {
        fetchStatus();
        fetchKeys();
    }, []);
    return (_jsxs("div", { className: "space-y-6", children: [_jsxs(Card, { className: "p-5", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-lg font-semibold text-gray-900", children: "Quantum System Status" }), _jsx(Button, { onClick: fetchStatus, disabled: statusLoading, size: "sm", children: statusLoading ? 'Refreshing...' : 'Refresh Status' })] }), statusLoading ? (_jsxs("div", { className: "animate-pulse", children: [_jsx("div", { className: "h-4 bg-gray-200 rounded w-3/4 mb-2" }), _jsx("div", { className: "h-4 bg-gray-200 rounded w-1/2 mb-2" }), _jsx("div", { className: "h-4 bg-gray-200 rounded w-5/6" })] })) : systemStatus ? (_jsxs(_Fragment, { children: [_jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-4", children: [_jsxs("div", { className: "bg-gray-50 p-3 rounded-lg", children: [_jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "text-sm text-gray-600", children: "System Status:" }), _jsx("div", { className: "mt-1", children: _jsx(StatusIndicator, { status: systemStatus.system_status }) })] }), _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "text-sm text-gray-600", children: "Available Keys:" }), _jsx("div", { className: "font-medium text-gray-900", children: systemStatus.total_available_keys || 0 })] }), _jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "text-sm text-gray-600", children: "Healthy Servers:" }), _jsxs("div", { className: "font-medium text-gray-900", children: [systemStatus.healthy_servers, "/", systemStatus.total_servers] })] }), _jsxs("div", { children: [_jsx("span", { className: "text-sm text-gray-600", children: "Average Entropy:" }), _jsx("div", { className: "font-medium text-gray-900", children: systemStatus.average_entropy?.toFixed(2) || 'N/A' })] })] }), _jsxs("div", { className: "bg-gray-50 p-3 rounded-lg", children: [_jsxs("div", { className: "mb-2", children: [_jsx("span", { className: "text-sm text-gray-600", children: "KME Server 1:" }), _jsxs("div", { className: "mt-1 flex justify-between items-center", children: [_jsx(StatusIndicator, { status: systemStatus.qkd_clients?.kme1?.status || 'unknown' }), _jsx(Button, { onClick: () => testKmeConnection(1), size: "sm", variant: "outline", children: "Test Connection" })] })] }), _jsxs("div", { children: [_jsx("span", { className: "text-sm text-gray-600", children: "KME Server 2:" }), _jsxs("div", { className: "mt-1 flex justify-between items-center", children: [_jsx(StatusIndicator, { status: systemStatus.qkd_clients?.kme2?.status || 'unknown' }), _jsx(Button, { onClick: () => testKmeConnection(2), size: "sm", variant: "outline", children: "Test Connection" })] })] }), _jsxs("div", { className: "mt-2 text-xs text-gray-500", children: ["Last Updated:", ' ', systemStatus.qkd_clients?.kme1?.timestamp
                                                        ? new Date(systemStatus.qkd_clients.kme1.timestamp).toLocaleString()
                                                        : 'Never'] })] })] }), systemStatus && systemStatus.qkd_clients && (_jsxs("div", { className: "mt-4 grid grid-cols-1 md:grid-cols-2 gap-4", children: [_jsxs("div", { className: "bg-blue-50 p-3 rounded-lg border border-blue-200", children: [_jsx("h4", { className: "font-medium text-blue-800 mb-2", children: "\uD83D\uDD10 KME1 Quantum Details" }), _jsxs("div", { className: "space-y-1 text-sm text-blue-700", children: [_jsxs("div", { children: ["Keys Stored:", ' ', _jsx("span", { className: "font-medium text-blue-900", children: systemStatus.qkd_clients.kme1.stored_key_count })] }), _jsxs("div", { children: ["Total Size:", ' ', _jsxs("span", { className: "font-medium text-blue-900", children: [(systemStatus.qkd_clients.kme1.total_key_size / 1024).toFixed(1), " KB"] })] }), _jsxs("div", { children: ["Entropy:", ' ', _jsx("span", { className: "font-medium text-blue-900", children: systemStatus.qkd_clients.kme1.average_entropy.toFixed(3) })] }), _jsxs("div", { children: ["Generation Rate:", ' ', _jsxs("span", { className: "font-medium text-blue-900", children: [systemStatus.qkd_clients.kme1.key_generation_rate, " bits/s"] })] })] })] }), _jsxs("div", { className: "bg-green-50 p-3 rounded-lg border border-green-200", children: [_jsx("h4", { className: "font-medium text-green-800 mb-2", children: "\uD83D\uDD11 KME2 Quantum Details" }), _jsxs("div", { className: "space-y-1 text-sm text-green-700", children: [_jsxs("div", { children: ["Keys Stored:", ' ', _jsx("span", { className: "font-medium text-green-900", children: systemStatus.qkd_clients.kme2.stored_key_count })] }), _jsxs("div", { children: ["Total Size:", ' ', _jsxs("span", { className: "font-medium text-green-900", children: [(systemStatus.qkd_clients.kme2.total_key_size / 1024).toFixed(1), " KB"] })] }), _jsxs("div", { children: ["Entropy:", ' ', _jsx("span", { className: "font-medium text-green-900", children: systemStatus.qkd_clients.kme2.average_entropy.toFixed(3) })] }), _jsxs("div", { children: ["Generation Rate:", ' ', _jsxs("span", { className: "font-medium text-green-900", children: [systemStatus.qkd_clients.kme2.key_generation_rate, " bits/s"] })] })] })] })] }))] })) : (_jsx("div", { className: "text-center py-4 text-gray-500", children: "No system status available" }))] }), _jsxs(Card, { className: "p-5", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-lg font-semibold text-gray-900", children: "Quantum Key Management" }), _jsx(Button, { onClick: fetchKeys, disabled: loading, size: "sm", children: loading ? 'Loading...' : 'Refresh Keys' })] }), _jsxs("div", { className: "mb-6 space-y-4", children: [_jsxs("div", { className: "bg-purple-50 p-4 rounded-lg border border-purple-200", children: [_jsx("h3", { className: "text-md font-medium mb-2 text-purple-800", children: "\uD83D\uDD11 Generate Quantum Keys" }), _jsx("p", { className: "text-sm text-purple-700 mb-3", children: "Generate new quantum keys on both KME servers. These keys are created using real quantum hardware." }), _jsxs("div", { className: "flex flex-col sm:flex-row sm:items-center gap-3", children: [_jsx(Button, { onClick: () => generateKeys(), disabled: loading, className: "bg-purple-600 hover:bg-purple-700 text-white", children: loading ? 'Generating...' : 'Generate 10 New Keys' }), _jsx("span", { className: "text-sm text-purple-600", children: "Keys will be generated on both KME Server 1 and KME Server 2" })] })] }), _jsxs("div", { className: "bg-indigo-50 p-4 rounded-lg border border-indigo-200", children: [_jsx("h3", { className: "text-md font-medium mb-2 text-indigo-800", children: "\uD83D\uDD04 Quantum Key Exchange" }), _jsx("p", { className: "text-sm text-indigo-700 mb-3", children: "Exchange quantum keys between KME Server 1 and KME Server 2 for secure email encryption." }), _jsxs("div", { className: "flex flex-col sm:flex-row sm:items-center gap-3", children: [_jsx(Button, { onClick: exchangeKeys, disabled: isExchanging || statusLoading, className: "bg-indigo-600 hover:bg-indigo-700 text-white", children: isExchanging ? 'Exchanging...' : 'Exchange Keys' }), exchangeResult && (_jsx("div", { className: `mt-2 sm:mt-0 px-3 py-2 rounded text-sm ${exchangeResult.status === 'success'
                                                    ? 'bg-green-50 text-green-800'
                                                    : 'bg-red-50 text-red-800'}`, children: exchangeResult.status === 'success'
                                                    ? `✅ Successfully exchanged key: ${exchangeResult.key_id} (${exchangeResult.key_length} bytes)`
                                                    : `❌ Exchange failed: ${exchangeResult.error || 'Unknown error'}` }))] })] })] }), _jsxs("div", { children: [_jsx("h3", { className: "text-md font-medium mb-2 text-gray-900", children: "Available Quantum Keys" }), loading ? (_jsx("div", { className: "animate-pulse space-y-2", children: [1, 2, 3].map((i) => (_jsx("div", { className: "h-8 bg-gray-100 rounded" }, i))) })) : error ? (_jsx("div", { className: "text-center py-4", children: _jsx("span", { className: "text-red-500", children: error }) })) : keys.length === 0 ? (_jsx("div", { className: "text-center py-4", children: _jsx("span", { className: "text-gray-500", children: "No quantum keys available" }) })) : (_jsx("div", { className: "overflow-x-auto", children: _jsxs("table", { className: "min-w-full divide-y divide-gray-200", children: [_jsx("thead", { className: "bg-gray-50", children: _jsxs("tr", { children: [_jsx("th", { className: "px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "Key ID" }), _jsx("th", { className: "px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "KME Server" }), _jsx("th", { className: "px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "Type" })] }) }), _jsx("tbody", { className: "bg-white divide-y divide-gray-200", children: keys.map((key, index) => (_jsxs("tr", { className: index % 2 === 0 ? 'bg-white' : 'bg-gray-50', children: [_jsx("td", { className: "px-3 py-2 whitespace-nowrap text-sm font-medium text-gray-900", children: key.id }), _jsx("td", { className: "px-3 py-2 whitespace-nowrap text-sm text-gray-500", children: key.kme }), _jsx("td", { className: "px-3 py-2 whitespace-nowrap text-sm text-gray-500", children: key.type })] }, index))) })] }) }))] })] })] }));
};
export default QuantumDashboard;
