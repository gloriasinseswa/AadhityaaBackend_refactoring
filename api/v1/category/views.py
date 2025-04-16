from rest_framework import viewsets, permissions
from account.models import Category, UserCategory
from api.v1.category.serializers import CategorySerializer, UserCategorySerializer

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from account.models import Category
from api.v1.category.serializers import CategorySerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']  # Explicitly define allowed methods
    
    # Debug the create method
    def create(self, request, *args, **kwargs):
        print("Create method called with data:", request.data)
        return super().create(request, *args, **kwargs)
    
    # Example of an action decorator
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        category = self.get_object()
        # Do something with the category
        return Response({'status': 'category activated'})
    
    # Example of a list action
    @action(detail=False, methods=['get'])
    def featured(self, request):
        featured_categories = Category.objects.filter(featured=True)
        serializer = self.get_serializer(featured_categories, many=True)
        return Response(serializer.data)

class UserCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = UserCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserCategory.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)