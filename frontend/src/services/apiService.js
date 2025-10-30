/**
 * API Service with proper error handling and request management
 */

class ApiError extends Error {
  constructor(status, statusText, data = null) {
    super(`HTTP ${status}: ${statusText}`);
    this.status = status;
    this.statusText = statusText;
    this.data = data;
    this.name = 'ApiError';
  }
}

class ApiService {
  constructor(baseURL = process.env.REACT_APP_API_URL || process.env.REACT_APP_BACKEND_URL || 'http://localhost:30886') {
    this.baseURL = baseURL;
    this.timeout = 60000; // Increased to 60 seconds
    this.activeRequests = new Map();
    this.cache = new Map();
    this.cacheTimeout = 5 * 60 * 1000; // 5 minutes
    this.retryAttempts = 2; // Reduced retries to avoid long delays
    this.retryDelay = 2000; // Increased delay between retries
  }

  // Cache management
  getCacheKey(endpoint, params = {}) {
    return `${endpoint}_${JSON.stringify(params)}`;
  }

  getFromCache(key) {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < this.cacheTimeout) {
      return cached.data;
    }
    this.cache.delete(key);
    return null;
  }

  setCache(key, data) {
    this.cache.set(key, {
      data,
      timestamp: Date.now()
    });
    // Cleanup old cache entries
    if (this.cache.size > 100) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }
  }

  async request(endpoint, options = {}) {
    const requestId = `${options.method || 'GET'}_${endpoint}`;
    
    // Check cache for GET requests
    if (!options.method || options.method === 'GET') {
      const cacheKey = this.getCacheKey(endpoint, options.params);
      const cachedData = this.getFromCache(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }
    
    // Cancel previous request if exists (but allow multiple concurrent requests)
    // if (this.activeRequests.has(requestId)) {
    //   this.activeRequests.get(requestId).abort();
    // }

    const controller = new AbortController();
    this.activeRequests.set(requestId, controller);
    
    let lastError;
    for (let attempt = 0; attempt < this.retryAttempts; attempt++) {
      try {
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        const response = await fetch(`${this.baseURL}${endpoint}`, {
          ...options,
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        });

        clearTimeout(timeoutId);
        
        if (!response.ok) {
          let errorData = null;
          try {
            errorData = await response.json();
          } catch {
            // Ignore JSON parsing errors for error responses
          }
          throw new ApiError(response.status, response.statusText, errorData);
        }

        const data = await response.json();
        
        // Cache successful GET requests
        if (!options.method || options.method === 'GET') {
          const cacheKey = this.getCacheKey(endpoint, options.params);
          this.setCache(cacheKey, data);
        }
        
        this.activeRequests.delete(requestId);
        return data;
        
      } catch (error) {
        lastError = error;
        
        if (error.name === 'AbortError') {
          this.activeRequests.delete(requestId);
          throw new Error('Request cancelled');
        }
        
        // Don't retry on client errors (4xx)
        if (error instanceof ApiError && error.status >= 400 && error.status < 500) {
          this.activeRequests.delete(requestId);
          throw error;
        }
        
        // Wait before retry
        if (attempt < this.retryAttempts - 1) {
          await new Promise(resolve => setTimeout(resolve, this.retryDelay * (attempt + 1)));
        }
      }
    }
    
    this.activeRequests.delete(requestId);
    throw lastError;
  }

  async getStations() {
    try {
      const data = await this.request('/api/stations');
      return {
        stations: Array.isArray(data.stations) ? data.stations : [],
        database_available: data.database_available || false
      };
    } catch (error) {
      console.error('Error fetching stations:', error);
      return { stations: [], database_available: false };
    }
  }

  async getData(params) {
    try {
      const queryParams = new URLSearchParams();
      
      // Validate and add parameters
      if (params.station) queryParams.append('station', params.station);
      if (params.start_date) queryParams.append('start_date', params.start_date);
      if (params.end_date) queryParams.append('end_date', params.end_date);
      if (params.data_source) queryParams.append('data_source', params.data_source);
      if (params.show_anomalies) queryParams.append('show_anomalies', params.show_anomalies);
      if (params.limit) queryParams.append('limit', params.limit);

      const data = await this.request(`/api/data?${queryParams}`);
      return Array.isArray(data) ? data : [];
    } catch (error) {
      console.error('Error fetching data:', error);
      return [];
    }
  }

  async getPredictions(params) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.stations) queryParams.append('stations', params.stations);
      if (params.model) queryParams.append('model', params.model);
      if (params.steps) queryParams.append('steps', params.steps);

      return await this.request(`/api/predictions?${queryParams}`);
    } catch (error) {
      console.error('Error fetching predictions:', error);
      return {};
    }
  }

  async getSeaForecast() {
    try {
      return await this.request('/api/sea-forecast');
    } catch (error) {
      console.error('Error fetching sea forecast:', error);
      return null;
    }
  }

  async getHealth() {
    try {
      return await this.request('/api/health');
    } catch (error) {
      console.error('Error checking health:', error);
      return { status: 'error', message: error.message };
    }
  }

  // Cancel all active requests
  cancelAllRequests() {
    this.activeRequests.forEach(controller => controller.abort());
    this.activeRequests.clear();
  }

  // Clear cache
  clearCache() {
    this.cache.clear();
  }
}

const apiService = new ApiService();
export default apiService;