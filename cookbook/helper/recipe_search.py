from functools import reduce

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

from cookbook.models import ViewLog
from recipes import settings


def search_recipes(request, queryset, params):
    search_string = params.get('query', '')
    search_keywords = params.getlist('keywords', [])
    search_foods = params.getlist('foods', [])
    search_books = params.getlist('books', [])

    search_keywords_or = params.get('keywords_or', True)
    search_foods_or = params.get('foods_or', True)
    search_books_or = params.get('books_or', True)

    search_internal = params.get('internal', None)
    search_random = params.get('random', False)
    search_last_viewed = int(params.get('last_viewed', 0))

    if search_last_viewed > 0:
        last_viewed_recipes = ViewLog.objects.filter(created_by=request.user, space=request.space).values_list('recipe__pk', flat=True).distinct()
        # TODO filter by created by in last two weeks and re add limit to recipe selection (after reversing the order)
        # Distinct does not work with order by
        return queryset.filter(pk__in=list(set(last_viewed_recipes)))

    if settings.DATABASES['default']['ENGINE'] in ['django.db.backends.postgresql_psycopg2',
                                                   'django.db.backends.postgresql']:
        queryset = queryset.annotate(similarity=TrigramSimilarity('name', search_string), ).filter(
            Q(similarity__gt=0.1) | Q(name__unaccent__icontains=search_string)).order_by('-similarity')
    else:
        queryset = queryset.filter(name__icontains=search_string)

    if len(search_keywords) > 0:
        if search_keywords_or == 'true':
            queryset = queryset.filter(keywords__id__in=search_keywords)
        else:
            for k in search_keywords:
                queryset = queryset.filter(keywords__id=k)

    if len(search_foods) > 0:
        if search_foods_or == 'true':
            queryset = queryset.filter(steps__ingredients__food__id__in=search_foods)
        else:
            for k in search_foods:
                queryset = queryset.filter(steps__ingredients__food__id=k)

    if len(search_books) > 0:
        if search_books_or == 'true':
            queryset = queryset.filter(recipebookentry__book__id__in=search_books)
        else:
            for k in search_books:
                queryset = queryset.filter(recipebookentry__book__id=k)

    queryset = queryset.distinct()

    if search_internal == 'true':
        queryset = queryset.filter(internal=True)

    if search_random == 'true':
        queryset = queryset.order_by("?")

    return queryset
