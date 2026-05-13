from django.urls import path
from .views import (
    CommentListCreateView,
    CommentDetailView,
    CommentReplyView,
)

urlpatterns = [
    path('', CommentListCreateView.as_view(), name='comment-list-create'),
    path('<uuid:comment_id>/', CommentDetailView.as_view(), name='comment-detail'),
    path('<uuid:comment_id>/replies/', CommentReplyView.as_view(), name='comment-replies'),
    path('<uuid:comment_id>/reply/', CommentReplyView.as_view(), name='comment-reply-create'),
]