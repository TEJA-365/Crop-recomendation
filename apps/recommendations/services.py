"""
Recommendation service for crop recommendations.
Uses ML models when available, falls back to rule-based logic.
Enhanced with sophisticated business logic for Phase 4.
"""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import ML service
try:
    from .ml_service import get_ml_service
    ML_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    ML_AVAILABLE = False
    logger.debug(f"ML service not available: {e}. Using rule-based recommendations only.")

# Import enhanced business logic
try:
    from .business_logic import (
        CropRotationAnalyzer,
        ProfitCalculator,
        SustainabilityScorer,
        RecommendationRanker
    )
    BUSINESS_LOGIC_AVAILABLE = True
except ImportError as e:
    BUSINESS_LOGIC_AVAILABLE = False
    logger.warning(f"Enhanced business logic not available: {e}. Using basic logic.")


class CropRecommendationService:
    """Service for generating crop recommendations based on soil and weather data."""
    
    # Crop requirements database
    # Format: crop_name: {requirements}
    CROP_REQUIREMENTS = {
        'Rice': {
            'ph_min': 5.0,
            'ph_max': 7.5,
            'n_min': 100,
            'p_min': 20,
            'k_min': 40,
            'moisture_min': 60,
            'temperature_min': 20,
            'temperature_max': 35,
            'rainfall_min': 1000,
            'season': ['kharif'],
            'sustainability_score': 75,
        },
        'Wheat': {
            'ph_min': 6.0,
            'ph_max': 7.5,
            'n_min': 120,
            'p_min': 30,
            'k_min': 50,
            'moisture_min': 40,
            'temperature_min': 15,
            'temperature_max': 25,
            'rainfall_min': 500,
            'season': ['rabi'],
            'sustainability_score': 80,
        },
        'Maize': {
            'ph_min': 5.5,
            'ph_max': 7.0,
            'n_min': 150,
            'p_min': 25,
            'k_min': 60,
            'moisture_min': 50,
            'temperature_min': 18,
            'temperature_max': 30,
            'rainfall_min': 600,
            'season': ['kharif', 'zaid'],
            'sustainability_score': 70,
        },
        'Cotton': {
            'ph_min': 5.5,
            'ph_max': 8.0,
            'n_min': 80,
            'p_min': 20,
            'k_min': 50,
            'moisture_min': 50,
            'temperature_min': 21,
            'temperature_max': 35,
            'rainfall_min': 500,
            'season': ['kharif'],
            'sustainability_score': 65,
        },
        'Sugarcane': {
            'ph_min': 6.0,
            'ph_max': 7.5,
            'n_min': 200,
            'p_min': 40,
            'k_min': 100,
            'moisture_min': 70,
            'temperature_min': 20,
            'temperature_max': 35,
            'rainfall_min': 1200,
            'season': ['year_round'],
            'sustainability_score': 60,
        },
        'Potato': {
            'ph_min': 4.8,
            'ph_max': 5.5,
            'n_min': 100,
            'p_min': 50,
            'k_min': 150,
            'moisture_min': 60,
            'temperature_min': 15,
            'temperature_max': 25,
            'rainfall_min': 500,
            'season': ['rabi', 'zaid'],
            'sustainability_score': 75,
        },
        'Tomato': {
            'ph_min': 6.0,
            'ph_max': 7.0,
            'n_min': 120,
            'p_min': 40,
            'k_min': 120,
            'moisture_min': 60,
            'temperature_min': 18,
            'temperature_max': 28,
            'rainfall_min': 400,
            'season': ['year_round'],
            'sustainability_score': 70,
        },
        'Onion': {
            'ph_min': 6.0,
            'ph_max': 7.0,
            'n_min': 100,
            'p_min': 30,
            'k_min': 80,
            'moisture_min': 50,
            'temperature_min': 13,
            'temperature_max': 25,
            'rainfall_min': 400,
            'season': ['rabi', 'kharif'],
            'sustainability_score': 75,
        },
        'Chilli': {
            'ph_min': 6.0,
            'ph_max': 7.0,
            'n_min': 100,
            'p_min': 30,
            'k_min': 100,
            'moisture_min': 50,
            'temperature_min': 20,
            'temperature_max': 30,
            'rainfall_min': 400,
            'season': ['kharif', 'rabi'],
            'sustainability_score': 70,
        },
        'Groundnut': {
            'ph_min': 6.0,
            'ph_max': 7.5,
            'n_min': 20,
            'p_min': 20,
            'k_min': 40,
            'moisture_min': 40,
            'temperature_min': 20,
            'temperature_max': 35,
            'rainfall_min': 500,
            'season': ['kharif', 'rabi'],
            'sustainability_score': 80,
        },
        'Soybean': {
            'ph_min': 6.0,
            'ph_max': 7.0,
            'n_min': 20,
            'p_min': 30,
            'k_min': 50,
            'moisture_min': 50,
            'temperature_min': 20,
            'temperature_max': 30,
            'rainfall_min': 600,
            'season': ['kharif'],
            'sustainability_score': 85,
        },
        'Pigeon Pea': {
            'ph_min': 6.0,
            'ph_max': 7.5,
            'n_min': 20,
            'p_min': 20,
            'k_min': 30,
            'moisture_min': 40,
            'temperature_min': 20,
            'temperature_max': 35,
            'rainfall_min': 600,
            'season': ['kharif'],
            'sustainability_score': 90,
        },
    }
    
    # Average yield in kg/hectare (can be improved with ML)
    AVERAGE_YIELDS = {
        'Rice': 3000,
        'Wheat': 3500,
        'Maize': 4000,
        'Cotton': 500,
        'Sugarcane': 70000,
        'Potato': 25000,
        'Tomato': 30000,
        'Onion': 20000,
        'Chilli': 15000,
        'Groundnut': 2000,
        'Soybean': 2500,
        'Pigeon Pea': 1200,
    }
    
    # Average profit per hectare (in local currency - approximate)
    AVERAGE_PROFITS = {
        'Rice': 50000,
        'Wheat': 60000,
        'Maize': 55000,
        'Cotton': 80000,
        'Sugarcane': 150000,
        'Potato': 200000,
        'Tomato': 250000,
        'Onion': 180000,
        'Chilli': 200000,
        'Groundnut': 70000,
        'Soybean': 60000,
        'Pigeon Pea': 50000,
    }
    
    @classmethod
    def get_current_season(cls) -> str:
        """Determine current season based on date."""
        month = timezone.now().month
        if month in [6, 7, 8, 9, 10]:  # June to October
            return 'kharif'
        elif month in [11, 12, 1, 2, 3]:  # November to March
            return 'rabi'
        else:  # April, May
            return 'zaid'
    
    @classmethod
    def calculate_compatibility_score(
        cls,
        crop: str,
        soil_ph: Optional[float],
        soil_n: Optional[float],
        soil_p: Optional[float],
        soil_k: Optional[float],
        soil_moisture: Optional[float],
        temperature: Optional[float],
        rainfall: Optional[float],
        season: Optional[str] = None
    ) -> Dict:
        """
        Calculate compatibility score for a crop based on conditions.
        
        Returns:
            Dictionary with score, reasons, and match details
        """
        if crop not in cls.CROP_REQUIREMENTS:
            return {
                'score': 0,
                'reasons': ['Crop not in database'],
                'match_details': {}
            }
        
        requirements = cls.CROP_REQUIREMENTS[crop]
        score = 100
        reasons = []
        match_details = {}
        
        # Check pH
        if soil_ph is not None:
            ph_min = requirements['ph_min']
            ph_max = requirements['ph_max']
            if ph_min <= soil_ph <= ph_max:
                match_details['ph'] = 'optimal'
            elif abs(soil_ph - ph_min) < 0.5 or abs(soil_ph - ph_max) < 0.5:
                score -= 10
                match_details['ph'] = 'acceptable'
                reasons.append(f'pH ({soil_ph}) slightly outside optimal range ({ph_min}-{ph_max})')
            else:
                score -= 30
                match_details['ph'] = 'poor'
                reasons.append(f'pH ({soil_ph}) outside optimal range ({ph_min}-{ph_max})')
        else:
            score -= 5
            match_details['ph'] = 'unknown'
        
        # Check nutrients
        if soil_n is not None:
            n_min = requirements['n_min']
            if soil_n >= n_min:
                match_details['n'] = 'sufficient'
            elif soil_n >= n_min * 0.7:
                score -= 5
                match_details['n'] = 'low'
                reasons.append(f'Nitrogen ({soil_n} kg/ha) below optimal ({n_min} kg/ha)')
            else:
                score -= 15
                match_details['n'] = 'deficient'
                reasons.append(f'Nitrogen ({soil_n} kg/ha) significantly below optimal ({n_min} kg/ha)')
        else:
            score -= 3
            match_details['n'] = 'unknown'
        
        if soil_p is not None:
            p_min = requirements['p_min']
            if soil_p >= p_min:
                match_details['p'] = 'sufficient'
            elif soil_p >= p_min * 0.7:
                score -= 5
                match_details['p'] = 'low'
                reasons.append(f'Phosphorus ({soil_p} kg/ha) below optimal ({p_min} kg/ha)')
            else:
                score -= 15
                match_details['p'] = 'deficient'
                reasons.append(f'Phosphorus ({soil_p} kg/ha) significantly below optimal ({p_min} kg/ha)')
        else:
            score -= 3
            match_details['p'] = 'unknown'
        
        if soil_k is not None:
            k_min = requirements['k_min']
            if soil_k >= k_min:
                match_details['k'] = 'sufficient'
            elif soil_k >= k_min * 0.7:
                score -= 5
                match_details['k'] = 'low'
                reasons.append(f'Potassium ({soil_k} kg/ha) below optimal ({k_min} kg/ha)')
            else:
                score -= 15
                match_details['k'] = 'deficient'
                reasons.append(f'Potassium ({soil_k} kg/ha) significantly below optimal ({k_min} kg/ha)')
        else:
            score -= 3
            match_details['k'] = 'unknown'
        
        # Check moisture
        if soil_moisture is not None:
            moisture_min = requirements['moisture_min']
            if soil_moisture >= moisture_min:
                match_details['moisture'] = 'sufficient'
            elif soil_moisture >= moisture_min * 0.8:
                score -= 5
                match_details['moisture'] = 'low'
                reasons.append(f'Moisture ({soil_moisture}%) below optimal ({moisture_min}%)')
            else:
                score -= 10
                match_details['moisture'] = 'deficient'
                reasons.append(f'Moisture ({soil_moisture}%) significantly below optimal ({moisture_min}%)')
        else:
            score -= 3
            match_details['moisture'] = 'unknown'
        
        # Check temperature
        if temperature is not None:
            temp_min = requirements['temperature_min']
            temp_max = requirements['temperature_max']
            if temp_min <= temperature <= temp_max:
                match_details['temperature'] = 'optimal'
            elif abs(temperature - temp_min) < 3 or abs(temperature - temp_max) < 3:
                score -= 5
                match_details['temperature'] = 'acceptable'
                reasons.append(f'Temperature ({temperature}°C) slightly outside optimal range ({temp_min}-{temp_max}°C)')
            else:
                score -= 15
                match_details['temperature'] = 'poor'
                reasons.append(f'Temperature ({temperature}°C) outside optimal range ({temp_min}-{temp_max}°C)')
        else:
            score -= 3
            match_details['temperature'] = 'unknown'
        
        # Check season
        if season is None:
            season = cls.get_current_season()
        
        if season in requirements['season'] or 'year_round' in requirements['season']:
            match_details['season'] = 'suitable'
        else:
            score -= 20
            match_details['season'] = 'unsuitable'
            reasons.append(f'Current season ({season}) not ideal for {crop}')
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        if score >= 80:
            reasons.insert(0, 'Excellent match for current conditions')
        elif score >= 60:
            reasons.insert(0, 'Good match for current conditions')
        elif score >= 40:
            reasons.insert(0, 'Moderate match - some conditions need improvement')
        else:
            reasons.insert(0, 'Poor match - significant improvements needed')
        
        return {
            'score': round(score, 2),
            'reasons': reasons,
            'match_details': match_details
        }
    
    @classmethod
    def get_recommendations(
        cls,
        soil_ph: Optional[float] = None,
        soil_n: Optional[float] = None,
        soil_p: Optional[float] = None,
        soil_k: Optional[float] = None,
        soil_moisture: Optional[float] = None,
        temperature: Optional[float] = None,
        rainfall: Optional[float] = None,
        humidity: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        season: Optional[str] = None,
        limit: int = 10,
        use_ml: bool = True
    ) -> List[Dict]:
        """
        Get crop recommendations based on soil and weather conditions.
        Uses ML models if available, otherwise falls back to rule-based logic.
        
        Args:
            use_ml: Whether to try using ML models first (default: True)
            
        Returns:
            List of recommendations sorted by score (highest first)
        """
        # Try ML models first if available and requested
        if use_ml and ML_AVAILABLE:
            try:
                ml_service = get_ml_service()
                ml_recommendations = ml_service.predict_crop_recommendations(
                    soil_ph=soil_ph,
                    soil_n=soil_n,
                    soil_p=soil_p,
                    soil_k=soil_k,
                    soil_moisture=soil_moisture,
                    temperature=temperature,
                    rainfall=rainfall,
                    humidity=humidity,
                    latitude=latitude,
                    longitude=longitude,
                    season=season,
                    limit=limit
                )
                
                if ml_recommendations:
                    # Enhance ML recommendations with yield, profit, and sustainability
                    enhanced_recommendations = []
                    for rec in ml_recommendations:
                        crop_name = rec['crop_name']
                        
                        # Get yield prediction from ML model
                        ml_yield = ml_service.predict_yield(
                            crop_name=crop_name,
                            soil_ph=soil_ph,
                            soil_n=soil_n,
                            soil_p=soil_p,
                            soil_k=soil_k,
                            soil_moisture=soil_moisture,
                            temperature=temperature,
                            rainfall=rainfall,
                            humidity=humidity,
                            latitude=latitude,
                            longitude=longitude,
                            season=season
                        )
                        
                        # Use ML yield if available, otherwise use average
                        if ml_yield is not None:
                            expected_yield = ml_yield
                        else:
                            expected_yield = cls.AVERAGE_YIELDS.get(crop_name, 0)
                            # Adjust based on confidence
                            expected_yield = expected_yield * (rec['confidence_score'] / 100)
                        
                        # Use enhanced profit calculator if available
                        if BUSINESS_LOGIC_AVAILABLE:
                            yield_multiplier = rec['confidence_score'] / 100
                            profit_data = ProfitCalculator.calculate_profit(
                                crop_name=crop_name,
                                expected_yield=expected_yield,
                                yield_multiplier=1.0,  # Already adjusted
                                risk_adjustment=1.0
                            )
                            profit_margin = profit_data['risk_adjusted_profit']
                            profit_details = profit_data
                        else:
                            # Fallback to basic calculation
                            profit_per_kg = cls.AVERAGE_PROFITS.get(crop_name, 0) / max(cls.AVERAGE_YIELDS.get(crop_name, 1), 1)
                            profit_margin = expected_yield * profit_per_kg
                            profit_details = {'profit_margin': profit_margin}
                        
                        # Use enhanced sustainability scorer if available
                        if BUSINESS_LOGIC_AVAILABLE:
                            sustainability_data = SustainabilityScorer.calculate_sustainability_score(
                                crop_name=crop_name,
                                water_availability=rainfall * 1000 if rainfall else None,  # Rough estimate
                                soil_health_bonus=0.0,
                                rotation_bonus=0.0
                            )
                            sustainability_score = sustainability_data['sustainability_score']
                            sustainability_details = sustainability_data
                        else:
                            sustainability_score = cls.CROP_REQUIREMENTS.get(crop_name, {}).get('sustainability_score', 70)
                            sustainability_details = {}
                        
                        enhanced_rec = {
                            'crop_name': crop_name,
                            'confidence_score': rec['confidence_score'],
                            'expected_yield': round(expected_yield, 2),
                            'profit_margin': round(profit_margin, 2),
                            'sustainability_score': sustainability_score,
                            'reasons': [f'ML model prediction with {rec["confidence_score"]:.1f}% confidence'],
                            'match_details': {'ml_prediction': True},
                            'ml_prediction': True,
                            'profit_details': profit_details,
                            'sustainability_details': sustainability_details,
                        }
                        enhanced_recommendations.append(enhanced_rec)
                    
                    logger.info(f"Using ML model for recommendations. Generated {len(enhanced_recommendations)} recommendations.")
                    return enhanced_recommendations
                    
            except Exception as e:
                logger.warning(f"ML model prediction failed: {e}. Falling back to rule-based logic.")
        
        # Fallback to rule-based logic with enhanced business logic
        recommendations = []
        
        for crop in cls.CROP_REQUIREMENTS.keys():
            compatibility = cls.calculate_compatibility_score(
                crop=crop,
                soil_ph=soil_ph,
                soil_n=soil_n,
                soil_p=soil_p,
                soil_k=soil_k,
                soil_moisture=soil_moisture,
                temperature=temperature,
                rainfall=rainfall,
                season=season
            )
            
            # Get base yield
            expected_yield = cls.AVERAGE_YIELDS.get(crop, 0)
            yield_multiplier = compatibility['score'] / 100
            adjusted_yield = expected_yield * yield_multiplier
            
            # Use enhanced profit calculator if available
            if BUSINESS_LOGIC_AVAILABLE:
                profit_data = ProfitCalculator.calculate_profit(
                    crop_name=crop,
                    expected_yield=expected_yield,
                    yield_multiplier=yield_multiplier,
                    risk_adjustment=1.0
                )
                profit_margin = profit_data['risk_adjusted_profit']
                profit_details = profit_data
            else:
                # Fallback to basic calculation
                profit_margin = cls.AVERAGE_PROFITS.get(crop, 0) * yield_multiplier
                profit_details = {'profit_margin': profit_margin}
            
            # Use enhanced sustainability scorer if available
            if BUSINESS_LOGIC_AVAILABLE:
                sustainability_data = SustainabilityScorer.calculate_sustainability_score(
                    crop_name=crop,
                    water_availability=rainfall * 1000 if rainfall else None,
                    soil_health_bonus=0.0,
                    rotation_bonus=0.0
                )
                sustainability_score = sustainability_data['sustainability_score']
                sustainability_details = sustainability_data
            else:
                sustainability_score = cls.CROP_REQUIREMENTS[crop]['sustainability_score']
                sustainability_details = {}
            
            recommendation = {
                'crop_name': crop,
                'confidence_score': compatibility['score'],
                'expected_yield': round(adjusted_yield, 2),
                'profit_margin': round(profit_margin, 2),
                'sustainability_score': sustainability_score,
                'reasons': compatibility['reasons'],
                'match_details': compatibility['match_details'],
                'ml_prediction': False,
                'profit_details': profit_details,
                'sustainability_details': sustainability_details,
            }
            
            recommendations.append(recommendation)
        
        # Sort by confidence score (highest first) - will be enhanced with composite scoring
        recommendations.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Return top recommendations
        return recommendations[:limit]
    
    @classmethod
    def get_recommendation_for_field(
        cls,
        field,
        weather_data=None,
        limit: int = 10,
        use_ml: bool = True
    ) -> List[Dict]:
        """
        Get recommendations for a specific field with enhanced business logic.
        
        Args:
            field: Field model instance
            weather_data: WeatherData model instance (optional)
            limit: Maximum number of recommendations to return
            use_ml: Whether to try using ML models first (default: True)
        """
        # Get soil data from field
        soil_ph = float(field.soil_ph) if field.soil_ph else None
        soil_n = float(field.n_content) if field.n_content else None
        soil_p = float(field.p_content) if field.p_content else None
        soil_k = float(field.k_content) if field.k_content else None
        soil_moisture = float(field.soil_moisture) if field.soil_moisture else None
        
        # Get location
        latitude = None
        longitude = None
        if field.latitude and field.longitude:
            latitude = float(field.latitude)
            longitude = float(field.longitude)
        elif field.farm.latitude and field.farm.longitude:
            latitude = float(field.farm.latitude)
            longitude = float(field.farm.longitude)
        
        # Get weather data
        temperature = None
        rainfall = None
        humidity = None
        if weather_data:
            temperature = float(weather_data.temperature) if weather_data.temperature else None
            rainfall = float(weather_data.rainfall) if weather_data.rainfall else None
            humidity = float(weather_data.humidity) if weather_data.humidity else None
        
        # Get latest soil data if available
        latest_soil = field.soil_data.first() if hasattr(field, 'soil_data') else None
        if latest_soil:
            soil_ph = float(latest_soil.ph) if latest_soil.ph else soil_ph
            soil_n = float(latest_soil.n) if latest_soil.n else soil_n
            soil_p = float(latest_soil.p) if latest_soil.p else soil_p
            soil_k = float(latest_soil.k) if latest_soil.k else soil_k
            soil_moisture = float(latest_soil.moisture) if latest_soil.moisture else soil_moisture
        
        # Check if soil data is missing and log a warning
        missing_data = []
        if soil_ph is None:
            missing_data.append('pH')
        if soil_n is None:
            missing_data.append('Nitrogen')
        if soil_p is None:
            missing_data.append('Phosphorus')
        if soil_k is None:
            missing_data.append('Potassium')
        
        if missing_data:
            logger.warning(
                f"Field '{field.name}' (ID: {field.id}) is missing soil data: {', '.join(missing_data)}. "
                f"Recommendations may be less accurate. Location: ({latitude}, {longitude})"
            )
        
        # Get initial recommendations
        recommendations = cls.get_recommendations(
            soil_ph=soil_ph,
            soil_n=soil_n,
            soil_p=soil_p,
            soil_k=soil_k,
            soil_moisture=soil_moisture,
            temperature=temperature,
            rainfall=rainfall,
            humidity=humidity,
            latitude=latitude,
            longitude=longitude,
            limit=limit * 2,  # Get more for filtering
            use_ml=use_ml
        )
        
        # Enhance with crop rotation analysis and composite scoring
        if BUSINESS_LOGIC_AVAILABLE and recommendations:
            # Get crop history for rotation analysis
            from apps.farms.models import CropHistory
            crop_history = CropHistory.objects.filter(field=field).order_by('-year', '-season')
            field_history = [
                {
                    'crop_name': ch.crop_name,
                    'year': ch.year,
                    'season': ch.season
                }
                for ch in crop_history
            ]
            
            # Enhance each recommendation with rotation analysis and composite scoring
            enhanced_recommendations = []
            max_profit = max((r.get('profit_margin', 0) for r in recommendations), default=1)
            
            for rec in recommendations:
                crop_name = rec['crop_name']
                
                # Get rotation analysis
                rotation_analysis = CropRotationAnalyzer.get_rotation_score(
                    crop_name=crop_name,
                    field_history=field_history
                )
                
                # Get risk factor for ranking
                risk_factor = ProfitCalculator.RISK_FACTORS.get(crop_name, 0.3)
                
                # Calculate composite score
                profit_score = RecommendationRanker.normalize_profit_for_scoring(
                    rec.get('profit_margin', 0),
                    max_profit=max_profit
                )
                
                composite_score_data = RecommendationRanker.calculate_composite_score(
                    compatibility_score=rec.get('confidence_score', 0),
                    profit_score=profit_score,
                    sustainability_score=rec.get('sustainability_score', 0),
                    rotation_score=rotation_analysis['rotation_score'],
                    risk_factor=risk_factor
                )
                
                # Update recommendation with enhanced data
                rec['rotation_analysis'] = rotation_analysis
                rec['composite_score'] = composite_score_data['composite_score']
                rec['composite_breakdown'] = composite_score_data['breakdown']
                rec['rotation_score'] = rotation_analysis['rotation_score']
                
                # Add rotation reasons to main reasons
                if rotation_analysis['reasons']:
                    rec['reasons'].extend(rotation_analysis['reasons'])
                
                enhanced_recommendations.append(rec)
            
            # Sort by composite score instead of just confidence
            enhanced_recommendations.sort(
                key=lambda x: x.get('composite_score', x.get('confidence_score', 0)),
                reverse=True
            )
            
            # Add warning flag if soil data is missing
            if missing_data:
                for rec in enhanced_recommendations:
                    rec['missing_soil_data'] = missing_data
                    rec['data_quality_warning'] = f"Recommendations based on estimated soil data. Missing: {', '.join(missing_data)}"
            
            return enhanced_recommendations[:limit]
        
        # Add warning flag if soil data is missing
        if missing_data:
            for rec in recommendations:
                rec['missing_soil_data'] = missing_data
                rec['data_quality_warning'] = f"Recommendations based on estimated soil data. Missing: {', '.join(missing_data)}"
        
        return recommendations[:limit]

