import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Button, Spinner, Tabs, Tab, Table } from 'react-bootstrap';

const translateWind = (windStr) => {
  if (!windStr) return windStr;
  const parts = windStr.split('/');
  if (parts.length !== 2) return windStr;
  const directions = {'045': 'NE', '135': 'SE', '225': 'SW', '315': 'NW', '180': 'S', '000': 'N', '090': 'E', '270': 'W'};
  const dirPart = parts[0].trim();
  let dirText = dirPart;
  if (dirPart.includes('-')) {
    const [start, end] = dirPart.split('-');
    dirText = `${directions[start] || start}-${directions[end] || end}`;
  } else {
    dirText = directions[dirPart] || dirPart;
  }
  return `${dirText} (${parts[1].trim()} km/h)`;
};

const translateWeatherCode = (code) => {
  const codes = {'1220': 'Partly Cloudy', '1250': 'Mostly Cloudy', '1000': 'Clear', '4001': 'Rain', '8000': 'Thunderstorm'};
  return codes[code] || code;
};

const translateSeaStatus = (seaStr) => {
  if (!seaStr) return seaStr;
  const parts = seaStr.split(' / ');
  if (parts.length !== 2) return seaStr;
  const code = parts[0].trim();
  const height = parts[1].trim();
  const seaCodes = {'10': 'Calm', '20': 'Smooth', '30': 'Slight', '40': 'Light', '50': 'Slight', '60': 'Moderate', '70': 'Rough', '80': 'Very Rough', '90': 'High', '95': 'Very High'};
  const description = seaCodes[code] || code;
  return `${description} (${height} cm)`;
};

