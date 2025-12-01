import React from 'react';
import { ShieldCheck, Lock, FileCheck } from 'lucide-react';

interface SecurityDetailsProps {
    email: any;
}

const SecurityDetails: React.FC<SecurityDetailsProps> = ({ email }) => {
    // Extract security details from the email object (handling both backend and sample formats)
    const securityLevel = email.security_level ?? email.securityLevel;
    const flowId = email.flow_id ?? email.flowId ?? email.securityDetails?.flowId ?? email.encryption_metadata?.flow_id ?? 'N/A';
    
    // Extract Key ID from multiple possible sources
    const getKeyId = (): string => {
        // Direct key_id field
        const directKeyId = email.encryption_metadata?.key_id ?? 
                            email.key_id ?? 
                            email.securityDetails?.keyId;
        if (directKeyId) return directKeyId;
        
        // From quantum_enhancement key_ids (Level 3 PQC)
        const quantumKeyIds = email.encryption_metadata?.quantum_enhancement?.key_ids;
        if (quantumKeyIds?.km1) return quantumKeyIds.km1;
        
        // From key_fragments array (Level 1/2)
        const keyFragments = email.encryption_metadata?.key_fragments;
        if (keyFragments && keyFragments.length > 0) {
            return Array.isArray(keyFragments) ? keyFragments[0] : keyFragments;
        }
        
        // Fallback to flow_id
        if (flowId && flowId !== 'N/A') return flowId;
        
        return 'N/A';
    };
    const keyId = getKeyId();
    
    const isVerified = email.security_info?.verification_status === 'Verified' || email.securityDetails?.signatureVerified === true;
    const algorithm = email.security_info?.algorithm ?? email.encryption_metadata?.algorithm ?? 'AES-256 + QKD Layer';

    if (!securityLevel && !email.securityDetails) return null;

    return (
        <div className="mt-8 mb-2 bg-gray-50/50 rounded-lg border border-gray-200 p-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200/60">
                <h3 className="font-semibold text-gray-900 text-xs flex items-center gap-2">
                    <ShieldCheck size={14} className="text-indigo-600" />
                    Security Verification
                </h3>
                <span className="text-[10px] text-gray-400 font-mono">Key ID: {keyId}</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Encryption Type */}
                <div className="flex items-start gap-3">
                    <div className="mt-0.5 p-1.5 bg-white rounded-md border border-gray-100 shadow-sm text-indigo-600">
                        <Lock size={14} />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Encryption Protocol</p>
                        <p className="text-xs font-semibold text-gray-700 mt-0.5">Level {securityLevel}</p>
                        <p className="text-[10px] text-gray-500">{algorithm}</p>
                    </div>
                </div>

                {/* Verification */}
                <div className="flex items-start gap-3">
                    <div className="mt-0.5 p-1.5 bg-white rounded-md border border-gray-100 shadow-sm text-emerald-600">
                        <FileCheck size={14} />
                    </div>
                    <div>
                        <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Digital Signature</p>
                        <div className="flex items-center gap-1 mt-0.5">
                            <span className={`text-xs font-semibold ${isVerified ? 'text-gray-700' : 'text-gray-500'}`}>
                                {isVerified ? 'Verified Certificate' : 'Pending Verification'}
                            </span>
                            {isVerified && <ShieldCheck size={10} className="text-emerald-500" fill="currentColor" />}
                        </div>
                        <p className="text-[10px] text-gray-500"> </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SecurityDetails;
