/**
 * Safe date parsing utilities to prevent crashes
 */

export const safeParseDate = (dateStr) => {
  if (!dateStr) return null;
  
  try {
    const date = new Date(dateStr);
    return isNaN(date.getTime()) ? null : date;
  } catch {
    return null;
  }
};

export const formatDateTime = (dateStr) => {
  const date = safeParseDate(dateStr);
  if (!date) return 'Invalid Date';
  
  return date.toISOString().replace('T', ' ').replace('.000Z', '');
};

export const isValidDate = (dateStr) => {
  return safeParseDate(dateStr) !== null;
};