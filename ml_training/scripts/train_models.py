"""
Main training pipeline for Phase 3 Part 2: Model Training.

This script orchestrates training of both:
1. Crop Recommendation Model (classification)
2. Yield Prediction Model (regression)
"""

import sys
from pathlib import Path

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from ml_training.scripts.train_crop_recommendation import CropRecommendationTrainer
from ml_training.scripts.train_yield_prediction import YieldPredictionTrainer


def train_crop_recommendation_model(data_dir=None, model_dir=None, **kwargs):
    """
    Train crop recommendation model.
    
    Args:
        data_dir: Directory with preprocessed data
        model_dir: Directory to save models
        **kwargs: Additional training parameters
    """
    print("\n" + "=" * 60)
    print("Training Crop Recommendation Model")
    print("=" * 60)
    
    trainer = CropRecommendationTrainer(data_dir=data_dir, model_dir=model_dir)
    
    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.load_data()
    
    # Train model
    n_estimators = kwargs.get('n_estimators', 100)
    max_depth = kwargs.get('max_depth', None)
    trainer.train(X_train, y_train, X_val, y_val, 
                  n_estimators=n_estimators, max_depth=max_depth)
    
    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)
    
    # Save
    trainer.save_model(metrics)
    
    return trainer, metrics


def train_yield_prediction_model(data_dir=None, model_dir=None, **kwargs):
    """
    Train yield prediction model.
    
    Args:
        data_dir: Directory with preprocessed data
        model_dir: Directory to save models
        **kwargs: Additional training parameters
    """
    print("\n" + "=" * 60)
    print("Training Yield Prediction Model")
    print("=" * 60)
    
    trainer = YieldPredictionTrainer(data_dir=data_dir, model_dir=model_dir)
    
    # Load data
    X_train, X_val, X_test, y_train, y_val, y_test = trainer.load_data()
    
    # Train model
    model_type = kwargs.get('model_type', 'random_forest')
    n_estimators = kwargs.get('n_estimators', 100)
    max_depth = kwargs.get('max_depth', None)
    trainer.train(X_train, y_train, X_val, y_val,
                  model_type=model_type, n_estimators=n_estimators, max_depth=max_depth)
    
    # Evaluate
    metrics = trainer.evaluate(X_test, y_test)
    
    # Save
    trainer.save_model(metrics)
    
    return trainer, metrics


def main():
    """Main training pipeline."""
    print("=" * 60)
    print("Phase 3 Part 2: ML Model Training Pipeline")
    print("=" * 60)
    
    # Check if preprocessed data exists
    data_dir = BASE_DIR / 'ml_training' / 'data'
    model_dir = BASE_DIR / 'ml_training' / 'models'
    
    # Check for required data files
    required_files = [
        'crop_recommendation_X_train.npy',
        'yield_prediction_X_train.npy',
    ]
    
    missing_files = []
    for file in required_files:
        if not (data_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("\n⚠️  Error: Preprocessed data not found!")
        print("Missing files:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPlease run data preprocessing first:")
        print("  python ml_training/scripts/data_pipeline.py")
        return
    
    # Train crop recommendation model
    try:
        crop_trainer, crop_metrics = train_crop_recommendation_model(
            data_dir=data_dir,
            model_dir=model_dir
        )
        print("\n✓ Crop recommendation model training complete!")
        print(f"  Test Accuracy: {crop_metrics['accuracy']:.4f}")
    except Exception as e:
        print(f"\n✗ Error training crop recommendation model: {e}")
        import traceback
        traceback.print_exc()
        crop_trainer = None
        crop_metrics = None
    
    # Train yield prediction model
    try:
        yield_trainer, yield_metrics = train_yield_prediction_model(
            data_dir=data_dir,
            model_dir=model_dir
        )
        print("\n✓ Yield prediction model training complete!")
        print(f"  Test RMSE: {yield_metrics['rmse']:.2f} kg/ha")
        print(f"  Test R²:   {yield_metrics['r2_score']:.4f}")
    except Exception as e:
        print(f"\n✗ Error training yield prediction model: {e}")
        import traceback
        traceback.print_exc()
        yield_trainer = None
        yield_metrics = None
    
    # Summary
    print("\n" + "=" * 60)
    print("Training Pipeline Summary")
    print("=" * 60)
    
    if crop_trainer:
        print("\n✓ Crop Recommendation Model:")
        print(f"  - Model saved to: {model_dir / 'crop_recommendation_model.pkl'}")
        if crop_metrics:
            print(f"  - Accuracy: {crop_metrics['accuracy']:.4f}")
            print(f"  - F1 Score: {crop_metrics['f1_score']:.4f}")
    
    if yield_trainer:
        print("\n✓ Yield Prediction Model:")
        print(f"  - Model saved to: {model_dir / 'yield_prediction_model.pkl'}")
        if yield_metrics:
            print(f"  - RMSE: {yield_metrics['rmse']:.2f} kg/ha")
            print(f"  - R²:   {yield_metrics['r2_score']:.4f}")
    
    print("\n" + "=" * 60)
    print("Phase 3 Part 2: Model Training - COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review model performance metrics")
    print("2. Proceed to Phase 3 Part 3: Model Integration")
    print("3. Update recommendation service to use ML models")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML models for crop recommendation')
    parser.add_argument(
        '--crop-only',
        action='store_true',
        help='Train only crop recommendation model'
    )
    parser.add_argument(
        '--yield-only',
        action='store_true',
        help='Train only yield prediction model'
    )
    parser.add_argument(
        '--n-estimators',
        type=int,
        default=100,
        help='Number of estimators for tree-based models (default: 100)'
    )
    parser.add_argument(
        '--max-depth',
        type=int,
        default=None,
        help='Maximum depth of trees (default: None)'
    )
    parser.add_argument(
        '--model-type',
        type=str,
        default='random_forest',
        choices=['random_forest', 'gradient_boosting'],
        help='Model type for yield prediction (default: random_forest)'
    )
    
    args = parser.parse_args()
    
    if args.crop_only:
        data_dir = BASE_DIR / 'ml_training' / 'data'
        model_dir = BASE_DIR / 'ml_training' / 'models'
        train_crop_recommendation_model(
            data_dir=data_dir,
            model_dir=model_dir,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth
        )
    elif args.yield_only:
        data_dir = BASE_DIR / 'ml_training' / 'data'
        model_dir = BASE_DIR / 'ml_training' / 'models'
        train_yield_prediction_model(
            data_dir=data_dir,
            model_dir=model_dir,
            model_type=args.model_type,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth
        )
    else:
        main()

