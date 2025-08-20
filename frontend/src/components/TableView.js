import React, { useState, useEffect } from 'react';
import { Table } from 'react-bootstrap';
import moment from 'moment';

const TableView = ({ filters, apiBaseUrl }) => {
  const [tableData, setTableData] = useState([]);
  const [columns, setColumns] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/data?station=${filters.station}&start_date=${moment(filters.startDate).format('YYYY-MM-DD')}&end_date=${moment(filters.endDate).format('YYYY-MM-DD')}&data_source=${filters.dataType}`
        );
        const data = await response.json();
        if (!data || data.length === 0) {
          setTableData([]);
          setColumns([{ name: 'Status', id: 'Status' }]);
          return;
        }

        const columnMapping = filters.dataType === 'tides' ? {
          "Date": "Date",
          "Station": "Station",
          "HighTide": "High Tide (m)",
          "HighTideTime": "High Tide Time",
          "HighTideTemp": "High Tide Temp (°C)",
          "LowTide": "Low Tide (m)",
          "LowTideTime": "Low Tide Time",
          "LowTideTemp": "Low Tide Temp (°C)",
          "anomaly": "Anomaly"
        } : {
          "Tab_DateTime": "Date/Time",
          "Station": "Station",
          "Tab_Value_mDepthC1": "Sea Level (m)",
          "Tab_Value_monT2m": "Water Temp (°C)"
        };

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
        {tableData.length > 0 ? tableData.map((row, index) => (
          <tr key={index}>
            {columns.map(col => (
              <td key={col.id}>{typeof row[col.id] === 'number' ? row[col.id].toFixed(3) : row[col.id]}</td>
            ))}
          </tr>
        )) : (
          <tr>
            <td colSpan={columns.length}>No data available</td>
          </tr>
        )}
      </tbody>
    </Table>
  );
};

export default TableView;