from django.urls import path
from . import views

app_name = 'farms'

urlpatterns = [
    # Farm URLs
    path('', views.farm_list, name='farm_list'),
    path('create/', views.farm_create, name='farm_create'),
    path('<int:pk>/', views.farm_detail, name='farm_detail'),
    path('<int:pk>/update/', views.farm_update, name='farm_update'),
    path('<int:pk>/delete/', views.farm_delete, name='farm_delete'),
    
    # Field URLs
    path('fields/', views.field_list, name='field_list'),
    path('fields/create/', views.field_create, name='field_create'),
    path('fields/<int:pk>/', views.field_detail, name='field_detail'),
    path('fields/<int:pk>/update/', views.field_update, name='field_update'),
    path('fields/<int:pk>/delete/', views.field_delete, name='field_delete'),
]

