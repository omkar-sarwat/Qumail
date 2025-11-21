import React, { useState, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { Inbox, Send, Star, Archive, Trash2, Shield, Folder, PenSquare } from 'lucide-react'
import { useAuthStore } from '../../stores/authStore'
import { useEmailStore } from '../../stores/emailStore'
import { useKMEStore } from '../../stores/kmeStore'
import { Button } from '../ui/Button'
import { ComposeEmailModal } from './ComposeEmailModal'
import { EmailList } from './EmailList'
import { EmailDetails } from './EmailDetails'
// Import via layout barrel to avoid transient path resolution issue
import { Sidebar } from './Sidebar'
import { apiService } from '../../services/api'

// We now rely on the central email store's Email type; keep lightweight projection for UI logic only when needed
interface UIEmailSummary {
  id: string
  subject: string
  snippet: string
  timestamp: string
  isRead: boolean
  isStarred: boolean
  securityLevel: string | number
  from: string
  source?: string
  labels?: string[]
}

interface Folder {
  id: string
  name: string
  count: number
  icon?: React.ComponentType<{ className?: string }>
  type: 'gmail' | 'quantum' | 'system'
}

const folderIconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  inbox: Inbox,
  sent: Send,
  starred: Star,
  star: Star,
  drafts: PenSquare,
  draft: PenSquare,
  trash: Trash2,
  bin: Trash2,
  archive: Archive,
  quantum: Shield,
  gmail: Inbox,
}

const resolveFolderIcon = (folder: Partial<Folder> & { icon?: any }) => {
  if (folder.icon && typeof folder.icon === 'function') {
    return folder.icon as React.ComponentType<{ className?: string }>
  }

  const iconKey = typeof folder.icon === 'string' ? folder.icon.toLowerCase() : ''
  if (iconKey && folderIconMap[iconKey]) {
    return folderIconMap[iconKey]
  }

  const normalizedId = (folder.id || '').toLowerCase()
  const normalizedName = (folder.name || '').toLowerCase()

  if ((folder.type || '').toLowerCase() === 'quantum' || normalizedId.startsWith('quantum_')) {
    return Shield
  }
  if (normalizedId.includes('inbox') || normalizedName.includes('inbox')) {
    return Inbox
  }
  if (normalizedId.includes('sent') || normalizedName.includes('sent')) {
    return Send
  }
  if (normalizedId.includes('draft')) {
    return PenSquare
  }
  if (normalizedId.includes('star')) {
    return Star
  }
  if (normalizedId.includes('trash') || normalizedId.includes('bin')) {
    return Trash2
  }
  if (normalizedId.includes('archive')) {
    return Archive
  }

  return Folder
}

