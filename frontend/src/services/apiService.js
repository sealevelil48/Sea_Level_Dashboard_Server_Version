class ApiService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl || process.env.REACT_APP_API_URL;
  }

  async fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
      try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
      } catch (error) {
        if (i === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
      }
    }
  }

  async getStations() {
    return this.fetchWithRetry(`${this.baseUrl}/stations`);
  }

  async getData(params) {
    const queryString = new URLSearchParams(params).toString();
    return this.fetchWithRetry(`${this.baseUrl}/data?${queryString}`);
  }
}

export default new ApiService();