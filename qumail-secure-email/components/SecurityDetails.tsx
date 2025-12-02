import React from 'react';
import { ShieldCheck, Lock, Activity, FileCheck } from 'lucide-react';
import { Email } from '../types';

interface SecurityDetailsProps {
  email: Email;
}

const SecurityDetails: React.FC<SecurityDetailsProps> = ({ email }) => {
  if (!email.securityDetails) return null;

  return (
    <div className="mt-8 mb-2 bg-gray-50/50 rounded-xl border border-gray-200 p-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-gray-200/60">
          <h3 className="font-semibold text-gray-900 text-xs flex items-center gap-2">
            <ShieldCheck size={14} className="text-indigo-600" />
            Security Verification
          </h3>
          <span className="text-[10px] text-gray-400 font-mono">{email.securityDetails.flowId}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Encryption Type */}
        <div className="flex items-start gap-3">
           <div className="mt-0.5 p-1.5 bg-white rounded-md border border-gray-100 shadow-sm text-indigo-600">
                <Lock size={14} />
           </div>
           <div>
                <p className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Encryption Protocol</p>
                <p className="text-xs font-semibold text-gray-700 mt-0.5">{email.securityLevel}</p>
                <p className="text-[10px] text-gray-500">AES-256 + QKD Layer</p>
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
                    <span className="text-xs font-semibold text-gray-700">Verified Certificate</span>
                    <ShieldCheck size={10} className="text-emerald-500" fill="currentColor" />
                </div>
                <p className="text-[10px] text-gray-500"> </p>
           </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityDetails;