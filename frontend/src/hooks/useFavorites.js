import { useState, useEffect } from 'react';

export const useFavorites = () => {
  const [favorites, setFavorites] = useState([]);

  useEffect(() => {
    const stored = localStorage.getItem('seaLevelFavorites');
    if (stored) {
      setFavorites(JSON.parse(stored));
    }
  }, []);

  const addFavorite = (station) => {
    const updated = [...favorites, station];
    setFavorites(updated);
    localStorage.setItem('seaLevelFavorites', JSON.stringify(updated));
  };

  const removeFavorite = (station) => {
    const updated = favorites.filter(f => f !== station);
    setFavorites(updated);
    localStorage.setItem('seaLevelFavorites', JSON.stringify(updated));
  };

  const isFavorite = (station) => favorites.includes(station);

  return { favorites, addFavorite, removeFavorite, isFavorite };
};