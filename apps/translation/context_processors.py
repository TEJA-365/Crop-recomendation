"""
Context processors for translation utilities in templates.
"""
from .utils import get_user_language, get_all_languages, get_language_name
from .services import get_translation_service


# Common UI strings that appear on every page
COMMON_UI_STRINGS = [
    "Dashboard", "Profile", "Settings", "About", "Contact",
    "Login", "Register", "Logout", "Change Password",
    "Crop Recommendation", "Crop Recommendation System",
    "Welcome back", "Get Recommendations", "Quick Actions",
    "Total Farms", "Total Fields", "Recommendations", "Crop History",
    "Add Farm", "Add Field", "Soil Data", "Weather Data",
    "My Farms", "My Fields", "View all farms", "View all fields",
    "View all recommendations", "View Soil Data", "View Weather",
    "All soil records", "All weather records", "Recent Recommendations",
    "System Status", "Weather API", "Soil Data API", "ML Models",
    "Connected", "Ready", "Update Profile", "Crop", "Field", "Confidence",
    "Date", "No recommendations yet. Get started by adding a farm and field!",
    "AI-powered farming solutions for better yields and profits.",
    "Quick Links", "About Us", "Contact Us", "Crop Recommendation System. All rights reserved.",
    "Register a new farm", "Add a new field", "Add soil data", "Add weather data",
    "AI-powered suggestions", "Chat Assistant", "Ask questions", "Coming Soon",
]


def translation_context(request):
    """
    Add translation-related context to all templates.
    Pre-translates common UI strings for better performance.
    
    Returns:
        Dictionary with translation utilities and pre-translated strings
    """
    user = getattr(request, 'user', None)
    current_language = get_user_language(user) if user and user.is_authenticated else 'en'
    
    # Pre-translate common UI strings if not English
    translated_strings = {}
    if current_language != 'en':
        service = get_translation_service()
        translated_dict = service.translate_batch(COMMON_UI_STRINGS, current_language)
        translated_strings = translated_dict
    
    return {
        'current_language': current_language,
        'supported_languages': get_all_languages(),
        'language_name': get_language_name(current_language),
        'translated_strings': translated_strings,  # Pre-translated common strings
    }

