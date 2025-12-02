import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Reply,
  ReplyAll,
  Forward,
  Trash2,
  Archive,
  Printer,
  Ban,
  MoreHorizontal,
  ShieldCheck,
  Cpu,
} from 'lucide-react';
import SecurityDetails from './SecurityDetails';
import { QuantumEmailViewer } from '../email/QuantumEmailViewer';
import { getAvatarColor } from '../../utils/avatarColors';
import { EMAIL_PLACEHOLDER_HTML, normalizeEmailBody } from '../../utils/emailContent';

// Simplified Email type for UI purposes
interface Email {
  id: string;
  email_id?: string;
  flow_id?: string;
  subject?: string;
  senderName?: string;
  senderEmail?: string;
  senderAvatar?: string;
  timestamp?: string;
  fullDate?: string;
  isEncrypted?: boolean;
  isDecrypted?: boolean;
  securityLevel?: number;
  security_level?: number;
  securityDetails?: any;
  content?: string;
  isStarred?: boolean;
  isUnread?: boolean;
  tags?: string[];
  isRead?: boolean;
  snippet?: string;
  attachments?: any[];
  hashSequence?: string;
  decryptProgress?: number;
  body?: string;
  bodyHtml?: string;
  bodyText?: string;
  html_body?: string;
  plain_body?: string;
  decrypted_body?: string;
  body_encrypted?: string;
  requires_decryption?: boolean;
  decrypt_endpoint?: string;
  security_info?: {
    level?: number;
    algorithm?: string;
    quantum_enhanced?: boolean;
    encrypted_size?: number;
  };
  // Gmail custom headers for QuMail metadata
  customHeaders?: {
    'x-qumail-flow-id'?: string;
    'x-qumail-key-id'?: string;
    'x-qumail-security-level'?: string;
    'x-qumail-algorithm'?: string;
    'x-qumail-auth-tag'?: string;
    'x-qumail-nonce'?: string;
    'x-qumail-salt'?: string;
    'x-qumail-key-fragments'?: string;
    'x-qumail-plaintext-size'?: string;
  };
}

interface EmailViewerProps {
  email: Email | null;
  onReply: () => void;
  onReplyAll: () => void;
  onForward: () => void;
  onDelete: () => void;
  onEmailDecrypted?: (payload: { email_data: any; security_info?: any }) => void;
}

const IconButtonWithTooltip = ({ icon: Icon, label, onClick }: { icon: any; label: string; onClick?: () => void }) => (
  <button
    onClick={onClick}
    className="group relative p-2 hover:bg-gray-100 rounded-full text-gray-500 transition-colors"
  >
    <Icon size={18} />
    <span className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap">
      {label}
    </span>
  </button>
);

