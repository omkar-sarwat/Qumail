/**
 * Performance monitoring utilities for production
 */

interface PerformanceMetric {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  metadata?: Record<string, unknown>;
}

class PerformanceMonitor {
  private metrics: Map<string, PerformanceMetric> = new Map();
  private completedMetrics: PerformanceMetric[] = [];
  private maxCompletedMetrics = 50;

  /**
   * Start timing an operation
   */
  start(name: string, metadata?: Record<string, unknown>): void {
    this.metrics.set(name, {
      name,
      startTime: performance.now(),
      metadata,
    });
  }

  /**
   * End timing an operation and return duration
   */
  end(name: string): number | null {
    const metric = this.metrics.get(name);
    if (!metric) {
      console.warn(`[Perf] No metric found for: ${name}`);
      return null;
    }

    const endTime = performance.now();
    const duration = endTime - metric.startTime;

    metric.endTime = endTime;
    metric.duration = duration;

    // Store completed metric
    this.completedMetrics.push(metric);
    if (this.completedMetrics.length > this.maxCompletedMetrics) {
      this.completedMetrics.shift();
    }

    // Remove from active metrics
    this.metrics.delete(name);

    // Log slow operations in development
    if (import.meta.env.DEV && duration > 100) {
      console.warn(`[Perf] Slow operation: ${name} took ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  /**
   * Measure a function execution time
   */
  async measure<T>(name: string, fn: () => Promise<T> | T): Promise<T> {
    this.start(name);
    try {
      const result = await fn();
      return result;
    } finally {
      this.end(name);
    }
  }

  /**
   * Get completed metrics summary
   */
  getSummary(): Record<string, { count: number; avgDuration: number; maxDuration: number }> {
    const summary: Record<string, { count: number; totalDuration: number; maxDuration: number }> = {};

    for (const metric of this.completedMetrics) {
      if (!metric.duration) continue;

      if (!summary[metric.name]) {
        summary[metric.name] = { count: 0, totalDuration: 0, maxDuration: 0 };
      }

      summary[metric.name].count++;
      summary[metric.name].totalDuration += metric.duration;
      summary[metric.name].maxDuration = Math.max(summary[metric.name].maxDuration, metric.duration);
    }

    const result: Record<string, { count: number; avgDuration: number; maxDuration: number }> = {};
    for (const [name, data] of Object.entries(summary)) {
      result[name] = {
        count: data.count,
        avgDuration: data.totalDuration / data.count,
        maxDuration: data.maxDuration,
      };
    }

    return result;
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics.clear();
    this.completedMetrics = [];
  }
}

// Web Vitals tracking
interface WebVitals {
  fcp?: number; // First Contentful Paint
  lcp?: number; // Largest Contentful Paint
  fid?: number; // First Input Delay
  cls?: number; // Cumulative Layout Shift
  ttfb?: number; // Time to First Byte
}

class VitalsTracker {
  private vitals: WebVitals = {};

  init(): void {
    if (typeof window === 'undefined') return;

    // Track First Contentful Paint
    this.observePaint('first-contentful-paint', (value) => {
      this.vitals.fcp = value;
    });

    // Track Largest Contentful Paint
    this.observeLCP((value) => {
      this.vitals.lcp = value;
    });

    // Track First Input Delay
    this.observeFID((value) => {
      this.vitals.fid = value;
    });

    // Track Cumulative Layout Shift
    this.observeCLS((value) => {
      this.vitals.cls = value;
    });

    // Track Time to First Byte
    this.trackTTFB();
  }

  private observePaint(name: string, callback: (value: number) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.name === name) {
            callback(entry.startTime);
            observer.disconnect();
          }
        }
      });
      observer.observe({ entryTypes: ['paint'] });
    } catch (e) {
      // Not supported
    }
  }

  private observeLCP(callback: (value: number) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        if (lastEntry) {
          callback(lastEntry.startTime);
        }
      });
      observer.observe({ entryTypes: ['largest-contentful-paint'] });
    } catch (e) {
      // Not supported
    }
  }

  private observeFID(callback: (value: number) => void): void {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          const fidEntry = entry as PerformanceEventTiming;
          if (fidEntry.processingStart) {
            callback(fidEntry.processingStart - entry.startTime);
            observer.disconnect();
          }
        }
      });
      observer.observe({ entryTypes: ['first-input'] });
    } catch (e) {
      // Not supported
    }
  }

  private observeCLS(callback: (value: number) => void): void {
    let clsValue = 0;
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
            callback(clsValue);
          }
        }
      });
      observer.observe({ entryTypes: ['layout-shift'] });
    } catch (e) {
      // Not supported
    }
  }

  private trackTTFB(): void {
    try {
      const navEntry = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (navEntry) {
        this.vitals.ttfb = navEntry.responseStart - navEntry.requestStart;
      }
    } catch (e) {
      // Not supported
    }
  }

  getVitals(): WebVitals {
    return { ...this.vitals };
  }
}

// Export singleton instances
export const perfMonitor = new PerformanceMonitor();
export const vitalsTracker = new VitalsTracker();

// Initialize vitals tracking
if (typeof window !== 'undefined') {
  vitalsTracker.init();
}

export default perfMonitor;
