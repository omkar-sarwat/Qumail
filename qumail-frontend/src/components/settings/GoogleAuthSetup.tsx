/**
 * Google Authenticator Setup Component
 * 
 * Allows users to set up Google Authenticator for securing decrypt operations.
 * Shows QR code that can be scanned by Google Authenticator app.
 */
import React, { useState, useEffect, useRef } from 'react';
import { Smartphone, CheckCircle, AlertCircle, Shield, Copy, Check } from 'lucide-react';
import { decryptAuthService, DecryptAuthStatus } from '../../services/decryptAuthService';

interface GoogleAuthSetupProps {
  onSetupComplete?: () => void;
}

export const GoogleAuthSetup: React.FC<GoogleAuthSetupProps> = ({ onSetupComplete }) => {
  const [_status, setStatus] = useState<DecryptAuthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Setup state
  const [qrCode, setQrCode] = useState<string | null>(null);
  const [secret, setSecret] = useState<string | null>(null);
  const [setupStep, setSetupStep] = useState<'loading' | 'show_qr' | 'verify' | 'complete'>('loading');
  const [verificationCode, setVerificationCode] = useState(['', '', '', '', '', '']);
  const [verifying, setVerifying] = useState(false);
  const [verifyError, setVerifyError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Check current status on mount
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const result = await decryptAuthService.getStatus();
        setStatus(result);
        if (result.totp_verified) {
          setSetupStep('complete');
        }
      } catch (e: any) {
        setError(e.message || 'Failed to check status');
      } finally {
        setLoading(false);
      }
    };
    checkStatus();
  }, []);

  // Start setup
  const handleStartSetup = async () => {
    setError(null);
    setLoading(true);
    
    try {
      const response = await decryptAuthService.setup2FA();
      setQrCode(response.qr_code);
      setSecret(response.secret);
      setSetupStep('show_qr');
    } catch (e: any) {
      setError(e.message || 'Failed to start setup');
    } finally {
      setLoading(false);
    }
  };

  // Handle code input
  const handleCodeChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newCode = [...verificationCode];
    newCode[index] = value.slice(-1);
    setVerificationCode(newCode);
    
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
    
    // Auto-verify when complete
    if (newCode.every(d => d !== '') && index === 5) {
      handleVerify(newCode.join(''));
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !verificationCode[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  // Verify code
  const handleVerify = async (code: string) => {
    setVerifying(true);
    setVerifyError(null);
    
    try {
      const result = await decryptAuthService.verifySetup(code);
      if (result.success) {
        setSetupStep('complete');
        onSetupComplete?.();
      } else {
        setVerifyError('Invalid code. Please try again.');
        setVerificationCode(['', '', '', '', '', '']);
        inputRefs.current[0]?.focus();
      }
    } catch (e: any) {
      setVerifyError(e.message || 'Verification failed');
      setVerificationCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setVerifying(false);
    }
  };

  // Copy secret to clipboard
  const handleCopySecret = async () => {
    if (secret) {
      await navigator.clipboard.writeText(secret);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Disable 2FA
  const handleDisable = async () => {
    if (!confirm('Are you sure you want to disable Google Authenticator? You will no longer need a code to view decrypted emails.')) {
      return;
    }
    
    try {
      await decryptAuthService.disable2FA();
      setStatus(null);
      setSetupStep('loading');
      setQrCode(null);
      setSecret(null);
    } catch (e: any) {
      setError(e.message || 'Failed to disable');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full totp-verify-spin" />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-indigo-50 to-purple-50">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
            <Smartphone className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Google Authenticator</h3>
            <p className="text-xs text-gray-500">Secure your decrypted emails with 2FA</p>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-800 text-sm">
            <AlertCircle className="w-4 h-4" />
            <span>{error}</span>
          </div>
        )}

        {setupStep === 'complete' ? (
          /* Already set up */
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle className="w-8 h-8 text-green-600" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-1">Google Authenticator Active</h4>
            <p className="text-sm text-gray-500 mb-6">
              You'll need to enter a code from Google Authenticator<br />to view previously decrypted emails.
            </p>
            <button
              onClick={handleDisable}
              className="text-sm text-red-600 hover:text-red-700 hover:underline"
            >
              Disable Google Authenticator
            </button>
          </div>
        ) : setupStep === 'show_qr' ? (
          /* Show QR code */
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-4">
              Scan this QR code with your Google Authenticator app:
            </p>
            
            {qrCode && (
              <div className="inline-block p-4 bg-white border-2 border-gray-200 rounded-xl mb-4">
                <img src={qrCode} alt="QR Code" className="w-48 h-48" />
              </div>
            )}
            
            <div className="text-sm text-gray-500 mb-4">
              Or enter this code manually:
            </div>
            
            {secret && (
              <div className="inline-flex items-center gap-2 bg-gray-100 px-4 py-2 rounded-lg mb-6">
                <code className="font-mono text-sm text-gray-800">{secret}</code>
                <button
                  onClick={handleCopySecret}
                  className="p-1 hover:bg-gray-200 rounded transition-colors"
                  title="Copy to clipboard"
                >
                  {copied ? (
                    <Check className="w-4 h-4 text-green-600" />
                  ) : (
                    <Copy className="w-4 h-4 text-gray-500" />
                  )}
                </button>
              </div>
            )}
            
            <button
              onClick={() => setSetupStep('verify')}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors"
            >
              I've scanned the code
            </button>
          </div>
        ) : setupStep === 'verify' ? (
          /* Verify code */
          <div className="text-center totp-input-stable">
            <h4 className="font-semibold text-gray-900 mb-2">Verify Setup</h4>
            <p className="text-sm text-gray-500 mb-6">
              Enter the 6-digit code from Google Authenticator:
            </p>
            
            <div className="flex justify-center gap-2 mb-4">
              {verificationCode.map((digit, index) => (
                <input
                  key={index}
                  ref={el => inputRefs.current[index] = el}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={digit}
                  onChange={e => handleCodeChange(index, e.target.value)}
                  onKeyDown={e => handleKeyDown(index, e)}
                  disabled={verifying}
                  className={`totp-digit-input w-12 h-14 text-center text-2xl font-bold border-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500
                    ${verifyError ? 'border-red-300 bg-red-50' : 'border-gray-300 bg-white'}
                    ${verifying ? 'opacity-60' : ''}
                  `}
                />
              ))}
            </div>
            
            {/* Fixed height container for error/verifying states */}
            <div className="h-8 flex items-center justify-center mb-4">
              {verifyError ? (
                <p className="text-red-600 text-sm">{verifyError}</p>
              ) : verifying ? (
                <div className="flex items-center justify-center gap-2 text-indigo-600">
                  <div className="w-4 h-4 border-2 border-indigo-600 border-t-transparent rounded-full totp-verify-spin" />
                  <span className="text-sm">Verifying...</span>
                </div>
              ) : null}
            </div>
            
            <button
              onClick={() => setSetupStep('show_qr')}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              ← Back to QR code
            </button>
          </div>
        ) : (
          /* Initial state - start setup */
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Shield className="w-8 h-8 text-gray-400" />
            </div>
            <h4 className="font-semibold text-gray-900 mb-2">Not Set Up</h4>
            <p className="text-sm text-gray-500 mb-6 max-w-xs mx-auto">
              Enable Google Authenticator to require a verification code when viewing decrypted emails on subsequent views.
            </p>
            <button
              onClick={handleStartSetup}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2 mx-auto"
            >
              <Smartphone className="w-4 h-4" />
              Set Up Google Authenticator
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default GoogleAuthSetup;
