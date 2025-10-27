import React from 'react';
import { Card } from 'react-bootstrap';

const StatsCard = ({ label, value, unit = '', colorClass = '', isMobile = false, title, color, suffix = '' }) => {
  // Support both old and new prop names for backward compatibility
  const cardLabel = label || title;
  const cardValue = value;
  const cardUnit = unit || suffix;
  const cardColor = colorClass || color;
  
  // Determine font sizes based on screen size
  const labelSize = isMobile ? '0.75rem' : '0.9rem';
  const valueSize = isMobile ? '1.2rem' : '2rem';
  const unitSize = isMobile ? '0.8rem' : '1rem';
  
  return (
    <Card className={`stat-card ${cardColor}`} style={{ height: '100%' }}>
      <Card.Body style={{ padding: isMobile ? '10px' : '15px' }}>
        <div 
          className="stat-label" 
          style={{ 
            fontSize: labelSize,
            marginBottom: isMobile ? '4px' : '8px',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}
        >
          {cardLabel}
        </div>
        <div 
          className="stat-value" 
          style={{ 
            fontSize: valueSize,
            display: 'flex',
            alignItems: 'baseline',
            justifyContent: 'center',
            flexWrap: 'wrap'
          }}
        >
          <span>{cardValue}</span>
          {cardUnit && (
            <span 
              className="stat-unit" 
              style={{ 
                fontSize: unitSize,
                marginLeft: '4px'
              }}
            >
              {cardUnit}
            </span>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default React.memo(StatsCard);