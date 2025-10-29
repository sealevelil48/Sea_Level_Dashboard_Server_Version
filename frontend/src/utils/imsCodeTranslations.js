// IMS Weather and Sea State Code Translations
// Based on Israeli Meteorological Service official codes

export const weatherCodes = {
  // Israel Weather Codes
  1010: "Sandstorms",
  1020: "Thunderstorms", 
  1060: "Snow",
  1070: "Light snow",
  1080: "Sleet",
  1140: "Rainy",
  1160: "Fog",
  1220: "Partly cloudy",
  1230: "Cloudy",
  1250: "Clear",
  1260: "Windy",
  1270: "Muggy",
  1300: "Frost",
  1310: "Hot",
  1320: "Cold",
  1510: "Stormy",
  1520: "Heavy snow",
  1530: "Partly cloudy, possible rain",
  1540: "Cloudy, possible rain",
  1560: "Cloudy, light rain",
  1570: "Dust",
  1580: "Extremely hot",
  1590: "Extremely cold",
  
  // Global Weather Codes
  1030: "Hail",
  1040: "Blowing Snow, Blizzard, Snowdrift, Snowstorm",
  1050: "Snow Showers, Flurries",
  1090: "Showers, Heavy Showers",
  1100: "Occasional Showers, Scattered Showers",
  1110: "Isolated Showers",
  1120: "Light Showers",
  1130: "Freezing Rain",
  1150: "Drizzle, Light Rain",
  1170: "Mist",
  1180: "Smoke",
  1190: "Haze",
  1200: "Overcast",
  1210: "Sunny Interval, No Rain, Clearing",
  1240: "Bright, Sunny, Fair",
  1280: "Dry",
  1290: "Freezing",
  1330: "Warming",
  1340: "Cooling"
};

export const seaStateCodes = {
  10: "Calm",
  20: "Rippled", 
  30: "Smooth",
  40: "Smooth to slight",
  50: "Slight",
  55: "Slight to moderate",
  60: "Moderate",
  70: "Moderate to rough",
  80: "Rough",
  90: "Rough to very rough",
  110: "Very rough",
  120: "Very rough to high",
  130: "High",
  140: "High to very high",
  150: "Very high",
  160: "Phenomenal",
  161: "Smooth. Becoming slight.",
  162: "Smooth. Becoming slight during day time.",
  163: "Smooth. Becoming tomorrow slight to moderate.",
  164: "Smooth. Becoming slight to moderate",
  165: "Smooth to slight. Becoming moderate",
  166: "Smooth at west coast, slight at east coast",
  167: "Smooth to slight. Becoming slight to moderate.",
  168: "Slight. Becoming moderate.",
  169: "Smooth to slight. Becoming moderate to rough.",
  170: "Slight over Western bank, moderate over Eastern bank.",
  171: "Slight to moderate. Becoming moderate to rough"
};

export const windDirections = {
  "000": "Northerly",
  "045": "North Easterly",
  "090": "Easterly", 
  "135": "South Easterly",
  "180": "Southerly",
  "225": "South Westerly",
  "270": "Westerly",
  "315": "North Westerly",
  "360": "Northerly"
};

// Helper functions to translate codes
export const translateWeatherCode = (code) => {
  const numCode = parseInt(code);
  return weatherCodes[numCode] || code;
};

export const translateSeaStateCode = (code) => {
  const numCode = parseInt(code);
  return seaStateCodes[numCode] || code;
};

export const translateWindDirection = (direction) => {
  const dirStr = String(direction).padStart(3, '0');
  return windDirections[dirStr] || direction;
};

// Parse and translate wind format: "045-135/10-25"
// First part (045-135) are IMS wind direction codes, second part (10-25) is actual wind speed in kph
export const parseWindInfo = (windString) => {
  if (!windString || typeof windString !== 'string') return windString;
  
  const parts = windString.split('/');
  if (parts.length !== 2) return windString;
  
  const [directions, speeds] = parts;
  
  // Parse directions (e.g., "045-135")
  let translatedDirections = directions;
  if (directions.includes('-')) {
    const [dir1, dir2] = directions.split('-');
    const trans1 = translateWindDirection(dir1.padStart(3, '0'));
    const trans2 = translateWindDirection(dir2.padStart(3, '0'));
    translatedDirections = `${trans1}-${trans2}`;
  } else {
    translatedDirections = translateWindDirection(directions.padStart(3, '0'));
  }
  
  return `${translatedDirections} (${speeds.trim()} km/h)`;
};

// Parse wave height format: "50 / 50-100" 
// First part (50) is IMS sea state code, second part (50-100) is actual wave height in cm
export const parseWaveHeight = (waveString) => {
  if (!waveString || typeof waveString !== 'string') return waveString;
  
  const parts = waveString.split(' / ');
  if (parts.length !== 2) {
    // Single code - translate it
    return translateSeaStateCode(waveString.trim());
  }
  
  const [code, actualHeight] = parts;
  const translatedCode = translateSeaStateCode(code.trim());
  
  return `${translatedCode} (${actualHeight.trim()} cm)`;
};

// Get weather risk color based on sea state code
export const getWaveRiskColor = (waveString) => {
  if (!waveString) return 'secondary';
  
  const code = parseInt(waveString.split(' / ')[0] || waveString);
  
  if (code >= 80) return 'danger';     // Severe Risk - red
  if (code >= 60) return 'warning';    // Significant Risk - orange  
  if (code >= 40) return 'warning';    // Risk - yellow
  return 'secondary';                  // No significant weather - grey
};

// Get wind risk color based on wind speed
export const getWindRiskColor = (windString) => {
  if (!windString) return 'secondary';
  
  const speedPart = windString.split('/')[1];
  if (!speedPart) return 'secondary';
  
  const maxSpeed = Math.max(...speedPart.split('-').map(s => parseInt(s.trim())));
  
  if (maxSpeed >= 40) return 'danger';     // Severe Risk - red
  if (maxSpeed >= 25) return 'warning';    // Significant Risk - orange
  if (maxSpeed >= 15) return 'warning';    // Risk - yellow  
  return 'secondary';                      // No significant weather - grey
};

// Add pressure unit (hPa)
export const formatPressure = (pressure) => {
  if (!pressure) return pressure;
  return `${pressure} hPa`;
};

// Add visibility unit (nm - nautical miles)
export const formatVisibility = (visibility) => {
  if (!visibility) return visibility;
  return `${visibility} nm`;
};

// Parse swell format - can contain wind direction codes or sea state codes
export const parseSwellInfo = (swellString) => {
  if (!swellString || typeof swellString !== 'string') return swellString;
  
  const parts = swellString.split(' / ');
  if (parts.length !== 2) {
    // Single code - check if it's a wind direction or sea state code
    const code = swellString.trim();
    const windDir = translateWindDirection(code.padStart(3, '0'));
    if (windDir !== code) {
      return windDir; // It's a wind direction code
    }
    return translateSeaStateCode(code); // Try as sea state code
  }
  
  const [code, actualHeight] = parts;
  const codeStr = code.trim();
  
  // Check if first part is wind direction code
  const windDir = translateWindDirection(codeStr.padStart(3, '0'));
  if (windDir !== codeStr) {
    return `${windDir} (${actualHeight.trim()} cm)`;
  }
  
  // Otherwise treat as sea state code
  const translatedCode = translateSeaStateCode(codeStr);
  return `${translatedCode} (${actualHeight.trim()} cm)`;
};