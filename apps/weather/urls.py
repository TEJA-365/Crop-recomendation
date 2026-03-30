from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.weather_data_list, name='weather_data_list'),
    path('options/', views.weather_data_options, name='weather_data_options'),
    path('fetch/', views.weather_data_fetch, name='weather_data_fetch'),
    path('add/', views.weather_data_add, name='weather_data_add'),
    path('forecast/', views.weather_forecast, name='weather_forecast'),
    path('fetch-ajax/', views.weather_data_fetch_ajax, name='weather_data_fetch_ajax'),
    path('<int:pk>/', views.weather_data_detail, name='weather_data_detail'),
]