export const ModernEmailDashboard: React.FC = () => {
  const { user, logout } = useAuthStore()
  const { isLoading: emailsLoading, emails, fetchEmails, selectEmail, selectedEmailId } = useEmailStore()
  const { quantumKeysAvailable, overallStatus, fetchKMEStatus } = useKMEStore()
  
  const [selectedFolder, setSelectedFolder] = useState('inbox')
  const [selectedEmail, setSelectedEmail] = useState<UIEmailSummary | null>(null)
  const [isComposeOpen, setIsComposeOpen] = useState(false)
  const [emailList, setEmailList] = useState<UIEmailSummary[]>([])
  const [folders, setFolders] = useState<Folder[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  useEffect(() => {
    initializeDashboard()
  }, [])

  useEffect(() => {
    // Trigger email fetch via store
    fetchEmails({ folder: selectedFolder as any }, true)
  }, [selectedFolder, fetchEmails])

  // Auto-refresh emails every 30 seconds
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      console.log('🔄 Auto-refreshing emails...')
      setLastRefresh(new Date())
      fetchEmails({ folder: selectedFolder as any }, true)
    }, 30000) // 30 seconds

    return () => clearInterval(refreshInterval)
  }, [selectedFolder, fetchEmails])

  // Keep local UI list in sync when store emails change
  useEffect(() => {
    const mapped = emails.map(e => ({
      id: e.id,
      subject: e.subject,
      snippet: e.snippet,
      timestamp: e.timestamp,
      isRead: e.isRead,
      isStarred: e.isStarred,
      securityLevel: e.securityLevel,
      from: e.sender || e.fromAddress || e.recipient || 'Unknown sender',
      source: e.source || (e.id?.startsWith('gmail_') ? 'gmail' : 'qumail'),
      labels: e.labels,
    }))
    setEmailList(mapped)
    if (selectedEmailId) {
      const sel = mapped.find(m => m.id === selectedEmailId) || null
      setSelectedEmail(sel)
    }
  }, [emails, selectedEmailId])

  const initializeDashboard = async () => {
    try {
      // Fetch folders via API (real data only)
      const foldersData = await apiService.getEmailFolders().catch(() => [])
      const normalizedFolders = (Array.isArray(foldersData) ? foldersData : []).map((folder) => ({
        ...folder,
        icon: resolveFolderIcon(folder),
      })) as Folder[]

      setFolders(normalizedFolders)
      // Fetch initial inbox emails
      setLastRefresh(new Date())
      fetchEmails({ folder: 'inbox' }, true)
      // Fetch KME status
      fetchKMEStatus()
    } catch (error) {
      console.error('Failed to initialize dashboard:', error)
    }
  }

  const handleEmailSelect = (email: UIEmailSummary) => {
    setSelectedEmail(email)
    selectEmail(email.id)
  }

  const handleCompose = () => {
    setIsComposeOpen(true)
  }

  const handleEmailSent = () => {
    fetchEmails({ folder: selectedFolder as any }, true)
    setIsComposeOpen(false)
  }

  const handleRefresh = () => {
    console.log('🔄 Manual refresh triggered')
    toast.loading('Refreshing emails...', { duration: 1000 })
    setLastRefresh(new Date())
    fetchEmails({ folder: selectedFolder as any }, true)
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    // In a real implementation, this would trigger an API call with search parameters
  }

  const filteredEmails = emailList.filter(email =>
    email.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.from.toLowerCase().includes(searchQuery.toLowerCase()) ||
    email.snippet.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        folders={folders as any}
        selectedFolder={selectedFolder}
        onFolderSelect={setSelectedFolder}
  onComposeClick={handleCompose}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
    user={user ? { name: user.displayName || user.email, email: user.email } : undefined}
        quantumKeysAvailable={quantumKeysAvailable}
        systemStatus={overallStatus}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
                className="lg:hidden p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white flex items-center">
                <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                QuMail Secure
              </h1>
            </div>

            {/* Search Bar */}
            <div className="flex-1 max-w-2xl mx-8">
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                </div>
                <input
                  type="text"
                  placeholder="Search emails..."
                  value={searchQuery}
                  onChange={(e) => handleSearch(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-4">
              {/* Refresh Button */}
              <button
                onClick={handleRefresh}
                className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                title="Refresh emails"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              
              {/* Last Refresh Timestamp */}
              {lastRefresh && (
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </div>
              )}
              
              <div className="text-sm text-gray-600 dark:text-gray-300">
                {user?.displayName || user?.email}
              </div>
              <Button
                onClick={logout}
                variant="outline"
                size="sm"
                className="text-gray-600 hover:text-gray-900"
              >
                Logout
              </Button>
            </div>
          </div>
        </header>

        {/* Email Content */}
        <div className="flex-1 flex overflow-hidden">
          {/* Email List */}
          <div className="w-1/3 border-r border-gray-200 dark:border-gray-700 flex flex-col">
            <EmailList
              emails={filteredEmails as any}
              selectedEmail={selectedEmail as any}
              onEmailSelect={handleEmailSelect as any}
              isLoading={emailsLoading}
              folderName={folders.find(f => f.id === selectedFolder)?.name || 'Inbox'}
            />
          </div>

          {/* Email Details */}
          <div className="flex-1">
            <EmailDetails
              email={selectedEmail as any}
              onReply={() => setIsComposeOpen(true)}
              onForward={() => setIsComposeOpen(true)}
            />
          </div>
        </div>
      </div>

      {/* Compose Modal */}
      <AnimatePresence>
        {isComposeOpen && (
          <ComposeEmailModal
            isOpen={isComposeOpen}
            onClose={() => setIsComposeOpen(false)}
            onSent={handleEmailSent}
            quantumKeysAvailable={quantumKeysAvailable}
          />
        )}
      </AnimatePresence>
    </div>
  )
}