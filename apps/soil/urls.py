from django.urls import path
from . import views

app_name = 'soil'

urlpatterns = [
    path('', views.soil_data_list, name='soil_data_list'),
    path('options/', views.soil_data_options, name='soil_data_options'),
    path('add/', views.soil_data_add, name='soil_data_add'),
    path('fetch/', views.soil_data_fetch, name='soil_data_fetch'),
    path('fetch-ajax/', views.soil_data_fetch_ajax, name='soil_data_fetch_ajax'),
    path('<int:pk>/', views.soil_data_detail, name='soil_data_detail'),
]

