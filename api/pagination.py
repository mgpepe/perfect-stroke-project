import json
from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class RangePagination(BasePagination):
    """
    Range-based pagination matching the .NET API behavior.
    Expects query param: ?range=[0,9]
    Returns Content-Range header: "items 0-9/100"
    """
    default_range = [0, 24]

    def paginate_queryset(self, queryset, request, view=None):
        self.total_count = queryset.count()
        range_param = request.query_params.get('range')

        if range_param:
            try:
                self.range = json.loads(range_param)
            except (json.JSONDecodeError, TypeError):
                self.range = self.default_range
        else:
            self.range = self.default_range

        start = self.range[0]
        end = self.range[1]
        self.start = start
        self.end = min(end, self.total_count - 1) if self.total_count > 0 else 0

        return list(queryset[start:end + 1])

    def get_paginated_response(self, data):
        resource = getattr(self, 'resource_name', 'items')
        response = Response(data)
        response['Content-Range'] = f'{resource} {self.start}-{self.end}/{self.total_count}'
        response['Access-Control-Expose-Headers'] = 'Content-Range'
        return response
