import React, { useEffect, useRef, useState } from 'react';
import moment from 'moment';
import LeafletFallback from './LeafletFallback';

const GovMapView = ({ filters, apiBaseUrl }) => {
  const iframeRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [mapData, setMapData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=default`
        );
        const data = await response.json();

        const stationsResponse = await fetch(`${apiBaseUrl}/stations/map?end_date=${moment(filters.endDate).format('YYYY-MM-DD')}`);
        const stationsData = await stationsResponse.json();

        setMapData(stationsData);
        
        // Send date update message to iframe with delay
        if (iframeRef.current && iframeRef.current.contentWindow) {
          const endDate = moment(filters.endDate).format('YYYY-MM-DD');
          console.log('Sending date update to iframe:', endDate);
          setTimeout(() => {
            iframeRef.current.contentWindow.postMessage(
              { type: 'UPDATE_DATE', payload: endDate },
              '*'
            );
          }, 500);
        }
      } catch (error) {
        console.error('Error fetching map data:', error);
        setError('Failed to fetch station data');
      }
    };

    fetchData();
  }, [filters, apiBaseUrl]);

  useEffect(() => {
    const iframe = iframeRef.current;
    if (!iframe) return;

    const handleIframeLoad = () => {
      setLoading(false);
      
      // Send station data to iframe after it loads
      if (mapData.length > 0) {
        setTimeout(() => {
          try {
            iframe.contentWindow.postMessage({
              type: 'UPDATE_STATIONS',
              stations: mapData
            }, '*');
          } catch (err) {
            console.warn('Failed to send data to iframe:', err);
          }
        }, 1000);
      }
    };

    const handleIframeError = () => {
      setError('Failed to load GovMap');
      setLoading(false);
    };

    iframe.addEventListener('load', handleIframeLoad);
    iframe.addEventListener('error', handleIframeError);

    return () => {
      iframe.removeEventListener('load', handleIframeLoad);
      iframe.removeEventListener('error', handleIframeError);
    };
  }, [mapData]);

  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '500px', 
        background: '#f8f9fa',
        border: '1px solid #dee2e6',
        borderRadius: '4px'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div>Loading GovMap...</div>
          <div style={{ fontSize: '12px', color: '#6c757d', marginTop: '5px' }}>
            Initializing Israeli Government Map
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    console.warn('GovMap failed, falling back to Leaflet:', error);
    return (
      <div>
        <div style={{ 
          background: '#fff3cd',
          border: '1px solid #ffeaa7',
          borderRadius: '4px',
          padding: '8px',
          marginBottom: '10px',
          fontSize: '14px',
          color: '#856404'
        }}>
          ⚠️ GovMap unavailable - using OpenStreetMap fallback
        </div>
        <LeafletFallback filters={filters} apiBaseUrl={apiBaseUrl} />
      </div>
    );
  }

  return (
    <iframe
      ref={iframeRef}
      key={moment(filters.endDate).format('YYYY-MM-DD')}
      src={`${apiBaseUrl}/mapframe?end_date=${moment(filters.endDate).format('YYYY-MM-DD')}`}
      style={{ 
        width: '100%', 
        height: '500px',
        border: '1px solid #dee2e6',
        borderRadius: '4px'
      }}
      title="GovMap - Sea Level Stations"
    />
  );
};

export default GovMapView;