/**
 * Parallel Data Loader with Error Recovery
 * ==========================================
 * Replaces sequential API loading with parallel requests
 * Includes: Request deduplication, error recovery, partial results
 * 
 * Expected Impact: 50-75% faster initial load (10-16s → 2-4s)
 */

class ParallelDataLoader {
  constructor() {
    this.pendingRequests = new Map();
    this.abortControllers = new Map();
  }

  /**
   * Load all initial dashboard data in parallel
   * @param {Object} options - Loading options
   * @returns {Promise<Object>} Combined results with error handling
   */
  async loadInitialData(options = {}) {
    const {
      selectedStations = ['All Stations'],
      startDate = null,
      endDate = null,
      enableForecast = true,
      enablePredictions = false,
      enableStatistics = true
    } = options;

    console.log('[ParallelDataLoader] Starting parallel load...');
    const startTime = performance.now();

    // Define all data fetching tasks
    const tasks = {
      stations: this.fetchWithRecovery('stations', () => 
        this.apiService.getStations()
      ),
      
      recentData: this.fetchWithRecovery('recentData', () => 
        this.apiService.getLatestData({
          station: selectedStations[0] || 'All Stations',
          limit: 100
        })
      )
    };

    // Add optional tasks
    if (enableStatistics && startDate && endDate) {
      tasks.statistics = this.fetchWithRecovery('statistics', () =>
        this.apiService.getStatistics({
          startDate,
          endDate,
          station: selectedStations[0] || 'All Stations'
        })
      );
    }

    if (enableForecast) {
      tasks.seaForecast = this.fetchWithRecovery('seaForecast', () =>
        this.apiService.getSeaForecast()
      );
    }

    if (enablePredictions && selectedStations.length > 0 && 
        !selectedStations.includes('All Stations')) {
      tasks.predictions = this.fetchWithRecovery('predictions', () =>
        this.apiService.getPredictions({
          stations: selectedStations.slice(0, 3),
          hours: 24
        })
      );
    }

    // Execute all tasks in parallel with timeout
    const results = await this.executeWithTimeout(tasks, 30000); // 30s timeout

    const duration = performance.now() - startTime;
    console.log(`[ParallelDataLoader] Completed in ${duration.toFixed(0)}ms`);

    // Log individual task performance
    this.logPerformanceMetrics(results);

    return {
      data: this.extractSuccessfulData(results),
      errors: this.extractErrors(results),
      metadata: {
        totalDuration: duration,
        successCount: this.countSuccessful(results),
        errorCount: this.countErrors(results)
      }
    };
  }

  /**
   * Fetch data with automatic retry and error recovery
   */
  async fetchWithRecovery(taskName, fetchFn, maxRetries = 2) {
    const startTime = performance.now();
    
    // Check for pending duplicate request
    if (this.pendingRequests.has(taskName)) {
      console.log(`[ParallelDataLoader] Deduplicating request: ${taskName}`);
      return this.pendingRequests.get(taskName);
    }

    // Create AbortController for cancellation
    const abortController = new AbortController();
    this.abortControllers.set(taskName, abortController);

    const executeWithRetry = async (retriesLeft) => {
      try {
        const result = await fetchFn({ signal: abortController.signal });
        const duration = performance.now() - startTime;
        
        return {
          status: 'success',
          taskName,
          data: result,
          duration,
          retries: maxRetries - retriesLeft
        };
      } catch (error) {
        // Check if request was aborted
        if (error.name === 'AbortError') {
          return {
            status: 'aborted',
            taskName,
            error: 'Request cancelled',
            duration: performance.now() - startTime
          };
        }

        // Retry on network errors
        if (retriesLeft > 0 && this.isRetryableError(error)) {
          console.warn(`[${taskName}] Retry ${maxRetries - retriesLeft + 1}/${maxRetries}:`, error.message);
          await this.delay(1000 * (maxRetries - retriesLeft + 1)); // Exponential backoff
          return executeWithRetry(retriesLeft - 1);
        }

        // Return error result
        const duration = performance.now() - startTime;
        console.error(`[${taskName}] Failed after ${maxRetries - retriesLeft} retries:`, error);
        
        return {
          status: 'error',
          taskName,
          error: error.message || 'Unknown error',
          duration,
          retries: maxRetries - retriesLeft
        };
      }
    };

    // Create and store promise
    const promise = executeWithRetry(maxRetries).finally(() => {
      this.pendingRequests.delete(taskName);
      this.abortControllers.delete(taskName);
    });

    this.pendingRequests.set(taskName, promise);
    return promise;
  }

