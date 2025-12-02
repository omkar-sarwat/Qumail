import React from 'react';
import { Lock, Star, Zap } from 'lucide-react';
import { Email } from '../types';

interface EmailListProps {
  emails: Email[];
  selectedId: string | null;
  folderLabel: string;
  onSelect: (id: string) => void;
  onToggleStar: (id: string) => void;
  isLoading?: boolean;
}

const EmailList: React.FC<EmailListProps> = ({ emails, selectedId, folderLabel, onSelect, onToggleStar, isLoading }) => {
  return (
    <div className="flex flex-col h-full w-[28rem] bg-white flex-shrink-0 z-0 rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="h-14 px-5 border-b border-gray-200 bg-white flex items-center justify-between flex-shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <h2 className="font-bold text-gray-900 text-base">{folderLabel}</h2>
          <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">
            {emails.length}
          </span>
        </div>
        {isLoading && (
          <span className="text-[11px] text-indigo-600 font-semibold animate-pulse">Syncing…</span>
        )}
      </div>

      {/* List Container */}
      <div className="flex-1 overflow-y-auto bg-white">
        {emails.length === 0 && !isLoading && (
          <div className="py-12 text-center text-gray-400 text-sm">
            No messages in this folder yet.
          </div>
        )}
        {emails.map((email) => {
          const isSelected = selectedId === email.id;
          
          return (
            <div
              key={email.id}
              onClick={() => onSelect(email.id)}
              className={`relative py-4 px-4 border-b border-gray-100 cursor-pointer transition-colors duration-150 group flex gap-3
                ${isSelected 
                  ? 'bg-indigo-50/60' 
                  : 'hover:bg-gray-50'
                }`}
            >
              {/* Selection Accent Line */}
              {isSelected && (
                 <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600" />
              )}

              {/* Avatar */}
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm font-bold text-white shadow-sm flex-shrink-0 mt-0.5
                  ${email.senderName === 'Google Security' ? 'bg-blue-600' : 
                    email.senderName === 'QKD System' ? 'bg-purple-600' : 
                    email.senderName === 'MongoDB Atlas' ? 'bg-emerald-600' : 
                    email.senderName === 'Render' ? 'bg-gray-900' : 
                    email.senderName === 'GitHub' ? 'bg-gray-800' :
                    'bg-gray-400'
                  }`}
              >
                  {email.senderAvatar}
              </div>

              {/* Content Column */}
              <div className="min-w-0 overflow-hidden flex-1">
                  {/* Row 1: Sender & Time */}
                  <div className="flex justify-between items-baseline mb-0.5">
                      <span className={`text-[15px] truncate pr-2 ${email.isUnread ? 'font-bold text-gray-900' : 'font-bold text-gray-700'}`}>
                          {email.senderName}
                      </span>
                      <span className={`text-xs whitespace-nowrap ${isSelected ? 'text-indigo-600 font-medium' : 'text-gray-400'}`}>
                          {email.timestamp}
                      </span>
                  </div>

                  {/* Row 2: Subject */}
                  <div className="flex items-center gap-1.5 mb-0.5">
                      {email.isEncrypted && (
                          <Lock size={12} className="text-indigo-500 flex-shrink-0" strokeWidth={2.5} />
                      )}
                      <h4 className={`text-[15px] truncate leading-tight ${email.isUnread ? 'font-semibold text-gray-900' : 'font-medium text-gray-800'}`}>
                          {email.subject}
                      </h4>
                  </div>

                  {/* Row 3: Snippet */}
                  <div className="flex justify-between items-start">
                      <p className="text-[13px] text-gray-500 truncate leading-relaxed max-w-[90%]">
                          {email.snippet}
                      </p>
                      {/* Star Button */}
                       <button 
                          onClick={(e) => {
                              e.stopPropagation();
                              onToggleStar(email.id);
                          }}
                          className={`ml-1 p-0.5 rounded transition-all hover:scale-110
                              ${email.isStarred 
                                  ? 'text-yellow-400 opacity-100' 
                                  : `text-gray-300 hover:text-yellow-400 ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`
                              }
                          `}
                       >
                          <Star size={16} fill={email.isStarred ? "currentColor" : "none"} />
                      </button>
                  </div>

                  {/* Tags */}
                  {email.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                          {email.tags.map(tag => {
                              const isQuantum = tag === 'QUANTUM';
                              return (
                                  <span key={tag} className={`text-[10px] px-2 py-0.5 rounded-full border flex items-center gap-1 font-bold tracking-wide transition-all
                                      ${isQuantum 
                                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:border-emerald-300' 
                                          : 'bg-white text-gray-500 border-gray-200'
                                      }`}>
                                      {isQuantum && <Zap size={10} className="text-emerald-600 fill-emerald-100" />}
                                      {tag}
                                  </span>
                              );
                          })}
                      </div>
                  )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EmailList;