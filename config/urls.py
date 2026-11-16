from django.urls import path

from routes.views import OptimizeView, city_search, demo, health, landing

urlpatterns = [
    path('', landing, name='landing'),
    path('demo/', demo, name='demo'),
    path('health/', health, name='health'),
    path('api/v1/cities/', city_search, name='city_search'),
    path('api/v1/routes/optimize/', OptimizeView.as_view(), name='optimize'),
]
