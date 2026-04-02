"""
Train yield prediction model (regression).

This script trains a regression model to predict crop yield
based on crop type, soil properties, weather conditions, and location.
"""

import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score
)
import sys

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


class YieldPredictionTrainer:
    """Trainer for yield prediction regression model."""
    
    def __init__(self, data_dir=None, model_dir=None):
        """
        Initialize trainer.
        
        Args:
            data_dir: Directory containing preprocessed data
            model_dir: Directory to save trained models
        """
        if data_dir is None:
            self.data_dir = BASE_DIR / 'ml_training' / 'data'
        else:
            self.data_dir = Path(data_dir)
        
        if model_dir is None:
            self.model_dir = BASE_DIR / 'ml_training' / 'models'
        else:
            self.model_dir = Path(model_dir)
        
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.model = None
        self.scaler = None
        self.y_scaler = None
        self.crop_encoder = None
        self.metadata = None
    
    def load_data(self):
        """Load preprocessed training data."""
        print("Loading preprocessed data...")
        
        # Load features and labels
        X_train = np.load(self.data_dir / 'yield_prediction_X_train.npy')
        X_val = np.load(self.data_dir / 'yield_prediction_X_val.npy')
        X_test = np.load(self.data_dir / 'yield_prediction_X_test.npy')
        
        y_train = np.load(self.data_dir / 'yield_prediction_y_train.npy')
        y_val = np.load(self.data_dir / 'yield_prediction_y_val.npy')
        y_test = np.load(self.data_dir / 'yield_prediction_y_test.npy')
        
        # Load scalers and encoder
        with open(self.data_dir / 'yield_prediction_scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)
        
        with open(self.data_dir / 'yield_prediction_y_scaler.pkl', 'rb') as f:
            self.y_scaler = pickle.load(f)
        
        with open(self.data_dir / 'yield_prediction_encoder.pkl', 'rb') as f:
            self.crop_encoder = pickle.load(f)
        
        # Load metadata
        with open(self.data_dir / 'yield_prediction_metadata.json', 'r') as f:
            self.metadata = json.load(f)
        
        print(f"Training samples: {len(X_train)}")
        print(f"Validation samples: {len(X_val)}")
        print(f"Test samples: {len(X_test)}")
        print(f"Features: {self.metadata['n_features']}")
        print(f"Yield range: {self.metadata['yield_min']:.2f} - {self.metadata['yield_max']:.2f} kg/ha")
        
        return (X_train, X_val, X_test, y_train, y_val, y_test)
    
    def train(self, X_train, y_train, X_val, y_val, model_type='random_forest', 
              n_estimators=100, max_depth=None, random_state=42):
        """
        Train regression model.
        
        Args:
            X_train: Training features
            y_train: Training targets (yield)
            X_val: Validation features
            y_val: Validation targets
            model_type: 'random_forest' or 'gradient_boosting'
            n_estimators: Number of trees
            max_depth: Maximum depth of trees
            random_state: Random seed
            
        Returns:
            Trained model
        """
        print(f"\nTraining {model_type} regressor...")
        print(f"Parameters: n_estimators={n_estimators}, max_depth={max_depth}")
        
        # Create model
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                n_jobs=-1
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=random_state,
                learning_rate=0.1
            )
        else:
            raise ValueError(f"Unknown model_type: {model_type}")
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation set
        y_val_pred = self.model.predict(X_val)
        val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
        val_mae = mean_absolute_error(y_val, y_val_pred)
        val_r2 = r2_score(y_val, y_val_pred)
        
        print(f"Validation RMSE: {val_rmse:.2f} kg/ha")
        print(f"Validation MAE:   {val_mae:.2f} kg/ha")
        print(f"Validation R²:   {val_r2:.4f}")
        
        return self.model
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test targets
            
        Returns:
            Dictionary with evaluation metrics
        """
        print("\nEvaluating model on test set...")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Calculate percentage errors
        mape = np.mean(np.abs((y_test - y_pred) / (y_test + 1e-6))) * 100
        
        metrics = {
            'mse': float(mse),
            'rmse': float(rmse),
            'mae': float(mae),
            'r2_score': float(r2),
            'mape': float(mape),
        }
        
        # Print results
        print(f"\nTest Set Metrics:")
        print(f"  RMSE:  {rmse:.2f} kg/ha")
        print(f"  MAE:   {mae:.2f} kg/ha")
        print(f"  R²:    {r2:.4f}")
        print(f"  MAPE:  {mape:.2f}%")
        
        # Print some example predictions
        print(f"\nExample Predictions (first 10):")
        print("  Actual    Predicted   Error")
        print("  " + "-" * 35)
        for i in range(min(10, len(y_test))):
            error = y_test[i] - y_pred[i]
            print(f"  {y_test[i]:8.2f}  {y_pred[i]:8.2f}  {error:7.2f}")
        
        return metrics
    
    def save_model(self, metrics=None):
        """
        Save trained model and associated files.
        
        Args:
            metrics: Evaluation metrics to save
        """
        print("\nSaving model...")
        
        # Save model
        model_path = self.model_dir / 'yield_prediction_model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"  Model saved to: {model_path}")
        
        # Save scaler
        scaler_path = self.model_dir / 'yield_prediction_scaler.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"  Scaler saved to: {scaler_path}")
        
        # Save y_scaler
        y_scaler_path = self.model_dir / 'yield_prediction_y_scaler.pkl'
        with open(y_scaler_path, 'wb') as f:
            pickle.dump(self.y_scaler, f)
        print(f"  Y-Scaler saved to: {y_scaler_path}")
        
        # Save encoder
        encoder_path = self.model_dir / 'yield_prediction_encoder.pkl'
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.crop_encoder, f)
        print(f"  Encoder saved to: {encoder_path}")
        
        # Save metadata
        metadata_path = self.model_dir / 'yield_prediction_model_metadata.json'
        model_metadata = {
            'model_type': type(self.model).__name__,
            'n_features': self.metadata['n_features'],
            'feature_names': self.metadata['feature_names'],
            'yield_min': self.metadata['yield_min'],
            'yield_max': self.metadata['yield_max'],
            'yield_mean': self.metadata['yield_mean'],
            'yield_std': self.metadata['yield_std'],
        }
        
        if metrics:
            model_metadata['test_metrics'] = {
                'rmse': metrics['rmse'],
                'mae': metrics['mae'],
                'r2_score': metrics['r2_score'],
                'mape': metrics['mape'],
            }
        
        with open(metadata_path, 'w') as f:
            json.dump(model_metadata, f, indent=2)
        print(f"  Metadata saved to: {metadata_path}")
        
        # Save evaluation metrics
        if metrics:
            metrics_path = self.model_dir / 'yield_prediction_metrics.json'
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"  Metrics saved to: {metrics_path}")
    
    def predict(self, X):
        """
        Make predictions using trained model.
        
        Args:
            X: Features (already scaled)
            
        Returns:
            Predicted yields (in original scale)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = self.model.predict(X)
        
        # Inverse transform if y_scaler was used
        if self.y_scaler is not None:
            predictions = self.y_scaler.inverse_transform(predictions.reshape(-1, 1)).ravel()
        
        return predictions


def main():
    """Main training function."""
    print("=" * 60)
    print("Yield Prediction Model Training")
    print("=" * 60)
    
    trainer = YieldPredictionTrainer()
    
    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.load_data()
    
    # Train model (try both Random Forest and Gradient Boosting)
    print("\nTraining Random Forest model...")
    trainer.train(X_train, y_train, X_val, y_val, 
                  model_type='random_forest', n_estimators=100, max_depth=None)
    
    # Evaluate on test set
    metrics = trainer.evaluate(X_test, y_test)
    
    # Save model
    trainer.save_model(metrics)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"\nModel saved to: {trainer.model_dir}")
    print(f"Test RMSE: {metrics['rmse']:.2f} kg/ha")
    print(f"Test R²:   {metrics['r2_score']:.4f}")


if __name__ == '__main__':
    main()

