// Quick Performance Check - Run in browser console
console.log('=== PERFORMANCE VERIFICATION ===');

// Memory check
if (performance.memory) {
  const memoryMB = (performance.memory.usedJSHeapSize / 1048576).toFixed(2);
  const status = memoryMB < 100 ? '✅' : memoryMB < 150 ? '⚠️' : '❌';
  console.log(`Memory: ${memoryMB} MB ${status}`);
}

// API calls check
const apiCalls = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/api/')).length;
const apiStatus = apiCalls < 8 ? '✅' : apiCalls < 12 ? '⚠️' : '❌';
console.log(`API Calls: ${apiCalls} ${apiStatus}`);

// Forecast calls check
const forecastCalls = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('forecast')).length;
const forecastStatus = forecastCalls < 2 ? '✅' : '❌';
console.log(`Forecast Calls: ${forecastCalls} ${forecastStatus}`);

// GovMap calls check
const govmapCalls = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('govmap')).length;
const govmapStatus = govmapCalls === 0 ? '✅' : '❌';
console.log(`GovMap Calls: ${govmapCalls} ${govmapStatus}`);

// Load time check
const navigation = performance.getEntriesByType('navigation')[0];
if (navigation) {
  const loadTime = (navigation.loadEventEnd - navigation.fetchStart) / 1000;
  const loadStatus = loadTime < 3 ? '✅' : loadTime < 8 ? '⚠️' : '❌';
  console.log(`Load Time: ${loadTime.toFixed(2)}s ${loadStatus}`);
}

// Check for infinite loop indicators
const recentApiCalls = performance.getEntriesByType('resource')
  .filter(r => r.name.includes('/api/') && (Date.now() - r.startTime) < 10000);
if (recentApiCalls.length > 5) {
  console.log('⚠️ Possible infinite loop detected - too many recent API calls');
}

console.log('=== END VERIFICATION ===');