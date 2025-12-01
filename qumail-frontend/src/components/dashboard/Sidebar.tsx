import React from 'react'
import { Button } from '../ui/Button'

interface SidebarProps {
  activeFolder: string
  onFolderChange: (folder: string) => void
  onCompose: () => void
  emailCounts: {
    inbox: number
    sent: number
    drafts: number
    trash: number
  }
  onNavigateToView?: (view: string) => void
  isCompact?: boolean
  currentView?: string
  keyManagerLoggedIn?: boolean
  keyManagerType?: 'KM1' | 'KM2' | null
  selectedSecurityLevels?: Set<number>
  onSecurityLevelToggle?: (level: number) => void
  emails?: any[]
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeFolder,
  onFolderChange,
  onCompose,
  emailCounts,
  onNavigateToView,
  isCompact = false,
  currentView = 'email',
  keyManagerLoggedIn = false,
  keyManagerType = null,
  // selectedSecurityLevels, onSecurityLevelToggle, emails - removed, not used
}) => {

  const iconSize = isCompact ? 'w-5 h-5' : 'w-5 h-5'
  const iconWrapperSize = isCompact ? 'w-9 h-9' : 'w-4 h-4'

  const folders = [
    {
      id: 'inbox',
      name: 'Inbox',
      icon: (
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
      ),
      count: emailCounts.inbox,
    },
    {
      id: 'sent',
      name: 'Sent',
      icon: (
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
        </svg>
      ),
      count: emailCounts.sent,
    },
    {
      id: 'drafts',
      name: 'Drafts',
      icon: (
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
        </svg>
      ),
      count: emailCounts.drafts,
    },
    {
      id: 'trash',
      name: 'Trash',
      icon: (
        <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      ),
      count: emailCounts.trash,
    }
  ]

  return (
    <div className={`${isCompact ? 'w-24' : 'w-64'} h-full bg-white border-y border-r border-gray-200 rounded-r-2xl shadow-sm flex flex-col flex-shrink-0 transition-[width] duration-300 ease-in-out z-20 relative overflow-y-auto overflow-x-hidden will-change-[width]`}>
      {/* Modern Compose Button */}
      <div className="p-5 flex justify-center border-b border-gray-100 dark:border-gray-800">
        <Button
          onClick={onCompose}
          className={`bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors duration-200 flex items-center justify-center gap-2 text-sm ${isCompact ? 'w-12 h-12 p-0 rounded-xl' : 'w-full px-4'}`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {!isCompact && <span>Compose</span>}
        </Button>
      </div>

      {/* Clean Navigation Folders */}
      <div className="px-3 py-2 flex-1">
        {!isCompact && (
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-3 mb-2">
            Folders
          </h3>
        )}
        <nav className="space-y-0.5">
          {folders.map((folder) => (
            <button
              key={folder.id}
              onClick={() => onFolderChange(folder.id)}
              className={`group w-full flex items-center ${isCompact ? 'justify-center relative' : 'justify-between'} px-3 py-2.5 rounded-md text-left transition-colors duration-150 ${activeFolder === folder.id
                  ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/20 dark:text-indigo-400'
                  : 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800/50'
                }`}
            >
              <div className="flex items-center gap-2.5">
                <div className={`${iconWrapperSize} flex items-center justify-center ${activeFolder === folder.id ? 'text-indigo-600 dark:text-indigo-400' : 'text-gray-500 dark:text-gray-400'
                  }`}>
                  {folder.icon}
                </div>
                {!isCompact && <span className="font-medium text-sm">{folder.name}</span>}
              </div>
              {!isCompact && folder.count > 0 && (
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${activeFolder === folder.id
                    ? 'bg-indigo-100 text-indigo-700 dark:bg-indigo-800/30 dark:text-indigo-300'
                    : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  }`}>
                  {folder.count}
                </span>
              )}

              {isCompact && (
                <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
                  {folder.name}{folder.count > 0 ? ` (${folder.count})` : ''}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Admin Section - Key Manager */}
      <div className="px-3 py-2 border-t border-gray-100 dark:border-gray-800">
        {!isCompact && (
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide px-3 mb-2">
            Admin
          </h3>
        )}
        <button
          onClick={() => onNavigateToView?.('keymanager')}
          className={`group w-full flex items-center ${isCompact ? 'justify-center relative' : 'justify-between'} px-3 py-2.5 rounded-md text-left transition-colors duration-150 ${
            currentView === 'keymanager'
              ? 'bg-purple-50 text-purple-700 dark:bg-purple-900/20 dark:text-purple-400'
              : 'text-gray-600 hover:bg-gray-50 dark:text-gray-300 dark:hover:bg-gray-800/50'
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className={`${iconWrapperSize} flex items-center justify-center ${
              currentView === 'keymanager' ? 'text-purple-600 dark:text-purple-400' : 'text-gray-500 dark:text-gray-400'
            }`}>
              <svg className={iconSize} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
            </div>
            {!isCompact && <span className="font-medium text-sm">Key Manager</span>}
          </div>
          {!isCompact && keyManagerLoggedIn && keyManagerType && (
            <span className="text-xs font-medium px-2 py-0.5 rounded bg-purple-100 text-purple-700 dark:bg-purple-800/30 dark:text-purple-300">
              {keyManagerType}
            </span>
          )}
          {isCompact && (
            <span className="absolute left-full ml-4 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-50">
              Key Manager{keyManagerLoggedIn && keyManagerType ? ` (${keyManagerType})` : ''}
            </span>
          )}
        </button>
      </div>

      {/* Encryption Badge */}
      <div className="p-5 mt-auto">
        <div className={`bg-gray-50/50 dark:bg-gray-800/50 border border-gray-200 dark:border-gray-700 rounded-xl ${isCompact ? 'p-2 flex justify-center' : 'p-3'}`}>
          <div className={`flex items-center ${isCompact ? 'justify-center' : 'gap-3'}`}>
            <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center flex-shrink-0 text-green-600 dark:text-green-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            {!isCompact && (
              <div className="min-w-0">
                <div className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                  Encrypted
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                  QKD Active
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}