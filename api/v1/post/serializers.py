from rest_framework import serializers

from account.models import Category, Comment, Like, Location, Post
from api.v1.auth.serializers import LocationSerializer
from api.v1.category.serializers import CategorySerializer


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    is_liked_by_user = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()
    zip_code = serializers.ListSerializer(
        child=serializers.PrimaryKeyRelatedField(queryset=Location.objects.all()),
        write_only=True
    )
    zip_code_details = LocationSerializer(source='location', many=True, read_only=True)
    categories_details = CategorySerializer(source='categories', many=True, read_only=True)
    categories = serializers.ListSerializer(
        child=serializers.PrimaryKeyRelatedField(queryset=Category.objects.all()),
        write_only=True
    )

    class Meta:
        model = Post
        fields = [
            'id', 'content_type', 'text_content', 'media_file', 'link',
            'zip_code', 'zip_code_details', 'categories', 'categories_details',
            'likes_count', 'is_liked_by_user', 'user', 'comment_number', 'created_at'
        ]

    def create(self, validated_data):
        categories_data = validated_data.pop('categories', [])
        zip_code_data = validated_data.pop('zip_code', [])
        post = Post.objects.create(**validated_data)
        if categories_data:
            post.categories.set(categories_data)
        if zip_code_data:
            post.location.set(zip_code_data)

        return post

    def validate(self, data):
        content_type = data.get("content_type")
        text_content = data.get("text_content")
        media_file = data.get("media_file")
        link = data.get("link")

        if content_type not in dict(Post.POST_TYPES):
            raise serializers.ValidationError({"content_type": "Invalid post type."})

        if content_type == "text":
            if not text_content:
                raise serializers.ValidationError({"text_content": "A text post must have text content."})
            if media_file or link:
                raise serializers.ValidationError({"error": "A text post cannot have media or a link."})

        elif content_type in ["image", "video", "audio", "document"]:
            if not media_file:
                raise serializers.ValidationError({"media_file": f"A {content_type} post must have a media file."})
            if link:
                raise serializers.ValidationError({"error": f"A {content_type} post cannot have a link."})

        elif content_type == "link":
            if not link:
                raise serializers.ValidationError({"link": "A link post must have a valid link."})
            if media_file:
                raise serializers.ValidationError({"error": "A link post cannot have a media file."})

        return data

    def get_comment_number(self, obj):
        """Returns the number of comments for a given post"""
        return Comment.objects.filter(post=obj).count()

    def get_user(self, obj):
        """Returns the full name of the post's author"""
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else None

    def get_likes_count(self, obj):
        """Returns the number of likes for a given post"""
        return obj.likes.count()

    def get_is_liked_by_user(self, obj):
        """Checks if the authenticated user has liked the post"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Like.objects.filter(post=obj, user=request.user).exists()
        return False


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'comment_text', 'created_at']  # Changed from text_content to comment_text
        read_only_fields = ['user']

    def get_user(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user else None


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'post', 'user', 'created_at']
        read_only_fields = ['user']