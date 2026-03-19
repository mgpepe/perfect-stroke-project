import json


def parse_filter_ids(request):
    """Parse filter query param for ID-based filtering. Expects ?filter={"Id":["id1","id2"]}"""
    filter_param = request.query_params.get('filter')
    if not filter_param:
        return None
    try:
        parsed = json.loads(filter_param)
        return parsed.get('Id') or parsed.get('id')
    except (json.JSONDecodeError, TypeError):
        return None


def parse_range_notation(notation):
    """Parse range notation like '1-5,7,9-10' into a list of integers."""
    result = []
    for part in notation.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            result.extend(range(int(start), int(end) + 1))
        else:
            result.append(int(part))
    return result
