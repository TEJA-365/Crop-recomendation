"""
Translation utility functions for templates and views.
"""
from typing import Optional
from django.utils.translation import get_language
from django.conf import settings
from .services import translate_text, detect_language, get_translation_service


def get_user_language(user) -> str:
    """
    Get user's preferred language.
    
    Args:
        user: User instance
        
    Returns:
        Language code (default: 'en')
    """
    if user and hasattr(user, 'profile'):
        return user.profile.preferred_language or 'en'
    return 'en'


def translate_for_user(text: str, user) -> str:
    """
    Translate text to user's preferred language.
    
    Args:
        text: Text to translate
        user: User instance
        
    Returns:
        Translated text
    """
    if not text:
        return text
    
    target_lang = get_user_language(user)
    if target_lang == 'en':
        return text
    
    translated = translate_text(text, target_lang)
    return translated if translated else text


def translate_for_language(text: str, lang_code: str) -> str:
    """
    Translate text to specified language.
    
    Args:
        text: Text to translate
        lang_code: Target language code
        
    Returns:
        Translated text
    """
    if not text or not lang_code:
        return text
    
    if lang_code == 'en' or lang_code not in get_translation_service().get_supported_languages():
        return text
    
    translated = translate_text(text, lang_code)
    return translated if translated else text


def get_language_name(lang_code: str) -> str:
    """
    Get language name from language code.
    
    Args:
        lang_code: Language code (e.g., 'hi', 'te')
        
    Returns:
        Language name (e.g., 'Hindi', 'Telugu')
    """
    service = get_translation_service()
    languages = service.get_supported_languages()
    return languages.get(lang_code.lower(), lang_code.upper())


def get_all_languages() -> dict:
    """
    Get all supported languages.
    
    Returns:
        Dictionary of language codes and names
    """
    service = get_translation_service()
    return service.get_supported_languages()

