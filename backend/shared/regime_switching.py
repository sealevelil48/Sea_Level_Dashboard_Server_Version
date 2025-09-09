"""
Regime-Switching Kalman Filter for Storm Surge Detection
Implements Hidden Markov Model combined with multiple Kalman filters
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from scipy import stats
from hmmlearn import hmm
import pickle

logger = logging.getLogger(__name__)

class SeaLevelRegime(Enum):
    """Sea level regimes"""
    CALM = 0
    MODERATE = 1
    SURGE = 2
    STORM = 3

@dataclass
class RegimeConfig:
    """Configuration for each regime"""
    name: str
    regime: SeaLevelRegime
    process_noise: float
    measurement_noise: float
    trend_variance: float
    surge_threshold: float
    
class RegimeSwitchingKalman:
    """
    Switching Kalman filter that adapts to different sea level regimes
    Combines HMM for regime detection with regime-specific Kalman filters
    """
    
    def __init__(self):
        self.hmm_model = None
        self.kalman_filters = {}
        self.current_regime = SeaLevelRegime.CALM
        self.regime_history = []
        self.regime_probabilities = []
        
        # Define regime configurations
        self.regime_configs = {
            SeaLevelRegime.CALM: RegimeConfig(
                name="Calm",
                regime=SeaLevelRegime.CALM,
                process_noise=0.001,
                measurement_noise=0.01,
                trend_variance=0.0001,
                surge_threshold=0.1
            ),
            SeaLevelRegime.MODERATE: RegimeConfig(
                name="Moderate",
                regime=SeaLevelRegime.MODERATE,
                process_noise=0.01,
                measurement_noise=0.02,
                trend_variance=0.001,
                surge_threshold=0.3
            ),
            SeaLevelRegime.SURGE: RegimeConfig(
                name="Surge",
                regime=SeaLevelRegime.SURGE,
                process_noise=0.05,
                measurement_noise=0.05,
                trend_variance=0.01,
                surge_threshold=0.5
            ),
            SeaLevelRegime.STORM: RegimeConfig(
                name="Storm",
                regime=SeaLevelRegime.STORM,
                process_noise=0.1,
                measurement_noise=0.1,
                trend_variance=0.05,
                surge_threshold=1.0
            )
        }
    
    def extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Extract features for regime detection
        
        Args:
            df: DataFrame with sea level data
            
        Returns:
            Feature matrix for HMM
        """
        features = []
        
        # Calculate rolling statistics
        window = 12  # 12 hours
        
        # Level change rate
        df['level_change'] = df['Tab_Value_mDepthC1'].diff()
        
        # Rolling variance (volatility)
        df['rolling_var'] = df['Tab_Value_mDepthC1'].rolling(window).var()
        
        # Rolling mean
        df['rolling_mean'] = df['Tab_Value_mDepthC1'].rolling(window).mean()
        
        # Deviation from rolling mean
        df['deviation'] = np.abs(df['Tab_Value_mDepthC1'] - df['rolling_mean'])
        
        # Rate of change acceleration
        df['acceleration'] = df['level_change'].diff()
        
        # Build feature matrix
        feature_cols = ['level_change', 'rolling_var', 'deviation', 'acceleration']
        features = df[feature_cols].fillna(0).values
        
        return features
    
    def train_hmm(self, df: pd.DataFrame):
        """
        Train Hidden Markov Model for regime detection
        
        Args:
            df: Historical sea level data
        """
        try:
            # Extract features
            features = self.extract_features(df)
            
            # Initialize HMM with 4 states (regimes)
            self.hmm_model = hmm.GaussianHMM(
                n_components=4,
                covariance_type="diag",
                n_iter=100,
                random_state=42
            )
            
            # Train the model
            self.hmm_model.fit(features)
            
            # Set transition matrix to favor staying in current regime
            # but allow transitions during extreme events
            self.hmm_model.transmat_ = np.array([
                [0.95, 0.04, 0.01, 0.00],  # Calm -> others
                [0.10, 0.80, 0.09, 0.01],  # Moderate -> others
                [0.05, 0.15, 0.70, 0.10],  # Surge -> others
                [0.02, 0.08, 0.20, 0.70]   # Storm -> others
            ])
            
            logger.info("HMM trained successfully for regime detection")
            
        except Exception as e:
            logger.error(f"Error training HMM: {e}")
            raise
    
    def detect_regime(self, features: np.ndarray) -> Tuple[SeaLevelRegime, np.ndarray]:
        """
        Detect current regime using HMM
        
        Args:
            features: Current feature vector
            
        Returns:
            Detected regime and probability distribution
        """
        if self.hmm_model is None:
            return SeaLevelRegime.CALM, np.array([1.0, 0.0, 0.0, 0.0])
        
        try:
            # Predict regime
            regime_idx = self.hmm_model.predict(features.reshape(1, -1))[0]
            
            # Get regime probabilities
            log_prob, posteriors = self.hmm_model.score_samples(features.reshape(1, -1))
            regime_probs = posteriors[0]
            
            # Map to regime enum
            regime = SeaLevelRegime(regime_idx)
            
            return regime, regime_probs
            
        except Exception as e:
            logger.error(f"Error detecting regime: {e}")
            return SeaLevelRegime.CALM, np.array([1.0, 0.0, 0.0, 0.0])
    
    def initialize_kalman_filters(self, data: pd.DataFrame):
        """
        Initialize regime-specific Kalman filters
        
        Args:
            data: Training data
        """
        from shared.kalman_filter import KalmanFilterSeaLevel, KalmanConfig
        
        for regime, config in self.regime_configs.items():
            # Create custom config for each regime
            kalman_config = KalmanConfig(
                use_level=True,
                use_trend=True,
                use_seasonal=True,
                tidal_periods=[12.42, 12.00, 24.07, 25.82]
            )
            
            # Initialize filter
            kf = KalmanFilterSeaLevel(kalman_config)
            
            # Fit with regime-specific parameters
            # In production, adjust Q and R matrices based on regime
            kf.fit(data)
            
            self.kalman_filters[regime] = kf
            
        logger.info(f"Initialized {len(self.kalman_filters)} regime-specific Kalman filters")
    
    def predict(self, df: pd.DataFrame, steps: int = 240, 
                exog: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Generate predictions using regime-switching approach
        
        Args:
            df: Historical data
            steps: Forecast horizon
            exog: Exogenous variables (pressure, wind)
            
        Returns:
            DataFrame with predictions and regime probabilities
        """
        # Extract current features
        features = self.extract_features(df)
        current_features = features[-1:] if len(features) > 0 else features
        
        # Detect current regime
        current_regime, regime_probs = self.detect_regime(current_features)
        
        # Store regime info
        self.current_regime = current_regime
        self.regime_probabilities.append(regime_probs)
        self.regime_history.append(current_regime)
        
        # Get predictions from all regime filters
        predictions = {}
        for regime, kf in self.kalman_filters.items():
            try:
                regime_forecast = kf.forecast(steps=steps, exog_future=exog)
                predictions[regime] = regime_forecast
            except Exception as e:
                logger.error(f"Error in {regime.name} forecast: {e}")
                continue
        
        # Weighted average based on regime probabilities
        if predictions:
            # Initialize result
            weighted_forecast = None
            
            for i, (regime, forecast) in enumerate(predictions.items()):
                weight = regime_probs[regime.value]
                
                if weighted_forecast is None:
                    weighted_forecast = forecast.copy()
                    weighted_forecast['yhat'] *= weight
                    if 'yhat_lower' in weighted_forecast.columns:
                        weighted_forecast['yhat_lower'] *= weight
                        weighted_forecast['yhat_upper'] *= weight
                else:
                    weighted_forecast['yhat'] += forecast['yhat'] * weight
                    if 'yhat_lower' in forecast.columns:
                        weighted_forecast['yhat_lower'] += forecast['yhat_lower'] * weight
                        weighted_forecast['yhat_upper'] += forecast['yhat_upper'] * weight
            
            # Add regime information
            weighted_forecast['regime'] = current_regime.name
            weighted_forecast['regime_probability'] = regime_probs[current_regime.value]
            
            # Add surge warning if in surge/storm regime
            if current_regime in [SeaLevelRegime.SURGE, SeaLevelRegime.STORM]:
                weighted_forecast['surge_warning'] = True
                weighted_forecast['surge_level'] = self.regime_configs[current_regime].surge_threshold
            else:
                weighted_forecast['surge_warning'] = False
                weighted_forecast['surge_level'] = 0.0
            
            return weighted_forecast
        
        return pd.DataFrame()
    
    def get_regime_analysis(self) -> Dict:
        """
        Get comprehensive regime analysis
        
        Returns:
            Dictionary with regime statistics and warnings
        """
        if not self.regime_history:
            return {
                'current_regime': 'Unknown',
                'regime_probability': 0.0,
                'surge_risk': 'Low',
                'warnings': []
            }
        
        current_regime = self.regime_history[-1]
        current_probs = self.regime_probabilities[-1] if self.regime_probabilities else [0.25] * 4
        
        # Calculate surge risk
        surge_risk = 'Low'
        warnings = []
        
        surge_prob = current_probs[SeaLevelRegime.SURGE.value] + current_probs[SeaLevelRegime.STORM.value]
        
        if surge_prob > 0.7:
            surge_risk = 'High'
            warnings.append('HIGH SURGE RISK: Storm surge highly likely')
        elif surge_prob > 0.4:
            surge_risk = 'Moderate'
            warnings.append('MODERATE SURGE RISK: Elevated sea levels possible')
        elif surge_prob > 0.2:
            surge_risk = 'Low-Moderate'
            warnings.append('Monitor conditions: Surge risk increasing')
        
        # Check regime transitions
        if len(self.regime_history) >= 3:
            recent_regimes = self.regime_history[-3:]
            if SeaLevelRegime.CALM in recent_regimes and SeaLevelRegime.SURGE in recent_regimes:
                warnings.append('RAPID TRANSITION: Conditions deteriorating quickly')
        
        return {
            'current_regime': current_regime.name,
            'regime_probability': float(current_probs[current_regime.value]),
            'regime_distribution': {
                'calm': float(current_probs[0]),
                'moderate': float(current_probs[1]),
                'surge': float(current_probs[2]),
                'storm': float(current_probs[3])
            },
            'surge_risk': surge_risk,
            'surge_probability': float(surge_prob),
            'warnings': warnings,
            'regime_history': [r.name for r in self.regime_history[-24:]]  # Last 24 hours
        }
    
    def save_model(self, filepath: str):
        """Save trained model to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'hmm_model': self.hmm_model,
                'regime_configs': self.regime_configs,
                'regime_history': self.regime_history
            }, f)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained model from file"""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
            self.hmm_model = data['hmm_model']
            self.regime_configs = data['regime_configs']
            self.regime_history = data.get('regime_history', [])
        logger.info(f"Model loaded from {filepath}")