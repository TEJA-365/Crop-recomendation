"""
Weather data API integration services.
Handles fetching weather data from OpenWeatherMap and Open-Meteo (free fallback).
"""
import requests
import logging
from typing import Dict, Optional, List, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# WMO Weather Code descriptions (used by Open-Meteo)
WMO_WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

# WMO code to icon mapping (approximate OpenWeatherMap-style icons)
WMO_ICON_MAP = {
    0: "01d", 1: "01d", 2: "02d", 3: "04d",
    45: "50d", 48: "50d",
    51: "09d", 53: "09d", 55: "09d",
    56: "13d", 57: "13d",
    61: "10d", 63: "10d", 65: "10d",
    66: "13d", 67: "13d",
    71: "13d", 73: "13d", 75: "13d", 77: "13d",
    80: "09d", 81: "09d", 82: "09d",
    85: "13d", 86: "13d",
    95: "11d", 96: "11d", 99: "11d",
}


class WeatherDataService:
    """Service for fetching and processing weather data from various sources."""
    
    @staticmethod
    def fetch_openweathermap_current(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch current weather data from OpenWeatherMap API.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with current weather data or None if failed
        """
        try:
            api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
            if not api_key:
                logger.info("OpenWeatherMap API key not configured, falling back to Open-Meteo")
                return WeatherDataService._fetch_open_meteo_current(latitude, longitude)
            
            base_url = "https://api.openweathermap.org/data/2.5/weather"
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': api_key,
                'units': 'metric'  # Get temperature in Celsius
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract weather data
                weather_data = {
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind'].get('speed', 0) * 3.6,  # Convert m/s to km/h
                    'rainfall': data.get('rain', {}).get('1h', 0) if 'rain' in data else 0,
                    'pressure': data['main'].get('pressure', None),
                    'description': data['weather'][0]['description'] if data.get('weather') else None,
                    'icon': data['weather'][0]['icon'] if data.get('weather') else None,
                    '_source': 'openweathermap',
                }
                
                return weather_data
            elif response.status_code == 401:
                logger.warning("OpenWeatherMap API key invalid, falling back to Open-Meteo")
                return WeatherDataService._fetch_open_meteo_current(latitude, longitude)
            else:
                logger.warning(
                    f"OpenWeatherMap API returned status {response.status_code}, "
                    f"falling back to Open-Meteo"
                )
                return WeatherDataService._fetch_open_meteo_current(latitude, longitude)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OpenWeatherMap data: {str(e)}, falling back to Open-Meteo")
            return WeatherDataService._fetch_open_meteo_current(latitude, longitude)
        except Exception as e:
            logger.error(f"Unexpected error in OpenWeatherMap fetch: {str(e)}")
            return None
    
    @staticmethod
    def _fetch_open_meteo_current(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch current weather data from Open-Meteo API (free, no API key required).
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with current weather data or None if failed
        """
        try:
            base_url = "https://api.open-meteo.com/v1/forecast"
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'current': 'temperature_2m,relative_humidity_2m,rain,wind_speed_10m,surface_pressure,weather_code',
                'timezone': 'auto',
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                current = data.get('current', {})
                
                if not current:
                    logger.warning("Open-Meteo returned empty current data")
                    return None
                
                weather_code = current.get('weather_code', 0)
                
                weather_data = {
                    'temperature': current.get('temperature_2m'),
                    'humidity': current.get('relative_humidity_2m'),
                    'wind_speed': current.get('wind_speed_10m', 0),  # Already in km/h
                    'rainfall': current.get('rain', 0),
                    'pressure': current.get('surface_pressure'),
                    'description': WMO_WEATHER_CODES.get(weather_code, 'Unknown'),
                    'icon': WMO_ICON_MAP.get(weather_code, '01d'),
                    '_source': 'open_meteo',
                }
                
                logger.info(
                    f"Open-Meteo: Current weather for ({latitude}, {longitude}): "
                    f"{weather_data['temperature']}°C, {weather_data['humidity']}% humidity, "
                    f"{weather_data['description']}"
                )
                
                return weather_data
            else:
                logger.warning(f"Open-Meteo API returned status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Open-Meteo data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Open-Meteo fetch: {str(e)}")
            return None
    
    @staticmethod
    def fetch_openweathermap_forecast(latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
        """
        Fetch weather forecast from OpenWeatherMap API, with Open-Meteo fallback.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast (max 5 for free OWM tier, up to 16 for Open-Meteo)
            
        Returns:
            Dictionary with forecast data or None if failed
        """
        try:
            api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')
            if not api_key:
                logger.info("OpenWeatherMap API key not configured, using Open-Meteo for forecast")
                return WeatherDataService._fetch_open_meteo_forecast(latitude, longitude, days)
            
            # Limit to 5 days for free tier
            days = min(days, 5)
            
            base_url = "https://api.openweathermap.org/data/2.5/forecast"
            
            params = {
                'lat': latitude,
                'lon': longitude,
                'appid': api_key,
                'units': 'metric',
                'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Process forecast data
                forecast_list = []
                for item in data.get('list', []):
                    forecast_item = {
                        'datetime': item['dt_txt'],
                        'temperature': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': item['wind'].get('speed', 0) * 3.6,  # Convert m/s to km/h
                        'rainfall': item.get('rain', {}).get('3h', 0) if 'rain' in item else 0,
                        'description': item['weather'][0]['description'] if item.get('weather') else None,
                        'icon': item['weather'][0]['icon'] if item.get('weather') else None,
                    }
                    forecast_list.append(forecast_item)
                
                return {
                    'forecast': forecast_list,
                    'city': data.get('city', {}).get('name', ''),
                    'country': data.get('city', {}).get('country', ''),
                    '_source': 'openweathermap',
                }
            else:
                logger.warning(
                    f"OpenWeatherMap Forecast API returned status {response.status_code}, "
                    f"falling back to Open-Meteo"
                )
                return WeatherDataService._fetch_open_meteo_forecast(latitude, longitude, days)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching OpenWeatherMap forecast: {str(e)}, falling back to Open-Meteo")
            return WeatherDataService._fetch_open_meteo_forecast(latitude, longitude, days)
        except Exception as e:
            logger.error(f"Unexpected error in OpenWeatherMap forecast fetch: {str(e)}")
            return None
    
    @staticmethod
    def _fetch_open_meteo_forecast(latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
        """
        Fetch weather forecast from Open-Meteo API (free, no API key required).
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast (up to 16)
            
        Returns:
            Dictionary with forecast data or None if failed
        """
        try:
            days = min(days, 16)  # Open-Meteo supports up to 16 days
            
            base_url = "https://api.open-meteo.com/v1/forecast"
            
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'daily': 'temperature_2m_max,temperature_2m_min,rain_sum,wind_speed_10m_max,weather_code',
                'timezone': 'auto',
                'forecast_days': days,
            }
            
            response = requests.get(base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                daily = data.get('daily', {})
                
                if not daily or not daily.get('time'):
                    logger.warning("Open-Meteo returned empty forecast data")
                    return None
                
                # Convert daily forecast to our format
                forecast_list = []
                times = daily.get('time', [])
                temp_max = daily.get('temperature_2m_max', [])
                temp_min = daily.get('temperature_2m_min', [])
                rain_sum = daily.get('rain_sum', [])
                wind_max = daily.get('wind_speed_10m_max', [])
                weather_codes = daily.get('weather_code', [])
                
                for i in range(len(times)):
                    # Calculate average temperature
                    t_max = temp_max[i] if i < len(temp_max) else None
                    t_min = temp_min[i] if i < len(temp_min) else None
                    avg_temp = None
                    if t_max is not None and t_min is not None:
                        avg_temp = round((t_max + t_min) / 2, 1)
                    
                    wmo_code = weather_codes[i] if i < len(weather_codes) else 0
                    
                    forecast_item = {
                        'datetime': f"{times[i]} 12:00:00",  # Use noon as representative time
                        'date': times[i],
                        'temperature': avg_temp,
                        'temperature_max': t_max,
                        'temperature_min': t_min,
                        'humidity': None,  # Daily humidity not in basic Open-Meteo
                        'wind_speed': wind_max[i] if i < len(wind_max) else 0,
                        'rainfall': rain_sum[i] if i < len(rain_sum) else 0,
                        'description': WMO_WEATHER_CODES.get(wmo_code, 'Unknown'),
                        'icon': WMO_ICON_MAP.get(wmo_code, '01d'),
                    }
                    forecast_list.append(forecast_item)
                
                # Get location info from Open-Meteo response
                timezone_name = data.get('timezone', '')
                
                logger.info(
                    f"Open-Meteo: Got {len(forecast_list)}-day forecast for ({latitude}, {longitude})"
                )
                
                return {
                    'forecast': forecast_list,
                    'city': timezone_name.split('/')[-1].replace('_', ' ') if '/' in timezone_name else '',
                    'country': '',
                    '_source': 'open_meteo',
                }
            else:
                logger.warning(f"Open-Meteo Forecast API returned status {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Open-Meteo forecast: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Open-Meteo forecast fetch: {str(e)}")
            return None
    
    @staticmethod
    def get_weather_data(latitude: float, longitude: float, date: Optional[datetime] = None) -> Optional[Dict]:
        """
        Get weather data for a specific location and date.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            date: Date for weather data (None for current)
            
        Returns:
            Dictionary with weather data or None if failed
        """
        if date is None or date.date() == timezone.now().date():
            # Fetch current weather
            return WeatherDataService.fetch_openweathermap_current(latitude, longitude)
        else:
            # For historical data, would need a different API or stored data
            # For now, return current weather
            logger.warning("Historical weather data not available, fetching current weather")
            return WeatherDataService.fetch_openweathermap_current(latitude, longitude)
    
    @staticmethod
    def get_weather_forecast(latitude: float, longitude: float, days: int = 7) -> Optional[Dict]:
        """
        Get weather forecast for a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to forecast
            
        Returns:
            Dictionary with forecast data or None if failed
        """
        return WeatherDataService.fetch_openweathermap_forecast(latitude, longitude, days)
    
    @staticmethod
    def validate_weather_data(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate weather data values.
        
        Args:
            data: Dictionary with weather data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate temperature (reasonable range: -50 to 60 Celsius)
        if 'temperature' in data and data['temperature'] is not None:
            temp = float(data['temperature'])
            if not (-50 <= temp <= 60):
                return False, "Temperature must be between -50 and 60 Celsius"
        
        # Validate humidity (0-100%)
        if 'humidity' in data and data['humidity'] is not None:
            humidity = float(data['humidity'])
            if not (0 <= humidity <= 100):
                return False, "Humidity must be between 0 and 100"
        
        # Validate rainfall (non-negative)
        if 'rainfall' in data and data['rainfall'] is not None:
            rainfall = float(data['rainfall'])
            if rainfall < 0:
                return False, "Rainfall must be non-negative"
        
        # Validate wind speed (non-negative)
        if 'wind_speed' in data and data['wind_speed'] is not None:
            wind_speed = float(data['wind_speed'])
            if wind_speed < 0:
                return False, "Wind speed must be non-negative"
        
        return True, None
    
    @staticmethod
    def calculate_weather_alerts(weather_data: Dict) -> List[str]:
        """
        Calculate weather alerts based on weather conditions.
        
        Args:
            weather_data: Dictionary with weather data
            
        Returns:
            List of alert messages
        """
        alerts = []
        
        # Temperature alerts
        if 'temperature' in weather_data:
            temp = float(weather_data['temperature'])
            if temp < 5:
                alerts.append("⚠️ Low temperature warning: Risk of frost")
            elif temp > 40:
                alerts.append("⚠️ High temperature warning: Extreme heat conditions")
        
        # Rainfall alerts
        if 'rainfall' in weather_data:
            rainfall = float(weather_data['rainfall'])
            if rainfall > 50:
                alerts.append("⚠️ Heavy rainfall warning: Potential flooding risk")
            elif rainfall < 1 and 'temperature' in weather_data and float(weather_data['temperature']) > 30:
                alerts.append("⚠️ Drought warning: Low rainfall and high temperature")
        
        # Wind alerts
        if 'wind_speed' in weather_data:
            wind = float(weather_data['wind_speed'])
            if wind > 50:
                alerts.append("⚠️ Strong wind warning: High wind speeds detected")
        
        return alerts
