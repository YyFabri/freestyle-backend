from django.db import models

class Freestyler(models.Model):
    name = models.CharField(max_length=100, unique=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    profile_picture_url = models.URLField(null=True, blank=True)

    def __str__(self):
        return self.name

class Competition(models.Model):
    name = models.CharField(max_length=100)
    logo_url = models.URLField(null=True, blank=True)
    
    def __str__(self):
        return self.name

class Season(models.Model):
    competition = models.ForeignKey(Competition, on_delete=models.CASCADE, related_name='seasons')
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return f"{self.competition.name} - {self.name}"

class Matchday(models.Model):
    event_id = models.CharField(max_length=255, unique=True)
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='matchdays')
    name = models.CharField(max_length=100)
    start_datetime_utc = models.DateTimeField(null=True, blank=True)
    country = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    youtube_video_id = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['start_datetime_utc']

    def __str__(self):
        return f"{self.season} - {self.name}"

class Battle(models.Model):
    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE, related_name='battles')
    mc_1 = models.ForeignKey(Freestyler, on_delete=models.CASCADE, related_name='battles_as_mc1')
    mc_2 = models.ForeignKey(Freestyler, on_delete=models.CASCADE, related_name='battles_as_mc2')
    score_1 = models.IntegerField(null=True, blank=True)
    score_2 = models.IntegerField(null=True, blank=True)
    winner = models.ForeignKey(Freestyler, on_delete=models.SET_NULL, null=True, blank=True, related_name='battles_won')
    is_exhibition = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[('scheduled', 'Programada'), ('finished', 'Finalizada')])    
    votes_mc_1 = models.IntegerField(null=True, blank=True)
    votes_mc_2 = models.IntegerField(null=True, blank=True)
    votes_replica = models.IntegerField(null=True, blank=True)
    has_replica = models.BooleanField(default=False)
    video_url = models.URLField(null=True, blank=True)
    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE, related_name='battles')
    has_replica = models.BooleanField(default=False)


class Standing(models.Model):
    season = models.ForeignKey(Season, on_delete=models.CASCADE, related_name='standings')
    freestyler = models.ForeignKey(Freestyler, on_delete=models.CASCADE)
    position = models.IntegerField()
    pts = models.IntegerField(default=0)
    ptb = models.FloatField(default=0.0)
    battles_played = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    wins_replica = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    losses_replica = models.IntegerField(default=0)
    mvp = models.IntegerField(default=0)

    class Meta:
        unique_together = ('season', 'freestyler')
        ordering = ['position']

class TournamentBracket(models.Model):
    matchday = models.ForeignKey(Matchday, on_delete=models.CASCADE, related_name='brackets')
    stage = models.CharField(max_length=50)
    battle = models.OneToOneField(Battle, on_delete=models.CASCADE)
    order = models.IntegerField()