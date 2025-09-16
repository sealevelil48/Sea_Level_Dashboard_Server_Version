# Sea Level Dashboard - Application Structure

## 🏗️ Overall Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEA LEVEL DASHBOARD                         │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React)     │  Backend (Python)     │  AWS Services   │
│  ┌─────────────────┐  │  ┌─────────────────┐  │  ┌─────────────┐ │
│  │   React App     │◄─┤  │  Local Server   │◄─┤  │   Lambda    │ │
│  │   Components    │  │  │  API Gateway    │  │  │  Functions  │ │
│  │   Services      │  │  │  Data Processing│  │  │   RDS/DB    │ │
│  └─────────────────┘  │  └─────────────────┘  │  └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
Sea_Level_Dashboard/
├── 🎨 frontend/                    # React Application
│   ├── public/
│   │   ├── assets/
│   │   │   ├── Mapi_Logo2.png     # Logo
│   │   │   └── style.css          # Global styles
│   │   └── index.html             # Main HTML template
│   ├── src/
│   │   ├── components/            # React Components
│   │   │   ├── ErrorBoundary.js   # Error handling
│   │   │   ├── Filters.js         # Filter controls
│   │   │   ├── GraphView.js       # Chart visualization
│   │   │   ├── MapView.js         # Map container
│   │   │   ├── OSMMap.js          # OpenStreetMap
│   │   │   ├── GovMapView.js      # Government map
│   │   │   ├── StatsCards.js      # Statistics display
│   │   │   ├── TableView.js       # Data tables
│   │   │   └── LeafletFallback.js # Map fallback
│   │   ├── hooks/
│   │   │   └── useFavorites.js    # Favorites management
│   │   ├── services/
│   │   │   └── apiService.js      # API communication
│   │   ├── utils/
│   │   │   └── dataOptimizer.js   # Data optimization
│   │   ├── App.js                 # Main application
│   │   ├── App.css                # App styles
│   │   └── index.js               # Entry point
│   └── package.json               # Dependencies
│
├── 🔧 backend/                     # Python Backend
│   ├── lambdas/                   # AWS Lambda Functions
│   │   ├── get_data/              # Historical data retrieval
│   │   ├── get_live_data/         # Real-time data
│   │   ├── get_predictions/       # ML predictions
│   │   ├── get_stations/          # Station information
│   │   ├── get_station_map/       # Map data
│   │   └── get_yesterday_data/    # Recent data
│   ├── shared/                    # Shared modules
│   │   ├── data_processing.py     # Data processing logic
│   │   ├── database.py            # Database operations
│   │   ├── kalman_filter.py       # Kalman filtering
│   │   ├── regime_switching.py    # Statistical models
│   │   └── utils.py               # Utility functions
│   ├── tests/                     # Test suite
│   ├── local_server.py            # Development server
│   ├── local_server-prod.py       # Production server
│   └── mapframe.html              # Map iframe
│
├── 🚀 deployment/                  # Deployment files
│   ├── *.zip                      # Lambda deployment packages
│   └── Deployment Guide.docx      # Setup instructions
│
└── 📋 Root files
    ├── start_backend.bat          # Backend startup
    ├── start_frontend.bat         # Frontend startup
    ├── start_dev.py               # Development launcher
    └── setup_project.py           # Project setup
```

## 🔄 Data Flow Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  React Frontend │───▶│  API Service    │
│  (Filters/UI)   │    │   Components    │    │   (apiService)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Display   │◄───│  State Manager  │◄───│  Backend API    │
│ (Charts/Tables) │    │   (useState)    │    │ (Local/Lambda)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────┐
                                              │    Database     │
                                              │  (Sea Level     │
                                              │     Data)       │
                                              └─────────────────┘
```

## 🧩 Component Hierarchy

```
App.js (Main Container)
├── Header (Logo + Time)
├── Container (Bootstrap)
│   ├── Filters Column (Col-3)
│   │   ├── Date Range
│   │   ├── Station Selection
│   │   ├── Data Type
│   │   ├── Trendline Options
│   │   ├── Analysis Type
│   │   ├── Prediction Models
│   │   └── Export Buttons
│   │
│   └── Content Column (Col-9)
│       ├── Stats Cards Row
│       │   ├── Current Level
│       │   ├── 24h Change
│       │   ├── Avg Temperature
│       │   └── Anomalies Count
│       │
│       └── Tabs Container
│           ├── Graph View Tab
│           │   └── Plot (Plotly.js)
│           ├── Table View Tab
│           │   ├── Historical Tab
│           │   └── Forecast Tab
│           └── Map View Tab
│               ├── OpenStreetMap Tab
│               └── GovMap Tab
```

## 🔌 API Endpoints

```
Backend API Structure:
├── /stations              # Get available stations
├── /data                  # Get historical data
├── /live_data            # Get real-time data
├── /predictions          # Get ML predictions
├── /station_map          # Get map data
├── /yesterday_data       # Get recent data
└── /mapframe             # Map iframe endpoint
```

## 🤖 Machine Learning Models

```
Prediction System:
├── Kalman Filter
│   ├── State estimation
│   ├── Nowcast generation
│   ├── Forecast with uncertainty
│   └── Confidence intervals
├── ARIMA Model
│   ├── Time series analysis
│   ├── Trend detection
│   └── Statistical forecasting
└── Ensemble Model
    ├── Multiple model combination
    ├── Weighted predictions
    └── Robust forecasting
```

## 📊 Data Processing Pipeline

```
Raw Data → Data Processing → Analysis → Visualization
    │            │              │           │
    ▼            ▼              ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────┐
│Database │ │Filtering│ │Trendlines   │ │Charts   │
│Records  │ │Cleaning │ │Anomalies    │ │Tables   │
│         │ │         │ │Predictions  │ │Maps     │
└─────────┘ └─────────┘ └─────────────┘ └─────────┘
```

## 🎯 Key Features

### Frontend Features:
- **Multi-station selection** (up to 3 stations)
- **Real-time data visualization** with Plotly.js
- **Interactive maps** (OSM + GovMap)
- **Statistical analysis** (trendlines, rolling averages)
- **ML predictions** (Kalman, ARIMA, Ensemble)
- **Data export** (PNG, Excel)
- **Responsive design** with Bootstrap

### Backend Features:
- **RESTful API** with Flask/FastAPI
- **AWS Lambda integration**
- **Database connectivity**
- **Machine learning models**
- **Data processing pipelines**
- **Real-time data fetching**

### Deployment:
- **Local development** servers
- **AWS Lambda** functions
- **Containerized** deployment
- **Environment** configurations