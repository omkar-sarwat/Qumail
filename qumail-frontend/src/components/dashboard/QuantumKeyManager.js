import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import axios from 'axios';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
const QuantumKeyManager = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [keys, setKeys] = useState([]);
    const [exchangeStatus, setExchangeStatus] = useState(null);
    // Function to fetch available quantum keys
    const fetchAvailableKeys = async () => {
        try {
            setLoading(true);
            const response = await axios.get('/api/v1/quantum/keys/available');
            setKeys(response.data.keys || []);
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
        }
        catch (err) {
            console.error('Error exchanging quantum keys:', err);
            setExchangeStatus({
                status: 'error',
                message: `Exchange failed: ${err.response?.data?.detail || err.message || 'Unknown error'}`
            });
        }
        finally {
            setLoading(false);
        }
    };
    // Fetch available keys on component mount
    useEffect(() => {
        fetchAvailableKeys();
    }, []);
    // Status badge component
    const StatusBadge = ({ status }) => {
        const colors = {
            success: 'bg-green-100 text-green-800',
            error: 'bg-red-100 text-red-800',
            pending: 'bg-yellow-100 text-yellow-800'
        };
        return (_jsx("span", { className: `px-2 py-1 rounded text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`, children: status.toUpperCase() }));
    };
    return (_jsxs(Card, { className: "p-4 mb-4", children: [_jsxs("div", { className: "flex justify-between items-center mb-4", children: [_jsx("h2", { className: "text-lg font-semibold", children: "Quantum Key Management" }), _jsx(Button, { onClick: fetchAvailableKeys, disabled: loading, variant: "outline", size: "sm", children: "Refresh" })] }), _jsxs("div", { className: "mb-6 p-3 bg-gray-50 rounded-md", children: [_jsx("h3", { className: "font-medium mb-2", children: "Exchange Quantum Keys" }), _jsx("p", { className: "text-sm text-gray-600 mb-3", children: "Request new quantum keys to be exchanged between KME servers" }), _jsxs("div", { className: "flex items-center", children: [_jsx(Button, { onClick: exchangeKeys, disabled: loading, className: "bg-blue-600 hover:bg-blue-700 text-white", children: "Exchange Keys" }), exchangeStatus && (_jsxs("div", { className: "ml-3 flex items-center", children: [_jsx(StatusBadge, { status: exchangeStatus.status }), _jsx("span", { className: "ml-2 text-sm", children: exchangeStatus.message })] }))] })] }), _jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-center mb-2", children: [_jsx("h3", { className: "font-medium", children: "Available Quantum Keys" }), _jsxs("span", { className: "text-sm text-gray-500", children: [keys.length, " ", keys.length === 1 ? 'key' : 'keys', " available"] })] }), error ? (_jsx("div", { className: "text-red-500 text-sm", children: error })) : loading && keys.length === 0 ? (_jsx("div", { className: "text-gray-500 text-sm", children: "Loading quantum keys..." })) : keys.length === 0 ? (_jsx("div", { className: "text-gray-500 text-sm py-3", children: "No quantum keys available" })) : (_jsx("div", { className: "border rounded-md overflow-hidden", children: _jsxs("table", { className: "min-w-full divide-y divide-gray-200", children: [_jsx("thead", { className: "bg-gray-50", children: _jsxs("tr", { children: [_jsx("th", { className: "px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "Key ID" }), _jsx("th", { className: "px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "KME Server" }), _jsx("th", { className: "px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider", children: "Type" })] }) }), _jsx("tbody", { className: "bg-white divide-y divide-gray-200", children: keys.map((key, index) => (_jsxs("tr", { className: "hover:bg-gray-50", children: [_jsx("td", { className: "px-4 py-2 whitespace-nowrap text-sm text-gray-900", children: key.id }), _jsx("td", { className: "px-4 py-2 whitespace-nowrap text-sm text-gray-500", children: key.kme }), _jsx("td", { className: "px-4 py-2 whitespace-nowrap text-sm text-gray-500", children: key.type })] }, index))) })] }) }))] })] }));
};
export default QuantumKeyManager;
