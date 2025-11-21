import React from 'react'
import { motion } from 'framer-motion'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  text?: string
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'md', 
  className = '',
  text 
}) => {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12'
  }

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
        className={`${sizeClasses[size]} border-2 border-gray-200 dark:border-gray-700 border-t-blue-600 dark:border-t-blue-400 rounded-full`}
      />
      {text && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 font-medium">
          {text}
        </p>
      )}
    </div>
  )
}

export const EmailListSkeleton: React.FC = () => {
  return (
    <div className="p-4 space-y-4">
      {[...Array(8)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="flex items-start space-x-3 p-3">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full loading-shimmer" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" style={{ width: `${Math.random() * 40 + 60}%` }} />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" style={{ width: `${Math.random() * 30 + 50}%` }} />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" style={{ width: `${Math.random() * 50 + 40}%` }} />
            </div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-16" />
          </div>
        </div>
      ))}
    </div>
  )
}

export const EmailViewerSkeleton: React.FC = () => {
  return (
    <div className="h-full flex flex-col bg-white dark:bg-gray-800">
      <div className="flex-shrink-0 p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="animate-pulse space-y-4">
          {/* Action buttons skeleton */}
          <div className="flex items-center space-x-2 mb-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-8 w-16 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" />
            ))}
          </div>
          
          {/* Subject skeleton */}
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-3/4" />
          
          {/* Sender info skeleton */}
          <div className="flex items-center space-x-4">
            <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full loading-shimmer" />
            <div className="flex-1 space-y-2">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-1/3" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-1/2" />
            </div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer w-20" />
          </div>
        </div>
      </div>
      
      {/* Content skeleton */}
      <div className="flex-1 p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded loading-shimmer" style={{ width: `${Math.random() * 30 + 70}%` }} />
          ))}
        </div>
      </div>
    </div>
  )
}