const MarinersForecastView = ({ apiBaseUrl }) => {
  const [forecastData, setForecastData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('table');
  const [iframeCreated, setIframeCreated] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);

  // Mobile detection
  useEffect(() => {
    const handleResize = () => setWindowWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isMobile = windowWidth < 768;

  const fetchForecastData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${apiBaseUrl}/api/mariners-forecast`);
      
      if (response.ok) {
        const data = await response.json();
        setForecastData(data);
      } else {
        setError(`Failed to fetch mariners forecast: ${response.status}`);
      }
    } catch (err) {
      console.error('Mariners forecast fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  useEffect(() => {
    fetchForecastData();
    const interval = setInterval(fetchForecastData, 30 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchForecastData]);

  useEffect(() => {
    const handleExportEvent = () => {
      exportTable();
    };
    
    window.addEventListener('exportMarinersTable', handleExportEvent);
    return () => window.removeEventListener('exportMarinersTable', handleExportEvent);
  }, [forecastData]);

  const formatDateTime = (dateTimeStr) => {
    return new Date(dateTimeStr).toLocaleString('en-IL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const exportTable = () => {
    if (!forecastData?.locations) return;
    
    const csvData = [];
    csvData.push(['Location', 'Period From', 'Period To', 'Pressure (hPa)', 'Sea Status & Waves', 'Wind', 'Visibility (NM)', 'Weather', 'Swell']);
    
    forecastData.locations.forEach(location => {
      location.forecasts.forEach(forecast => {
        csvData.push([
          `${location.name_eng} (${location.name_heb})`,
          formatDateTime(forecast.from),
          formatDateTime(forecast.to),
          forecast.elements['Pressure'] || 'N/A',
          forecast.elements['Sea status and waves height'] ? translateSeaStatus(forecast.elements['Sea status and waves height']) : 'N/A',
          forecast.elements['Wind direction and speed'] ? translateWind(forecast.elements['Wind direction and speed']) : 'N/A',
          forecast.elements['Visibility'] || 'N/A',
          forecast.elements['Weather code'] ? translateWeatherCode(forecast.elements['Weather code']) : 'N/A',
          forecast.elements['Swell'] || 'N/A'
        ]);
      });
    });
    
    const csvContent = csvData.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mariners_forecast_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (loading) {
    return (
      <div className="text-center p-5">
        <Spinner animation="border" variant="primary" />
        <p className="mt-2">Loading mariners forecast...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center p-5">
        <p className="text-danger">Error: {error}</p>
      </div>
    );
  }

  if (!forecastData || !forecastData.locations) {
    return (
      <div className="text-center p-5">
        <p>No mariners forecast data available</p>
      </div>
    );
  }

  const TableView = () => (
    <div>
      {/* Export button */}
      <div className="mb-2 text-end">
        <Button 
          variant="outline-success" 
          size="sm" 
          onClick={exportTable}
        >
          📥 Export CSV
        </Button>
      </div>

      {/* OUTER DIV: Vertical scroll container */}
      <div 
        style={{ 
          maxHeight: isMobile ? '400px' : '500px',
          overflowY: 'auto',
          marginBottom: '15px'
        }}
      >
        {/* INNER DIV: Horizontal scroll wrapper - CRITICAL FIX */}
        <div 
          className="table-responsive"
          style={{ 
            overflowX: 'auto',
            overflowY: 'visible',  // CRITICAL: Don't block vertical scroll
            WebkitOverflowScrolling: 'touch',
            width: '100%',
            display: 'block'
          }}
        >
          <Table 
            striped 
            bordered 
            hover 
            variant="dark" 
            size="sm"
            style={{
              marginBottom: 0,
              minWidth: isMobile ? '800px' : '1000px'  // Force horizontal scroll
            }}
          >
            <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
              <tr>
                <th style={{ minWidth: '120px' }}>Location</th>
                <th style={{ minWidth: '140px' }}>Period</th>
                <th style={{ minWidth: '100px' }}>Pressure (hPa)</th>
                <th style={{ minWidth: '150px' }}>Sea Status & Waves</th>
                <th style={{ minWidth: '140px' }}>Wind</th>
                <th style={{ minWidth: '100px' }}>Visibility (NM)</th>
                <th style={{ minWidth: '120px' }}>Weather</th>
                <th style={{ minWidth: '100px' }}>Swell</th>
              </tr>
            </thead>
            <tbody>
              {forecastData.locations.map((location) =>
                location.forecasts.map((forecast, idx) => (
                  <tr key={`${location.id}-${idx}`}>
                    <td>
                      <strong>{location.name_eng}</strong>
                      <br />
                      <small className="text-muted">{location.name_heb}</small>
                    </td>
                    <td>
                      <small>
                        {formatDateTime(forecast.from)}
                        <br />
                        to
                        <br />
                        {formatDateTime(forecast.to)}
                      </small>
                    </td>
                    <td>{forecast.elements['Pressure'] || 'N/A'}</td>
                    <td>{forecast.elements['Sea status and waves height'] ? translateSeaStatus(forecast.elements['Sea status and waves height']) : 'N/A'}</td>
                    <td>{forecast.elements['Wind direction and speed'] ? translateWind(forecast.elements['Wind direction and speed']) : 'N/A'}</td>
                    <td>{forecast.elements['Visibility'] || 'N/A'}</td>
                    <td>{forecast.elements['Weather code'] ? translateWeatherCode(forecast.elements['Weather code']) : 'N/A'}</td>
                    <td>{forecast.elements['Swell'] || 'N/A'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </div>
      </div>

      {/* Mobile scroll hint */}
      {isMobile && (
        <div 
          className="text-center text-muted" 
          style={{ fontSize: '0.85rem', marginTop: '10px' }}
        >
          👆 Swipe left/right to see all columns
        </div>
      )}
    </div>
  );

  return (
    <div>
      <Card className="mb-3">
        <Card.Body>
          <Row>
            <Col>
              <h5 className="mb-1">{forecastData.metadata?.title}</h5>
              <small className="text-muted">
                {forecastData.metadata?.organization} | 
                Issued: {formatDateTime(forecastData.metadata?.issue_datetime)}
              </small>
            </Col>
            <Col xs="auto">
              <Button 
                variant="outline-primary" 
                size="sm" 
                onClick={fetchForecastData}
                disabled={loading}
              >
                {loading ? <Spinner size="sm" /> : '🔄'} Refresh
              </Button>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
        <Tab eventKey="table" title="Table View">
          {activeTab === 'table' && <TableView />}
        </Tab>
        <Tab eventKey="map" title="Map View">
          <div style={{ width: '100%', height: 'clamp(400px, 60vh, 600px)', border: '1px solid #2a4a8c', borderRadius: '8px', overflow: 'hidden' }}>
            {!iframeCreated && activeTab === 'map' && (() => {
              setIframeCreated(true);
              return null;
            })()}
            {iframeCreated && (
              <iframe
                src={`${apiBaseUrl}/api/mariners-mapframe`}
                style={{ width: '100%', height: '100%', border: 'none' }}
                title="Mariners Forecast Map"
                allow="geolocation; accelerometer; clipboard-write"
                sandbox="allow-scripts allow-same-origin allow-forms"
              />
            )}
          </div>
        </Tab>
      </Tabs>

      <div className="text-center mt-3">
        <small className="text-muted">
          <a 
            href="https://ims.gov.il/he/marine" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#666', textDecoration: 'none' }}
          >
            IMS Mariners Forecast ©
          </a>
        </small>
      </div>
    </div>
  );
};

export default MarinersForecastView;