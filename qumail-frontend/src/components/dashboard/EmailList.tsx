import React, { useMemo } from 'react';
import { Lock, Star, Zap } from 'lucide-react';
import { getAvatarColor } from '../../utils/avatarColors';

const coerceLevel = (value: unknown): number | null => {
  if (typeof value === 'number') {
    return value;
  }
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return null;
    const direct = Number(trimmed);
    if (!Number.isNaN(direct)) {
      return direct;
    }
    const match = trimmed.match(/([0-4])/);
    if (match) {
      return Number(match[1]);
    }
  }
  return null;
};

const deriveSecurityLevel = (email: Email): number => {
  const candidates = [
    email.security_level,
    email.securityLevel,
    email.security_info?.level,
    (email as any)?.securityDetails?.level,
    (email as any)?.securityInfo?.level,
  ];

  for (const candidate of candidates) {
    const parsed = coerceLevel(candidate as any);
    if (parsed !== null && parsed >= 0 && parsed <= 4) {
      return parsed;
    }
  }

  const textSources = [email.subject, email.snippet]
    .filter(Boolean)
    .map((value) => String(value).toLowerCase())
    .join(' ');

  const hasQuantumContext = textSources.includes('qumail') || textSources.includes('quantum');

  if (hasQuantumContext) {
    const levelMatch = textSources.match(/(?:level|l)\s*([1-4])/);
    if (levelMatch) {
      return Number(levelMatch[1]);
    }
  }

  return 0;
};

interface Email {
  id: string;
  sender_name?: string;
  senderName?: string;
  senderAvatar?: string;
  timestamp: string;
  subject: string;
  snippet: string;
  isUnread?: boolean;
  isStarred?: boolean;
  tags?: string[];
  encrypted?: boolean;
  isEncrypted?: boolean;
  security_level?: number;
  securityLevel?: number;
  security_info?: {
    level?: number;
  };
  securityInfo?: {
    level?: number;
  };
}

interface EmailListProps {
  emails: Email[];
  selectedEmail: Email | null;
  onEmailSelect: (email: Email) => void;
  onToggleStar: (id: string) => void;
  isLoading: boolean;
  activeFolder: string;
}

