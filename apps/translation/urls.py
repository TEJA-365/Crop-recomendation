"""
URL patterns for translation app.
"""
from django.urls import path
from . import views

app_name = 'translation'

urlpatterns = [
    path('set-language/', views.set_language, name='set_language'),
]

