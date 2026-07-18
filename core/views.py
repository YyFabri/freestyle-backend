from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from .models import Standing, Battle, Competition
from .serializers import StandingSerializer, BattleSerializer, CompetitionSerializer

from django.core.management import call_command
from django.http import JsonResponse
import os
from rest_framework import viewsets
from .models import Freestyler, Competition, Season, Matchday, Battle, Standing
from .serializers import (
    FreestylerSerializer, CompetitionSerializer, SeasonSerializer, 
    MatchdaySerializer, BattleSerializer, StandingSerializer
)

class FreestylerViewSet(viewsets.ModelViewSet):
    queryset = Freestyler.objects.all()
    serializer_class = FreestylerSerializer

class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

class StandingViewSet(viewsets.ModelViewSet):
    queryset = Standing.objects.all()
    serializer_class = StandingSerializer
    filter_backends = [DjangoFilterBackend]
    # Filtramos por nombre de competencia y nombre de temporada
    filterset_fields = {
        'season__competition__name': ['exact'],
        'season__name': ['exact'],
    }

class CompetitionViewSet(viewsets.ModelViewSet):
    queryset = Competition.objects.all()
    serializer_class = CompetitionSerializer

class SeasonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer

class MatchdayViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Matchday.objects.all()
    serializer_class = MatchdaySerializer

class BattleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Battle.objects.all()
    serializer_class = BattleSerializer
    # Permite filtrar por jornada en la URL: /api/battles/?matchday=1
    filterset_fields = ['matchday', 'status'] 

class StandingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Standing.objects.all()
    serializer_class = StandingSerializer
    # Permite filtrar posiciones por temporada: /api/standings/?season=1
    filterset_fields = ['season']

def trigger_scraper(request):
    # Protegemos la URL con un token para que nadie más pueda ejecutar el scraper
    token = request.GET.get('token')
    secret_token = os.environ.get('SCRAPER_TOKEN', 'mi-token-secreto-local')
    
    if token != secret_token:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    try:
        # Esto ejecuta "python manage.py sync_stats" por detrás
        call_command('sync_stats')
        return JsonResponse({'status': 'Scraping completado con éxito'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)