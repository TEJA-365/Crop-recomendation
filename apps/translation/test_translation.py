"""
Quick test script to verify translation service is working.
Run with: python manage.py shell < apps/translation/test_translation.py
"""
from apps.translation.services import translate_text, get_translation_service

print("Testing Translation Service...")
print("=" * 50)

# Test basic translation
test_text = "Hello"
target_lang = "hi"

print(f"Translating '{test_text}' to {target_lang}...")
result = translate_text(test_text, target_lang)
print(f"Result: {result}")
print()

# Test service initialization
service = get_translation_service()
print(f"Google Translate available: {service.google_trans is not None}")
print(f"LibreTranslate URL: {service.libre_translate_url}")
print()

# Test multiple translations
test_texts = ["Dashboard", "Welcome", "Settings", "Profile"]
print("Testing multiple translations:")
for text in test_texts:
    result = translate_text(text, "hi")
    print(f"  '{text}' -> '{result}'")

print()
print("Test complete!")

