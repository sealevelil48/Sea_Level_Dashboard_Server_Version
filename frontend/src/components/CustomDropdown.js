import React, { useState } from 'react';
import './CustomDropdown.css';

const CustomDropdown = ({ value, onChange, options, label }) => {
  const [isOpen, setIsOpen] = useState(false);

  const handleSelect = (optionValue) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const selectedOption = options.find(opt => opt.value === value) || options[0];

  return (
    <div className={`custom-select ${isOpen ? 'open' : ''}`}>
      <div 
        className="custom-selected" 
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{selectedOption.label}</span>
        <svg className="custom-arrow" viewBox="0 0 24 24">
          <path d="M7 10l5 5 5-5z"/>
        </svg>
      </div>
      {isOpen && (
        <div className="custom-options">
          {options.map((option) => (
            <div
              key={option.value}
              className={`custom-option ${value === option.value ? 'selected' : ''}`}
              onClick={() => handleSelect(option.value)}
            >
              {option.label}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CustomDropdown;