from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import AuthViewSet, UserProfileViewSet

v1_router = DefaultRouter()
v1_router.register(r'auth', AuthViewSet, basename='auth')
v1_router.register(r'profile', UserProfileViewSet, basename='profile')

urlpatterns = [
    path('', include(v1_router.urls)),
]
