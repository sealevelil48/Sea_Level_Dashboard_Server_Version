# setup_project.py
"""
Quick setup script to create all necessary files for the Sea Level project
Run this from the project root directory
"""

import os
from pathlib import Path

def create_file(filepath, content):
    """Create a file with content, creating directories if needed"""
    file_path = Path(filepath)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created: {filepath}")

def main():
    """Create all project files"""
    print("🚀 Setting up Sea Level Monitoring Project...")
    print("=" * 50)
    
    # Backend .env file
    env_content = """DB_URI=postgresql://postgres:sealevel123@localhost:5432/Test2-SeaLevels
ENVIRONMENT=development
AWS_REGION=us-east-1
ELASTICACHE_ENDPOINT=localhost:6379
"""
    create_file("backend/.env", env_content)
    
    # Backend requirements.txt
    requirements_content = """fastapi==0.111.0
uvicorn[standard]==0.30.1
pandas==2.2.2
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
python-dotenv==1.0.1
redis==5.0.1
scikit-learn==1.4.2
statsmodels==0.14.2
prophet==1.1.5
pyproj==3.6.1
boto3==1.34.144
"""
    create_file("backend/requirements.txt", requirements_content)
    
    # Lambda get_stations
    get_stations_content = '''import json
import logging
import sys
import os

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

try:
    from shared.database import engine, L, db_manager
    from sqlalchemy import select
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database import error: {e}")
    DATABASE_AVAILABLE = False
    engine = L = db_manager = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_all_stations_from_db():
    """Get all stations from database"""
    if not DATABASE_AVAILABLE or not L:
        logger.error("Database not available")
        return ['All Stations', 'Demo Station 1', 'Demo Station 2']
    
    try:
        with engine.connect() as connection:
            query = select(L.c.Station).distinct().order_by(L.c.Station)
            result = connection.execute(query)
            stations = [row[0] for row in result if row[0] is not None]
            return ['All Stations'] + stations
    except Exception as e:
        logger.error(f"Error fetching stations: {e}")
        return ['All Stations', 'Error fetching stations']

def handler(event, context):
    """Lambda handler for get_stations"""
    try:
        stations = get_all_stations_from_db()
        logger.info(f"Found {len(stations)} stations")
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({"stations": stations})
        }
    except Exception as e:
        logger.error(f"Error in get_stations lambda: {e}")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Internal server error"})
        }
'''
    create_file("backend/lambdas/get_stations/main.py", get_stations_content)
    
    # Create other lambda files with basic demo functionality
    lambda_files = [
        ("get_data", "get_data"),
        ("get_live_data", "get_live_data"), 
        ("get_yesterday_data", "get_yesterday_data"),
        ("get_predictions", "get_predictions"),
        ("get_station_map", "get_station_map")
    ]
    
    for folder, name in lambda_files:
        basic_lambda_content = f'''import json
import logging
import sys
import os

# Add paths for shared modules
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, '..', '..')
sys.path.insert(0, backend_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """Lambda handler for {name}"""
    try:
        # Demo response - replace with actual implementation
        return {{
            "statusCode": 200,
            "headers": {{"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}},
            "body": json.dumps({{"message": "Demo response from {name}", "demo": True}})
        }}
    except Exception as e:
        logger.error(f"Error in {name} lambda: {{e}}")
        return {{
            "statusCode": 500,
            "headers": {{"Content-Type": "application/json"}},
            "body": json.dumps({{"error": "Internal server error"}})
        }}
'''
        create_file(f"backend/lambdas/{folder}/main.py", basic_lambda_content)
    
    # Frontend package.json
    package_json_content = """{
  "name": "sea-level-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-bootstrap": "^2.7.4",
    "bootstrap": "^5.2.3",
    "react-scripts": "5.0.1",
    "plotly.js": "^2.20.0",
    "react-plotly.js": "^2.6.0",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}"""
    create_file("frontend/package.json", package_json_content)
    
    # Frontend index.html
    index_html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta name="description" content="Sea Level Monitoring System" />
    <title>Sea Level Monitoring</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>"""
    create_file("frontend/public/index.html", index_html_content)
    
    # Frontend App.js
    app_js_content = """import React, { useState, useEffect } from 'react';
