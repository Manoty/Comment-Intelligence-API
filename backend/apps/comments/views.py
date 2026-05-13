import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError

from apps.common.pagination import CommentPagination
from apps.common.filters import CommentFilter
from apps.common.responses import created_response, no_content_response
from apps.common.throttles import CommentCreateThrottle
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
    [HARD-07a]
    GET  /api/comments/   → filtered, sorted, paginated list
    POST /api/comments/   → create comment (throttled)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_throttles(self):
        if self.request.method == 'POST':
            return [CommentCreateThrottle()]
        return super().get_throttles()

    def get(self, request):
        sort = request.query_params.get('sort', 'latest')
        qs   = RankingSelector.get_comments_by_sort(sort=sort)

        # Apply filters
        comment_filter = CommentFilter(request.query_params, queryset=qs)
        filtered_qs    = comment_filter.qs

        # Paginate
        paginator = CommentPagination()
        page      = paginator.paginate_queryset(filtered_qs, request)
        serializer = CommentSerializer(page, many=True)
        response   = paginator.get_paginated_response(serializer.data)
        response.data['sort'] = sort
        return response

    def post(self, request):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.create_comment(
            author=request.user,
            content=serializer.validated_data['content'],
        )
        return created_response(
            data=CommentSerializer(comment).data,
            message='Comment created.',
        )


class CommentDetailView(APIView):
    """
    [HARD-07b]
    GET    /api/comments/{id}/
    PATCH  /api/comments/{id}/
    DELETE /api/comments/{id}/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, comment_id):
        comment = CommentSelector.get_comment_by_id(comment_id)
        if not comment:
            from rest_framework.response import Response
            return Response(
                {'error': {'code': 'not_found', 'message': 'Comment not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return CommentSerializer(comment).data and \
               __import__('rest_framework.response', fromlist=['Response']).Response(
                   CommentSerializer(comment).data
               )

    def get(self, request, comment_id):
        from rest_framework.response import Response
        comment = CommentSelector.get_comment_by_id(comment_id)
        if not comment:
            return Response(
                {'error': {'code': 'not_found', 'message': 'Comment not found.'}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CommentSerializer(comment).data)

    def patch(self, request, comment_id):
        serializer = CommentEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = CommentService.edit_comment(
            comment_id=comment_id,
            requesting_user=request.user,
            content=serializer.validated_data['content'],
        )
        from rest_framework.response import Response
        return Response(CommentSerializer(comment).data)

    def delete(self, request, comment_id):
        CommentService.delete_comment(
            comment_id=comment_id,
            requesting_user=request.user,
        )
        return no_content_response()


class CommentReplyView(APIView):
    """
    [HARD-07c]
    GET  /api/comments/{id}/replies/
    POST /api/comments/{id}/reply/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_throttles(self):
        if self.request.method == 'POST':
            return [CommentCreateThrottle()]
        return super().get_throttles()

    def get(self, request, comment_id):
        from rest_framework.response import Response
        replies    = CommentSelector.get_replies(parent_id=comment_id)
        paginator  = CommentPagination()
        page       = paginator.paginate_queryset(replies, request)
        serializer = ReplySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request, comment_id):
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reply = CommentService.create_reply(
            author=request.user,
            parent_id=comment_id,
            content=serializer.validated_data['content'],
        )
        return created_response(
            data=ReplySerializer(reply).data,
            message='Reply created.',
        )