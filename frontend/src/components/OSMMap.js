// frontend/src/components/OSMMap.js - Optimized version with lazy loading
import React, { useEffect, useRef, useState } from 'react';
import { parseWindInfo, parseWaveHeight } from '../utils/imsCodeTranslations';

// Lazy load Leaflet only when needed
let L = null;
let leafletLoaded = false;

const loadLeaflet = async () => {
  if (leafletLoaded) return L;
  
  try {
    const leafletModule = await import('leaflet');
    await import('leaflet/dist/leaflet.css');
    L = leafletModule.default;
    
    // Fix for default markers in React
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png'
    });
    
    leafletLoaded = true;
    return L;
  } catch (error) {
    console.error('Failed to load Leaflet:', error);
    throw error;
  }
};

const OSMMap = ({ stations, currentStation, mapData, forecastData }) => {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef({});
  const [isVisible, setIsVisible] = useState(false);
  const [windowWidth, setWindowWidth] = useState(window.innerWidth);
  const [isLoading, setIsLoading] = useState(true);

  // Track window resize for responsive map
  useEffect(() => {
    const handleResize = () => {
      setWindowWidth(window.innerWidth);
      if (mapInstanceRef.current) {
        setTimeout(() => {
          mapInstanceRef.current.invalidateSize();
        }, 100);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const isMobile = windowWidth < 768;
  const mapHeight = isMobile ? (windowWidth < 576 ? '300px' : '350px') : '500px';

  // Station coordinates (Israel)
  const stationCoordinates = {
    'Acre': [32.9269, 35.0818],
    'Ashdod': [31.8044, 34.6553],
    'Ashkelon': [31.6658, 34.5664],
    'Eilat': [29.5581, 34.9482],
    'Haifa': [32.8191, 34.9983],
    'Yafo': [32.0535, 34.7503]
  };

  // Mapping between station names and forecast location names
  const stationToForecastMapping = {
    'Acre': 'Northern Coast',
    'Yafo': 'Central Coast', 
    'Ashkelon': 'Southern Coast',
    'Eilat': 'Gulf of Eilat'
  };

  // Helper function to get forecast data for a station
  const getForecastForStation = (stationName) => {
    const forecastLocationName = stationToForecastMapping[stationName];
    if (!forecastLocationName || !forecastData?.locations) return null;
    
    return forecastData.locations.find(loc => loc.name_eng === forecastLocationName);
  };



  // Check visibility and tab changes
  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting);
        if (entry.isIntersecting && mapInstanceRef.current) {
          // Force map refresh when becoming visible
          setTimeout(() => {
            mapInstanceRef.current.invalidateSize(true);
          }, 100);
        }
      },
      { threshold: 0.1 }
    );
    
    if (mapRef.current) {
      observer.observe(mapRef.current);
    }
    
    // Listen for tab visibility changes
    const handleVisibilityChange = () => {
      if (!document.hidden && mapInstanceRef.current) {
        setTimeout(() => {
          mapInstanceRef.current.invalidateSize(true);
        }, 200);
      }
    };
    
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      observer.disconnect();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  // Initialize map when visible - with better error handling
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current || !isVisible) return;
    
    // Prevent double initialization
    if (mapRef.current.dataset.initializing === 'true') return;
    mapRef.current.dataset.initializing = 'true';

    const initMap = async () => {
      try {
        // Double-check element still exists and is visible
        if (!mapRef.current || !isVisible) {
          console.log('OSM map element no longer available, skipping initialization');
          setIsLoading(false);
          return;
        }

        console.log('Loading Leaflet and initializing OSM map...');
        const LeafletLib = await loadLeaflet();
        
        if (!mapRef.current || !isVisible) {
          console.log('OSM map element no longer available after Leaflet load');
          setIsLoading(false);
          return;
        }

        mapInstanceRef.current = LeafletLib.map(mapRef.current, {
          center: [31.5, 34.8],
          zoom: 7,
          zoomControl: true,
          preferCanvas: true
        });
        
        LeafletLib.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap contributors',
          maxZoom: 18
        }).addTo(mapInstanceRef.current);
        
        console.log('OSM map initialized successfully');
        setIsLoading(false);

        // Add station markers
        Object.entries(stationCoordinates).forEach(([station, coords]) => {
          if (!mapInstanceRef.current) return;
          const marker = LeafletLib.marker(coords).addTo(mapInstanceRef.current);
          marker.bindTooltip(station);
          marker.bindPopup(`<h4>${station}</h4><p>Loading data...</p>`);
          markersRef.current[station] = marker;
        });

        // Center map properly after everything loads
        setTimeout(() => {
          if (mapInstanceRef.current && mapRef.current) {
            mapInstanceRef.current.invalidateSize(true);
            const allMarkers = Object.values(markersRef.current).filter(m => m);
            if (allMarkers.length > 0) {
              const group = new LeafletLib.featureGroup(allMarkers);
              mapInstanceRef.current.fitBounds(group.getBounds().pad(0.1));
            }
            if (mapRef.current) {
              mapRef.current.dataset.initializing = 'false';
            }
          }
        }, 300);
        
      } catch (error) {
        console.error('Map initialization error:', error);
        setIsLoading(false);
        if (mapRef.current) {
          mapRef.current.dataset.initializing = 'false';
        }
      }
    };

    // Delay initialization to ensure DOM is ready
    const timeoutId = setTimeout(() => {
      initMap().catch(error => {
        console.error('Failed to initialize map:', error);
        setIsLoading(false);
      });
    }, 200);
    return () => clearTimeout(timeoutId);
  }, [isVisible]);

  // Add Sea of Galilee marker when forecast data changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!mapInstanceRef.current || !forecastData?.locations) return;
      
      // Remove existing Sea of Galilee marker
      if (markersRef.current['forecast_sea_of_galilee']) {
        try {
          mapInstanceRef.current.removeLayer(markersRef.current['forecast_sea_of_galilee']);
        } catch (e) {
          console.warn('Error removing Sea of Galilee marker:', e);
        }
        delete markersRef.current['forecast_sea_of_galilee'];
      }
      
      // Find Sea of Galilee forecast data
      const seaOfGalilee = forecastData.locations.find(loc => loc.name_eng === 'Sea of Galilee');
      if (!seaOfGalilee || !leafletLoaded) return;
      
      const coords = [seaOfGalilee.coordinates.lat, seaOfGalilee.coordinates.lng];
      const marker = L.marker(coords).addTo(mapInstanceRef.current);
      
      const currentForecast = seaOfGalilee.forecasts[0];
      const waveHeight = currentForecast?.elements?.wave_height ? parseWaveHeight(currentForecast.elements.wave_height) : 'N/A';
      const windInfo = currentForecast?.elements?.wind ? parseWindInfo(currentForecast.elements.wind) : 'N/A';
      
      const popupContent = `
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
          <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${seaOfGalilee.name_eng}</h4>
          <p><strong>Wave Height:</strong> ${waveHeight}</p>
          <p><strong>Sea Temperature:</strong> ${currentForecast?.elements?.sea_temperature || 'N/A'}°C</p>
          <p><strong>Wind:</strong> ${windInfo}</p>
          <p><strong>Forecast Period:</strong><br/>${currentForecast?.period?.start || 'N/A'} - ${currentForecast?.period?.end || 'N/A'}</p>
          <p style="font-size: 11px; color: #888;">
            <a href="https://ims.gov.il/he/coasts" target="_blank" rel="noopener noreferrer" style="color: #666; text-decoration: none;">IMS Forecast ©</a>
          </p>
        </div>
      `;
      
      marker.bindPopup(popupContent);
      marker.bindTooltip('Sea of Galilee');
      markersRef.current['forecast_sea_of_galilee'] = marker;
    }, 500);
    
    return () => clearTimeout(timer);
  }, [forecastData]);

  // Fetch station map data for OpenStreetMap
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    
    const fetchStationMapData = async () => {
      try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://127.0.0.1:30886'}/api/stations/map?end_date=${today}`);
        const stationMapData = await response.json();
        
        if (Array.isArray(stationMapData) && stationMapData.length > 0) {
          // Update markers with fetched data
          updateMarkersWithData(stationMapData);
        }
      } catch (error) {
        console.warn('Failed to fetch station map data for OSM:', error);
      }
    };
    
    fetchStationMapData();
  }, [mapInstanceRef.current]);

  // Function to update markers with station data
  const updateMarkersWithData = (stationMapData) => {
    Object.entries(markersRef.current).forEach(([station, marker]) => {
      if (!marker || station.startsWith('forecast_')) return;
      
      const stationData = stationMapData.find(d => d.Station === station);
      const forecastLocation = getForecastForStation(station);
      
      let popupContent = '<div style="font-family: Arial, sans-serif; min-width: 200px;">';
      
      // Add sea level data first
      if (stationData) {
        popupContent += `
            <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
            <p><strong>Sea Level:</strong> ${stationData.latest_value} m</p>
            <p><strong>Temperature:</strong> ${stationData.temperature || 'N/A'}°C</p>
            <p><strong>Last Update:</strong> ${stationData.last_update}</p>
            <p style="font-size: 11px; color: #888;">
            <a href="https://www.gov.il/he/departments/survey_of_israel/govil-landing-page" target="_blank" rel="noopener noreferrer" style="color: #666; text-decoration: none;">© 2025 Survey of Israel. All rights reserved.</a>
          </p>
        `;
      } else {
        popupContent += `
            <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
            <p>Loading sea level data...</p>
        `;
      }
      
      // Add forecast data after sea level if available for combined stations
      if (forecastLocation && stationToForecastMapping[station]) {
        const currentForecast = forecastLocation.forecasts[0];
        const waveHeight = currentForecast?.elements?.wave_height ? parseWaveHeight(currentForecast.elements.wave_height) : 'N/A';
        const windInfo = currentForecast?.elements?.wind ? parseWindInfo(currentForecast.elements.wind) : 'N/A';
        
        popupContent += `
            <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
            <h4 style="margin: 0 0 10px 0; color: #ff8c00;">${forecastLocation.name_eng}</h4>
            <p><strong>Wave Height:</strong> ${waveHeight}</p>
            <p><strong>Sea Temperature:</strong> ${currentForecast?.elements?.sea_temperature || 'N/A'}°C</p>
            <p><strong>Wind:</strong> ${windInfo}</p>
            <p><strong>Forecast Period:</strong><br/>${currentForecast?.from || 'N/A'} - ${currentForecast?.to || 'N/A'}</p>
            <p style="font-size: 11px; color: #888;">
              <a href="https://ims.gov.il/he/coasts" target="_blank" rel="noopener noreferrer" style="color: #666; text-decoration: none;">IMS Forecast ©</a>
            </p>
        `;
      }
      
      popupContent += '</div>';
      marker.bindPopup(popupContent);
    });
  };

  // Update marker popups when data changes
  useEffect(() => {
    const timer = setTimeout(() => {
      if (!mapInstanceRef.current || !mapData?.length) return;

      console.log('Popup update: mapData length:', mapData?.length, 'forecast locations:', forecastData?.locations?.length);

      Object.entries(markersRef.current).forEach(([station, marker]) => {
        if (!marker || station.startsWith('forecast_')) return;
        
        const stationData = mapData.filter(d => d.Station === station);
        const latestData = stationData.length > 0 ? stationData[stationData.length - 1] : null;
        const forecastLocation = getForecastForStation(station);
        
        console.log(`Station ${station}: data=${!!latestData}, forecast=${!!forecastLocation}`);
        
        let popupContent = '<div style="font-family: Arial, sans-serif; min-width: 200px;">';
        
        // Add sea level data first
        if (latestData) {
          popupContent += `
              <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
              <p><strong>Sea Level:</strong> ${latestData.Tab_Value_mDepthC1?.toFixed(3) || 'N/A'} m</p>
              <p><strong>Temperature:</strong> ${latestData.Tab_Value_monT2m?.toFixed(1) || 'N/A'}°C</p>
              <p><strong>Last Update:</strong> ${latestData.Tab_DateTime ? new Date(latestData.Tab_DateTime).toISOString().replace('T', ' ').replace('.000Z', '') : 'N/A'}</p>
              <p style="font-size: 11px; color: #888;">
              <a href="https://www.gov.il/he/departments/survey_of_israel/govil-landing-page" target="_blank" rel="noopener noreferrer" style="color: #666; text-decoration: none;">© 2025 Survey of Israel. All rights reserved.</a>
            </p>
          `;
        } else {
          popupContent += `
              <h4 style="margin: 0 0 10px 0; color: #1e6bc4;">${station}</h4>
              <p>Loading sea level data...</p>
          `;
        }
        
        // Add forecast data after sea level if available for combined stations
        if (forecastLocation && stationToForecastMapping[station]) {
          const currentForecast = forecastLocation.forecasts[0];
          const waveHeight = currentForecast?.elements?.wave_height ? parseWaveHeight(currentForecast.elements.wave_height) : 'N/A';
          const windInfo = currentForecast?.elements?.wind ? parseWindInfo(currentForecast.elements.wind) : 'N/A';
          
          popupContent += `
              <hr style="margin: 15px 0; border: none; border-top: 1px solid #ddd;">
              <h4 style="margin: 0 0 10px 0; color: #ff8c00;">${forecastLocation.name_eng}</h4>
              <p><strong>Wave Height:</strong> ${waveHeight}</p>
              <p><strong>Sea Temperature:</strong> ${currentForecast?.elements?.sea_temperature || 'N/A'}°C</p>
              <p><strong>Wind:</strong> ${windInfo}</p>
              <p><strong>Forecast Period:</strong><br/>${currentForecast?.from || 'N/A'} - ${currentForecast?.to || 'N/A'}</p>
              <p style="font-size: 11px; color: #888;">
                <a href="https://ims.gov.il/he/coasts" target="_blank" rel="noopener noreferrer" style="color: #666; text-decoration: none;">IMS Forecast ©</a>
              </p>
          `;
        }
        
        popupContent += '</div>';
        marker.bindPopup(popupContent);
        
        // Force popup refresh
        if (marker.isPopupOpen()) {
          marker.closePopup();
          setTimeout(() => marker.openPopup(), 100);
        }
      });
    }, 2000);
    
    return () => clearTimeout(timer);
  }, [mapData, forecastData]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mapInstanceRef.current) {
        try {
          // Clear all markers first
          Object.values(markersRef.current).forEach(marker => {
            try {
              if (marker && mapInstanceRef.current) {
                mapInstanceRef.current.removeLayer(marker);
              }
            } catch (e) {
              console.warn('Error removing marker during cleanup:', e);
            }
          });
          markersRef.current = {};
          
          // Remove map
          mapInstanceRef.current.remove();
        } catch (e) {
          console.warn('Map cleanup warning:', e);
        }
        mapInstanceRef.current = null;
        setIsVisible(false);
      }
    };
  }, []);

  return (
    <div 
      ref={mapRef} 
      style={{ 
        width: '100%', 
        height: mapHeight,
        minHeight: mapHeight,
        borderRadius: '8px',
        border: '1px solid #2a4a8c',
        position: 'relative',
        zIndex: 1,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }} 
    >
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.9)',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <div style={{ marginBottom: '10px' }}>Loading OpenStreetMap...</div>
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default OSMMap;