from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CommentPagination(PageNumberPagination):
    """
    [HARD-03] Page-number paginator with enforced ceiling.
    Query params: ?page=1&page_size=20
    Max page_size: 100 (hard cap — cannot be overridden by client)
    """
    page_size              = 20
    page_size_query_param  = 'page_size'
    max_page_size          = 100
    page_query_param       = 'page'

    def get_paginated_response(self, data):
        return Response({
            'pagination': {
                'page':      self.page.number,
                'page_size': self.get_page_size(self.request),
                'count':     self.page.paginator.count,
                'next':      self.get_next_link(),
                'previous':  self.get_previous_link(),
            },
            'results': data,
        })

    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'pagination': {
                    'type': 'object',
                    'properties': {
                        'page':      {'type': 'integer'},
                        'page_size': {'type': 'integer'},
                        'count':     {'type': 'integer'},
                        'next':      {'type': 'string', 'nullable': True},
                        'previous':  {'type': 'string', 'nullable': True},
                    }
                },
                'results': schema,
            }
        }