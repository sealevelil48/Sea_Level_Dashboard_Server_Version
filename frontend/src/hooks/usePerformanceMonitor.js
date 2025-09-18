import { useEffect } from 'react';

/**
 * Performance monitoring hook
 */
export const usePerformanceMonitor = (componentName = 'Component') => {
  useEffect(() => {
    if (process.env.NODE_ENV !== 'production') {
      // Monitor render times
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (entry.entryType === 'measure') {
            console.log(`${componentName} - ${entry.name}: ${entry.duration.toFixed(2)}ms`);
          }
        });
      });

      observer.observe({ entryTypes: ['measure'] });

      // Mark component mount
      performance.mark(`${componentName}-mount-start`);

      return () => {
        // Mark component unmount
        performance.mark(`${componentName}-mount-end`);
        performance.measure(
          `${componentName}-mount-duration`,
          `${componentName}-mount-start`,
          `${componentName}-mount-end`
        );
        
        observer.disconnect();
      };
    }
  }, [componentName]);

  // Function to measure specific operations
  const measureOperation = (operationName, operation) => {
    if (process.env.NODE_ENV !== 'production') {
      const startMark = `${componentName}-${operationName}-start`;
      const endMark = `${componentName}-${operationName}-end`;
      const measureName = `${componentName}-${operationName}-duration`;

      performance.mark(startMark);
      
      const result = operation();
      
      if (result && typeof result.then === 'function') {
        // Handle async operations
        return result.finally(() => {
          performance.mark(endMark);
          performance.measure(measureName, startMark, endMark);
        });
      } else {
        // Handle sync operations
        performance.mark(endMark);
        performance.measure(measureName, startMark, endMark);
        return result;
      }
    } else {
      return operation();
    }
  };

  return { measureOperation };
};