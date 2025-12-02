import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Shield, Lock, AlertTriangle, CheckCircle, Clock, Paperclip, Download, ShieldCheck, Cpu, Key, Smartphone } from 'lucide-react';
import { emailService } from '../../services/emailService';
import { decryptAuthService } from '../../services/decryptAuthService';
import { EMAIL_PLACEHOLDER_HTML, normalizeEmailBody } from '../../utils/emailContent';

type DecryptStage = 'locked' | 'decrypting' | 'totp_required' | 'verifying_totp' | 'decrypted';

// Module-level Set to track decrypted emails in this browser session
// This persists across component re-renders and re-mounts
const sessionDecryptedEmails = new Set<string>();

interface QuantumEmailViewerProps {
  email: {
    email_id: string;
    flow_id: string;
    sender_email: string;
    receiver_email: string;
    subject: string;
    body_encrypted: string;
    decrypted_body?: string;  // Already decrypted content from parent/cache
    security_level: number;
    timestamp: string;
    is_read: boolean;
    is_starred: boolean;
    requires_decryption: boolean;
    decrypt_endpoint: string;
    security_info: {
      level: number;
      algorithm: string;
      quantum_enhanced: boolean;
      encrypted_size?: number;
      verification_status?: string;
      signature_verified?: boolean;
    };
    encryption_metadata?: any;
    // Additional fields from Gmail headers for direct decrypt
    custom_headers?: {
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
  };
  onDecrypted?: (decryptedEmail: any) => void;
}

interface DecryptedAttachment {
  filename: string;
  content: string;
  mime_type: string;
  size: number;
}

// TOTP Input Component for Google Authenticator verification
// Memoized to prevent re-renders during parent state changes
const TOTPInput: React.FC<{
  onSubmit: (code: string) => void;
  isVerifying: boolean;
  error: string | null;
}> = React.memo(({ onSubmit, isVerifying, error }) => {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return; // Only digits
    
    const newCode = [...code];
    newCode[index] = value.slice(-1); // Only last digit
    setCode(newCode);
    
    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
    
    // Auto-submit when all 6 digits entered
    if (newCode.every(d => d !== '') && index === 5) {
      onSubmit(newCode.join(''));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newCode = [...code];
    for (let i = 0; i < pasted.length; i++) {
      newCode[i] = pasted[i];
    }
    setCode(newCode);
    if (pasted.length === 6) {
      onSubmit(pasted);
    }
  };

  return (
    <div className="text-center totp-input-stable">
      <div className="w-16 h-16 bg-indigo-100 rounded-2xl flex items-center justify-center mb-4 mx-auto">
        <Smartphone className="w-8 h-8 text-indigo-600" />
      </div>
      
      <h3 className="text-lg font-bold text-gray-900 mb-2">Enter Authenticator Code</h3>
      <p className="text-gray-500 text-sm mb-6">
        Open Google Authenticator and enter the 6-digit code for QuMail
      </p>
      
      <div className="flex justify-center gap-2 mb-4">
        {code.map((digit, index) => (
          <input
            key={index}
            ref={el => inputRefs.current[index] = el}
            type="text"
            inputMode="numeric"
            maxLength={1}
            value={digit}
            onChange={e => handleChange(index, e.target.value)}
            onKeyDown={e => handleKeyDown(index, e)}
            onPaste={handlePaste}
            disabled={isVerifying}
            className={`totp-digit-input w-12 h-14 text-center text-2xl font-bold border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500
              ${error ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'}
              ${isVerifying ? 'opacity-60' : ''}
            `}
          />
        ))}
      </div>
      
      {/* Fixed height container for error/verifying states to prevent layout shift */}
      <div className="h-8 flex items-center justify-center">
        {error ? (
          <p className="text-red-600 text-sm">{error}</p>
        ) : isVerifying ? (
          <div className="flex items-center justify-center gap-2 text-indigo-600">
            <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full totp-verify-spin" />
            <span className="text-sm">Verifying...</span>
          </div>
        ) : null}
      </div>
      
      <p className="text-xs text-gray-400 mt-4">
        Code refreshes every 30 seconds
      </p>
    </div>
  );
});

const SecurityLevelBadge: React.FC<{ level: number; quantumEnhanced: boolean }> = ({ 
  level, 
  quantumEnhanced 
}) => {
  const getSecurityColor = (level: number) => {
    switch (level) {
      case 1: return 'bg-red-100 text-red-800 border-red-200';
      case 2: return 'bg-orange-100 text-orange-800 border-orange-200';
      case 3: return 'bg-blue-100 text-blue-800 border-blue-200';
      case 4: return 'bg-purple-100 text-purple-800 border-purple-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getSecurityName = (level: number) => {
    switch (level) {
      case 1: return 'QKD-OTP';
      case 2: return 'QKD-AES';
      case 3: return 'QKD-PQC';
      case 4: return 'QKD-RSA';
      default: return 'Unknown';
    }
  };

  return (
    <div className={`inline-flex items-center px-3 py-1 rounded-lg border text-sm font-medium ${getSecurityColor(level)}`}>
      <Shield className="w-4 h-4 mr-2" />
      Level {level}: {getSecurityName(level)}
      {quantumEnhanced && (
        <span className="ml-2 px-2 py-0.5 bg-green-200 text-green-800 rounded text-xs">
          Quantum Enhanced
        </span>
      )}
    </div>
  );
};

// Helper function to compute initial state SYNCHRONOUSLY
// This prevents the brief flash of decrypt button or TOTP when switching emails
const getInitialState = (email: QuantumEmailViewerProps['email']): {
  stage: DecryptStage;
  content: any | null;
  info: any | null;
} => {
  // If parent provided decrypted content
  if (email.decrypted_body && !email.requires_decryption) {
    sessionDecryptedEmails.add(email.email_id);
    return { stage: 'decrypted', content: { body: email.decrypted_body }, info: null };
  }
  
  // If already decrypted in this session, check cache
  if (sessionDecryptedEmails.has(email.email_id)) {
    const cacheKey = `qumail_decrypted_${email.email_id}`;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const cachedData = JSON.parse(cached);
        
        // Check TOTP session SYNCHRONOUSLY
        // If valid TOTP session exists, go straight to decrypted
        const hasValidSession = decryptAuthService.hasValidTOTPSession(email.email_id);
        
        if (hasValidSession) {
          // Valid TOTP session - show decrypted content immediately
          return { 
            stage: 'decrypted', 
            content: cachedData.content, 
            info: cachedData.security_info || null 
          };
        }
        
        // No valid session - will need to check if TOTP is required async
        // Default to 'totp_required' to prevent flash of decrypt button
        // The useEffect will correct this to 'decrypted' if TOTP not enabled
        return { 
          stage: 'totp_required', 
          content: cachedData.content, 
          info: cachedData.security_info || null 
        };
      }
    } catch (e) {
      console.warn('Failed to load cached content in initial state:', e);
    }
  }
  
