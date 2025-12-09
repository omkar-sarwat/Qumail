/**
 * Secure credential storage for email accounts
 * 
 * Uses:
 * - Browser: Session storage (cleared when browser closes)
 * - Local storage (to survive browser restarts)
 * - In-memory cache for quick access
 * 
 * Note: Persisting to localStorage keeps passwords across browser restarts. This
 * improves UX for repeated logins but is less secure than memory/session only.
 */

// In-memory cache for credentials (cleared on page reload)
const credentialCache = new Map<string, string>()

/**
 * Store a password for an email account
 */
export function storePassword(accountId: string, password: string): void {
  // Store in memory
  credentialCache.set(accountId, password)
  
  // Use session storage (cleared when browser closes)
  try {
    sessionStorage.setItem(`qumail_pwd_${accountId}`, btoa(password))
  } catch (err) {
    console.warn('Failed to store in session storage:', err)
  }

  // Persist in local storage so users do not need to re-authenticate on reload
  try {
    localStorage.setItem(`qumail_pwd_${accountId}`, btoa(password))
  } catch (err) {
    console.warn('Failed to store in local storage:', err)
  }
}

/**
 * Retrieve a password for an email account
 */
export function getPassword(accountId: string): string | null {
  // Check memory cache first
  if (credentialCache.has(accountId)) {
    return credentialCache.get(accountId) || null
  }
  
  // Check session storage
  try {
    const stored = sessionStorage.getItem(`qumail_pwd_${accountId}`)
    if (stored) {
      const password = atob(stored)
      credentialCache.set(accountId, password)
      return password
    }
  } catch (err) {
    console.warn('Failed to retrieve from session storage:', err)
  }

  // Check local storage as long-lived fallback
  try {
    const stored = localStorage.getItem(`qumail_pwd_${accountId}`)
    if (stored) {
      const password = atob(stored)
      credentialCache.set(accountId, password)
      // Keep session storage in sync for current tab lifecycle
      sessionStorage.setItem(`qumail_pwd_${accountId}`, stored)
      return password
    }
  } catch (err) {
    console.warn('Failed to retrieve from local storage:', err)
  }
  
  return null
}

/**
 * Remove password for an account
 */
export function removePassword(accountId: string): void {
  credentialCache.delete(accountId)
  
  try {
    sessionStorage.removeItem(`qumail_pwd_${accountId}`)
  } catch (err) {
    console.warn('Failed to remove from session storage:', err)
  }

  try {
    localStorage.removeItem(`qumail_pwd_${accountId}`)
  } catch (err) {
    console.warn('Failed to remove from local storage:', err)
  }
}

/**
 * Check if password exists for account
 */
export function hasPassword(accountId: string): boolean {
  return credentialCache.has(accountId) || 
    sessionStorage.getItem(`qumail_pwd_${accountId}`) !== null ||
    localStorage.getItem(`qumail_pwd_${accountId}`) !== null
}

/**
 * Clear all stored passwords
 */
export function clearAllPasswords(): void {
  credentialCache.clear()
  
  // Clear session storage items with our prefix
  try {
    const keysToRemove: string[] = []
    for (let i = 0; i < sessionStorage.length; i++) {
      const key = sessionStorage.key(i)
      if (key?.startsWith('qumail_pwd_')) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => sessionStorage.removeItem(key))
  } catch (err) {
    console.warn('Failed to clear session storage:', err)
  }

  // Clear local storage items with our prefix
  try {
    const keysToRemove: string[] = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key?.startsWith('qumail_pwd_')) {
        keysToRemove.push(key)
      }
    }
    keysToRemove.forEach(key => localStorage.removeItem(key))
  } catch (err) {
    console.warn('Failed to clear local storage:', err)
  }
}
