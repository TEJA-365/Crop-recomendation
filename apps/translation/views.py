"""
Views for translation and language switching.
"""
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from apps.users.models import UserProfile
from .utils import get_all_languages
from .services import get_translation_service


@login_required
@require_http_methods(["POST"])
def set_language(request):
    """
    Set user's preferred language.
    
    POST parameters:
        language: Language code (e.g., 'hi', 'te')
        next: URL to redirect to after language change
    """
    language = request.POST.get('language', 'en')
    next_url = request.POST.get('next', '/')
    
    # Validate language
    service = get_translation_service()
    if not service.is_language_supported(language):
        messages.error(request, f'Language "{language}" is not supported.')
        return redirect(next_url)
    
    # Update user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    profile.preferred_language = language
    profile.save()
    
    messages.success(request, f'Language changed to {get_all_languages().get(language, language)}.')
    
    # If AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'language': language,
            'language_name': get_all_languages().get(language, language)
        })
    
    return redirect(next_url)
