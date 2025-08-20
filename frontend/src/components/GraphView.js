// frontend/src/components/GraphView.js - Added trendlines and rolling avgs
import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import moment from 'moment';

// Helper for linear regression
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

// Helper for rolling average
function rollingAverage(values, window) {
  return values.map((val, idx, arr) => {
    const start = Math.max(0, idx - window + 1);
    const slice = arr.slice(start, idx + 1);
    return slice.reduce((sum, v) => sum + v, 0) / slice.length;
  });
}

const GraphView = ({ filters, apiBaseUrl, setStats }) => {
  const [graphData, setGraphData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=${filters.dataType}&show_anomalies=${filters.showAnomalies}`
        );
        const data = await response.json();
        if (!data || data.length === 0) {
          setGraphData([]);
          setStats({ current_level: null, '24h_change': null, avg_temp: null, anomalies: null });
          return;
        }

        let traces = [];
        if (filters.dataType === 'default') {
          const df = data.map(item => ({
            ...item,
            Tab_DateTime: new Date(item.Tab_DateTime)
          }));

          let mainTrace = {
            x: df.map(item => item.Tab_DateTime),
            y: df.map(item => item.Tab_Value_mDepthC1),
            type: 'scattergl',
            mode: 'lines',
            name: `Sea Level Data (${filters.station})`,
            hoverinfo: 'x+y'
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
                marker: { color: 'red', symbol: 'x', size: 8 }
              });
            }
          }

          // Predictions
          if (filters.predictionModels.length > 0) {
            const predResponse = await fetch(`${apiBaseUrl}/predictions?station=${filters.station}&model=${filters.predictionModels.join(',')}`);
            const predData = await predResponse.json();

            if (predData.arima) {
              traces.push({
                x: predData.arima.map(item => new Date(item.ds)),
                y: predData.arima.map(item => item.yhat),
                type: 'scattergl',
                mode: 'lines',
                name: 'ARIMA Forecast',
                line: { dash: 'dot', color: 'lime' }
              });
            }

            if (predData.prophet) {
              traces.push({
                x: predData.prophet.map(item => new Date(item.ds)),
                y: predData.prophet.map(item => item.yhat),
                type: 'scattergl',
                mode: 'lines',
                name: 'Prophet Forecast',
                line: { dash: 'dot', color: 'orange' }
              });
            }
          }

          // Trendlines (linear fit)
          if (filters.trendline !== 'none') {
            let filteredDf = df;
            const now = new Date();
            if (filters.trendline === 'last_two_decades') {
              const twoDecadesAgo = new Date(now.setFullYear(now.getFullYear() - 20));
              filteredDf = df.filter(item => item.Tab_DateTime >= twoDecadesAgo);
            } else if (filters.trendline === 'last_decade') {
              const decadeAgo = new Date(now.setFullYear(now.getFullYear() - 10));
              filteredDf = df.filter(item => item.Tab_DateTime >= decadeAgo);
            }

            const xNums = filteredDf.map(item => item.Tab_DateTime.getTime());  // Use timestamps for regression
            const y = filteredDf.map(item => item.Tab_Value_mDepthC1);
            const { slope, intercept } = linearRegression(xNums, y);

            const trendY = xNums.map(x => slope * x + intercept);
            traces.push({
              x: filteredDf.map(item => item.Tab_DateTime),
              y: trendY,
              type: 'scatter',
              mode: 'lines',
              name: 'Trendline',
              line: { color: 'yellow', dash: 'dash' }
            });
          }

          // Rolling Averages (assume hourly data; window in hours)
          if (filters.analysisType !== 'none') {
            const y = df.map(item => item.Tab_Value_mDepthC1);
            const x = df.map(item => item.Tab_DateTime);

            const addRollingTrace = (windowHours, color, name) => {
              const rollingY = rollingAverage(y, windowHours);
              traces.push({
                x,
                y: rollingY,
                type: 'scattergl',
                mode: 'lines',
                name,
                line: { color, width: 2 }
              });
            };

            if (filters.analysisType === 'rolling_avg_3h' || filters.analysisType === 'all') {
              addRollingTrace(3, 'purple', '3h Rolling Avg');
            }
            if (filters.analysisType === 'rolling_avg_6h' || filters.analysisType === 'all') {
              addRollingTrace(6, 'green', '6h Rolling Avg');
            }
            if (filters.analysisType === 'rolling_avg_24h' || filters.analysisType === 'all') {
              addRollingTrace(24, 'blue', '24h Rolling Avg');
            }
          }

          // Stats (add live data if available for current_level)
          const liveResponse = await fetch(`${apiBaseUrl}/live_data?station=${filters.station}`);
          const liveData = await liveResponse.json();
          const currentLevel = liveData.data[0]?.Tab_Value_mDepthC1 || (df.length > 0 ? df[df.length - 1].Tab_Value_mDepthC1 : null);

          const stats = {
            current_level: currentLevel,
            '24h_change': df.length > 1 ? df[df.length - 1].Tab_Value_mDepthC1 - df[0].Tab_Value_mDepthC1 : null,
            avg_temp: df.length > 0 ? df.reduce((sum, item) => sum + (item.Tab_Value_monT2m || 0), 0) / df.length : null,
            anomalies: df.filter(item => item.anomaly === -1).length
          };
          setStats(stats);
        } else {
          // Tides handling (already present, but ensure traces match old)
          traces.push({
            x: data.map(item => new Date(item.Date)),
            y: data.map(item => item.HighTide),
            type: 'scatter',
            mode: 'lines',
            name: 'High Tide (m)',
            line: { color: 'deepskyblue' },
            hoverinfo: 'x+y+name'
          });
          traces.push({
            x: data.map(item => new Date(item.Date)),
            y: data.map(item => item.LowTide),
            type: 'scatter',
            mode: 'lines',
            name: 'Low Tide (m)',
            line: { color: 'lightcoral' },
            hoverinfo: 'x+y+name'
          });
          setStats({ current_level: null, '24h_change': null, avg_temp: null, anomalies: null });
        }

        setGraphData(traces);
      } catch (error) {
        console.error('Error fetching graph data:', error);
        setGraphData([]);
        setStats({ current_level: null, '24h_change': null, avg_temp: null, anomalies: null });
      }
    };

    fetchData();
  }, [filters, apiBaseUrl]);

  return (
    <Plot
      data={graphData}
      layout={{
        title: filters.dataType === 'default' ? 'Sea Level Over Time' : 'Tides Over Time',
        xaxis: { title: 'Date', linecolor: '#7FD1AE', gridcolor: '#1e3c72', gridwidth: 0.5 },
        yaxis: { title: filters.dataType === 'default' ? 'Sea Level (m)' : 'Tide Level (m)', linecolor: '#7FD1AE', gridcolor: '#1e3c72', gridwidth: 0.5 },
        showlegend: true,
        plot_bgcolor: '#142950',
        paper_bgcolor: '#0c1c35',
        font: { color: 'white' },
        hovermode: 'x unified',
        legend: { bgcolor: '#1e3c70', font: { size: 10 } }
      }}
      style={{ width: '100%', height: '100%' }}
      config={{ scrollZoom: true }}
    />
  );
};

export default GraphView;