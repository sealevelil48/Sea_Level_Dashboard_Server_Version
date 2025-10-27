import React, { useState, useEffect, useMemo } from 'react';
import Plot from 'react-plotly.js';
import { Button } from 'react-bootstrap';
import apiService from '../services/apiService';

// Helper for linear regression (existing)
function linearRegression(x, y) {
  const n = x.length;
  let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
  for (let i = 0; i < n; i++) {
    sumX += x[i];
    sumY += y[i];
    sumXY += x[i] * y[i];
    sumX2 += x[i] * x[i];
  }
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;
  return { slope, intercept };
}

// Helper for rolling average (existing)
function rollingAverage(values, window) {
  return values.map((val, idx, arr) => {
    const start = Math.max(0, idx - window + 1);
    const slice = arr.slice(start, idx + 1);
    return slice.reduce((sum, v) => sum + v, 0) / slice.length;
  });
}

const GraphView = ({ filters, apiBaseUrl, setStats }) => {
  const [graphData, setGraphData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Track window resize for responsive layout
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Determine if mobile view
  const isMobile = windowWidth < 768;
  const isTablet = windowWidth >= 768 && windowWidth < 1024;

  // Handle fullscreen toggle
  const toggleFullscreen = () => {
    if (!isFullscreen) {
      const elem = document.getElementById('graph-container');
      if (elem.requestFullscreen) {
        elem.requestFullscreen();
      } else if (elem.webkitRequestFullscreen) {
        elem.webkitRequestFullscreen();
      } else if (elem.msRequestFullscreen) {
        elem.msRequestFullscreen();
      }
      setIsFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      } else if (document.webkitExitFullscreen) {
        document.webkitExitFullscreen();
      } else if (document.msExitFullscreen) {
        document.msExitFullscreen();
      }
      setIsFullscreen(false);
    }
  };

  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement || 
                              document.webkitFullscreenElement || 
                              document.msFullscreenElement));
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('msfullscreenchange', handleFullscreenChange);

    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
      document.removeEventListener('webkitfullscreenchange', handleFullscreenChange);
      document.removeEventListener('msfullscreenchange', handleFullscreenChange);
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Fetch historical data
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${new Date(filters.startDate).toISOString().split('T')[0]}&end_date=${new Date(filters.endDate).toISOString().split('T')[0]}&data_source=${filters.dataType}&show_anomalies=${filters.showAnomalies}`
        );
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data || data.length === 0) {
          setGraphData([]);
          setStats({ current_level: null, '24h_change': null, avg_temp: null, anomalies: null });
          return;
        }

        let traces = [];
        
        // Process main data
        if (filters.dataType === 'default') {
          const df = data.map(item => ({
            ...item,
            Tab_DateTime: new Date(item.Tab_DateTime + (item.Tab_DateTime.endsWith('Z') ? '' : 'Z'))
          }));

          // Main sea level trace
          let mainTrace = {
            x: df.map(item => item.Tab_DateTime),
            y: df.map(item => item.Tab_Value_mDepthC1),
            type: 'scattergl',
            mode: 'lines',
            name: `Sea Level - ${filters.station}`,
            line: { color: '#00bfff', width: 2 },
            hovertemplate: '<b>%{x}</b><br>Level: %{y:.3f}m<extra></extra>'
          };
          traces.push(mainTrace);

          // Anomalies
          if (filters.showAnomalies) {
            const anomalies = df.filter(item => item.anomaly === -1);
            if (anomalies.length > 0) {
              traces.push({
                x: anomalies.map(item => item.Tab_DateTime),
                y: anomalies.map(item => item.Tab_Value_mDepthC1),
                type: 'scattergl',
                mode: 'markers',
                name: 'Anomalies',
                marker: { 
                  color: '#ff4444', 
                  symbol: 'x', 
                  size: 10,
                  line: { color: 'white', width: 1 }
                },
                hovertemplate: '<b>Anomaly</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
              });
            }
          }

          // Fetch predictions for multiple stations
          if (filters.predictionModels && filters.predictionModels.length > 0) {
            try {
              // Build model parameter string
              const modelParam = filters.predictionModels.join(',');
              
              // Support multiple stations - use current station or multiple if available
              const stationParam = filters.station;
              
              const predResponse = await fetch(
                `${apiBaseUrl}/predictions?stations=${stationParam}&model=${modelParam}`
              );
              
              if (predResponse.ok) {
                const predData = await predResponse.json();
                
                // Handle multi-station prediction response
                const stationColors = ['#00ff88', '#ffaa00', '#ff6600', '#00aaff', '#ff00aa'];
                let colorIndex = 0;
                
                Object.entries(predData).forEach(([stationKey, stationPredictions]) => {
                  if (stationKey === 'global_metadata') return;
                  
                  const baseColor = stationColors[colorIndex % stationColors.length];
                  colorIndex++;
                  
                  // Kalman Filter predictions
                  if (stationPredictions.kalman && stationPredictions.kalman.length > 0) {
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
                        type: 'scattergl',
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
                          type: 'scattergl',
                          mode: 'lines',
                          name: '95% CI Upper',
                          line: { color: 'rgba(0, 255, 136, 0.2)', width: 0 },
                          showlegend: false,
                          hoverinfo: 'skip',
                          fill: 'tonexty',
                          fillcolor: 'rgba(0, 255, 136, 0.1)'
                        });
                        
                        traces.push({
                          x: forecastData.map(item => new Date(item.ds)),
                          y: forecastData.map(item => item.yhat_lower),
                          type: 'scattergl',
                          mode: 'lines',
                          name: '95% CI Lower',
                          line: { color: 'rgba(0, 255, 136, 0.2)', width: 1, dash: 'dot' },
                          showlegend: false,
                          hovertemplate: `<b>${stationKey} 95% CI</b><br>%{x}<br>Lower: %{y:.3f}m<extra></extra>`
                        });
                      }
                    }
                  }
                  
                  // Ensemble predictions
                  if (stationPredictions.ensemble && stationPredictions.ensemble.length > 0) {
                    traces.push({
                      x: stationPredictions.ensemble.map(item => new Date(item.ds)),
                      y: stationPredictions.ensemble.map(item => item.yhat),
                      type: 'scattergl',
                      mode: 'lines',
                      name: `${stationKey} - Ensemble`,
                      line: { color: baseColor, width: 2, dash: 'dash' },
                      hovertemplate: `<b>${stationKey} Ensemble</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>`
                    });
                  }
                  
                  // ARIMA predictions
                  if (stationPredictions.arima && stationPredictions.arima.length > 0) {
                    traces.push({
                      x: stationPredictions.arima.map(item => new Date(item.ds)),
                      y: stationPredictions.arima.map(item => item.yhat),
                      type: 'scattergl',
                      mode: 'lines',
                      name: `${stationKey} - ARIMA`,
                      line: { color: baseColor, width: 1.5, dash: 'dot' },
                      hovertemplate: `<b>${stationKey} ARIMA</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>`
                    });
                  }
                  
                  // Prophet predictions
                  if (stationPredictions.prophet && stationPredictions.prophet.length > 0) {
                    traces.push({
                      x: stationPredictions.prophet.map(item => new Date(item.ds)),
                      y: stationPredictions.prophet.map(item => item.yhat),
                      type: 'scattergl',
                      mode: 'lines',
                      name: `${stationKey} - Prophet`,
                      line: { color: baseColor, width: 1.5, dash: 'dashdot' },
                      hovertemplate: `<b>${stationKey} Prophet</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>`
                    });
                  }
                });
              }
            } catch (predError) {
              console.error('Error fetching predictions:', predError);
            }
          }

          // Trendlines (existing functionality)
          if (filters.trendline && filters.trendline !== 'none') {
            let filteredDf = df;
            const now = new Date();
            
            if (filters.trendline === 'last_two_decades') {
              const twoDecadesAgo = new Date();
              twoDecadesAgo.setFullYear(now.getFullYear() - 20);
              filteredDf = df.filter(item => item.Tab_DateTime >= twoDecadesAgo);
            } else if (filters.trendline === 'last_decade') {
              const decadeAgo = new Date();
              decadeAgo.setFullYear(now.getFullYear() - 10);
              filteredDf = df.filter(item => item.Tab_DateTime >= decadeAgo);
            }

            if (filteredDf.length > 1) {
              const xNums = filteredDf.map(item => item.Tab_DateTime.getTime());
              const y = filteredDf.map(item => item.Tab_Value_mDepthC1);
              const { slope, intercept } = linearRegression(xNums, y);

              const trendY = xNums.map(x => slope * x + intercept);
              traces.push({
                x: filteredDf.map(item => item.Tab_DateTime),
                y: trendY,
                type: 'scatter',
                mode: 'lines',
                name: `Linear Trend (${filters.trendline.replace(/_/g, ' ')})`,
                line: { color: '#ff00ff', width: 2, dash: 'dash' },
                hovertemplate: '<b>Trend</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
              });
              
              // Calculate trend statistics
              const yearlyTrend = slope * 365 * 24 * 60 * 60 * 1000; // Convert to yearly
              console.log(`Trend: ${yearlyTrend.toFixed(4)} m/year`);
            }
          }

          // Rolling average
          if (filters.rollingAverage && filters.rollingAverage > 0) {
            const rollingAvg = rollingAverage(
              df.map(item => item.Tab_Value_mDepthC1),
              filters.rollingAverage
            );
            traces.push({
              x: df.map(item => item.Tab_DateTime),
              y: rollingAvg,
              type: 'scattergl',
              mode: 'lines',
              name: `${filters.rollingAverage}-point Moving Average`,
              line: { color: '#ffff00', width: 2 },
              hovertemplate: '<b>Moving Avg</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
            });
          }

          // Calculate and set statistics
          const stats = {
            current_level: df[df.length - 1]?.Tab_Value_mDepthC1 || null,
            '24h_change': null,
            avg_temp: null,
            anomalies: null
          };

          if (df.length > 24) {
            const now = df[df.length - 1].Tab_Value_mDepthC1;
            const yesterday = df[df.length - 25]?.Tab_Value_mDepthC1;
            if (now && yesterday) {
              stats['24h_change'] = now - yesterday;
            }
          }

          if (filters.showAnomalies) {
            stats.anomalies = df.filter(item => item.anomaly === -1).length;
          }

          setStats(stats);
        }

        setGraphData(traces);
        
      } catch (err) {
        console.error('Error fetching data:', err);
        setError(err.message);
        setGraphData([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [filters, apiBaseUrl, setStats]);

  // Responsive layout configuration
  const layout = useMemo(() => {
    const stationName = filters.station || 'Multiple Stations';
    
    return {
      title: {
        text: `Sea Level Analysis - ${stationName}`,
        font: { 
          color: 'white', 
          size: isFullscreen ? 24 : (isMobile ? 14 : (isTablet ? 16 : 20))
        },
        x: isMobile && !isFullscreen ? 0 : 0.5,
        xanchor: isMobile && !isFullscreen ? 'left' : 'center'
      },
      plot_bgcolor: '#1a2332',
      paper_bgcolor: '#0c1c35',
      font: { 
        color: 'white',
        size: isFullscreen ? 14 : (isMobile ? 10 : (isTablet ? 11 : 12))
      },
      xaxis: {
        title: isMobile && !isFullscreen ? '' : 'Date/Time',
        color: 'white',
        gridcolor: '#2a3f5f',
        showgrid: true,
        zeroline: false,
        tickangle: isMobile && !isFullscreen ? -45 : 0,
        tickfont: { size: isFullscreen ? 12 : (isMobile ? 9 : 11) }
      },
      yaxis: {
        title: isMobile && !isFullscreen ? 'm' : 'Sea Level (m)',
        color: 'white',
        gridcolor: '#2a3f5f',
        showgrid: true,
        zeroline: true,
        zerolinecolor: '#666',
        tickfont: { size: isFullscreen ? 12 : (isMobile ? 9 : 11) }
      },
      legend: {
        x: isMobile && !isFullscreen ? 0 : 0,
        y: isMobile && !isFullscreen ? -0.2 : 1,
        orientation: isMobile && !isFullscreen ? 'h' : 'v',
        bgcolor: 'rgba(0,0,0,0.5)',
        bordercolor: '#444',
        borderwidth: 1,
        font: { size: isFullscreen ? 12 : (isMobile ? 9 : 11) }
      },
      hovermode: 'x unified',
      margin: isFullscreen 
        ? { l: 80, r: 40, t: 80, b: 80 }
        : (isMobile 
          ? { l: 40, r: 10, t: 40, b: 60 }
          : isTablet
          ? { l: 50, r: 20, t: 50, b: 50 }
          : { l: 60, r: 30, t: 60, b: 60 })
      autosize: true,
      showlegend: true
    };
  }, [filters.station, isMobile, isTablet, isFullscreen]);

  const config = useMemo(() => ({
    displayModeBar: !isMobile || isFullscreen,
    displaylogo: false,
    responsive: true,
    modeBarButtonsToRemove: isMobile && !isFullscreen ? [] : ['lasso2d', 'select2d'],
    toImageButtonOptions: {
      format: 'png',
      filename: `sea_level_${filters.station || 'multiple'}_${new Date().toISOString().split('T')[0]}`,
      height: isFullscreen ? 1080 : (isMobile ? 400 : 600),
      width: isFullscreen ? 1920 : (isMobile ? 800 : 1200),
      scale: 2
    }
  }), [isMobile, isFullscreen, filters.station]);

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: isMobile ? '300px' : '400px',
        color: 'white'
      }}>
        <div>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <div className="mt-2">Loading sea level data...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: isMobile ? '300px' : '400px',
        color: '#ff4444',
        padding: '20px',
        textAlign: 'center'
      }}>
        <div>
          <div style={{ fontSize: isMobile ? '1.2rem' : '1.5rem', marginBottom: '10px' }}>⚠️</div>
          <div>Error: {error}</div>
        </div>
      </div>
    );
  }

  return (
    <div 
      id="graph-container"
      style={{ 
        width: '100%', 
        height: '100%',
        position: 'relative',
        backgroundColor: isFullscreen ? '#0c1c35' : 'transparent'
      }}
    >
      {/* Fullscreen button - Only on mobile */}
      {isMobile && (
        <Button
          variant={isFullscreen ? 'danger' : 'outline-primary'}
          size="sm"
          onClick={toggleFullscreen}
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            zIndex: 1000,
            fontSize: '0.75rem',
            padding: '4px 8px'
          }}
        >
          {isFullscreen ? '✕ Exit' : '⛶ Fullscreen'}
        </Button>
      )}

      <Plot
        data={graphData}
        layout={layout}
        config={config}
        style={{ 
          width: '100%', 
          height: isFullscreen 
            ? '100vh' 
            : (isMobile ? '350px' : (isTablet ? '450px' : '500px'))
        }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default GraphView;