// Simple API test script
const API_URL = 'http://5.102.231.16:30886';

async function testAPI() {
  console.log('Testing API connectivity...');
  
  try {
    // Test stations endpoint
    console.log('1. Testing /api/stations...');
    const stationsResponse = await fetch(`${API_URL}/api/stations`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(10000) // 10 second timeout
    });
    
    if (!stationsResponse.ok) {
      throw new Error(`HTTP ${stationsResponse.status}: ${stationsResponse.statusText}`);
    }
    
    const stationsData = await stationsResponse.json();
    console.log('✅ Stations:', stationsData);
    
    // Test Ashkelon data specifically
    console.log('2. Testing Ashkelon data...');
    const ashkelonResponse = await fetch(`${API_URL}/api/data?station=Ashkelon&start_date=2025-10-29&end_date=2025-10-30`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      signal: AbortSignal.timeout(15000) // 15 second timeout
    });
    
    if (!ashkelonResponse.ok) {
      throw new Error(`HTTP ${ashkelonResponse.status}: ${ashkelonResponse.statusText}`);
    }
    
    const ashkelonData = await ashkelonResponse.json();
    console.log(`✅ Ashkelon data points: ${ashkelonData.length}`);
    
    if (ashkelonData.length > 0) {
      console.log('Sample Ashkelon data:', ashkelonData[0]);
    }
    
    console.log('🎉 All tests passed! API is working correctly.');
    
  } catch (error) {
    console.error('❌ API test failed:', error.message);
    
    if (error.name === 'AbortError') {
      console.error('Request timed out - this might be the issue your frontend is experiencing');
    }
  }
}

testAPI();