export const EmailViewer: React.FC<EmailViewerProps> = ({
  email,
  onReply,
  onReplyAll,
  onForward,
  onDelete,
  onEmailDecrypted,
}) => {
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close more menu on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowMoreMenu(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const normalizedSecurityLevel = useMemo(() => {
    if (!email) return 0;
    return (
      email.securityLevel ??
      email.security_level ??
      email.security_info?.level ??
      0
    );
  }, [email]);

  const securityLevelMeta = useMemo(() => {
    if (!normalizedSecurityLevel) return null;

    const levelMap: Record<number, { label: string; classes: string }> = {
      1: { label: 'Quantum OTP', classes: 'bg-purple-50 text-purple-700 border border-purple-100' },
      2: { label: 'Quantum AES', classes: 'bg-indigo-50 text-indigo-700 border border-indigo-100' },
      3: { label: 'Quantum PQC', classes: 'bg-teal-50 text-teal-700 border border-teal-100' },
      4: { label: 'Standard', classes: 'bg-gray-50 text-gray-700 border border-gray-200' },
    };

    return levelMap[normalizedSecurityLevel] ?? { label: 'Standard', classes: 'bg-gray-50 text-gray-700 border border-gray-200' };
  }, [normalizedSecurityLevel]);

  const { formattedDate, formattedTime } = useMemo(() => {
    if (!email) return { formattedDate: '', formattedTime: '' };

    const rawTimestamp = email.timestamp || email.fullDate || '';
    if (!rawTimestamp) return { formattedDate: '', formattedTime: '' };

    const parsed = new Date(rawTimestamp);
    if (Number.isNaN(parsed.getTime())) {
      return {
        formattedDate: email.fullDate ?? '',
        formattedTime: '',
      };
    }

    return {
      formattedDate: parsed.toLocaleDateString(undefined, {
        month: 'long',
        day: 'numeric',
        year: 'numeric',
      }),
      formattedTime: parsed.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };
  }, [email]);

  const resolvedEmailBody = useMemo(() => {
    if (!email) return EMAIL_PLACEHOLDER_HTML;
    const rawContent =
      email.decrypted_body ??
      email.content ??
      email.bodyHtml ??
      email.html_body ??
      email.body ??
      email.bodyText ??
      email.plain_body ??
      email.snippet ??
      '';

    return normalizeEmailBody(rawContent, EMAIL_PLACEHOLDER_HTML);
  }, [email]);

  // Only show quantum decrypt UI for security levels 1, 2, 3
  // Level 0 = regular email (no encryption)
  // Level 4 = RSA-4096 (hybrid, shows like normal email - decrypted automatically)
  const isQuantumEmail = useMemo(() => {
    if (!email) return false;
    
    // If already decrypted, don't show quantum UI - show normal email view
    if (email.isDecrypted) return false;
    
    // Check if the body contains quantum encryption markers (Gmail HTML template)
    const bodyContent = (email.body ?? email.bodyHtml ?? email.html_body ?? email.content ?? '').toLowerCase();
    const hasQuantumMarkers = 
      bodyContent.includes('quantum-encrypted') ||
      bodyContent.includes('encrypted content (base64 ciphertext)') ||
      bodyContent.includes('quantum otp') ||
      bodyContent.includes('quantum aes') ||
      bodyContent.includes('qkd-etsi') ||
      bodyContent.includes('security level 1') ||
      bodyContent.includes('security level 2') ||
      bodyContent.includes('security level 3') ||
      bodyContent.includes('encryption details');
    
    // Security levels 1-3 require manual decryption via quantum UI
    // Level 4 (RSA-4096) is auto-decrypted and shown like normal email
    // Level 0 is not encrypted at all
    if (normalizedSecurityLevel >= 1 && normalizedSecurityLevel <= 3) {
      const hasEncryptedPayload = typeof email.body_encrypted === 'string' && email.body_encrypted.trim().length > 0;
      const explicitFlag = Boolean(email.requires_decryption);
      const hasFlow = Boolean(email.flow_id);
      
      // Show quantum UI if there's encrypted content OR body has quantum markers
      return hasEncryptedPayload || explicitFlag || hasFlow || hasQuantumMarkers;
    }
    
    // Also show quantum UI if body contains quantum markers even without security level
    if (hasQuantumMarkers) {
      return true;
    }
    
    return false;
  }, [email, normalizedSecurityLevel]);

  if (!email) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">Select an email to view</div>
    );
  }

  if (isQuantumEmail) {
    // Check if already decrypted (from cache or previous session)
    const alreadyDecrypted = email.isDecrypted === true || Boolean(email.decrypted_body);
    
    // Try to extract metadata from customHeaders first (Gmail X-QuMail-* headers)
    const customHeaders = email.customHeaders || {};
    
    // Try to extract flow_id from customHeaders, then email body if not already set
    let flowId = customHeaders['x-qumail-flow-id'] || email.flow_id || '';
    let encryptedBody = email.body_encrypted ?? '';
    let detectedSecurityLevel = parseInt(customHeaders['x-qumail-security-level'] || '') || normalizedSecurityLevel;
    
    // Parse the Gmail HTML template to extract flow_id and ciphertext
    const bodyContent = email.body ?? email.bodyHtml ?? email.html_body ?? email.content ?? '';
    
    if (!flowId && bodyContent) {
      // Extract flow_id from HTML body
      const flowIdMatch = bodyContent.match(/Flow ID[:\s]*([a-f0-9-]+)/i);
      if (flowIdMatch) {
        flowId = flowIdMatch[1];
      }
    }
    
    if (!encryptedBody && bodyContent) {
      // Extract ciphertext from HTML body (between ENCRYPTED CONTENT markers)
      const cipherMatch = bodyContent.match(/BASE64 CIPHERTEXT[^>]*>([^<]+)/i) ||
                         bodyContent.match(/<code[^>]*>([A-Za-z0-9+/=\s]+)<\/code>/i) ||
                         bodyContent.match(/([A-Za-z0-9+/]{50,}={0,2})/);
      if (cipherMatch) {
        encryptedBody = cipherMatch[1].replace(/\s+/g, '');
      }
    }
    
    // Detect security level from body if not set
    if (!detectedSecurityLevel && bodyContent) {
      if (bodyContent.toLowerCase().includes('security level 1') || bodyContent.toLowerCase().includes('level 1')) {
        detectedSecurityLevel = 1;
      } else if (bodyContent.toLowerCase().includes('security level 2') || bodyContent.toLowerCase().includes('level 2')) {
        detectedSecurityLevel = 2;
      } else if (bodyContent.toLowerCase().includes('security level 3') || bodyContent.toLowerCase().includes('level 3')) {
        detectedSecurityLevel = 3;
      }
    }
    
    const quantumEmail = {
      email_id: email.email_id ?? email.id,
      flow_id: flowId,
      sender_email: email.senderEmail ?? '',
      receiver_email: 'me',
      subject: email.subject ?? '(No Subject)',
      body_encrypted: encryptedBody,
      // Pass decrypted body if available
      decrypted_body: email.decrypted_body ?? undefined,
      security_level: detectedSecurityLevel || 1,
      timestamp: email.timestamp ?? new Date().toISOString(),
      is_read: Boolean(email.isRead),
      is_starred: Boolean(email.isStarred),
      // Only require decryption if not already decrypted
      requires_decryption: !alreadyDecrypted,
      decrypt_endpoint: email.decrypt_endpoint ?? `/api/v1/emails/email/${email.email_id ?? email.id}/decrypt`,
      security_info: {
        level: email.security_info?.level ?? detectedSecurityLevel ?? 1,
        algorithm: email.security_info?.algorithm ?? 'Unknown',
        quantum_enhanced: email.security_info?.quantum_enhanced ?? true,
        encrypted_size: email.security_info?.encrypted_size ?? encryptedBody.length ?? 0,
      },
      encryption_metadata: email.security_info,
      // Pass custom headers from Gmail for direct decrypt
      custom_headers: email.customHeaders,
    };

    return (
      <QuantumEmailViewer
        email={quantumEmail}
        onDecrypted={(result) => onEmailDecrypted?.(result)}
      />
    );
  }

  return (
    <div className="flex-1 h-full overflow-hidden">
      <div className="h-full flex flex-col bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Sticky Toolbar */}
        <div className="px-8 py-4 border-b border-gray-100 flex items-center justify-between bg-white flex-shrink-0">
          <div className="flex items-center gap-1 text-gray-500">
            <IconButtonWithTooltip icon={Trash2} label="Delete" onClick={onDelete} />
            <IconButtonWithTooltip icon={Archive} label="Archive" onClick={onReply} />
            <IconButtonWithTooltip icon={Ban} label="Spam" onClick={onDelete} />
            <div className="w-px h-6 bg-gray-200 mx-4" />
            <IconButtonWithTooltip icon={Printer} label="Print" />
            <div className="relative" ref={menuRef}>
              <IconButtonWithTooltip
                icon={MoreHorizontal}
                label="More"
                onClick={() => setShowMoreMenu(!showMoreMenu)}
              />
              {showMoreMenu && (
                <div className="absolute left-0 top-full mt-2 w-48 bg-white rounded-2xl shadow-xl border border-gray-200 z-50 py-1">
                  <button className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors" onClick={() => setShowMoreMenu(false)}>
                    <Reply size={14} className="text-gray-400" /> Reply
                  </button>
                  <button className="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 flex items-center gap-3 transition-colors" onClick={() => setShowMoreMenu(false)}>
                    <Forward size={14} className="text-gray-400" /> Forward
                  </button>
                </div>
              )}
            </div>
          </div>
          {securityLevelMeta && (
            <div
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold tracking-tight ${securityLevelMeta.classes}`}
            >
              <ShieldCheck size={14} className="text-current" />
              <span>{`${securityLevelMeta.label} (Level ${normalizedSecurityLevel})`}</span>
            </div>
          )}
        </div>

        {/* Email Header */}
        <div className="px-8 py-6 border-b border-gray-100 space-y-6">
          <div className="flex items-start justify-between gap-6">
            <h1 className="text-2xl font-semibold text-gray-900 leading-tight tracking-tight">
              {email.subject ?? '(No Subject)'}
            </h1>
          </div>

          <div className="flex items-start justify-between gap-4">
            <div className="flex items-center gap-4">
              <div
                className={`w-12 h-12 rounded-2xl flex items-center justify-center text-lg font-semibold text-white shadow-sm ${getAvatarColor(email.senderName ?? '')}`}
              >
                {(email.senderName?.[0] ?? '?').toUpperCase()}
              </div>
              <div>
                <div className="flex flex-wrap items-baseline gap-2 text-gray-900">
                  <span className="font-semibold text-base">{email.senderName || 'Unknown Sender'}</span>
                  {email.senderEmail && (
                    <span className="text-sm text-gray-500">&lt;{email.senderEmail}&gt;</span>
                  )}
                </div>
                <p className="text-xs text-gray-500 mt-1">To: Me</p>
              </div>
            </div>
            <div className="text-right text-sm text-gray-600">
              {formattedDate && <p className="font-semibold text-gray-900">{formattedDate}</p>}
              {formattedTime && <p className="text-xs text-gray-500">{formattedTime}</p>}
            </div>
          </div>
        </div>

        {/* Email Body */}
        <div className="flex-1 overflow-y-auto px-8 py-8">
          {email.isEncrypted && !email.isDecrypted ? (
          <div className="relative m-8 bg-gray-50/50 rounded-lg border border-gray-200 flex flex-col items-center justify-center overflow-hidden shadow-inner">
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage:
                  'linear-gradient(#4f46e5 1px, transparent 1px), linear-gradient(90deg, #4f46e5 1px, transparent 1px)',
                backgroundSize: '20px 20px',
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/40 to-white/80" />
            <div className="w-full max-w-xs relative z-10 text-center">
              <div className="relative w-16 h-16 mx-auto mb-6">
                <div className="absolute inset-0 bg-indigo-100 rounded-full animate-ping" />
                <div className="relative bg-white rounded-full w-16 h-16 flex items-center justify-center border border-indigo-100 shadow-sm">
                  <Cpu size={32} className="text-indigo-600 animate-pulse" />
                </div>
              </div>
              <h2 className="text-indigo-900 font-bold text-sm tracking-wider mb-2">ESTABLISHING SECURE LINK</h2>
              <div className="font-mono text-[10px] text-indigo-600/60 h-4 mb-4 tracking-widest">{email.hashSequence ?? ''}</div>
              <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden w-full">
                <div
                  className="h-full bg-indigo-600 shadow-[0_0_8px_rgba(79,70,229,0.4)] transition-all duration-75 ease-out"
                  style={{ width: `${email.decryptProgress ?? 0}%` }}
                />
              </div>
              <button
                onClick={onReply}
                className="group bg-indigo-600 text-white hover:bg-indigo-700 px-6 py-2.5 rounded-lg text-sm font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all flex items-center gap-2 mx-auto mt-4"
              >
                <span>Decrypt Message</span>
                <ShieldCheck size={16} className="text-indigo-200 group-hover:text-white group-hover:scale-110 transition-all" />
              </button>
            </div>
          </div>
          ) : (
            <article className="email-content-wrapper">
              <div
                className="email-html-content prose max-w-none text-gray-800 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: resolvedEmailBody }}
              />
            </article>
          )}
          {email.securityDetails && <SecurityDetails email={email} />}

          <div className="px-8 py-6 mt-8 border-t border-gray-100 flex flex-wrap items-center justify-end gap-3 bg-white">
            <button className="px-4 py-2 rounded-xl border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 flex items-center gap-2 transition-all" onClick={onReply}>
              <Reply size={16} /> Reply
            </button>
            <button className="px-4 py-2 rounded-xl border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 flex items-center gap-2 transition-all" onClick={onReplyAll}>
              <ReplyAll size={16} /> Reply All
            </button>
            <button className="px-4 py-2 rounded-xl border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 flex items-center gap-2 transition-all" onClick={onForward}>
              <Forward size={16} /> Forward
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmailViewer;
