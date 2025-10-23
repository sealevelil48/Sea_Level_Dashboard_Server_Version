import React, { useState, useEffect } from 'react';

const WarningsCard = ({ apiBaseUrl }) => {
  const [warnings, setWarnings] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchWarnings = async () => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/ims-warnings`);
        if (response.ok) {
          const data = await response.json();
          setWarnings(data.warnings || []);
        }
      } catch (error) {
        console.error('Error fetching warnings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchWarnings();
    const interval = setInterval(fetchWarnings, 15 * 60 * 1000);
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  // Cycle through warnings every 4 seconds
  useEffect(() => {
    if (warnings.length > 1) {
      const interval = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % warnings.length);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [warnings.length]);

  const getWarningColor = (severity) => {
    switch (severity) {
      case 'red': return '#dc3545';
      case 'orange': return '#fd7e14';
      case 'yellow': return '#ffc107';
      default: return '#0d6efd';
    }
  };

  if (loading) {
    return (
      <div className="stats-card h-100">
        <div className="card-body text-center p-3">
          <div className="spinner-border spinner-border-sm" role="status"></div>
        </div>
      </div>
    );
  }

  const currentWarning = warnings[currentIndex];
  const warningCount = warnings.length;
  const color = currentWarning ? getWarningColor(currentWarning.severity) : '#28a745';

  return (
    <div className="stats-card h-100" style={{ borderLeft: `4px solid ${color}` }}>
      <div className="card-body p-3">
        <h6 className="card-title mb-2" style={{ color }}>
          🚨 IMS Warnings
        </h6>
        <div className="stats-value mb-2">
          <span className="h3 mb-0" style={{ color }}>
            {warningCount}
          </span>
        </div>
        <div 
          className="warning-message" 
          style={{ 
            height: '60px', 
            overflow: 'hidden',
            transition: 'transform 0.5s ease-in-out'
          }}
        >
          {warningCount === 0 ? (
            <div className="text-success small">
              ✓ No Active Warnings
            </div>
          ) : (
            <div className="small" style={{ color }}>
              <strong>{currentWarning.title}</strong>
              <div className="text-muted mt-1">
                {new Date(currentWarning.pub_date).toLocaleDateString('en-US', {
                  month: 'short',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarningsCard;