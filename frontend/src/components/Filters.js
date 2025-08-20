import React from 'react';
import { Form, Button } from 'react-bootstrap';
import DatePicker from 'react-date-picker';
import moment from 'moment';

const Filters = ({ stations, filters, setFilters, apiBaseUrl }) => {
  const handleExportGraph = async () => {
    const response = await fetch(`${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=${filters.dataType}&show_anomalies=${filters.showAnomalies}`);
    const data = await response.json();
    const filename = `sea_level_${filters.station || 'AllStations'}_${moment(filters.startDate).format('YYYY-MM-DD')}_to_${moment(filters.endDate).format('YYYY-MM-DD')}.json`;
    const blob = new Blob([JSON.stringify(data)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleExportTable = async () => {
    const response = await fetch(`${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=${filters.dataType}`);
    const data = await response.json();
    const csv = convertToCSV(data);
    const filename = `sea_level_${filters.station || 'AllStations'}_${moment(filters.startDate).format('YYYY-MM-DD')}_to_${moment(filters.endDate).format('YYYY-MM-DD')}.csv`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const convertToCSV = (data) => {
    if (!data || data.length === 0) return '';
    const headers = Object.keys(data[0]);
    const rows = data.map(row => headers.map(header => JSON.stringify(row[header])).join(','));
    return [headers.join(','), ...rows].join('\n');
  };

  return (
    <div>
      <h3>Data Filters</h3>
      <Form>
        <Form.Group>
          <Form.Label>Date Range:</Form.Label>
          <div>
            <DatePicker
              onChange={(date) => setFilters({ ...filters, startDate: date })}
              value={filters.startDate}
              format="yyyy-MM-dd"
            />
            <DatePicker
              onChange={(date) => setFilters({ ...filters, endDate: date })}
              value={filters.endDate}
              format="yyyy-MM-dd"
            />
          </div>
        </Form.Group>

        <Form.Group>
          <Form.Label>Station Selection:</Form.Label>
          <Form.Select
            value={filters.station}
            onChange={(e) => setFilters({ ...filters, station: e.target.value })}
          >
            {stations.map((station) => (
              <option key={station} value={station}>{station}</option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group>
          <Form.Label>Data Type:</Form.Label>
          <Form.Select
            value={filters.dataType}
            onChange={(e) => setFilters({ ...filters, dataType: e.target.value })}
          >
            <option value="default">Default Sensor Data</option>
            <option value="tides">Tidal Data</option>
          </Form.Select>
        </Form.Group>

        <Form.Group>
          <Form.Label>Trendline Period:</Form.Label>
          <Form.Select
            value={filters.trendline}
            onChange={(e) => setFilters({ ...filters, trendline: e.target.value })}
          >
            <option value="none">No Trendline</option>
            <option value="all">All Period</option>
            <option value="last_two_decades">Last Two Decades</option>
            <option value="last_decade">Last Decade</option>
          </Form.Select>
        </Form.Group>

        <Form.Group>
          <Form.Label>Analysis Type:</Form.Label>
          <Form.Select
            value={filters.analysisType}
            onChange={(e) => setFilters({ ...filters, analysisType: e.target.value })}
          >
            <option value="none">None</option>
            <option value="rolling_avg_3h">3-Hour Rolling Avg</option>
            <option value="rolling_avg_6h">6-Hour Rolling Avg</option>
            <option value="rolling_avg_24h">24-Hour Rolling Avg</option>
            <option value="all">All Rolling Averages</option>
          </Form.Select>
        </Form.Group>

        <Form.Group>
          <Form.Check
            type="switch"
            label="Show Anomalies"
            checked={filters.showAnomalies}
            onChange={(e) => setFilters({ ...filters, showAnomalies: e.target.checked })}
          />
        </Form.Group>

        <Form.Group>
          <Form.Label>Prediction Models:</Form.Label>
          <Form.Check
            type="switch"
            label="ARIMA"
            checked={filters.predictionModels.includes('arima')}
            onChange={(e) => {
              const models = e.target.checked
                ? [...filters.predictionModels, 'arima']
                : filters.predictionModels.filter(m => m !== 'arima');
              setFilters({ ...filters, predictionModels: models });
            }}
          />
          <Form.Check
            type="switch"
            label="Prophet"
            checked={filters.predictionModels.includes('prophet')}
            onChange={(e) => {
              const models = e.target.checked
                ? [...filters.predictionModels, 'prophet']
                : filters.predictionModels.filter(m => m !== 'prophet');
              setFilters({ ...filters, predictionModels: models });
            }}
          />
        </Form.Group>

        <div className="export-buttons">
          <Button onClick={handleExportGraph} className="w-50">Export Graph</Button>
          <Button onClick={handleExportTable} className="w-50">Export Table</Button>
        </div>
      </Form>
    </div>
  );
};

export default Filters;