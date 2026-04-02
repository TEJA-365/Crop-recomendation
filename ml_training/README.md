# ML Training Module

This directory contains scripts and utilities for training ML models for crop recommendation and yield prediction.

## Directory Structure

```
ml_training/
├── data/              # Training datasets (raw and processed)
├── models/            # Trained ML models (to be saved here)
├── notebooks/         # Jupyter notebooks for exploration
└── scripts/           # Python scripts for data processing and training
    ├── collect_data.py              # Collect data from Django database
    ├── generate_synthetic_data.py   # Generate synthetic training data
    ├── preprocess_data.py           # Data preprocessing and feature engineering
    └── data_pipeline.py             # Main pipeline script
```

## Phase 3 Part 1: Data Collection and Preprocessing

### Overview

This phase focuses on collecting and preparing data for ML model training. The pipeline includes:

1. **Data Collection**: Extract data from Django database (soil, weather, crop history)
2. **Synthetic Data Generation**: Create realistic training data when real data is insufficient
3. **Data Preprocessing**: Clean, normalize, and engineer features
4. **Data Splitting**: Create train/validation/test splits

### Usage

#### Run Complete Pipeline

```bash
# From project root
python ml_training/scripts/data_pipeline.py
```

#### Options

```bash
# Skip real data collection (use only synthetic)
python ml_training/scripts/data_pipeline.py --no-real-data

# Skip synthetic data generation (use only real data)
python ml_training/scripts/data_pipeline.py --no-synthetic-data

# Customize parameters
python ml_training/scripts/data_pipeline.py \
    --min-samples 200 \
    --synthetic-samples 100 \
    --output-dir /path/to/output
```

#### Run Individual Steps

```bash
# Step 1: Collect real data
python ml_training/scripts/collect_data.py

# Step 2: Generate synthetic data
python ml_training/scripts/generate_synthetic_data.py

# Step 3: Preprocess data
python ml_training/scripts/preprocess_data.py
```

### Output Files

After running the pipeline, you'll find:

#### Raw Data
- `crop_recommendation_raw.csv` - Raw crop recommendation data
- `crop_recommendation_synthetic.csv` - Synthetic crop recommendation data
- `yield_prediction_raw.csv` - Raw yield prediction data
- `yield_prediction_synthetic.csv` - Synthetic yield prediction data

#### Processed Data
- `crop_recommendation_X_train.npy` - Training features
- `crop_recommendation_X_val.npy` - Validation features
- `crop_recommendation_X_test.npy` - Test features
- `crop_recommendation_y_train.npy` - Training labels
- `crop_recommendation_y_val.npy` - Validation labels
- `crop_recommendation_y_test.npy` - Test labels
- `crop_recommendation_scaler.pkl` - Feature scaler
- `crop_recommendation_encoder.pkl` - Label encoder
- `crop_recommendation_metadata.json` - Dataset metadata

Similar files for yield prediction with `yield_prediction_` prefix.

### Data Features

#### Crop Recommendation Features
- **Soil Properties**: pH, moisture, N, P, K content
- **Weather**: Temperature, rainfall, humidity
- **Location**: Latitude, longitude (normalized)
- **Engineered Features**:
  - Nutrient ratios (N/P, N/K, P/K)
  - Total nutrients
  - pH categories (acidic, neutral, alkaline)
  - Temperature categories
  - Rainfall categories
  - Nutrient sufficiency indicators

#### Yield Prediction Features
- All features from crop recommendation
- **Crop Type**: Encoded crop name
- **Target**: Yield achieved (kg/hectare)

### Data Statistics

After preprocessing, check the metadata files for:
- Number of samples (train/val/test)
- Number of features
- Number of classes (for classification)
- Feature names
- Class names (for classification)
- Yield statistics (for regression)

### Phase 3 Part 2: Model Training

### Overview

After preprocessing data, train ML models for:
1. **Crop Recommendation** (Classification)
2. **Yield Prediction** (Regression)

### Usage

#### Train Both Models

```bash
python ml_training/scripts/train_models.py
```

#### Train Individual Models

```bash
# Crop recommendation only
python ml_training/scripts/train_crop_recommendation.py

# Yield prediction only
python ml_training/scripts/train_yield_prediction.py
```

#### Load Models for Inference

```python
from ml_training.scripts.load_models import ModelLoader

loader = ModelLoader()
crop_model = loader.load_crop_recommendation_model()
yield_model = loader.load_yield_prediction_model()
```

### Model Files

After training, models are saved to `ml_training/models/`:
- `crop_recommendation_model.pkl` - Trained classifier
- `yield_prediction_model.pkl` - Trained regressor
- `*_scaler.pkl` - Feature scalers
- `*_encoder.pkl` - Label encoders
- `*_metadata.json` - Model metadata
- `*_metrics.json` - Evaluation metrics

### Evaluation Metrics

**Crop Recommendation**:
- Accuracy, Precision, Recall, F1 Score
- Per-class metrics
- Confusion matrix

**Yield Prediction**:
- RMSE, MAE, R² Score, MAPE
- Example predictions

## Next Steps

After completing model training:

1. **Review Model Performance**: Check evaluation metrics
2. **Phase 3 Part 3**: Integrate models with Django
3. **Update Recommendation Service**: Use ML models instead of rule-based logic
4. **Test End-to-End**: Verify predictions work correctly

## Requirements

### Python Packages

Make sure you have the required packages installed:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install all requirements (includes pandas, numpy, scikit-learn)
pip install -r requirements.txt
```

Or install just the ML training dependencies:

```bash
pip install pandas numpy scikit-learn
```

### Verify Setup

Check if all packages are installed:

```bash
python ml_training/scripts/verify_setup.py
```

### Django Setup

For running the data collection script, Django must be set up:

```bash
# Ensure Django is configured
python manage.py check
```

## Notes

- Synthetic data is generated based on known crop requirements from the recommendation service
- Real data is collected from Django models (Field, CropHistory, SoilData, WeatherData)
- Data is automatically cleaned and validated
- Missing values are handled with reasonable defaults
- Features are scaled using StandardScaler for better model performance
- Train/val/test splits use stratification for classification tasks

