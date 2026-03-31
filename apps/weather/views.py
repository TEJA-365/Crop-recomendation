"""
Views for weather data management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime, timedelta
from .models import WeatherData
from .forms import WeatherDataFetchForm, WeatherDataManualForm
from .services import WeatherDataService


@login_required
def weather_data_list(request):
    """List all weather data records."""
    weather_data_list = WeatherData.objects.all().order_by('-date', '-created_at')[:50]
    
    context = {
        'weather_data_list': weather_data_list,
    }
    return render(request, 'weather/weather_data_list.html', context)


@login_required
def weather_data_options(request):
    """Show options for adding weather data (manual or fetch from API)."""
    from apps.farms.models import Farm, Field
    user_fields = Field.objects.filter(farm__user=request.user)
    user_farms = Farm.objects.filter(user=request.user)
    
    has_fields = user_fields.exists()
    has_farms = user_farms.exists()
    
    context = {
        'has_fields': has_fields,
        'has_farms': has_farms,
        'fields_count': user_fields.count(),
        'farms_count': user_farms.count(),
    }
    return render(request, 'weather/weather_data_options.html', context)


@login_required
def weather_data_fetch(request):
    """Fetch weather data from API."""
    if request.method == 'POST':
        form = WeatherDataFetchForm(request.POST, user=request.user)
        if form.is_valid():
            location_type = form.cleaned_data['location_type']
            forecast_days = form.cleaned_data['forecast_days']
            
            # Get coordinates based on location type
            if location_type == 'field':
                field = form.cleaned_data['field']
                if field.latitude and field.longitude:
                    lat = float(field.latitude)
                    lon = float(field.longitude)
                    location_name = f"{field.name} (Field)"
                elif field.farm.latitude and field.farm.longitude:
                    lat = float(field.farm.latitude)
                    lon = float(field.farm.longitude)
                    location_name = f"{field.farm.name} (Farm)"
                else:
                    messages.error(request, 'Field or farm location is required.')
                    form = WeatherDataFetchForm(user=request.user)
                    return render(request, 'weather/weather_data_fetch.html', {'form': form})
            
            elif location_type == 'farm':
                farm = form.cleaned_data['farm']
                lat = float(farm.latitude)
                lon = float(farm.longitude)
                location_name = f"{farm.name} (Farm)"
            
            else:  # custom
                lat = float(form.cleaned_data['latitude'])
                lon = float(form.cleaned_data['longitude'])
                location_name = f"Custom Location ({lat}, {lon})"
            
            # Fetch current weather
            current_weather = WeatherDataService.fetch_openweathermap_current(lat, lon)
            
            if current_weather:
                # Validate data
                is_valid, error_msg = WeatherDataService.validate_weather_data(current_weather)
                if not is_valid:
                    messages.error(request, f'Invalid weather data: {error_msg}')
                    form = WeatherDataFetchForm(user=request.user)
                    return render(request, 'weather/weather_data_fetch.html', {'form': form})
                
                # Track data source for user feedback
                data_source = current_weather.pop('_source', 'unknown')
                
                # Get weather alerts
                alerts = WeatherDataService.calculate_weather_alerts(current_weather)
                
                # Create or update WeatherData record for today
                today = timezone.now().date()
                weather_data, created = WeatherData.objects.update_or_create(
                    latitude=lat,
                    longitude=lon,
                    date=today,
                    defaults={
                        'temperature': current_weather['temperature'],
                        'rainfall': current_weather.get('rainfall', 0),
                        'humidity': current_weather['humidity'],
                        'wind_speed': current_weather['wind_speed'],
                        'forecast_data': {
                            'pressure': current_weather.get('pressure'),
                            'description': current_weather.get('description'),
                            'icon': current_weather.get('icon'),
                            'source': data_source,
                        }
                    }
                )
                
                # Fetch forecast if requested
                forecast = None
                if forecast_days > 1:
                    forecast = WeatherDataService.get_weather_forecast(lat, lon, forecast_days)
                    # Store forecast in weather_data for detail view
                    if forecast:
                        forecast.pop('_source', None)
                        weather_data.forecast_data['forecast'] = forecast['forecast']
                        weather_data.forecast_data['city'] = forecast.get('city', '')
                        weather_data.forecast_data['country'] = forecast.get('country', '')
                        weather_data.save()
                
                action = 'updated' if not created else 'fetched'
                source_label = 'Open-Meteo' if data_source == 'open_meteo' else 'OpenWeatherMap'
                messages.success(
                    request,
                    f'Weather data {action} successfully for {location_name} '
                    f'(via {source_label})!'
                )
                
                context = {
                    'weather_data': weather_data,
                    'alerts': alerts,
                    'forecast': forecast,
                    'location_name': location_name,
                }
                return render(request, 'weather/weather_data_detail.html', context)
            else:
                messages.error(
                    request,
                    'Failed to fetch weather data from all sources. '
                    'Please check your internet connection or try again later.'
                )
                form = WeatherDataFetchForm(user=request.user)
                return render(request, 'weather/weather_data_fetch.html', {'form': form})
    else:
        form = WeatherDataFetchForm(user=request.user)
    
    return render(request, 'weather/weather_data_fetch.html', {'form': form})


@login_required
def weather_data_add(request):
    """Add weather data manually."""
    if request.method == 'POST':
        form = WeatherDataManualForm(request.POST)
        if form.is_valid():
            weather_data = form.save()
            messages.success(request, f'Weather data added successfully for {weather_data.date}!')
            return redirect('weather:weather_data_list')
    else:
        form = WeatherDataManualForm()
    
    return render(request, 'weather/weather_data_add.html', {'form': form})


@login_required
def weather_data_detail(request, pk):
    """View weather data details."""
    weather_data = get_object_or_404(WeatherData, pk=pk)
    
    # Get weather alerts
    weather_dict = {
        'temperature': float(weather_data.temperature),
        'rainfall': float(weather_data.rainfall),
        'humidity': float(weather_data.humidity),
        'wind_speed': float(weather_data.wind_speed),
    }
    alerts = WeatherDataService.calculate_weather_alerts(weather_dict)
    
    # Get forecast if available
    forecast = None
    if weather_data.forecast_data and 'forecast' in weather_data.forecast_data:
        forecast = weather_data.forecast_data['forecast']
    
    context = {
        'weather_data': weather_data,
        'alerts': alerts,
        'forecast': forecast,
    }
    return render(request, 'weather/weather_data_detail.html', context)


@login_required
@require_http_methods(["POST"])
def weather_data_fetch_ajax(request):
    """AJAX endpoint for fetching weather data."""
    lat = request.POST.get('latitude')
    lon = request.POST.get('longitude')
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid coordinates'}, status=400)
    
    # Fetch current weather
    weather_data = WeatherDataService.fetch_openweathermap_current(lat, lon)
    
    if weather_data:
        # Validate
        is_valid, error_msg = WeatherDataService.validate_weather_data(weather_data)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        
        # Get alerts
        alerts = WeatherDataService.calculate_weather_alerts(weather_data)
        
        return JsonResponse({
            'success': True,
            'data': {
                'temperature': weather_data.get('temperature'),
                'rainfall': weather_data.get('rainfall', 0),
                'humidity': weather_data.get('humidity'),
                'wind_speed': weather_data.get('wind_speed'),
                'pressure': weather_data.get('pressure'),
                'description': weather_data.get('description'),
                'icon': weather_data.get('icon'),
            },
            'alerts': alerts
        })
    else:
        return JsonResponse({'success': False, 'error': 'Failed to fetch weather data'}, status=500)


@login_required
def weather_forecast(request):
    """Get weather forecast for a location."""
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    days = int(request.GET.get('days', 7))
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (ValueError, TypeError):
        messages.error(request, 'Invalid coordinates')
        return redirect('weather:weather_data_fetch')
    
    forecast = WeatherDataService.get_weather_forecast(lat, lon, days)
    
    if forecast:
        context = {
            'forecast': forecast,
            'latitude': lat,
            'longitude': lon,
        }
        return render(request, 'weather/weather_forecast.html', context)
    else:
        messages.error(request, 'Failed to fetch weather forecast.')
        return redirect('weather:weather_data_fetch')
