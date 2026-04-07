#!/usr/bin/env python
"""
Complete test script for AI/ML recommendations
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crop_recommendation.settings')
django.setup()

from apps.recommendations.ml_service import get_ml_service
from apps.recommendations.services import CropRecommendationService

print("=" * 60)
print("Testing AI/ML Crop Recommendations")
print("=" * 60)

# Test 1: Check if models are loaded
print("\n1. Checking ML Models...")
ml_service = get_ml_service()
crop_loaded = ml_service.crop_model_data is not None
yield_loaded = ml_service.yield_model_data is not None

print(f"   Crop Recommendation Model: {'✅ Loaded' if crop_loaded else '❌ Not loaded'}")
print(f"   Yield Prediction Model: {'✅ Loaded' if yield_loaded else '❌ Not loaded'}")

if not (crop_loaded and yield_loaded):
    print("\n⚠️  Models not loaded. Train models first:")
    print("   python ml_training/scripts/train_models.py")
    exit(1)

# Test 2: Test crop recommendations
print("\n2. Testing Crop Recommendations...")
recommendations = CropRecommendationService.get_recommendations(
    soil_ph=6.5,
    soil_n=120,
    soil_p=30,
    soil_k=50,
    soil_moisture=60,
    temperature=25,
    rainfall=600,
    humidity=70,
    latitude=20.0,
    longitude=77.0,
    limit=5
)

using_ml = any(rec.get('ml_prediction', False) for rec in recommendations)
print(f"   Using ML Models: {'✅ Yes' if using_ml else '❌ No (rule-based)'}")

print("\n   Top 5 Recommendations:")
for i, rec in enumerate(recommendations[:5], 1):
    ml_indicator = "🤖" if rec.get('ml_prediction', False) else "📋"
    print(f"   {i}. {ml_indicator} {rec['crop_name']}")
    print(f"      Confidence: {rec['confidence_score']:.2f}%")
    print(f"      Yield: {rec['expected_yield']:.2f} kg/ha")
    print(f"      Profit: ₹{rec['profit_margin']:.2f}")

# Test 3: Test yield prediction
print("\n3. Testing Yield Predictions...")
test_crops = ['Rice', 'Wheat', 'Maize']
for crop in test_crops:
    yield_pred = ml_service.predict_yield(
        crop_name=crop,
        soil_ph=6.5,
        soil_n=120,
        soil_p=30,
        soil_k=50,
        soil_moisture=60,
        temperature=25,
        rainfall=600,
        humidity=70
    )
    print(f"   {crop}: {yield_pred:.2f} kg/ha")

print("\n" + "=" * 60)
print("✅ Testing Complete!")
print("=" * 60)
