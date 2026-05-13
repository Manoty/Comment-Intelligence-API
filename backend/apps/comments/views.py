import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.core.exceptions import PermissionDenied, ValidationError

from apps.ranking.selectors import RankingSelector

from .services import CommentService
from .selectors import CommentSelector
from .serializers import (
    CommentSerializer,
    CommentCreateSerializer,
    CommentEditSerializer,
    ReplySerializer,
)

logger = logging.getLogger(__name__)


class CommentListCreateView(APIView):
    """
    [COMMENT-05a]
    GET  /api/comments/        → list root comments (sorted)
    POST /api/comments/        → create root comment
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request):
        sort = request.query_params.get('sort', 'latest')
        comments = RankingSelector.get_comments_by_sort(sort=sort)

        page_size = int(request.query_params.get('page_size', 20))
        page = int(request.query_params.get('page', 1))
        start = (page - 1) * page_size
        end = start + page_size

        paginated = comments[start:end]
        serializer = CommentSerializer(paginated, many=True)

        return Response({
            'page': page,
            'page_size': page_size,
            'sort': sort,
            'results': serializer.data,
        })

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = CommentService.create_comment(
                author=request.user,
                content=serializer.validated_data['content'],
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            CommentSerializer(comment).data,
            status=status.HTTP_201_CREATED,
        )


class CommentDetailView(APIView):
    """
    [COMMENT-05b]
    GET    /api/comments/{id}/  → get single comment with replies
    PATCH  /api/comments/{id}/  → edit comment (author only)
    DELETE /api/comments/{id}/  → soft delete (author only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, comment_id):
        comment = CommentSelector.get_comment_by_id(comment_id)
        if not comment:
            return Response(
                {'detail': 'Comment not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CommentSerializer(comment).data)

    def patch(self, request, comment_id):
        serializer = CommentEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            comment = CommentService.edit_comment(
                comment_id=comment_id,
                requesting_user=request.user,
                content=serializer.validated_data['content'],
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(CommentSerializer(comment).data)

    def delete(self, request, comment_id):
        try:
            CommentService.delete_comment(
                comment_id=comment_id,
                requesting_user=request.user,
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except PermissionDenied as e:
            return Response({'detail': str(e)}, status=status.HTTP_403_FORBIDDEN)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CommentReplyView(APIView):
    """
    [COMMENT-05c]
    GET  /api/comments/{id}/replies/  → list direct replies
    POST /api/comments/{id}/reply/    → post a reply
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, comment_id):
        replies = CommentSelector.get_replies(parent_id=comment_id)
        serializer = ReplySerializer(replies, many=True)
        return Response({'results': serializer.data})

    def post(self, request, comment_id):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            reply = CommentService.create_reply(
                author=request.user,
                parent_id=comment_id,
                content=serializer.validated_data['content'],
            )
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            ReplySerializer(reply).data,
            status=status.HTTP_201_CREATED,
        )