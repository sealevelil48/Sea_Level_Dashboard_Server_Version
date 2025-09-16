import React, { useState, useCallback, useMemo } from "react";
import { format, addMonths, subMonths, startOfMonth, endOfMonth, eachDayOfInterval, isWithinInterval, isSameDay, addDays, subDays } from "date-fns";

const DateRangePicker = ({ startDate, endDate, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [tempStartDate, setTempStartDate] = useState(startDate);
  const [tempEndDate, setTempEndDate] = useState(endDate);
  const [currentMonth, setCurrentMonth] = useState(startDate);
  const [selecting, setSelecting] = useState(false);
  const [showMonthPicker, setShowMonthPicker] = useState(false);
  const [showYearPicker, setShowYearPicker] = useState(false);

  const presetRanges = [
    { label: "Today", getValue: () => [new Date(), new Date()] },
    { label: "Yesterday", getValue: () => [subDays(new Date(), 1), subDays(new Date(), 1)] },
    { label: "Last 7 Days", getValue: () => [subDays(new Date(), 6), new Date()] },
    { label: "Last 30 Days", getValue: () => [subDays(new Date(), 29), new Date()] },
    { label: "This Month", getValue: () => [startOfMonth(new Date()), new Date()] },
    { label: "Last Month", getValue: () => [startOfMonth(subMonths(new Date(), 1)), endOfMonth(subMonths(new Date(), 1))] }
  ];

  const daysInMonth = useMemo(() => {
    const start = startOfMonth(currentMonth);
    const end = endOfMonth(currentMonth);
    const firstDay = start.getDay();
    const daysArray = [];
    
    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      daysArray.push(new Date(start.getTime() - (firstDay - i) * 24 * 60 * 60 * 1000));
    }
    
    // Add all days of the month
    const monthDays = eachDayOfInterval({ start, end });
    daysArray.push(...monthDays);
    
    return daysArray;
  }, [currentMonth]);

  const handlePresetSelect = useCallback((getValue) => {
    const [start, end] = getValue();
    setTempStartDate(start);
    setTempEndDate(end);
    setCurrentMonth(start);
  }, []);

  const handleDateSelect = useCallback((date) => {
    if (!selecting) {
      setTempStartDate(date);
      setTempEndDate(date);
      setSelecting(true);
    } else {
      if (date < tempStartDate) {
        setTempStartDate(date);
        setTempEndDate(tempStartDate);
      } else {
        setTempEndDate(date);
      }
      setSelecting(false);
    }
  }, [selecting, tempStartDate]);

  const isDateInRange = useCallback((date) => {
    return isWithinInterval(date, { start: tempStartDate, end: tempEndDate });
  }, [tempStartDate, tempEndDate]);

  const isDateSelected = useCallback((date) => {
    return isSameDay(date, tempStartDate) || isSameDay(date, tempEndDate);
  }, [tempStartDate, tempEndDate]);

  const nextMonth = () => setCurrentMonth(addMonths(currentMonth, 1));
  const prevMonth = () => setCurrentMonth(subMonths(currentMonth, 1));

  const months = useMemo(() => [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
  ], []);

  const years = useMemo(() => {
    const currentYear = new Date().getFullYear();
    return Array.from({length: 10}, (_, i) => currentYear - 5 + i);
  }, []);

  const handleApply = () => {
    onChange(tempStartDate, tempEndDate);
    setIsOpen(false);
  };

  const handleCancel = () => {
    setTempStartDate(startDate);
    setTempEndDate(endDate);
    setIsOpen(false);
  };

  return (
    <div className="position-relative">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="form-select d-flex align-items-center"
        style={{ cursor: 'pointer', backgroundColor: 'var(--bs-body-bg)', color: 'var(--bs-body-color)' }}
      >
        <span className="flex-grow-1">
          {format(startDate, "MMM dd, yyyy")} - {format(endDate, "MMM dd, yyyy")}
        </span>
      </div>

      {isOpen && (
        <div className="position-absolute bg-white border rounded shadow-lg p-2" 
             style={{ 
               top: '100%', 
               left: 0, 
               right: 0,
               zIndex: 1050, 
               marginTop: '5px',
               maxHeight: '400px',
               overflowY: 'auto'
             }}>
          <div className="row g-2">
            <div className="col-12 col-md-5 border-end pe-2">
              <h6 className="mb-2 small">Quick Select</h6>
              <div className="d-grid gap-1">
                {presetRanges.map((range) => (
                  <button
                    key={range.label}
                    onClick={() => handlePresetSelect(range.getValue)}
                    className="btn btn-sm btn-outline-secondary text-start py-1"
                    style={{ fontSize: '0.75rem' }}
                  >
                    {range.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="col-12 col-md-7">
              <div className="d-flex justify-content-between align-items-center mb-2 position-relative">
                <button onClick={prevMonth} className="btn btn-sm btn-outline-secondary px-2 py-1">
                  ‹
                </button>
                <div className="d-flex gap-1">
                  <button
                    onClick={() => setShowMonthPicker(!showMonthPicker)}
                    className="btn btn-sm btn-outline-secondary px-2 py-1"
                    style={{ fontSize: '0.75rem' }}
                  >
                    {format(currentMonth, "MMM")} ▼
                  </button>
                  <button
                    onClick={() => setShowYearPicker(!showYearPicker)}
                    className="btn btn-sm btn-outline-secondary px-2 py-1"
                    style={{ fontSize: '0.75rem' }}
                  >
                    {format(currentMonth, "yyyy")} ▼
                  </button>
                </div>
                <button onClick={nextMonth} className="btn btn-sm btn-outline-secondary px-2 py-1">
                  ›
                </button>

                {showMonthPicker && (
                  <div className="position-absolute bg-white border rounded shadow p-1" 
                       style={{ top: '100%', left: '50%', transform: 'translateX(-50%)', zIndex: 1051, width: '180px' }}>
                    <div className="row g-1">
                      {months.map((month, index) => (
                        <div key={month} className="col-4">
                          <button
                            onClick={() => {
                              setCurrentMonth(new Date(currentMonth.getFullYear(), index));
                              setShowMonthPicker(false);
                            }}
                            className="btn btn-sm btn-outline-secondary w-100 py-1"
                            style={{ fontSize: '0.65rem' }}
                          >
                            {month.slice(0, 3)}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {showYearPicker && (
                  <div className="position-absolute bg-white border rounded shadow p-1" 
                       style={{ top: '100%', left: '50%', transform: 'translateX(-50%)', zIndex: 1051, width: '150px' }}>
                    <div className="row g-1">
                      {years.map((year) => (
                        <div key={year} className="col-4">
                          <button
                            onClick={() => {
                              setCurrentMonth(new Date(year, currentMonth.getMonth()));
                              setShowYearPicker(false);
                            }}
                            className="btn btn-sm btn-outline-secondary py-1"
                            style={{ fontSize: '0.7rem' }}
                          >
                            {year}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="row g-0 mb-1">
                {["S", "M", "T", "W", "T", "F", "S"].map((day, i) => (
                  <div key={i} className="col text-center">
                    <small className="text-muted fw-bold" style={{ fontSize: '0.65rem' }}>{day}</small>
                  </div>
                ))}
              </div>

              <div className="row g-0">
                {daysInMonth.map((date) => {
                  const isCurrentMonth = date.getMonth() === currentMonth.getMonth();
                  return (
                    <div key={date.toString()} className="col p-0">
                      <button
                        onClick={() => handleDateSelect(date)}
                        className={`btn btn-sm w-100 ${
                          isDateSelected(date) ? "btn-primary" : 
                          isDateInRange(date) ? "btn-light" : 
                          "btn-outline-light"
                        }`}
                        style={{ 
                          opacity: isCurrentMonth ? 1 : 0.3,
                          fontSize: '0.65rem',
                          padding: '1px',
                          height: '24px'
                        }}
                      >
                        {format(date, "d")}
                      </button>
                    </div>
                  );
                })}
              </div>

              <div className="d-flex justify-content-end gap-1 mt-2">
                <button onClick={handleCancel} className="btn btn-sm btn-secondary px-2 py-1">
                  Cancel
                </button>
                <button onClick={handleApply} className="btn btn-sm btn-primary px-2 py-1">
                  Apply
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DateRangePicker;