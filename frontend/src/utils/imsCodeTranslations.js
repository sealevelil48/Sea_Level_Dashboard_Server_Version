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
  
  // World Weather Codes
  1030: "Hail",
  1040: "Blizzard",
  1050: "Snow Showers",
  1090: "Heavy Showers",
  1100: "Scattered Showers",
  1110: "Isolated Showers",
  1120: "Light Showers",
  1130: "Freezing Rain",
  1150: "Drizzle",
  1170: "Mist",
  1180: "Smoke",
  1190: "Haze",
  1200: "Overcast",
  1210: "Sunny Interval",
  1240: "Bright",
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
  045: "NE",
  090: "E", 
  135: "SE",
  180: "S",
  225: "SW",
  270: "W",
  315: "NW",
  360: "N"
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
  const numDir = parseInt(direction);
  return windDirections[numDir] || direction;
};

// Parse and translate wind format: "045-135/10-25"
export const parseWindInfo = (windString) => {
  if (!windString || typeof windString !== 'string') return windString;
  
  const parts = windString.split('/');
  if (parts.length !== 2) return windString;
  
  const [directions, speeds] = parts;
  
  // Parse directions (e.g., "045-135")
  let translatedDirections = directions;
  if (directions.includes('-')) {
    const [dir1, dir2] = directions.split('-');
    const trans1 = translateWindDirection(dir1);
    const trans2 = translateWindDirection(dir2);
    translatedDirections = `${trans1}-${trans2}`;
  } else {
    translatedDirections = translateWindDirection(directions);
  }
  
  return `${translatedDirections} / ${speeds} kt`;
};

// Parse wave height format: "50 / 50-100" 
export const parseWaveHeight = (waveString) => {
  if (!waveString || typeof waveString !== 'string') return waveString;
  
  const parts = waveString.split(' / ');
  if (parts.length !== 2) {
    // Single code
    return translateSeaStateCode(waveString.trim());
  }
  
  const [code1, code2] = parts;
  const trans1 = translateSeaStateCode(code1.trim());
  const trans2 = translateSeaStateCode(code2.trim());
  
  return `${trans1} / ${trans2}`;
};