// frontend/src/components/Filters.js
import React, { useState } from 'react';
import { Form, Row, Col, Button, Card, Badge } from 'react-bootstrap';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";

const Filters = ({ filters, setFilters, stations }) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Handle individual field changes
  const handleChange = (field, value) => {
    setFilters({ ...filters, [field]: value });
  };

  // Handle prediction model selection
  const handleModelChange = (model) => {
    const currentModels = filters.predictionModels || [];
    let newModels;
    
    if (currentModels.includes(model)) {
      // Remove model if already selected
      newModels = currentModels.filter(m => m !== model);
    } else {
      // Add model if not selected
      newModels = [...currentModels, model];
    }
    
    handleChange('predictionModels', newModels);
  };

  // Quick presets
  const applyPreset = (preset) => {
    const now = new Date();
    switch(preset) {
      case 'last24h':
        setFilters({
          ...filters,
          startDate: new Date(now.getTime() - 24 * 60 * 60 * 1000),
          endDate: now,
          predictionModels: ['kalman']
        });
        break;
      case 'lastWeek':
        setFilters({
          ...filters,
          startDate: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
          endDate: now,
          predictionModels: ['kalman']
        });
        break;
      case 'lastMonth':
        setFilters({
          ...filters,
          startDate: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
          endDate: now,
          predictionModels: ['ensemble']
        });
        break;
      default:
        break;
    }
  };

  // Refresh data
  const handleRefresh = () => {
    handleChange('refresh', Date.now());
  };

  return (
    <Card style={{ backgroundColor: '#1a2332', border: '1px solid #2a3f5f' }}>
      <Card.Body>
        <Card.Title style={{ color: 'white', marginBottom: '20px' }}>
          Filter Controls
          <Button 
            variant="outline-info" 
            size="sm" 
            className="float-end"
            onClick={() => setShowAdvanced(!showAdvanced)}
          >
            {showAdvanced ? 'Hide' : 'Show'} Advanced
          </Button>
        </Card.Title>

        {/* Basic Filters */}
        <Row className="mb-3">
          <Col md={3}>
            <Form.Group>
              <Form.Label style={{ color: '#8899aa' }}>Station</Form.Label>
              <Form.Select 
                value={filters.station}
                onChange={(e) => handleChange('station', e.target.value)}
                style={{ 
                  backgroundColor: '#2a3f5f', 
                  color: 'white', 
                  border: '1px solid #444' 
                }}
              >
                {stations.map(station => (
                  <option key={station} value={station}>{station}</option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
          
          <Col md={3}>
            <Form.Group>
              <Form.Label style={{ color: '#8899aa' }}>Start Date</Form.Label>
              <DatePicker
                selected={filters.startDate}
                onChange={(date) => handleChange('startDate', date)}
                className="form-control"
                dateFormat="yyyy-MM-dd"
                style={{ backgroundColor: '#2a3f5f', color: 'white' }}
                customInput={
                  <Form.Control 
                    style={{ 
                      backgroundColor: '#2a3f5f', 
                      color: 'white',
                      border: '1px solid #444' 
                    }}
                  />
                }
              />
            </Form.Group>
          </Col>
          
          <Col md={3}>
            <Form.Group>
              <Form.Label style={{ color: '#8899aa' }}>End Date</Form.Label>
              <DatePicker
                selected={filters.endDate}
                onChange={(date) => handleChange('endDate', date)}
                className="form-control"
                dateFormat="yyyy-MM-dd"
                customInput={
                  <Form.Control 
                    style={{ 
                      backgroundColor: '#2a3f5f', 
                      color: 'white',
                      border: '1px solid #444' 
                    }}
                  />
                }
              />
            </Form.Group>
          </Col>
          
          <Col md={3}>
            <Form.Group>
              <Form.Label style={{ color: '#8899aa' }}>Data Type</Form.Label>
              <Form.Select 
                value={filters.dataType}
                onChange={(e) => handleChange('dataType', e.target.value)}
                style={{ 
                  backgroundColor: '#2a3f5f', 
                  color: 'white', 
                  border: '1px solid #444' 
                }}
              >
                <option value="default">Sea Level</option>
                <option value="tides">Tidal Analysis</option>
                <option value="temperature">Temperature</option>
              </Form.Select>
            </Form.Group>
          </Col>
        </Row>

        {/* Prediction Models Section - Always Visible */}
        <Row className="mb-3">
          <Col md={12}>
            <Form.Label style={{ color: '#8899aa' }}>
              Prediction Models 
              <Badge bg="success" className="ms-2">New</Badge>
            </Form.Label>
            <div className="d-flex flex-wrap gap-3" style={{ 
              padding: '10px', 
              backgroundColor: '#0c1c35', 
              borderRadius: '5px',
              border: '1px solid #2a3f5f'
            }}>
              <Form.Check
                type="checkbox"
                id="kalman-check"
                checked={filters.predictionModels?.includes('kalman') || false}
                onChange={() => handleModelChange('kalman')}
                label={
                  <span style={{ color: 'white' }}>
                    <strong>Kalman Filter</strong>
                    <Badge bg="primary" className="ms-1">Recommended</Badge>
                    <Badge bg="success" className="ms-1">Multi-Station</Badge>
                    <small style={{ color: '#8899aa', display: 'block' }}>
                      State-space model with uncertainty bands
                    </small>
                  </span>
                }
              />
              
              <Form.Check
                type="checkbox"
                id="ensemble-check"
                checked={filters.predictionModels?.includes('ensemble') || false}
                onChange={() => handleModelChange('ensemble')}
                label={
                  <span style={{ color: 'white' }}>
                    <strong>Ensemble</strong>
                    <Badge bg="success" className="ms-1">Multi-Station</Badge>
                    <small style={{ color: '#8899aa', display: 'block' }}>
                      Combined multi-model forecast
                    </small>
                  </span>
                }
              />
              
              <Form.Check
                type="checkbox"
                id="arima-check"
                checked={filters.predictionModels?.includes('arima') || false}
                onChange={() => handleModelChange('arima')}
                label={
                  <span style={{ color: 'white' }}>
                    <strong>ARIMA</strong>
                    <Badge bg="success" className="ms-1">Multi-Station</Badge>
                    <small style={{ color: '#8899aa', display: 'block' }}>
                      Time series model
                    </small>
                  </span>
                }
              />
              
              <Form.Check
                type="checkbox"
                id="prophet-check"
                checked={filters.predictionModels?.includes('prophet') || false}
                onChange={() => handleModelChange('prophet')}
                label={
                  <span style={{ color: 'white' }}>
                    <strong>Prophet</strong>
                    <Badge bg="success" className="ms-1">Multi-Station</Badge>
                    <small style={{ color: '#8899aa', display: 'block' }}>
                      Facebook's forecasting
                    </small>
                  </span>
                }
              />
            </div>
          </Col>
        </Row>

        {/* Advanced Options */}
        {showAdvanced && (
          <>
            <Row className="mb-3">
              <Col md={3}>
                <Form.Group>
                  <Form.Label style={{ color: '#8899aa' }}>Trendline Analysis</Form.Label>
                  <Form.Select 
                    value={filters.trendline || 'none'}
                    onChange={(e) => handleChange('trendline', e.target.value)}
                    style={{ 
                      backgroundColor: '#2a3f5f', 
                      color: 'white', 
                      border: '1px solid #444' 
                    }}
                  >
                    <option value="none">None</option>
                    <option value="all_data">All Data</option>
                    <option value="last_decade">Last Decade</option>
                    <option value="last_two_decades">Last Two Decades</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              
              <Col md={3}>
                <Form.Group>
                  <Form.Label style={{ color: '#8899aa' }}>
                    Rolling Average (Hours)
                  </Form.Label>
                  <Form.Control
                    type="number"
                    min="0"
                    max="168"
                    value={filters.rollingAverage || 0}
                    onChange={(e) => handleChange('rollingAverage', parseInt(e.target.value) || 0)}
                    style={{ 
                      backgroundColor: '#2a3f5f', 
                      color: 'white', 
                      border: '1px solid #444' 
                    }}
                    placeholder="0 = disabled"
                  />
                </Form.Group>
              </Col>
              
              <Col md={3}>
                <Form.Group>
                  <Form.Label style={{ color: '#8899aa' }}>Forecast Hours</Form.Label>
                  <Form.Select 
                    value={filters.forecastHours || 240}
                    onChange={(e) => handleChange('forecastHours', parseInt(e.target.value))}
                    style={{ 
                      backgroundColor: '#2a3f5f', 
                      color: 'white', 
                      border: '1px solid #444' 
                    }}
                  >
                    <option value="24">24 hours (1 day)</option>
                    <option value="72">72 hours (3 days)</option>
                    <option value="168">168 hours (1 week)</option>
                    <option value="240">240 hours (10 days)</option>
                    <option value="720">720 hours (1 month)</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              
              <Col md={3}>
                <Form.Group>
                  <Form.Label style={{ color: '#8899aa' }}>Show Anomalies</Form.Label>
                  <Form.Check
                    type="switch"
                    id="anomalies-switch"
                    label={
                      <span style={{ color: filters.showAnomalies ? '#00ff00' : '#8899aa' }}>
                        {filters.showAnomalies ? "Enabled" : "Disabled"}
                      </span>
                    }
                    checked={filters.showAnomalies || false}
                    onChange={(e) => handleChange('showAnomalies', e.target.checked)}
                    style={{ marginTop: '8px' }}
                  />
                </Form.Group>
              </Col>
            </Row>
          </>
        )}

        {/* Action Buttons */}
        <Row>
          <Col>
            <div className="d-flex justify-content-between align-items-center">
              <div className="d-flex gap-2">
                <Button 
                  variant="primary"
                  onClick={handleRefresh}
                  style={{ 
                    backgroundColor: '#007bff', 
                    border: 'none',
                    minWidth: '120px' 
                  }}
                >
                  🔄 Refresh Data
                </Button>
                
                {filters.predictionModels && filters.predictionModels.length > 0 && (
                  <Button 
                    variant="outline-warning"
                    size="sm"
                    onClick={() => handleChange('predictionModels', [])}
                  >
                    Clear Models
                  </Button>
                )}
              </div>
              
              <div className="d-flex gap-2">
                <Button 
                  variant="outline-light"
                  size="sm"
                  onClick={() => applyPreset('last24h')}
                  title="Last 24 hours with Kalman filter"
                >
                  Quick: 24h
                </Button>
                
                <Button 
                  variant="outline-light"
                  size="sm"
                  onClick={() => applyPreset('lastWeek')}
                  title="Last week with Kalman filter"
                >
                  Quick: 1 Week
                </Button>
                
                <Button 
                  variant="outline-light"
                  size="sm"
                  onClick={() => applyPreset('lastMonth')}
                  title="Last month with ensemble forecast"
                >
                  Quick: 1 Month
                </Button>
              </div>
            </div>
          </Col>
        </Row>

        {/* Status indicator */}
        {filters.predictionModels && filters.predictionModels.length > 0 && (
          <Row className="mt-2">
            <Col>
              <div style={{ color: '#00ff00', fontSize: '0.9em' }}>
                ✓ Active Models: {filters.predictionModels.join(', ')}
              </div>
            </Col>
          </Row>
        )}
      </Card.Body>
    </Card>
  );
};

export default Filters;