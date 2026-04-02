"""
Data collection script for ML model training.

This script extracts data from Django database models and prepares it for ML training.
It collects soil data, weather data, and crop history to create training datasets.
"""

import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Setup Django environment
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crop_recommendation.settings')
django.setup()

from apps.farms.models import Field, CropHistory, Farm
from apps.soil.models import SoilData
from apps.weather.models import WeatherData
from django.contrib.auth.models import User


class DataCollector:
    """Collects data from Django models for ML training."""
    
    def __init__(self, output_dir=None):
        """
        Initialize data collector.
        
        Args:
            output_dir: Directory to save collected data (default: ml_training/data/)
        """
        if output_dir is None:
            self.output_dir = BASE_DIR / 'ml_training' / 'data'
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def collect_crop_recommendation_data(self, min_samples=100):
        """
        Collect data for crop recommendation model training.
        
        Creates a dataset with:
        - Features: soil properties, weather conditions, location, season
        - Target: crop_name (from crop history)
        
        Args:
            min_samples: Minimum number of samples to collect
            
        Returns:
            pandas.DataFrame: Training dataset
        """
        print("Collecting crop recommendation training data...")
        
        data_rows = []
        
        # Get all crop history entries
        crop_histories = CropHistory.objects.select_related(
            'field', 'field__farm'
        ).all()
        
        print(f"Found {crop_histories.count()} crop history entries")
        
        for crop_history in crop_histories:
            field = crop_history.field
            farm = field.farm
            
            # Get soil data (prefer latest, fallback to field defaults)
            soil_data = field.soil_data.order_by('-timestamp').first()
            
            if soil_data:
                ph = float(soil_data.ph)
                moisture = float(soil_data.moisture)
                n = float(soil_data.n)
                p = float(soil_data.p)
                k = float(soil_data.k)
            else:
                # Use field defaults if available
                ph = float(field.soil_ph) if field.soil_ph else None
                moisture = float(field.soil_moisture) if field.soil_moisture else None
                n = float(field.n_content) if field.n_content else None
                p = float(field.p_content) if field.p_content else None
                k = float(field.k_content) if field.k_content else None
            
            # Skip if no soil data available
            if ph is None or n is None or p is None or k is None:
                continue
            
            # Get weather data for the crop season
            # Try to find weather data around the crop planting time
            crop_date = datetime(crop_history.year, 1, 1)  # Approximate
            
            # Try to find weather data for this location and time
            weather = WeatherData.objects.filter(
                latitude__gte=float(farm.latitude) - 0.1,
                latitude__lte=float(farm.latitude) + 0.1,
                longitude__gte=float(farm.longitude) - 0.1,
                longitude__lte=float(farm.longitude) + 0.1,
                date__gte=crop_date - timedelta(days=30),
                date__lte=crop_date + timedelta(days=30)
            ).first()
            
            if weather:
                temperature = float(weather.temperature)
                rainfall = float(weather.rainfall)
                humidity = float(weather.humidity)
            else:
                # Use average values if weather data not available
                temperature = None
                rainfall = None
                humidity = None
            
            # Create data row
            row = {
                'crop_name': crop_history.crop_name,
                'ph': ph,
                'moisture': moisture if moisture else 50.0,  # Default if missing
                'n': n,
                'p': p,
                'k': k,
                'temperature': temperature if temperature else 25.0,  # Default
                'rainfall': rainfall if rainfall else 500.0,  # Default
                'humidity': humidity if humidity else 60.0,  # Default
                'latitude': float(farm.latitude),
                'longitude': float(farm.longitude),
                'season': crop_history.season,
                'year': crop_history.year,
                'yield_achieved': float(crop_history.yield_achieved) if crop_history.yield_achieved else None,
                'soil_type': farm.soil_type,
            }
            
            data_rows.append(row)
        
        if not data_rows:
            print("Warning: No data collected from database. Consider using synthetic data generator.")
            return None
        
        df = pd.DataFrame(data_rows)
        print(f"Collected {len(df)} samples")
        
        # Save raw data
        output_file = self.output_dir / 'crop_recommendation_raw.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved raw data to {output_file}")
        
        return df
    
    def collect_yield_prediction_data(self):
        """
        Collect data for yield prediction model training.
        
        Creates a dataset with:
        - Features: crop_name, soil properties, weather conditions, location, season
        - Target: yield_achieved (from crop history)
        
        Returns:
            pandas.DataFrame: Training dataset
        """
        print("Collecting yield prediction training data...")
        
        data_rows = []
        
        # Get all crop history entries with yield data
        crop_histories = CropHistory.objects.select_related(
            'field', 'field__farm'
        ).exclude(yield_achieved__isnull=True)
        
        print(f"Found {crop_histories.count()} crop history entries with yield data")
        
        for crop_history in crop_histories:
            field = crop_history.field
            farm = field.farm
            
            # Get soil data
            soil_data = field.soil_data.order_by('-timestamp').first()
            
            if soil_data:
                ph = float(soil_data.ph)
                moisture = float(soil_data.moisture)
                n = float(soil_data.n)
                p = float(soil_data.p)
                k = float(soil_data.k)
            else:
                ph = float(field.soil_ph) if field.soil_ph else None
                moisture = float(field.soil_moisture) if field.soil_moisture else None
                n = float(field.n_content) if field.n_content else None
                p = float(field.p_content) if field.p_content else None
                k = float(field.k_content) if field.k_content else None
            
            if ph is None or n is None or p is None or k is None:
                continue
            
            # Get weather data
            crop_date = datetime(crop_history.year, 1, 1)
            weather = WeatherData.objects.filter(
                latitude__gte=float(farm.latitude) - 0.1,
                latitude__lte=float(farm.latitude) + 0.1,
                longitude__gte=float(farm.longitude) - 0.1,
                longitude__lte=float(farm.longitude) + 0.1,
                date__gte=crop_date - timedelta(days=30),
                date__lte=crop_date + timedelta(days=30)
            ).first()
            
            if weather:
                temperature = float(weather.temperature)
                rainfall = float(weather.rainfall)
                humidity = float(weather.humidity)
            else:
                temperature = 25.0
                rainfall = 500.0
                humidity = 60.0
            
            row = {
                'crop_name': crop_history.crop_name,
                'ph': ph,
                'moisture': moisture if moisture else 50.0,
                'n': n,
                'p': p,
                'k': k,
                'temperature': temperature,
                'rainfall': rainfall,
                'humidity': humidity,
                'latitude': float(farm.latitude),
                'longitude': float(farm.longitude),
                'season': crop_history.season,
                'year': crop_history.year,
                'yield_achieved': float(crop_history.yield_achieved),
                'soil_type': farm.soil_type,
            }
            
            data_rows.append(row)
        
        if not data_rows:
            print("Warning: No yield data collected from database.")
            return None
        
        df = pd.DataFrame(data_rows)
        print(f"Collected {len(df)} samples with yield data")
        
        # Save raw data
        output_file = self.output_dir / 'yield_prediction_raw.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved raw data to {output_file}")
        
        return df
    
    def get_data_statistics(self, df):
        """
        Print statistics about collected data.
        
        Args:
            df: pandas.DataFrame to analyze
        """
        if df is None or df.empty:
            print("No data to analyze")
            return
        
        print("\n=== Data Statistics ===")
        print(f"Total samples: {len(df)}")
        print(f"\nFeatures shape: {df.shape}")
        print(f"\nMissing values:")
        print(df.isnull().sum())
        print(f"\nData types:")
        print(df.dtypes)
        
        if 'crop_name' in df.columns:
            print(f"\nCrop distribution:")
            print(df['crop_name'].value_counts())
        
        if 'yield_achieved' in df.columns:
            print(f"\nYield statistics:")
            print(df['yield_achieved'].describe())
        
        print(f"\nNumeric features statistics:")
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        print(df[numeric_cols].describe())


def main():
    """Main function to collect data."""
    collector = DataCollector()
    
    # Collect crop recommendation data
    crop_df = collector.collect_crop_recommendation_data()
    if crop_df is not None:
        collector.get_data_statistics(crop_df)
    
    # Collect yield prediction data
    yield_df = collector.collect_yield_prediction_data()
    if yield_df is not None:
        collector.get_data_statistics(yield_df)
    
    print("\nData collection complete!")


if __name__ == '__main__':
    main()

