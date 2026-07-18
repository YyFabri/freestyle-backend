import os

from django.core.management import call_command
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets

from .models import Freestyler, Competition, Season, Matchday, Battle, Standing
from .serializers import (
    FreestylerSerializer, CompetitionSerializer, SeasonSerializer,
    MatchdaySerializer, BattleSerializer, StandingSerializer,
)


class FreestylerViewSet(viewsets.ModelViewSet):
    queryset = Freestyler.objects.all()
    serializer_class = FreestylerSerializer


class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer


class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    filter_backends = [DjangoFilterBackend]
    # /api/seasons/?competition=1  -> temporadas de una liga puntual
    filterset_fields = ['competition']


class MatchdayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Matchday.objects.all()
    serializer_class = MatchdaySerializer
    filter_backends = [DjangoFilterBackend]
    # /api/matchdays/?season=3
    filterset_fields = ['season']


class BattleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Battle.objects.all()
    serializer_class = BattleSerializer
    filter_backends = [DjangoFilterBackend]
    # /api/battles/?matchday=1  o  /api/battles/?matchday__season=3&status=finished
    filterset_fields = ['matchday', 'matchday__season', 'status']


class StandingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Standing.objects.all()
    serializer_class = StandingSerializer
    filter_backends = [DjangoFilterBackend]
    # /api/standings/?season=3  (id, lo más simple y rápido)
    # /api/standings/?season__competition=1  o  ?season__name=2024-2025 (por si hace falta)
    filterset_fields = {
        'season': ['exact'],
        'season__competition': ['exact'],
        'season__name': ['exact'],
    }


def trigger_scraper(request):
    # Protegemos la URL con un token para que nadie más pueda ejecutar el scraper
    token = request.GET.get('token')
    secret_token = os.environ.get('SCRAPER_TOKEN', 'mi-token-secreto-local')

    if token != secret_token:
        return JsonResponse({'error': 'No autorizado'}, status=403)

    try:
        call_command('sync_stats')
        return JsonResponse({'status': 'Scraping completado con éxito'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)