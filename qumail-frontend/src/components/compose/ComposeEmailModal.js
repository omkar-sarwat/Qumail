import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import { Button } from '../ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
export const ComposeEmailModal = ({ isOpen, onClose, onSend, replyTo }) => {
    const [to, setTo] = useState('');
    const [cc, setCc] = useState('');
    const [bcc, setBcc] = useState('');
    const [subject, setSubject] = useState('');
    const [body, setBody] = useState('');
    const [securityLevel, setSecurityLevel] = useState(1);
    const [showCcBcc, setShowCcBcc] = useState(false);
    const [attachments, setAttachments] = useState([]);
    const [isSending, setIsSending] = useState(false);
    const [showContacts, setShowContacts] = useState(false);
    const [encryptionStatus, setEncryptionStatus] = useState('');
    const fileInputRef = useRef(null);
    const bodyRef = useRef(null);
    // Sample contacts for autocomplete
    const contacts = [
        { email: 'alice@example.com', name: 'Alice Johnson' },
        { email: 'bob@company.com', name: 'Bob Smith' },
        { email: 'carol@organization.org', name: 'Carol Williams' },
        { email: 'david@startup.io', name: 'David Brown' }
    ];
    useEffect(() => {
        if (replyTo) {
            // Handle optional fields safely - use new sender fields
            const senderEmail = replyTo.sender_email || replyTo.from_email || replyTo.from || '';
            setTo(senderEmail);
            // Handle subject safely
            const subjectText = replyTo.subject || '(No Subject)';
            setSubject(subjectText.startsWith('Re: ') ? subjectText : `Re: ${subjectText}`);
            // Format sender name for reply - try different fields
            const senderName = replyTo.sender_name || replyTo.from_name ||
                (replyTo.from && replyTo.from.includes('<') ?
                    replyTo.from.split('<')[0].trim().replace(/"/g, '') :
                    replyTo.from?.split('@')[0]) || 'Unknown Sender';
            // Get body content from available fields
            const bodyContent = replyTo.html_body || replyTo.body || replyTo.plain_body || '(No content)';
            // Create reply message body with safe fallbacks
            setBody(`\n\n--- Original Message ---\nFrom: ${senderName} <${senderEmail}>\nSubject: ${replyTo.subject || '(No Subject)'}\nDate: ${new Date(replyTo.timestamp).toLocaleString()}\n\n${bodyContent}`);
            // Default to security level 1 if undefined
            setSecurityLevel(replyTo.securityLevel || 1);
        }
        else {
            // Clear form for new email composition
            resetForm();
        }
    }, [replyTo]);
    useEffect(() => {
        if (isOpen && bodyRef.current) {
            bodyRef.current.focus();
        }
    }, [isOpen]);
    const parseRecipientList = (value) => value
        .split(',')
        .map((entry) => entry.trim())
        .filter((entry) => entry.length > 0);
    const handleSend = async () => {
        if (!to || !subject || !body) {
            toast.error('Please fill in To, Subject, and Body before sending.');
            return;
        }
        const token = localStorage.getItem('authToken');
        if (!token) {
            toast.error('Authentication required. Please sign in again.');
            return;
        }
        setIsSending(true);
        let finalSecurityLevel = securityLevel;
        try {
            if (finalSecurityLevel === 1) {
                setEncryptionStatus('Checking quantum key availability...');
                try {
                    const keysResponse = await fetch('http://localhost:8000/api/v1/quantum/keys/available', {
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    });
                    if (keysResponse.ok) {
                        const keysData = await keysResponse.json();
                        if (!keysData.available || keysData.count === 0) {
                            setEncryptionStatus('No quantum keys available. Generating new keys...');
                            const exchangeResponse = await fetch('http://localhost:8000/api/v1/quantum/key/exchange', {
                                method: 'POST',
                                headers: {
                                    Authorization: `Bearer ${token}`,
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({
                                    sender_kme_id: 1,
                                    recipient_kme_id: 2
                                })
                            });
                            if (!exchangeResponse.ok) {
                                throw new Error('Failed to generate new quantum keys');
                            }
                        }
                    }
                }
                catch (keyError) {
                    console.error('Error checking quantum keys:', keyError);
                    setEncryptionStatus('Quantum key error. Falling back to Level 2 (Quantum AES)...');
                    toast.error('Quantum keys unavailable. Falling back to Level 2 (Quantum AES).');
                    finalSecurityLevel = 2;
                    setSecurityLevel(2);
                }
            }
            const securityInfo = getSecurityInfo(finalSecurityLevel);
            setEncryptionStatus(`Encrypting with ${securityInfo.name}...`);
            const payload = {
                to,
                subject,
                body,
                security_level: finalSecurityLevel,
                type: 'quantum'
            };
            const ccList = parseRecipientList(cc);
            const bccList = parseRecipientList(bcc);
            if (ccList.length > 0)
                payload.cc = ccList;
            if (bccList.length > 0)
                payload.bcc = bccList;
            setEncryptionStatus('Sending encrypted email via Gmail...');
            const response = await fetch('http://localhost:8000/api/v1/emails/send/quantum', {
                method: 'POST',
                headers: {
                    Authorization: `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            const raw = await response.text();
            let result = {};
            if (raw) {
                try {
                    result = JSON.parse(raw);
                }
                catch (parseError) {
                    console.warn('Failed to parse response JSON:', parseError);
                }
            }
            if (!response.ok || result.success === false) {
                const message = result.detail || result.message || raw || 'Failed to send encrypted email';
                throw new Error(message);
            }
            const summary = {
                success: true,
                message: result.message || 'Levelled quantum email sent successfully',
                flowId: result.flowId || result.flow_id || result.flowID || 'unknown-flow',
                gmailMessageId: result.gmailMessageId || result.gmail_message_id,
                gmailThreadId: result.gmailThreadId || result.gmail_thread_id,
                encryptionMethod: result.encryptionMethod || result.encryption_method || securityInfo.name,
                securityLevel: result.securityLevel || result.security_level || finalSecurityLevel,
                emailId: result.emailId ?? result.email_id,
                emailUuid: result.emailUuid || result.email_uuid,
                entropy: result.entropy,
                keyId: result.keyId || result.key_id,
                encryptedSize: result.encryptedSize ?? result.encrypted_size,
                timestamp: result.timestamp,
                sentViaGmail: result.sent_via_gmail !== undefined ? result.sent_via_gmail : true
            };
            console.info('Quantum email sent successfully', summary);
            setEncryptionStatus(`Successfully sent with ${summary.encryptionMethod}!`);
            toast.success(`✉️ Email sent with ${summary.encryptionMethod}`, {
                duration: 4000,
                style: {
                    background: '#10b981',
                    color: 'white'
                }
            });
            toast.custom((t) => (_jsxs("div", { className: "bg-slate-900 text-slate-100 px-4 py-3 rounded-lg shadow-lg border border-slate-700 max-w-sm", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx("span", { className: "font-semibold text-sm", children: "Quantum email delivered" }), _jsx("button", { onClick: () => toast.dismiss(t.id), className: "text-slate-400 hover:text-slate-200 text-xs uppercase tracking-wide", children: "Dismiss" })] }), _jsxs("div", { className: "mt-2 space-y-1 text-xs font-mono", children: [_jsxs("div", { children: ["Flow: ", summary.flowId] }), summary.gmailMessageId && _jsxs("div", { children: ["Gmail ID: ", summary.gmailMessageId] }), _jsxs("div", { children: ["Level ", summary.securityLevel, " \u2022 ", summary.encryptionMethod] })] })] })), { duration: 7000 });
            resetForm();
            setIsSending(false);
            setEncryptionStatus('');
            onSend(summary);
        }
        catch (error) {
            console.error('Error sending email:', error);
            const message = error?.message || 'Network or server error';
            setEncryptionStatus(`Failed: ${message}`);
            toast.error(`Failed to send email: ${message}`, {
                duration: 5000,
                style: {
                    background: '#ef4444',
                    color: 'white'
                }
            });
            setIsSending(false);
        }
    };
    const resetForm = () => {
        setTo('');
        setCc('');
        setBcc('');
        setSubject('');
        setBody('');
        setSecurityLevel(1);
        setAttachments([]);
        setShowCcBcc(false);
        setEncryptionStatus('');
    };
    const handleFileSelect = (event) => {
        const files = Array.from(event.target.files || []);
        setAttachments(prev => [...prev, ...files]);
    };
    const removeAttachment = (index) => {
        setAttachments(prev => prev.filter((_, i) => i !== index));
    };
    const formatFileSize = (bytes) => {
        if (bytes === 0)
            return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };
    const getSecurityInfo = (level) => {
        switch (level) {
            case 1:
                return {
                    name: 'Quantum Secure (One Time Pad)',
                    description: 'Use One Time Pad with Quantum keys - Maximum security',
                    color: 'purple',
                    icon: (_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) }))
                };
            case 2:
                return {
                    name: 'Quantum-aided AES',
                    description: 'Use Quantum keys as seed for AES encryption',
                    color: 'blue',
                    icon: (_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) }))
                };
            case 3:
                return {
                    name: 'Post-Quantum Cryptography (PQC)',
                    description: 'Alternative encryption method for post-quantum era',
                    color: 'green',
                    icon: (_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) }))
                };
            case 4:
                return {
                    name: 'No Quantum Security',
                    description: 'Standard encryption without quantum enhancement',
                    color: 'gray',
                    icon: (_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" }) }))
                };
            default:
                // Default to level 1 (highest security) if something goes wrong
                return {
                    name: 'Quantum Secure (One Time Pad)',
                    description: 'Use One Time Pad with Quantum keys - Maximum security',
                    color: 'purple',
                    icon: (_jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" }) }))
                };
        }
    };
    // Get security info based on current level
    const security = getSecurityInfo(securityLevel);
    return (_jsx(AnimatePresence, { children: isOpen && (_jsxs(_Fragment, { children: [_jsx(motion.div, { initial: { opacity: 0 }, animate: { opacity: 1 }, exit: { opacity: 0 }, onClick: onClose, className: "fixed inset-0 bg-black/70 backdrop-blur-sm z-50" }), _jsx(motion.div, { initial: { opacity: 0, scale: 0.9 }, animate: { opacity: 1, scale: 1 }, exit: { opacity: 0, scale: 0.9 }, transition: { type: 'spring', damping: 25, stiffness: 200 }, className: "fixed inset-0 z-50 flex items-center justify-center p-4", children: _jsxs(Card, { className: "w-full max-w-4xl max-h-[90vh] overflow-hidden bg-white dark:bg-gray-800 shadow-2xl", children: [_jsxs(CardHeader, { className: "border-b border-gray-200 dark:border-gray-700 pb-4", children: [_jsxs("div", { className: "flex items-center justify-between", children: [_jsx(CardTitle, { className: "text-xl font-semibold text-gray-900 dark:text-white", children: replyTo ? 'Reply' : 'Compose Email' }), _jsxs("div", { className: "flex items-center space-x-2", children: [_jsxs("select", { value: securityLevel, onChange: (e) => setSecurityLevel(Number(e.target.value)), className: "px-3 py-1 rounded-lg text-sm font-medium border-2 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-white", children: [_jsx("option", { value: 1, children: "Level 1 - Quantum Secure (OTP)" }), _jsx("option", { value: 2, children: "Level 2 - Quantum-aided AES" }), _jsx("option", { value: 3, children: "Level 3 - Post-Quantum Cryptography" }), _jsx("option", { value: 4, children: "Level 4 - No Quantum Security" })] }), _jsx(Button, { onClick: onClose, variant: "ghost", size: "sm", className: "text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200", children: _jsx("svg", { className: "w-5 h-5", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) })] })] }), _jsx("div", { className: `mt-3 p-4 rounded-lg border transition-all duration-200 ${security.color === 'purple' ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800' :
                                            security.color === 'blue' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' :
                                                security.color === 'green' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' :
                                                    'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700'}`, children: _jsxs("div", { className: "flex items-start space-x-3", children: [_jsx("div", { className: `flex-shrink-0 p-2 rounded-lg ${security.color === 'purple' ? 'bg-purple-100 dark:bg-purple-800/50 text-purple-600 dark:text-purple-400' :
                                                        security.color === 'blue' ? 'bg-blue-100 dark:bg-blue-800/50 text-blue-600 dark:text-blue-400' :
                                                            security.color === 'green' ? 'bg-green-100 dark:bg-green-800/50 text-green-600 dark:text-green-400' :
                                                                'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'}`, children: security.icon }), _jsxs("div", { className: "flex-1", children: [_jsx("p", { className: `text-sm font-semibold ${security.color === 'purple' ? 'text-purple-800 dark:text-purple-300' :
                                                                security.color === 'blue' ? 'text-blue-800 dark:text-blue-300' :
                                                                    security.color === 'green' ? 'text-green-800 dark:text-green-300' :
                                                                        'text-gray-800 dark:text-gray-300'}`, children: security.name }), _jsx("p", { className: `text-xs mt-1 ${security.color === 'purple' ? 'text-purple-600 dark:text-purple-400' :
                                                                security.color === 'blue' ? 'text-blue-600 dark:text-blue-400' :
                                                                    security.color === 'green' ? 'text-green-600 dark:text-green-400' :
                                                                        'text-gray-600 dark:text-gray-400'}`, children: security.description })] })] }) })] }), _jsxs(CardContent, { className: "p-0 flex flex-col max-h-[calc(90vh-120px)]", children: [_jsxs("div", { className: "p-6 border-b border-gray-200 dark:border-gray-700 space-y-4", children: [_jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("label", { className: "w-12 text-sm font-medium text-gray-700 dark:text-gray-300", children: "To:" }), _jsxs("div", { className: "flex-1 relative", children: [_jsx("input", { type: "email", value: to, onChange: (e) => setTo(e.target.value), onFocus: () => setShowContacts(true), onBlur: () => setTimeout(() => setShowContacts(false), 200), placeholder: "recipient@example.com", className: "w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white", required: true }), _jsx(AnimatePresence, { children: showContacts && (_jsx(motion.div, { initial: { opacity: 0, y: -10 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -10 }, className: "absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-10 max-h-48 overflow-y-auto", children: contacts.map((contact, index) => (_jsxs("button", { onClick: () => {
                                                                            setTo(contact.email);
                                                                            setShowContacts(false);
                                                                        }, className: "w-full px-4 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-600 flex items-center space-x-3", children: [_jsx("div", { className: "w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center", children: _jsx("span", { className: "text-white text-sm font-medium", children: contact.name.charAt(0) }) }), _jsxs("div", { children: [_jsx("p", { className: "text-sm font-medium text-gray-900 dark:text-white", children: contact.name }), _jsx("p", { className: "text-xs text-gray-500 dark:text-gray-400", children: contact.email })] })] }, index))) })) })] }), _jsx(Button, { onClick: () => setShowCcBcc(!showCcBcc), variant: "ghost", size: "sm", className: "text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300", children: "Cc/Bcc" })] }), _jsx(AnimatePresence, { children: showCcBcc && (_jsxs(motion.div, { initial: { opacity: 0, height: 0 }, animate: { opacity: 1, height: 'auto' }, exit: { opacity: 0, height: 0 }, className: "space-y-4 overflow-hidden", children: [_jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("label", { className: "w-12 text-sm font-medium text-gray-700 dark:text-gray-300", children: "Cc:" }), _jsx("input", { type: "email", value: cc, onChange: (e) => setCc(e.target.value), placeholder: "cc@example.com", className: "flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white" })] }), _jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("label", { className: "w-12 text-sm font-medium text-gray-700 dark:text-gray-300", children: "Bcc:" }), _jsx("input", { type: "email", value: bcc, onChange: (e) => setBcc(e.target.value), placeholder: "bcc@example.com", className: "flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white" })] })] })) }), _jsxs("div", { className: "flex items-center space-x-4", children: [_jsx("label", { className: "w-12 text-sm font-medium text-gray-700 dark:text-gray-300", children: "Subject:" }), _jsx("input", { type: "text", value: subject, onChange: (e) => setSubject(e.target.value), placeholder: "Email subject", className: "flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white", required: true })] })] }), _jsx("div", { className: "flex-1 p-6", children: _jsxs("div", { className: "relative h-full", children: [_jsx("textarea", { ref: bodyRef, value: body, onChange: (e) => setBody(e.target.value), placeholder: "Write your quantum-encrypted message...", className: "w-full h-full min-h-[320px] px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none font-sans text-sm leading-relaxed transition-all duration-200", style: {
                                                        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                                                        lineHeight: '1.6'
                                                    }, required: true }), _jsxs("div", { className: "absolute bottom-2 right-2 text-xs text-gray-400 dark:text-gray-500 bg-white dark:bg-gray-700 px-2 py-1 rounded", children: [body.length, " characters"] })] }) }), attachments.length > 0 && (_jsxs("div", { className: "px-6 py-4 border-t border-gray-200 dark:border-gray-700", children: [_jsxs("h4", { className: "text-sm font-medium text-gray-900 dark:text-white mb-3", children: ["Attachments (", attachments.length, ")"] }), _jsx("div", { className: "space-y-2", children: attachments.map((file, index) => (_jsxs("div", { className: "flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded-lg", children: [_jsxs("div", { className: "flex items-center space-x-3", children: [_jsx("svg", { className: "w-5 h-5 text-gray-500", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" }) }), _jsxs("div", { children: [_jsx("p", { className: "text-sm font-medium text-gray-900 dark:text-white", children: file.name }), _jsx("p", { className: "text-xs text-gray-500 dark:text-gray-400", children: formatFileSize(file.size) })] })] }), _jsx(Button, { onClick: () => removeAttachment(index), variant: "ghost", size: "sm", className: "text-red-500 hover:text-red-700", children: _jsx("svg", { className: "w-4 h-4", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M6 18L18 6M6 6l12 12" }) }) })] }, index))) })] })), _jsxs("div", { className: "flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700", children: [_jsxs("div", { className: "flex items-center space-x-2", children: [_jsx("input", { ref: fileInputRef, type: "file", multiple: true, onChange: handleFileSelect, className: "hidden" }), _jsxs(Button, { onClick: () => fileInputRef.current?.click(), variant: "ghost", size: "sm", className: "text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200", children: [_jsx("svg", { className: "w-4 h-4 mr-2", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" }) }), "Attach"] })] }), _jsxs("div", { className: "flex items-center space-x-3", children: [_jsx(Button, { onClick: onClose, variant: "ghost", disabled: isSending, children: "Cancel" }), _jsx(Button, { onClick: handleSend, disabled: isSending || !to || !subject || !body, className: "bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white", children: isSending ? (_jsxs(_Fragment, { children: [_jsxs("svg", { className: "animate-spin w-4 h-4 mr-2", viewBox: "0 0 24 24", children: [_jsx("circle", { cx: "12", cy: "12", r: "10", stroke: "currentColor", strokeWidth: "4", className: "opacity-25", fill: "none" }), _jsx("path", { fill: "currentColor", className: "opacity-75", d: "M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" })] }), encryptionStatus || "Encrypting..."] })) : (_jsxs(_Fragment, { children: [_jsx("svg", { className: "w-4 h-4 mr-2", fill: "none", stroke: "currentColor", viewBox: "0 0 24 24", children: _jsx("path", { strokeLinecap: "round", strokeLinejoin: "round", strokeWidth: 2, d: "M12 19l9 2-9-18-9 18 9-2zm0 0v-8" }) }), "Send"] })) })] })] })] })] }) })] })) }));
};
