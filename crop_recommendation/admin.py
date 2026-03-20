"""
Custom admin site configuration for Crop Recommendation System.
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class CropRecommendationAdminSite(AdminSite):
    """
    Custom admin site with branding.
    """
    site_header = "Crop Recommendation System Administration"
    site_title = "Crop Recommendation Admin"
    index_title = "Welcome to Crop Recommendation Administration"


# Create custom admin site instance
admin_site = CropRecommendationAdminSite(name='crop_recommendation_admin')

