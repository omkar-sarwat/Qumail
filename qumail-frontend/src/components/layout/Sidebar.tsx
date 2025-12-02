import React from 'react'
import { Card, CardContent, Button, Badge } from '../ui'
import {
  Inbox,
  Send,
  Archive,
  Trash2,
  Star,
  Edit,
  Shield,
  User,
  LogOut
} from 'lucide-react'

interface FolderItem {
  id: string
  name: string
  count?: number
  icon?: React.ComponentType<{ className?: string }>
  type?: string
}

interface SidebarProps {
  onComposeClick?: () => void
  onFolderSelect?: (folder: string) => void
  selectedFolder?: string
  user?: {
    name: string
    email: string
    avatar?: string
  }
  onLogout?: () => void
  // Extended / optional props
  folders?: FolderItem[]
  collapsed?: boolean
  onToggleCollapse?: () => void
  quantumKeysAvailable?: number
  systemStatus?: 'healthy' | 'degraded' | 'critical'
}

const defaultFolders = [
  { id: 'inbox', name: 'Inbox', icon: Inbox, count: 12 },
  { id: 'sent', name: 'Sent', icon: Send, count: 0 },
  { id: 'starred', name: 'Starred', icon: Star, count: 3 },
  { id: 'archive', name: 'Archive', icon: Archive, count: 45 },
  { id: 'trash', name: 'Trash', icon: Trash2, count: 2 }
]

const securityLevels = [
  { level: 'Level 1', name: 'Standard', color: 'bg-green-500', count: 8 },
  { level: 'Level 2', name: 'Enhanced', color: 'bg-yellow-500', count: 3 },
  { level: 'Level 3', name: 'Classified', color: 'bg-orange-500', count: 1 },
  { level: 'Level 4', name: 'Top Secret', color: 'bg-red-500', count: 0 }
]

export const Sidebar: React.FC<SidebarProps> = ({
  onComposeClick,
  onFolderSelect,
  selectedFolder = 'inbox',
  user,
  onLogout,
  folders,
  collapsed = false,
  onToggleCollapse,
  quantumKeysAvailable,
  systemStatus
}) => {
  const effectiveFolders = folders && folders.length > 0 ? folders : defaultFolders
  const statusColor = systemStatus === 'critical' ? 'text-red-600 dark:text-red-400' : systemStatus === 'degraded' ? 'text-yellow-600 dark:text-yellow-400' : 'text-green-600 dark:text-green-400'

  if (collapsed) {
    return (
      <div className="w-16 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col items-center py-4 gap-4 transition-all duration-300 ease-in-out">
        {/* App Logo */}
        <div
          onClick={onToggleCollapse}
          className="qumail-logo-mark bg-gradient-to-br from-blue-500 to-purple-600 shadow-lg cursor-pointer hover:opacity-90"
        >
          <svg className="text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>

        {/* Compose Button */}
        <button
          onClick={onComposeClick}
          className="w-10 h-10 rounded-lg flex items-center justify-center bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-blue-50 hover:text-blue-600 dark:hover:bg-gray-700 transition-all duration-200"
          title="Compose"
        >
          <Edit className="w-5 h-5" />
        </button>
        {effectiveFolders.map(f => (
          <button
            key={f.id}
            onClick={() => onFolderSelect?.(f.id)}
            title={f.name}
            className={`w-10 h-10 rounded-lg flex items-center justify-center text-sm transition-colors ${
              selectedFolder === f.id
                ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-300'
                : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            {React.createElement(f.icon || Inbox, { className: 'w-4 h-4' })}
          </button>
        ))}
        <div className="mt-auto pb-2">
          <button
            onClick={onToggleCollapse}
            className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            ▶
          </button>
        </div>
      </div>
    )
  }
  return (
    <div className="w-64 bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col transition-all duration-300 ease-in-out">
      {/* App Header */}
      <div className="h-20 flex items-center px-6 border-b border-gray-200 dark:border-gray-700">
        <div className="qumail-logo-mark bg-gradient-to-br from-blue-500 to-purple-600 shadow-sm mr-3">
          <svg className="text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        </div>
        <span className="font-bold text-xl text-gray-900 dark:text-white tracking-tight">QuMail</span>
      </div>

      {/* User Profile */}
      {user && (
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
              {user.avatar ? (
                <img src={user.avatar} alt={user.name} className="w-full h-full rounded-full" />
              ) : (
                <User className="w-5 h-5 text-white" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {user.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                {user.email}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Compose Button */}
      <div className="p-4">
        <Button
          onClick={onComposeClick}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
        >
          <Edit className="w-4 h-4 mr-2" />
          Compose
        </Button>
      </div>

      {/* Folder Navigation */}
      <div className="flex-1 overflow-auto">
        <div className="px-4 pb-4">
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            Folders
          </h3>
          <nav className="space-y-1">
            {effectiveFolders.map((folder) => {
              const Icon = (folder as any).icon || Inbox
              const isSelected = selectedFolder === folder.id
              
              return (
                <button
                  key={folder.id}
                  onClick={() => onFolderSelect?.(folder.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 text-sm rounded-lg transition-colors ${
                    isSelected
                      ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{folder.name}</span>
                  </div>
                  {folder.count && folder.count > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {folder.count}
                    </Badge>
                  )}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Security Levels */}
        <div className="px-4 pb-4">
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            Security Levels
          </h3>
          <div className="space-y-2">
            {securityLevels.map((level) => (
              <div
                key={level.level}
                className="flex items-center justify-between px-3 py-2 text-sm rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-2 h-2 rounded-full ${level.color}`} />
                  <span className="text-gray-700 dark:text-gray-300">{level.name}</span>
                </div>
                {level.count > 0 && (
                  <Badge variant="secondary" className="text-xs">
                    {level.count}
                  </Badge>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Quantum Status */}
        <div className="px-4 pb-4">
          <Card className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 border-green-200 dark:border-green-800">
            <CardContent className="p-3 space-y-1">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-green-600 dark:text-green-400" />
                <span className="text-xs font-medium text-green-700 dark:text-green-300">Quantum Status</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-gray-600 dark:text-gray-400">Active Keys:</span>
                <span className="font-medium text-green-600 dark:text-green-400">{quantumKeysAvailable ?? 6400}</span>
              </div>
              {systemStatus && (
                <div className="flex justify-between text-xs">
                  <span className="text-gray-600 dark:text-gray-400">KME Status:</span>
                  <span className={`font-medium ${statusColor}`}>{systemStatus}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="space-y-2">
          {user && (
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-900/20"
              onClick={onLogout}
            >
              <LogOut className="w-4 h-4 mr-2" />
              Sign Out
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

export default Sidebar