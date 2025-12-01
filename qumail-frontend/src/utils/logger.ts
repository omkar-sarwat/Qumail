/**
 * Production-ready logger utility
 * Provides consistent logging with environment awareness
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogEntry {
  timestamp: string;
  level: LogLevel;
  message: string;
  data?: unknown;
  context?: string;
}

class Logger {
  private isDev = import.meta.env.DEV;
  private isDebugEnabled = import.meta.env.VITE_DEBUG === 'true';
  private logHistory: LogEntry[] = [];
  private maxHistorySize = 100;

  private formatTimestamp(): string {
    return new Date().toISOString();
  }

  private shouldLog(level: LogLevel): boolean {
    if (level === 'error' || level === 'warn') return true;
    if (level === 'info') return this.isDev || this.isDebugEnabled;
    if (level === 'debug') return this.isDev && this.isDebugEnabled;
    return false;
  }

  private addToHistory(entry: LogEntry): void {
    this.logHistory.push(entry);
    if (this.logHistory.length > this.maxHistorySize) {
      this.logHistory.shift();
    }
  }

  private formatMessage(level: LogLevel, context: string | undefined, message: string): string {
    const prefix = context ? `[${context}]` : '';
    const levelEmoji = {
      debug: '🔍',
      info: 'ℹ️',
      warn: '⚠️',
      error: '❌',
    }[level];
    return `${levelEmoji} ${prefix} ${message}`.trim();
  }

  debug(message: string, data?: unknown, context?: string): void {
    if (!this.shouldLog('debug')) return;

    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level: 'debug',
      message,
      data,
      context,
    };

    this.addToHistory(entry);
    console.debug(this.formatMessage('debug', context, message), data ?? '');
  }

  info(message: string, data?: unknown, context?: string): void {
    if (!this.shouldLog('info')) return;

    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level: 'info',
      message,
      data,
      context,
    };

    this.addToHistory(entry);
    console.info(this.formatMessage('info', context, message), data ?? '');
  }

  warn(message: string, data?: unknown, context?: string): void {
    if (!this.shouldLog('warn')) return;

    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level: 'warn',
      message,
      data,
      context,
    };

    this.addToHistory(entry);
    console.warn(this.formatMessage('warn', context, message), data ?? '');
  }

  error(message: string, error?: unknown, context?: string): void {
    const entry: LogEntry = {
      timestamp: this.formatTimestamp(),
      level: 'error',
      message,
      data: error instanceof Error ? { message: error.message, stack: error.stack } : error,
      context,
    };

    this.addToHistory(entry);
    console.error(this.formatMessage('error', context, message), error ?? '');

    // In production, could send to error tracking service
    if (import.meta.env.PROD && error instanceof Error) {
      // TODO: Send to error tracking service
    }
  }

  /**
   * Get recent log history (useful for debugging/support)
   */
  getHistory(): LogEntry[] {
    return [...this.logHistory];
  }

  /**
   * Clear log history
   */
  clearHistory(): void {
    this.logHistory = [];
  }

  /**
   * Create a scoped logger with a fixed context
   */
  scope(context: string): ScopedLogger {
    return new ScopedLogger(this, context);
  }
}

class ScopedLogger {
  constructor(private logger: Logger, private context: string) {}

  debug(message: string, data?: unknown): void {
    this.logger.debug(message, data, this.context);
  }

  info(message: string, data?: unknown): void {
    this.logger.info(message, data, this.context);
  }

  warn(message: string, data?: unknown): void {
    this.logger.warn(message, data, this.context);
  }

  error(message: string, error?: unknown): void {
    this.logger.error(message, error, this.context);
  }
}

// Export singleton instance
export const logger = new Logger();

// Export scoped loggers for common contexts
export const authLogger = logger.scope('Auth');
export const apiLogger = logger.scope('API');
export const emailLogger = logger.scope('Email');
export const encryptionLogger = logger.scope('Encryption');

export default logger;
