from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FreestylerViewSet, CompetitionViewSet, SeasonViewSet, 
    MatchdayViewSet, BattleViewSet, StandingViewSet, trigger_scraper # <-- Importamos la nueva vista
)


router = DefaultRouter()
router.register(r'freestylers', FreestylerViewSet)
router.register(r'competitions', CompetitionViewSet)
router.register(r'seasons', SeasonViewSet)
router.register(r'matchdays', MatchdayViewSet)
router.register(r'battles', BattleViewSet)
router.register(r'standings', StandingViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('trigger-sync/', trigger_scraper, name='trigger-sync'), # <-- La URL secreta
]