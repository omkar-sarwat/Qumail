import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
/**
 * DEMO: How to Use the New Compose Email Modal
 *
 * This file demonstrates various ways to integrate and use the NewComposeEmailModal
 * in your QuMail application.
 */
import React, { useState } from 'react';
import { NewComposeEmailModal } from '../components/compose';
import toast from 'react-hot-toast';
// ============================================
// EXAMPLE 1: Basic Integration
// ============================================
export function BasicExample() {
    const [isComposeOpen, setIsComposeOpen] = useState(false);
    const handleSend = (summary) => {
        console.log('✉️ Email Sent Successfully!', summary);
        console.log('Flow ID:', summary.flowId);
        console.log('Security Level:', summary.securityLevel);
        console.log('Encryption Method:', summary.encryptionMethod);
        // Close the modal
        setIsComposeOpen(false);
        // Show success message (optional, modal already shows toast)
        toast.success('Your quantum-encrypted email has been sent!');
    };
    return (_jsxs("div", { className: "p-4", children: [_jsx("button", { onClick: () => setIsComposeOpen(true), className: "px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold shadow-lg", children: "\u2709\uFE0F Compose New Email" }), _jsx(NewComposeEmailModal, { isOpen: isComposeOpen, onClose: () => setIsComposeOpen(false), onSend: handleSend })] }));
}
// ============================================
// EXAMPLE 2: Reply to Email
// ============================================
export function ReplyExample() {
    const [isReplyOpen, setIsReplyOpen] = useState(false);
    // Sample email to reply to
    const originalEmail = {
        id: '123',
        sender_email: 'alice@example.com',
        sender_name: 'Alice Johnson',
        subject: 'Project Update',
        body: 'Hi, just wanted to share the latest updates on the quantum encryption project...',
        timestamp: new Date().toISOString(),
        securityLevel: 2
    };
    const handleReplySent = (summary) => {
        console.log('Reply sent:', summary);
        setIsReplyOpen(false);
        // Update UI, refresh thread, etc.
        toast.success('Reply sent successfully!');
    };
    return (_jsxs("div", { className: "p-4", children: [_jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 max-w-2xl", children: [_jsxs("div", { className: "flex items-center justify-between mb-4", children: [_jsxs("div", { children: [_jsx("h3", { className: "text-lg font-semibold text-gray-900 dark:text-white", children: originalEmail.subject }), _jsxs("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: ["From: ", originalEmail.sender_name, " <", originalEmail.sender_email, ">"] })] }), _jsx("button", { onClick: () => setIsReplyOpen(true), className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors", children: "Reply" })] }), _jsx("div", { className: "mt-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg", children: _jsx("p", { className: "text-gray-800 dark:text-gray-200", children: originalEmail.body }) })] }), _jsx(NewComposeEmailModal, { isOpen: isReplyOpen, onClose: () => setIsReplyOpen(false), onSend: handleReplySent, replyTo: originalEmail })] }));
}
// ============================================
// EXAMPLE 3: Multiple Composers
// ============================================
export function MultipleComposersExample() {
    const [composeState, setComposeState] = useState({ type: null });
    const handleNewEmail = () => {
        setComposeState({ type: 'new' });
    };
    const handleReply = (email) => {
        setComposeState({ type: 'reply', email });
    };
    const handleClose = () => {
        setComposeState({ type: null });
    };
    const handleSend = (summary) => {
        console.log('Email sent:', summary);
        setComposeState({ type: null });
    };
    return (_jsxs("div", { className: "p-4", children: [_jsxs("div", { className: "space-x-4", children: [_jsx("button", { onClick: handleNewEmail, className: "px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700", children: "New Email" }), _jsx("button", { onClick: () => handleReply({
                            id: '1',
                            sender_email: 'bob@example.com',
                            sender_name: 'Bob Smith',
                            subject: 'Hello',
                            body: 'Test email',
                            timestamp: new Date().toISOString()
                        }), className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700", children: "Reply to Email" })] }), _jsx(NewComposeEmailModal, { isOpen: composeState.type !== null, onClose: handleClose, onSend: handleSend, replyTo: composeState.type === 'reply' ? composeState.email : null })] }));
}
// ============================================
// EXAMPLE 4: With State Management (Redux/Zustand)
// ============================================
// Using Zustand for state management
import { create } from 'zustand';
const useComposeStore = create((set) => ({
    isOpen: false,
    replyTo: null,
    openComposer: () => set({ isOpen: true, replyTo: null }),
    openReply: (email) => set({ isOpen: true, replyTo: email }),
    closeComposer: () => set({ isOpen: false, replyTo: null })
}));
export function StateManagementExample() {
    const { isOpen, replyTo, openComposer, openReply, closeComposer } = useComposeStore();
    const handleSend = (summary) => {
        console.log('Email sent:', summary);
        closeComposer();
        // Dispatch action to refresh inbox
        // dispatch(fetchEmails())
    };
    return (_jsxs("div", { className: "p-4", children: [_jsxs("div", { className: "flex gap-3", children: [_jsx("button", { onClick: openComposer, className: "px-4 py-2 bg-blue-600 text-white rounded-lg", children: "Compose" }), _jsx("button", { onClick: () => openReply({
                            id: 'sample-reply',
                            sender_email: 'alice@example.com',
                            sender_name: 'Alice Quantum',
                            subject: 'Follow-up on QKD session',
                            body: 'Just checking in about the keys we exchanged.',
                            timestamp: new Date().toISOString()
                        }), className: "px-4 py-2 bg-purple-600 text-white rounded-lg", children: "Reply to Sample" })] }), _jsx(NewComposeEmailModal, { isOpen: isOpen, onClose: closeComposer, onSend: handleSend, replyTo: replyTo })] }));
}
// ============================================
// EXAMPLE 5: Custom Send Handler with Error Handling
// ============================================
export function ErrorHandlingExample() {
    const [isOpen, setIsOpen] = useState(false);
    const [isSendingExternal, setIsSendingExternal] = useState(false);
    const handleSend = async (summary) => {
        setIsSendingExternal(true);
        try {
            // Additional processing after email is sent
            console.log('Processing send summary:', summary);
            // Maybe save to database
            // await saveToDatabase(summary)
            // Update UI
            // await refreshInbox()
            // Analytics
            // trackEmailSent(summary.securityLevel)
            console.log('✅ All post-send processing completed');
            setIsOpen(false);
            toast.success('Email sent and processed successfully!', {
                duration: 4000,
                icon: '🎉'
            });
        }
        catch (error) {
            console.error('Error in post-send processing:', error);
            toast.error('Email was sent but post-processing failed');
        }
        finally {
            setIsSendingExternal(false);
        }
    };
    return (_jsxs("div", { className: "p-4", children: [_jsx("button", { onClick: () => setIsOpen(true), disabled: isSendingExternal, className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50", children: isSendingExternal ? 'Processing...' : 'Compose Email' }), _jsx(NewComposeEmailModal, { isOpen: isOpen, onClose: () => !isSendingExternal && setIsOpen(false), onSend: handleSend })] }));
}
// ============================================
// EXAMPLE 6: Integration with Email Dashboard
// ============================================
export function DashboardIntegrationExample() {
    const [isComposeOpen, setIsComposeOpen] = useState(false);
    const [emails, setEmails] = useState([]);
    const [selectedEmail, setSelectedEmail] = useState(null);
    const handleSend = (summary) => {
        console.log('Email sent:', summary);
        setIsComposeOpen(false);
        setSelectedEmail(null);
        // Refresh email list
        refreshEmails();
    };
    const refreshEmails = async () => {
        setEmails([
            {
                id: 'demo-1',
                subject: 'Quantum status update',
                sender_name: 'QuMail Bot',
                sender_email: 'bot@qumail.app',
                timestamp: new Date().toISOString()
            },
            {
                id: 'demo-2',
                subject: 'Team meeting notes',
                sender_name: 'Security Team',
                sender_email: 'security@example.com',
                timestamp: new Date().toISOString()
            }
        ]);
        toast.success('Inbox refreshed!');
    };
    const handleReply = (email) => {
        setSelectedEmail(email);
        setIsComposeOpen(true);
    };
    return (_jsxs("div", { className: "min-h-screen bg-gray-100 dark:bg-gray-900 p-4", children: [_jsxs("div", { className: "max-w-7xl mx-auto", children: [_jsx("div", { className: "bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4 mb-4", children: _jsxs("div", { className: "flex items-center justify-between", children: [_jsx("h1", { className: "text-2xl font-bold text-gray-900 dark:text-white", children: "\uD83D\uDCE7 QuMail Dashboard" }), _jsx("button", { onClick: () => {
                                        setSelectedEmail(null);
                                        setIsComposeOpen(true);
                                    }, className: "px-6 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 font-semibold shadow-lg", children: "\u2709\uFE0F Compose" })] }) }), _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-lg shadow-lg p-4", children: [_jsx("h2", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "Inbox" }), emails.length === 0 ? (_jsx("p", { className: "text-gray-500 dark:text-gray-400 text-center py-8", children: "No emails yet. Compose your first quantum-encrypted email!" })) : (_jsx("div", { className: "space-y-2", children: emails.map((email) => (_jsx("div", { className: "p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer", children: _jsxs("div", { className: "flex items-center justify-between", children: [_jsxs("div", { children: [_jsx("p", { className: "font-semibold text-gray-900 dark:text-white", children: email.subject }), _jsxs("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: ["From: ", email.sender_name] })] }), _jsx("button", { onClick: () => handleReply(email), className: "px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700", children: "Reply" })] }) }, email.id))) }))] })] }), _jsx(NewComposeEmailModal, { isOpen: isComposeOpen, onClose: () => {
                    setIsComposeOpen(false);
                    setSelectedEmail(null);
                }, onSend: handleSend, replyTo: selectedEmail })] }));
}
// ============================================
// EXAMPLE 7: Keyboard Shortcut Integration
// ============================================
export function KeyboardShortcutExample() {
    const [isOpen, setIsOpen] = useState(false);
    React.useEffect(() => {
        const handleKeyDown = (e) => {
            // Ctrl+M or Cmd+M to open composer
            if ((e.ctrlKey || e.metaKey) && e.key === 'm') {
                e.preventDefault();
                setIsOpen(true);
            }
            // Escape to close (handled by modal, but good to know)
            if (e.key === 'Escape' && isOpen) {
                setIsOpen(false);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);
    return (_jsxs("div", { className: "p-4", children: [_jsx("div", { className: "bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4 mb-4", children: _jsxs("p", { className: "text-sm text-blue-800 dark:text-blue-300", children: ["\uD83D\uDCA1 ", _jsx("strong", { children: "Tip:" }), " Press ", _jsx("kbd", { className: "px-2 py-1 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded", children: "Ctrl+M" }), " to open the composer"] }) }), _jsx("button", { onClick: () => setIsOpen(true), className: "px-4 py-2 bg-blue-600 text-white rounded-lg", children: "Open Composer" }), _jsx(NewComposeEmailModal, { isOpen: isOpen, onClose: () => setIsOpen(false), onSend: (summary) => {
                    console.log('Sent:', summary);
                    setIsOpen(false);
                } })] }));
}
// ============================================
// EXAMPLE 8: Complete Demo App
// ============================================
export default function CompleteDemoApp() {
    return (_jsx("div", { className: "min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-900 dark:to-gray-800 p-8", children: _jsxs("div", { className: "max-w-6xl mx-auto space-y-8", children: [_jsxs("header", { className: "text-center mb-12", children: [_jsx("h1", { className: "text-4xl font-bold text-gray-900 dark:text-white mb-2", children: "\uD83D\uDCE7 QuMail Composer Demo" }), _jsx("p", { className: "text-gray-600 dark:text-gray-400", children: "Explore different ways to use the NewComposeEmailModal" })] }), _jsxs("div", { className: "grid grid-cols-1 md:grid-cols-2 gap-6", children: [_jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6", children: [_jsx("h3", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "1\uFE0F\u20E3 Basic Example" }), _jsx(BasicExample, {})] }), _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6", children: [_jsx("h3", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "2\uFE0F\u20E3 Reply Example" }), _jsx(ReplyExample, {})] }), _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6", children: [_jsx("h3", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "5\uFE0F\u20E3 Error Handling" }), _jsx(ErrorHandlingExample, {})] }), _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6", children: [_jsx("h3", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "7\uFE0F\u20E3 Keyboard Shortcuts" }), _jsx(KeyboardShortcutExample, {})] })] }), _jsxs("div", { className: "bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6", children: [_jsx("h3", { className: "text-lg font-semibold mb-4 text-gray-900 dark:text-white", children: "6\uFE0F\u20E3 Dashboard Integration" }), _jsx(DashboardIntegrationExample, {})] })] }) }));
}
