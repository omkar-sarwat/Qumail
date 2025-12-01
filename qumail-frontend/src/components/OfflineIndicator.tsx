import React from 'react';
import { useConnectionStatus } from '../hooks/useConnectionStatus';

/**
 * Displays an offline banner when the user loses internet connection
 */
export const OfflineIndicator: React.FC = () => {
  const { isOnline, isSlowConnection } = useConnectionStatus();

  if (isOnline && !isSlowConnection) {
    return null;
  }

  return (
    <div
      className={`fixed top-0 left-0 right-0 z-[9999] transition-all duration-300 ${
        !isOnline
          ? 'bg-red-600 text-white'
          : 'bg-yellow-500 text-yellow-900'
      }`}
    >
      <div className="px-4 py-2 text-center text-sm font-medium flex items-center justify-center gap-2">
        {!isOnline ? (
          <>
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
              />
            </svg>
            <span>You're offline. Some features may not be available.</span>
          </>
        ) : (
          <>
            <svg
              className="w-4 h-4"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span>Slow connection detected. Some operations may take longer.</span>
          </>
        )}
      </div>
    </div>
  );
};

export default OfflineIndicator;
