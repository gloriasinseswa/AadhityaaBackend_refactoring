from rest_framework import serializers
from account.models import Story, StoryImage

class StoryImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoryImage
        fields = ['id', 'image', 'created_at']

class StorySerializer(serializers.ModelSerializer):
    images = StoryImageSerializer(many=True, read_only=True)
    user = serializers.SerializerMethodField()

    class Meta:
        model = Story
        fields = ['id', 'user', 'images', 'created_at']
        read_only_fields = ['user']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'name': f"{obj.user.first_name} {obj.user.last_name}",
            'email': obj.user.email
        }

class StoryCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )

    class Meta:
        model = Story
        fields = ['images']
