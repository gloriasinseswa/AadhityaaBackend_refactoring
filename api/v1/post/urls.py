from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet, CommentViewSet

router = DefaultRouter()
print("Registering PostViewSet with router")
router.register(r'', PostViewSet, basename='posts')
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = router.urls
