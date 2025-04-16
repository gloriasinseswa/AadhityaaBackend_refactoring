from rest_framework import routers
from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    AccountViewSet, 
    LocationViewSet, 
    LanguageViewSet,
    ProfileViewSet,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('', AccountViewSet, basename='accounts')
router.register('profiles', ProfileViewSet, basename='profile')
router.register('languages', LanguageViewSet, basename='language')

router.register(r'profile/locations', LocationViewSet, basename='location')

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/me/', ProfileViewSet.as_view({'get': 'retrieve', 'put': 'update'}), name='profile-me'),
    path('locations/default/', LocationViewSet.as_view({'get': 'default'}), name='location-default'),
    path('locations/<int:pk>/set-default/', LocationViewSet.as_view({'post': 'set_default'}), name='location-set-default'),
] + router.urls 