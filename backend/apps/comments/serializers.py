from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Comment

User = get_user_model()


class CommentAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'reputation_score']


class ReplySerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'content', 'like_count',
            'score', 'created_at', 'updated_at', 'is_deleted',
        ]


class CommentSerializer(serializers.ModelSerializer):
    author = CommentAuthorSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    is_reply = serializers.BooleanField(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id', 'author', 'parent', 'content',
            'like_count', 'reply_count', 'score',
            'is_reply', 'replies',
            'created_at', 'updated_at', 'is_deleted',
        ]
        read_only_fields = [
            'id', 'like_count', 'reply_count',
            'score', 'is_reply', 'created_at', 'updated_at',
        ]


class CommentCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=10000)


class CommentEditSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=10000)