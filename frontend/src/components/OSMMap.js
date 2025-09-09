// frontend/src/components/OSMMap.js - Fixed version with proper centering
import React, { useEffect, useRef, useState } from 'react';
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
  const [isVisible, setIsVisible] = useState(false);

  // Station coordinates (Israel)
  const stationCoordinates = {
    'Acre': [32.9269, 35.0818],
    'Ashdod': [31.8044, 34.6553],
    'Ashkelon': [31.6658, 34.5664],
    'Eilat': [29.5581, 34.9482],
    'Haifa': [32.8191, 34.9983],
    'Yafo': [32.0535, 34.7503]
  };

  // Check visibility
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => setIsVisible(entry.isIntersecting),
      { threshold: 0.1 }
    );
    
    if (mapRef.current) {
      observer.observe(mapRef.current);
    }
    
    return () => observer.disconnect();
  }, []);

  // Initialize map when visible
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current || !isVisible) return;

    const initMap = () => {
      try {
        mapInstanceRef.current = L.map(mapRef.current, {
          center: [31.5, 34.8],
          zoom: 7,
          zoomControl: true
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 18
        }).addTo(mapInstanceRef.current);

        // Add markers with click handlers
        Object.entries(stationCoordinates).forEach(([station, coords]) => {
          const marker = L.marker(coords).addTo(mapInstanceRef.current);
          marker.bindTooltip(station);
          marker.bindPopup(`<h4>${station}</h4><p>Loading data...</p>`);
          markersRef.current[station] = marker;

          // Update popup on click
          marker.on('click', () => {
            const stationData = mapData?.filter(d => d.Station === station) || [];
            const latestData = stationData.length > 0 ? stationData[stationData.length - 1] : null;
            
            if (latestData) {
              const popupContent = `
                <div style="font-family: Arial, sans-serif; min-width: 200px;">
                  <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
                  <p><strong>Sea Level:</strong> ${latestData.Tab_Value_mDepthC1?.toFixed(3) || 'N/A'} m</p>
                  <p><strong>Temperature:</strong> ${latestData.Tab_Value_monT2m?.toFixed(1) || 'N/A'} °C</p>
                  <p><strong>Last Update:</strong> ${latestData.Tab_DateTime && !isNaN(new Date(latestData.Tab_DateTime)) ? new Date(latestData.Tab_DateTime).toISOString().replace('T', ' ').replace('.000Z', '') : 'N/A'}</p>
                </div>
              `;
              marker.setPopupContent(popupContent);
            }
          });
        });

        // Center map properly after everything loads
        setTimeout(() => {
          if (mapInstanceRef.current) {
            mapInstanceRef.current.invalidateSize();
            const group = new L.featureGroup(Object.values(markersRef.current));
            mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
          }
        }, 300);
        
      } catch (error) {
        console.error('Map initialization error:', error);
      }
    };

    setTimeout(initMap, 100);
  }, [isVisible]);

  // Update marker popups when data changes
  useEffect(() => {
    console.log('OSMMap useEffect triggered. mapData:', mapData?.length || 0, 'mapInstance:', !!mapInstanceRef.current);
    
    if (!mapInstanceRef.current) return;

    Object.entries(markersRef.current).forEach(([station, marker]) => {
      if (!marker) return;
      
      if (mapData && mapData.length > 0) {
        const stationData = mapData.filter(d => d.Station === station);
        const latestData = stationData.length > 0 ? stationData[stationData.length - 1] : null;
        
        if (latestData) {
          const popupContent = `
            <div style="font-family: Arial, sans-serif; min-width: 200px;">
              <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
              <p><strong>Sea Level:</strong> ${latestData.Tab_Value_mDepthC1?.toFixed(3) || 'N/A'} m</p>
              <p><strong>Temperature:</strong> ${latestData.Tab_Value_monT2m?.toFixed(1) || 'N/A'} °C</p>
              <p><strong>Last Update:</strong> ${latestData.Tab_DateTime ? new Date(latestData.Tab_DateTime).toISOString().replace('T', ' ').replace('.000Z', '') : 'N/A'}</p>
              <p><strong>Data Points:</strong> ${stationData.length}</p>
            </div>
          `;
          marker.bindPopup(popupContent);
          console.log(`Updated popup for ${station} with ${stationData.length} data points`);
        } else {
          marker.bindPopup(`<h4>${station}</h4><p>No data found for this station</p>`);
        }
      } else {
        marker.bindPopup(`<h4>${station}</h4><p>Loading data...</p>`);
      }
    });
  }, [mapData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        try {
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Map cleanup warning:', e);
        }
        mapInstanceRef.current = null;
        markersRef.current = {};
        setIsVisible(false);
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