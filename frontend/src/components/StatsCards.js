import React from 'react';

const StatsCards = ({ stats }) => {
  return (
    <div className="kpi-row">
      <div className="kpi-card">
        <div className="kpi-label">Current Level</div>
        <div className="kpi-value">{stats.current_level ? `${stats.current_level.toFixed(3)} m` : 'N/A'}</div>
      </div>
      <div className={`kpi-card ${stats['24h_change'] && stats['24h_change'] >= 0 ? 'green' : 'red'}`}>
        <div className="kpi-label">24h Change</div>
        <div className="kpi-value">{stats['24h_change'] ? `${stats['24h_change'].toFixed(3)} m` : 'N/A'}</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Avg. Temp</div>
        <div className="kpi-value">{stats.avg_temp ? `${stats.avg_temp.toFixed(1)}°C` : 'N/A'}</div>
      </div>
      <div className="kpi-card">
        <div className="kpi-label">Anomalies</div>
        <div className="kpi-value">{stats.anomalies !== null ? stats.anomalies : 'N/A'}</div>
      </div>
    </div>
  );
};

export default StatsCards;