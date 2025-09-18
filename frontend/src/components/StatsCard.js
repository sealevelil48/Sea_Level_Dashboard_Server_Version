import React from 'react';
import { Card } from 'react-bootstrap';

const StatsCard = React.memo(({ title, value, color, suffix = '' }) => {
  return (
    <Card className={`stat-card ${color || ''}`}>
      <Card.Body className="text-center p-3">
        <div className="stat-label">{title}</div>
        <div className="stat-value">{value}{suffix}</div>
      </Card.Body>
    </Card>
  );
});

StatsCard.displayName = 'StatsCard';

export default StatsCard;