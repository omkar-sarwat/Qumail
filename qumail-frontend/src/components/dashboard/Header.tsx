import React, { useState, useRef, useEffect } from 'react'
import { Button } from '../ui/Button'
import { offlineService } from '../../services/offlineService'

interface User {
  id: string
  email: string
  name: string
  picture?: string
}

interface HeaderProps {
  user: User | null
  onCompose: () => void
  onSettings: () => void
  searchQuery: string
  onSearchChange: (query: string) => void
  currentView?: 'email' | 'quantum' | 'keymanager'
  onViewChange?: (view: 'email' | 'quantum' | 'keymanager') => void
  onToggleSidebar: () => void
  isSidebarCollapsed?: boolean
  onRefresh?: () => void
  isRefreshing?: boolean
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onCompose: _onCompose,
  onSettings,
  searchQuery,
  onSearchChange,
  currentView = 'email',
  onViewChange,
  onToggleSidebar,
  isSidebarCollapsed = false,
  onRefresh,
  isRefreshing = false
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  const [isOnline, setIsOnline] = useState(true)
  const [pendingSyncCount, setPendingSyncCount] = useState(0)

  const userMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)

  // Listen for network status changes
  useEffect(() => {
    const unsubscribe = offlineService.addNetworkListener((status) => {
      setIsOnline(status.isOnline)
    })

    // Get pending sync count
    const updateSyncCount = async () => {
      const count = await offlineService.getPendingSyncCount()
      setPendingSyncCount(count)
    }
    updateSyncCount()
    const syncCountInterval = setInterval(updateSyncCount, 10000) // Every 10 seconds

    return () => {
      unsubscribe()
      clearInterval(syncCountInterval)
    }
  }, [])

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false)
      }
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setShowSearchSuggestions(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  // Simulate search delay
  useEffect(() => {
    if (searchQuery) {
      setIsSearching(true)
      const timer = setTimeout(() => setIsSearching(false), 500)
      return () => clearTimeout(timer)
    }
  }, [searchQuery])

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    window.location.href = '/login'
  }

      return (
        <header className="relative z-50 h-20 bg-white border-b border-gray-200 flex items-center px-4 flex-shrink-0">
          {/* Left: Logo/Toggle - Width tracks sidebar state */}
          <div className={`${isSidebarCollapsed ? 'w-24' : 'w-64'} flex items-center gap-3 flex-shrink-0 pr-4 transition-all duration-300`}>
            <button
              onClick={onToggleSidebar}
              className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
              aria-label="Toggle sidebar"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            <div className="flex items-center">
              {isSidebarCollapsed ? (
                <img src="/qumail-icon.svg" alt="QuMail" className="h-9 w-auto" />
              ) : (
                <img src="/qumail-logo.svg" alt="QuMail" className="h-10 w-auto" />
              )}
            </div>
          </div>

          {/* Center: Search - Flexible with max width */}
          <div className="flex-1 max-w-3xl px-6" ref={searchRef}>
            <div className="relative group">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                {isSearching ? (
                  <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <svg className="w-5 h-5 text-gray-400 group-focus-within:text-blue-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                )}
              </div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onFocus={() => setShowSearchSuggestions(true)}
                onBlur={() => {
                  setTimeout(() => setShowSearchSuggestions(false), 200)
                }}
                placeholder="Search emails..."
                className="block w-full pl-10 pr-16 py-2.5 border border-gray-200 rounded-xl bg-gray-50 text-gray-900 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white transition-all duration-200 shadow-sm"
              />

              {/* Search Actions */}
              <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-1.5">
                {searchQuery && (
                  <button
                    onClick={() => onSearchChange('')}
                    className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
                <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-500 bg-white border border-gray-200 rounded-md shadow-sm">
                  ⌘K
                </kbd>
              </div>

              {/* Email Search Suggestions */}
              {showSearchSuggestions && searchQuery && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl shadow-xl border border-gray-100 overflow-hidden z-50 animate-in fade-in slide-in-from-top-2 duration-200">
                  <div className="p-2">
                    <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2 py-1.5">Search Results</div>
                    <div className="space-y-0.5">
                      {['Recent email from ' + searchQuery, 'Encrypted messages containing "' + searchQuery + '"', 'Emails in folder: ' + searchQuery].map((search, index) => (
                        <button
                          key={index}
                          onClick={() => onSearchChange(search)}
                          className="flex items-center gap-3 w-full p-2 rounded-lg hover:bg-gray-50 transition-colors text-left group/item"
                        >
                          <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center group-hover/item:bg-blue-50 group-hover/item:text-blue-600 transition-colors">
                            <svg className="w-4 h-4 text-gray-500 group-hover/item:text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                            </svg>
                          </div>
                          <span className="text-sm text-gray-700 font-medium">{search}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-3 ml-auto">
            {/* View Switcher */}
            {currentView === 'quantum' && onViewChange && (
              <Button
                onClick={() => onViewChange('email')}
                variant="outline"
                className="px-3 py-2 text-xs font-semibold text-gray-700 border-gray-200 bg-white hover:bg-gray-50 flex items-center gap-2 transition-all duration-200 rounded-lg shadow-sm"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
                <span>Back to Email</span>
              </Button>
            )}

            {/* Network Status Indicator */}
            <div className="flex items-center gap-2">
              {!isOnline ? (
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-amber-50 border border-amber-200 rounded-lg">
                  <div className="w-2 h-2 bg-amber-500 rounded-full animate-pulse"></div>
                  <span className="text-xs font-medium text-amber-700">Offline</span>
                  {pendingSyncCount > 0 && (
                    <span className="text-xs text-amber-600">({pendingSyncCount} pending)</span>
                  )}
                </div>
              ) : pendingSyncCount > 0 ? (
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-blue-50 border border-blue-200 rounded-lg">
                  <svg className="w-3 h-3 text-blue-500 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span className="text-xs font-medium text-blue-700">Syncing...</span>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-green-50 border border-green-200 rounded-lg" title="Connected & synced">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span className="text-xs font-medium text-green-700">Online</span>
                </div>
              )}
            </div>

            {/* Refresh Button */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors relative disabled:opacity-50"
                title="Refresh emails"
              >
                <svg 
                  className={`w-6 h-6 ${isRefreshing ? 'animate-spin' : ''}`} 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}

            {/* User Profile Menu */}
            <div className="relative ml-1" ref={userMenuRef}>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-3 pl-2 pr-1 py-1 hover:bg-gray-100 rounded-full transition-all duration-200 border border-transparent hover:border-gray-200"
              >
                {user && user.picture ? (
                  <img
                    src={user.picture}
                    alt={user?.name || 'User'}
                    className="w-9 h-9 rounded-full object-cover border-2 border-white shadow-sm"
                  />
                ) : (
                  <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-sm text-white font-medium text-sm">
                    {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </div>
                )}
                <div className="hidden lg:block text-left mr-1">
                  <p className="font-semibold text-gray-900 text-sm leading-none">
                    {user?.name?.split(' ')[0] || 'User'}
                  </p>
                </div>
                <svg className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${showUserMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {/* Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-gray-100 z-50 animate-in fade-in zoom-in-95 duration-100 origin-top-right">
                  {/* User Info Header */}
                  <div className="p-4 border-b border-gray-100 bg-gray-50/50 rounded-t-xl">
                    <div className="flex items-center gap-3">
                      {user && user.picture ? (
                        <img
                          src={user.picture}
                          alt={user?.name || 'User'}
                          className="w-10 h-10 rounded-full object-cover border-2 border-white shadow-sm"
                        />
                      ) : (
                        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-sm text-white font-medium">
                          {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate">
                          {user?.name || 'User'}
                        </p>
                        <p className="text-xs text-gray-500 truncate">
                          {user?.email || 'user@example.com'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Menu Items */}
                  <div className="p-2">
                    <button
                      onClick={() => {
                        setShowUserMenu(false)
                        onSettings()
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                    >
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      Settings
                    </button>
                    <div className="h-px bg-gray-100 my-1"></div>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                      </svg>
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>
      )
    }