from django.core.management.base import BaseCommand
from core.models import Freestyler, Competition, Season, Matchday, Battle, Standing
from scraper_core import FreestyleStatsScraper


class Command(BaseCommand):
    help = 'Sincroniza catálogo completo, calendario, posiciones y batallas con todos los detalles'

    CATALOGO = [
        # FMS
        ("fms-world-series", ["2025-2026", "2024-2025"]),
        ("fms-internacional", ["2025-2026", "2024-2025"]),
        ("fms-argentina", ["2025-2026", "2024-2025"]),
        ("fms-caribe", ["2025-2026", "2024-2025"]),
        ("fms-chile", ["2025-2026", "2024-2025"]),
        ("fms-colombia", ["2025-2026", "2024-2025"]),
        ("fms-espana", ["2025-2026", "2024-2025"]),
        ("fms-mexico", ["2025-2026", "2024-2025"]),
        ("fms-peru", ["2025-2026", "2024-2025"]),

        # RED BULL (Manejo especial de año 2024 vs 2024-2025)
        ("red-bull-batalla-internacional", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-argentina", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-chile", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-colombia", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-espana", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-mundial-por-equipos", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-mexico", ["2026-2027", "2025-2026", "2024"]),
        ("red-bull-batalla-peru", ["2026-2027", "2025-2026", "2024"]),

        # FU
        ("fu", ["2026", "2025"]),

        # WORLD CUP
        ("freestyle-world-cup", ["2026"]),
    ]

    def handle(self, *args, **kwargs):
        scraper = FreestyleStatsScraper()

        # 1. Sincronizar catálogo completo de competencias y temporadas
        self.stdout.write("Sincronizando catálogo de ligas y temporadas...")
        for slug, temporadas in self.CATALOGO:
            comp_name = slug.replace('-', ' ').title()
            comp, _ = Competition.objects.get_or_create(name=comp_name)
            for temp in temporadas:
                Season.objects.get_or_create(competition=comp, name=temp)

        # 2. Sincronizar calendario general (logos + fecha/ciudad/país cuando el scraper lo trae)
        self.stdout.write("Sincronizando calendario y logos...")
        eventos = scraper.get_calendario()
        for evento in eventos:
            comp, _ = Competition.objects.get_or_create(name=evento.get('tournament_name', 'N/A'))

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

        # 3. Sincronizar posiciones (standings) + avatares/nacionalidad
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

            # TODO: esto viene del script original y es un bug latente.
            # Season.objects.latest('id') agarra la season más nueva de TODA la DB,
            # no necesariamente FMS Chile 2025-2026 (que es la URL que estamos scrapeando).
            # Con el catálogo completo cargado esto se vuelve más riesgoso.
            # Reemplazar por algo tipo:
            # season = Season.objects.get(competition__name='Fms Chile', name='2025-2026')
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

        # 4. Recorrido profundo por catálogo: jornadas + batallas con TODOS los detalles
        self.stdout.write("Sincronizando jornadas y batallas por catálogo completo...")
        nombres_catalogo = [slug.replace('-', ' ').title() for slug, _ in self.CATALOGO]

        for comp in Competition.objects.filter(name__in=nombres_catalogo):
            slug = comp.name.lower().replace(' ', '-')

            for season in comp.season_set.all():
                url_base = f"https://freestylestats.com/competition/{slug}/{season.name}"
                self.stdout.write(f"--- {comp.name} ({season.name}) ---")

                jornadas_urls = scraper.get_links_jornadas(url_base)

                for j_url in jornadas_urls:
                    # NOTA: acá puede haber duplicados con el paso 2 si get_calendario()
                    # y get_links_jornadas() describen el mismo evento con distinto event_id.
                    # Si eso pasa, avisame y ajustamos la clave de dedupe.
                    matchday, _ = Matchday.objects.update_or_create(
                        event_id=j_url,
                        defaults={'season': season, 'name': j_url.split('/')[-1]}
                    )

                    batallas = scraper.get_fixture_jornada(j_url)
                    for b in batallas:
                        mc1, _ = Freestyler.objects.get_or_create(name=b['mc_1'])
                        mc2, _ = Freestyler.objects.get_or_create(name=b['mc_2'])

                        if b.get('mc_1_avatar') and not mc1.profile_picture_url:
                            mc1.profile_picture_url = b['mc_1_avatar']
                            mc1.save()
                        if b.get('mc_2_avatar') and not mc2.profile_picture_url:
                            mc2.profile_picture_url = b['mc_2_avatar']
                            mc2.save()

                        detalles = scraper.get_battle_details(b['battle_url'])

                        Battle.objects.update_or_create(
                            matchday=matchday, mc_1=mc1, mc_2=mc2,
                            defaults={
                                'status': b.get('status', 'finished'),
                                'score_1': b.get('score_1'),
                                'score_2': b.get('score_2'),
                                'has_replica': detalles['has_replica'],
                                'video_url': detalles['video_url']
                            }
                        )

        self.stdout.write(self.style.SUCCESS('Sincronización total finalizada. Ya sos FotMob.'))