"""
Translation service for multilingual support.
Supports Google Translate API (via deep-translator) and LibreTranslate as fallback.
"""
import logging
from typing import Optional, Dict, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import hashlib

logger = logging.getLogger(__name__)

# Supported languages mapping
LANGUAGE_CODES = {
    'en': 'English',
    'hi': 'Hindi',
    'te': 'Telugu',
    'ta': 'Tamil',
    'kn': 'Kannada',
    'mr': 'Marathi',
}

# Reverse mapping for language names
LANGUAGE_NAMES = {v: k for k, v in LANGUAGE_CODES.items()}


class TranslationService:
    """Translation service with multiple provider support."""
    
    # Default cache timeout in seconds (24 hours for better performance)
    DEFAULT_CACHE_TIMEOUT = 86400
    
    def __init__(self):
        self.google_trans = None
        self.libre_translate_url = getattr(settings, 'LIBRETRANSLATE_URL', None)
        self.libre_translate_api_key = getattr(settings, 'LIBRETRANSLATE_API_KEY', None)
        self.cache_timeout = getattr(settings, 'TRANSLATION_CACHE_TIMEOUT', self.DEFAULT_CACHE_TIMEOUT)
        self._init_google_trans()
    
    def _init_google_trans(self):
        """Initialize Google Translate client."""
        try:
            from deep_translator import GoogleTranslator
            # Test translation to verify it works
            try:
                test_translator = GoogleTranslator(target='hi')
                test_result = test_translator.translate('Hello')
                if test_result:
                    logger.info("Google Translate initialized and tested successfully")
                    self.google_trans = True  # Mark as available
                else:
                    logger.warning("Google Translate initialized but test translation failed")
            except Exception as test_e:
                logger.warning(f"Google Translate test failed: {test_e}")
                self.google_trans = False
        except ImportError:
            logger.warning("deep-translator not available. Install with: pip install deep-translator")
            self.google_trans = False
        except Exception as e:
            logger.warning(f"Failed to initialize Google Translate: {e}")
            self.google_trans = False
    
    def _get_cache_key(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> str:
        """Generate cache key for translation."""
        key_parts = [text, target_lang]
        if source_lang:
            key_parts.append(source_lang)
        key_string = '|'.join(key_parts)
        return f"translation:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _translate_google(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> Optional[str]:
        """Translate using Google Translate API via deep-translator."""
        if not self.google_trans:
            return None
            
        try:
            from deep_translator import GoogleTranslator
            
            # Convert language code if needed
            lang_code = self._normalize_language_code(target_lang)
            
            # Translate using deep-translator
            if source_lang:
                source_code = self._normalize_language_code(source_lang)
                translator = GoogleTranslator(source=source_code, target=lang_code)
            else:
                translator = GoogleTranslator(target=lang_code)
            
            result = translator.translate(text)
            return result if result else None
        except ImportError:
            logger.error("deep-translator not available")
            return None
        except Exception as e:
            logger.error(f"Google Translate error: {e}")
            return None
    
    def _translate_libre(self, text: str, target_lang: str, source_lang: Optional[str] = None) -> Optional[str]:
        """Translate using LibreTranslate API."""
        if not self.libre_translate_url:
            return None
        
        try:
            import requests
            
            # Convert language code if needed
            lang_code = self._normalize_language_code(target_lang)
            source_code = self._normalize_language_code(source_lang) if source_lang else 'auto'
            
            url = f"{self.libre_translate_url.rstrip('/')}/translate"
            payload = {
                'q': text,
                'source': source_code,
                'target': lang_code,
                'format': 'text'
            }
            
            headers = {}
            if self.libre_translate_api_key:
                headers['Authorization'] = f'Bearer {self.libre_translate_api_key}'
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            if 'translatedText' in data:
                return data['translatedText']
            return None
        except ImportError:
            logger.warning("requests library not available for LibreTranslate")
            return None
        except Exception as e:
            logger.error(f"LibreTranslate error: {e}")
            return None
    
    def _normalize_language_code(self, lang_code: str) -> str:
        """Normalize language code for translation APIs."""
        # Map our language codes to API codes
        lang_mapping = {
            'en': 'en',
            'hi': 'hi',
            'te': 'te',
            'ta': 'ta',
            'kn': 'kn',
            'mr': 'mr',
        }
        return lang_mapping.get(lang_code.lower(), lang_code.lower())
    
    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: Optional[str] = None,
        use_cache: bool = True
    ) -> Optional[str]:
        """
        Translate text to target language.
        
        Args:
            text: Text to translate
            target_lang: Target language code (e.g., 'hi', 'te')
            source_lang: Source language code (optional, auto-detect if not provided)
            use_cache: Whether to use cache (default: True)
            
        Returns:
            Translated text or None if translation fails
        """
        if not text or not text.strip():
            return text
        
        # Check if translation is needed
        if target_lang == 'en' or target_lang not in LANGUAGE_CODES:
            return text
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(text, target_lang, source_lang)
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Translation cache hit for: {text[:50]}...")
                return cached_result
        
        # Try Google Translate first
        translated = self._translate_google(text, target_lang, source_lang)
        
        # Fallback to LibreTranslate
        if not translated and self.libre_translate_url:
            logger.info(f"Falling back to LibreTranslate for: {text[:50]}...")
            translated = self._translate_libre(text, target_lang, source_lang)
        
        # Log if translation failed
        if not translated:
            logger.warning(f"Translation failed for text: '{text[:50]}...' to language: {target_lang}")
        
        # Cache result if successful
        if translated and use_cache:
            cache_key = self._get_cache_key(text, target_lang, source_lang)
            cache.set(cache_key, translated, self.cache_timeout)
        
        return translated
    
    def translate_batch(
        self,
        texts: List[str],
        target_lang: str,
        source_lang: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Translate multiple texts efficiently with caching.
        Returns a dictionary mapping original text to translated text.
        
        Args:
            texts: List of texts to translate
            target_lang: Target language code
            source_lang: Source language code (optional)
            
        Returns:
            Dictionary mapping original text to translated text
        """
        if not texts:
            return {}
        
        # Check if translation is needed
        if target_lang == 'en' or target_lang not in LANGUAGE_CODES:
            return {text: text for text in texts}
        
        results = {}
        texts_to_translate = []
        text_indices = []
        
        # Check cache for each text
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results[text] = text
                continue
            
            cache_key = self._get_cache_key(text, target_lang, source_lang)
            cached_result = cache.get(cache_key)
            if cached_result:
                results[text] = cached_result
            else:
                texts_to_translate.append(text)
                text_indices.append(i)
        
        # Batch translate remaining texts
        if texts_to_translate:
            try:
                from deep_translator import GoogleTranslator
                lang_code = self._normalize_language_code(target_lang)
                translator = GoogleTranslator(target=lang_code)
                
                # Translate in batches (Google Translate has limits)
                batch_size = 10
                for batch_start in range(0, len(texts_to_translate), batch_size):
                    batch = texts_to_translate[batch_start:batch_start + batch_size]
                    for text in batch:
                        try:
                            translated = translator.translate(text)
                            if translated:
                                results[text] = translated
                                # Cache the result
                                cache_key = self._get_cache_key(text, target_lang, source_lang)
                                cache.set(cache_key, translated, self.cache_timeout)
                            else:
                                results[text] = text
                        except Exception as e:
                            logger.warning(f"Batch translation failed for '{text[:50]}...': {e}")
                            results[text] = text
            except Exception as e:
                logger.error(f"Batch translation error: {e}")
                # Fallback to individual translation
                for text in texts_to_translate:
                    if text not in results:
                        translated = self.translate(text, target_lang, source_lang)
                        results[text] = translated if translated else text
        
        return results
    
    def detect_language(self, text: str) -> Optional[str]:
        """
        Detect the language of the given text.
        
        Args:
            text: Text to detect language for
            
        Returns:
            Language code (e.g., 'en', 'hi') or None if detection fails
        """
        if not text or not text.strip():
            return None
        
        # Check cache
        cache_key = f"lang_detect:{hashlib.md5(text.encode()).hexdigest()}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Try Google Translate detection
        if self.google_trans:
            try:
                result = self.google_trans.detect(text)
                if result and hasattr(result, 'lang'):
                    lang_code = result.lang.lower()
                    # Normalize to our language codes
                    if lang_code in LANGUAGE_CODES:
                        cache.set(cache_key, lang_code, self.CACHE_TIMEOUT)
                        return lang_code
            except Exception as e:
                logger.error(f"Language detection error: {e}")
        
        # Default to English if detection fails
        return 'en'
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get dictionary of supported language codes and names."""
        return LANGUAGE_CODES.copy()
    
    def is_language_supported(self, lang_code: str) -> bool:
        """Check if a language code is supported."""
        return lang_code.lower() in LANGUAGE_CODES


# Singleton instance
_translation_service = None


def get_translation_service() -> TranslationService:
    """Get singleton translation service instance."""
    global _translation_service
    if _translation_service is None:
        _translation_service = TranslationService()
    return _translation_service


def translate_text(text: str, target_lang: str, source_lang: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to translate text.
    
    Args:
        text: Text to translate
        target_lang: Target language code
        source_lang: Source language code (optional)
        
    Returns:
        Translated text or original text if translation fails
    """
    if not text:
        return text
    
    service = get_translation_service()
    translated = service.translate(text, target_lang, source_lang)
    return translated if translated else text


def detect_language(text: str) -> Optional[str]:
    """
    Convenience function to detect language.
    
    Args:
        text: Text to detect language for
        
    Returns:
        Language code or 'en' as default
    """
    if not text:
        return 'en'
    
    service = get_translation_service()
    detected = service.detect_language(text)
    return detected if detected else 'en'

