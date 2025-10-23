import React, { useState, useEffect } from 'react';
import { Badge } from 'react-bootstrap';

const WarningsCard = ({ apiBaseUrl }) => {
  const [warnings, setWarnings] = useState([]);
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
    const interval = setInterval(fetchWarnings, 15 * 60 * 1000); // 15 minutes
    return () => clearInterval(interval);
  }, [apiBaseUrl]);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'red': return 'danger';
      case 'orange': return 'warning';
      case 'yellow': return 'warning';
      default: return 'info';
    }
  };

  const formatDate = (dateStr) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return <div className="text-muted">Loading warnings...</div>;
  }

  if (warnings.length === 0) {
    return (
      <div className="text-center">
        <Badge bg="success" className="px-3 py-2">
          ✓ No Active Warnings
        </Badge>
      </div>
    );
  }

  return (
    <div>
      {warnings.map((warning, index) => (
        <div key={index} className={`mb-2 ${index > 0 ? 'pt-2 border-top' : ''}`}>
          <div className="d-flex justify-content-between align-items-start mb-1">
            <Badge bg={getSeverityColor(warning.severity)} className="me-2">
              {warning.severity.toUpperCase()}
            </Badge>
            <small className="text-muted">{formatDate(warning.pub_date)}</small>
          </div>
          <div className="small">
            <strong>{warning.title}</strong>
          </div>
          {warning.description && (
            <div className="small text-muted mt-1" 
                 dangerouslySetInnerHTML={{ 
                   __html: warning.description.replace(/<[^>]*>/g, '').substring(0, 100) + '...' 
                 }} 
            />
          )}
        </div>
      ))}
    </div>
  );
};

export default WarningsCard;