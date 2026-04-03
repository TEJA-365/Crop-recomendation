"""
ML Model Integration Service for Django.

This module provides integration between trained ML models and Django,
allowing the recommendation service to use ML predictions.
"""

import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from django.conf import settings
import sys

logger = logging.getLogger(__name__)

# Add ml_training to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from ml_training.scripts.load_models import ModelLoader
    ML_MODELS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    ML_MODELS_AVAILABLE = False
    # Use debug level to avoid cluttering logs - this is expected if models aren't trained yet
    logger.debug(f"ML models package not available: {e}. Using rule-based recommendations.")


class MLRecommendationService:
    """Service for ML-based crop recommendations and yield predictions."""
    
    def __init__(self):
        """Initialize ML service with model loader."""
        self.model_loader = None
        self.crop_model_data = None
        self.yield_model_data = None
        self._load_models()
    
    def _load_models(self):
        """Load ML models if available."""
        if not ML_MODELS_AVAILABLE:
            logger.debug("ML models package not available. Install required packages (scikit-learn, numpy).")
            return
        
        try:
            self.model_loader = ModelLoader()
            
            # Try to load crop recommendation model
            try:
                self.crop_model_data = self.model_loader.load_crop_recommendation_model()
                logger.info("Crop recommendation ML model loaded successfully")
            except FileNotFoundError:
                logger.debug("Crop recommendation model not found. Train models first or use rule-based fallback.")
                self.crop_model_data = None
            except Exception as e:
                logger.debug(f"Error loading crop recommendation model: {e}")
                self.crop_model_data = None
            
            # Try to load yield prediction model
            try:
                self.yield_model_data = self.model_loader.load_yield_prediction_model()
                logger.info("Yield prediction ML model loaded successfully")
            except FileNotFoundError:
                logger.debug("Yield prediction model not found. Train models first or use rule-based fallback.")
                self.yield_model_data = None
            except Exception as e:
                logger.debug(f"Error loading yield prediction model: {e}")
                self.yield_model_data = None
                
        except Exception as e:
            logger.debug(f"Error initializing ML model loader: {e}")
            self.crop_model_data = None
            self.yield_model_data = None
    
    def prepare_crop_features(
        self,
        soil_ph: Optional[float],
        soil_n: Optional[float],
        soil_p: Optional[float],
        soil_k: Optional[float],
        soil_moisture: Optional[float],
        temperature: Optional[float],
        rainfall: Optional[float],
        humidity: Optional[float],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        season: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Prepare features for crop recommendation model.
        
        Args:
            soil_ph: Soil pH
            soil_n: Nitrogen content (kg/ha)
            soil_p: Phosphorus content (kg/ha)
            soil_k: Potassium content (kg/ha)
            soil_moisture: Soil moisture (%)
            temperature: Temperature (°C)
            rainfall: Rainfall (mm)
            humidity: Humidity (%)
            latitude: Latitude
            longitude: Longitude
            season: Season (kharif/rabi/zaid)
            
        Returns:
            Feature array or None if insufficient data
        """
        if self.crop_model_data is None:
            return None
        
        # Get feature names from metadata
        feature_names = self.crop_model_data['metadata']['feature_names']
        
        # Use location-based defaults if data is missing to differentiate fields
        # This prevents all fields from getting identical recommendations
        if latitude is not None and longitude is not None:
            # Use location-based defaults to add variation
            # India-specific: latitude affects soil characteristics
            lat_factor = (latitude - 8) / (37 - 8)  # Normalize to 0-1 for India
            lon_factor = (longitude - 68) / (97 - 68)  # Normalize to 0-1 for India
            
            # Location-based pH (varies by region)
            ph_default = 6.5 + (lat_factor * 1.5)  # Range: 6.5-8.0
            # Location-based nutrients (varies by region)
            n_default = 80.0 + (lat_factor * 60.0)  # Range: 80-140
            p_default = 25.0 + (lon_factor * 15.0)  # Range: 25-40
            k_default = 40.0 + (lat_factor * 30.0)  # Range: 40-70
            # Location-based moisture
            moisture_default = 45.0 + (lon_factor * 20.0)  # Range: 45-65
        else:
            # Fallback to neutral defaults if no location
            ph_default = 7.0
            n_default = 100.0
            p_default = 30.0
            k_default = 50.0
            moisture_default = 50.0
        
        # Use provided values or location-based defaults
        ph = soil_ph if soil_ph is not None else ph_default
        moisture = soil_moisture if soil_moisture is not None else moisture_default
        n = soil_n if soil_n is not None else n_default
        p = soil_p if soil_p is not None else p_default
        k = soil_k if soil_k is not None else k_default
        temp = temperature if temperature is not None else 25.0
        rain = rainfall if rainfall is not None else 500.0
        hum = humidity if humidity is not None else 60.0
        
        # Log when defaults are used (for debugging)
        if soil_ph is None or soil_n is None or soil_p is None or soil_k is None:
            logger.debug(
                f"Using location-based defaults for crop recommendation at ({latitude}, {longitude}): "
                f"ph={ph:.2f}, n={n:.2f}, p={p:.2f}, k={k:.2f}"
            )
        
        # Calculate engineered features
        np_ratio = n / (p + 1e-6)
        nk_ratio = n / (k + 1e-6)
        pk_ratio = p / (k + 1e-6)
        total_nutrients = n + p + k
        
        n_sufficient = 1 if n >= 100 else 0
        p_sufficient = 1 if p >= 30 else 0
        k_sufficient = 1 if k >= 50 else 0
        
        # Location normalization (India coordinates)
        lat_norm = ((latitude - 8) / (37 - 8)) if latitude else 0.5
        lon_norm = ((longitude - 68) / (97 - 68)) if longitude else 0.5
        
        # pH category encoding
        if ph < 5.5:
            ph_category = 0  # acidic
        elif ph < 6.5:
            ph_category = 1  # slightly_acidic
        elif ph < 7.5:
            ph_category = 2  # neutral
        else:
            ph_category = 3  # alkaline
        
        # Temperature category encoding
        if temp < 15:
            temp_category = 0  # cold
        elif temp < 25:
            temp_category = 1  # moderate
        elif temp < 35:
            temp_category = 2  # warm
        else:
            temp_category = 3  # hot
        
        # Rainfall category encoding
        if rain < 400:
            rainfall_category = 0  # low
        elif rain < 800:
            rainfall_category = 1  # moderate
        elif rain < 1200:
            rainfall_category = 2  # high
        else:
            rainfall_category = 3  # very_high
        
        # Build feature array in the same order as training
        features = []
        for feature_name in feature_names:
            if feature_name == 'ph':
                features.append(ph)
            elif feature_name == 'moisture':
                features.append(moisture)
            elif feature_name == 'n':
                features.append(n)
            elif feature_name == 'p':
                features.append(p)
            elif feature_name == 'k':
                features.append(k)
            elif feature_name == 'temperature':
                features.append(temp)
            elif feature_name == 'rainfall':
                features.append(rain)
            elif feature_name == 'humidity':
                features.append(hum)
            elif feature_name == 'np_ratio':
                features.append(np_ratio)
            elif feature_name == 'nk_ratio':
                features.append(nk_ratio)
            elif feature_name == 'pk_ratio':
                features.append(pk_ratio)
            elif feature_name == 'total_nutrients':
                features.append(total_nutrients)
            elif feature_name == 'n_sufficient':
                features.append(n_sufficient)
            elif feature_name == 'p_sufficient':
                features.append(p_sufficient)
            elif feature_name == 'k_sufficient':
                features.append(k_sufficient)
            elif feature_name == 'lat_norm':
                features.append(lat_norm)
            elif feature_name == 'lon_norm':
                features.append(lon_norm)
            elif feature_name == 'ph_category_encoded':
                features.append(ph_category)
            elif feature_name == 'temp_category_encoded':
                features.append(temp_category)
            elif feature_name == 'rainfall_category_encoded':
                features.append(rainfall_category)
            else:
                # Unknown feature, use default
                features.append(0.0)
        
        return np.array(features)
    
    def prepare_yield_features(
        self,
        crop_name: str,
        soil_ph: Optional[float],
        soil_n: Optional[float],
        soil_p: Optional[float],
        soil_k: Optional[float],
        soil_moisture: Optional[float],
        temperature: Optional[float],
        rainfall: Optional[float],
        humidity: Optional[float],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        season: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """
        Prepare features for yield prediction model.
        
        Args:
            crop_name: Name of the crop
            soil_ph: Soil pH
            soil_n: Nitrogen content (kg/ha)
            soil_p: Phosphorus content (kg/ha)
            soil_k: Potassium content (kg/ha)
            soil_moisture: Soil moisture (%)
            temperature: Temperature (°C)
            rainfall: Rainfall (mm)
            humidity: Humidity (%)
            latitude: Latitude
            longitude: Longitude
            season: Season
            
        Returns:
            Feature array or None if insufficient data
        """
        if self.yield_model_data is None:
            return None
        
        # Get feature names from metadata
        feature_names = self.yield_model_data['metadata']['feature_names']
        
        # Encode crop name
        try:
            crop_encoded = self.yield_model_data['encoder'].transform([crop_name])[0]
        except (ValueError, KeyError):
            # Crop not in encoder, use default
            crop_encoded = 0
        
        # Prepare features specifically for yield prediction (may differ from crop recommendation)
        # Get the exact feature list expected by yield model
        yield_feature_names = [f for f in feature_names if f != 'crop_encoded']
        
        # Use location-based defaults if data is missing to differentiate fields
        # This prevents all fields from getting identical recommendations
        if latitude is not None and longitude is not None:
            # Use location-based defaults to add variation
            # India-specific: latitude affects soil characteristics
            lat_factor = (latitude - 8) / (37 - 8)  # Normalize to 0-1 for India
            lon_factor = (longitude - 68) / (97 - 68)  # Normalize to 0-1 for India
            
            # Location-based pH (varies by region)
            ph_default = 6.5 + (lat_factor * 1.5)  # Range: 6.5-8.0
            # Location-based nutrients (varies by region)
            n_default = 80.0 + (lat_factor * 60.0)  # Range: 80-140
            p_default = 25.0 + (lon_factor * 15.0)  # Range: 25-40
            k_default = 40.0 + (lat_factor * 30.0)  # Range: 40-70
            # Location-based moisture
            moisture_default = 45.0 + (lon_factor * 20.0)  # Range: 45-65
        else:
            # Fallback to neutral defaults if no location
            ph_default = 7.0
            n_default = 100.0
            p_default = 30.0
            k_default = 50.0
            moisture_default = 50.0
        
        # Use provided values or location-based defaults
        ph = soil_ph if soil_ph is not None else ph_default
        moisture = soil_moisture if soil_moisture is not None else moisture_default
        n = soil_n if soil_n is not None else n_default
        p = soil_p if soil_p is not None else p_default
        k = soil_k if soil_k is not None else k_default
        temp = temperature if temperature is not None else 25.0
        rain = rainfall if rainfall is not None else 500.0
        hum = humidity if humidity is not None else 60.0
        
        # Log when defaults are used (for debugging)
        if soil_ph is None or soil_n is None or soil_p is None or soil_k is None:
            logger.debug(
                f"Using location-based defaults for yield prediction at ({latitude}, {longitude}): "
                f"ph={ph:.2f}, n={n:.2f}, p={p:.2f}, k={k:.2f}"
            )
        
        # Calculate engineered features
        np_ratio = n / (p + 1e-6)
        nk_ratio = n / (k + 1e-6)
        pk_ratio = p / (k + 1e-6)
        total_nutrients = n + p + k
        
        n_sufficient = 1 if n >= 100 else 0
        p_sufficient = 1 if p >= 30 else 0
        k_sufficient = 1 if k >= 50 else 0
        
        # Location normalization (India coordinates)
        lat_norm = ((latitude - 8) / (37 - 8)) if latitude else 0.5
        lon_norm = ((longitude - 68) / (97 - 68)) if longitude else 0.5
        
        # Build feature array in the exact order expected by yield model
        features = []
        for feature_name in feature_names:
            if feature_name == 'crop_encoded':
                features.append(crop_encoded)
            elif feature_name == 'ph':
                features.append(ph)
            elif feature_name == 'moisture':
                features.append(moisture)
            elif feature_name == 'n':
                features.append(n)
            elif feature_name == 'p':
                features.append(p)
            elif feature_name == 'k':
                features.append(k)
            elif feature_name == 'temperature':
                features.append(temp)
            elif feature_name == 'rainfall':
                features.append(rain)
            elif feature_name == 'humidity':
                features.append(hum)
            elif feature_name == 'np_ratio':
                features.append(np_ratio)
            elif feature_name == 'nk_ratio':
                features.append(nk_ratio)
            elif feature_name == 'pk_ratio':
                features.append(pk_ratio)
            elif feature_name == 'total_nutrients':
                features.append(total_nutrients)
            elif feature_name == 'n_sufficient':
                features.append(n_sufficient)
            elif feature_name == 'p_sufficient':
                features.append(p_sufficient)
            elif feature_name == 'k_sufficient':
                features.append(k_sufficient)
            elif feature_name == 'lat_norm':
                features.append(lat_norm)
            elif feature_name == 'lon_norm':
                features.append(lon_norm)
            # Note: yield model doesn't use category encodings (ph_category, temp_category, rainfall_category)
            else:
                # Unknown feature, use default
                features.append(0.0)
        
        return np.array(features)
    
    def predict_crop_recommendations(
        self,
        soil_ph: Optional[float],
        soil_n: Optional[float],
        soil_p: Optional[float],
        soil_k: Optional[float],
        soil_moisture: Optional[float],
        temperature: Optional[float],
        rainfall: Optional[float],
        humidity: Optional[float],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        season: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get crop recommendations using ML model.
        
        Returns:
            List of recommendations with crop names and confidence scores
        """
        if self.crop_model_data is None:
            return []
        
        # Prepare features
        features = self.prepare_crop_features(
            soil_ph=soil_ph,
            soil_n=soil_n,
            soil_p=soil_p,
            soil_k=soil_k,
            soil_moisture=soil_moisture,
            temperature=temperature,
            rainfall=rainfall,
            humidity=humidity,
            latitude=latitude,
            longitude=longitude,
            season=season
        )
        
        if features is None:
            return []
        
        # Scale features
        features_scaled = self.crop_model_data['scaler'].transform([features])
        
        # Get predictions for all crops
        probabilities = self.crop_model_data['model'].predict_proba(features_scaled)[0]
        crop_names = self.crop_model_data['encoder'].classes_
        
        # Create recommendations
        recommendations = []
        for i, crop_name in enumerate(crop_names):
            confidence = probabilities[i] * 100
            
            recommendations.append({
                'crop_name': crop_name,
                'confidence_score': round(confidence, 2),
                'ml_prediction': True,  # Flag to indicate ML prediction
            })
        
        # Sort by confidence
        recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return recommendations[:limit]
    
    def predict_yield(
        self,
        crop_name: str,
        soil_ph: Optional[float],
        soil_n: Optional[float],
        soil_p: Optional[float],
        soil_k: Optional[float],
        soil_moisture: Optional[float],
        temperature: Optional[float],
        rainfall: Optional[float],
        humidity: Optional[float],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        season: Optional[str] = None
    ) -> Optional[float]:
        """
        Predict crop yield using ML model.
        
        Args:
            crop_name: Name of the crop
            Other args: Same as prepare_yield_features
            
        Returns:
            Predicted yield in kg/hectare, or None if prediction fails
        """
        if self.yield_model_data is None:
            return None
        
        # Prepare features
        features = self.prepare_yield_features(
            crop_name=crop_name,
            soil_ph=soil_ph,
            soil_n=soil_n,
            soil_p=soil_p,
            soil_k=soil_k,
            soil_moisture=soil_moisture,
            temperature=temperature,
            rainfall=rainfall,
            humidity=humidity,
            latitude=latitude,
            longitude=longitude,
            season=season
        )
        
        if features is None:
            return None
        
        # Scale features
        features_scaled = self.yield_model_data['scaler'].transform([features])
        
        # Predict (model was trained on unscaled targets, so prediction is already in kg/ha)
        yield_pred = self.yield_model_data['model'].predict(features_scaled)[0]
        
        # Note: y_scaler exists but model was trained on unscaled y_train,
        # so predictions are already in the correct scale (kg/ha)
        # No inverse transform needed
        
        # Ensure non-negative and within reasonable bounds
        yield_pred = max(0, yield_pred)
        # Cap at reasonable maximum (e.g., 200,000 kg/ha for very high-yield crops like sugarcane)
        yield_pred = min(yield_pred, 200000)
        
        return round(yield_pred, 2)


# Global instance
_ml_service = None


def get_ml_service() -> MLRecommendationService:
    """Get or create global ML service instance."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLRecommendationService()
    return _ml_service

