import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import moment from 'moment';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const MapView = ({ filters, apiBaseUrl }) => {
  const [mapData, setMapData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=default`
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
          last_update: latestValues[station.Station]?.Tab_DateTime ? moment(latestValues[station.Station].Tab_DateTime).format('YYYY-MM-DD HH:mm') : 'N/A'
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
    <MapContainer center={[31.5, 34.75]} zoom={6} style={{ height: '500px', width: '100%' }}>
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      {mapData.map(station => (
        <Marker key={station.Station} position={[station.latitude, station.longitude]}>
          <Popup>
            <b>{station.Station}</b><br />
            Sea Level (m): {typeof station.latest_value === 'number' ? station.latest_value.toFixed(3) : station.latest_value}<br />
            Last Update: {station.last_update}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default MapView;