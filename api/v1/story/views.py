from rest_framework import viewsets, status
from rest_framework.views import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, MethodNotAllowed
from account.models import Story, StoryImage
from api.v1.story.serializer import StoryCreateSerializer, StorySerializer

class StoryViewSet(viewsets.ModelViewSet):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']
    
    def get_queryset(self):
        time_threshold = timezone.now() - timezone.timedelta(hours=24)
        return Story.objects.filter(
            created_at__gte=time_threshold
        ).order_by('-created_at')

    def get_serializer_class(self):
        if self.action == 'create':
            return StoryCreateSerializer
        return StorySerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        story = Story.objects.create(user=request.user)
        for image in serializer.validated_data['images']:
            StoryImage.objects.create(story=story, image=image)
        
        return Response(
            StorySerializer(story, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        if not kwargs.get('pk'):
            raise MethodNotAllowed('PUT/PATCH', detail='Cannot update multiple stories at once')
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You cannot update someone else's story")
            
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.get('partial', False))
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        if not kwargs.get('pk'):
            raise MethodNotAllowed('DELETE', detail='Cannot delete multiple stories at once')
        instance = self.get_object()
        if instance.user != request.user:
            raise PermissionDenied("You cannot delete someone else's story")
            
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
