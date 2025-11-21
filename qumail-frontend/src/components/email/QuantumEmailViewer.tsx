import React, { useState, useCallback, useEffect } from 'react';
import { Shield, Lock, Unlock, Eye, EyeOff, AlertTriangle, CheckCircle, Clock, Paperclip, Download } from 'lucide-react';
import { emailService } from '../../services/emailService';

interface QuantumEmailViewerProps {
  email: {
    email_id: string;
    flow_id: string;
    sender_email: string;
    receiver_email: string;
    subject: string;
    body_encrypted: string;
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
  };
  onDecrypted?: (decryptedEmail: any) => void;
}

interface DecryptedAttachment {
  filename: string;
  content: string;
  mime_type: string;
  size: number;
}

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

export const QuantumEmailViewer: React.FC<QuantumEmailViewerProps> = ({ 
  email, 
  onDecrypted 
}) => {
  const [isDecrypting, setIsDecrypting] = useState(false);
  const [decryptedContent, setDecryptedContent] = useState<any | null>(null);
  const [decryptionInfo, setDecryptionInfo] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showEncryptedContent, setShowEncryptedContent] = useState(false);

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

  useEffect(() => {
    setIsDecrypting(false);
    setDecryptedContent(null);
    setDecryptionInfo(null);
    setError(null);
    setShowEncryptedContent(false);
  }, [email.email_id, email.body_encrypted]);

  const handleDecrypt = useCallback(async () => {
    if (decryptedContent) {
      // Already decrypted, just toggle view
      return;
    }

    setIsDecrypting(true);
    setError(null);

    try {
      const response = await emailService.decryptEmail(email.email_id);
      
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
        onDecrypted?.({ ...response, email_data: enrichedData });
      } else {
        setError('Failed to decrypt email');
      }
    } catch (err: any) {
      console.error('Decryption error:', err);
      setError(err.message || 'Failed to decrypt email');
    } finally {
      setIsDecrypting(false);
    }
  }, [email.email_id, decryptedContent, onDecrypted]);

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const truncateEncryptedContent = (content: string, maxLength: number = 100) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const resolvedSecurityLevel = decryptedContent?.security_level ?? email.security_level ?? 0;
  const resolvedAlgorithm = decryptedContent?.algorithm ?? email.security_info?.algorithm ?? getAlgorithmName(email.security_level);
  const resolvedQuantumEnhanced =
    decryptedContent?.quantum_enhanced ?? email.security_info?.quantum_enhanced ?? true;
  const resolvedVerification =
    decryptedContent?.verification_status ?? decryptionInfo?.verification_status ?? 'Pending';
  const resolvedFlowId = decryptedContent?.flow_id ?? email.flow_id ?? email.encryption_metadata?.flow_id ?? 'N/A';
  
  // Calculate encrypted size with multiple fallbacks
  const encryptedSize = 
    decryptedContent?.encrypted_size ??
    email.security_info?.encrypted_size ??
    email.encryption_metadata?.encrypted_size ??
    (email.body_encrypted && typeof email.body_encrypted === 'string' ? email.body_encrypted.length : 0);

  // Helper function to get algorithm name from security level
  function getAlgorithmName(level: number): string {
    switch (level) {
      case 1: return 'OTP-QKD-ETSI-014';
      case 2: return 'AES-256-GCM';
      case 3: return 'PQC-Kyber1024';
      case 4: return 'RSA-4096';
      default: return 'Unknown';
    }
  }

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

        {/* Decryption Controls */}
        <div className="flex items-center gap-3">
          {!decryptedContent ? (
            <button
              onClick={handleDecrypt}
              disabled={isDecrypting}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isDecrypting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Decrypting...
                </>
              ) : (
                <>
                  <Unlock className="w-4 h-4" />
                  Decrypt Email
                </>
              )}
            </button>
          ) : (
            <div className="flex items-center gap-2 text-green-700">
              <CheckCircle className="w-5 h-5" />
              <span className="font-medium">Email Decrypted Successfully</span>
            </div>
          )}

          <button
            onClick={() => setShowEncryptedContent(!showEncryptedContent)}
            className="flex items-center gap-2 px-3 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            {showEncryptedContent ? (
              <>
                <EyeOff className="w-4 h-4" />
                Hide Encrypted
              </>
            ) : (
              <>
                <Eye className="w-4 h-4" />
                Show Encrypted
              </>
            )}
          </button>
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
        {decryptedContent ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800 mb-2">Decrypted Content</h3>
              <div 
                className="prose prose-sm max-w-none text-gray-900 dark:text-white [&>*]:text-gray-900 [&_strong]:font-bold [&_em]:italic [&_u]:underline [&_ul]:list-disc [&_ol]:list-decimal [&_ul]:ml-6 [&_ol]:ml-6 [&_li]:mb-1 [&_a]:text-blue-600 [&_a]:underline [&_code]:bg-gray-100 [&_code]:px-1 [&_code]:py-0.5 [&_code]:rounded [&_pre]:bg-gray-100 [&_pre]:p-3 [&_pre]:rounded"
                dangerouslySetInnerHTML={{ __html: decryptedContent.body }}
              />
            </div>

            {/* Attachments Section */}
            {decryptedContent.attachments && decryptedContent.attachments.length > 0 && (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <Paperclip className="w-5 h-5 text-gray-600" />
                  <h3 className="font-semibold text-gray-800">
                    Attachments ({decryptedContent.attachments.length})
                  </h3>
                </div>
                <div className="space-y-2">
                  {decryptedContent.attachments.map((attachment: DecryptedAttachment, index: number) => {
                    const handleDownload = () => {
                      try {
                        // Decode base64 and create blob
                        const byteCharacters = atob(attachment.content);
                        const byteNumbers = new Array(byteCharacters.length);
                        for (let i = 0; i < byteCharacters.length; i++) {
                          byteNumbers[i] = byteCharacters.charCodeAt(i);
                        }
                        const byteArray = new Uint8Array(byteNumbers);
                        const blob = new Blob([byteArray], { type: attachment.mime_type });
                        
                        // Create download link
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
                        className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
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
            
            {/* Security Information - Only shown after decryption */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-800 mb-2">Security Information</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-blue-600 font-medium">Security Level:</span>
                  <div>{securityLevelDisplay}</div>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Quantum Enhanced:</span>
                  <div>{resolvedQuantumEnhanced ? 'Yes' : 'No'}</div>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Flow ID:</span>
                  <div className="font-mono text-xs break-all">{resolvedFlowId}</div>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Encrypted Size:</span>
                  <div>{encryptedSize} characters</div>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Algorithm:</span>
                  <div>{resolvedAlgorithm}</div>
                </div>
                <div>
                  <span className="text-blue-600 font-medium">Verification:</span>
                  <div>{resolvedVerification}</div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <Lock className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-800">Encrypted Content</h3>
            </div>
            
            <div className="text-sm text-gray-600 mb-3">
              This email is quantum-encrypted. Click "Decrypt Email" to view the content.
            </div>
            
            {showEncryptedContent && (
              <div className="bg-white border rounded p-3 font-mono text-xs text-gray-700 break-all">
                {truncateEncryptedContent(email.body_encrypted, 500)}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default QuantumEmailViewer;
