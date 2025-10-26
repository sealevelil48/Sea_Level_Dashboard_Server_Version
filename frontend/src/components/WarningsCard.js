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

  const getWarningBadge = (description) => {
    const text = description.toLowerCase();
    if (text.includes('red')) return { color: '#dc3545', text: 'RED' };
    if (text.includes('orange')) return { color: '#fd7e14', text: 'ORANGE' };
    if (text.includes('yellow')) return { color: '#ffc107', text: 'YELLOW' };
    return null;
  };

  const formatTitleWithTime = (title, pubDate) => {
    if (!pubDate) return title;
    const date = new Date(pubDate);
    const ampm = date.toLocaleTimeString('en-US', { hour12: true }).split(' ')[1];
    return `${title} ${ampm}`;
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
            minHeight: '80px', 
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
              <strong>{formatTitleWithTime(currentWarning.title, currentWarning.pub_date)}</strong>
              {currentWarning.description && (
                <div className="mt-1" style={{ fontSize: '0.8em', lineHeight: '1.2' }}>
                  {(() => {
                    const badge = getWarningBadge(currentWarning.description);
                    const cleanDescription = currentWarning.description.replace(/^(red|orange|yellow)\s+warning\s+of\s+/i, '');
                    return (
                      <>
                        {badge && (
                          <span 
                            style={{ 
                              backgroundColor: badge.color, 
                              color: 'white', 
                              padding: '2px 6px', 
                              borderRadius: '3px', 
                              fontSize: '0.7em', 
                              fontWeight: 'bold',
                              marginRight: '5px'
                            }}
                          >
                            {badge.text}
                          </span>
                        )}
                        {cleanDescription}
                      </>
                    );
                  })()
                  }
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarningsCard;