from django.db.models import Q


def _as_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _get_list(params, key):
    if hasattr(params, 'getlist'):
        return [value for value in params.getlist(key) if value]
    value = params.get(key) if params else None
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [item for item in value if item]
    return [value]


def filter_spaces(queryset, params):
    q = (params.get('q') or params.get('search') or '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(address__icontains=q) |
            Q(description__icontains=q)
        )

    category = (params.get('category') or '').strip()
    if category:
        queryset = queryset.filter(category__slug=category)

    capacity_min = _as_int(params.get('capacity_min'))
    capacity_max = _as_int(params.get('capacity_max'))
    price_min = _as_int(params.get('price_min'))
    price_max = _as_int(params.get('price_max'))

    if capacity_min is not None:
        queryset = queryset.filter(capacity__gte=capacity_min)
    if capacity_max is not None:
        queryset = queryset.filter(capacity__lte=capacity_max)
    if price_min is not None:
        queryset = queryset.filter(price_per_hour__gte=price_min)
    if price_max is not None:
        queryset = queryset.filter(price_per_hour__lte=price_max)

    for amenity_slug in _get_list(params, 'amenities'):
        queryset = queryset.filter(amenities__slug=amenity_slug)

    ordering = {
        'price_asc': 'price_per_hour',
        'price_desc': '-price_per_hour',
        'capacity_asc': 'capacity',
        'capacity_desc': '-capacity',
    }.get(params.get('sort'))
    if ordering:
        queryset = queryset.order_by(ordering, 'name')

    return queryset.distinct()
