import { useEffect, useState, useCallback } from 'react';

interface ConnectionStatus {
  isOnline: boolean;
  isSlowConnection: boolean;
  connectionType: string | null;
  effectiveType: string | null;
  downlink: number | null;
  rtt: number | null;
}

/**
 * Hook to monitor network connection status
 */
export function useConnectionStatus(): ConnectionStatus {
  const [status, setStatus] = useState<ConnectionStatus>(() => ({
    isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
    isSlowConnection: false,
    connectionType: null,
    effectiveType: null,
    downlink: null,
    rtt: null,
  }));

  const updateConnectionInfo = useCallback(() => {
    const connection = (navigator as any).connection || 
                       (navigator as any).mozConnection || 
                       (navigator as any).webkitConnection;

    const newStatus: ConnectionStatus = {
      isOnline: navigator.onLine,
      isSlowConnection: false,
      connectionType: connection?.type || null,
      effectiveType: connection?.effectiveType || null,
      downlink: connection?.downlink || null,
      rtt: connection?.rtt || null,
    };

    // Detect slow connection
    if (connection) {
      const slowTypes = ['slow-2g', '2g'];
      newStatus.isSlowConnection = slowTypes.includes(connection.effectiveType) ||
                                    (connection.downlink && connection.downlink < 0.5) ||
                                    (connection.rtt && connection.rtt > 1000);
    }

    setStatus(newStatus);
  }, []);

  useEffect(() => {
    // Initial update
    updateConnectionInfo();

    // Listen for online/offline events
    const handleOnline = () => {
      setStatus(prev => ({ ...prev, isOnline: true }));
      updateConnectionInfo();
    };

    const handleOffline = () => {
      setStatus(prev => ({ ...prev, isOnline: false }));
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Listen for connection changes
    const connection = (navigator as any).connection || 
                       (navigator as any).mozConnection || 
                       (navigator as any).webkitConnection;

    if (connection) {
      connection.addEventListener('change', updateConnectionInfo);
    }

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (connection) {
        connection.removeEventListener('change', updateConnectionInfo);
      }
    };
  }, [updateConnectionInfo]);

  return status;
}

/**
 * Hook to detect if the app is focused/visible
 */
export function useAppVisibility(): boolean {
  const [isVisible, setIsVisible] = useState(() => 
    typeof document !== 'undefined' ? document.visibilityState === 'visible' : true
  );

  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsVisible(document.visibilityState === 'visible');
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  return isVisible;
}

/**
 * Hook to detect if the window is focused
 */
export function useWindowFocus(): boolean {
  const [isFocused, setIsFocused] = useState(() => 
    typeof document !== 'undefined' ? document.hasFocus() : true
  );

  useEffect(() => {
    const handleFocus = () => setIsFocused(true);
    const handleBlur = () => setIsFocused(false);

    window.addEventListener('focus', handleFocus);
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('focus', handleFocus);
      window.removeEventListener('blur', handleBlur);
    };
  }, []);

  return isFocused;
}

export default useConnectionStatus;
