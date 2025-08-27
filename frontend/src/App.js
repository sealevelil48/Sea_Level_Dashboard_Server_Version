// frontend/src/App.js - Fixed version with all bug fixes
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Container, Row, Col, Card, Form, Tabs, Tab } from 'react-bootstrap';
import Plot from 'react-plotly.js';
import OSMMap from './components/OSMMap';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('graph');
  const [mapTab, setMapTab] = useState('osm');
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [predictions, setPredictions] = useState({ arima: null, prophet: null });
  const [selectedStations, setSelectedStations] = useState(['All Stations']);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const plotRef = useRef(null);
  
  // Initialize stats
  const [stats, setStats] = useState({
    current_level: 0,
    '24h_change': 0,
    avg_temp: 0,
    anomalies: 0
  });

  // Filter states - Fixed date picker to use full day ranges
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    dataType: 'default',
    trendline: 'none',
    analysisType: 'none',
    showAnomalies: false,
    predictionModels: []
  });

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch stations on mount
  useEffect(() => {
    fetchStations();
  }, []);

  const fetchStations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/stations`);
      if (response.ok) {
        const data = await response.json();
        setStations(data.stations || []);
      }
    } catch (error) {
      console.error('Error fetching stations:', error);
    } finally {
      setLoading(false);
    }
  };

  // Calculate stats from data
  const calculateStats = useCallback((data) => {
    if (!data || data.length === 0) return;

    let currentLevel = 0;
    let change24h = 0;
    let avgTemp = 0;
    let anomalyCount = 0;

    if (selectedStations.includes('All Stations') || selectedStations.length > 1) {
      const stationGroups = {};
      data.forEach(d => {
        if (!stationGroups[d.Station]) {
          stationGroups[d.Station] = [];
        }
        stationGroups[d.Station].push(d);
      });

      let stationCount = 0;
      Object.values(stationGroups).forEach(stationData => {
        if (stationData.length > 0) {
          stationCount++;
          const levels = stationData.map(d => d.Tab_Value_mDepthC1).filter(v => !isNaN(v));
          const temps = stationData.map(d => d.Tab_Value_monT2m).filter(v => !isNaN(v));
          
          if (levels.length > 0) {
            currentLevel += levels[levels.length - 1];
            if (levels.length > 1) {
              change24h += levels[levels.length - 1] - levels[0];
            }
          }
          if (temps.length > 0) {
            avgTemp += temps.reduce((a, b) => a + b, 0) / temps.length;
          }
          anomalyCount += stationData.filter(d => d.anomaly === -1).length;
        }
      });

      if (stationCount > 0) {
        currentLevel /= stationCount;
        change24h /= stationCount;
        avgTemp /= stationCount;
      }
    } else {
      const levels = data.map(d => d.Tab_Value_mDepthC1).filter(v => !isNaN(v));
      const temps = data.map(d => d.Tab_Value_monT2m).filter(v => !isNaN(v));
      
      if (levels.length > 0) {
        currentLevel = levels[levels.length - 1];
        if (levels.length > 1) {
          change24h = levels[levels.length - 1] - levels[0];
        }
      }
      if (temps.length > 0) {
        avgTemp = temps.reduce((a, b) => a + b, 0) / temps.length;
      }
      anomalyCount = data.filter(d => d.anomaly === -1).length;
    }

    setStats({
      current_level: currentLevel,
      '24h_change': change24h,
      avg_temp: avgTemp,
      anomalies: anomalyCount
    });
  }, [selectedStations]);

  // Fetch predictions - STABLE VERSION
  const fetchPredictions = useCallback(async (station) => {
    if (filters.predictionModels.length === 0) {
      setPredictions({ arima: null, prophet: null });
      return;
    }

    try {
      const params = new URLSearchParams({
        station: station,
        model: filters.predictionModels.join(',')
      });

      const response = await fetch(`${API_BASE_URL}/predictions?${params}`);
      if (response.ok) {
        const data = await response.json();
        setPredictions(data);
      }
    } catch (error) {
      console.error('Error fetching predictions:', error);
      setPredictions({ arima: null, prophet: null });
    }
  }, [filters.predictionModels]);

  // Fetch data - FIXED VERSION to prevent infinite loops
  const fetchData = useCallback(async () => {
    if (stations.length === 0 || selectedStations.length === 0) return;
    
    setLoading(true);
    try {
      let allData = [];

      if (selectedStations.includes('All Stations')) {
        const stationList = stations.filter(s => s !== 'All Stations');
        
        for (const station of stationList) {
          const params = new URLSearchParams({
            station: station,
            start_date: filters.startDate,
            end_date: filters.endDate,
            data_source: filters.dataType,
            show_anomalies: filters.showAnomalies.toString()
          });

          try {
            const response = await fetch(`${API_BASE_URL}/data?${params}`);
            if (response.ok) {
              const data = await response.json();
              if (Array.isArray(data)) {
                allData = allData.concat(data);
              }
            }
          } catch (err) {
            console.error(`Error fetching data for ${station}:`, err);
          }
        }
      } else {
        for (const station of selectedStations.filter(s => s !== 'All Stations').slice(0, 3)) {
          const params = new URLSearchParams({
            station: station,
            start_date: filters.startDate,
            end_date: filters.endDate,
            data_source: filters.dataType,
            show_anomalies: filters.showAnomalies.toString()
          });

          try {
            const response = await fetch(`${API_BASE_URL}/data?${params}`);
            if (response.ok) {
              const data = await response.json();
              if (Array.isArray(data)) {
                allData = allData.concat(data);
              }
            }
          } catch (err) {
            console.error(`Error fetching data for ${station}:`, err);
          }
        }
      }

      if (Array.isArray(allData) && allData.length > 0) {
        setGraphData(allData);
        
        // For table view, add calculated values
        const enrichedData = allData.map((row, index) => {
          const enriched = { ...row };
          
          // Add trendline value if selected
          if (filters.trendline !== 'none' && allData.length > 1) {
            const trendlineData = calculateTrendline(allData, filters.trendline);
            enriched.trendlineValue = trendlineData?.y?.[index] || 'N/A';
          }
          
          // Add analysis value if selected
          if (filters.analysisType !== 'none' && allData.length > 1) {
            const analysisData = calculateAnalysis(allData, filters.analysisType);
            if (Array.isArray(analysisData)) {
              enriched.analysisValue = analysisData[0]?.y?.[index] || 'N/A';
            } else {
              enriched.analysisValue = analysisData?.y?.[index] || 'N/A';
            }
          }
          
          return enriched;
        });
        
        const sortedData = enrichedData.sort((a, b) => new Date(a.Tab_DateTime || a.Date) - new Date(b.Tab_DateTime || b.Date));
        setTableData(sortedData);
        setCurrentPage(1);

        calculateStats(allData);
      } else {
        setGraphData([]);
        setTableData([]);
        setStats({ current_level: 0, '24h_change': 0, avg_temp: 0, anomalies: 0 });
      }
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  }, [filters.startDate, filters.endDate, filters.dataType, filters.showAnomalies, filters.trendline, filters.analysisType, selectedStations, stations, calculateStats]);

  // AUTO-UPDATE: Fetch data when filters or stations change - FIXED
  useEffect(() => {
    if (stations.length > 0) {
      const timeoutId = setTimeout(() => {
        fetchData();
      }, 300);
      
      return () => clearTimeout(timeoutId);
    }
  }, [fetchData, stations.length]);

  // SEPARATE EFFECT: Handle predictions to prevent infinite loops
  useEffect(() => {
    if (filters.predictionModels.length > 0 && selectedStations.length === 1 && !selectedStations.includes('All Stations') && graphData.length > 0) {
      fetchPredictions(selectedStations[0]);
    } else {
      setPredictions({ arima: null, prophet: null });
    }
  }, [filters.predictionModels, selectedStations, fetchPredictions, graphData.length]);

  // Handle station selection (support multi-select up to 3)
  const handleStationChange = (value) => {
    if (value === 'All Stations') {
      setSelectedStations(['All Stations']);
    } else {
      setSelectedStations(prev => {
        if (prev.includes(value)) {
          return prev.filter(s => s !== value);
        } else if (prev.length < 3 && !prev.includes('All Stations')) {
          return [...prev, value];
        } else {
          return [value];
        }
      });
    }
  };

  // Handle filter changes - data will auto-update via useEffect
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Calculate trendline
  const calculateTrendline = (data, period) => {
    if (!data || data.length < 2) return null;

    const periodDays = {
      '7d': 7,
      '30d': 30,
      '90d': 90,
      '1y': 365,
      'last_decade': 3650,
      'last_two_decades': 7300,
      'all': null
    };

    const days = periodDays[period];
    let filteredData = data;

    if (days !== null) {
      const endDate = new Date(data[data.length - 1].Tab_DateTime);
      const startDate = new Date(endDate - days * 24 * 60 * 60 * 1000);
      filteredData = data.filter(d => new Date(d.Tab_DateTime) >= startDate);
    }
    
    if (filteredData.length < 2) return null;

    const n = filteredData.length;
    const xValues = filteredData.map((_, i) => i);
    const yValues = filteredData.map(d => d.Tab_Value_mDepthC1);
    
    const sumX = xValues.reduce((a, b) => a + b, 0);
    const sumY = yValues.reduce((a, b) => a + b, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return {
      x: filteredData.map(d => d.Tab_DateTime),
      y: xValues.map(x => slope * x + intercept),
      type: 'scatter',
      mode: 'lines',
      name: `Trendline (${period})`,
      line: { color: 'yellow', dash: 'dash', width: 2 }
    };
  };

  // Calculate analysis
  const calculateAnalysis = (data, analysisType) => {
    if (!data || data.length === 0) return null;

    const analyses = {
      'rolling_avg_3h': { window: 3, name: '3-Hour Avg', color: 'violet' },
      'rolling_avg_6h': { window: 6, name: '6-Hour Avg', color: 'cyan' },
      'rolling_avg_24h': { window: 24, name: '24-Hour Avg', color: 'magenta' },
      'all': null
    };

    if (analysisType === 'all') {
      return Object.entries(analyses)
        .filter(([key]) => key !== 'all')
        .map(([key, config]) => calculateAnalysis(data, key))
        .filter(Boolean);
    }

    const config = analyses[analysisType];
    if (!config) return null;

    const rollingAvg = [];
    const windowSize = config.window;
    
    for (let i = 0; i < data.length; i++) {
      const start = Math.max(0, i - windowSize + 1);
      const window = data.slice(start, i + 1);
      const validValues = window.map(d => d.Tab_Value_mDepthC1).filter(v => !isNaN(v));
      const avg = validValues.length > 0 
        ? validValues.reduce((sum, v) => sum + v, 0) / validValues.length 
        : null;
      rollingAvg.push(avg);
    }
    
    return {
      x: data.map(d => d.Tab_DateTime),
      y: rollingAvg,
      type: 'scatter',
      mode: 'lines',
      name: config.name,
      line: { color: config.color, width: 2 }
    };
  };

  // Create plot with preserved zoom/pan
  const createPlot = () => {
    if (!graphData || graphData.length === 0) {
      return {
        data: [],
        layout: {
          title: 'No Data Available',
          plot_bgcolor: '#142950',
          paper_bgcolor: '#142950',
          font: { color: 'white' },
          uirevision: 'true'
        }
      };
    }

    const traces = [];

    if (filters.dataType === 'tides') {
      if (graphData.length > 0) {
        const highTideData = graphData.filter(d => d.HighTide != null && !isNaN(d.HighTide));
        const lowTideData = graphData.filter(d => d.LowTide != null && !isNaN(d.LowTide));
        
        if (highTideData.length > 0) {
          traces.push({
            x: highTideData.map(d => d.Date || d.Tab_DateTime),
            y: highTideData.map(d => d.HighTide),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'High Tide',
            line: { color: 'deepskyblue', width: 2 },
            marker: { size: 4 }
          });
        }
        
        if (lowTideData.length > 0) {
          traces.push({
            x: lowTideData.map(d => d.Date || d.Tab_DateTime),
            y: lowTideData.map(d => d.LowTide),
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Low Tide',
            line: { color: 'lightcoral', width: 2 },
            marker: { size: 4 }
          });
        }
        
        if (highTideData.length === 0 && lowTideData.length === 0) {
          return {
            data: [],
            layout: {
              title: 'No Tidal Data Available',
              plot_bgcolor: '#142950',
              paper_bgcolor: '#142950',
              font: { color: 'white' },
              annotations: [{
                text: 'Tidal data not available for selected stations/dates',
                x: 0.5,
                y: 0.5,
                xref: 'paper',
                yref: 'paper',
                showarrow: false,
                font: { size: 16, color: 'white' }
              }],
              uirevision: 'constant'
            }
          };
        }
      }
    } else {
      if (selectedStations.includes('All Stations')) {
        const stationGroups = {};
        graphData.forEach(d => {
          if (!stationGroups[d.Station]) {
            stationGroups[d.Station] = [];
          }
          stationGroups[d.Station].push(d);
        });

        Object.entries(stationGroups).forEach(([station, data]) => {
          traces.push({
            x: data.map(d => d.Tab_DateTime),
            y: data.map(d => d.Tab_Value_mDepthC1),
            type: 'scatter',
            mode: 'lines',
            name: station,
            line: { width: 2 }
          });
        });
      } else {
        selectedStations.forEach(station => {
          const stationData = graphData.filter(d => d.Station === station);
          if (stationData.length > 0) {
            traces.push({
              x: stationData.map(d => d.Tab_DateTime),
              y: stationData.map(d => d.Tab_Value_mDepthC1),
              type: 'scatter',
              mode: 'lines',
              name: station,
              line: { width: 2 }
            });
          }
        });
      }

      // Add anomalies if enabled
      if (filters.showAnomalies) {
        const anomalies = graphData.filter(d => d.anomaly === -1 || d.anomaly === 1);
        if (anomalies.length > 0) {
          traces.push({
            x: anomalies.map(d => d.Tab_DateTime),
            y: anomalies.map(d => d.Tab_Value_mDepthC1),
            type: 'scatter',
            mode: 'markers',
            name: 'Anomalies',
            marker: { 
              color: 'red', 
              size: 10, 
              symbol: 'x',
              line: { color: 'white', width: 1 }
            },
            showlegend: true
          });
        }
      }

      // Add trendline if selected
      if (filters.trendline !== 'none') {
        const trendline = calculateTrendline(graphData, filters.trendline);
        if (trendline) {
          traces.push(trendline);
        }
      }

      // Add analysis if selected
      if (filters.analysisType !== 'none') {
        const analysis = calculateAnalysis(graphData, filters.analysisType);
        if (analysis) {
          if (Array.isArray(analysis)) {
            traces.push(...analysis);
          } else {
            traces.push(analysis);
          }
        }
      }

      // Add predictions if available
      if (predictions.arima && selectedStations.length === 1) {
        const lastDate = new Date(graphData[graphData.length - 1].Tab_DateTime);
        const predictionDates = Array.from({ length: predictions.arima.length }, (_, i) => {
          const date = new Date(lastDate);
          date.setHours(date.getHours() + i + 1);
          return date.toISOString();
        });

        traces.push({
          x: predictionDates,
          y: predictions.arima,
          type: 'scatter',
          mode: 'lines',
          name: 'ARIMA Forecast',
          line: { color: 'lime', dash: 'dot', width: 2 }
        });
      }

      if (predictions.prophet && predictions.prophet.length > 0 && selectedStations.length === 1) {
        traces.push({
          x: predictions.prophet.map(p => p.ds),
          y: predictions.prophet.map(p => p.yhat),
          type: 'scatter',
          mode: 'lines',
          name: 'Prophet Forecast',
          line: { color: 'orange', dash: 'dot', width: 2 }
        });
      }
    }

    const currentLayout = plotRef.current?.el?.layout;
    
    return {
      data: traces,
      layout: {
        title: filters.dataType === 'tides' ? 'Tidal Data' : `Sea Level Monitoring`,
        plot_bgcolor: '#142950',
        paper_bgcolor: '#142950',
        font: { color: 'white' },
        xaxis: { 
          title: 'Date/Time', 
          color: 'white', 
          gridcolor: '#1e3c72',
          range: currentLayout?.xaxis?.range
        },
        yaxis: { 
          title: filters.dataType === 'tides' ? 'Tide Level (m)' : 'Sea Level (m)', 
          color: 'white', 
          gridcolor: '#1e3c72',
          range: currentLayout?.yaxis?.range
        },
        margin: { t: 50, r: 20, b: 50, l: 60 },
        height: 400,
        showlegend: true,
        legend: {
          x: 0,
          y: 1,
          bgcolor: 'rgba(20, 41, 80, 0.8)',
          bordercolor: '#2a4a8c',
          borderwidth: 1
        },
        uirevision: 'constant'
      }
    };
  };

  // Export functions
  const exportGraph = () => {
    const plotElement = document.querySelector('.js-plotly-plot');
    if (plotElement) {
      window.Plotly.downloadImage(plotElement, {
        format: 'png',
        width: 1200,
        height: 600,
        filename: `sea_level_graph_${selectedStations.join('_')}_${new Date().toISOString().split('T')[0]}`
      });
    }
  };

  const exportTable = () => {
    if (tableData.length === 0) {
      alert('No data to export');
      return;
    }

    const headers = Object.keys(tableData[0]);
    const csvContent = [
      headers.join(','),
      ...tableData.map(row => 
        headers.map(header => {
          const value = row[header];
          return typeof value === 'string' && value.includes(',') 
            ? `"${value}"` 
            : value;
        }).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sea_level_data_${selectedStations.join('_')}_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Map component - Fixed to prevent state conflicts
  const MapView = useCallback(() => {
    if (mapTab === 'govmap') {
      return (
        <div key="govmap-container" style={{ width: '100%', height: '500px', border: '1px solid #2a4a8c', borderRadius: '8px', overflow: 'hidden' }}>
          <iframe
            key={`govmap-${Date.now()}`}
            src={`${API_BASE_URL}/mapframe?t=${Date.now()}`}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="GovMap"
            loading="eager"
          />
        </div>
      );
    } else {
      return (
        <div key="osm-container">
          <OSMMap 
            key="osm-map"
            stations={stations.filter(s => s !== 'All Stations')}
            currentStation={selectedStations[0]}
            mapData={graphData}
          />
        </div>
      );
    }
  }, [mapTab, stations, selectedStations, graphData]);

  return (
    <div className="dash-container">
      {/* Header */}
      <div className="header">
        <h1 className="navbar-brand">
          <img src="/assets/Mapi_Logo2.png" alt="Mapi Logo" style={{height: '40px', marginRight: '10px'}} />
          Sea Level Monitoring Dashboard
        </h1>
        <div id="current-time">{currentTime.toLocaleString()}</div>
      </div>

      {/* Main Content */}
      <Container fluid className="p-3">
        <Row>
          {/* Filters Column */}
          <Col md={3}>
            <Card className="filters-card">
              <Card.Body>
                <h5 className="mb-3">Filters</h5>
                
                <Form.Group className="mb-3">
                  <Form.Label>Date Range</Form.Label>
                  <Form.Control
                    type="date"
                    value={filters.startDate}
                    onChange={(e) => handleFilterChange('startDate', e.target.value)}
                    className="mb-2"
                  />
                  <Form.Control
                    type="date"
                    value={filters.endDate}
                    onChange={(e) => handleFilterChange('endDate', e.target.value)}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Stations ({selectedStations.length}/3)</Form.Label>
                  {stations.map(station => (
                    <Form.Check
                      key={station}
                      type="checkbox"
                      label={station}
                      checked={selectedStations.includes(station)}
                      onChange={() => handleStationChange(station)}
                      disabled={!selectedStations.includes(station) && selectedStations.length >= 3 && station !== 'All Stations'}
                    />
                  ))}
                  <small className="text-muted">Select up to 3 stations or "All Stations"</small>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Data Type</Form.Label>
                  <Form.Select
                    value={filters.dataType}
                    onChange={(e) => handleFilterChange('dataType', e.target.value)}
                  >
                    <option value="default">Default</option>
                    <option value="tides">Tidal Data</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Trendline Period</Form.Label>
                  <Form.Select
                    value={filters.trendline}
                    onChange={(e) => handleFilterChange('trendline', e.target.value)}
                  >
                    <option value="none">None</option>
                    <option value="7d">7 Days</option>
                    <option value="30d">30 Days</option>
                    <option value="90d">90 Days</option>
                    <option value="1y">1 Year</option>
                    <option value="last_decade">Last Decade</option>
                    <option value="last_two_decades">Last Two Decades</option>
                    <option value="all">All Time</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Analysis Type</Form.Label>
                  <Form.Select
                    value={filters.analysisType}
                    onChange={(e) => handleFilterChange('analysisType', e.target.value)}
                  >
                    <option value="none">None</option>
                    <option value="rolling_avg_3h">3-Hour Average</option>
                    <option value="rolling_avg_6h">6-Hour Average</option>
                    <option value="rolling_avg_24h">24-Hour Average</option>
                    <option value="all">All Analyses</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="checkbox"
                    label="Show Anomalies"
                    checked={filters.showAnomalies}
                    onChange={(e) => handleFilterChange('showAnomalies', e.target.checked)}
                  />
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Prediction Models</Form.Label>
                  <Form.Check
                    type="checkbox"
                    label="ARIMA"
                    checked={filters.predictionModels.includes('arima')}
                    onChange={(e) => {
                      const models = e.target.checked 
                        ? [...filters.predictionModels, 'arima']
                        : filters.predictionModels.filter(m => m !== 'arima');
                      handleFilterChange('predictionModels', models);
                    }}
                  />
                  <Form.Check
                    type="checkbox"
                    label="Prophet"
                    checked={filters.predictionModels.includes('prophet')}
                    onChange={(e) => {
                      const models = e.target.checked 
                        ? [...filters.predictionModels, 'prophet']
                        : filters.predictionModels.filter(m => m !== 'prophet');
                      handleFilterChange('predictionModels', models);
                    }}
                  />
                </Form.Group>

                <Row className="mt-4">
                  <Col>
                    <button 
                      className="btn btn-outline-primary btn-sm w-100"
                      onClick={exportGraph}
                    >
                      Export Graph
                    </button>
                  </Col>
                  <Col>
                    <button 
                      className="btn btn-outline-primary btn-sm w-100"
                      onClick={exportTable}
                    >
                      Export Table
                    </button>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>

          {/* Content Column */}
          <Col md={9}>
            {/* Stats Cards */}
            <Row className="mb-3">
              <Col md={3}>
                <Card className="stat-card">
                  <Card.Body className="text-center p-3">
                    <div className="stat-label">Current Level</div>
                    <div className="stat-value">{stats.current_level.toFixed(3)}m</div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={3}>
                <Card className={`stat-card ${stats['24h_change'] >= 0 ? 'green' : 'red'}`}>
                  <Card.Body className="text-center p-3">
                    <div className="stat-label">24h Change</div>
                    <div className="stat-value">
                      {stats['24h_change'] >= 0 ? '+' : ''}{stats['24h_change'].toFixed(3)}m
                    </div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={3}>
                <Card className="stat-card">
                  <Card.Body className="text-center p-3">
                    <div className="stat-label">Avg. Temp</div>
                    <div className="stat-value">{stats.avg_temp.toFixed(1)}°C</div>
                  </Card.Body>
                </Card>
              </Col>
              <Col md={3}>
                <Card className="stat-card">
                  <Card.Body className="text-center p-3">
                    <div className="stat-label">Anomalies</div>
                    <div className="stat-value">{stats.anomalies}</div>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            {/* Tabs */}
            <Card>
              <Card.Body>
                <Tabs activeKey={activeTab} onSelect={(key) => {
                  setActiveTab(key);
                  if (key === 'graph') {
                    setTimeout(() => {
                      if (plotRef.current?.el) {
                        window.Plotly.Plots.resize(plotRef.current.el);
                      }
                    }, 100);
                  }
                }} className="mb-3">
                  <Tab eventKey="graph" title="Graph View">
                    {loading ? (
                      <div className="text-center p-5">
                        <div className="spinner-border text-primary" role="status">
                          <span className="visually-hidden">Loading...</span>
                        </div>
                      </div>
                    ) : graphData.length > 0 ? (
                      <Plot
                        ref={plotRef}
                        data={createPlot().data}
                        layout={createPlot().layout}
                        config={{ responsive: true }}
                        style={{ width: '100%', height: '400px' }}
                        useResizeHandler={true}
                      />
                    ) : (
                      <div className="text-center p-5">
                        <p>No data to display. Select a station to view data.</p>
                      </div>
                    )}
                  </Tab>
                  
                  <Tab eventKey="table" title="Table View">
                    <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
                      {tableData.length > 0 ? (
                        <>
                          <table className="table table-dark table-striped">
                            <thead>
                              <tr>
                                <th>Date/Time</th>
                                <th>Station</th>
                                {filters.dataType === 'tides' ? (
                                  <>
                                    <th>High Tide (m)</th>
                                    <th>High Tide Time</th>
                                    <th>High Tide Temp (°C)</th>
                                    <th>Low Tide (m)</th>
                                    <th>Low Tide Time</th>
                                    <th>Low Tide Temp (°C)</th>
                                  </>
                                ) : (
                                  <>
                                    <th>Sea Level (m)</th>
                                    <th>Temperature (°C)</th>
                                  </>
                                )}
                                <th>Anomaly</th>
                                {filters.trendline !== 'none' && <th>Trendline Value</th>}
                                {filters.analysisType !== 'none' && <th>Analysis Value</th>}
                                {filters.predictionModels.includes('arima') && <th>ARIMA Prediction</th>}
                                {filters.predictionModels.includes('prophet') && <th>Prophet Prediction</th>}
                              </tr>
                            </thead>
                            <tbody>
                              {tableData
                                .slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage)
                                .map((row, idx) => (
                                <tr key={idx}>
                                  <td>{filters.dataType === 'tides' ? row.Date : (row.Tab_DateTime && !isNaN(new Date(row.Tab_DateTime)) ? new Date(row.Tab_DateTime).toISOString().replace('T', ' ').replace('.000Z', '') : 'Invalid Date')}</td>
                                  <td>{row.Station}</td>
                                  {filters.dataType === 'tides' ? (
                                    <>
                                      <td>{row.HighTide?.toFixed(3) || 'N/A'}</td>
                                      <td>{row.HighTideTime || 'N/A'}</td>
                                      <td>{row.HighTideTemp?.toFixed(1) || 'N/A'}</td>
                                      <td>{row.LowTide?.toFixed(3) || 'N/A'}</td>
                                      <td>{row.LowTideTime || 'N/A'}</td>
                                      <td>{row.LowTideTemp?.toFixed(1) || 'N/A'}</td>
                                    </>
                                  ) : (
                                    <>
                                      <td>{row.Tab_Value_mDepthC1?.toFixed(3) || 'N/A'}</td>
                                      <td>{row.Tab_Value_monT2m?.toFixed(1) || 'N/A'}</td>
                                    </>
                                  )}
                                  <td>{row.anomaly || 0}</td>
                                  {filters.trendline !== 'none' && <td>{typeof row.trendlineValue === 'number' ? row.trendlineValue.toFixed(3) : row.trendlineValue}</td>}
                                  {filters.analysisType !== 'none' && <td>{typeof row.analysisValue === 'number' ? row.analysisValue.toFixed(3) : row.analysisValue}</td>}
                                  {filters.predictionModels.includes('arima') && <td>{predictions.arima && predictions.arima[idx] ? predictions.arima[idx].toFixed(3) : 'N/A'}</td>}
                                  {filters.predictionModels.includes('prophet') && <td>{predictions.prophet && predictions.prophet[idx] ? predictions.prophet[idx].yhat?.toFixed(3) || predictions.prophet[idx].toFixed(3) : 'N/A'}</td>}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <div className="d-flex justify-content-between align-items-center mt-3">
                            <span className="text-muted">
                              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, tableData.length)} of {tableData.length} entries
                            </span>
                            <div>
                              <button 
                                className="btn btn-outline-primary btn-sm me-2"
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                              >
                                Previous
                              </button>
                              <span className="mx-2">Page {currentPage} of {Math.ceil(tableData.length / itemsPerPage)}</span>
                              <button 
                                className="btn btn-outline-primary btn-sm ms-2"
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, Math.ceil(tableData.length / itemsPerPage)))}
                                disabled={currentPage === Math.ceil(tableData.length / itemsPerPage)}
                              >
                                Next
                              </button>
                            </div>
                          </div>
                        </>
                      ) : (
                        <p className="text-center">No data to display</p>
                      )}
                    </div>
                  </Tab>
                  
                  <Tab eventKey="map" title="Map View">
                    <Tabs activeKey={mapTab} onSelect={setMapTab} className="mb-2">
                      <Tab eventKey="osm" title="OpenStreetMap">
                        <MapView />
                      </Tab>
                      <Tab eventKey="govmap" title="GovMap">
                        <MapView />
                      </Tab>
                    </Tabs>
                  </Tab>
                </Tabs>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default App;