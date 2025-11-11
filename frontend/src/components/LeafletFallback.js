import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Button, Modal } from 'react-bootstrap';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { format } from 'date-fns';
import SeaForecastView from './SeaForecastView';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const LeafletFallback = ({ filters, apiBaseUrl }) => {
  const [mapData, setMapData] = useState([]);
  const [showWaveForecast, setShowWaveForecast] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${format(filters.startDate, 'yyyy-MM-dd')}&end_date=${format(filters.endDate, 'yyyy-MM-dd')}&data_source=default`
        );
        const data = await response.json();

        const stationsResponse = await fetch(`${apiBaseUrl}/stations/map`);
        const stationsData = await stationsResponse.json();

        if (!data || !stationsData) {
          setMapData([]);
          return;
        }

        const latestValues = data.reduce((acc, item) => {
          if (!acc[item.Station] || new Date(item.Tab_DateTime) > new Date(acc[item.Station].Tab_DateTime)) {
            acc[item.Station] = item;
          }
          return acc;
        }, {});

        const mergedData = stationsData.map(station => ({
          ...station,
          latest_value: latestValues[station.Station]?.Tab_Value_mDepthC1 || 'N/A',
          last_update: latestValues[station.Station]?.Tab_DateTime ? format(new Date(latestValues[station.Station].Tab_DateTime), 'yyyy-MM-dd HH:mm') : 'N/A'
        }));

        setMapData(mergedData);
      } catch (error) {
        console.error('Error fetching map data:', error);
        setMapData([]);
      }
    };

    fetchData();
  }, [filters, apiBaseUrl]);

  if (mapData.length === 0) {
    return <div>No station location data available</div>;
  }

  return (
    <div style={{ position: 'relative' }}>
      {/* Wave Forecast Button */}
      <Button
        variant="info"
        size="sm"
        onClick={() => setShowWaveForecast(true)}
        style={{
          position: 'absolute',
          top: '10px',
          right: '10px',
          zIndex: 1000,
          backgroundColor: '#17a2b8',
          borderColor: '#17a2b8'
        }}
      >
        🌊 Wave Forecast
      </Button>

      <MapContainer center={[31.5, 34.75]} zoom={6} style={{ height: '500px', width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {mapData.map(station => (
          <Marker key={station.Station} position={[station.latitude, station.longitude]}>
            <Popup>
              <b>{station.name || station.Station}</b><br />
              Sea Level (m): {typeof station.latest_value === 'number' ? station.latest_value.toFixed(3) : station.latest_value}<br />
              Last Update: {station.last_update}
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Wave Forecast Modal */}
      <Modal 
        show={showWaveForecast} 
        onHide={() => setShowWaveForecast(false)}
        size="xl"
        centered
      >
        <Modal.Header closeButton>
          <Modal.Title>🌊 Wave Forecast</Modal.Title>
        </Modal.Header>
        <Modal.Body style={{ maxHeight: '70vh', overflowY: 'auto' }}>
          <SeaForecastView apiBaseUrl={apiBaseUrl} />
        </Modal.Body>
      </Modal>
    </div>
  );
};

export default LeafletFallback;