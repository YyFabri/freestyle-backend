from rest_framework import serializers
from .models import Freestyler, Competition, Season, Matchday, Battle, Standing, TournamentBracket

class FreestylerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Freestyler
        fields = '__all__'

class CompetitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competition
        fields = '__all__'

class SeasonSerializer(serializers.ModelSerializer):
    competition = CompetitionSerializer(read_only=True)
    
    class Meta:
        model = Season
        fields = '__all__'

class StandingSerializer(serializers.ModelSerializer):
    freestyler = FreestylerSerializer(read_only=True)
    
    class Meta:
        model = Standing
        fields = '__all__'

class BattleSerializer(serializers.ModelSerializer):
    mc_1 = FreestylerSerializer(read_only=True)
    mc_2 = FreestylerSerializer(read_only=True)
    winner = FreestylerSerializer(read_only=True)
    
    class Meta:
        model = Battle
        fields = '__all__'

class MatchdaySerializer(serializers.ModelSerializer):
    season = SeasonSerializer(read_only=True)
    # Traemos las batallas anidadas dentro de la jornada
    battles = BattleSerializer(many=True, read_only=True) 
    
    class Meta:
        model = Matchday
        fields = '__all__'