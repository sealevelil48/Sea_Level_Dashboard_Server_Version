import React, { useState, useEffect } from 'react';

const WarningsCard = ({ apiBaseUrl }) => {
  const [warnings, setWarnings] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [isExpanded, setIsExpanded] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

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

  // Only cycle through warnings on desktop or when expanded
  useEffect(() => {
    if (warnings.length > 1 && (!isMobile || isExpanded)) {
      const interval = setInterval(() => {
        setCurrentIndex(prev => (prev + 1) % warnings.length);
      }, 4000);
      return () => clearInterval(interval);
    }
  }, [warnings.length, isMobile, isExpanded]);

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

  const getFullWarningText = (warning) => {
    return warning.description?.replace(/^(red|orange|yellow)\s+warning\s+of\s+/i, '') || warning.title || '';
  };

  const getCompactWarningText = (warning) => {
    const fullText = getFullWarningText(warning);
    return isMobile && !isExpanded ? fullText.substring(0, 35) + (fullText.length > 35 ? '...' : '') : fullText;
  };

  const handleTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const handleTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const handleTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    if (!isExpanded || warnings.length <= 1) return;
    
    const distance = touchStart - touchEnd;
    const isRightToLeftSwipe = distance > 50;
    const isLeftToRightSwipe = distance < -50;
    
    if (isRightToLeftSwipe) {
      setCurrentIndex(prev => (prev + 1) % warnings.length);
    } else if (isLeftToRightSwipe) {
      setCurrentIndex(prev => (prev - 1 + warnings.length) % warnings.length);
    }
  };

  const renderWarningWithBadge = (warning, index) => {
    const badge = getWarningBadge(warning.description);
    const displayText = getCompactWarningText(warning);
    
    return (
      <div 
        key={index}
        onClick={() => setIsExpanded(!isExpanded)}
        onTouchStart={handleTouchStart}
        onTouchMove={handleTouchMove}
        onTouchEnd={handleTouchEnd}
        style={{ 
          cursor: 'pointer',
          marginBottom: index < warnings.length - 1 ? '8px' : '0',
          padding: '2px 0',
          touchAction: isExpanded && warnings.length > 1 ? 'pan-x' : 'auto'
        }}
      >
        {badge && (
          <span 
            style={{ 
              backgroundColor: badge.color, 
              color: 'white', 
              padding: '2px 6px', 
              borderRadius: '3px', 
              fontSize: '0.7em', 
              fontWeight: 'bold',
              marginRight: '6px'
            }}
          >
            {badge.text}
          </span>
        )}
        {displayText}
      </div>
    );
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
    <div 
      className="stats-card" 
      style={{ 
        borderLeft: `4px solid ${color}`,
        minHeight: isMobile && !isExpanded ? '60px' : 'auto',
        maxHeight: isMobile && !isExpanded ? '60px' : 'none',
        overflow: 'hidden',
        transition: 'all 0.3s ease'
      }}
    >
      <div className="card-body" style={{ padding: isMobile ? '8px 12px' : '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
          <h6 className="card-title mb-0" style={{ color, fontSize: isMobile ? '0.85rem' : '1rem' }}>
            ⚠️ IMS ALERTS ({warningCount})
          </h6>
          {isMobile && isExpanded && warningCount > 1 && (
            <div style={{ fontSize: '0.7rem', color: '#4dabf5' }}>
              {currentIndex + 1}/{warningCount} • Swipe ↔️
            </div>
          )}
        </div>
        
        <div style={{ fontSize: isMobile ? '0.75rem' : '0.85rem', lineHeight: '1.4' }}>
          {warningCount === 0 ? (
            <div className="text-success">
              ✓ No Active Warnings
            </div>
          ) : isMobile && !isExpanded ? (
            <div style={{ color: 'white' }}>
              {renderWarningWithBadge(warnings[0], 0)}
            </div>
          ) : isMobile && isExpanded ? (
            <div style={{ color: 'white' }}>
              {renderWarningWithBadge(warnings[currentIndex], currentIndex)}
            </div>
          ) : (
            <div style={{ color: 'white' }}>
              {warnings.map((warning, index) => renderWarningWithBadge(warning, index))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WarningsCard;