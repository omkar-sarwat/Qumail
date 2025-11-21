import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
export const ComposeEmailModal = ({ isOpen, onClose, onSent, quantumKeysAvailable }) => {
    const [formData, setFormData] = useState({
        to: '',
        cc: '',
        bcc: '',
        subject: '',
        body: '',
        securityLevel: 'quantum-otp',
        priority: 'normal'
    });
    const [isSending, setIsSending] = useState(false);
    const securityLevels = [
        {
            id: 'quantum-otp',
            name: 'Quantum OTP (Level 1)',
            description: 'One-time pad encryption with quantum keys',
            color: 'text-purple-600',
            available: quantumKeysAvailable > 0
        },
        {
            id: 'quantum-aes',
            name: 'Quantum AES (Level 2)',
            description: 'AES encryption with quantum-generated keys',
            color: 'text-blue-600',
            available: quantumKeysAvailable > 0
        },
        {
            id: 'post-quantum',
            name: 'Post-Quantum (Level 3)',
            description: 'Kyber + Dilithium cryptography',
            color: 'text-green-600',
            available: true
        },
        {
            id: 'standard',
            name: 'Standard RSA (Level 4)',
            description: 'RSA-4096 with AES-256-GCM',
            color: 'text-gray-600',
            available: true
        }
    ];
    const handleInputChange = (field, value) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };
    const handleSend = async () => {
        if (!formData.to || !formData.subject || !formData.body) {
            alert('Please fill in all required fields');
            return;
        }
        setIsSending(true);
        try {
            const response = await fetch('http://localhost:8000/api/v1/emails/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({
                    to: formData.to.split(',').map(email => email.trim()),
                    cc: formData.cc ? formData.cc.split(',').map(email => email.trim()) : [],
                    bcc: formData.bcc ? formData.bcc.split(',').map(email => email.trim()) : [],
                    subject: formData.subject,
                    body: formData.body,
                    security_level: formData.securityLevel,
                    priority: formData.priority
                })
            });
            if (response.ok) {
                onSent();
                setFormData({
                    to: '',
                    cc: '',
                    bcc: '',
                    subject: '',
                    body: '',
                    securityLevel: 'quantum-otp',
                    priority: 'normal'
                });
            }
            else {
                const error = await response.json();
                alert(`Failed to send email: ${error.detail || 'Unknown error'}`);
            }
        }
        catch (error) {
            console.error('Failed to send email:', error);
            alert('Failed to send email. Please try again.');
        }
        finally {
            setIsSending(false);
        }
    };
    const selectedSecurity = securityLevels.find(level => level.id === formData.securityLevel);
    return (_jsx(AnimatePresence, { children: isOpen && (_jsx("div", { className: "fixed inset-0 z-50 overflow-y-auto", children: _jsxs("div", { className: "flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0", children: [_jsx(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, className: "fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity", onClick: onClose }), _jsxs(motion.div, { initial: { opacity: 0, scale: 0.95, y: 20 }, animate: { opacity: 1, scale: 1, y: 0 }, exit: { opacity: 0, scale: 0.95, y: 20 }, className: "relative inline-block w-full max-w-4xl mx-auto overflow-hidden text-left align-middle transition-all transform bg-white dark:bg-gray-800 shadow-xl rounded-2xl", children: [_jsxs("div", { className: "flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700", children: [_jsxs("h3", { className: "text-lg font-semibold text-gray-900 dark:text-white flex items-center", children: [_jsx("svg", { className: "w-5 h-5 mr-2 text-blue-600", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 19l9 2-9-18-9 18 9-2zm0 0v-8" }) }), "Compose Quantum Email"] }), _jsx("button", { onClick: onClose, className: "text-gray-400 hover:text-gray-600 dark:hover:text-gray-300", children: _jsx("svg", { className: "w-6 h-6", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) })] }), _jsx("div", { className: "px-6 py-4 max-h-96 overflow-y-auto", children: _jsxs("div", { className: "space-y-4", children: [_jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1", children: "To *" }), _jsx("input", { type: "email", value: formData.to, onChange: (e) => handleInputChange('to', e.target.value), placeholder: "recipient@example.com", className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500", required: true })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1", children: "CC" }), _jsx("input", { type: "email", value: formData.cc, onChange: (e) => handleInputChange('cc', e.target.value), placeholder: "cc@example.com", className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500" })] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1", children: "Subject *" }), _jsx("input", { type: "text", value: formData.subject, onChange: (e) => handleInputChange('subject', e.target.value), placeholder: "Email subject", className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500", required: true })] }), _jsxs("div", { className: "p-4 bg-gray-50 dark:bg-gray-700 rounded-lg", children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2", children: "Security Level" }), _jsx("select", { value: formData.securityLevel, onChange: (e) => handleInputChange('securityLevel', e.target.value), className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500", children: securityLevels.map((level) => (_jsxs("option", { value: level.id, disabled: !level.available, children: [level.name, " - ", level.description] }, level.id))) }), selectedSecurity && (_jsxs("div", { className: `mt-2 p-2 rounded-lg bg-opacity-10 ${selectedSecurity.color.replace('text-', 'bg-')}`, children: [_jsxs("div", { className: `flex items-center ${selectedSecurity.color}`, children: [_jsx("svg", { className: "w-4 h-4 mr-2", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) }), _jsx("span", { className: "text-sm font-medium", children: selectedSecurity.name })] }), _jsx("p", { className: "text-xs mt-1 opacity-80", children: selectedSecurity.description })] }))] }), _jsxs("div", { children: [_jsx("label", { className: "block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1", children: "Message *" }), _jsx("textarea", { value: formData.body, onChange: (e) => handleInputChange('body', e.target.value), placeholder: "Type your quantum-secured message...", rows: 10, className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none", required: true })] })] }) }), _jsxs("div", { className: "flex items-center justify-between px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750", children: [_jsxs("div", { className: "flex items-center text-sm text-gray-600 dark:text-gray-400", children: [_jsx("svg", { className: "w-4 h-4 mr-1", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" }) }), quantumKeysAvailable, " quantum keys available"] }), _jsxs("div", { className: "flex space-x-3", children: [_jsx(Button, { onClick: onClose, variant: "outline", disabled: isSending, children: "Cancel" }), _jsx(Button, { onClick: handleSend, disabled: isSending || !formData.to || !formData.subject || !formData.body, className: "bg-blue-600 hover:bg-blue-700 text-white", children: isSending ? (_jsxs("div", { className: "flex items-center", children: [_jsxs("svg", { className: "animate-spin -ml-1 mr-2 h-4 w-4 text-white", fill: "none", viewBox: "0 0 24 24", children: [_jsx("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4", className: "opacity-25" }), _jsx("path", { fill: "currentColor", className: "opacity-75", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })] }), "Sending..."] })) : (_jsxs("div", { className: "flex items-center", children: [_jsx("svg", { className: "w-4 h-4 mr-1", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 19l9 2-9-18-9 18 9-2zm0 0v-8" }) }), "Send Quantum Email"] })) })] })] })] })] }) })) }));
};