  /**
   * Execute tasks with global timeout
   */
  async executeWithTimeout(tasks, timeoutMs) {
    const taskEntries = Object.entries(tasks);
    
    // Create timeout promise
    const timeoutPromise = new Promise((_, reject) => {
      setTimeout(() => reject(new Error('Global timeout exceeded')), timeoutMs);
    });

    try {
      // Race between all tasks completing and timeout
      const results = await Promise.race([
        Promise.allSettled(taskEntries.map(([key, promise]) => 
          promise.then(result => ({ key, ...result }))
        )),
        timeoutPromise
      ]);

      // Convert array to object
      return results.reduce((acc, result) => {
        if (result.status === 'fulfilled') {
          acc[result.value.key] = result.value;
        } else {
          acc[result.reason?.key || 'unknown'] = {
            status: 'error',
            taskName: result.reason?.key || 'unknown',
            error: result.reason?.message || 'Promise rejected',
            duration: 0
          };
        }
        return acc;
      }, {});

    } catch (error) {
      // Global timeout - cancel all pending requests
      console.error('[ParallelDataLoader] Global timeout - cancelling all requests');
      this.cancelAll();
      throw error;
    }
  }

  /**
   * Cancel all pending requests
   */
  cancelAll() {
    console.log(`[ParallelDataLoader] Cancelling ${this.abortControllers.size} pending requests`);
    
    for (const [taskName, controller] of this.abortControllers.entries()) {
      controller.abort();
      console.log(`[ParallelDataLoader] Cancelled: ${taskName}`);
    }
    
    this.abortControllers.clear();
    this.pendingRequests.clear();
  }

  /**
   * Extract successful data from results
   */
  extractSuccessfulData(results) {
    const data = {};
    
    for (const [key, result] of Object.entries(results)) {
      if (result.status === 'success') {
        data[key] = result.data;
      }
    }
    
    return data;
  }

  /**
   * Extract errors from results
   */
  extractErrors(results) {
    const errors = {};
    
    for (const [key, result] of Object.entries(results)) {
      if (result.status === 'error' || result.status === 'aborted') {
        errors[key] = result.error;
      }
    }
    
    return errors;
  }

  /**
   * Count successful tasks
   */
  countSuccessful(results) {
    return Object.values(results).filter(r => r.status === 'success').length;
  }

  /**
   * Count failed tasks
   */
  countErrors(results) {
    return Object.values(results).filter(r => 
      r.status === 'error' || r.status === 'aborted'
    ).length;
  }

  /**
   * Log performance metrics for each task
   */
  logPerformanceMetrics(results) {
    console.group('[ParallelDataLoader] Performance Metrics');
    
    for (const [key, result] of Object.entries(results)) {
      const status = result.status === 'success' ? '✓' : '✗';
      const duration = result.duration?.toFixed(0) || 'N/A';
      const retries = result.retries > 0 ? ` (${result.retries} retries)` : '';
      
      console.log(`${status} ${key}: ${duration}ms${retries}`);
    }
    
    console.groupEnd();
  }

  /**
   * Check if error is retryable
   */
  isRetryableError(error) {
    // Retry on network errors, timeouts, and 5xx server errors
    const retryableCodes = [408, 429, 500, 502, 503, 504];
    
    return (
      error.name === 'NetworkError' ||
      error.name === 'TimeoutError' ||
      error.message?.includes('timeout') ||
      error.message?.includes('network') ||
      (error.status && retryableCodes.includes(error.status))
    );
  }

  /**
   * Delay helper for retry backoff
   */
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Set API service instance
   */
  setApiService(apiService) {
    this.apiService = apiService;
  }
}

// Create singleton instance
const parallelDataLoader = new ParallelDataLoader();

export default parallelDataLoader;


/**
 * Usage Example:
 * 
 * import parallelDataLoader from './optimizations/ParallelDataLoader';
 * import apiService from './services/apiService';
 * 
 * // Initialize
 * parallelDataLoader.setApiService(apiService);
 * 
 * // Load data
 * const { data, errors, metadata } = await parallelDataLoader.loadInitialData({
 *   selectedStations: ['Haifa'],
 *   enableForecast: true,
 *   enablePredictions: false
 * });
 * 
 * // Handle partial success
 * if (data.stations) {
 *   setStations(data.stations);
 * }
 * 
 * if (errors.seaForecast) {
 *   console.warn('Forecast unavailable:', errors.seaForecast);
 * }
 * 
 * // Cancel on unmount
 * useEffect(() => {
 *   return () => parallelDataLoader.cancelAll();
 * }, []);
 */