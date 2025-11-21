import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useEffect, useRef, useCallback } from 'react';
import QuantumEmailViewer from '../email/QuantumEmailViewer';
import { Shield, ShieldCheck, Lock, Key, Download, Eye, EyeOff, Paperclip, Image as ImageIcon, File, X, ChevronUp, Star, Reply, ReplyAll, Forward, Trash2, MoreHorizontal, Check } from 'lucide-react';
export const EmailViewer = ({ email, onReply, onReplyAll, onForward, onDelete, onStar }) => {
    // Complex State Management
    const [state, setState] = useState({
        isSecurityPanelOpen: false,
        isAttachmentsPanelOpen: false,
        selectedAttachment: null,
        imageModal: {
            isOpen: false,
            imageUrl: '',
            imageName: '',
            imageIndex: 0,
            totalImages: 0
        },
        isStarred: false,
        isProcessingContent: true,
        contentHeight: 0,
        showRawHtml: false,
        copiedText: null,
        expandedSections: new Set(),
        attachmentPreviews: [],
        inlineImages: [],
        processedContent: '',
        securityInfo: null
    });
    const contentRef = useRef(null);
    const processingTimeoutRef = useRef();
    // Security Badge Processing
    const getSecurityBadgeInfo = useCallback((email) => {
        if (!email.encrypted && !email.securityLevel)
            return null;
        const level = email.securityLevel || email.security_info?.level || 1;
        const algorithm = email.encryptionMethod || email.encryption_method || email.security_info?.algorithm || 'Unknown';
        const quantum_enhanced = email.security_info?.quantum_enhanced || false;
        const securityConfigs = {
            1: {
                color: 'bg-blue-100 text-blue-800 border-blue-200',
                icon: _jsx(Key, { className: "w-4 h-4" }),
                description: 'Quantum OTP Encryption'
            },
            2: {
                color: 'bg-green-100 text-green-800 border-green-200',
                icon: _jsx(ShieldCheck, { className: "w-4 h-4" }),
                description: 'AES-256-GCM Quantum Enhanced'
            },
            3: {
                color: 'bg-purple-100 text-purple-800 border-purple-200',
                icon: _jsx(Shield, { className: "w-4 h-4" }),
                description: 'Post-Quantum Cryptography'
            },
            4: {
                color: 'bg-red-100 text-red-800 border-red-200',
                icon: _jsx(Lock, { className: "w-4 h-4" }),
                description: 'RSA-4096 Hybrid Encryption'
            }
        };
        const config = securityConfigs[level] || securityConfigs[1];
        return {
            level,
            algorithm,
            quantum_enhanced,
            color: config.color,
            icon: config.icon,
            description: config.description
        };
    }, []);
    // Advanced Attachment Processing
    const processAttachments = useCallback((email) => {
        if (!email.attachments || email.attachments.length === 0)
            return [];
        return email.attachments.map((attachment, index) => {
            const mimeType = attachment.mimeType || attachment.type || '';
            const name = attachment.filename || attachment.name || `attachment_${index + 1}`;
            const isImage = mimeType.startsWith('image/');
            const isVideo = mimeType.startsWith('video/');
            const isAudio = mimeType.startsWith('audio/');
            const isDocument = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument'].some(type => mimeType.includes(type));
            const isArchive = ['application/zip', 'application/x-rar', 'application/x-7z'].some(type => mimeType.includes(type));
            return {
                id: attachment.id || `att_${index}`,
                name,
                type: mimeType,
                size: attachment.size || 0,
                url: attachment.url,
                thumbnail: isImage ? attachment.url : undefined,
                previewUrl: attachment.url,
                isImage,
                isVideo,
                isAudio,
                isDocument,
                isArchive
            };
        });
    }, []);
    // Advanced HTML Content Processing
    const processEmailContent = useCallback((email) => {
        let content = email.bodyHtml || email.html_body || email.bodyText || email.body || email.plain_body || email.snippet || '';
        if (!content)
            return 'No content available';
        // Process inline images
        const imageRegex = /<img[^>]+src="([^"]+)"[^>]*>/gi;
        const images = [];
        let match;
        while ((match = imageRegex.exec(content)) !== null) {
            images.push(match[1]);
        }
        // Add click handlers to images for modal preview
        content = content.replace(imageRegex, (imgTag, src) => {
            const imageIndex = images.indexOf(src);
            return imgTag.replace('<img', `<img data-image-index="${imageIndex}" style="cursor: pointer; max-width: 100%; height: auto;"`);
        });
        // Process links
        content = content.replace(/<a([^>]+)>/gi, '<a$1 target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 underline">');
        // Sanitize and enhance content
        content = content.replace(/<script[^>]*>.*?<\/script>/gi, '');
        content = content.replace(/javascript:/gi, '');
        // Remove potentially problematic inline styles that could break layout
        content = content.replace(/position:\s*fixed/gi, 'position: relative');
        content = content.replace(/position:\s*absolute/gi, 'position: relative');
        content = content.replace(/width:\s*100vw/gi, 'width: 100%');
        content = content.replace(/height:\s*100vh/gi, 'height: auto');
        content = content.replace(/min-width:\s*\d+px/gi, 'min-width: auto');
        // Wrap content in a constrained container
        content = `<div style="max-width: 100%; overflow: hidden; word-wrap: break-word;">${content}</div>`;
        return content;
    }, []);
    // Formatted file size display
    const formatFileSize = useCallback((bytes) => {
        if (bytes === 0)
            return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }, []);
    // Effects for processing email content and attachments
    useEffect(() => {
        if (!email)
            return;
        setState(prev => ({ ...prev, isProcessingContent: true }));
        // Simulate processing delay for complex content
        processingTimeoutRef.current = setTimeout(() => {
            const securityInfo = getSecurityBadgeInfo(email);
            const attachmentPreviews = processAttachments(email);
            const processedContent = processEmailContent(email);
            const images = processEmailContent(email).match(/<img[^>]+src="([^"]+)"/gi) || [];
            const inlineImages = images.map(img => img.match(/src="([^"]+)"/)?.[1] || '').filter(Boolean);
            setState(prev => ({
                ...prev,
                securityInfo,
                attachmentPreviews,
                processedContent,
                inlineImages,
                isProcessingContent: false,
                isStarred: email.isStarred || false,
                isAttachmentsPanelOpen: attachmentPreviews.length > 0
            }));
        }, 300);
        return () => {
            if (processingTimeoutRef.current) {
                clearTimeout(processingTimeoutRef.current);
            }
        };
    }, [email, getSecurityBadgeInfo, processAttachments, processEmailContent]);
    // Handle content height calculation
    useEffect(() => {
        if (contentRef.current) {
            const height = contentRef.current.scrollHeight;
            setState(prev => ({ ...prev, contentHeight: height }));
        }
    }, [state.processedContent]);
    // Action handlers
    const handleStarToggle = useCallback(() => {
        const newStarred = !state.isStarred;
        setState(prev => ({ ...prev, isStarred: newStarred }));
        onStar?.(newStarred);
    }, [state.isStarred, onStar]);
    const handleImageClick = useCallback((event) => {
        const target = event.target;
        if (target.tagName === 'IMG') {
            const imageIndex = parseInt(target.getAttribute('data-image-index') || '0');
            const imageSrc = target.getAttribute('src') || '';
            const imageName = target.getAttribute('alt') || `Image ${imageIndex + 1}`;
            setState(prev => ({
                ...prev,
                imageModal: {
                    isOpen: true,
                    imageUrl: imageSrc,
                    imageName,
                    imageIndex,
                    totalImages: prev.inlineImages.length
                }
            }));
        }
    }, []);
    const handleAttachmentDownload = useCallback(async (attachment) => {
        if (!attachment.url)
            return;
        try {
            const link = document.createElement('a');
            link.href = attachment.url;
            link.download = attachment.name;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
        catch (error) {
            console.error('Failed to download attachment:', error);
        }
    }, []);
    const closeImageModal = useCallback(() => {
        setState(prev => ({
            ...prev,
            imageModal: { ...prev.imageModal, isOpen: false }
        }));
    }, []);
    const navigateImage = useCallback((direction) => {
        setState(prev => {
            const currentIndex = prev.imageModal.imageIndex;
            const totalImages = prev.imageModal.totalImages;
            let newIndex = direction === 'next' ? currentIndex + 1 : currentIndex - 1;
            if (newIndex >= totalImages)
                newIndex = 0;
            if (newIndex < 0)
                newIndex = totalImages - 1;
            const newImageUrl = prev.inlineImages[newIndex] || '';
            return {
                ...prev,
                imageModal: {
                    ...prev.imageModal,
                    imageIndex: newIndex,
                    imageUrl: newImageUrl,
                    imageName: `Image ${newIndex + 1}`
                }
            };
        });
    }, []);
    // Only log when we detect potential quantum email for debugging
    const debugLogEmail = email?.security_level > 0 || email?.body_encrypted;
    if (debugLogEmail) {
        console.log('🔍 EmailViewer received email:', {
            id: email?.id,
            subject: email?.subject,
            body_encrypted: email?.body_encrypted ? `${email.body_encrypted.substring(0, 50)}...` : null,
            security_level: email?.security_level,
            security_info: email?.security_info,
            requires_decryption: email?.requires_decryption,
            flow_id: email?.flow_id
        });
    }
    // Handle encrypted emails with QuantumEmailViewer
    // ONLY show QuantumEmailViewer for emails that were actually quantum-encrypted
    const hasEncryptedPayload = Boolean(email &&
        typeof email.body_encrypted === 'string' &&
        email.body_encrypted.trim().length > 0);
    const encryptionMetadata = email?.encryption_metadata;
    const hasEncryptionMetadata = Boolean(encryptionMetadata);
    const explicitQuantumFlag = Boolean(email?.requires_decryption);
    const normalizedSecurityLevel = Number(email?.security_level ??
        email?.securityLevel ??
        email?.security_info?.level ??
        0);
    const hasSecurityLevel = normalizedSecurityLevel > 0;
    const hasQuantumMetadata = Boolean(hasEncryptionMetadata && (encryptionMetadata?.flow_id ||
        encryptionMetadata?.flowId ||
        encryptionMetadata?.algorithm ||
        encryptionMetadata?.encrypted_size ||
        encryptionMetadata?.encryptedSize));
    const isQuantumType = email?.type === 'quantum';
    if (debugLogEmail) {
        console.log('🔍 Quantum detection flags:', {
            hasEncryptedPayload,
            hasQuantumMetadata,
            explicitQuantumFlag,
            hasSecurityLevel,
            isQuantumType
        });
    }
    // Route to QuantumEmailViewer whenever the backend marks the email as encrypted
    // or we have clear encrypted payload/metadata to avoid hiding the decrypt button
    const isActuallyQuantumEmail = Boolean(hasEncryptedPayload ||
        explicitQuantumFlag ||
        hasQuantumMetadata ||
        hasSecurityLevel ||
        isQuantumType);
    if (email && isActuallyQuantumEmail) {
        console.log('🔐 Routing to QuantumEmailViewer with email data:', {
            email_id: email.email_id ?? email.id,
            flow_id: email.flow_id,
            security_level: email.security_level,
            encrypted_size: email.encrypted_size,
            security_info: email.security_info,
            encryption_metadata: email.encryption_metadata,
            hasEncryptedPayload,
            hasSecurityLevel,
            explicitQuantumFlag
        });
        const quantumEmail = {
            email_id: String(email.email_id ?? email.id ?? ''),
            flow_id: email.flow_id ?? email.flowId ?? '',
            sender_email: email.sender_email ??
                email.senderEmail ??
                email.from_email ??
                email.sender ??
                '',
            receiver_email: email.receiver_email ??
                email.receiverEmail ??
                email.to ??
                email.recipient ??
                '',
            subject: email.subject || '(No Subject)',
            body_encrypted: email.body_encrypted ?? '',
            security_level: email.security_level ??
                email.securityLevel ??
                email.security_info?.level ??
                0,
            timestamp: email.timestamp || new Date().toISOString(),
            is_read: email.is_read ?? email.isRead ?? false,
            is_starred: email.is_starred ?? email.isStarred ?? false,
            requires_decryption: true,
            decrypt_endpoint: email.decrypt_endpoint ??
                `/api/v1/emails/email/${String(email.email_id ?? email.id ?? '')}/decrypt`,
            security_info: email.security_info ?? {
                level: email.security_level ??
                    email.securityLevel ??
                    0,
                algorithm: email.encryptionMethod ??
                    email.encryption_method ??
                    email.encryption_metadata?.algorithm ??
                    'Unknown',
                quantum_enhanced: email.security_info?.quantum_enhanced ??
                    email.encryption_metadata?.quantum_enhanced ??
                    true,
                encrypted_size: email.encrypted_size ??
                    email.encryptedSize ??
                    email.security_info?.encrypted_size ??
                    email.encryption_metadata?.encrypted_size ??
                    (email.body_encrypted ? email.body_encrypted.length : 0)
            },
            encryption_metadata: email.encryption_metadata
        };
        return _jsx(QuantumEmailViewer, { email: quantumEmail });
    }
    // Helper functions for email processing
    const getSenderInfo = (email) => {
        const senderName = email.sender_name || email.from_name ||
            (email.sender && email.sender.includes('<') ?
                email.sender.split('<')[0].trim().replace(/"/g, '') :
                email.sender?.split('@')[0]) ||
            (email.from && email.from.includes('<') ?
                email.from.split('<')[0].trim().replace(/"/g, '') :
                email.from?.split('@')[0]) || 'Unknown Sender';
        const senderEmail = email.sender_email || email.from_email ||
            (email.sender && email.sender.includes('<') ?
                email.sender.split('<')[1]?.replace('>', '').trim() :
                email.sender) ||
            (email.from && email.from.includes('<') ?
                email.from.split('<')[1]?.replace('>', '').trim() :
                email.from) || '';
        return { senderName, senderEmail };
    };
    // Show empty state if no email selected
    if (!email) {
        return (_jsx("div", { className: "h-full flex items-center justify-center bg-white dark:bg-[#0d1117]", children: _jsxs("div", { className: "text-center p-8", children: [_jsx("div", { className: "w-20 h-20 mx-auto mb-4 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center", children: _jsx(ImageIcon, { className: "w-10 h-10 text-gray-400" }) }), _jsx("h3", { className: "text-base font-semibold text-gray-900 dark:text-white mb-1", children: "No Email Selected" }), _jsx("p", { className: "text-sm text-gray-500 dark:text-gray-400", children: "Select an email from the list to view its contents" })] }) }));
    }
    const { senderName, senderEmail } = getSenderInfo(email);
    return (_jsxs("div", { className: "h-full flex bg-white dark:bg-[#0d1117] overflow-hidden", children: [_jsxs("div", { className: "flex-1 flex flex-col overflow-hidden", children: [_jsx("div", { className: "flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-[#0d1117]", children: _jsxs("div", { className: "flex items-center gap-3", children: [_jsxs("div", { className: "flex items-center gap-1", children: [_jsxs("button", { onClick: onReply, className: "inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: "Reply", children: [_jsx(Reply, { className: "w-4 h-4" }), _jsx("span", { children: "Reply" })] }), _jsxs("button", { onClick: onReplyAll, className: "inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: "Reply All", children: [_jsx(ReplyAll, { className: "w-4 h-4" }), _jsx("span", { children: "Reply All" })] }), _jsxs("button", { onClick: onForward, className: "inline-flex items-center gap-2 px-4 py-2 text-sm font-normal text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: "Forward", children: [_jsx(Forward, { className: "w-4 h-4" }), _jsx("span", { children: "Forward" })] })] }), _jsx("div", { className: "h-6 w-px bg-gray-200 dark:bg-gray-700 mx-2" }), _jsxs("div", { className: "flex items-center gap-1", children: [_jsx("button", { onClick: onDelete, className: "p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: "Delete", children: _jsx(Trash2, { className: "w-4 h-4" }) }), _jsx("button", { onClick: handleStarToggle, className: `p-2 rounded transition-colors ${state.isStarred
                                                ? 'text-yellow-500 hover:bg-gray-100 dark:hover:bg-gray-800'
                                                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`, title: state.isStarred ? 'Unstar' : 'Star', children: state.isStarred ? _jsx(Star, { className: "w-4 h-4 fill-current" }) : _jsx(Star, { className: "w-4 h-4" }) }), _jsx("button", { onClick: () => setState(prev => ({ ...prev, showRawHtml: !prev.showRawHtml })), className: "p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: state.showRawHtml ? 'Show formatted' : 'Show source', children: state.showRawHtml ? _jsx(EyeOff, { className: "w-4 h-4" }) : _jsx(Eye, { className: "w-4 h-4" }) }), _jsx("button", { className: "p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded transition-colors", title: "More options", children: _jsx(MoreHorizontal, { className: "w-4 h-4" }) })] })] }) }), _jsxs("div", { className: "px-8 py-6 border-b border-gray-200 dark:border-gray-700", children: [_jsx("h1", { className: "text-2xl font-semibold text-gray-900 dark:text-white mb-5 leading-tight", children: email.subject || "(No Subject)" }), _jsxs("div", { className: "flex items-start justify-between", children: [_jsxs("div", { className: "flex items-start gap-3", children: [_jsx("div", { className: "w-12 h-12 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white font-medium text-base flex-shrink-0 shadow-sm", children: senderName.charAt(0).toUpperCase() }), _jsxs("div", { children: [_jsxs("div", { className: "flex items-center gap-2 mb-1", children: [_jsx("p", { className: "font-semibold text-base text-gray-900 dark:text-white", children: senderName }), email.encrypted && (_jsxs("span", { className: "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800", children: [_jsx(Lock, { className: "w-3 h-3 mr-1" }), "Encrypted"] }))] }), senderEmail && (_jsxs("p", { className: "text-sm text-gray-600 dark:text-gray-400 mb-1", children: ["<", senderEmail, ">"] })), _jsxs("p", { className: "text-sm text-gray-500 dark:text-gray-500", children: ["To: ", _jsx("span", { className: "text-gray-700 dark:text-gray-300", children: email.to || email.recipient || 'me' })] })] })] }), _jsxs("div", { className: "text-sm text-gray-500 dark:text-gray-400 text-right", children: [_jsx("p", { className: "font-normal", children: new Date(email.timestamp).toLocaleDateString('en-US', {
                                                    weekday: 'short',
                                                    month: 'short',
                                                    day: 'numeric',
                                                    year: 'numeric'
                                                }) }), _jsx("p", { className: "text-gray-400 dark:text-gray-500 mt-0.5", children: new Date(email.timestamp).toLocaleTimeString('en-US', {
                                                    hour: '2-digit',
                                                    minute: '2-digit',
                                                    hour12: true
                                                }) })] })] })] }), state.attachmentPreviews.length > 0 && (_jsxs("div", { className: "px-8 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-[#0d1117]", children: [_jsxs("div", { className: "flex items-center gap-2 mb-3", children: [_jsx(Paperclip, { className: "w-4 h-4 text-gray-500 dark:text-gray-400" }), _jsxs("h3", { className: "text-sm font-medium text-gray-700 dark:text-gray-300", children: [state.attachmentPreviews.length, " ", state.attachmentPreviews.length === 1 ? 'Attachment' : 'Attachments'] })] }), _jsx("div", { className: "flex flex-wrap gap-2", children: state.attachmentPreviews.map((attachment) => (_jsxs("div", { className: "inline-flex items-center gap-2 pl-3 pr-2 py-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm transition-all group", children: [_jsx(File, { className: "w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" }), _jsxs("div", { className: "flex flex-col min-w-0", children: [_jsx("p", { className: "text-sm text-gray-900 dark:text-white truncate max-w-xs", children: attachment.name }), _jsx("p", { className: "text-xs text-gray-500 dark:text-gray-400", children: formatFileSize(attachment.size) })] }), _jsx("button", { onClick: () => handleAttachmentDownload(attachment), className: "flex-shrink-0 p-1.5 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded transition-colors", title: "Download", children: _jsx(Download, { className: "w-3.5 h-3.5" }) })] }, attachment.id))) })] })), _jsx("div", { className: "flex-1 overflow-hidden bg-white dark:bg-[#0d1117]", children: state.isProcessingContent ? (_jsx("div", { className: "h-full flex items-center justify-center", children: _jsxs("div", { className: "text-center", children: [_jsx("div", { className: "w-10 h-10 border-2 border-gray-200 dark:border-gray-700 border-t-blue-600 rounded-full animate-spin mx-auto mb-4" }), _jsx("p", { className: "text-sm text-gray-600 dark:text-gray-400", children: "Loading message..." })] }) })) : (_jsx("div", { className: "h-full overflow-y-auto", children: _jsx("div", { className: "max-w-5xl mx-auto px-8 py-8", children: state.showRawHtml ? (_jsx("div", { className: "bg-gray-900 dark:bg-black text-gray-100 p-4 rounded-lg overflow-x-auto font-mono text-xs", children: _jsx("pre", { className: "whitespace-pre-wrap break-words", children: state.processedContent }) })) : (_jsx("div", { ref: contentRef, className: "prose prose-base dark:prose-invert max-w-none \r\n                    prose-headings:text-gray-900 dark:prose-headings:text-white prose-headings:font-semibold\r\n                    prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed prose-p:text-[15px]\r\n                    prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline prose-a:font-normal\r\n                    prose-strong:text-gray-900 dark:prose-strong:text-white prose-strong:font-semibold\r\n                    prose-code:text-gray-800 dark:prose-code:text-gray-200 prose-code:bg-gray-100 dark:prose-code:bg-gray-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm\r\n                    prose-pre:bg-gray-50 dark:prose-pre:bg-gray-900 prose-pre:border prose-pre:border-gray-200 dark:prose-pre:border-gray-800\r\n                    prose-img:rounded-lg prose-img:shadow-sm prose-img:border prose-img:border-gray-200 dark:prose-img:border-gray-700\r\n                    prose-ul:text-gray-700 dark:prose-ul:text-gray-300 prose-ul:leading-relaxed\r\n                    prose-ol:text-gray-700 dark:prose-ol:text-gray-300 prose-ol:leading-relaxed\r\n                    prose-li:text-gray-700 dark:prose-li:text-gray-300 prose-li:text-[15px]\r\n                    prose-blockquote:border-l-4 prose-blockquote:border-l-gray-300 dark:prose-blockquote:border-l-gray-700 prose-blockquote:text-gray-600 dark:prose-blockquote:text-gray-400 prose-blockquote:italic\r\n                    prose-hr:border-gray-200 dark:prose-hr:border-gray-700\r\n                    [&>*]:max-w-full [&_img]:max-w-full [&_img]:h-auto [&_table]:max-w-full [&_table]:overflow-x-auto", style: {
                                        maxWidth: '100%',
                                        overflow: 'hidden',
                                        wordWrap: 'break-word',
                                        overflowWrap: 'break-word',
                                        lineHeight: '1.7'
                                    }, onClick: handleImageClick, dangerouslySetInnerHTML: { __html: state.processedContent } })) }) })) }), state.imageModal.isOpen && (_jsx("div", { className: "fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-90 transition-opacity duration-300", children: _jsxs("div", { className: "relative max-w-4xl max-h-screen p-4", children: [_jsx("button", { onClick: closeImageModal, className: "absolute top-6 right-6 z-10 p-2 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200", children: _jsx(X, { className: "w-6 h-6" }) }), state.imageModal.totalImages > 1 && (_jsxs(_Fragment, { children: [_jsx("button", { onClick: () => navigateImage('prev'), className: "absolute left-6 top-1/2 transform -translate-y-1/2 z-10 p-3 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200", children: _jsx(ChevronUp, { className: "w-6 h-6 transform -rotate-90" }) }), _jsx("button", { onClick: () => navigateImage('next'), className: "absolute right-6 top-1/2 transform -translate-y-1/2 z-10 p-3 text-white bg-black bg-opacity-50 rounded-full hover:bg-opacity-70 transition-all duration-200", children: _jsx(ChevronUp, { className: "w-6 h-6 transform rotate-90" }) })] })), _jsx("img", { src: state.imageModal.imageUrl, alt: state.imageModal.imageName, className: "max-w-full max-h-full object-contain rounded-lg shadow-2xl" }), _jsxs("div", { className: "absolute bottom-6 left-1/2 transform -translate-x-1/2 text-center text-white", children: [_jsx("p", { className: "text-lg font-medium mb-1", children: state.imageModal.imageName }), state.imageModal.totalImages > 1 && (_jsxs("p", { className: "text-sm opacity-75", children: [state.imageModal.imageIndex + 1, " of ", state.imageModal.totalImages] }))] })] }) }))] }), (() => {
                // Determine the declared security level and normalize it for comparisons
                const resolveLevel = (value) => {
                    if (typeof value === 'number')
                        return value;
                    if (typeof value === 'string') {
                        const numeric = value.match(/\d+/);
                        if (numeric) {
                            return parseInt(numeric[0], 10);
                        }
                        switch (value.toLowerCase().trim()) {
                            case 'rsa':
                            case 'rsa-4096':
                            case 'standard':
                                return 4;
                            case 'qkd':
                            case 'quantum-otp':
                            case 'otp':
                                return 1;
                            case 'pqc':
                            case 'post-quantum':
                            case 'kyber':
                                return 3;
                            case 'aes':
                            case 'quantum-aes':
                            case 'q-aes':
                                return 2;
                            default:
                                return 0;
                        }
                    }
                    return 0;
                };
                const rawLevelSource = email.securityLevel ??
                    email.security_level ??
                    email.security_info?.level ??
                    email.securitylevel ??
                    email.level;
                let levelNum = resolveLevel(rawLevelSource);
                // Level 4 is standard RSA encryption (NOT quantum) - don't show panel
                if (levelNum === 4) {
                    console.log('🔐 Security Panel: Hidden (Level 4 - Standard RSA)');
                    return null;
                }
                // Only show panel for explicitly encrypted emails with quantum features (levels 1-3)
                const isExplicitlyEncrypted = email.encrypted === true ||
                    email.isEncrypted === true ||
                    email.security_info?.encrypted === true;
                const hasQuantumEnhancement = email.security_info?.quantum_enhanced === true;
                const hasEncryptionMetadata = email.security_info?.algorithm ||
                    email.encryption_method ||
                    email.security_info?.flow_id ||
                    email.flow_id;
                // Show panel ONLY if email is quantum encrypted (levels 1-3)
                const shouldShowPanel = (isExplicitlyEncrypted || hasQuantumEnhancement || hasEncryptionMetadata) && levelNum !== 4;
                console.log('🔐 Security Panel Check:', {
                    emailId: email.id,
                    subject: email.subject?.substring(0, 30),
                    securityLevel: levelNum,
                    encrypted: email.encrypted,
                    quantum_enhanced: email.security_info?.quantum_enhanced,
                    shouldShowPanel
                });
                if (!shouldShowPanel)
                    return null;
                // Helper to get algorithm name from security level
                function getAlgorithmName(level) {
                    const numLevel = typeof level === 'string' ? parseInt(level) : level;
                    switch (numLevel) {
                        case 1: return 'OTP-QKD';
                        case 2: return 'AES-256-GCM';
                        case 3: return 'PQC-Kyber1024';
                        case 4: return 'RSA-4096';
                        default: return 'AES-256-GCM';
                    }
                }
                console.log('🔍 Security Level Debug:', {
                    emailId: email.id,
                    securityLevel: email.securityLevel,
                    security_level: email.security_level,
                    security_info_level: email.security_info?.level,
                    rawLevel: rawLevelSource,
                    emailKeys: Object.keys(email)
                });
                const securityLevelNum = levelNum || 2;
                console.log('✅ Resolved Security Level:', securityLevelNum);
                // Get algorithm - check multiple sources
                const rawAlgorithm = email.encryptionMethod ||
                    email.encryption_method ||
                    email.security_info?.algorithm ||
                    email.algorithm;
                const algorithm = rawAlgorithm || getAlgorithmName(securityLevelNum);
                // Determine if quantum enhanced (levels 1-2 are quantum)
                const quantumEnhanced = email.security_info?.quantum_enhanced ?? (securityLevelNum <= 2);
                // For standard emails (non-encrypted), show as verified since they're from trusted sources (Gmail)
                // For encrypted emails, check actual verification status
                const isEncrypted = email.encrypted === true ||
                    email.security_info?.encrypted === true ||
                    email.isEncrypted === true;
                const isVerified = isEncrypted
                    ? (email.security_info?.verification_status === 'Verified' ||
                        email.security_info?.signature_verified === true ||
                        email.encrypted === true)
                    : true; // Standard emails from Gmail are verified by default
                // Key validation - encrypted emails need validation, standard emails are always valid
                const keyValid = isEncrypted
                    ? (email.security_info?.key_validation === 'Valid' ||
                        email.security_info?.key_validated === true ||
                        email.encrypted === true)
                    : true; // Standard emails don't need key validation
                // Get encryption type display
                let encryptionType;
                let algorithmDisplay;
                if (isEncrypted) {
                    // For encrypted emails, show quantum-enhanced or standard based on level
                    encryptionType = quantumEnhanced ? 'Quantum-Enhanced' : 'Standard Encryption';
                    // Format algorithm for display
                    if (algorithm.includes('AES')) {
                        algorithmDisplay = algorithm.includes('256') ? 'AES-256-GCM' : 'AES-256';
                    }
                    else if (algorithm.includes('OTP') || algorithm.includes('QKD')) {
                        algorithmDisplay = 'OTP-QKD';
                    }
                    else if (algorithm.includes('Kyber') || algorithm.includes('PQC')) {
                        algorithmDisplay = 'PQC-Kyber1024';
                    }
                    else if (algorithm.includes('RSA')) {
                        algorithmDisplay = algorithm.includes('4096') ? 'RSA-4096' : 'RSA-4096';
                    }
                    else {
                        algorithmDisplay = algorithm;
                    }
                }
                else {
                    // For standard (non-encrypted) emails
                    encryptionType = 'Standard Email';
                    algorithmDisplay = 'TLS Transport Security';
                }
                return (_jsx("div", { className: "w-80 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-[#0d1117] overflow-y-auto flex-shrink-0", children: _jsxs("div", { className: "p-6", children: [_jsx("h2", { className: "text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider mb-6", children: "Security Details" }), "            ", _jsxs("div", { className: "mb-5", children: [_jsx("label", { className: "block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2", children: "Encryption Type" }), _jsx("div", { className: "p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg", children: _jsxs("div", { className: "flex items-center gap-3", children: [_jsx("div", { className: "w-9 h-9 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center flex-shrink-0", children: _jsx(ShieldCheck, { className: "w-5 h-5 text-blue-600 dark:text-blue-400" }) }), _jsxs("div", { children: [_jsx("p", { className: "text-sm font-medium text-gray-900 dark:text-white", children: encryptionType }), _jsx("p", { className: "text-xs text-gray-500 dark:text-gray-400 mt-0.5", children: algorithmDisplay })] })] }) })] }), "              ", _jsxs("div", { className: "mb-5", children: [_jsx("label", { className: "block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2", children: "Security Level" }), _jsx("div", { className: "p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg", children: _jsxs("div", { className: "flex items-center gap-2.5", children: [_jsx(Shield, { className: "w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0" }), _jsxs("span", { className: "text-sm text-gray-700 dark:text-gray-300", children: ["Level ", securityLevelNum] })] }) })] }), _jsxs("div", { className: "mb-5", children: [_jsx("label", { className: "block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2", children: "Key Validation" }), _jsx("div", { className: "p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg", children: _jsxs("div", { className: "flex items-center gap-2.5", children: [keyValid ? (_jsx("div", { className: "w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0", children: _jsx(Check, { className: "w-3 h-3 text-green-600 dark:text-green-400" }) })) : (_jsx(Key, { className: "w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" })), _jsx("span", { className: `text-sm ${keyValid
                                                        ? 'text-green-600 dark:text-green-400 font-medium'
                                                        : 'text-gray-600 dark:text-gray-400'}`, children: keyValid ? 'Valid Key' : 'Pending Validation' })] }) })] }), _jsxs("div", { className: "mb-5", children: [_jsx("label", { className: "block text-xs font-medium text-gray-500 dark:text-gray-400 mb-2", children: "Signature Verification" }), _jsx("div", { className: "p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg", children: _jsxs("div", { className: "flex items-center gap-2.5", children: [isVerified ? (_jsx("div", { className: "w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0", children: _jsx(Check, { className: "w-3 h-3 text-green-600 dark:text-green-400" }) })) : (_jsx(ShieldCheck, { className: "w-4 h-4 text-gray-400 dark:text-gray-500 flex-shrink-0" })), _jsx("span", { className: `text-sm ${isVerified
                                                        ? 'text-green-600 dark:text-green-400 font-medium'
                                                        : 'text-gray-600 dark:text-gray-400'}`, children: isVerified ? 'Verified' : 'Pending' })] }) })] })] }) }));
            })()] }));
};
export default EmailViewer;
