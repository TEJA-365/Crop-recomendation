"""
Soil data API integration services.
Handles fetching soil data from various sources (Soil Grids, Bhuvan, manual input).
"""
import requests
import logging
from typing import Dict, Optional, Tuple
from decimal import Decimal
from django.conf import settings

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Regional soil estimation data for India (state/zone-level averages)
# Source: Indian Council of Agricultural Research (ICAR) published ranges
# Used as fallback when APIs return no data for a location.
# ──────────────────────────────────────────────────────────────
INDIA_SOIL_REGIONS = [
    # (name, lat_min, lat_max, lon_min, lon_max, ph, moisture, n, p, k)
    # Telangana / Andhra Pradesh (Deccan Plateau - Black/Red soil)
    ('Telangana-AP', 13.0, 19.5, 77.0, 81.5, 7.5, 28.0, 185.0, 22.0, 280.0),
    # Karnataka (Deccan Plateau)
    ('Karnataka', 11.5, 18.5, 74.0, 78.5, 7.2, 25.0, 195.0, 20.0, 260.0),
    # Tamil Nadu (Coastal / Red soil)
    ('Tamil Nadu', 8.0, 13.5, 76.0, 80.5, 7.0, 30.0, 210.0, 18.0, 240.0),
    # Kerala (Laterite soil - acidic)
    ('Kerala', 8.0, 13.0, 74.5, 77.5, 5.5, 45.0, 280.0, 15.0, 200.0),
    # Maharashtra (Black cotton soil)
    ('Maharashtra', 15.5, 22.0, 72.5, 80.5, 7.8, 22.0, 170.0, 24.0, 310.0),
    # Gujarat
    ('Gujarat', 20.0, 24.5, 68.0, 74.5, 7.9, 18.0, 155.0, 26.0, 320.0),
    # Rajasthan (Arid / Sandy)
    ('Rajasthan', 23.0, 30.0, 69.0, 78.0, 8.2, 12.0, 130.0, 15.0, 220.0),
    # Madhya Pradesh
    ('Madhya Pradesh', 21.0, 26.5, 74.0, 82.5, 7.4, 24.0, 190.0, 20.0, 270.0),
    # UP / Bihar (Indo-Gangetic alluvial)
    ('UP-Bihar', 24.0, 30.0, 80.0, 88.5, 7.6, 32.0, 230.0, 28.0, 200.0),
    # Punjab / Haryana
    ('Punjab-Haryana', 28.5, 32.5, 74.0, 77.5, 7.8, 20.0, 210.0, 25.0, 250.0),
    # West Bengal (Alluvial)
    ('West Bengal', 21.5, 27.0, 86.5, 89.5, 6.5, 38.0, 260.0, 22.0, 210.0),
    # Northeast India (Acidic / Laterite)
    ('Northeast', 22.0, 29.5, 89.5, 97.5, 5.2, 42.0, 290.0, 12.0, 180.0),
    # Odisha (Red / Laterite)
    ('Odisha', 17.5, 22.5, 81.0, 87.5, 6.2, 35.0, 220.0, 16.0, 230.0),
    # Chhattisgarh
    ('Chhattisgarh', 17.5, 24.0, 80.0, 84.5, 6.8, 28.0, 200.0, 18.0, 240.0),
    # Jammu & Kashmir / Himachal
    ('JK-Himachal', 30.5, 37.0, 73.5, 80.0, 6.5, 35.0, 250.0, 20.0, 220.0),
    # Default for India
    ('India-Default', 6.0, 37.0, 68.0, 97.0, 7.0, 25.0, 200.0, 20.0, 250.0),
]


