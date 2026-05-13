from rest_framework.response import Response
from rest_framework import status


def success_response(data=None, message: str = 'OK', status_code: int = 200) -> Response:
    """
    [HARD-02a] Standard success envelope.
    {
        "message": "OK",
        "data": { ... }
    }
    """
    payload = {'message': message}
    if data is not None:
        payload['data'] = data
    return Response(payload, status=status_code)


def created_response(data=None, message: str = 'Created') -> Response:
    """[HARD-02b] 201 Created shorthand."""
    return success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def no_content_response() -> Response:
    """[HARD-02c] 204 No Content shorthand."""
    return Response(status=status.HTTP_204_NO_CONTENT)


def paginated_response(*, page, page_size, sort=None, count=None, results) -> Response:
    """
    [HARD-02d] Consistent paginated list envelope.
    {
        "pagination": { "page": 1, "page_size": 20, "count": 100 },
        "sort": "latest",
        "results": [ ... ]
    }
    """
    pagination = {'page': page, 'page_size': page_size}
    if count is not None:
        pagination['count'] = count

    payload = {'pagination': pagination, 'results': results}
    if sort is not None:
        payload['sort'] = sort

    return Response(payload, status=status.HTTP_200_OK)