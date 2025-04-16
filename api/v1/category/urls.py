from django.urls import include,path
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')

urlpatterns = router.urls + [
    path('api/v1/', include(router.urls)),
    path('categories/create/', CategoryViewSet.as_view({'post': 'create'}), name='category-create'),
] + router.urls