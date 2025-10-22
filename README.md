# Sea Level Monitoring System

A comprehensive real-time sea level monitoring and analysis system with predictive capabilities, anomaly detection, and interactive data visualization for Israeli coastal stations.

## 🎯 Overview

The Sea Level Monitoring System provides real-time monitoring and analysis of sea level data from multiple stations across Israel's coastline. Built with modern web technologies, it offers interactive visualizations, wave forecasting, and comprehensive data analysis capabilities.

### Key Stations Monitored
- **Haifa** - Northern Israel's main port
- **Acre** - Historic coastal city  
- **Ashdod** - Central Mediterranean port
- **Ashkelon** - Southern coastal city
- **Yafo (Jaffa)** - Tel Aviv metropolitan area
- **Eilat** - Red Sea monitoring station

## ✨ Features

### 📊 Data Visualization
- **Interactive Charts** - Real-time sea level and temperature graphs
- **Geographic Mapping** - Station locations with live status indicators (OpenStreetMap & GovMap)
- **Data Tables** - Sortable, filterable tabular data views
- **Wave Forecasting** - IMS weather forecast integration

### 🔮 Predictive Analytics
- **ARIMA Forecasting** - Short-term sea level predictions
- **Statistical Analysis** - Trend analysis and pattern recognition
- **Confidence Intervals** - Prediction uncertainty visualization

### 🔄 Real-time Monitoring
- **Live Data Streams** - Regular data updates
- **System Health** - Station status and connectivity monitoring
- **Performance Metrics** - API response times and data quality

## 🏗️ Architecture

### Technology Stack

**Frontend:**
- React 18 - Modern component-based UI
- Bootstrap 5 - Responsive CSS framework
- Plotly.js - Interactive data visualization
- React-Leaflet - Interactive maps
- Axios - HTTP client

**Backend:**
- FastAPI - High-performance Python web framework
- SQLAlchemy - Database ORM
- PostgreSQL - Primary data storage
- Redis - Caching (optional)
- Pandas - Data processing

## 🚀 Quick Start

### Prerequisites
- Python 3.8+ and pip
- Node.js 16+ and npm
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/sealevelil48/Sea_Level_Dashboard_Server_Version.git
cd Sea_Level_Dashboard_Server_Version
```

2. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your database credentials
python local_server.py
```

3. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

4. **Access the Application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:30886
- API Documentation: http://localhost:30886/docs

## 💻 Usage

### Basic Operations

1. **Viewing Real-time Data**
   - Navigate to the main dashboard
   - Select station from dropdown or view "All Stations"
   - Data updates automatically

2. **Historical Analysis**
   - Use date range picker to select time period
   - Choose from preset ranges (24h, 7d, 30d)
   - View trends in interactive graphs

3. **Wave Forecasting**
   - Navigate to "Waves Forecast" tab
   - View IMS weather forecasts for coastal regions
   - See combined data in map markers

4. **Map Views**
   - Switch between OpenStreetMap and GovMap
   - Click markers for detailed station information
   - View forecast data overlays

## 🔌 API Documentation

### Core Endpoints

- `GET /stations` - Get all monitoring stations
- `GET /data` - Get time series data with filters
- `GET /live` - Get latest readings
- `GET /sea-forecast` - Get IMS wave forecast data
- `GET /health` - System health check

### Example Usage
```bash
# Get stations
curl http://localhost:30886/api/stations

# Get data for specific station
curl "http://localhost:30886/api/data?station=Haifa&start_date=2024-01-01&end_date=2024-01-31"

# Get wave forecast
curl http://localhost:30886/api/sea-forecast
```

## 🛠️ Development

### Project Structure
```
Sea_Level_Dashboard_Server_Version/
├── README.md
├── requirements.txt
├── .gitignore
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   ├── public/
│   └── package.json
├── backend/
│   ├── lambdas/
│   ├── shared/
│   ├── tests/
│   └── requirements.txt
└── deployment/
```

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### Code Style
- Python: Follow PEP 8, use type hints
- JavaScript: Use ESLint, prefer functional components
- Commit messages: Use conventional commits format

## 🚀 Deployment

### Docker Deployment (Recommended)
```bash
# Build and start services
docker-compose up -d

# Check status
docker-compose ps
```

### Manual Deployment
```bash
# Backend
cd backend
gunicorn -w 4 -k uvicorn.workers.UvicornWorker local_server:app

# Frontend
cd frontend
npm run build
# Serve build/ directory with nginx
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Make changes and add tests
4. Commit changes: `git commit -m 'feat: add amazing feature'`
5. Push to branch: `git push origin feature/amazing-feature`
6. Open Pull Request

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql
# Test connection
psql -h localhost -U username -d database_name
```

**Frontend Not Loading**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API CORS Errors**
- Verify API URL in frontend .env
- Check CORS settings in backend configuration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Israeli Meteorological Service - Weather forecast data
- OpenStreetMap - Map tiles and geographic data
- Survey of Israel - Geographic and mapping services
- All contributors who have helped improve this project

---

For more detailed information, check the API documentation at `/docs` when running the backend server.