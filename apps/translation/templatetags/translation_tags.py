"""
Django template tags for translation.
"""
from django import template
from django.utils.safestring import mark_safe
from ..services import translate_text
from ..utils import translate_for_user, get_language_name

register = template.Library()


@register.simple_tag(takes_context=True)
def translate(context, text, target_lang=None):
    """
    Translate text in template.
    
    Usage:
        {% translate "Hello" "hi" %}
        {% translate "Welcome" %}  (uses user's preferred language)
    """
    if not text:
        return text
    
    # Get target language
    if not target_lang:
        user = context.get('user')
        if user and user.is_authenticated and hasattr(user, 'profile'):
            target_lang = user.profile.preferred_language or 'en'
        else:
            target_lang = 'en'
    
    # Translate
    translated = translate_text(text, target_lang)
    return translated if translated else text


@register.simple_tag(takes_context=True)
def translate_user(context, text):
    """
    Translate text to user's preferred language or current language from context.
    Uses pre-translated strings from context for better performance.
    
    Usage:
        {% translate_user "Hello" %}
    """
    if not text:
        return text
    
    # Try to get language from context (set by context processor)
    current_language = context.get('current_language', 'en')
    
    # If user is authenticated, use their preferred language
    user = context.get('user')
    if user and user.is_authenticated and hasattr(user, 'profile'):
        target_lang = user.profile.preferred_language or current_language
    else:
        target_lang = current_language
    
    # Don't translate if target is English
    if target_lang == 'en':
        return text
    
    # First, check pre-translated strings from context (fast lookup)
    translated_strings = context.get('translated_strings', {})
    if text in translated_strings:
        return translated_strings[text]
    
    # Fallback to on-demand translation (slower, but works for dynamic text)
    translated = translate_text(text, target_lang)
    return translated if translated else text


@register.simple_tag
def language_name(lang_code):
    """
    Get language name from code.
    
    Usage:
        {% language_name "hi" %}
    """
    return get_language_name(lang_code)

