from django.core.management.base import BaseCommand
from core.models import Freestyler, Competition, Season, Matchday, Battle, Standing
from scraper_core import FreestyleStatsScraper

class Command(BaseCommand):
    help = 'Sincroniza el calendario, posiciones y batallas, incluyendo detalles y videos'

    def handle(self, *args, **kwargs):
        scraper = FreestyleStatsScraper()
        
        # 1. Sincronizar Calendario
        self.stdout.write("Sincronizando calendario y logos...")
        eventos = scraper.get_calendario()
        for evento in eventos:
            comp, created = Competition.objects.get_or_create(name=evento.get('tournament_name', 'N/A'))
            
            if evento.get('competition_logo') and not comp.logo_url:
                comp.logo_url = evento['competition_logo']
                comp.save()

            season, _ = Season.objects.get_or_create(competition=comp, name=evento.get('season', 'N/A'))
            
            Matchday.objects.update_or_create(
                event_id=evento['event_id'],
                defaults={
                    'season': season,
                    'name': evento['matchday_name'],
                    'start_datetime_utc': evento['start_datetime_utc'],
                    'city': evento['city'],
                    'country': evento['country']
                }
            )

        # 2. Sincronizar Posiciones
        self.stdout.write("Sincronizando posiciones y avatares/banderas...")
        tabla = scraper.get_tabla_posiciones("https://freestylestats.com/competition/fms-chile/2025-2026/standings")
        for pos in tabla:
            mc, _ = Freestyler.objects.get_or_create(name=pos['mc_name'])
            
            actualizado = False
            if pos.get('mc_avatar') and mc.profile_picture_url != pos['mc_avatar']:
                mc.profile_picture_url = pos['mc_avatar']
                actualizado = True
            if pos.get('mc_country') and mc.nationality != pos['mc_country']:
                mc.nationality = pos['mc_country']
                actualizado = True
            if actualizado:
                mc.save()

            season = Season.objects.latest('id')
            Standing.objects.update_or_create(
                season=season, freestyler=mc,
                defaults={
                    'position': pos['position'], 'pts': pos['pts'], 'ptb': pos['ptb'],
                    'battles_played': pos['battles_played'], 'wins': pos['wins'],
                    'wins_replica': pos['wins_replica'], 'losses': pos['losses'],
                    'losses_replica': pos['losses_replica'], 'mvp': pos['mvp']
                }
            )

        # 3. Sincronizar Batallas
        self.stdout.write("Sincronizando batallas y detalles (videos/réplicas)...")
        for m in Matchday.objects.all():
            url = f"https://freestylestats.com/competition/{m.season.competition.name.lower().replace(' ', '-')}/{m.season.name.replace(' ', '-').lower()}/{m.name.lower().replace(' ', '-')}"
            batallas = scraper.get_fixture_jornada(url)
            
            for b in batallas:
                mc1, _ = Freestyler.objects.get_or_create(name=b['mc_1'])
                mc2, _ = Freestyler.objects.get_or_create(name=b['mc_2'])
                
                if b.get('mc_1_avatar') and not mc1.profile_picture_url:
                    mc1.profile_picture_url = b['mc_1_avatar']
                    mc1.save()
                if b.get('mc_2_avatar') and not mc2.profile_picture_url:
                    mc2.profile_picture_url = b['mc_2_avatar']
                    mc2.save()

                # Extraemos los detalles entrando a la URL de la batalla
                detalles = scraper.get_battle_details(b['battle_url'])

                Battle.objects.update_or_create(
                    matchday=m, mc_1=mc1, mc_2=mc2,
                    defaults={
                        'status': b['status'], 
                        'score_1': b['score_1'], 
                        'score_2': b['score_2'],
                        'has_replica': detalles['has_replica'],
                        'video_url': detalles['video_url']
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Sincronización total finalizada. Ya sos FotMob.'))