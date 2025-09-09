// frontend/src/components/GraphView.js - Enhanced with Kalman filter support
import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import moment from 'moment';

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

          // Fetch predictions
          if (filters.predictionModels && filters.predictionModels.length > 0) {
            try {
              // Build model parameter string
              const modelParam = filters.predictionModels.includes('kalman') ? 'kalman' :
                                filters.predictionModels.includes('ensemble') ? 'ensemble' :
                                filters.predictionModels.join(',');
              
              const predResponse = await fetch(
                `${apiBaseUrl}/predictions?station=${filters.station}&model=${modelParam}`
              );
              
              if (predResponse.ok) {
                const predData = await predResponse.json();
                
                // Kalman Filter predictions with confidence intervals
                if (predData.kalman && predData.kalman.length > 0) {
                  const kalmanData = predData.kalman;
                  
                  // Check if it's a nowcast (first point)
                  const nowcast = kalmanData.find(p => p.type === 'nowcast');
                  if (nowcast) {
                    traces.push({
                      x: [new Date(nowcast.ds)],
                      y: [nowcast.yhat],
                      type: 'scatter',
                      mode: 'markers',
                      name: 'Nowcast (Filtered State)',
                      marker: { 
                        color: '#00ff00', 
                        symbol: 'star', 
                        size: 12,
                        line: { color: 'white', width: 2 }
                      },
                      hovertemplate: '<b>Current Nowcast</b><br>%{x}<br>Level: %{y:.3f}m<br>Uncertainty: ±' + 
                                    (nowcast.uncertainty ? nowcast.uncertainty.toFixed(3) : '0.000') + 'm<extra></extra>'
                    });
                  }
                  
                  // Forecast line
                  const forecastData = kalmanData.filter(p => p.type !== 'nowcast');
                  traces.push({
                    x: forecastData.map(item => new Date(item.ds)),
                    y: forecastData.map(item => item.yhat),
                    type: 'scattergl',
                    mode: 'lines',
                    name: 'Kalman Filter Forecast',
                    line: { color: '#00ff88', width: 2, dash: 'solid' },
                    hovertemplate: '<b>Kalman Forecast</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
                  });
                  
                  // Confidence intervals (if available)
                  if (forecastData[0]?.yhat_lower !== undefined) {
                    // Upper confidence band
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
                    
                    // Lower confidence band
                    traces.push({
                      x: forecastData.map(item => new Date(item.ds)),
                      y: forecastData.map(item => item.yhat_lower),
                      type: 'scattergl',
                      mode: 'lines',
                      name: '95% CI Lower',
                      line: { color: 'rgba(0, 255, 136, 0.2)', width: 1, dash: 'dot' },
                      showlegend: false,
                      hovertemplate: '<b>95% Confidence Interval</b><br>%{x}<br>Lower: %{y:.3f}m<extra></extra>'
                    });
                  }
                }
                
                // Ensemble predictions
                if (predData.ensemble && predData.ensemble.length > 0) {
                  traces.push({
                    x: predData.ensemble.map(item => new Date(item.ds)),
                    y: predData.ensemble.map(item => item.yhat),
                    type: 'scattergl',
                    mode: 'lines',
                    name: 'Ensemble Forecast',
                    line: { color: '#ffaa00', width: 2, dash: 'dash' },
                    hovertemplate: '<b>Ensemble</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
                  });
                }
                
                // ARIMA predictions (fallback)
                if (predData.arima && predData.arima.length > 0) {
                  traces.push({
                    x: predData.arima.map(item => new Date(item.ds)),
                    y: predData.arima.map(item => item.yhat),
                    type: 'scattergl',
                    mode: 'lines',
                    name: 'ARIMA Forecast',
                    line: { color: '#00ffff', width: 1.5, dash: 'dot' },
                    hovertemplate: '<b>ARIMA</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
                  });
                }
                
                // Prophet predictions (fallback)
                if (predData.prophet && predData.prophet.length > 0) {
                  traces.push({
                    x: predData.prophet.map(item => new Date(item.ds)),
                    y: predData.prophet.map(item => item.yhat),
                    type: 'scattergl',
                    mode: 'lines',
                    name: 'Prophet Forecast',
                    line: { color: '#ff8800', width: 1.5, dash: 'dashdot' },
                    hovertemplate: '<b>Prophet</b><br>%{x}<br>Level: %{y:.3f}m<extra></extra>'
                  });
                }
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

  // Layout configuration
  const layout = {
    title: {
      text: `Sea Level Analysis - ${filters.station}`,
      font: { color: 'white', size: 20 }
    },
    plot_bgcolor: '#1a2332',
    paper_bgcolor: '#0c1c35',
    font: { color: 'white' },
    xaxis: {
      title: 'Date/Time',
      color: 'white',
      gridcolor: '#2a3f5f',
      showgrid: true,
      zeroline: false
    },
    yaxis: {
      title: 'Sea Level (m)',
      color: 'white',
      gridcolor: '#2a3f5f',
      showgrid: true,
      zeroline: true,
      zerolinecolor: '#666'
    },
    legend: {
      x: 0,
      y: 1,
      bgcolor: 'rgba(0,0,0,0.5)',
      bordercolor: '#444',
      borderwidth: 1
    },
    hovermode: 'x unified',
    margin: { l: 60, r: 30, t: 60, b: 60 },
    autosize: true,
    showlegend: true
  };

  const config = {
    displayModeBar: true,
    displaylogo: false,
    responsive: true,
    toImageButtonOptions: {
      format: 'png',
      filename: `sea_level_${filters.station}_${new Date().toISOString().split('T')[0]}`,
      height: 600,
      width: 1200,
      scale: 2
    }
  };

  if (isLoading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: 'white'
      }}>
        <div>Loading sea level data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '400px',
        color: '#ff4444'
      }}>
        <div>Error: {error}</div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Plot
        data={graphData}
        layout={layout}
        config={config}
        style={{ width: '100%', height: '500px' }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default GraphView;