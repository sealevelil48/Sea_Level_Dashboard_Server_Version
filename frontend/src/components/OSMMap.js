// frontend/src/components/OSMMap.js - Fixed version without loops
import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png'
});

const OSMMap = ({ stations, currentStation, mapData }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});

  // Station coordinates (Israel)
  const stationCoordinates = {
    'Acre': [32.9269, 35.0818],
    'Ashdod': [31.8044, 34.6553],
    'Ashkelon': [31.6658, 34.5664],
    'Eilat': [29.5581, 34.9482],
    'Haifa': [32.8191, 34.9983],
    'Yafo': [32.0535, 34.7503]
  };

  // Initialize map once
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    try {
      mapInstanceRef.current = L.map(mapRef.current).setView([31.5, 34.8], 7);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
      }).addTo(mapInstanceRef.current);

      // Add initial markers
      Object.entries(stationCoordinates).forEach(([station, coords]) => {
        const marker = L.marker(coords).addTo(mapInstanceRef.current);
        marker.bindTooltip(station);
        markersRef.current[station] = marker;
      });
    } catch (error) {
      console.error('Map initialization error:', error);
    }
  }, []);

  // Update marker popups when data changes
  useEffect(() => {
    if (!mapInstanceRef.current || !mapData || mapData.length === 0) return;

    // Debounce updates to prevent excessive re-renders
    const timeoutId = setTimeout(() => {
      Object.entries(markersRef.current).forEach(([station, marker]) => {
        const stationData = mapData.find(d => d.Station === station);
        
        if (stationData) {
          const popupContent = `
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
              <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
              <p><strong>Sea Level:</strong> ${stationData.Tab_Value_mDepthC1?.toFixed(3) || 'N/A'} m</p>
              <p><strong>Temperature:</strong> ${stationData.Tab_Value_monT2m?.toFixed(1) || 'N/A'} °C</p>
              <p><strong>Last Update:</strong> ${stationData.Tab_DateTime ? new Date(stationData.Tab_DateTime).toLocaleString() : 'N/A'}</p>
            </div>
          `;
          marker.bindPopup(popupContent);
        } else {
          marker.bindPopup(`<h4>${station}</h4><p>No data available</p>`);
        }
      });
    }, 100);

    return () => clearTimeout(timeoutId);
  }, [mapData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        markersRef.current = {};
      }
    };
  }, []);

  return (
    <div 
      ref={mapRef} 
      style={{ 
        width: '100%', 
        height: '500px',
        borderRadius: '8px',
        border: '1px solid #2a4a8c'
      }} 
    />
  );
};

export default OSMMap;