"""
Views for crop recommendations.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Recommendation
from .forms import RecommendationRequestForm
from .services import CropRecommendationService
from apps.farms.models import Field
from apps.weather.models import WeatherData


@login_required
def recommendation_request(request):
    """Request crop recommendations for a field."""
    if request.method == 'POST':
        form = RecommendationRequestForm(request.POST, user=request.user)
        if form.is_valid():
            field = form.cleaned_data['field']
            include_weather = form.cleaned_data.get('include_weather', True)
            
            # Get weather data if requested
            weather_data = None
            if include_weather:
                # Try to get latest weather data for field location
                if field.latitude and field.longitude:
                    weather_data = WeatherData.objects.filter(
                        latitude=field.latitude,
                        longitude=field.longitude
                    ).order_by('-date').first()
                elif field.farm.latitude and field.farm.longitude:
                    weather_data = WeatherData.objects.filter(
                        latitude=field.farm.latitude,
                        longitude=field.farm.longitude
                    ).order_by('-date').first()
            
            # Get recommendations
            recommendations = CropRecommendationService.get_recommendation_for_field(
                field=field,
                weather_data=weather_data,
                limit=10
            )
            
            if not recommendations:
                messages.warning(request, 'No recommendations available. Please ensure field has soil data.')
                return render(request, 'recommendations/recommendation_request.html', {'form': form})
            
            # Save top recommendations to database
            saved_recommendations = []
            for rec in recommendations[:5]:  # Save top 5
                # Check if recommendation already exists
                existing = Recommendation.objects.filter(
                    user=request.user,
                    field=field,
                    crop_name=rec['crop_name']
                ).order_by('-created_at').first()
                
                if existing:
                    # Update existing recommendation
                    existing.confidence_score = rec['confidence_score']
                    existing.expected_yield = rec['expected_yield']
                    existing.profit_margin = rec['profit_margin']
                    existing.sustainability_score = rec['sustainability_score']
                    reasoning_data = {
                        'reasons': rec['reasons'],
                        'match_details': rec['match_details']
                    }
                    # Add profit_details if available
                    if 'profit_details' in rec:
                        reasoning_data['profit_details'] = rec['profit_details']
                    # Add sustainability_details if available
                    if 'sustainability_details' in rec:
                        reasoning_data['sustainability_details'] = rec['sustainability_details']
                    # Add rotation_analysis if available
                    if 'rotation_analysis' in rec:
                        reasoning_data['rotation_analysis'] = rec['rotation_analysis']
                    existing.reasoning = reasoning_data
                    existing.save()
                    saved_recommendations.append(existing)
                else:
                    # Create new recommendation
                    reasoning_data = {
                        'reasons': rec['reasons'],
                        'match_details': rec['match_details']
                    }
                    # Add profit_details if available
                    if 'profit_details' in rec:
                        reasoning_data['profit_details'] = rec['profit_details']
                    # Add sustainability_details if available
                    if 'sustainability_details' in rec:
                        reasoning_data['sustainability_details'] = rec['sustainability_details']
                    # Add rotation_analysis if available
                    if 'rotation_analysis' in rec:
                        reasoning_data['rotation_analysis'] = rec['rotation_analysis']
                    
                    recommendation = Recommendation.objects.create(
                        user=request.user,
                        field=field,
                        crop_name=rec['crop_name'],
                        confidence_score=rec['confidence_score'],
                        expected_yield=rec['expected_yield'],
                        profit_margin=rec['profit_margin'],
                        sustainability_score=rec['sustainability_score'],
                        reasoning=reasoning_data
                    )
                    saved_recommendations.append(recommendation)
            
            messages.success(request, f'Generated {len(recommendations)} crop recommendations for {field.name}!')
            
            context = {
                'field': field,
                'recommendations': recommendations,
                'saved_recommendations': saved_recommendations,
                'weather_data': weather_data,
            }
            return render(request, 'recommendations/recommendation_results.html', context)
    else:
        form = RecommendationRequestForm(user=request.user)
    
    return render(request, 'recommendations/recommendation_request.html', {'form': form})


@login_required
def recommendation_list(request):
    """List all recommendations for the current user."""
    recommendations = Recommendation.objects.filter(
        user=request.user
    ).select_related('field', 'field__farm').order_by('-created_at')[:50]
    
    context = {
        'recommendations': recommendations,
    }
    return render(request, 'recommendations/recommendation_list.html', context)


@login_required
def recommendation_detail(request, pk):
    """View recommendation details."""
    recommendation = get_object_or_404(
        Recommendation,
        pk=pk,
        user=request.user
    )
    
    context = {
        'recommendation': recommendation,
    }
    return render(request, 'recommendations/recommendation_detail.html', context)


@login_required
def recommendation_for_field(request, field_pk):
    """Get recommendations for a specific field."""
    field = get_object_or_404(Field, pk=field_pk, farm__user=request.user)
    
    # Get latest weather data
    weather_data = None
    if field.latitude and field.longitude:
        weather_data = WeatherData.objects.filter(
            latitude=field.latitude,
            longitude=field.longitude
        ).order_by('-date').first()
    elif field.farm.latitude and field.farm.longitude:
        weather_data = WeatherData.objects.filter(
            latitude=field.farm.latitude,
            longitude=field.farm.longitude
        ).order_by('-date').first()
    
    # Get recommendations
    recommendations = CropRecommendationService.get_recommendation_for_field(
        field=field,
        weather_data=weather_data,
        limit=10
    )
    
    context = {
        'field': field,
        'recommendations': recommendations,
        'weather_data': weather_data,
    }
    return render(request, 'recommendations/recommendation_results.html', context)
