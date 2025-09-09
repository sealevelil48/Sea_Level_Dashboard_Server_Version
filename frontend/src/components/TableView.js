import React, { useState, useEffect, useMemo } from 'react';
import { Table } from 'react-bootstrap';

const COLUMN_MAPPINGS = {
  tides: {
    "Date": "Date",
    "Station": "Station",
    "HighTide": "High Tide (m)",
    "HighTideTime": "High Tide Time",
    "HighTideTemp": "High Tide Temp (°C)",
    "LowTide": "Low Tide (m)",
    "LowTideTime": "Low Tide Time",
    "LowTideTemp": "Low Tide Temp (°C)",
    "anomaly": "Anomaly"
  },
  default: {
    "Tab_DateTime": "Date/Time",
    "Station": "Station",
    "Tab_Value_mDepthC1": "Sea Level (m)",
    "Tab_Value_monT2m": "Water Temp (°C)"
  }
};

const NO_DATA_MESSAGE = "No data available";

const formatCellContent = (value, columnId) => {
  if (columnId === 'Tab_DateTime' || columnId === 'Date') {
    try {
      const date = new Date(value);
      return isNaN(date.getTime()) ? value : date.toLocaleString('sv-SE').replace('T', ' ');
    } catch {
      return value;
    }
  } else if (columnId === 'HighTideTime' || columnId === 'LowTideTime') {
    if (value && typeof value === 'string' && value.includes(':')) {
      const timeParts = value.split(':');
      return timeParts.length === 2 ? value + ':00' : value;
    }
    return value;
  } else if (typeof value === 'number') {
    return value.toFixed(3);
  }
  return value;
};

const TableView = ({ filters, apiBaseUrl }) => {
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const startDate = filters.startDate && !isNaN(new Date(filters.startDate)) ? new Date(filters.startDate).toISOString().split('T')[0] : new Date().toISOString().split('T')[0];
        const endDate = filters.endDate && !isNaN(new Date(filters.endDate)) ? new Date(filters.endDate).toISOString().split('T')[0] : new Date().toISOString().split('T')[0];
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${startDate}&end_date=${endDate}&data_source=${filters.dataType}`
        );
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (!data || data.length === 0) {
          setTableData([]);
          setColumns([{ name: 'Status', id: 'Status' }]);
          return;
        }

        const columnMapping = COLUMN_MAPPINGS[filters.dataType] || COLUMN_MAPPINGS.default;

        const cols = Object.keys(data[0]).map(col => ({
          name: columnMapping[col] || col,
          id: col
        }));
        setColumns(cols);
        setTableData(data);
      } catch (error) {
        console.error('Error fetching table data:', error);
        setTableData([]);
        setColumns([{ name: 'Status', id: 'Status' }]);
      }
    };

    fetchData();
  }, [filters, apiBaseUrl]);

  const formattedData = useMemo(() => {
    if (!tableData?.length || !columns?.length) return [];
    return tableData.map((row, index) => {
      if (!row) return { key: `invalid-${index}`, formatted: {} };
      const key = `${row.Station || 'unknown'}-${row.Date || row.Tab_DateTime || index}`;
      const formatted = {};
      columns.forEach(col => {
        if (col?.id) {
          formatted[col.id] = formatCellContent(row[col.id], col.id);
        }
      });
      return { key, formatted };
    });
  }, [tableData, columns]);

  return (
    <Table striped bordered hover responsive className="dash-table">
      <thead>
        <tr>
          {columns.map(col => (
            <th key={col.id}>{col.name}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {formattedData.length > 0 ? formattedData.map((row) => (
          <tr key={row.key}>
            {columns.map(col => (
              <td key={col.id}>
                {row.formatted[col.id]}
              </td>
            ))}
          </tr>
        )) : (
          <tr>
            <td colSpan={columns.length}>{NO_DATA_MESSAGE}</td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default React.memo(TableView);