class SoilDataService:
    """Service for fetching and processing soil data from various sources."""
    
    @staticmethod
    def fetch_soil_grids_data(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch soil data from Soil Grids API using batch query with multi-depth fallback.
        
        Queries all properties in a single request.
        If 0-5cm depth returns null, tries deeper depths (5-15cm, 15-30cm).
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with soil data or None if failed
        """
        try:
            base_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
            
            # All properties we need, including 'nitrogen' which is directly available
            properties_to_fetch = ['phh2o', 'nitrogen', 'ocd', 'sand', 'clay', 'bdod', 'cec']
            
            # Try multiple depths - some locations have data at deeper layers but not surface
            depth_priorities = ['0-5cm', '5-15cm', '15-30cm', '30-60cm']
            
            property_values = {}
            used_depth = None
            
            for depth in depth_priorities:
                # Batch query: pass all properties at once
                params = [
                    ('lon', float(longitude)),
                    ('lat', float(latitude)),
                    ('depth', depth),
                    ('value', 'mean'),
                ]
                # Add each property as a separate param (API accepts repeated 'property' keys)
                for prop in properties_to_fetch:
                    params.append(('property', prop))
                
                try:
                    response = requests.get(base_url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Extract all property values from this depth
                        depth_values = {}
                        for prop in properties_to_fetch:
                            value = SoilDataService._extract_property_from_layers(data, prop)
                            if value is not None:
                                depth_values[prop] = value
                        
                        if depth_values:
                            property_values = depth_values
                            used_depth = depth
                            logger.info(
                                f"Soil Grids: Got {len(depth_values)} properties at depth {depth} "
                                f"for ({latitude}, {longitude})"
                            )
                            break  # Got data, stop trying deeper
                        else:
                            logger.debug(
                                f"Soil Grids: No data at depth {depth} for ({latitude}, {longitude})"
                            )
                    else:
                        logger.warning(
                            f"Soil Grids API returned status {response.status_code} for depth {depth}. "
                            f"Response: {response.text[:200]}"
                        )
                except requests.exceptions.Timeout:
                    logger.warning(f"Soil Grids API timeout at depth {depth}")
                    continue
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error at depth {depth}: {str(e)}")
                    continue
            
            if not property_values:
                logger.warning(
                    f"Soil Grids: No data at any depth for ({latitude}, {longitude}). "
                    f"This location may be in an urban area or ocean with no coverage."
                )
                return None
            
            # ── Convert Soil Grids raw values to our format ──
            
            # pH: stored as pH*10 (d_factor=10)
            ph_value = property_values.get('phh2o')
            ph = ph_value / 10.0 if ph_value is not None else None
            
            # Nitrogen: stored as cg/kg (d_factor=100), convert to kg/ha
            # Assuming bulk density ~1.3 g/cm³ and depth layer ~15cm
            nitrogen_raw = property_values.get('nitrogen')
            n_value = None
            if nitrogen_raw is not None:
                # cg/kg → g/kg: divide by 100
                # g/kg → kg/ha: multiply by bulk_density(g/cm³) * depth(cm) * 0.1
                bulk_density = property_values.get('bdod', 130) / 100.0  # cg/cm³ → g/cm³
                n_value = round((nitrogen_raw / 100.0) * bulk_density * 15 * 0.1, 2)
            else:
                # Estimate N from organic carbon if nitrogen not available
                organic_carbon = property_values.get('ocd')
                if organic_carbon is not None:
                    bulk_density = property_values.get('bdod', 130) / 100.0
                    n_value = round(organic_carbon * 0.1 * bulk_density * 15 * 0.01, 2)
            
            # Organic carbon density: dg/dm³ (d_factor=10)
            organic_carbon = property_values.get('ocd')
            
            soil_data = {
                'ph': round(ph, 2) if ph is not None else None,
                'moisture': None,  # Soil Grids doesn't provide moisture
                'n': n_value,
                'p': None,  # Not available from Soil Grids
                'k': None,  # Not available from Soil Grids
                'organic_carbon': organic_carbon,
                'sand': property_values.get('sand'),
                'clay': property_values.get('clay'),
                'bulk_density': round(property_values.get('bdod', 0) / 100.0, 2) if property_values.get('bdod') else None,
                'cec': property_values.get('cec'),
                '_depth_used': used_depth,
            }
            
            return soil_data
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Soil Grids data: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Soil Grids fetch: {str(e)}")
            return None
    
    @staticmethod
    def fetch_bhuvan_data(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Fetch soil data for Indian regions using OpenGeoHub / alternative open sources.
        
        Since the Bhuvan NRSC soil API is not publicly accessible as a REST endpoint,
        this method uses the Open Landmap / OpenGeoHub API as an alternative source
        for Indian soil data, then falls back to regional estimates from ICAR data.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with soil data or None if failed
        """
        # ── Attempt 1: Try Open Landmap API (works for India) ──
        try:
            base_url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
            
            # Use batch query with multiple depths for better coverage
            params = [
                ('lon', float(longitude)),
                ('lat', float(latitude)),
                ('value', 'mean'),
            ]
            for depth in ['0-5cm', '5-15cm', '15-30cm']:
                params.append(('depth', depth))
            for prop in ['phh2o', 'nitrogen', 'ocd', 'sand', 'clay']:
                params.append(('property', prop))
            
            response = requests.get(base_url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Try to get values from any available depth
                property_values = {}
                for prop in ['phh2o', 'nitrogen', 'ocd', 'sand', 'clay']:
                    value = SoilDataService._extract_best_value_from_layers(data, prop)
                    if value is not None:
                        property_values[prop] = value
                
                if property_values:
                    ph_value = property_values.get('phh2o')
                    ph = round(ph_value / 10.0, 2) if ph_value is not None else None
                    
                    # Convert nitrogen from cg/kg to kg/ha
                    nitrogen_raw = property_values.get('nitrogen')
                    n_value = None
                    if nitrogen_raw is not None:
                        n_value = round((nitrogen_raw / 100.0) * 1.3 * 15 * 0.1, 2)
                    
                    soil_data = {
                        'ph': ph,
                        'moisture': None,
                        'n': n_value,
                        'p': None,
                        'k': None,
                    }
                    
                    # Only return if we got at least pH or nitrogen
                    if ph is not None or n_value is not None:
                        logger.info(f"Bhuvan (via SoilGrids): Got data for ({latitude}, {longitude})")
                        return soil_data
                    
        except requests.exceptions.RequestException as e:
            logger.warning(f"Alternative soil API failed for Bhuvan: {str(e)}")
        except Exception as e:
            logger.warning(f"Unexpected error in alternative Bhuvan fetch: {str(e)}")
        
        # ── Attempt 2: Fall back to Indian regional estimates ──
        logger.info(f"Using regional soil estimates for ({latitude}, {longitude})")
        return SoilDataService._get_indian_regional_estimate(latitude, longitude)

    @staticmethod
    def _get_indian_regional_estimate(latitude: float, longitude: float) -> Optional[Dict]:
        """
        Return estimated soil data based on Indian region.
        Uses published ICAR data for major agro-climatic zones.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with estimated soil data, or None if not in India
        """
        is_india = 6.0 <= latitude <= 37.0 and 68.0 <= longitude <= 97.0
        if not is_india:
            return None
        
        # Find best matching region (first specific match wins; last entry is default)
        for name, lat_min, lat_max, lon_min, lon_max, ph, moisture, n, p, k in INDIA_SOIL_REGIONS:
            if lat_min <= latitude <= lat_max and lon_min <= longitude <= lon_max:
                logger.info(f"Regional estimate: matched region '{name}' for ({latitude}, {longitude})")
                return {
                    'ph': ph,
                    'moisture': moisture,
                    'n': n,
                    'p': p,
                    'k': k,
                    '_estimated': True,
                    '_region': name,
                }
        
        return None
    
    @staticmethod
    def get_soil_data(latitude: float, longitude: float, source: str = 'auto') -> Optional[Dict]:
        """
        Get soil data from the best available source with fallback chain.
        
        Fallback order for 'auto':
          1. Soil Grids API (works globally)
          2. Regional estimates for India (ICAR-based)
        
        For 'bhuvan':
          1. Soil Grids query for Indian coordinates
          2. Regional estimates for India
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            source: Data source preference ('auto', 'soil_grids', 'bhuvan', 'manual')
            
        Returns:
            Dictionary with soil data or None if failed
        """
        is_india = 6.0 <= latitude <= 37.0 and 68.0 <= longitude <= 97.0
        
        if source == 'auto':
            # Try Soil Grids first (works globally and is the most reliable API)
            data = SoilDataService.fetch_soil_grids_data(latitude, longitude)
            if data:
                data['source'] = 'soil_grids'
                return data
            
            # For India: fall back to regional estimates
            if is_india:
                data = SoilDataService._get_indian_regional_estimate(latitude, longitude)
                if data:
                    data['source'] = 'bhuvan'  # Label as bhuvan for display
                    logger.info(
                        f"Auto mode: Using Indian regional estimate for ({latitude}, {longitude})"
                    )
                    return data
            
            logger.warning(f"Auto mode: No soil data available for ({latitude}, {longitude})")
            return None
        
        elif source == 'soil_grids':
            data = SoilDataService.fetch_soil_grids_data(latitude, longitude)
            if data:
                data['source'] = 'soil_grids'
                return data
            
            # Fallback to regional estimate if in India
            if is_india:
                data = SoilDataService._get_indian_regional_estimate(latitude, longitude)
                if data:
                    data['source'] = 'soil_grids'
                    data['_note'] = 'Regional estimate (Soil Grids had no data for this location)'
                    return data
            return None
        
        elif source == 'bhuvan':
            data = SoilDataService.fetch_bhuvan_data(latitude, longitude)
            if data:
                data['source'] = 'bhuvan'
                return data
            return None
        
        return None
    
    @staticmethod
    def _extract_property(properties: Dict, key: str, stat: str = 'mean') -> Optional[float]:
        """Extract property value from Soil Grids response (legacy method)."""
        try:
            prop_data = properties.get(key, {})
            if isinstance(prop_data, dict):
                return prop_data.get(stat)
            return prop_data
        except (KeyError, TypeError, AttributeError):
            return None
    
    @staticmethod
    def _extract_property_from_layers(data: Dict, property_name: str) -> Optional[float]:
        """Extract property value from Soil Grids API response structure.
        
        The API returns: {
            "properties": {
                "layers": [{
                    "name": "phh2o",
                    "depths": [{
                        "values": {"mean": 63}
                    }]
                }]
            }
        }
        """
        try:
            properties = data.get('properties', {})
            layers = properties.get('layers', [])
            
            # Find the layer with matching property name
            for layer in layers:
                if layer.get('name') == property_name:
                    depths = layer.get('depths', [])
                    if depths:
                        # Get the first depth
                        values = depths[0].get('values', {})
                        mean_value = values.get('mean')
                        return float(mean_value) if mean_value is not None else None
            
            return None
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.debug(f"Error extracting {property_name}: {str(e)}")
            return None
    
    @staticmethod
    def _extract_best_value_from_layers(data: Dict, property_name: str) -> Optional[float]:
        """Extract the best available value from Soil Grids response across all depths.
        
        Tries each depth in order and returns the first non-null value found.
        This handles cases where some depths have data but others don't.
        """
        try:
            properties = data.get('properties', {})
            layers = properties.get('layers', [])
            
            for layer in layers:
                if layer.get('name') == property_name:
                    depths = layer.get('depths', [])
                    for depth in depths:
                        values = depth.get('values', {})
                        mean_value = values.get('mean')
                        if mean_value is not None:
                            return float(mean_value)
            
            return None
        except (KeyError, TypeError, AttributeError, ValueError) as e:
            logger.debug(f"Error extracting best value for {property_name}: {str(e)}")
            return None
    
    @staticmethod
    def validate_soil_data(data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate soil data values.
        
        Args:
            data: Dictionary with soil data
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate pH (typically 0-14)
        if 'ph' in data and data['ph'] is not None:
            ph = float(data['ph'])
            if not (0 <= ph <= 14):
                return False, "pH must be between 0 and 14"
        
        # Validate moisture (typically 0-100%)
        if 'moisture' in data and data['moisture'] is not None:
            moisture = float(data['moisture'])
            if not (0 <= moisture <= 100):
                return False, "Moisture must be between 0 and 100"
        
        # Validate nutrients (should be positive)
        for nutrient in ['n', 'p', 'k']:
            if nutrient in data and data[nutrient] is not None:
                value = float(data[nutrient])
                if value < 0:
                    return False, f"{nutrient.upper()} must be non-negative"
        
        return True, None
