import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { useAuth } from '../../context/AuthContext';
import { apiService } from '../../services/api';
import { useAuthStore } from '../../stores/authStore';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { EmailList } from './EmailList';
import { EmailViewer } from './EmailViewer';
import QuantumDashboard from './QuantumDashboard';
import { SettingsPanel } from './SettingsPanel';
import { NewComposeEmailModal } from '../compose/NewComposeEmailModal';
const deriveDisplayName = (email, name) => {
    if (name && name.trim().length > 0)
        return name;
    if (!email)
        return 'User';
    const prefix = email.split('@')[0];
    return prefix || email;
};
const initialCounts = { inbox: 0, sent: 0, drafts: 0, trash: 0 };
const generateId = () => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
    }
    return Math.random().toString(36).slice(2);
};
export const MainDashboard = () => {
    const { user, isAuthenticated } = useAuth();
    const [currentView, setCurrentView] = useState('email');
    const [activeFolder, setActiveFolder] = useState('inbox');
    const [emails, setEmails] = useState([]);
    const [selectedEmail, setSelectedEmail] = useState(null);
    const [isLoadingEmails, setIsLoadingEmails] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [emailCounts, setEmailCounts] = useState(initialCounts);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [isComposeOpen, setIsComposeOpen] = useState(false);
    const [replyToEmail, setReplyToEmail] = useState(null);
    const normalizeEmail = useCallback((raw) => {
        if (!raw) {
            return {
                id: generateId(),
                timestamp: new Date().toISOString(),
            };
        }
        const baseId = raw.id ?? raw.email_id ?? raw.gmailMessageId ?? raw.messageId ?? raw.uuid ?? raw.uid;
        const resolvedId = baseId ? String(baseId) : generateId();
        const senderEmail = raw.sender_email ?? raw.from_email ?? raw.fromAddress ?? raw.from ?? '';
        const inferredSenderEmail = senderEmail || (typeof raw.sender === 'string' && raw.sender.includes('<')
            ? raw.sender.split('<')[1]?.replace('>', '').trim()
            : raw.sender);
        const finalSenderEmail = inferredSenderEmail || (typeof raw.from === 'string' && raw.from.includes('<')
            ? raw.from.split('<')[1]?.replace('>', '').trim()
            : raw.from);
        const senderName = raw.sender_name ?? raw.from_name ?? (() => {
            if (typeof raw.sender === 'string' && raw.sender.includes('<')) {
                return raw.sender.split('<')[0].trim().replace(/"/g, '');
            }
            if (typeof raw.from === 'string' && raw.from.includes('<')) {
                return raw.from.split('<')[0].trim().replace(/"/g, '');
            }
            if (raw.sender)
                return raw.sender.split('@')[0];
            if (raw.from)
                return raw.from.split('@')[0];
            if (finalSenderEmail)
                return finalSenderEmail.split('@')[0];
            return 'Unknown Sender';
        })();
        const toAddress = raw.to ?? raw.toAddress ?? raw.recipient ?? raw.receiver_email ?? '';
        const timestampSource = raw.timestamp ?? raw.date ?? raw.sentAt ?? raw.receivedAt ?? raw.internalDate;
        const timestamp = timestampSource ? new Date(timestampSource).toISOString() : new Date().toISOString();
        // Don't default security level to 4 - use 0 for non-quantum emails
        const securityLevel = (raw.security_level ?? raw.securityLevel ?? raw.security_info?.level ?? 0);
        const flowId = raw.flow_id ?? raw.flowId ?? raw.encryption_metadata?.flow_id ?? raw.encryption_metadata?.flowId ?? '';
        const gmailMessageId = raw.gmail_message_id ?? raw.gmailMessageId ?? raw.messageId ?? null;
        const gmailThreadId = raw.gmail_thread_id ?? raw.gmailThreadId ?? raw.threadId ?? null;
        const bodyHtml = raw.bodyHtml ?? raw.html_body ?? null;
        const bodyText = raw.bodyText ?? raw.body ?? raw.plain_body ?? raw.snippet ?? '';
        const encryptedBody = raw.body_encrypted ?? raw.encrypted_body ?? '';
        const encryptionMetadata = raw.encryption_metadata ?? raw.encryptionMetadata ?? null;
        const encryptionMethod = raw.encryption_method ?? raw.encryptionMethod ?? encryptionMetadata?.algorithm ?? null;
        const subjectText = String(raw.subject ?? '').toLowerCase();
        const snippetText = String(raw.snippet ?? '').toLowerCase();
        const combinedBody = `${bodyText ?? ''} ${bodyHtml ?? ''}`.toLowerCase();
        const looksQuantumBySubject = subjectText.includes('[quantum') || subjectText.includes('quantum-secured');
        const looksQuantumByContent = combinedBody.includes('quantum-encrypted email') || combinedBody.includes('encrypted content (base64 ciphertext)') || combinedBody.includes('quantum aes-256-gcm');
        const looksQuantumBySnippet = snippetText.includes('quantum-encrypted') || snippetText.includes('qkd');
        const algorithmText = (raw.security_info?.algorithm ?? encryptionMethod ?? '').toLowerCase();
        const hasQuantumSecurityFlag = Boolean(raw.security_info?.quantum_enhanced || algorithmText.includes('quantum') || algorithmText.includes('qkd'));
        const requiresDecryption = raw.requires_decryption ??
            raw.requiresDecryption ??
            Boolean((encryptedBody && encryptedBody.trim().length > 0) ||
                encryptionMetadata ||
                raw.encrypted ||
                looksQuantumBySubject ||
                looksQuantumByContent ||
                looksQuantumBySnippet ||
                hasQuantumSecurityFlag);
        const attachmentsRaw = Array.isArray(raw.attachments)
            ? raw.attachments
            : Array.isArray(raw.attachments_metadata)
                ? raw.attachments_metadata
                : [];
        const normalizedAttachments = attachmentsRaw.map((attachment) => ({
            ...attachment,
            id: attachment.id ?? attachment.attachmentId ?? attachment.partId ?? generateId(),
            name: attachment.name ?? attachment.filename ?? attachment.fileName ?? 'attachment',
            filename: attachment.filename ?? attachment.name ?? attachment.fileName ?? 'attachment',
            size: attachment.size ?? attachment.bodySize ?? 0,
            mimeType: attachment.mimeType ?? attachment.type ?? 'application/octet-stream',
        }));
        const securityInfo = raw.security_info ?? {
            level: securityLevel,
            algorithm: encryptionMethod ?? 'Unknown',
            quantum_enhanced: raw.security_info?.quantum_enhanced ?? true,
            encrypted_size: raw.encrypted_size ?? raw.encryptedSize ?? raw.security_info?.encrypted_size ?? 0,
        };
        return {
            ...raw,
            id: resolvedId,
            email_id: raw.email_id ?? resolvedId,
            subject: raw.subject ?? '(No Subject)',
            snippet: raw.snippet ?? bodyText?.slice(0, 140) ?? '',
            body: raw.body ?? bodyText ?? '',
            bodyText,
            bodyHtml,
            html_body: bodyHtml ?? undefined,
            plain_body: raw.plain_body ?? bodyText ?? '',
            body_encrypted: encryptedBody,
            encrypted_size: raw.encrypted_size ?? raw.encryptedSize ?? 0,
            timestamp,
            securityLevel,
            security_level: securityLevel,
            to: toAddress,
            recipient: raw.recipient ?? toAddress,
            sender: raw.sender ?? (finalSenderEmail ? `${senderName} <${finalSenderEmail}>` : senderName),
            sender_name: senderName,
            sender_email: finalSenderEmail ?? '',
            from: raw.from ?? (finalSenderEmail ? `${senderName} <${finalSenderEmail}>` : senderName),
            from_name: raw.from_name ?? senderName,
            from_email: raw.from_email ?? finalSenderEmail ?? '',
            receiver_email: raw.receiver_email ?? toAddress,
            encrypted: raw.encrypted ?? requiresDecryption,
            requires_decryption: requiresDecryption,
            decrypt_endpoint: raw.decrypt_endpoint ?? `/api/v1/emails/email/${resolvedId}/decrypt`,
            flowId,
            flow_id: flowId,
            gmailMessageId,
            gmail_message_id: gmailMessageId,
            gmailThreadId,
            gmail_thread_id: gmailThreadId,
            encryptionMethod,
            encryption_method: encryptionMethod,
            encryption_metadata: encryptionMetadata,
            sent_via_gmail: raw.sent_via_gmail ?? encryptionMetadata?.sent_via_gmail,
            attachments: normalizedAttachments,
            read: raw.read ?? raw.isRead ?? raw.is_read ?? true,
            isRead: raw.isRead ?? raw.read ?? raw.is_read ?? true,
            is_read: raw.is_read ?? raw.isRead ?? raw.read ?? true,
            isStarred: raw.isStarred ?? raw.is_starred ?? false,
            is_starred: raw.is_starred ?? raw.isStarred ?? false,
            security_info: securityInfo,
        };
    }, []);
    const fetchEmailCounts = useCallback(async () => {
        try {
            const folders = await apiService.getEmailFolders().catch(() => []);
            if (!Array.isArray(folders)) {
                setEmailCounts(initialCounts);
                return;
            }
            const counts = folders.reduce((acc, folder) => {
                const id = String(folder.id ?? folder.name ?? '').toLowerCase();
                const value = Number(folder.count ?? folder.total ?? 0);
                if (id.includes('inbox'))
                    acc.inbox = value;
                if (id.includes('sent'))
                    acc.sent = value;
                if (id.includes('draft'))
                    acc.drafts = value;
                if (id.includes('trash') || id.includes('bin'))
                    acc.trash = value;
                return acc;
            }, { ...initialCounts });
            setEmailCounts(counts);
        }
        catch (error) {
            console.error('Failed to fetch email counts:', error);
            setEmailCounts(initialCounts);
        }
    }, []);
    const loadEmailDetails = useCallback(async (emailId, fallback) => {
        try {
            console.log('📧 Loading email details for:', emailId);
            const details = await apiService.getEmailDetails(emailId);
            console.log('📥 Received email details from backend:', {
                flow_id: details.flow_id,
                security_level: details.security_level,
                encrypted_size: details.encrypted_size,
                security_info: details.security_info,
                encryption_metadata: details.encryption_metadata,
                requires_decryption: details.requires_decryption,
                body_encrypted: details.body_encrypted ? `${details.body_encrypted.substring(0, 50)}...` : null
            });
            const normalized = normalizeEmail({ ...fallback, ...details });
            console.log('🔄 Normalized email:', {
                id: normalized.id,
                flow_id: normalized.flow_id,
                security_level: normalized.security_level,
                encrypted_size: normalized.encrypted_size,
                security_info: normalized.security_info,
                requires_decryption: normalized.requires_decryption,
                body_encrypted: normalized.body_encrypted ? `${normalized.body_encrypted.substring(0, 50)}...` : null
            });
            setSelectedEmail(normalized);
            setEmails((current) => current.map((email) => (email.id === normalized.id ? normalized : email)));
            if (!normalized.isRead) {
                await apiService.markEmailAsRead(normalized.id, true).catch(() => undefined);
                setEmails((current) => current.map((email) => email.id === normalized.id ? { ...email, isRead: true, read: true, is_read: true } : email));
            }
        }
        catch (error) {
            console.error('Failed to load email details:', error);
            toast.error('Failed to load full email content');
        }
    }, [normalizeEmail]);
    const fetchEmails = useCallback(async (folder) => {
        setIsLoadingEmails(true);
        try {
            const response = await apiService.getEmails({ folder: folder, maxResults: 50 });
            const mapped = Array.isArray(response.emails)
                ? response.emails.map((email) => normalizeEmail(email))
                : [];
            setEmails(mapped);
            if (mapped.length > 0) {
                const initialEmail = mapped[0];
                setSelectedEmail(initialEmail);
                loadEmailDetails(initialEmail.id, initialEmail);
            }
            else {
                setSelectedEmail(null);
            }
        }
        catch (error) {
            console.error('Failed to fetch emails:', error);
            toast.error('Failed to load emails');
            setEmails([]);
            setSelectedEmail(null);
        }
        finally {
            setIsLoadingEmails(false);
        }
    }, [loadEmailDetails, normalizeEmail]);
    const handleEmailSelect = useCallback((email) => {
        setCurrentView('email');
        setSelectedEmail(email);
        // Immediately mark as read in local state to remove red dot
        if (!email.isRead && !email.read) {
            setEmails(current => current.map(e => e.id === email.id ? { ...e, isRead: true, read: true, is_read: true } : e));
        }
        loadEmailDetails(email.id, email);
    }, [loadEmailDetails]);
    const handleFolderChange = useCallback((folder) => {
        setCurrentView('email');
        setActiveFolder(folder);
        setSelectedEmail(null);
    }, []);
    const handleCompose = useCallback(() => {
        setReplyToEmail(null);
        setIsComposeOpen(true);
    }, []);
    const handleReply = useCallback(() => {
        if (!selectedEmail)
            return;
        setReplyToEmail(selectedEmail);
        setIsComposeOpen(true);
    }, [selectedEmail]);
    const handleReplyAll = useCallback(() => {
        if (!selectedEmail)
            return;
        setReplyToEmail(selectedEmail);
        setIsComposeOpen(true);
    }, [selectedEmail]);
    const handleForward = useCallback(() => {
        if (!selectedEmail)
            return;
        setReplyToEmail(selectedEmail);
        setIsComposeOpen(true);
    }, [selectedEmail]);
    const handleDeleteEmail = useCallback(async () => {
        if (!selectedEmail)
            return;
        try {
            if (activeFolder === 'trash') {
                await apiService.deleteEmail(selectedEmail.id);
            }
            else {
                await apiService.moveEmailToTrash(selectedEmail.id);
            }
            toast.success(activeFolder === 'trash' ? 'Email deleted' : 'Moved to trash');
            await fetchEmails(activeFolder);
            await fetchEmailCounts();
        }
        catch (error) {
            console.error('Failed to remove email:', error);
            toast.error('Failed to delete email');
        }
    }, [activeFolder, fetchEmailCounts, fetchEmails, selectedEmail]);
    const handleEmailSent = useCallback((summary) => {
        toast.success(summary.message || 'Encrypted email sent');
        setIsComposeOpen(false);
        setReplyToEmail(null);
        fetchEmails(activeFolder);
        fetchEmailCounts();
    }, [activeFolder, fetchEmailCounts, fetchEmails]);
    const filteredEmails = useMemo(() => {
        if (!searchQuery.trim())
            return emails;
        const query = searchQuery.toLowerCase();
        return emails.filter((email) => {
            const fields = [
                email.subject,
                email.snippet,
                email.bodyText,
                email.sender_name,
                email.sender_email,
                email.from,
                email.to,
            ];
            return fields.some((field) => field && String(field).toLowerCase().includes(query));
        });
    }, [emails, searchQuery]);
    useEffect(() => {
        const token = localStorage.getItem('authToken');
        if (!token) {
            apiService.clearAuthToken();
            useAuthStore.setState((state) => ({
                ...state,
                sessionToken: null,
                isAuthenticated: false,
            }));
            return;
        }
        apiService.setAuthToken(token);
        useAuthStore.setState((state) => {
            if (state.sessionToken === token && state.isAuthenticated) {
                return state;
            }
            return {
                ...state,
                sessionToken: token,
                isAuthenticated: true,
                isLoading: false,
                error: null,
                user: state.user ||
                    (user
                        ? {
                            email: user.email,
                            displayName: deriveDisplayName(user.email, user.name),
                            createdAt: new Date().toISOString(),
                            oauthConnected: true,
                            lastLogin: new Date().toISOString(),
                        }
                        : state.user),
            };
        });
    }, [isAuthenticated, user?.email, user?.name]);
    useEffect(() => {
        fetchEmailCounts();
    }, [fetchEmailCounts]);
    useEffect(() => {
        fetchEmails(activeFolder);
    }, [activeFolder, fetchEmails]);
    const headerUser = user
        ? {
            id: user.email,
            email: user.email,
            name: deriveDisplayName(user.email, user.name),
            picture: user?.picture,
        }
        : null;
    return (_jsxs("div", { className: "flex-1 flex flex-col bg-[#fafbfc] dark:bg-[#0d1117] overflow-hidden h-full", children: [_jsx(Header, { user: headerUser, onCompose: handleCompose, onSettings: () => setIsSettingsOpen(true), searchQuery: searchQuery, onSearchChange: setSearchQuery, currentView: currentView, onViewChange: setCurrentView }), _jsxs("div", { className: "flex-1 flex overflow-hidden px-3 pb-3 pt-2 gap-3", children: [_jsx("div", { className: "w-56 flex-shrink-0", children: _jsx(Sidebar, { activeFolder: activeFolder, onFolderChange: handleFolderChange, onCompose: handleCompose, emailCounts: emailCounts, onNavigateToView: (view) => setCurrentView(view === 'quantum' ? 'quantum' : 'email') }) }), currentView === 'email' ? (_jsxs(_Fragment, { children: [_jsx("div", { className: "w-80 flex-shrink-0", children: _jsx(EmailList, { emails: filteredEmails, selectedEmail: selectedEmail, onEmailSelect: (email) => handleEmailSelect(email), isLoading: isLoadingEmails, activeFolder: activeFolder }) }), _jsx("div", { className: "flex-1 min-w-0", children: _jsx(EmailViewer, { email: selectedEmail, onReply: handleReply, onReplyAll: handleReplyAll, onForward: handleForward, onDelete: handleDeleteEmail }) })] })) : (_jsx("div", { className: "flex-1 overflow-auto", children: _jsx(QuantumDashboard, {}) }))] }), _jsx(NewComposeEmailModal, { isOpen: isComposeOpen, onClose: () => {
                    setIsComposeOpen(false);
                    setReplyToEmail(null);
                }, onSend: handleEmailSent, replyTo: replyToEmail }), _jsx(SettingsPanel, { isOpen: isSettingsOpen, onClose: () => setIsSettingsOpen(false), user: headerUser })] }));
};
export default MainDashboard;
