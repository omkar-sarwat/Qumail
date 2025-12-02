import React, { useState, useEffect, useRef } from 'react';
import { Archive, Trash2, Printer, Ban, MoreHorizontal, ShieldAlert, Lock, CheckCircle2, Terminal, Reply, Forward, ShieldCheck, Cpu } from 'lucide-react';
import { Email, SecurityLevel } from '../types';
import SecurityDetails from './SecurityDetails';

interface EmailDetailProps {
    email: Email;
    isDecrypted: boolean;
    onDecrypt: () => Promise<void> | void;
    onDelete: () => void;
    onArchive: () => void;
    isDecrypting?: boolean;
    isLoading?: boolean;
}

const IconButtonWithTooltip = ({ icon: Icon, label, onClick }: { icon: any, label: string, onClick?: () => void }) => (
  <button 
    onClick={onClick}
    className="group relative p-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors"
  >
    <Icon size={18} />
    <span className="absolute top-full mt-2 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50 whitespace-nowrap">
      {label}
    </span>
  </button>
);

const EmailDetail: React.FC<EmailDetailProps> = ({ email, isDecrypted, onDecrypt, onDelete, onArchive, isDecrypting = false, isLoading = false }) => {
    const [isDecryptingUI, setIsDecryptingUI] = useState(false);
  const [progress, setProgress] = useState(0);
  const [hashSequence, setHashSequence] = useState("");
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  // Effect for simple hash changing
    useEffect(() => {
        if (!isDecryptingUI && !isDecrypting) return;

    const chars = "0123456789ABCDEF";
    let interval: any;
    
    interval = setInterval(() => {
       let result = "";
       for(let i=0; i<24; i++) {
          result += chars.charAt(Math.floor(Math.random() * chars.length));
          if ((i+1) % 4 === 0 && i !== 23) result += " ";
       }
       setHashSequence(result);
    }, 80);

        return () => clearInterval(interval);
    }, [isDecryptingUI, isDecrypting]);

  useEffect(() => {
      const handleClickOutside = (event: MouseEvent) => {
          if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
              setShowMoreMenu(false);
          }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

    const handleDecrypt = () => {
        if (isDecrypting || isDecryptingUI) return;
        setIsDecryptingUI(true);
    setProgress(0);
    
    const duration = 1500; // Slightly faster, snappy feel
    const intervalTime = 15;
    const steps = duration / intervalTime;
    let currentStep = 0;

    const timer = setInterval(() => {
        currentStep++;
        const newProgress = Math.min((currentStep / steps) * 100, 100);
        setProgress(newProgress);

        if (currentStep >= steps) {
            clearInterval(timer);
                        setTimeout(async () => {
                                try {
                                        await onDecrypt();
                                } finally {
                                        setIsDecryptingUI(false);
                                }
                        }, 150);
        }
    }, intervalTime);
  };

    const renderLoadingState = () => (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 text-sm gap-3">
                <div className="w-12 h-12 rounded-full border-4 border-gray-100 border-t-indigo-500 animate-spin"></div>
                <p>Preparing secure content…</p>
        </div>
    );

  return (
    <div className="flex-1 h-full flex flex-col bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden relative">
        {/* Integrated Toolbar */}
        <div className="px-6 py-3 border-b border-gray-100 flex items-center justify-between bg-white flex-shrink-0 sticky top-0 z-20">
            <div className="flex items-center gap-1">
            <IconButtonWithTooltip icon={Archive} label="Archive" onClick={onArchive} />
            <IconButtonWithTooltip icon={Trash2} label="Delete" onClick={onDelete} />
            <IconButtonWithTooltip icon={Ban} label="Spam" onClick={onDelete} />
            <div className="w-px h-5 bg-gray-200 mx-2"></div>
            <IconButtonWithTooltip icon={Printer} label="Print" />
            
            <div className="relative" ref={menuRef}>
                <IconButtonWithTooltip 
                    icon={MoreHorizontal} 
                    label="More" 
                    onClick={() => setShowMoreMenu(!showMoreMenu)} 
                />
                {showMoreMenu && (
                    <div className="absolute left-0 top-full mt-1 w-48 bg-white rounded-lg shadow-xl border border-gray-200 z-50 py-1 animate-in fade-in zoom-in-95 duration-100 origin-top-left">
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
            
            {email.securityLevel && (
            <div className={`px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2 cursor-help
                ${email.securityLevel === SecurityLevel.LEVEL_1 ? 'bg-purple-100 text-purple-700' : 
                email.securityLevel === SecurityLevel.LEVEL_2 ? 'bg-indigo-100 text-indigo-700' :
                'bg-gray-100 text-gray-600'
                }
            `} title="Encryption Level">
                <ShieldAlert size={14} />
                {email.securityLevel}
            </div>
            )}
        </div>

        {/* Scrollable Content Area */}
        <div className="flex-1 overflow-y-auto">
           {/* Header Info */}
           <div className="p-8 border-b border-gray-100">
                <h1 className="text-2xl font-bold text-gray-900 mb-6">{email.subject}</h1>
                
                <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-lg font-bold text-white shadow-sm
                            ${email.senderName === 'Google Security' ? 'bg-blue-600' : 
                                email.senderName === 'QKD System' ? 'bg-purple-600' : 
                                email.senderName === 'MongoDB Atlas' ? 'bg-emerald-600' : 
                                email.senderName === 'Render' ? 'bg-gray-900' : 'bg-gray-600'
                            }`}
                        >
                            {typeof email.senderAvatar === 'string' && email.senderAvatar.length <= 2 ? email.senderAvatar : email.senderName[0]}
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="font-bold text-gray-900">{email.senderName}</span>
                                <span className="text-sm text-gray-500">&lt;{email.senderEmail}&gt;</span>
                            </div>
                            <p className="text-xs text-gray-500 mt-0.5">To: Me</p>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">{email.fullDate}</p>
                        <p className="text-xs text-gray-500">{email.timestamp}</p>
                    </div>
                </div>
           </div>

           {/* Content Area */}
           <div className="p-8 flex-1 relative flex flex-col min-h-[400px]">
                {isLoading ? (
                    renderLoadingState()
                ) : email.isEncrypted && !isDecrypted ? (
                    <div className="absolute inset-0 m-8 bg-gray-50/50 rounded-lg border border-gray-200 flex flex-col items-center justify-center overflow-hidden shadow-inner">
                         
                         {/* Subtle background grid - Light Theme */}
                         <div className="absolute inset-0 opacity-[0.03]" 
                              style={{ backgroundImage: 'linear-gradient(#4f46e5 1px, transparent 1px), linear-gradient(90deg, #4f46e5 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
                         </div>
                         
                         {/* Light gradient overlay */}
                         <div className="absolute inset-0 bg-gradient-to-b from-transparent via-white/40 to-white/80"></div>

                         {isDecrypting || isDecryptingUI ? (
                            <div className="w-full max-w-xs relative z-10 text-center">
                                {/* Pulsing Icon - Light Theme */}
                                <div className="relative w-16 h-16 mx-auto mb-6">
                                    <div className="absolute inset-0 bg-indigo-100 rounded-full animate-ping"></div>
                                    <div className="relative bg-white rounded-full w-16 h-16 flex items-center justify-center border border-indigo-100 shadow-sm">
                                        <Cpu size={32} className="text-indigo-600 animate-pulse" />
                                    </div>
                                </div>

                                <h2 className="text-indigo-900 font-bold text-sm tracking-wider mb-2">ESTABLISHING SECURE LINK</h2>
                                
                                {/* Hash Sequence */}
                                <div className="font-mono text-[10px] text-indigo-600/60 h-4 mb-4 tracking-widest">
                                    {hashSequence}
                                </div>
                                
                                {/* Modern Progress Bar - Light Theme */}
                                <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden w-full">
                                    <div 
                                        className="h-full bg-indigo-600 shadow-[0_0_8px_rgba(79,70,229,0.4)] transition-all duration-75 ease-out" 
                                        style={{ width: `${progress}%` }}
                                    ></div>
                                </div>
                            </div>
                         ) : (
                            <div className="text-center z-10 max-w-sm">
                                <div className="w-16 h-16 bg-white rounded-2xl flex items-center justify-center mb-5 mx-auto border border-gray-200 shadow-lg rotate-3 hover:rotate-0 transition-transform duration-500">
                                    <Lock size={28} className="text-gray-400" />
                                </div>
                                <h3 className="text-lg font-bold text-gray-900 mb-2">Encrypted Message</h3>
                                <p className="text-gray-500 text-xs mb-8 leading-relaxed">
                                    This content is protected by {email.securityLevel}.<br/>
                                    Decrypt using your private quantum key.
                                </p>
                                <button 
                                    onClick={handleDecrypt}
                                    disabled={isDecrypting || isDecryptingUI}
                                    className={`group bg-indigo-600 text-white hover:bg-indigo-700 px-6 py-2.5 rounded-lg text-sm font-bold shadow-lg shadow-indigo-200 hover:shadow-indigo-300 transition-all flex items-center gap-2 mx-auto ${(isDecrypting || isDecryptingUI) ? 'opacity-60 cursor-not-allowed' : ''}`}
                                >
                                    <span>{(isDecrypting || isDecryptingUI) ? 'Decrypting…' : 'Decrypt Message'}</span>
                                    <ShieldCheck size={16} className="text-indigo-200 group-hover:text-white group-hover:scale-110 transition-all" />
                                </button>
                            </div>
                         )}
                    </div>
                ) : (
                    <div className={`prose max-w-none flex-1 flex flex-col ${email.isEncrypted ? 'animate-in fade-in zoom-in-[0.98] duration-500' : ''}`}>
                         {/* Success Banner */}
                         {email.isEncrypted && (
                             <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-3 mb-6 flex items-center gap-3 animate-in slide-in-from-top-2 duration-300">
                                <div className="w-6 h-6 bg-indigo-100 rounded-full flex items-center justify-center flex-shrink-0">
                                    <ShieldCheck size={14} className="text-indigo-600" />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-indigo-900">Secure Connection Established</p>
                                    <p className="text-[11px] text-indigo-700">Decrypted via Quantum-Aided AES-256 • Key ID: #8842-A</p>
                                </div>
                             </div>
                         )}

                         {/* Render Content */}
                         <div className="mb-10 text-gray-800 leading-relaxed">
                             {typeof email.content === 'string' ? (
                                 <div dangerouslySetInnerHTML={{ __html: email.content }} />
                             ) : (
                                 email.content
                             )}
                         </div>

                         {/* Security Details Embedded at Bottom */}
                         {email.securityDetails && (
                             <SecurityDetails email={email} />
                         )}
                         
                         {/* Reply/Forward Buttons */}
                         <div className="mt-auto pt-8 border-t border-gray-100 flex gap-3">
                            <button className="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 flex items-center gap-2 transition-all shadow-sm hover:shadow">
                                <Reply size={16} /> Reply
                            </button>
                            <button className="px-4 py-2 rounded-lg border border-gray-200 text-gray-600 text-sm font-medium hover:bg-gray-50 hover:text-gray-900 hover:border-gray-300 flex items-center gap-2 transition-all shadow-sm hover:shadow">
                                <Forward size={16} /> Forward
                            </button>
                         </div>
                    </div>
                )}
           </div>
        </div>
    </div>
  );
};

export default EmailDetail;