export const EmailList: React.FC<EmailListProps> = ({ emails, selectedEmail, onEmailSelect, onToggleStar, isLoading, activeFolder }) => {
  const selectedId = selectedEmail?.id ?? null;

  const formatTimestamp = useMemo(() => (value: string) => {
    if (!value) return '';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;

    const now = new Date();
    const isSameDay = date.toDateString() === now.toDateString();
    const isSameYear = date.getFullYear() === now.getFullYear();

    const options: Intl.DateTimeFormatOptions = isSameDay
      ? { hour: '2-digit', minute: '2-digit' }
      : isSameYear
        ? { month: 'short', day: 'numeric' }
        : { month: 'short', day: 'numeric', year: 'numeric' };

    return date.toLocaleString(undefined, options);
  }, []);

  const handleSelect = (id: string) => {
    const email = emails.find((e) => e.id === id);
    if (email) onEmailSelect(email);
  };

  // Memoize email items to prevent unnecessary re-renders
  const emailItems = useMemo(() => emails.map((email) => {
    const senderName = email.sender_name || email.senderName || 'Unknown Sender';
    const securityLevel = deriveSecurityLevel(email);
    const isEncrypted = email.isEncrypted ?? email.encrypted ?? securityLevel > 0;
    return { ...email, senderName, securityLevel, isEncrypted };
  }), [emails]);

  if (isLoading) {
    return (
      <div className="h-full flex flex-col bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        {/* Header placeholder */}
        <div className="h-14 px-5 border-b border-gray-200 bg-white flex items-center justify-between flex-shrink-0 sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <h2 className="font-bold text-gray-900 text-base capitalize">{activeFolder}</h2>
            <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{emails.length}</span>
          </div>
        </div>
        {/* Loading skeleton */}
        <div className="flex-1 p-4 animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
          <div className="h-4 bg-gray-200 rounded w-1/2" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-[28rem] bg-white flex-shrink-0 z-0 rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="h-14 px-5 border-b border-gray-200 bg-white flex items-center justify-between flex-shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <h2 className="font-bold text-gray-900 text-base capitalize">{activeFolder}</h2>
          <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full text-xs font-bold">{emails.length}</span>
        </div>
      </div>

      {/* List Container */}
      <div className="flex-1 overflow-y-auto bg-white">
        {emailItems.map((email) => {
          const isSelected = selectedId === email.id;
          const { senderName, securityLevel, isEncrypted } = email;
          return (
            <div
              key={email.id}
              onClick={() => handleSelect(email.id)}
              className={`relative py-4 px-4 border-b border-gray-100 cursor-pointer transition-colors duration-150 group flex gap-3 ${isSelected ? 'bg-indigo-50/60' : 'hover:bg-gray-50'
                }`}
            >
              {/* Selection Accent Line */}
              {isSelected && <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-600" />}

              {/* Avatar */}
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-white flex-shrink-0 mt-0.5 ${getAvatarColor(senderName)}`}
              >
                {(senderName?.[0] ?? '?').toUpperCase()}
              </div>

              {/* Content Column */}
              <div className="min-w-0 overflow-hidden flex-1">
                {/* Row 1: Sender & Time */}
                <div className="flex justify-between items-baseline mb-0.5">
                  <span className={`text-[15px] truncate pr-2 ${email.isUnread ? 'font-bold text-gray-900' : 'font-bold text-gray-700'}`}>
                    {senderName}
                  </span>
                  <span className={`text-xs whitespace-nowrap ${isSelected ? 'text-indigo-600 font-medium' : 'text-gray-400'}`}>
                    {formatTimestamp(email.timestamp)}
                  </span>
                </div>

                {/* Row 2: Subject */}
                <div className="flex items-center gap-1.5 mb-0.5">
                  {isEncrypted && (
                    <Lock size={12} className="text-indigo-500 flex-shrink-0" strokeWidth={2.5} />
                  )}
                  <h4 className={`text-[15px] truncate leading-tight ${email.isUnread ? 'font-semibold text-gray-900' : 'font-medium text-gray-800'}`}>
                    {email.subject}
                  </h4>
                </div>

                {/* Row 3: Snippet */}
                <div className="flex justify-between items-start">
                  <p className="text-[13px] text-gray-500 truncate leading-relaxed max-w-[90%]">{email.snippet}</p>
                  {/* Star Button */}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleStar(email.id);
                    }}
                    className={`ml-1 p-0.5 rounded transition-all hover:scale-110 ${email.isStarred
                        ? 'text-yellow-400 opacity-100'
                        : `text-gray-300 hover:text-yellow-400 ${isSelected ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`
                      }`}
                  >
                    <Star size={16} fill={email.isStarred ? 'currentColor' : 'none'} />
                  </button>
                </div>

                {/* Row 4: Quantum Level Badge */}
                {(() => {
                  const level = securityLevel;
                  if (level === 0) return null;

                  const levelColors: Record<number, string> = {
                    1: 'bg-purple-50 text-purple-700 border-purple-200',
                    2: 'bg-blue-50 text-blue-700 border-blue-200',
                    3: 'bg-emerald-50 text-emerald-700 border-emerald-200',
                    4: 'bg-gray-100 text-gray-700 border-gray-200',
                  };
                  const levelNames: Record<number, string> = {
                    1: 'Level 1',
                    2: 'Level 2',
                    3: 'Level 3',
                    4: 'Standard',
                  };

                  return (
                    <div className="mt-1.5">
                      <span className={`inline-flex items-center gap-1.5 text-[10px] px-2 py-1 rounded-md border font-bold tracking-wide ${levelColors[level] ?? 'bg-gray-100 text-gray-700 border-gray-200'}`}>
                        <Zap size={10} className="fill-current" />
                        {levelNames[level] ?? 'Standard'}
                      </span>
                    </div>
                  );
                })()}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default EmailList;