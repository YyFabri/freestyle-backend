from django.core.management.base import BaseCommand
from core.models import Freestyler, Matchday, Battle, TournamentBracket
from scraper_core import FreestyleStatsScraper

class Command(BaseCommand):
    help = 'Sincroniza torneos de eliminación (Brackets)'

    def add_arguments(self, parser):
        parser.add_argument('matchday_id', type=int)

    def handle(self, *args, **options):
        scraper = FreestyleStatsScraper()
        # Buscamos la jornada por ID
        try:
            m = Matchday.objects.get(id=options['matchday_id'])
        except Matchday.DoesNotExist:
            self.stdout.write(self.style.ERROR('No existe esa jornada.'))
            return
        
        self.stdout.write(f"Extrayendo brackets para {m.name}...")
        # Asegurate de que esta URL sea la correcta para el torneo
        data = scraper.get_bracket_data(f"https://freestylestats.com/competition/torneo-ejemplo/brackets")
        
        for item in data:
            # Primero: aseguramos que los MCs existan en la base de datos
            mc1, _ = Freestyler.objects.get_or_create(name=item['mc_1'])
            mc2, _ = Freestyler.objects.get_or_create(name=item['mc_2'])
            
            # Segundo: Creamos la batalla vinculada a la jornada
            battle, _ = Battle.objects.get_or_create(
                matchday=m,
                mc_1=mc1,
                mc_2=mc2,
                defaults={'status': 'scheduled'}
            )
            
            # Tercero: Vinculamos al modelo de árbol
            TournamentBracket.objects.update_or_create(
                battle=battle,
                defaults={'stage': item['stage'], 'order': item['order'], 'matchday': m}
            )
            
        self.stdout.write(self.style.SUCCESS('Brackets sincronizados correctamente.'))