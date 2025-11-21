import React, { useState, useRef, useEffect } from 'react'
import { Button } from '../ui/Button'

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
  currentView?: 'email' | 'quantum'
  onViewChange?: (view: 'email' | 'quantum') => void
}

export const Header: React.FC<HeaderProps> = ({
  user,
  onCompose,
  onSettings,
  searchQuery,
  onSearchChange,
  currentView = 'email',
  onViewChange
}) => {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showSearchSuggestions, setShowSearchSuggestions] = useState(false)
  const [isSearching, setIsSearching] = useState(false)
  
  const userMenuRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLDivElement>(null)



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
    <header className="bg-white dark:bg-[#0d1117] border-b border-gray-200 dark:border-gray-800 px-4 py-2 z-50">
      <div className="flex items-center justify-between">
        {/* Professional Logo and Brand */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-3">
            {/* Clean Professional Logo */}
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
                QuMail
              </h1>
            </div>
          </div>
          
          {/* Status Indicators */}
          <div className="hidden lg:flex items-center gap-2">
            <div className="flex items-center gap-1.5 text-xs text-gray-600 dark:text-gray-400">
              <div className="w-2 h-2 rounded-full bg-green-500"></div>
              <span className="font-medium">QKD Active</span>
            </div>
          </div>
        </div>

        {/* Professional Search Bar */}
        <div className="flex-1 max-w-xl mx-6" ref={searchRef}>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              {isSearching ? (
                <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
              ) : (
                <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
              className="block w-full pl-10 pr-16 py-2.5 border border-gray-300 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm transition-colors"
            />
            
            {/* Search Actions */}
            <div className="absolute inset-y-0 right-0 flex items-center pr-2 gap-1.5">
              {searchQuery && (
                <button
                  onClick={() => onSearchChange('')}
                  className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              )}
              <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.5 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded">
                ⌘K
              </kbd>
            </div>
          </div>
          
          {/* Email Search Suggestions */}
          {showSearchSuggestions && searchQuery && (
            <div className="absolute top-full left-0 right-0 mt-1.5 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
              <div className="p-2">
                <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">Search Results</div>
                <div className="space-y-0.5">
                  {['Recent email from ' + searchQuery, 'Encrypted messages containing "' + searchQuery + '"', 'Emails in folder: ' + searchQuery].map((search, index) => (
                    <button
                      key={index}
                      onClick={() => onSearchChange(search)}
                      className="flex items-center gap-1.5 w-full p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-left"
                    >
                      <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                      <span className="text-xs text-gray-700 dark:text-gray-300">{search}</span>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Action Bar */}
        <div className="flex items-center gap-2">

          {/* View Switcher */}
          {currentView === 'quantum' && onViewChange && (
            <Button
              onClick={() => onViewChange('email')}
              variant="outline"
              className="px-3 py-1.5 text-xs font-semibold text-gray-700 border-gray-300 bg-white hover:bg-gray-50 dark:text-gray-300 dark:border-gray-600 dark:hover:bg-gray-700 flex items-center space-x-1.5 transition-all duration-200 rounded-xl hover:scale-105"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <span>Back to Email</span>
            </Button>
          )}
          
          {/* Compose Button */}
          {currentView === 'email' && (
            <Button
              onClick={onCompose}
              className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Compose</span>
            </Button>
          )}

          {/* Settings Button */}
          <Button
            onClick={onSettings}
            variant="ghost"
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </Button>

          {/* User Profile Menu */}
          <div className="relative" ref={userMenuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2.5 text-sm hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg px-3 py-1.5 transition-colors"
            >
              {user && user.picture ? (
                <img
                  src={user.picture}
                  alt={user?.name || 'User'}
                  className="w-8 h-8 rounded-full object-cover"
                />
              ) : (
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <span className="text-white text-sm font-medium">
                    {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                  </span>
                </div>
              )}
              <div className="hidden lg:block text-left">
                <p className="font-medium text-gray-900 dark:text-white text-sm truncate max-w-24">
                  {user?.name?.split(' ')[0] || 'User'}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 truncate max-w-24">
                  {user?.email || 'user@example.com'}
                </p>
              </div>
              <svg className={`w-4 h-4 text-gray-400 transition-transform ${showUserMenu ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-1.5 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                {/* User Info Header */}
                <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    {user && user.picture ? (
                      <img
                        src={user.picture}
                        alt={user?.name || 'User'}
                        className="w-8 h-8 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                        <span className="text-white text-sm font-medium">
                          {user?.name?.charAt(0) || user?.email?.charAt(0) || 'U'}
                        </span>
                      </div>
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {user?.name || 'User'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {user?.email || 'user@example.com'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Logout Button */}
                <div className="p-1.5">
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-3 py-1.5 text-left text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                    </svg>
                    <span>Sign Out</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}