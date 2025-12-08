/**
 * Secure credential storage for email accounts
 * 
 * Uses:
 * - Browser: Session storage (cleared when browser closes)
 * - In-memory cache for quick access
 * 
 * Passwords are NOT persisted to localStorage for security
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
}

/**
 * Check if password exists for account
 */
export function hasPassword(accountId: string): boolean {
  return credentialCache.has(accountId) || 
    sessionStorage.getItem(`qumail_pwd_${accountId}`) !== null
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
}
