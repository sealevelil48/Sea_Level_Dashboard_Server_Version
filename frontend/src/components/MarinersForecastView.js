import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Button, Spinner, Tabs, Tab, Table } from 'react-bootstrap';
import { 
  parseWindInfo, 
  translateWeatherCode, 
  parseWaveHeight, 
  formatPressure, 
  formatVisibility,
  parseSwellInfo 
} from '../utils/imsCodeTranslations';

const MarinersForecastView = ({ apiBaseUrl, isFullscreen = false }) => {
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

  const formatDateTime = (dateTimeStr) => {
    return new Date(dateTimeStr).toLocaleString('en-IL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const exportTable = useCallback(() => {
    if (!forecastData?.locations) return;
    
    const csvData = [];
    csvData.push([
      'Location', 'Period From', 'Period To', 'Pressure (hPa)', 
      'Sea Status & Waves', 'Wind', 'Visibility (NM)', 'Weather', 'Swell'
    ]);
    
    forecastData.locations.forEach(location => {
      location.forecasts.forEach(forecast => {
        csvData.push([
          `${location.name_eng} (${location.name_heb})`,
          formatDateTime(forecast.from),
          formatDateTime(forecast.to),
          forecast.elements['Pressure'] ? 
            formatPressure(forecast.elements['Pressure']) : 'N/A',
          forecast.elements['Sea status and waves height'] ? 
            parseWaveHeight(forecast.elements['Sea status and waves height']) : 'N/A',
          forecast.elements['Wind direction and speed'] ? 
            parseWindInfo(forecast.elements['Wind direction and speed']) : 'N/A',
          forecast.elements['Visibility'] ? 
            formatVisibility(forecast.elements['Visibility']) : 'N/A',
          forecast.elements['Weather code'] ? 
            translateWeatherCode(forecast.elements['Weather code']) : 'N/A',
          forecast.elements['Swell'] ? 
            parseSwellInfo(forecast.elements['Swell']) : 'N/A'
        ]);
      });
    });
    
    const csvContent = csvData.map(row => 
      row.map(cell => `"${cell}"`).join(',')
    ).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mariners_forecast_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [forecastData]);

  useEffect(() => {
    const handleExportEvent = () => exportTable();
    window.addEventListener('exportMarinersTable', handleExportEvent);
    return () => window.removeEventListener('exportMarinersTable', handleExportEvent);
  }, [exportTable]);

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

  return (
    <div>
      {/* Header */}
      <Card className="mb-3">
        <Card.Body>
          <Row>
            <Col>
              <h5 className="mb-1" style={{ fontSize: isMobile ? '1rem' : '1.25rem' }}>
                {forecastData.metadata?.title}
              </h5>
              <small style={{ 
                color: '#FFFFFF',
                fontSize: isMobile ? '0.75rem' : '0.875rem' 
              }}>
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

      {/* Tabs */}
      <Tabs 
        activeKey={activeTab} 
        onSelect={(k) => setActiveTab(k)} 
        className="mb-3"
      >
        <Tab eventKey="table" title="Table View">
          {activeTab === 'table' && (
            <div style={{ 
              overflowX: 'auto',
              maxHeight: isFullscreen ? 'calc(100vh - 200px)' : 'clamp(400px, 60vh, 600px)'
            }}>
              <Table 
                striped 
                bordered 
                hover 
                variant="dark" 
                size="sm"
                responsive
                style={{ minWidth: '1100px' }}
              >
                <thead style={{ backgroundColor: '#1e3c72' }}>
                  <tr>
                    <th style={{ minWidth: '150px' }}>📍 Location</th>
                    <th style={{ minWidth: '160px' }}>⏰ Period</th>
                    <th style={{ minWidth: '100px' }}>🌡️ Pressure (hPa)</th>
                    <th style={{ minWidth: '180px' }}>🌊 Sea Status</th>
                    <th style={{ minWidth: '150px' }}>💨 Wind</th>
                    <th style={{ minWidth: '100px' }}>👁️ Visibility (nm)</th>
                    <th style={{ minWidth: '130px' }}>☁️ Weather</th>
                    <th style={{ minWidth: '100px' }}>🌀 Swell</th>
                  </tr>
                </thead>
                <tbody>
                  {forecastData.locations.map((location) =>
                    location.forecasts.map((forecast, idx) => (
                      <tr key={`${location.id}-${idx}`}>
                        <td>
                          <strong>{location.name_eng}</strong>
                          <br />
                          <small style={{ color: '#FFFFFF' }}>{location.name_heb}</small>
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
                        <td>
                          {forecast.elements['Pressure'] ? 
                            formatPressure(forecast.elements['Pressure']) : 
                            'N/A'
                          }
                        </td>
                        <td>
                          {forecast.elements['Sea status and waves height'] ? 
                            parseWaveHeight(forecast.elements['Sea status and waves height']) : 
                            'N/A'
                          }
                        </td>
                        <td>
                          {forecast.elements['Wind direction and speed'] ? 
                            parseWindInfo(forecast.elements['Wind direction and speed']) : 
                            'N/A'
                          }
                        </td>
                        <td>
                          {forecast.elements['Visibility'] ? 
                            formatVisibility(forecast.elements['Visibility']) : 
                            'N/A'
                          }
                        </td>
                        <td>
                          {forecast.elements['Weather code'] ? 
                            translateWeatherCode(forecast.elements['Weather code']) : 
                            'N/A'
                          }
                        </td>
                        <td>
                          {forecast.elements['Swell'] ? 
                            parseSwellInfo(forecast.elements['Swell']) : 
                            'N/A'
                          }
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </Table>
            </div>
          )}
        </Tab>
        
        <Tab eventKey="map" title="Map View">
          <div 
            style={{ 
              width: '100%', 
              height: isFullscreen ? 'calc(100vh - 200px)' : (isMobile ? '350px' : 'clamp(400px, 60vh, 600px)'), 
              border: '1px solid #2a4a8c', 
              borderRadius: '8px', 
              overflow: 'hidden' 
            }}
          >
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

      {/* IMS Copyright */}
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