  // Not decrypted - show locked
  return { stage: 'locked', content: null, info: null };
};

export const QuantumEmailViewer: React.FC<QuantumEmailViewerProps> = ({ 
  email, 
  onDecrypted 
}) => {
  // Compute initial state SYNCHRONOUSLY to prevent flash of wrong UI
  const initialState = getInitialState(email);
  
  const [stage, setStage] = useState<DecryptStage>(initialState.stage);
  const [decryptedContent, setDecryptedContent] = useState<any | null>(initialState.content);
  const [decryptionInfo, setDecryptionInfo] = useState<any | null>(initialState.info);
  const [error, setError] = useState<string | null>(null);
  const [totpError, setTotpError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [hashSequence, setHashSequence] = useState('');
  const [_totpSetup, setTotpSetup] = useState<boolean | null>(null);
  const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Track the email ID to detect when we switch emails
  const currentEmailIdRef = useRef(email.email_id);

  // Helper to get cache key for this email
  const getCacheKey = useCallback((emailId: string) => `qumail_decrypted_${emailId}`, []);

  const stopProgressAnimation = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  }, []);

  const startProgressAnimation = useCallback(() => {
    stopProgressAnimation();
    // Use a smoother progress animation with larger intervals
    progressIntervalRef.current = setInterval(() => {
      setProgress(prev => {
        if (prev >= 96) {
          return prev;
        }
        // Smoother increment with less frequent updates
        const increment = 1.5 + Math.random() * 1.5;
        return Math.min(prev + increment, 96);
      });
    }, 50); // 50ms instead of 18ms for smoother visual
  }, [stopProgressAnimation]);

  useEffect(() => {
    console.log('📩 QuantumEmailViewer received email:', {
      email_id: email.email_id,
      flow_id: email.flow_id,
      security_level: email.security_level,
      security_info: email.security_info,
      encryption_metadata: email.encryption_metadata,
      body_encrypted_length: email.body_encrypted?.length
    })
  }, [email])

  // Combined initialization - handles email switching and TOTP validation
  useEffect(() => {
    let cancelled = false;
    
    // Detect if we switched emails - if so, SYNCHRONOUSLY reset state
    if (currentEmailIdRef.current !== email.email_id) {
      currentEmailIdRef.current = email.email_id;
      
      // Synchronously compute and apply the new state for this email
      const newState = getInitialState(email);
      setStage(newState.stage);
      setDecryptedContent(newState.content);
      setDecryptionInfo(newState.info);
      setError(null);
      setProgress(0);
      setHashSequence('');
      stopProgressAnimation();
    }
    
    const initialize = async () => {
      // CASE 1: Parent provided already decrypted content
      if (email.decrypted_body && !email.requires_decryption) {
        console.log('✅ Using decrypted_body from parent for email:', email.email_id);
        setDecryptedContent({ body: email.decrypted_body });
        setError(null);
        setStage('decrypted');
        sessionDecryptedEmails.add(email.email_id);
        return;
      }
      
      // CASE 2: Check if decrypted in THIS SESSION (module-level Set)
      const wasDecryptedThisSession = sessionDecryptedEmails.has(email.email_id);
      console.log('📧 Email session check:', email.email_id, 'decrypted:', wasDecryptedThisSession);
      
      if (wasDecryptedThisSession) {
        // User already decrypted this email in current session
        // Content already loaded synchronously in getInitialState
        // Just need to check TOTP status
        
        // Check TOTP requirement
        try {
          const status = await decryptAuthService.getStatus();
          if (cancelled) return;
          
          setTotpSetup(status.totp_verified);
          
          if (status.totp_verified && !decryptAuthService.hasValidTOTPSession(email.email_id)) {
            // TOTP enabled but session expired (>5 min) - require verification
            // Stage is already 'totp_required' from getInitialState
            console.log('🔐 TOTP session expired, requiring verification');
            setStage('totp_required');
          } else {
            // No TOTP or valid session - show content directly
            console.log('✅ Valid TOTP session or no TOTP, showing content');
            setError(null);
            setStage('decrypted');
          }
        } catch (e) {
          console.warn('Failed to check TOTP status:', e);
          if (!cancelled) {
            // Default to showing decrypted content if TOTP check fails
            setStage('decrypted');
          }
        }
        return;
      }
      
      // CASE 3: Never decrypted this session → Stage is already 'locked' from getInitialState
      console.log('🔒 Email not decrypted in session, showing decrypt button');
      
      // Preload TOTP status in background
      try {
        const status = await decryptAuthService.getStatus();
        if (!cancelled) {
          setTotpSetup(status.totp_verified);
        }
      } catch (e) {
        console.warn('Failed to check TOTP status:', e);
        if (!cancelled) setTotpSetup(false);
      }
    };
    
    initialize();
    
    return () => {
      cancelled = true;
    };
  }, [email.email_id, email.decrypted_body, email.requires_decryption, getCacheKey, stopProgressAnimation]);

  // Hash sequence animation - smoother and less frequent updates
  useEffect(() => {
    if (stage !== 'decrypting') return;

    const chars = '0123456789ABCDEF';
    // Generate initial hash immediately
    let initial = '';
    for (let i = 0; i < 24; i++) {
      initial += chars.charAt(Math.floor(Math.random() * chars.length));
      if ((i + 1) % 4 === 0 && i !== 23) {
        initial += ' ';
      }
    }
    setHashSequence(initial);
    
    // Update less frequently (200ms instead of 80ms) to reduce flicker
    const interval = setInterval(() => {
      let next = '';
      for (let i = 0; i < 24; i++) {
        next += chars.charAt(Math.floor(Math.random() * chars.length));
        if ((i + 1) % 4 === 0 && i !== 23) {
          next += ' ';
        }
      }
      setHashSequence(next);
    }, 200);

    return () => clearInterval(interval);
  }, [stage]);

  useEffect(() => () => stopProgressAnimation(), [stopProgressAnimation]);

  // Handle TOTP verification
  const handleTotpVerify = useCallback(async (code: string) => {
    setStage('verifying_totp');
    setTotpError(null);
    
    try {
      const result = await decryptAuthService.verifyDecryptTOTP(code, email.email_id);
      
      if (result.success) {
        // TOTP verified - show decrypted content
        setStage('decrypted');
        // Notify parent
        if (onDecrypted && decryptedContent) {
          onDecrypted({ 
            success: true, 
            email_data: decryptedContent, 
            security_info: decryptionInfo,
            from_cache: true 
          });
        }
      } else {
        setTotpError('Invalid code. Please try again.');
        setStage('totp_required');
      }
    } catch (err: any) {
      setTotpError(err.message || 'Verification failed');
      setStage('totp_required');
    }
  }, [email.email_id, decryptedContent, decryptionInfo, onDecrypted]);

  const handleDecrypt = useCallback(async () => {
    if (stage === 'decrypted') {
      // Already decrypted, just toggle view
      return;
    }

    setStage('decrypting');
    setError(null);
    setProgress(0);
    setHashSequence('');
    startProgressAnimation();

    try {
      // Extract metadata from email headers or encryption_metadata
      const headers = email.custom_headers || {};
      const metadata = email.encryption_metadata || {};
      
      const flowId = headers['x-qumail-flow-id'] || email.flow_id || metadata.flow_id;
      const keyId = headers['x-qumail-key-id'] || metadata.key_id;
      const securityLevel = parseInt(headers['x-qumail-security-level'] || '') || email.security_level || metadata.security_level || 1;
      const algorithm = headers['x-qumail-algorithm'] || metadata.algorithm;
      const authTag = headers['x-qumail-auth-tag'] || metadata.auth_tag;
      const nonce = headers['x-qumail-nonce'] || metadata.nonce;
      const salt = headers['x-qumail-salt'] || metadata.salt;
      const keyFragmentsRaw = headers['x-qumail-key-fragments'] || metadata.key_fragments;
      const plaintextSize = parseInt(headers['x-qumail-plaintext-size'] || '') || metadata.required_size || metadata.plaintext_size;
      
      // Parse key fragments
      let keyFragments: string[] = [];
      if (keyFragmentsRaw) {
        if (Array.isArray(keyFragmentsRaw)) {
          keyFragments = keyFragmentsRaw.map(String);
        } else if (typeof keyFragmentsRaw === 'string') {
          try {
            keyFragments = JSON.parse(keyFragmentsRaw);
          } catch {
            keyFragments = keyFragmentsRaw.split(',').map((s: string) => s.trim());
          }
        }
      }
      if (!keyFragments.length && keyId) {
        keyFragments = [keyId];
      }

      // Get ciphertext from body
      const ciphertext = email.body_encrypted || metadata.ciphertext || '';
      
      if (!ciphertext) {
        throw new Error('No encrypted content found');
      }

      // Extract Level 3 PQC-specific fields from metadata
      const kemCiphertext = metadata.kem_ciphertext || metadata.kyber_ciphertext;
      const kemSecretKey = metadata.kem_secret_key || metadata.kyber_private_key;
      const kemPublicKey = metadata.kem_public_key || metadata.kyber_public_key;
      const dsaPublicKey = metadata.dsa_public_key || metadata.dilithium_public_key;
      const signature = metadata.signature;
      const quantumEnhancement = metadata.quantum_enhancement;

      // Try direct decrypt first (uses headers/metadata, no MongoDB)
      let response;
      try {
        response = await emailService.decryptEmailDirect({
          ciphertext,
          flow_id: flowId,
          key_id: keyId,
          key_fragments: keyFragments,
          security_level: securityLevel,
          algorithm,
          auth_tag: authTag,
          nonce,
          salt,
          plaintext_size: plaintextSize,
          subject: email.subject,
          sender_email: email.sender_email,
          // Level 3 PQC-specific fields
          kem_ciphertext: kemCiphertext,
          kem_secret_key: kemSecretKey,
          kem_public_key: kemPublicKey,
          dsa_public_key: dsaPublicKey,
          signature: signature,
          quantum_enhancement: quantumEnhancement
        });
      } catch (directError) {
        console.warn('Direct decrypt failed, falling back to legacy method:', directError);
        // Fall back to legacy endpoint
        response = await emailService.decryptEmail(email.email_id);
      }
      
      if (response.success) {
        const enrichedData = {
          ...response.email_data,
          security_level: response.security_info?.security_level ?? response.email_data.security_level ?? email.security_level,
          algorithm: response.security_info?.algorithm ?? response.email_data.algorithm ?? email.security_info.algorithm,
          verification_status: response.security_info?.verification_status ?? response.email_data.verification_status,
          quantum_enhanced: response.security_info?.quantum_enhanced ?? response.email_data.quantum_enhanced ?? email.security_info.quantum_enhanced,
          flow_id: response.email_data.flow_id ?? email.flow_id,
          encrypted_size: response.security_info?.encrypted_size ?? response.email_data.encrypted_size ?? (email.body_encrypted ? email.body_encrypted.length : undefined)
        };

        setDecryptedContent(enrichedData);
        setDecryptionInfo(response.security_info ?? null);
        
        // Mark as decrypted in this session (module-level Set persists across re-renders)
        sessionDecryptedEmails.add(email.email_id);
        
        // Cache decrypted content in localStorage
        try {
          const cacheKey = getCacheKey(email.email_id);
          localStorage.setItem(cacheKey, JSON.stringify({
            content: enrichedData,
            security_info: response.security_info,
            cached_at: new Date().toISOString()
          }));
          console.log('💾 Cached decrypted content for email:', email.email_id);
        } catch (cacheError) {
          console.warn('Failed to cache decrypted content:', cacheError);
        }
        
        setProgress(100);
        
        // After successful decrypt, check if TOTP is enabled
        // If enabled, show TOTP input immediately (don't show content yet)
        try {
          const status = await decryptAuthService.getStatus();
          if (status.totp_verified) {
            // TOTP is enabled - require verification before showing content
            console.log('🔐 TOTP enabled, requiring verification after decrypt');
            setStage('totp_required');
          } else {
            // No TOTP - show content directly
            onDecrypted?.({ ...response, email_data: enrichedData });
            setStage('decrypted');
          }
        } catch (e) {
          // On error checking TOTP, just show content
          console.warn('Failed to check TOTP status after decrypt:', e);
          onDecrypted?.({ ...response, email_data: enrichedData });
          setStage('decrypted');
        }
      } else {
        setError('Failed to decrypt email');
        setStage('locked');
      }
    } catch (err: any) {
      console.error('Decryption error:', err);
      setError(err.message || 'Failed to decrypt email');
      setStage('locked');
    } finally {
      stopProgressAnimation();
    }
  }, [email, stage, onDecrypted, startProgressAnimation, stopProgressAnimation, getCacheKey]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const resolvedSecurityLevel = decryptedContent?.security_level ?? email.security_level ?? 0;
  const resolvedAlgorithm = decryptedContent?.algorithm ?? email.security_info?.algorithm ?? getAlgorithmName(email.security_level);
  const resolvedQuantumEnhanced =
    decryptedContent?.quantum_enhanced ?? email.security_info?.quantum_enhanced ?? true;
  const resolvedVerification =
    decryptedContent?.verification_status ?? decryptionInfo?.verification_status ?? 'Pending';
  const resolvedFlowId = decryptedContent?.flow_id ?? email.flow_id ?? email.encryption_metadata?.flow_id ?? 'N/A';
  
  // Extract Key ID from multiple possible sources
  const getKeyId = (): string => {
    // Direct key_id field
    const directKeyId = decryptedContent?.key_id ?? 
                        email.encryption_metadata?.key_id ?? 
                        email.custom_headers?.['x-qumail-key-id'];
    if (directKeyId) return directKeyId;
    
    // From quantum_enhancement key_ids (Level 3 PQC)
    const quantumKeyIds = decryptedContent?.quantum_enhancement?.key_ids ?? 
                          email.encryption_metadata?.quantum_enhancement?.key_ids;
    if (quantumKeyIds?.km1) return quantumKeyIds.km1;
    
    // From key_fragments array (Level 1/2)
    const keyFragments = decryptedContent?.key_fragments ?? 
                         email.encryption_metadata?.key_fragments;
    if (keyFragments && keyFragments.length > 0) {
      return Array.isArray(keyFragments) ? keyFragments[0] : keyFragments;
    }
    
    // Fallback to flow_id (it's also a unique identifier)
    if (resolvedFlowId && resolvedFlowId !== 'N/A') return resolvedFlowId;
    
    return 'N/A';
  };
  // resolvedKeyId used for display purposes
  const _resolvedKeyId = getKeyId();
  void _resolvedKeyId; // Suppress unused warning
  
  // Calculate encrypted size with multiple fallbacks
  const encryptedSize = 
    decryptedContent?.encrypted_size ??
    email.security_info?.encrypted_size ??
    email.encryption_metadata?.encrypted_size ??
    (email.body_encrypted && typeof email.body_encrypted === 'string' ? email.body_encrypted.length : 0);

  // Helper function to get algorithm name from security level
  function getAlgorithmName(level: number): string {
    switch (level) {
      case 1: return 'Quantum Secure OTP';
      case 2: return 'AES-256-GCM';
      case 3: return 'PQC-Kyber1024';
      case 4: return 'RSA-4096';
      default: return 'Unknown';
    }
  }

  const formatDecryptedBody = (body: string | undefined) => normalizeEmailBody(body, EMAIL_PLACEHOLDER_HTML)

  // Format security level display
  const securityLevelDisplay = `${resolvedSecurityLevel} - ${resolvedAlgorithm}`;

  console.log('🎯 QuantumEmailViewer resolved display values:', {
    resolvedSecurityLevel,
    resolvedAlgorithm,
    resolvedFlowId,
    encryptedSize,
    securityLevelDisplay,
    sources: {
      decryptedContent_encrypted_size: decryptedContent?.encrypted_size,
      security_info_encrypted_size: email.security_info?.encrypted_size,
      encryption_metadata_encrypted_size: email.encryption_metadata?.encrypted_size,
      body_encrypted_length: email.body_encrypted?.length
    }
  })

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm">
      {/* Email Header */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <SecurityLevelBadge 
                level={resolvedSecurityLevel} 
                quantumEnhanced={resolvedQuantumEnhanced}
              />
              <span className="text-sm text-gray-500">
                Flow ID: {resolvedFlowId}
              </span>
            </div>
            
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              {email.subject}
            </h2>
            
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>From: <strong>{email.sender_email}</strong></span>
              <span>To: <strong>{email.receiver_email}</strong></span>
              <span className="flex items-center gap-1">
                <Clock className="w-4 h-4" />
                {formatTimestamp(email.timestamp)}
              </span>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800">
            <AlertTriangle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* Email Content */}
      <div className="p-6">
        {stage === 'decrypted' && decryptedContent ? (
          <div className="space-y-6">
            <div className="bg-indigo-50 border border-indigo-100 rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-indigo-100 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-indigo-900">Secure Connection Established</p>
                <p className="text-xs text-indigo-700">Decrypted via {resolvedAlgorithm}</p>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-6">
              <div
                className="prose prose-sm max-w-none text-gray-900 [&>*]:text-gray-900 [&_strong]:font-semibold [&_em]:italic [&_p]:leading-relaxed [&_p]:mb-4"
                dangerouslySetInnerHTML={{ __html: formatDecryptedBody(decryptedContent.body) }}
              />
            </div>

            <div className="rounded-2xl border border-gray-200 bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between text-xs font-semibold text-gray-500 uppercase tracking-[0.2em]">
                <span>Security Verification</span>
                <span>{resolvedFlowId}</span>
              </div>
              <div className="grid gap-4 mt-4 md:grid-cols-2">
                <div className="flex items-center gap-4 rounded-xl border border-gray-200 p-4">
                  <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center">
                    <Shield className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Encryption Protocol</p>
                    <p className="text-sm font-semibold text-gray-900">Quantum-Aided {resolvedAlgorithm.includes('AES') ? 'AES (Level 2)' : resolvedAlgorithm}</p>
                    <p className="text-xs text-gray-500">{resolvedAlgorithm} • QKD Layer</p>
                  </div>
                </div>
                <div className="flex items-center gap-4 rounded-xl border border-gray-200 p-4">
                  <div className="w-12 h-12 rounded-2xl bg-emerald-50 flex items-center justify-center">
                    <CheckCircle className="w-5 h-5 text-emerald-600" />
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Digital Signature</p>
                    <p className="text-sm font-semibold text-gray-900">{resolvedVerification}</p>
                    <p className="text-xs text-gray-500"> </p>
                  </div>
                </div>
              </div>
            </div>

            {decryptedContent.attachments && decryptedContent.attachments.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Paperclip className="w-5 h-5 text-gray-600" />
                  <h3 className="text-sm font-semibold text-gray-800">
                    Attachments ({decryptedContent.attachments.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {decryptedContent.attachments.map((attachment: DecryptedAttachment, index: number) => {
                    const handleDownload = () => {
                      try {
                        const byteCharacters = atob(attachment.content);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {
                          byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], { type: attachment.mime_type });
                        const url = window.URL.createObjectURL(blob);
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = attachment.filename;
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        window.URL.revokeObjectURL(url);
                      } catch (error) {
                        console.error('Error downloading attachment:', error);
                      }
                    };

                    const formatFileSize = (bytes: number) => {
                      if (bytes < 1024) return bytes + ' B';
                      if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
                      return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
                    };

                    return (
                      <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <Paperclip className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-gray-900 truncate">
                              {attachment.filename}
                            </div>
                            <div className="text-xs text-gray-500">
                              {formatFileSize(attachment.size)} • {attachment.mime_type}
                            </div>
                          </div>
                        </div>
                        <button
                          onClick={handleDownload}
                          className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors flex-shrink-0"
                        >
                          <Download className="w-4 h-4" />
                          Download
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="relative min-h-[420px] rounded-2xl border border-gray-200 bg-gray-50/60 shadow-inner overflow-hidden flex items-center justify-center">
            <div
              className="absolute inset-0 opacity-[0.03]"
              style={{
                backgroundImage: 'linear-gradient(#4f46e5 1px, transparent 1px), linear-gradient(90deg, #4f46e5 1px, transparent 1px)',
                backgroundSize: '20px 20px'
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/40 to-white/80" />

            <div className="relative z-10 w-full px-8">
              {stage === 'decrypting' ? (
                <div className="w-full max-w-xs mx-auto text-center decrypt-progress-stable">
                  <div className="relative w-16 h-16 mx-auto mb-6">
                    <div className="absolute inset-0 bg-indigo-50 rounded-full opacity-60"></div>
                    <div className="relative bg-white rounded-full w-16 h-16 flex items-center justify-center border border-indigo-100 shadow-sm">
                      <Cpu size={32} className="text-indigo-600 decrypt-icon-spin" />
                    </div>
                  </div>

                  <h2 className="text-indigo-900 font-bold text-sm tracking-wider mb-2">
                    DECRYPTING MESSAGE
                  </h2>
                  <p className="text-xs text-gray-500 mb-2">Using quantum keys from KME</p>
                  <div className="font-mono text-[10px] text-indigo-600/50 h-4 mb-4 tracking-widest overflow-hidden">
                    <span className="inline-block">{hashSequence || '\u00A0'}</span>
                  </div>
                  <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden w-full">
                    <div
                      className="h-full bg-indigo-600 decrypt-progress-bar"
                      style={{ width: `${progress}%` }}
                    ></div>
                  </div>
                </div>
              ) : stage === 'totp_required' || stage === 'verifying_totp' ? (
                /* TOTP Verification Screen */
                <div className="py-4 totp-container-stable">
                  <TOTPInput
                    onSubmit={handleTotpVerify}
                    isVerifying={stage === 'verifying_totp'}
                    error={totpError}
                  />
                </div>
              ) : (
                <div className="text-center max-w-sm mx-auto">
                  <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mb-5 mx-auto border border-gray-200 shadow-lg rotate-3 hover:rotate-0 transition-transform duration-500">
                    <Lock size={28} className="text-gray-400" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900 mb-2">Encrypted Message</h3>
                  <p className="text-gray-500 text-xs mb-8 leading-relaxed">
                    This content is protected by {securityLevelDisplay}.
                    <br />Decrypt using your private quantum key.
                  </p>
                  <button
                    onClick={handleDecrypt}
                    disabled={stage !== 'locked'}
                    className="group bg-indigo-600 text-white hover:bg-indigo-700 px-6 py-2.5 rounded-lg text-sm font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all flex items-center gap-2 mx-auto"
                  >
                    <Key size={16} className="text-indigo-200" />
                    <span>Decrypt with Quantum Key</span>
                    <ShieldCheck size={16} className="text-indigo-200 group-hover:text-white group-hover:scale-110 transition-all" />
                  </button>
                  <div className="mt-6 text-[11px] text-gray-400 uppercase tracking-[0.2em]">
                    Quantum-Aided Secure Delivery
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QuantumEmailViewer;
