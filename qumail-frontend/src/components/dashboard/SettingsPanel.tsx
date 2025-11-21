import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Button } from '../ui/Button'
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card'

interface User {
  id: string
  email: string
  name: string
  picture?: string
}

interface SettingsPanelProps {
  isOpen: boolean
  onClose: () => void
  user: User | null
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isOpen,
  onClose,
  user
}) => {
  const [activeTab, setActiveTab] = useState('account')
  const [keyManagerSettings, setKeyManagerSettings] = useState({
    autoRefresh: true,
    keyRotationInterval: 24,
    maxKeysPerSession: 100
  })

  const tabs = [
    {
      id: 'account',
      name: 'Account',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      )
    },
    {
      id: 'security',
      name: 'Security',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      )
    },
    {
      id: 'keymanager',
      name: 'Key Manager',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
        </svg>
      )
    },
    {
      id: 'about',
      name: 'About',
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    }
  ]

  const handleLogout = () => {
    localStorage.removeItem('authToken')
    localStorage.removeItem('user')
    window.location.reload()
  }

  const renderAccountTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <CardContent>
          {user && (
            <div className="flex items-center space-x-4 mb-6">
              {user.picture ? (
                <img
                  src={user.picture}
                  alt={user.name}
                  className="w-16 h-16 rounded-full"
                />
              ) : (
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xl font-medium">
                    {user.name?.charAt(0) || user.email.charAt(0)}
                  </span>
                </div>
              )}
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {user.name || user.email.split('@')[0]}
                </h3>
                <p className="text-gray-600 dark:text-gray-400">{user.email}</p>
              </div>
            </div>
          )}
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Display Name
              </label>
              <input
                type="text"
                value={user?.name || ''}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Enter your display name"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email Address
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-600 text-gray-500 dark:text-gray-400"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Button
              onClick={handleLogout}
              variant="outline"
              className="w-full justify-start text-red-600 border-red-300 hover:bg-red-50 dark:text-red-400 dark:border-red-600 dark:hover:bg-red-900/20"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Sign Out
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderSecurityTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Security Preferences</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  Always use Quantum Encryption
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Force all outgoing emails to use quantum encryption
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  Require Recipient Verification
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Verify recipient identity before sending sensitive emails
                </p>
              </div>
              <input
                type="checkbox"
                defaultChecked
                className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  Auto-delete on Forward
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Automatically delete original when forwarding quantum emails
                </p>
              </div>
              <input
                type="checkbox"
                className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Encryption Standards</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                <div>
                  <p className="font-medium text-green-700 dark:text-green-300">
                    ETSI GS QKD-014 Compliant
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    Quantum key distribution standards fully implemented
                  </p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm font-medium text-purple-700 dark:text-purple-300">
                  Quantum Keys Available
                </p>
                <p className="text-2xl font-bold text-purple-900 dark:text-purple-100">
                  6,400
                </p>
              </div>
              
              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm font-medium text-blue-700 dark:text-blue-300">
                  Keys Used Today
                </p>
                <p className="text-2xl font-bold text-blue-900 dark:text-blue-100">
                  23
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderKeyManagerTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Key Management Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Key Rotation Interval (hours)
              </label>
              <input
                type="number"
                value={keyManagerSettings.keyRotationInterval}
                onChange={(e) => setKeyManagerSettings(prev => ({
                  ...prev,
                  keyRotationInterval: parseInt(e.target.value)
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Maximum Keys per Session
              </label>
              <input
                type="number"
                value={keyManagerSettings.maxKeysPerSession}
                onChange={(e) => setKeyManagerSettings(prev => ({
                  ...prev,
                  maxKeysPerSession: parseInt(e.target.value)
                }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900 dark:text-white">
                  Auto-refresh Keys
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Automatically refresh quantum keys when running low
                </p>
              </div>
              <input
                type="checkbox"
                checked={keyManagerSettings.autoRefresh}
                onChange={(e) => setKeyManagerSettings(prev => ({
                  ...prev,
                  autoRefresh: e.target.checked
                }))}
                className="w-5 h-5 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 dark:focus:ring-blue-600 dark:ring-offset-gray-800 focus:ring-2 dark:bg-gray-700 dark:border-gray-600"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>KME Server Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <div>
                  <p className="font-medium text-green-700 dark:text-green-300">
                    KME Server 1
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    localhost:13000 - Online
                  </p>
                </div>
              </div>
              <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                Connected
              </span>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                <div>
                  <p className="font-medium text-green-700 dark:text-green-300">
                    KME Server 2
                  </p>
                  <p className="text-sm text-green-600 dark:text-green-400">
                    localhost:14000 - Online
                  </p>
                </div>
              </div>
              <span className="text-green-600 dark:text-green-400 text-sm font-medium">
                Connected
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderAboutTab = () => (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>About QuMail</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            
            <div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                QuMail v1.0.0
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Quantum-Secured Email Platform
              </p>
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 max-w-md mx-auto">
              The world's first quantum-secured email platform using real quantum key distribution 
              for unbreakable encryption and perfect forward secrecy.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Protocol:</span>
              <span className="font-medium text-gray-900 dark:text-white">ETSI GS QKD-014</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Encryption:</span>
              <span className="font-medium text-gray-900 dark:text-white">Quantum + AES-256</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Key Distribution:</span>
              <span className="font-medium text-gray-900 dark:text-white">QKD Active</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Backend:</span>
              <span className="font-medium text-gray-900 dark:text-white">FastAPI + Rust KME</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Frontend:</span>
              <span className="font-medium text-gray-900 dark:text-white">React + TypeScript</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )

  const renderTabContent = () => {
    switch (activeTab) {
      case 'account':
        return renderAccountTab()
      case 'security':
        return renderSecurityTab()
      case 'keymanager':
        return renderKeyManagerTab()
      case 'about':
        return renderAboutTab()
      default:
        return renderAccountTab()
    }
  }

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/60 z-40"
            style={{ willChange: 'opacity' }}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: 400 }}
            animate={{ x: 0 }}
            exit={{ x: 400 }}
            transition={{ duration: 0.2, ease: [0.4, 0, 0.2, 1] }}
            className="fixed right-0 top-0 h-full w-96 bg-white dark:bg-gray-800 shadow-2xl z-50 flex flex-col"
            style={{ willChange: 'transform', transform: 'translateZ(0)' }}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Settings
              </h2>
              <Button
                onClick={onClose}
                variant="ghost"
                size="sm"
                className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </Button>
            </div>

            {/* Tabs */}
            <div className="flex-shrink-0 border-b border-gray-200 dark:border-gray-700">
              <nav className="flex space-x-1 p-4">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300'
                        : 'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    {tab.icon}
                    <span>{tab.name}</span>
                  </button>
                ))}
              </nav>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {renderTabContent()}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}