import { Container, Navbar, Alert, Button, Card, Row, Col } from 'react-bootstrap';
import 'bootstrap/dist/css/bootstrap.min.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [testResults, setTestResults] = useState({});

  const testEndpoint = async (endpoint, params = {}) => {
    setLoading(true);
    setError(null);
    try {
      const url = new URL(`${API_BASE_URL}${endpoint}`);
      Object.keys(params).forEach(key => {
        if (params[key] !== null && params[key] !== undefined) {
          url.searchParams.append(key, params[key]);
        }
      });
      
      const response = await fetch(url);
      const data = await response.json();
      
      setTestResults(prev => ({
        ...prev,
        [endpoint]: { success: true, data, status: response.status, timestamp: new Date().toLocaleTimeString() }
      }));
    } catch (error) {
      setTestResults(prev => ({
        ...prev,
        [endpoint]: { success: false, error: error.message, timestamp: new Date().toLocaleTimeString() }
      }));
    }
    setLoading(false);
  };

  useEffect(() => {
    // Test stations endpoint on load
    testEndpoint('/stations');
  }, []);

  const testButtons = [
    { name: 'Health Check', endpoint: '/health' },
    { name: 'Stations', endpoint: '/stations' },
    { name: 'Live Data', endpoint: '/live' },
    { name: 'Station Map', endpoint: '/stations/map' },
    { name: 'Data (Demo)', endpoint: '/data', params: { station: 'Demo Station 1', start_date: '2024-01-01', end_date: '2024-01-31' } },
    { name: 'Predictions (Demo)', endpoint: '/predictions', params: { station: 'Demo Station 1' } }
  ];

  return (
    <div className="App">
      <Navbar bg="dark" variant="dark" className="mb-4">
        <Container>
          <Navbar.Brand>🌊 Sea Level Monitoring - Test Interface</Navbar.Brand>
        </Container>
      </Navbar>

      <Container>
        <Row>
          <Col md={4}>
            <Card className="mb-4">
              <Card.Header>
                <Card.Title>API Test Controls</Card.Title>
              </Card.Header>
              <Card.Body>
                <div className="d-grid gap-2">
                  {testButtons.map((btn, index) => (
                    <Button 
                      key={index}
                      variant="primary" 
                      onClick={() => testEndpoint(btn.endpoint, btn.params)}
                      disabled={loading}
                      size="sm"
                    >
                      {btn.name}
                    </Button>
                  ))}
                </div>
                
                {loading && (
                  <Alert variant="info" className="mt-3">
                    <div className="d-flex align-items-center">
                      <div className="spinner-border spinner-border-sm me-2" role="status"></div>
                      Testing API endpoint...
                    </div>
                  </Alert>
                )}
              </Card.Body>
            </Card>
          </Col>
          
          <Col md={8}>
            <Card>
              <Card.Header>
                <Card.Title>Test Results</Card.Title>
              </Card.Header>
              <Card.Body style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {Object.keys(testResults).length === 0 ? (
                  <Alert variant="secondary">No tests run yet. Click a button to test an endpoint.</Alert>
                ) : (
                  Object.entries(testResults).reverse().map(([endpoint, result]) => (
                    <div key={endpoint} className="mb-3">
                      <h6 className="d-flex justify-content-between align-items-center">
                        <span>{endpoint}</span>
                        <small className="text-muted">{result.timestamp}</small>
                      </h6>
                      {result.success ? (
                        <Alert variant="success">
                          <strong>Status:</strong> {result.status}<br/>
                          <strong>Response:</strong>
                          <pre style={{ fontSize: '0.8em', maxHeight: '200px', overflow: 'auto' }}>
                            {JSON.stringify(result.data, null, 2)}
                          </pre>
                        </Alert>
                      ) : (
                        <Alert variant="danger">
                          <strong>Error:</strong> {result.error}
                        </Alert>
                      )}
                    </div>
                  ))
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;"""
    create_file("frontend/src/App.js", app_js_content)
    
    # Frontend index.js
    index_js_content = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);"""
    create_file("frontend/src/index.js", index_js_content)
    
    print("\n" + "=" * 50)
    print("✅ Project setup complete!")
    print("\n📝 Next Steps:")
    print("1. Install backend dependencies:")
    print("   cd backend")
    print("   pip install -r requirements.txt")
    print("\n2. Install frontend dependencies:")
    print("   cd frontend")
    print("   npm install")
    print("\n3. Start the application:")
    print("   cd backend")
    print("   python local_server.py --auto-frontend")
    print("\n🌐 URLs after startup:")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:3000")
    print("   API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()