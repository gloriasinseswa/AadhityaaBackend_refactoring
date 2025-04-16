from rest_framework.routers import DefaultRouter
from api.v1.story.views import StoryViewSet

router = DefaultRouter()
router.register(r'', StoryViewSet, basename='story')
urlpatterns = router.urls

