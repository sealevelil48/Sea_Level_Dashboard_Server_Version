import React, { useState, useEffect, useCallback, useRef, useMemo, Suspense, lazy } from 'react';
import { Container, Row, Col, Card, Form, Tabs, Tab, Badge, Button, Spinner } from 'react-bootstrap';
import Plot from 'react-plotly.js';
import * as XLSX from 'xlsx';
import ErrorBoundary from './components/ErrorBoundary';
import { useFavorites } from './hooks/useFavorites';
import apiService from './services/apiService';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

// Lazy load heavy components
const OSMMap = lazy(() => import('./components/OSMMap'));

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://sea-level-dash-local:8001';

function App() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [activeTab, setActiveTab] = useState('graph');
  const [mapTab, setMapTab] = useState('osm');
  const [tableTab, setTableTab] = useState('historical');
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [predictions, setPredictions] = useState({});
  const [selectedStations, setSelectedStations] = useState(['All Stations']);
  const [currentPage, setCurrentPage] = useState(1);
  const [forecastPage, setForecastPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const plotRef = useRef(null);
  const abortControllerRef = useRef(null);
  
  const { favorites, addFavorite, removeFavorite, isFavorite } = useFavorites();
  
  // Initialize stats
  const [stats, setStats] = useState({
    current_level: 0,
    '24h_change': 0,
    avg_temp: 0,
    anomalies: 0
  });

  // Filter states - Modified with 3 days default
  const [filters, setFilters] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    dataType: 'default',
    trendline: 'none',
    analysisType: 'none',
    showAnomalies: false,
    predictionModels: [],
    forecastHours: 72  // Changed default to 3 days
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
      const data = await apiService.getStations();
      setStations(data.stations || []);
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

  // Enhanced fetch predictions for multiple stations
  const fetchPredictions = useCallback(async (stations) => {
    if (filters.predictionModels.length === 0) {
      setPredictions({ arima: null, kalman: null, ensemble: null });
      return;
    }

    try {
      // Determine which model to request
      let modelParam = filters.predictionModels.join(',');
      
      // Support multiple stations
      const stationParam = Array.isArray(stations) ? stations.join(',') : stations;
      
      const params = new URLSearchParams({
        stations: stationParam,
        model: modelParam,
        steps: filters.forecastHours.toString()
      });

      const response = await fetch(`${API_BASE_URL}/predictions?${params}`);
      if (response.ok) {
        const data = await response.json();
        setPredictions(data);
      }
    } catch (error) {
      console.error('Error fetching predictions:', error);
      setPredictions({});
    }
  }, [filters.predictionModels, filters.forecastHours]);

  // Stabilize fetchData with proper dependencies
  const fetchData = useCallback(async () => {
    if (loading || stations.length === 0 || selectedStations.length === 0) return;
    
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    abortControllerRef.current = new AbortController();
    setLoading(true);
    try {
      let allData = [];

      if (selectedStations.includes('All Stations')) {
        const stationList = stations.filter(s => s !== 'All Stations');
        
        for (const station of stationList) {
          const params = {
            station: station,
            start_date: filters.startDate,
            end_date: filters.endDate,
            data_source: filters.dataType,
            show_anomalies: filters.showAnomalies.toString()
          };

          try {
            const data = await apiService.getData(params);
            if (Array.isArray(data)) {
              allData = allData.concat(data);
            }
          } catch (err) {
            console.error(`Error fetching data for ${station}:`, err);
          }
        }
      } else {
        for (const station of selectedStations.filter(s => s !== 'All Stations').slice(0, 3)) {
          const params = {
            station: station,
            start_date: filters.startDate,
            end_date: filters.endDate,
            data_source: filters.dataType,
            show_anomalies: filters.showAnomalies.toString()
          };

          try {
            const data = await apiService.getData(params);
            if (Array.isArray(data)) {
              allData = allData.concat(data);
            }
          } catch (err) {
            console.error(`Error fetching data for ${station}:`, err);
          }
        }
      }

      if (Array.isArray(allData) && allData.length > 0) {
        setGraphData(allData);
        
        // Optimize data for large datasets
        const optimizedData = allData.length > 5000 ? allData.filter((_, i) => i % 10 === 0) : allData;
        
        // Pre-calculate trendline and analysis once
        let trendlineValues = null;
        let analysisValues = null;
        
        if (filters.trendline !== 'none' && optimizedData.length > 1) {
          const trendlineData = calculateTrendline(optimizedData, filters.trendline);
          trendlineValues = trendlineData?.y || [];
        }
        
        if (filters.analysisType !== 'none' && optimizedData.length > 1) {
          const analysisData = calculateAnalysis(optimizedData, filters.analysisType);
          if (Array.isArray(analysisData)) {
            analysisValues = analysisData[0]?.y || [];
          } else {
            analysisValues = analysisData?.y || [];
          }
        }
        
        // Add calculated values to table data
        const enrichedData = optimizedData.map((row, index) => {
          const enriched = { ...row };
          
          if (trendlineValues) {
            enriched.trendlineValue = trendlineValues[index]?.toFixed(3) || 'N/A';
          }
          
          if (analysisValues) {
            enriched.analysisValue = analysisValues[index]?.toFixed(3) || 'N/A';
          }
          
          return enriched;
        });
        
        setTableData(enrichedData.sort((a, b) => new Date(a.Tab_DateTime || a.Date) - new Date(b.Tab_DateTime || b.Date)));
        setCurrentPage(1);
        calculateStats(allData);
      } else {
        setGraphData([]);
        setTableData([]);
        setStats({ current_level: 0, '24h_change': 0, avg_temp: 0, anomalies: 0 });
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        console.error('Error fetching data:', error);
      }
    } finally {
      setLoading(false);
    }
  }, [
    // Remove predictions from dependencies
    filters.startDate, 
    filters.endDate, 
    filters.dataType,
    filters.showAnomalies,
    filters.trendline,
    filters.analysisType,
    selectedStations,
    stations.length // Use length instead of full array
  ]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // Debounced data fetching
  useEffect(() => {
    if (stations.length > 0 && selectedStations.length > 0) {
      const timeoutId = setTimeout(() => {
        fetchData();
      }, 300);
      
      return () => clearTimeout(timeoutId);
    }
  }, [filters.startDate, filters.endDate, filters.dataType, filters.showAnomalies, selectedStations, stations.length]);

  // Separate effect for predictions - support multiple stations
  useEffect(() => {
    if (filters.predictionModels.length > 0 && 
        selectedStations.length > 0 && 
        !selectedStations.includes('All Stations')) {
      const stationsToPredict = selectedStations.filter(s => s !== 'All Stations').slice(0, 3);
      if (stationsToPredict.length > 0) {
        fetchPredictions(stationsToPredict);
      }
    }
  }, [filters.predictionModels, selectedStations, fetchPredictions]);

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

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  // Handle model selection
  const handleModelChange = (model) => {
    const currentModels = filters.predictionModels || [];
    if (currentModels.includes(model)) {
      handleFilterChange('predictionModels', currentModels.filter(m => m !== model));
    } else {
      handleFilterChange('predictionModels', [...currentModels, model]);
    }
  };

  // Calculate trendline - memoized for performance
  const calculateTrendline = useCallback((data, period) => {
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
  }, []);

  // Calculate analysis - memoized for performance
  const calculateAnalysis = useCallback((data, analysisType) => {
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
  }, []);

  // Enhanced plot creation with Kalman support - memoized for performance
  const createPlot = useMemo(() => {
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
      // Tidal data handling (existing code)
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
      }
    } else {
      // Regular sea level data
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

      // ADD PREDICTIONS FOR MULTIPLE STATIONS
      if (predictions && Object.keys(predictions).length > 0) {
        const stationColors = ['#00ff88', '#ffaa00', '#ff6600', '#00aaff', '#ff00aa'];
        let colorIndex = 0;
        
        // Process each station's predictions
        Object.entries(predictions).forEach(([stationKey, stationPredictions]) => {
          if (stationKey === 'global_metadata' || !stationPredictions) return;
          
          const baseColor = stationColors[colorIndex % stationColors.length];
          colorIndex++;
          
          // KALMAN FILTER PREDICTIONS
          if (stationPredictions?.kalman && stationPredictions.kalman.length > 0) {
            const kalmanData = stationPredictions.kalman;
            
            // Check for nowcast
            const nowcast = kalmanData.find(p => p.type === 'nowcast');
            if (nowcast) {
              traces.push({
                x: [new Date(nowcast.ds)],
                y: [nowcast.yhat],
                type: 'scatter',
                mode: 'markers',
                name: `${stationKey} - Nowcast`,
                marker: { 
                  color: baseColor, 
                  symbol: 'star', 
                  size: 12,
                  line: { color: 'white', width: 2 }
                },
                hovertemplate: `<b>${stationKey} Nowcast</b><br>%{x}<br>Level: %{y:.3f}m<br>Uncertainty: ±` + 
                              (nowcast.uncertainty ? nowcast.uncertainty.toFixed(3) : '0.000') + 'm<extra></extra>'
              });
            }
            
            // Forecast line
            const forecastData = kalmanData.filter(p => p.type !== 'nowcast');
            if (forecastData.length > 0) {
              traces.push({
                x: forecastData.map(item => new Date(item.ds)),
                y: forecastData.map(item => item.yhat),
                type: 'scatter',
                mode: 'lines',
                name: `${stationKey} - Kalman Forecast`,
                line: { color: baseColor, width: 2 },
                hovertemplate: `<b>${stationKey} Kalman</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>`
              });
              
              // Confidence intervals (only for first station to avoid clutter)
              if (colorIndex === 1 && forecastData[0]?.yhat_lower !== undefined) {
                traces.push({
                  x: forecastData.map(item => new Date(item.ds)),
                  y: forecastData.map(item => item.yhat_upper),
                  type: 'scatter',
                  mode: 'lines',
                  name: '95% CI Upper',
                  line: { color: `rgba(${parseInt(baseColor.slice(1,3), 16)}, ${parseInt(baseColor.slice(3,5), 16)}, ${parseInt(baseColor.slice(5,7), 16)}, 0.2)`, width: 0 },
                  showlegend: false,
                  hoverinfo: 'skip',
                  fill: 'tonexty',
                  fillcolor: `rgba(${parseInt(baseColor.slice(1,3), 16)}, ${parseInt(baseColor.slice(3,5), 16)}, ${parseInt(baseColor.slice(5,7), 16)}, 0.1)`
                });
                
                traces.push({
                  x: forecastData.map(item => new Date(item.ds)),
                  y: forecastData.map(item => item.yhat_lower),
                  type: 'scatter',
                  mode: 'lines',
                  name: '95% CI Lower',
                  line: { color: `rgba(${parseInt(baseColor.slice(1,3), 16)}, ${parseInt(baseColor.slice(3,5), 16)}, ${parseInt(baseColor.slice(5,7), 16)}, 0.2)`, width: 1, dash: 'dot' },
                  showlegend: false,
                  hovertemplate: `<b>${stationKey} 95% CI</b><br>%{x}<br>Lower: %{y:.3f}m<extra></extra>`
                });
              }
            }
          }
          
          // ENSEMBLE PREDICTIONS
          if (stationPredictions?.ensemble && stationPredictions.ensemble.length > 0) {
            traces.push({
              x: stationPredictions.ensemble.map(item => new Date(item.ds)),
              y: stationPredictions.ensemble.map(item => item.yhat),
              type: 'scatter',
              mode: 'lines',
              name: `${stationKey} - Ensemble`,
              line: { color: baseColor, width: 2, dash: 'dash' },
              hovertemplate: `<b>${stationKey} Ensemble</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>`
            });
          }
          
          // ARIMA PREDICTIONS
          if (stationPredictions?.arima && Array.isArray(stationPredictions.arima) && stationPredictions.arima.length > 0) {
            if (typeof stationPredictions.arima[0] === 'object' && stationPredictions.arima[0].ds) {
              traces.push({
                x: stationPredictions.arima.map(item => new Date(item.ds)),
                y: stationPredictions.arima.map(item => item.yhat),
                type: 'scatter',
                mode: 'lines',
                name: `${stationKey} - ARIMA`,
                line: { color: baseColor, dash: 'dot', width: 2 }
              });
            }
          }
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
  }, [graphData, filters.dataType, selectedStations, filters.showAnomalies, filters.trendline, filters.analysisType, predictions, calculateTrendline, calculateAnalysis]);

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

    const workbook = {
      SheetNames: ['Historical Data'],
      Sheets: {}
    };

    // Historical data worksheet
    workbook.Sheets['Historical Data'] = XLSX.utils.json_to_sheet(tableData);

    // Forecast data worksheet
    const predictionRows = [];
    Object.entries(predictions).forEach(([stationKey, stationPredictions]) => {
      if (stationKey === 'global_metadata' || !stationPredictions) return;
      
      ['kalman', 'ensemble', 'arima'].forEach(model => {
        if (stationPredictions[model] && Array.isArray(stationPredictions[model])) {
          stationPredictions[model].forEach((pred) => {
            predictionRows.push({
              Station: stationKey,
              Model: model,
              DateTime: pred.ds,
              PredictedLevel: pred.yhat || pred,
              Type: pred.type || 'forecast',
              Uncertainty: pred.uncertainty || '',
              UpperBound: pred.yhat_upper || '',
              LowerBound: pred.yhat_lower || ''
            });
          });
        }
      });
    });

    if (predictionRows.length > 0) {
      workbook.SheetNames.push('Forecast Data');
      workbook.Sheets['Forecast Data'] = XLSX.utils.json_to_sheet(predictionRows);
    }

    XLSX.writeFile(workbook, `sea_level_data_${selectedStations.join('_')}_${new Date().toISOString().split('T')[0]}.xlsx`);
  };

  // Map component
  const MapView = useCallback(() => {
    if (mapTab === 'govmap') {
      return (
        <div style={{ width: '100%', height: '500px', border: '1px solid #2a4a8c', borderRadius: '8px', overflow: 'hidden' }}>
          <iframe
            src={`${API_BASE_URL}/mapframe?end_date=${filters.endDate}`}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="GovMap"
            allow="geolocation; accelerometer; clipboard-write"
            sandbox="allow-scripts allow-same-origin allow-forms"
          />
        </div>
      );
    } else {
      return (
        <OSMMap 
          stations={stations.filter(s => s !== 'All Stations')}
          currentStation={selectedStations[0]}
          mapData={graphData}
        />
      );
    }
  }, [mapTab, stations, selectedStations, graphData, filters.endDate]);

  return (
    <ErrorBoundary>
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
                    <div key={station} className="d-flex align-items-center">
                      <Form.Check
                        type="checkbox"
                        label={station}
                        checked={selectedStations.includes(station)}
                        onChange={() => handleStationChange(station)}
                        disabled={!selectedStations.includes(station) && selectedStations.length >= 3 && station !== 'All Stations'}
                        className="flex-grow-1"
                      />
                      {station !== 'All Stations' && (
                        <Button
                          variant="link"
                          size="sm"
                          className="p-0 ms-2"
                          onClick={() => isFavorite(station) ? removeFavorite(station) : addFavorite(station)}
                          title={isFavorite(station) ? 'Remove from favorites' : 'Add to favorites'}
                        >
                          {isFavorite(station) ? '⭐' : '☆'}
                        </Button>
                      )}
                    </div>
                  ))}
                  <small className="text-muted">Select up to 3 stations or "All Stations"</small>
                  {favorites.length > 0 && (
                    <div className="mt-2">
                      <small className="text-info">Favorites: {favorites.join(', ')}</small>
                    </div>
                  )}
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
                  <Form.Label>Forecast Period</Form.Label>
                  <Form.Select
                    value={filters.forecastHours}
                    onChange={(e) => handleFilterChange('forecastHours', parseInt(e.target.value))}
                  >
                    <option value="24">24H</option>
                    <option value="48">48H</option>
                    <option value="72">72H</option>
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
                  <div style={{ 
                    backgroundColor: '#0c1c35', 
                    padding: '10px', 
                    borderRadius: '5px',
                    border: '1px solid #2a3f5f'
                  }}>
                    <Form.Check
                      type="checkbox"
                      id="kalman-check"
                      label={
                        <span title="The Kalman Filter is a powerful algorithm that provides an optimal estimate of the state of a dynamic system from a series of noisy measurements. It's like a sophisticated GPS that constantly refines its location estimate. By tracking the system's past behavior and accounting for known uncertainties, it makes highly accurate short-term forecasts. Learn more: https://en.wikipedia.org/wiki/Kalman_filter">
                          <strong>Kalman Filter</strong>
                        </span>
                      }
                      checked={filters.predictionModels?.includes('kalman') || false}
                      onChange={() => handleModelChange('kalman')}
                    />
                    <Form.Check
                      type="checkbox"
                      id="ensemble-check"
                      label={
                        <span title="Ensemble modeling combines the predictions from multiple independent models to produce a single, more robust and accurate forecast. Instead of relying on a single expert, this method is like taking a poll of many different experts. By averaging their predictions, the errors tend to cancel each other out. Learn more: https://en.wikipedia.org/wiki/Ensemble_learning">
                          <strong>Ensemble</strong>
                        </span>
                      }
                      checked={filters.predictionModels?.includes('ensemble') || false}
                      onChange={() => handleModelChange('ensemble')}
                    />
                    <Form.Check
                      type="checkbox"
                      id="arima-check"
                      label={
                        <span title="ARIMA (Autoregressive Integrated Moving Average) is a statistical model used for time series data analysis and forecasting. It uses patterns in historical data to predict future values by combining autoregressive, integrated, and moving average components to capture repeating patterns and trends in sea level data. Learn more: https://en.wikipedia.org/wiki/Autoregressive_integrated_moving_average">
                          <strong>ARIMA</strong>
                        </span>
                      }
                      checked={filters.predictionModels?.includes('arima') || false}
                      onChange={() => handleModelChange('arima')}
                    />
                  </div>
                  {selectedStations.length > 3 && filters.predictionModels.length > 0 && (
                    <small className="text-warning">
                      Predictions limited to 3 stations maximum
                    </small>
                  )}
                </Form.Group>

                <Row className="mt-4">
                  <Col>
                    <Button 
                      variant="outline-primary"
                      size="sm"
                      className="w-100"
                      onClick={exportGraph}
                    >
                      Export Graph
                    </Button>
                  </Col>
                  <Col>
                    <Button 
                      variant="outline-primary"
                      size="sm"
                      className="w-100"
                      onClick={exportTable}
                    >
                      Export Table
                    </Button>
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
                        data={createPlot.data}
                        layout={createPlot.layout}
                        config={{ responsive: true }}
                        style={{ width: '100%', height: '400px' }}
                        useResizeHandler={true}
                      />
                    ) : (
                      <div className="text-center p-5">
                        <p>No data to display. Select a station to view data.</p>
                      </div>
                    )}
                    {/* Model Status Indicator */}
                    {filters.predictionModels && filters.predictionModels.length > 0 && (
                      <div className="mt-2 text-center">
                        <small style={{ color: '#00ff00' }}>
                          Active Models: {filters.predictionModels.join(', ')} | 
                          Stations: {selectedStations.filter(s => s !== 'All Stations').length > 0 ? 
                            selectedStations.filter(s => s !== 'All Stations').slice(0, 3).join(', ') : 'None'}
                        </small>
                      </div>
                    )}
                  </Tab>
                  
                  <Tab eventKey="table" title="Table View">
                    <Tabs activeKey={tableTab} onSelect={setTableTab} className="mb-2">
                      <Tab eventKey="historical" title="Historical">
                        <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
                          {tableData.length > 0 ? (
                            <>
                              <table className="table table-dark table-striped table-sm">
                                <thead>
                                  <tr>
                                    <th>Date/Time</th>
                                    <th>Station</th>
                                    {filters.dataType === 'tides' ? (
                                      <>
                                        <th>High Tide (m)</th>
                                        <th>Low Tide (m)</th>
                                      </>
                                    ) : (
                                      <>
                                        <th>Sea Level (m)</th>
                                        <th>Temperature (°C)</th>
                                      </>
                                    )}
                                    <th>Anomaly</th>
                                    {filters.trendline !== 'none' && <th>Trendline</th>}
                                    {filters.analysisType !== 'none' && <th>Analysis</th>}
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
                                      <td>{row.LowTide?.toFixed(3) || 'N/A'}</td>
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
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <div className="d-flex justify-content-between align-items-center mt-3">
                            <span className="text-muted">
                              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, tableData.length)} of {tableData.length} entries
                            </span>
                            <div>
                              <Button 
                                variant="outline-primary"
                                size="sm"
                                className="me-2"
                                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                                disabled={currentPage === 1}
                              >
                                Previous
                              </Button>
                              <span className="mx-2">Page {currentPage} of {Math.ceil(tableData.length / itemsPerPage)}</span>
                              <Button 
                                variant="outline-primary"
                                size="sm"
                                className="ms-2"
                                onClick={() => setCurrentPage(prev => Math.min(prev + 1, Math.ceil(tableData.length / itemsPerPage)))}
                                disabled={currentPage === Math.ceil(tableData.length / itemsPerPage)}
                              >
                                Next
                              </Button>
                            </div>
                          </div>
                        </>
                          ) : (
                            <p className="text-center">No data to display</p>
                          )}
                        </div>
                      </Tab>
                      <Tab eventKey="forecast" title="Forecast">
                        <div style={{ overflowX: 'auto', maxHeight: '400px' }}>
                          {(() => {
                            const predictionRows = [];
                            
                            Object.entries(predictions).forEach(([stationKey, stationPredictions]) => {
                              if (stationKey === 'global_metadata' || !stationPredictions) return;
                              
                              ['kalman', 'ensemble', 'arima'].forEach(model => {
                                if (stationPredictions[model] && Array.isArray(stationPredictions[model])) {
                                  stationPredictions[model].forEach((pred) => {
                                    predictionRows.push({
                                      station: stationKey,
                                      model: model,
                                      datetime: pred.ds,
                                      value: pred.yhat || pred,
                                      type: pred.type || 'forecast',
                                      uncertainty: pred.uncertainty,
                                      upper: pred.yhat_upper,
                                      lower: pred.yhat_lower
                                    });
                                  });
                                }
                              });
                            });
                            
                            predictionRows.sort((a, b) => {
                              if (a.station !== b.station) return a.station.localeCompare(b.station);
                              if (a.model !== b.model) return a.model.localeCompare(b.model);
                              return new Date(a.datetime) - new Date(b.datetime);
                            });
                            
                            return predictionRows.length > 0 ? (
                              <>
                                <table className="table table-dark table-striped">
                                <thead>
                                  <tr>
                                    <th>Station</th>
                                    <th>Model</th>
                                    <th>Date/Time</th>
                                    <th>Predicted Level (m)</th>
                                    <th>Type</th>
                                    <th>Uncertainty</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {predictionRows
                                    .slice((forecastPage - 1) * itemsPerPage, forecastPage * itemsPerPage)
                                    .map((row, idx) => (
                                    <tr key={idx}>
                                      <td>{row.station}</td>
                                      <td>
                                        <Badge bg={row.model === 'kalman' ? 'success' : row.model === 'ensemble' ? 'warning' : 'info'}>
                                          {row.model.toUpperCase()}
                                        </Badge>
                                      </td>
                                      <td>{new Date(row.datetime).toISOString().replace('T', ' ').replace('.000Z', '')}</td>
                                      <td>{typeof row.value === 'number' ? row.value.toFixed(3) : 'N/A'}</td>
                                      <td>
                                        <Badge bg={row.type === 'nowcast' ? 'primary' : 'secondary'}>
                                          {row.type || 'forecast'}
                                        </Badge>
                                      </td>
                                      <td>
                                        {row.uncertainty ? `±${row.uncertainty.toFixed(3)}` : 
                                         (row.upper && row.lower) ? `${row.lower.toFixed(3)} - ${row.upper.toFixed(3)}` : 'N/A'}
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                              <div className="d-flex justify-content-between align-items-center mt-3">
                                <span className="text-muted">
                                  Showing {((forecastPage - 1) * itemsPerPage) + 1} to {Math.min(forecastPage * itemsPerPage, predictionRows.length)} of {predictionRows.length} entries
                                </span>
                                <div>
                                  <Button 
                                    variant="outline-primary"
                                    size="sm"
                                    className="me-2"
                                    onClick={() => setForecastPage(prev => Math.max(prev - 1, 1))}
                                    disabled={forecastPage === 1}
                                  >
                                    Previous
                                  </Button>
                                  <span className="mx-2">Page {forecastPage} of {Math.ceil(predictionRows.length / itemsPerPage)}</span>
                                  <Button 
                                    variant="outline-primary"
                                    size="sm"
                                    className="ms-2"
                                    onClick={() => setForecastPage(prev => Math.min(prev + 1, Math.ceil(predictionRows.length / itemsPerPage)))}
                                    disabled={forecastPage === Math.ceil(predictionRows.length / itemsPerPage)}
                                  >
                                    Next
                                  </Button>
                                </div>
                              </div>
                              </>
                            ) : (
                              <p className="text-center">No predictions available. Select prediction models to see forecasts.</p>
                            );
                          })()
                          }
                        </div>
                      </Tab>
                    </Tabs>
                  </Tab>
                  
                  <Tab eventKey="map" title="Map View">
                    <Tabs activeKey={mapTab} onSelect={setMapTab} className="mb-2">
                      <Tab eventKey="osm" title="OpenStreetMap">
                        <Suspense fallback={<Spinner animation="border" />}>
                          <MapView />
                        </Suspense>
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
      <div className="text-center mt-1 mb-3 me-3">
        <small style={{ fontSize: '0.85rem' }}>
          <strong>Disclaimer:</strong> Sea level forecast is based on sea level measurements only and is for informational purposes. Its accuracy is not guaranteed.
        </small>
      </div>
    </div>
    </ErrorBoundary>
  );
}

export default App;