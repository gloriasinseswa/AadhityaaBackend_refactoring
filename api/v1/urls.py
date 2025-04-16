from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.v1.post.views import PostViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'comments', CommentViewSet, basename='comments')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('api.v1.auth.urls')),
    path('categories/', include('api.v1.category.urls')),
    path('stories/', include('api.v1.story.urls')),
]