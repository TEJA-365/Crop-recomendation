"""
Synthetic data generator for ML model training.

This script generates synthetic training data when real data is insufficient.
It creates realistic crop-soil-weather combinations based on known crop requirements.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


class SyntheticDataGenerator:
    """Generates synthetic training data for crop recommendation and yield prediction."""
    
    # Crop requirements (from recommendation service)
    CROP_REQUIREMENTS = {
        'Rice': {
            'ph_min': 5.0, 'ph_max': 7.5,
            'n_min': 100, 'p_min': 20, 'k_min': 40,
            'moisture_min': 60,
            'temperature_min': 20, 'temperature_max': 35,
            'rainfall_min': 1000,
            'season': ['kharif'],
            'avg_yield': 3000,
        },
        'Wheat': {
            'ph_min': 6.0, 'ph_max': 7.5,
            'n_min': 120, 'p_min': 30, 'k_min': 50,
            'moisture_min': 40,
            'temperature_min': 15, 'temperature_max': 25,
            'rainfall_min': 500,
            'season': ['rabi'],
            'avg_yield': 3500,
        },
        'Maize': {
            'ph_min': 5.5, 'ph_max': 7.0,
            'n_min': 150, 'p_min': 25, 'k_min': 60,
            'moisture_min': 50,
            'temperature_min': 18, 'temperature_max': 30,
            'rainfall_min': 600,
            'season': ['kharif', 'zaid'],
            'avg_yield': 4000,
        },
        'Cotton': {
            'ph_min': 5.5, 'ph_max': 8.0,
            'n_min': 80, 'p_min': 20, 'k_min': 50,
            'moisture_min': 50,
            'temperature_min': 21, 'temperature_max': 35,
            'rainfall_min': 500,
            'season': ['kharif'],
            'avg_yield': 500,
        },
        'Sugarcane': {
            'ph_min': 6.0, 'ph_max': 7.5,
            'n_min': 200, 'p_min': 40, 'k_min': 100,
            'moisture_min': 70,
            'temperature_min': 20, 'temperature_max': 35,
            'rainfall_min': 1200,
            'season': ['year_round'],
            'avg_yield': 70000,
        },
        'Potato': {
            'ph_min': 4.8, 'ph_max': 5.5,
            'n_min': 100, 'p_min': 50, 'k_min': 150,
            'moisture_min': 60,
            'temperature_min': 15, 'temperature_max': 25,
            'rainfall_min': 500,
            'season': ['rabi', 'zaid'],
            'avg_yield': 25000,
        },
        'Tomato': {
            'ph_min': 6.0, 'ph_max': 7.0,
            'n_min': 120, 'p_min': 40, 'k_min': 120,
            'moisture_min': 60,
            'temperature_min': 18, 'temperature_max': 28,
            'rainfall_min': 400,
            'season': ['year_round'],
            'avg_yield': 30000,
        },
        'Onion': {
            'ph_min': 6.0, 'ph_max': 7.0,
            'n_min': 100, 'p_min': 30, 'k_min': 80,
            'moisture_min': 50,
            'temperature_min': 13, 'temperature_max': 25,
            'rainfall_min': 400,
            'season': ['rabi', 'kharif'],
            'avg_yield': 20000,
        },
        'Chilli': {
            'ph_min': 6.0, 'ph_max': 7.0,
            'n_min': 100, 'p_min': 30, 'k_min': 100,
            'moisture_min': 50,
            'temperature_min': 20, 'temperature_max': 30,
            'rainfall_min': 400,
            'season': ['kharif', 'rabi'],
            'avg_yield': 15000,
        },
        'Groundnut': {
            'ph_min': 6.0, 'ph_max': 7.5,
            'n_min': 20, 'p_min': 20, 'k_min': 40,
            'moisture_min': 40,
            'temperature_min': 20, 'temperature_max': 35,
            'rainfall_min': 500,
            'season': ['kharif', 'rabi'],
            'avg_yield': 2000,
        },
        'Soybean': {
            'ph_min': 6.0, 'ph_max': 7.0,
            'n_min': 20, 'p_min': 30, 'k_min': 50,
            'moisture_min': 50,
            'temperature_min': 20, 'temperature_max': 30,
            'rainfall_min': 600,
            'season': ['kharif'],
            'avg_yield': 2500,
        },
        'Pigeon Pea': {
            'ph_min': 6.0, 'ph_max': 7.5,
            'n_min': 20, 'p_min': 20, 'k_min': 30,
            'moisture_min': 40,
            'temperature_min': 20, 'temperature_max': 35,
            'rainfall_min': 600,
            'season': ['kharif'],
            'avg_yield': 1200,
        },
    }
    
    # Indian regions (approximate coordinates)
    REGIONS = {
        'North': {'lat_range': (28, 32), 'lon_range': (74, 80)},
        'South': {'lat_range': (10, 15), 'lon_range': (76, 80)},
        'East': {'lat_range': (20, 26), 'lon_range': (85, 90)},
        'West': {'lat_range': (18, 24), 'lon_range': (72, 76)},
        'Central': {'lat_range': (20, 26), 'lon_range': (75, 82)},
    }
    
    SEASONS = ['kharif', 'rabi', 'zaid', 'year_round']
    SOIL_TYPES = ['clay', 'sandy', 'loamy', 'silt', 'peat', 'chalky']
    
    def __init__(self, output_dir=None, random_seed=42):
        """
        Initialize synthetic data generator.
        
        Args:
            output_dir: Directory to save generated data
            random_seed: Random seed for reproducibility
        """
        if output_dir is None:
            self.output_dir = BASE_DIR / 'ml_training' / 'data'
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        np.random.seed(random_seed)
    
    def generate_optimal_sample(self, crop_name):
        """
        Generate a sample with optimal conditions for a crop.
        
        Args:
            crop_name: Name of the crop
            
        Returns:
            dict: Sample data
        """
        req = self.CROP_REQUIREMENTS[crop_name]
        
        # Generate optimal values within range
        ph = np.random.uniform(req['ph_min'], req['ph_max'])
        n = np.random.uniform(req['n_min'], req['n_min'] * 1.5)
        p = np.random.uniform(req['p_min'], req['p_min'] * 1.5)
        k = np.random.uniform(req['k_min'], req['k_min'] * 1.5)
        moisture = np.random.uniform(req['moisture_min'], 100)
        temperature = np.random.uniform(req['temperature_min'], req['temperature_max'])
        rainfall = np.random.uniform(req['rainfall_min'], req['rainfall_min'] * 1.5)
        humidity = np.random.uniform(50, 80)
        
        # Select season
        if 'year_round' in req['season']:
            season = np.random.choice(['kharif', 'rabi', 'zaid'])
        else:
            season = np.random.choice(req['season'])
        
        # Generate location
        region = np.random.choice(list(self.REGIONS.keys()))
        lat = np.random.uniform(*self.REGIONS[region]['lat_range'])
        lon = np.random.uniform(*self.REGIONS[region]['lon_range'])
        
        # Calculate yield (optimal conditions = high yield)
        base_yield = req['avg_yield']
        yield_multiplier = np.random.uniform(0.9, 1.2)  # 90-120% of average
        yield_achieved = base_yield * yield_multiplier
        
        return {
            'crop_name': crop_name,
            'ph': round(ph, 2),
            'moisture': round(moisture, 2),
            'n': round(n, 2),
            'p': round(p, 2),
            'k': round(k, 2),
            'temperature': round(temperature, 2),
            'rainfall': round(rainfall, 2),
            'humidity': round(humidity, 2),
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'season': season,
            'year': np.random.randint(2020, 2024),
            'yield_achieved': round(yield_achieved, 2),
            'soil_type': np.random.choice(self.SOIL_TYPES),
        }
    
    def generate_suboptimal_sample(self, crop_name):
        """
        Generate a sample with suboptimal conditions for a crop.
        
        Args:
            crop_name: Name of the crop
            
        Returns:
            dict: Sample data
        """
        req = self.CROP_REQUIREMENTS[crop_name]
        
        # Generate values that may be outside optimal range
        # pH might be slightly off
        ph_offset = np.random.choice([-1, 1]) * np.random.uniform(0.5, 2.0)
        ph = np.clip((req['ph_min'] + req['ph_max']) / 2 + ph_offset, 3.0, 9.0)
        
        # Nutrients might be low
        n = np.random.uniform(req['n_min'] * 0.5, req['n_min'] * 0.9)
        p = np.random.uniform(req['p_min'] * 0.5, req['p_min'] * 0.9)
        k = np.random.uniform(req['k_min'] * 0.5, req['k_min'] * 0.9)
        
        moisture = np.random.uniform(req['moisture_min'] * 0.7, req['moisture_min'] * 0.95)
        temperature = np.random.uniform(
            req['temperature_min'] - 5, 
            req['temperature_max'] + 5
        )
        rainfall = np.random.uniform(req['rainfall_min'] * 0.6, req['rainfall_min'] * 0.9)
        humidity = np.random.uniform(30, 70)
        
        # Season might not be ideal
        if 'year_round' in req['season']:
            season = np.random.choice(['kharif', 'rabi', 'zaid'])
        else:
            # Sometimes wrong season
            if np.random.random() < 0.3:
                wrong_seasons = [s for s in self.SEASONS if s not in req['season']]
                season = np.random.choice(wrong_seasons) if wrong_seasons else np.random.choice(req['season'])
            else:
                season = np.random.choice(req['season'])
        
        region = np.random.choice(list(self.REGIONS.keys()))
        lat = np.random.uniform(*self.REGIONS[region]['lat_range'])
        lon = np.random.uniform(*self.REGIONS[region]['lon_range'])
        
        # Lower yield due to suboptimal conditions
        base_yield = req['avg_yield']
        yield_multiplier = np.random.uniform(0.5, 0.85)  # 50-85% of average
        yield_achieved = base_yield * yield_multiplier
        
        return {
            'crop_name': crop_name,
            'ph': round(ph, 2),
            'moisture': round(moisture, 2),
            'n': round(n, 2),
            'p': round(p, 2),
            'k': round(k, 2),
            'temperature': round(temperature, 2),
            'rainfall': round(rainfall, 2),
            'humidity': round(humidity, 2),
            'latitude': round(lat, 6),
            'longitude': round(lon, 6),
            'season': season,
            'year': np.random.randint(2020, 2024),
            'yield_achieved': round(yield_achieved, 2),
            'soil_type': np.random.choice(self.SOIL_TYPES),
        }
    
    def generate_crop_recommendation_dataset(self, n_samples_per_crop=50):
        """
        Generate synthetic dataset for crop recommendation.
        
        Args:
            n_samples_per_crop: Number of samples to generate per crop
            
        Returns:
            pandas.DataFrame: Generated dataset
        """
        print(f"Generating synthetic crop recommendation dataset...")
        print(f"Target: {n_samples_per_crop} samples per crop")
        
        data_rows = []
        
        for crop_name in self.CROP_REQUIREMENTS.keys():
            # Generate mix of optimal and suboptimal samples
            n_optimal = int(n_samples_per_crop * 0.6)  # 60% optimal
            n_suboptimal = n_samples_per_crop - n_optimal  # 40% suboptimal
            
            for _ in range(n_optimal):
                data_rows.append(self.generate_optimal_sample(crop_name))
            
            for _ in range(n_suboptimal):
                data_rows.append(self.generate_suboptimal_sample(crop_name))
        
        df = pd.DataFrame(data_rows)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        print(f"Generated {len(df)} samples")
        print(f"Crop distribution:")
        print(df['crop_name'].value_counts())
        
        # Save
        output_file = self.output_dir / 'crop_recommendation_synthetic.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")
        
        return df
    
    def generate_yield_prediction_dataset(self, n_samples_per_crop=50):
        """
        Generate synthetic dataset for yield prediction.
        
        Args:
            n_samples_per_crop: Number of samples to generate per crop
            
        Returns:
            pandas.DataFrame: Generated dataset
        """
        print(f"Generating synthetic yield prediction dataset...")
        print(f"Target: {n_samples_per_crop} samples per crop")
        
        data_rows = []
        
        for crop_name in self.CROP_REQUIREMENTS.keys():
            for _ in range(n_samples_per_crop):
                # Mix of optimal and suboptimal
                if np.random.random() < 0.6:
                    sample = self.generate_optimal_sample(crop_name)
                else:
                    sample = self.generate_suboptimal_sample(crop_name)
                
                data_rows.append(sample)
        
        df = pd.DataFrame(data_rows)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        print(f"Generated {len(df)} samples")
        print(f"Yield statistics:")
        print(df['yield_achieved'].describe())
        
        # Save
        output_file = self.output_dir / 'yield_prediction_synthetic.csv'
        df.to_csv(output_file, index=False)
        print(f"Saved to {output_file}")
        
        return df


def main():
    """Main function to generate synthetic data."""
    generator = SyntheticDataGenerator()
    
    # Generate crop recommendation dataset
    crop_df = generator.generate_crop_recommendation_dataset(n_samples_per_crop=50)
    
    # Generate yield prediction dataset
    yield_df = generator.generate_yield_prediction_dataset(n_samples_per_crop=50)
    
    print("\nSynthetic data generation complete!")


if __name__ == '__main__':
    main()

