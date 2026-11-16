from django.urls import path
from routes.views import OptimizeView, health, demo
urlpatterns = [path('api/v1/routes/optimize/', OptimizeView.as_view()), path('health/', health), path('demo/', demo)]
