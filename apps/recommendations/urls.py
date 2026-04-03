from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommendation_list, name='recommendation_list'),
    path('request/', views.recommendation_request, name='recommendation_request'),
    path('field/<int:field_pk>/', views.recommendation_for_field, name='recommendation_for_field'),
    path('<int:pk>/', views.recommendation_detail, name='recommendation_detail'),
]

