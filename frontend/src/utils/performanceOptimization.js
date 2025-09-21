/**
 * Performance optimization utilities and configurations
 */

// Data virtualization for large datasets
export const dataOptimizer = {
  // Downsample data for visualization when exceeding threshold
  downsampleData: (data, maxPoints = 1000) => {
    if (!Array.isArray(data) || data.length <= maxPoints) {
      return data;
    }
    
    const ratio = Math.ceil(data.length / maxPoints);
    return data.filter((_, index) => index % ratio === 0);
  },
  
  // Chunk data for progressive loading
  chunkData: (data, chunkSize = 500) => {
    const chunks = [];
    for (let i = 0; i < data.length; i += chunkSize) {
      chunks.push(data.slice(i, i + chunkSize));
    }
    return chunks;
  },
  
  // Optimize time series data for Plotly
  optimizeForPlotly: (data, threshold = 5000) => {
    if (data.length <= threshold) return data;
    
    // Use scattergl for better performance with large datasets
    return {
      data: dataOptimizer.downsampleData(data, threshold),
      layout: {
        datarevision: Math.random(), // Force update
        uirevision: 'constant' // Preserve zoom/pan state
      },
      config: {
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        toImageButtonOptions: {
          format: 'png',
          filename: 'sea_level_data'
        }
      }
    };
  }
};

// Debounce utility for input handlers
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Throttle utility for scroll/resize handlers
export const throttle = (func, limit) => {
  let inThrottle;
  return function(...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => inThrottle = false, limit);
    }
  };
};

// Memoization for expensive calculations
export const memoize = (fn) => {
  const cache = new Map();
  return (...args) => {
    const key = JSON.stringify(args);
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = fn.apply(this, args);
    cache.set(key, result);
    // Limit cache size
    if (cache.size > 100) {
      const firstKey = cache.keys().next().value;
      cache.delete(firstKey);
    }
    return result;
  };
};