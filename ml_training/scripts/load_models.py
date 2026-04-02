"""
Model loading utilities for inference.

This module provides functions to load trained models and make predictions.
"""

import pickle
import json
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


class ModelLoader:
    """Utility class for loading trained models."""
    
    def __init__(self, model_dir=None):
        """
        Initialize model loader.
        
        Args:
            model_dir: Directory containing trained models
        """
        if model_dir is None:
            self.model_dir = BASE_DIR / 'ml_training' / 'models'
        else:
            self.model_dir = Path(model_dir)
    
    def load_crop_recommendation_model(self):
        """
        Load crop recommendation model and associated files.
        
        Returns:
            Dictionary with model, scaler, encoder, and metadata
        """
        model_path = self.model_dir / 'crop_recommendation_model.pkl'
        scaler_path = self.model_dir / 'crop_recommendation_scaler.pkl'
        encoder_path = self.model_dir / 'crop_recommendation_encoder.pkl'
        metadata_path = self.model_dir / 'crop_recommendation_model_metadata.json'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        
        with open(encoder_path, 'rb') as f:
            encoder = pickle.load(f)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            'model': model,
            'scaler': scaler,
            'encoder': encoder,
            'metadata': metadata,
        }
    
    def load_yield_prediction_model(self):
        """
        Load yield prediction model and associated files.
        
        Returns:
            Dictionary with model, scaler, y_scaler, encoder, and metadata
        """
        model_path = self.model_dir / 'yield_prediction_model.pkl'
        scaler_path = self.model_dir / 'yield_prediction_scaler.pkl'
        y_scaler_path = self.model_dir / 'yield_prediction_y_scaler.pkl'
        encoder_path = self.model_dir / 'yield_prediction_encoder.pkl'
        metadata_path = self.model_dir / 'yield_prediction_model_metadata.json'
        
        if not model_path.exists():
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        with open(scaler_path, 'rb') as f:
            scaler = pickle.load(f)
        
        with open(y_scaler_path, 'rb') as f:
            y_scaler = pickle.load(f)
        
        with open(encoder_path, 'rb') as f:
            encoder = pickle.load(f)
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        return {
            'model': model,
            'scaler': scaler,
            'y_scaler': y_scaler,
            'encoder': encoder,
            'metadata': metadata,
        }
    
    def predict_crop(self, features):
        """
        Predict crop recommendation.
        
        Args:
            features: Array of features (must match training features)
            
        Returns:
            Tuple of (crop_name, confidence_score, all_probabilities)
        """
        model_data = self.load_crop_recommendation_model()
        
        # Scale features
        features_scaled = model_data['scaler'].transform([features])
        
        # Predict
        prediction = model_data['model'].predict(features_scaled)[0]
        probabilities = model_data['model'].predict_proba(features_scaled)[0]
        
        # Decode crop name
        crop_name = model_data['encoder'].inverse_transform([prediction])[0]
        confidence = probabilities[prediction] * 100
        
        # Get all crop probabilities
        crop_probs = {}
        for i, crop in enumerate(model_data['encoder'].classes_):
            crop_probs[crop] = probabilities[i] * 100
        
        return crop_name, confidence, crop_probs
    
    def predict_yield(self, features):
        """
        Predict crop yield.
        
        Args:
            features: Array of features (must match training features)
            
        Returns:
            Predicted yield in kg/hectare
        """
        model_data = self.load_yield_prediction_model()
        
        # Scale features
        features_scaled = model_data['scaler'].transform([features])
        
        # Predict
        yield_pred = model_data['model'].predict(features_scaled)[0]
        
        # Inverse transform if y_scaler was used
        if model_data['y_scaler'] is not None:
            yield_pred = model_data['y_scaler'].inverse_transform([[yield_pred]])[0][0]
        
        return yield_pred


def main():
    """Example usage of model loader."""
    loader = ModelLoader()
    
    # Example: Predict crop recommendation
    print("Loading crop recommendation model...")
    try:
        crop_model = loader.load_crop_recommendation_model()
        print("✓ Crop recommendation model loaded")
        print(f"  Classes: {crop_model['metadata']['n_classes']}")
        print(f"  Features: {crop_model['metadata']['n_features']}")
    except FileNotFoundError as e:
        print(f"✗ {e}")
    
    # Example: Predict yield
    print("\nLoading yield prediction model...")
    try:
        yield_model = loader.load_yield_prediction_model()
        print("✓ Yield prediction model loaded")
        print(f"  Features: {yield_model['metadata']['n_features']}")
        print(f"  Yield range: {yield_model['metadata']['yield_min']:.2f} - {yield_model['metadata']['yield_max']:.2f} kg/ha")
    except FileNotFoundError as e:
        print(f"✗ {e}")


if __name__ == '__main__':
    main()

