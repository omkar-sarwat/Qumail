import React, { useEffect } from 'react'
import { motion } from 'framer-motion'
import { useAuthStore } from '../../stores/authStore'
import { useEmailStore } from '../../stores/emailStore'
import { useKMEStore } from '../../stores/kmeStore'
import { Button } from '../ui/Button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/Card'

export const Dashboard: React.FC = () => {
  const { user, logout } = useAuthStore()
  const { emails, fetchEmails, isLoading: emailsLoading } = useEmailStore()
  const { 
    kmeServers, 
    quantumKeysAvailable, 
    overallStatus, 
    connectionQuality, 
    fetchKMEStatus,
    isLoading: kmeLoading 
  } = useKMEStore()

  useEffect(() => {
    // Initialize data on component mount
    fetchEmails()
    fetchKMEStatus()
  }, [fetchEmails, fetchKMEStatus])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'excellent':
        return 'text-green-600 bg-green-100'
      case 'degraded':
      case 'good':
        return 'text-yellow-600 bg-yellow-100'
      case 'critical':
      case 'poor':
      case 'offline':
        return 'text-red-600 bg-red-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.6, staggerChildren: 0.1 }
    }
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { duration: 0.4 }
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-50 dark:bg-gray-900 overflow-hidden h-full">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6">
          <div className="flex justify-between items-center h-12">
            <div className="flex items-center">
              <div className="w-6 h-6 bg-gradient-to-br from-blue-600 to-purple-600 rounded flex items-center justify-center mr-2">
                <svg className="w-3.5 h-3.5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h1 className="text-base font-semibold text-gray-900 dark:text-white">
                QuMail Dashboard
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              <div className="text-xs text-gray-600 dark:text-gray-300">
                Welcome, {user?.displayName || user?.email}
              </div>
              <Button onClick={logout} variant="outline" size="sm">
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden">
        <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-6 py-4">
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="space-y-4"
        >
          {/* Status Cards Row */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Security Status */}
            <motion.div variants={cardVariants}>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <svg className="w-4 h-4 mr-1.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    Security Status
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-300">Overall</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(overallStatus)}`}>
                        {overallStatus.charAt(0).toUpperCase() + overallStatus.slice(1)}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-300">Connection</span>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(connectionQuality)}`}>
                        {connectionQuality.charAt(0).toUpperCase() + connectionQuality.slice(1)}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Quantum Keys */}
            <motion.div variants={cardVariants}>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <svg className="w-4 h-4 mr-1.5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                    Quantum Keys
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {quantumKeysAvailable.toLocaleString()}
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-300">Available for encryption</p>
                </CardContent>
              </Card>
            </motion.div>

            {/* Email Count */}
            <motion.div variants={cardVariants}>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center">
                    <svg className="w-4 h-4 mr-1.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                    </svg>
                    Total Emails
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-xl font-bold text-gray-900 dark:text-white">
                    {emails.length}
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-300">
                    {emailsLoading ? 'Loading...' : 'In your mailbox'}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* KME Servers Status */}
          <motion.div variants={cardVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-sm">
                  <span>KME Servers Status</span>
                  {kmeLoading && (
                    <svg className="animate-spin h-4 w-4 text-gray-400" viewBox="0 0 24 24">
                      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25" fill="none" />
                      <path fill="currentColor" className="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  )}
                </CardTitle>
                <CardDescription className="text-xs">
                  Real-time status of Quantum Key Management servers
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {kmeServers.length === 0 ? (
                    <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                      No KME servers available
                    </p>
                  ) : (
                    kmeServers.map((server) => (
                      <div key={server.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className={`w-2.5 h-2.5 rounded-full ${
                            server.status === 'connected' 
                              ? 'bg-green-500' 
                              : server.status === 'disconnected'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`} />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white">{server.name}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">{server.url}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs font-medium text-gray-900 dark:text-white">
                            {server.latency ? `${server.latency}ms` : '—'}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {server.keysAvailable} keys available
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Emails */}
          <motion.div variants={cardVariants}>
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Recent Emails</CardTitle>
                <CardDescription className="text-xs">
                  Latest quantum-encrypted messages
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {emails.length === 0 ? (
                    <p className="text-xs text-gray-500 dark:text-gray-400 text-center py-3">
                      {emailsLoading ? 'Loading emails...' : 'No emails found'}
                    </p>
                  ) : (
                    emails.slice(0, 5).map((email) => (
                      <div key={email.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className={`w-1.5 h-1.5 rounded-full ${
                            email.securityLevel === 1 ? 'bg-purple-500' :
                            email.securityLevel === 2 ? 'bg-blue-500' :
                            email.securityLevel === 3 ? 'bg-green-500' :
                            'bg-gray-500'
                          }`} />
                          <div>
                            <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-xs">
                              {email.subject || 'No Subject'}
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                              from {email.fromAddress}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            Level {email.securityLevel} Security
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">
                            {new Date(email.timestamp).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </motion.div>
        </div>
      </main>
    </div>
  )
}