from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import LimitOffsetPagination

from account.models import Comment, Post, Like
from api.v1.post.serializers import CommentSerializer, LikeSerializer, PostSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    pagination_class = LimitOffsetPagination
    permission_classes = [permissions.IsAuthenticated] 
    http_method_names = ['get', 'post', 'put', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        print("Create method called with data:", request.data)
        return super().create(request, *args, **kwargs)
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_permissions(self):
        if self.action in ['create', 'like', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated()]
        return []

    def get_serializer_context(self):
        return {'request': self.request}

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """Get details of a specific post"""
        post = self.get_object()
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @action(detail=True, methods=['put'])
    def update_post(self, request, pk=None):
        """Update a specific post"""
        post = self.get_object()
        if post.user != request.user:
            return Response(
                {"error": "You cannot edit someone else's post."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(post, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['delete'])
    def delete_post(self, request, pk=None):
        """Delete a specific post"""
        post = self.get_object()
        if post.user != request.user:
            return Response(
                {"error": "You cannot delete someone else's post."},
                status=status.HTTP_403_FORBIDDEN
            )
        post.delete()
        return Response(
            {"message": "Post deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
    @action(detail=True, methods=['post'], serializer_class=LikeSerializer)
    def like(self, request, pk=None):
        """Like or unlike a post"""
        post = self.get_object()
        existing_like = Like.objects.filter(user=request.user, post=post).first()

        if existing_like:
            existing_like.delete()
            return Response({
                'status': 'unliked', 
                'likes_count': post.likes.count()
            }, status=status.HTTP_200_OK)
        else:
            Like.objects.create(user=request.user, post=post)
            return Response({
                'status': 'liked', 
                'likes_count': post.likes.count()
            }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='comments')
    def add_comment(self, request, pk=None):
        """Add a comment to a specific post"""
        if not request.user.is_authenticated:
            return Response(
                {"error": "Authentication required to add comments."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
            
        post = self.get_object()
        serializer = CommentSerializer(data={
            'post': post.id,
            'comment_text': request.data.get('content')
        }, context={'request': request})
        
        if serializer.is_valid():
            serializer.save(user=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing comments on posts.
    arg: post_id: ID of the post to which the comment belongs.
    arg: parent_id: ID of the parent comment if it's a reply.
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
            
        queryset = Comment.objects.all().order_by('-created_at')
        if 'parent_id' in self.kwargs:
            return queryset.filter(parent_id=self.kwargs['parent_id'])
            
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        """Get replies for a specific comment"""
        comment = self.get_object()
        replies = Comment.objects.filter(parent=comment).order_by('-created_at')
        page = self.paginate_queryset(replies)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)