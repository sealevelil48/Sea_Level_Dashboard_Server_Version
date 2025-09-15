export const optimizeDataPoints = (data, maxPoints = 1000) => {
  if (data.length <= maxPoints) return data;
  
  // Downsample data for performance
  const step = Math.ceil(data.length / maxPoints);
  return data.filter((_, index) => index % step === 0);
};

export const memoizedCalculations = (() => {
  const cache = new Map();
  
  return (key, calculationFn) => {
    if (cache.has(key)) {
      return cache.get(key);
    }
    const result = calculationFn();
    cache.set(key, result);
    return result;
  };
})();