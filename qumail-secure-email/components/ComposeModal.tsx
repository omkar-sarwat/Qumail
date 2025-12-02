import React, { useEffect, useState } from 'react';
import { X, Maximize2, Minimize2, Paperclip, MoreVertical, Send, Bold, Italic, Underline, List, Link, Image as ImageIcon, Smile, ChevronUp, Zap, Cpu, Shield, Lock } from 'lucide-react';
import { SecurityLevel } from '../types';
import EncryptionSelector from './EncryptionSelector';

interface ComposeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSend: (emailData: { to: string; subject: string; content: string; securityLevel: SecurityLevel }) => Promise<void> | void;
  isSending?: boolean;
}

const ToolbarButton = ({ icon: Icon, label }: { icon: any, label: string }) => (
    <button className="group relative p-1.5 rounded hover:bg-gray-100 hover:text-gray-700 transition text-gray-400">
        <Icon size={18} />
        <span className="absolute bottom-full mb-2 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-[10px] px-2 py-1 rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
            {label}
        </span>
    </button>
);

const ComposeModal: React.FC<ComposeModalProps> = ({ isOpen, onClose, onSend, isSending = false }) => {
  const [securityLevel, setSecurityLevel] = useState<SecurityLevel>(SecurityLevel.LEVEL_1);
  const [showEncryptionMenu, setShowEncryptionMenu] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);
  
  const [to, setTo] = useState('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');

    useEffect(() => {
      if (!isOpen) {
        setTo('');
        setSubject('');
        setContent('');
        setSecurityLevel(SecurityLevel.LEVEL_1);
      }
    }, [isOpen]);

    if (!isOpen) return null;

    const handleSendClick = async () => {
      await onSend({
        to,
        subject,
        content,
        securityLevel
      });
    };

  const getSecurityBadgeStyle = (level: SecurityLevel) => {
    if(level === SecurityLevel.LEVEL_1) return "bg-purple-100 text-purple-700 border-purple-200";
    if(level === SecurityLevel.LEVEL_2) return "bg-indigo-100 text-indigo-700 border-indigo-200";
    if(level === SecurityLevel.LEVEL_3) return "bg-teal-100 text-teal-700 border-teal-200";
    return "bg-gray-100 text-gray-600 border-gray-200";
  };

  const getSecurityShortName = (level: SecurityLevel) => {
      return level.split('(')[0].trim();
  }

  return (
    <div className={`fixed z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm transition-all duration-300 ${isMaximized ? 'inset-0 p-0' : 'inset-0 p-8'}`}>
      <div 
        className={`bg-white shadow-2xl flex flex-col overflow-hidden border border-gray-200 animate-in fade-in zoom-in-95 duration-200 transition-all ease-in-out
            ${isMaximized ? 'w-full h-full rounded-none' : 'w-[900px] h-[600px] rounded-xl'}
        `}
      >
        
        {/* Header */}
        <div className="h-14 px-6 border-b border-gray-100 flex items-center justify-between bg-white flex-shrink-0 z-20 relative shadow-sm">
          <div className="flex items-center gap-3">
            <h3 className="font-bold text-gray-900">New Message</h3>
            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${getSecurityBadgeStyle(securityLevel)}`}>
              {getSecurityShortName(securityLevel)}
            </span>
          </div>
          <div className="flex items-center gap-2 text-gray-400">
            <button 
                onClick={() => setIsMaximized(!isMaximized)}
                className="p-2 hover:bg-gray-100 hover:text-gray-600 rounded-lg transition-colors"
                title={isMaximized ? "Minimize" : "Maximize"}
            >
                {isMaximized ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
            </button>
            <button 
                onClick={onClose} 
                className="p-2 hover:bg-red-50 hover:text-red-500 rounded-lg transition-colors text-gray-500"
                title="Close"
            >
                <X size={20} />
            </button>
          </div>
        </div>

        {/* Form Fields */}
        <div className="px-6 py-2 flex-shrink-0 bg-white">
          <div className="flex items-center py-3 border-b border-gray-100 group">
            <span className="text-gray-500 w-16 text-sm font-medium">To:</span>
            <input 
                type="text" 
                value={to}
                onChange={(e) => setTo(e.target.value)}
                placeholder="Recipients (e.g., alice@example.com)" 
                className="flex-1 text-sm outline-none text-gray-900 placeholder-gray-400 bg-white" 
            />
            <span className="text-xs text-gray-400 cursor-pointer hover:text-indigo-600 transition-colors">Cc/Bcc</span>
          </div>
          <div className="flex items-center py-3 border-b border-gray-100 group">
            <span className="text-gray-500 w-16 text-sm font-medium">Subject:</span>
            <input 
                type="text" 
                value={subject}
                onChange={(e) => setSubject(e.target.value)}
                placeholder="Enter subject" 
                className="flex-1 text-sm outline-none text-gray-900 placeholder-gray-400 bg-white" 
            />
          </div>
          
          {/* Toolbar */}
          <div className="flex items-center gap-4 py-3 text-gray-400 border-b border-gray-100 bg-white">
             <div className="flex items-center gap-1 border-r border-gray-200 pr-4">
                <ToolbarButton icon={Bold} label="Bold" />
                <ToolbarButton icon={Italic} label="Italic" />
                <ToolbarButton icon={Underline} label="Underline" />
             </div>
             <div className="flex items-center gap-1 border-r border-gray-200 pr-4">
                <ToolbarButton icon={List} label="List" />
             </div>
             <div className="flex items-center gap-2">
                <ToolbarButton icon={Link} label="Link" />
                <ToolbarButton icon={ImageIcon} label="Image" />
                <ToolbarButton icon={Smile} label="Emoji" />
             </div>
          </div>
        </div>

        {/* Editor */}
        <div className="flex-1 px-6 py-4 bg-white">
            <textarea 
                value={content}
                onChange={(e) => setContent(e.target.value)}
                className="w-full h-full resize-none outline-none text-sm text-gray-900 placeholder-gray-300 leading-relaxed bg-white" 
                placeholder="Write your secure message here..."
                autoFocus
            ></textarea>
        </div>

        {/* Footer */}
        <div className="h-16 px-6 border-t border-gray-100 flex items-center justify-between bg-gray-50/80 flex-shrink-0">
            <div className="relative">
                 <button 
                    onClick={() => setShowEncryptionMenu(!showEncryptionMenu)}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all border shadow-sm ${
                        securityLevel === SecurityLevel.LEVEL_1 ? 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100' :
                        securityLevel === SecurityLevel.LEVEL_2 ? 'bg-indigo-50 text-indigo-700 border-indigo-200 hover:bg-indigo-100' :
                        'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
                    }`}
                 >
                    {securityLevel === SecurityLevel.LEVEL_1 && <Zap size={14} />}
                    {securityLevel === SecurityLevel.LEVEL_2 && <Cpu size={14} />}
                    {securityLevel === SecurityLevel.LEVEL_3 && <Shield size={14} />}
                    {securityLevel === SecurityLevel.LEVEL_4 && <Lock size={14} />}
                    {getSecurityShortName(securityLevel)}
                    <ChevronUp size={14} className={`transition-transform ${showEncryptionMenu ? 'rotate-180' : ''}`} />
                 </button>

                 {showEncryptionMenu && (
                     <div onClick={() => setShowEncryptionMenu(false)}>
                        <EncryptionSelector selected={securityLevel} onSelect={setSecurityLevel} />
                     </div>
                 )}
            </div>

            <div className="flex items-center gap-4">
                <button className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-all" title="Attach File"><Paperclip size={20} /></button>
                <button className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-all" title="More Options"><MoreVertical size={20} /></button>
                <button 
                  onClick={handleSendClick}
                  disabled={!to || !subject || isSending}
                  className={`bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors shadow-lg shadow-indigo-200 hover:shadow-indigo-300 ${( !to || !subject || isSending) ? 'opacity-50 cursor-not-allowed' : ''}`}>
                  {isSending ? 'Sending…' : 'Encrypt & Send'} <Send size={16} />
                </button>
            </div>
        </div>
      </div>
    </div>
  );
};

export default ComposeModal;