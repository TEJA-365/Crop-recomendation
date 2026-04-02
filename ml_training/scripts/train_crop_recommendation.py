"""
Train crop recommendation model (classification).

This script trains a multi-class classification model to recommend crops
based on soil properties, weather conditions, and location.
"""

import numpy as np
import pickle
import json
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, classification_report, confusion_matrix,
    precision_score, recall_score, f1_score
)
import sys

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))


class CropRecommendationTrainer:
    """Trainer for crop recommendation classification model."""
    
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
        self.label_encoder = None
        self.metadata = None
    
    def load_data(self):
        """Load preprocessed training data."""
        print("Loading preprocessed data...")
        
        # Load features and labels
        X_train = np.load(self.data_dir / 'crop_recommendation_X_train.npy')
        X_val = np.load(self.data_dir / 'crop_recommendation_X_val.npy')
        X_test = np.load(self.data_dir / 'crop_recommendation_X_test.npy')
        
        y_train = np.load(self.data_dir / 'crop_recommendation_y_train.npy')
        y_val = np.load(self.data_dir / 'crop_recommendation_y_val.npy')
        y_test = np.load(self.data_dir / 'crop_recommendation_y_test.npy')
        
        # Load scaler and encoder
        with open(self.data_dir / 'crop_recommendation_scaler.pkl', 'rb') as f:
            self.scaler = pickle.load(f)
        
        with open(self.data_dir / 'crop_recommendation_encoder.pkl', 'rb') as f:
            self.label_encoder = pickle.load(f)
        
        # Load metadata
        with open(self.data_dir / 'crop_recommendation_metadata.json', 'r') as f:
            self.metadata = json.load(f)
        
        print(f"Training samples: {len(X_train)}")
        print(f"Validation samples: {len(X_val)}")
        print(f"Test samples: {len(X_test)}")
        print(f"Features: {self.metadata['n_features']}")
        print(f"Classes: {self.metadata['n_classes']}")
        
        return (X_train, X_val, X_test, y_train, y_val, y_test)
    
    def train(self, X_train, y_train, X_val, y_val, n_estimators=100, max_depth=None, random_state=42):
        """
        Train Random Forest classifier.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            n_estimators: Number of trees in the forest
            max_depth: Maximum depth of trees
            random_state: Random seed
            
        Returns:
            Trained model
        """
        print("\nTraining Random Forest Classifier...")
        print(f"Parameters: n_estimators={n_estimators}, max_depth={max_depth}")
        
        # Create and train model
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            n_jobs=-1,  # Use all available cores
            class_weight='balanced'  # Handle class imbalance
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation set
        y_val_pred = self.model.predict(X_val)
        val_accuracy = accuracy_score(y_val, y_val_pred)
        
        print(f"Validation Accuracy: {val_accuracy:.4f}")
        
        return self.model
    
    def evaluate(self, X_test, y_test):
        """
        Evaluate model on test set.
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Dictionary with evaluation metrics
        """
        print("\nEvaluating model on test set...")
        
        # Predictions
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        # Per-class metrics
        class_names = self.label_encoder.classes_
        report = classification_report(
            y_test, y_pred,
            target_names=class_names,
            output_dict=True,
            zero_division=0
        )
        
        # Confusion matrix
        cm = confusion_matrix(y_test, y_pred)
        
        metrics = {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
        }
        
        # Print results
        print(f"\nTest Set Metrics:")
        print(f"  Accuracy:  {accuracy:.4f}")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        
        print(f"\nPer-Class Performance:")
        for class_name in class_names:
            if class_name in report:
                class_metrics = report[class_name]
                print(f"  {class_name}:")
                print(f"    Precision: {class_metrics['precision']:.4f}")
                print(f"    Recall:    {class_metrics['recall']:.4f}")
                print(f"    F1:        {class_metrics['f1-score']:.4f}")
        
        return metrics
    
    def save_model(self, metrics=None):
        """
        Save trained model and associated files.
        
        Args:
            metrics: Evaluation metrics to save
        """
        print("\nSaving model...")
        
        # Save model
        model_path = self.model_dir / 'crop_recommendation_model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"  Model saved to: {model_path}")
        
        # Save scaler
        scaler_path = self.model_dir / 'crop_recommendation_scaler.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(self.scaler, f)
        print(f"  Scaler saved to: {scaler_path}")
        
        # Save encoder
        encoder_path = self.model_dir / 'crop_recommendation_encoder.pkl'
        with open(encoder_path, 'wb') as f:
            pickle.dump(self.label_encoder, f)
        print(f"  Encoder saved to: {encoder_path}")
        
        # Save metadata
        metadata_path = self.model_dir / 'crop_recommendation_model_metadata.json'
        model_metadata = {
            'model_type': 'RandomForestClassifier',
            'n_features': self.metadata['n_features'],
            'n_classes': self.metadata['n_classes'],
            'feature_names': self.metadata['feature_names'],
            'class_names': self.metadata['class_names'],
        }
        
        if metrics:
            model_metadata['test_metrics'] = {
                'accuracy': metrics['accuracy'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
            }
        
        with open(metadata_path, 'w') as f:
            json.dump(model_metadata, f, indent=2)
        print(f"  Metadata saved to: {metadata_path}")
        
        # Save evaluation metrics
        if metrics:
            metrics_path = self.model_dir / 'crop_recommendation_metrics.json'
            # Remove confusion matrix and full report for cleaner JSON
            metrics_to_save = {
                'accuracy': metrics['accuracy'],
                'precision': metrics['precision'],
                'recall': metrics['recall'],
                'f1_score': metrics['f1_score'],
                'classification_report': metrics['classification_report'],
            }
            with open(metrics_path, 'w') as f:
                json.dump(metrics_to_save, f, indent=2)
            print(f"  Metrics saved to: {metrics_path}")
    
    def predict(self, X):
        """
        Make predictions using trained model.
        
        Args:
            X: Features (already scaled)
            
        Returns:
            Tuple of (predictions, probabilities)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)
        
        # Decode labels
        crop_names = self.label_encoder.inverse_transform(predictions)
        
        return crop_names, probabilities


def main():
    """Main training function."""
    print("=" * 60)
    print("Crop Recommendation Model Training")
    print("=" * 60)
    
    trainer = CropRecommendationTrainer()
    
    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.load_data()
    
    # Train model
    trainer.train(X_train, y_train, X_val, y_val, n_estimators=100, max_depth=None)
    
    # Evaluate on test set
    metrics = trainer.evaluate(X_test, y_test)
    
    # Save model
    trainer.save_model(metrics)
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"\nModel saved to: {trainer.model_dir}")
    print(f"Test Accuracy: {metrics['accuracy']:.4f}")


if __name__ == '__main__':
    main()

