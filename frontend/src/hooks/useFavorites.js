import { useState, useEffect, useCallback } from 'react';

export const useFavorites = () => {
  const [favorites, setFavorites] = useState([]);
  const [storageAvailable, setStorageAvailable] = useState(false);

  // Check if localStorage is available
  const checkStorage = useCallback(() => {
    try {
      const test = '__storage_test__';
      window.localStorage.setItem(test, test);
      window.localStorage.removeItem(test);
      return true;
    } catch (e) {
      console.warn('localStorage not available:', e);
      return false;
    }
  }, []);

  useEffect(() => {
    const isAvailable = checkStorage();
    setStorageAvailable(isAvailable);
    
    if (isAvailable) {
      try {
        const stored = localStorage.getItem('seaLevelFavorites');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            setFavorites(parsed);
          }
        }
      } catch (error) {
        console.error('Error loading favorites:', error);
        setFavorites([]);
      }
    }
  }, [checkStorage]);

  const addFavorite = useCallback((station) => {
    if (!station || typeof station !== 'string') {
      console.error('Invalid station provided to addFavorite');
      return false;
    }

    try {
      const updated = [...new Set([...favorites, station])];
      setFavorites(updated);
      
      if (storageAvailable) {
        localStorage.setItem('seaLevelFavorites', JSON.stringify(updated));
      }
      return true;
    } catch (error) {
      console.error('Error adding favorite:', error);
      return false;
    }
  }, [favorites, storageAvailable]);

  const removeFavorite = useCallback((station) => {
    if (!station || typeof station !== 'string') {
      console.error('Invalid station provided to removeFavorite');
      return false;
    }

    try {
      const updated = favorites.filter(f => f !== station);
      setFavorites(updated);
      
      if (storageAvailable) {
        localStorage.setItem('seaLevelFavorites', JSON.stringify(updated));
      }
      return true;
    } catch (error) {
      console.error('Error removing favorite:', error);
      return false;
    }
  }, [favorites, storageAvailable]);

  const isFavorite = useCallback((station) => {
    return favorites.includes(station);
  }, [favorites]);

  const clearFavorites = useCallback(() => {
    try {
      setFavorites([]);
      if (storageAvailable) {
        localStorage.removeItem('seaLevelFavorites');
      }
      return true;
    } catch (error) {
      console.error('Error clearing favorites:', error);
      return false;
    }
  }, [storageAvailable]);

  return { 
    favorites, 
    addFavorite, 
    removeFavorite, 
    isFavorite, 
    clearFavorites,
    storageAvailable 
  };
};