import React from 'react';
import GovMapView from './GovMapView';

const MapView = ({ filters, apiBaseUrl }) => {
  return <GovMapView filters={filters} apiBaseUrl={apiBaseUrl} />;
};

export default MapView;