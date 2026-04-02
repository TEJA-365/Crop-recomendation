"""
Main data pipeline script for Phase 3 Part 1: Data Collection and Preprocessing.

This script orchestrates the entire data collection and preprocessing pipeline:
1. Collects data from Django database (if available)
2. Generates synthetic data (if real data is insufficient)
3. Preprocesses and cleans the data
4. Creates train/val/test splits
5. Saves processed datasets ready for ML model training
"""

import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from ml_training.scripts.collect_data import DataCollector
from ml_training.scripts.generate_synthetic_data import SyntheticDataGenerator
from ml_training.scripts.preprocess_data import DataPreprocessor


def run_data_pipeline(
    use_real_data=True,
    use_synthetic_data=True,
    min_real_samples=100,
    synthetic_samples_per_crop=50,
    output_dir=None
):
    """
    Run the complete data collection and preprocessing pipeline.
    
    Args:
        use_real_data: Whether to collect data from Django database
        use_synthetic_data: Whether to generate synthetic data
        min_real_samples: Minimum number of real samples required
        synthetic_samples_per_crop: Number of synthetic samples per crop
        output_dir: Directory to save all data
    """
    print("=" * 60)
    print("Phase 3 Part 1: Data Collection and Preprocessing Pipeline")
    print("=" * 60)
    print()
    
    if output_dir is None:
        output_dir = BASE_DIR / 'ml_training' / 'data'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Collect real data from database
    crop_recommendation_df = None
    yield_prediction_df = None
    
    if use_real_data:
        print("Step 1: Collecting real data from database...")
        print("-" * 60)
        try:
            collector = DataCollector(output_dir=output_dir)
            
            # Collect crop recommendation data
            crop_recommendation_df = collector.collect_crop_recommendation_data(
                min_samples=min_real_samples
            )
            
            # Collect yield prediction data
            yield_prediction_df = collector.collect_yield_prediction_data()
            
            print("\nReal data collection complete!")
            
        except Exception as e:
            print(f"Error collecting real data: {e}")
            print("Will proceed with synthetic data generation...")
            crop_recommendation_df = None
            yield_prediction_df = None
    
    # Step 2: Generate synthetic data if needed
    if use_synthetic_data:
        print("\nStep 2: Generating synthetic data...")
        print("-" * 60)
        
        generator = SyntheticDataGenerator(output_dir=output_dir)
        
        # Generate synthetic crop recommendation data
        if crop_recommendation_df is None or len(crop_recommendation_df) < min_real_samples:
            print("Generating synthetic crop recommendation data...")
            synthetic_crop_df = generator.generate_crop_recommendation_dataset(
                n_samples_per_crop=synthetic_samples_per_crop
            )
            
            # Combine with real data if available
            if crop_recommendation_df is not None and len(crop_recommendation_df) > 0:
                print("Combining real and synthetic data...")
                crop_recommendation_df = pd.concat(
                    [crop_recommendation_df, synthetic_crop_df],
                    ignore_index=True
                )
                print(f"Combined dataset: {len(crop_recommendation_df)} samples")
            else:
                crop_recommendation_df = synthetic_crop_df
        else:
            print(f"Sufficient real data available ({len(crop_recommendation_df)} samples)")
        
        # Generate synthetic yield prediction data
        if yield_prediction_df is None or len(yield_prediction_df) < min_real_samples:
            print("\nGenerating synthetic yield prediction data...")
            synthetic_yield_df = generator.generate_yield_prediction_dataset(
                n_samples_per_crop=synthetic_samples_per_crop
            )
            
            # Combine with real data if available
            if yield_prediction_df is not None and len(yield_prediction_df) > 0:
                print("Combining real and synthetic data...")
                yield_prediction_df = pd.concat(
                    [yield_prediction_df, synthetic_yield_df],
                    ignore_index=True
                )
                print(f"Combined dataset: {len(yield_prediction_df)} samples")
            else:
                yield_prediction_df = synthetic_yield_df
        else:
            print(f"Sufficient real data available ({len(yield_prediction_df)} samples)")
    
    # Step 3: Preprocess data
    print("\nStep 3: Preprocessing data...")
    print("-" * 60)
    
    preprocessor = DataPreprocessor(output_dir=output_dir)
    
    # Preprocess crop recommendation data
    if crop_recommendation_df is not None and len(crop_recommendation_df) > 0:
        print("\nPreprocessing crop recommendation data...")
        try:
            crop_processed = preprocessor.prepare_crop_recommendation_data(
                crop_recommendation_df
            )
            preprocessor.save_processed_data(
                crop_processed,
                prefix='crop_recommendation'
            )
            print("✓ Crop recommendation data preprocessing complete!")
        except Exception as e:
            print(f"Error preprocessing crop recommendation data: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ No crop recommendation data to preprocess")
    
    # Preprocess yield prediction data
    if yield_prediction_df is not None and len(yield_prediction_df) > 0:
        print("\nPreprocessing yield prediction data...")
        try:
            yield_processed = preprocessor.prepare_yield_prediction_data(
                yield_prediction_df
            )
            preprocessor.save_processed_data(
                yield_processed,
                prefix='yield_prediction'
            )
            print("✓ Yield prediction data preprocessing complete!")
        except Exception as e:
            print(f"Error preprocessing yield prediction data: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠ No yield prediction data to preprocess")
    
    # Summary
    print("\n" + "=" * 60)
    print("Pipeline Summary")
    print("=" * 60)
    
    if crop_recommendation_df is not None:
        print(f"✓ Crop Recommendation Dataset: {len(crop_recommendation_df)} samples")
        print(f"  - Processed and ready for training")
        print(f"  - Files saved in: {output_dir}")
    
    if yield_prediction_df is not None:
        print(f"✓ Yield Prediction Dataset: {len(yield_prediction_df)} samples")
        print(f"  - Processed and ready for training")
        print(f"  - Files saved in: {output_dir}")
    
    print("\n" + "=" * 60)
    print("Phase 3 Part 1: Data Collection and Preprocessing - COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the processed data in:", output_dir)
    print("2. Proceed to Phase 3 Part 2: Model Training")
    print("3. Use the preprocessed data to train ML models")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run data collection and preprocessing pipeline'
    )
    parser.add_argument(
        '--no-real-data',
        action='store_true',
        help='Skip collecting real data from database'
    )
    parser.add_argument(
        '--no-synthetic-data',
        action='store_true',
        help='Skip generating synthetic data'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=100,
        help='Minimum number of real samples required (default: 100)'
    )
    parser.add_argument(
        '--synthetic-samples',
        type=int,
        default=50,
        help='Number of synthetic samples per crop (default: 50)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for processed data'
    )
    
    args = parser.parse_args()
    
    run_data_pipeline(
        use_real_data=not args.no_real_data,
        use_synthetic_data=not args.no_synthetic_data,
        min_real_samples=args.min_samples,
        synthetic_samples_per_crop=args.synthetic_samples,
        output_dir=args.output_dir
    )

