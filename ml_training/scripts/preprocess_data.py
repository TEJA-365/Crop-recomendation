"""
Data preprocessing utilities for ML model training.

This module provides functions for cleaning, normalizing, and feature engineering
of crop recommendation and yield prediction datasets.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.preprocessing import StandardScaler, LabelEncoder, MinMaxScaler
from sklearn.model_selection import train_test_split
import pickle
import json


class DataPreprocessor:
    """Preprocesses data for ML model training."""
    
    def __init__(self, output_dir=None):
        """
        Initialize preprocessor.
        
        Args:
            output_dir: Directory to save processed data and scalers
        """
        if output_dir is None:
            self.output_dir = Path(__file__).resolve().parent.parent / 'data'
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Scalers and encoders (will be fitted during preprocessing)
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.feature_scaler = MinMaxScaler()
    
    def clean_data(self, df):
        """
        Clean the dataset by removing invalid values and handling missing data.
        
        Args:
            df: pandas.DataFrame to clean
            
        Returns:
            pandas.DataFrame: Cleaned dataframe
        """
        print("Cleaning data...")
        original_len = len(df)
        
        # Remove rows with missing critical features
        critical_features = ['ph', 'n', 'p', 'k', 'crop_name']
        df = df.dropna(subset=critical_features)
        
        # Remove invalid pH values (should be between 0-14)
        df = df[(df['ph'] >= 0) & (df['ph'] <= 14)]
        
        # Remove negative values for nutrients and moisture
        df = df[(df['n'] >= 0) & (df['p'] >= 0) & (df['k'] >= 0)]
        if 'moisture' in df.columns:
            df = df[(df['moisture'] >= 0) & (df['moisture'] <= 100)]
        
        # Remove invalid temperature values
        if 'temperature' in df.columns:
            df = df[(df['temperature'] >= -10) & (df['temperature'] <= 50)]
        
        # Remove negative rainfall
        if 'rainfall' in df.columns:
            df = df[df['rainfall'] >= 0]
        
        # Fill missing values with reasonable defaults
        if 'moisture' in df.columns:
            df['moisture'] = df['moisture'].fillna(50.0)
        if 'temperature' in df.columns:
            df['temperature'] = df['temperature'].fillna(25.0)
        if 'rainfall' in df.columns:
            df['rainfall'] = df['rainfall'].fillna(500.0)
        if 'humidity' in df.columns:
            df['humidity'] = df['humidity'].fillna(60.0)
        
        # Fill missing soil_type
        if 'soil_type' in df.columns:
            df['soil_type'] = df['soil_type'].fillna('unknown')
        
        removed = original_len - len(df)
        if removed > 0:
            print(f"Removed {removed} invalid rows ({removed/original_len*100:.1f}%)")
        
        print(f"Cleaned dataset: {len(df)} samples")
        return df
    
    def engineer_features(self, df):
        """
        Create additional features for better model performance.
        
        Args:
            df: pandas.DataFrame to engineer features for
            
        Returns:
            pandas.DataFrame: DataFrame with additional features
        """
        print("Engineering features...")
        
        # Nutrient ratios
        df['np_ratio'] = df['n'] / (df['p'] + 1e-6)  # Add small value to avoid division by zero
        df['nk_ratio'] = df['n'] / (df['k'] + 1e-6)
        df['pk_ratio'] = df['p'] / (df['k'] + 1e-6)
        df['total_nutrients'] = df['n'] + df['p'] + df['k']
        
        # pH categories
        df['ph_category'] = pd.cut(
            df['ph'],
            bins=[0, 5.5, 6.5, 7.5, 14],
            labels=['acidic', 'slightly_acidic', 'neutral', 'alkaline']
        )
        
        # Temperature categories
        if 'temperature' in df.columns:
            df['temp_category'] = pd.cut(
                df['temperature'],
                bins=[-10, 15, 25, 35, 50],
                labels=['cold', 'moderate', 'warm', 'hot']
            )
        
        # Rainfall categories
        if 'rainfall' in df.columns:
            df['rainfall_category'] = pd.cut(
                df['rainfall'],
                bins=[0, 400, 800, 1200, 10000],
                labels=['low', 'moderate', 'high', 'very_high']
            )
        
        # Nutrient sufficiency indicators
        # These are crop-specific, so we'll use general thresholds
        df['n_sufficient'] = (df['n'] >= 100).astype(int)
        df['p_sufficient'] = (df['p'] >= 30).astype(int)
        df['k_sufficient'] = (df['k'] >= 50).astype(int)
        
        # Location features (normalized)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Normalize to 0-1 range (assuming Indian coordinates)
            df['lat_norm'] = (df['latitude'] - 8) / (37 - 8)  # India lat range ~8-37
            df['lon_norm'] = (df['longitude'] - 68) / (97 - 68)  # India lon range ~68-97
        
        print(f"Feature engineering complete. New shape: {df.shape}")
        return df
    
    def prepare_crop_recommendation_data(self, df, test_size=0.2, val_size=0.1):
        """
        Prepare data for crop recommendation model (classification).
        
        Args:
            df: pandas.DataFrame with training data
            test_size: Fraction of data for testing
            val_size: Fraction of data for validation (from training set)
            
        Returns:
            dict: Dictionary with train/val/test splits and metadata
        """
        print("Preparing crop recommendation data...")
        
        # Clean data
        df = self.clean_data(df.copy())
        
        # Engineer features
        df = self.engineer_features(df.copy())
        
        # Select features for training
        feature_columns = [
            'ph', 'moisture', 'n', 'p', 'k',
            'temperature', 'rainfall', 'humidity',
            'np_ratio', 'nk_ratio', 'pk_ratio', 'total_nutrients',
            'n_sufficient', 'p_sufficient', 'k_sufficient',
        ]
        
        # Add location if available
        if 'lat_norm' in df.columns and 'lon_norm' in df.columns:
            feature_columns.extend(['lat_norm', 'lon_norm'])
        
        # Add encoded categorical features
        if 'ph_category' in df.columns:
            df['ph_category_encoded'] = pd.Categorical(df['ph_category']).codes
            feature_columns.append('ph_category_encoded')
        
        if 'temp_category' in df.columns:
            df['temp_category_encoded'] = pd.Categorical(df['temp_category']).codes
            feature_columns.append('temp_category_encoded')
        
        if 'rainfall_category' in df.columns:
            df['rainfall_category_encoded'] = pd.Categorical(df['rainfall_category']).codes
            feature_columns.append('rainfall_category_encoded')
        
        # Ensure all feature columns exist
        available_features = [col for col in feature_columns if col in df.columns]
        
        X = df[available_features].values
        y = df['crop_name'].values
        
        # Encode labels
        y_encoded = self.label_encoder.fit_transform(y)
        unique_crops = self.label_encoder.classes_
        
        print(f"Features: {len(available_features)}")
        print(f"Classes: {len(unique_crops)}")
        print(f"Crop distribution:")
        for crop, count in zip(unique_crops, np.bincount(y_encoded)):
            print(f"  {crop}: {count}")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=42, stratify=y_encoded
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_size, random_state=42, stratify=y_train
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Save scaler and encoder
        scaler_path = self.output_dir / 'crop_recommendation_scaler.pkl'
        encoder_path = self.output_dir / 'crop_recommendation_encoder.pkl'
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        
        # Save metadata
        metadata = {
            'feature_names': available_features,
            'n_features': len(available_features),
            'n_classes': len(unique_crops),
            'class_names': unique_crops.tolist(),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
        }
        
        metadata_path = self.output_dir / 'crop_recommendation_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return {
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_val': y_val,
            'y_test': y_test,
            'feature_names': available_features,
            'class_names': unique_crops,
            'metadata': metadata,
        }
    
    def prepare_yield_prediction_data(self, df, test_size=0.2, val_size=0.1):
        """
        Prepare data for yield prediction model (regression).
        
        Args:
            df: pandas.DataFrame with training data
            test_size: Fraction of data for testing
            val_size: Fraction of data for validation (from training set)
            
        Returns:
            dict: Dictionary with train/val/test splits and metadata
        """
        print("Preparing yield prediction data...")
        
        # Clean data
        df = self.clean_data(df.copy())
        
        # Remove rows without yield data
        df = df.dropna(subset=['yield_achieved'])
        df = df[df['yield_achieved'] > 0]  # Remove zero/negative yields
        
        # Engineer features
        df = self.engineer_features(df.copy())
        
        # Encode crop_name for use as feature
        crop_encoder = LabelEncoder()
        df['crop_encoded'] = crop_encoder.fit_transform(df['crop_name'])
        
        # Select features
        feature_columns = [
            'crop_encoded',  # Crop type as feature
            'ph', 'moisture', 'n', 'p', 'k',
            'temperature', 'rainfall', 'humidity',
            'np_ratio', 'nk_ratio', 'pk_ratio', 'total_nutrients',
            'n_sufficient', 'p_sufficient', 'k_sufficient',
        ]
        
        if 'lat_norm' in df.columns and 'lon_norm' in df.columns:
            feature_columns.extend(['lat_norm', 'lon_norm'])
        
        if 'ph_category_encoded' in df.columns:
            feature_columns.append('ph_category_encoded')
        if 'temp_category_encoded' in df.columns:
            feature_columns.append('temp_category_encoded')
        if 'rainfall_category_encoded' in df.columns:
            feature_columns.append('rainfall_category_encoded')
        
        available_features = [col for col in feature_columns if col in df.columns]
        
        X = df[available_features].values
        y = df['yield_achieved'].values
        
        print(f"Features: {len(available_features)}")
        print(f"Yield range: {y.min():.2f} - {y.max():.2f} kg/ha")
        print(f"Yield mean: {y.mean():.2f} kg/ha")
        print(f"Yield std: {y.std():.2f} kg/ha")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=val_size, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Scale target (for some models)
        y_scaler = MinMaxScaler()
        y_train_scaled = y_scaler.fit_transform(y_train.reshape(-1, 1)).ravel()
        y_val_scaled = y_scaler.transform(y_val.reshape(-1, 1)).ravel()
        y_test_scaled = y_scaler.transform(y_test.reshape(-1, 1)).ravel()
        
        # Save scalers and encoder
        scaler_path = self.output_dir / 'yield_prediction_scaler.pkl'
        y_scaler_path = self.output_dir / 'yield_prediction_y_scaler.pkl'
        encoder_path = self.output_dir / 'yield_prediction_encoder.pkl'
        
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        
        with open(y_scaler_path, 'wb') as f:
            pickle.dump(y_scaler, f)
        
        with open(encoder_path, 'wb') as f:
            pickle.dump(crop_encoder, f)
        
        # Save metadata
        metadata = {
            'feature_names': available_features,
            'n_features': len(available_features),
            'train_samples': len(X_train),
            'val_samples': len(X_val),
            'test_samples': len(X_test),
            'yield_min': float(y.min()),
            'yield_max': float(y.max()),
            'yield_mean': float(y.mean()),
            'yield_std': float(y.std()),
        }
        
        metadata_path = self.output_dir / 'yield_prediction_metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        
        return {
            'X_train': X_train_scaled,
            'X_val': X_val_scaled,
            'X_test': X_test_scaled,
            'y_train': y_train,
            'y_train_scaled': y_train_scaled,
            'y_val': y_val,
            'y_val_scaled': y_val_scaled,
            'y_test': y_test,
            'y_test_scaled': y_test_scaled,
            'feature_names': available_features,
            'metadata': metadata,
        }
    
    def save_processed_data(self, data, prefix='crop_recommendation'):
        """
        Save processed data to numpy files.
        
        Args:
            data: Dictionary with processed data
            prefix: Prefix for output files
        """
        print(f"Saving processed data with prefix '{prefix}'...")
        
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                file_path = self.output_dir / f'{prefix}_{key}.npy'
                np.save(file_path, value)
                print(f"  Saved {key}: {value.shape} -> {file_path}")


def main():
    """Example usage of preprocessor."""
    preprocessor = DataPreprocessor()
    
    # Example: Load and preprocess crop recommendation data
    data_dir = preprocessor.output_dir
    
    # Try to load collected or synthetic data
    crop_file = data_dir / 'crop_recommendation_raw.csv'
    if not crop_file.exists():
        crop_file = data_dir / 'crop_recommendation_synthetic.csv'
    
    if crop_file.exists():
        print(f"Loading data from {crop_file}")
        df = pd.read_csv(crop_file)
        processed = preprocessor.prepare_crop_recommendation_data(df)
        preprocessor.save_processed_data(processed, prefix='crop_recommendation')
    else:
        print(f"No crop recommendation data found. Please run collect_data.py or generate_synthetic_data.py first.")
    
    # Try to load yield prediction data
    yield_file = data_dir / 'yield_prediction_raw.csv'
    if not yield_file.exists():
        yield_file = data_dir / 'yield_prediction_synthetic.csv'
    
    if yield_file.exists():
        print(f"\nLoading data from {yield_file}")
        df = pd.read_csv(yield_file)
        processed = preprocessor.prepare_yield_prediction_data(df)
        preprocessor.save_processed_data(processed, prefix='yield_prediction')
    else:
        print(f"No yield prediction data found. Please run collect_data.py or generate_synthetic_data.py first.")


if __name__ == '__main__':
    main()

