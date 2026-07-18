import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup

class FreestyleStatsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.session.headers.update(self.base_headers)
        self.base_url = "https://freestylestats.com"

    # ==========================================
    # MÉTODOS PRIVADOS (UTILIDADES INTERNAS)
    # ==========================================
    
    def _buscar_clave_recursiva(self, data, clave_objetivo):
        if isinstance(data, dict):
            if clave_objetivo in data:
                return data[clave_objetivo]
            for valor in data.values():
                resultado = self._buscar_clave_recursiva(valor, clave_objetivo)
                if resultado is not None:
                    return resultado
        elif isinstance(data, list):
            for item in data:
                resultado = self._buscar_clave_recursiva(item, clave_objetivo)
                if resultado is not None:
                    return resultado
        return None

    def _limpiar_texto(self, texto):
        return texto.strip() if texto else "N/A"

    def _formatear_url_imagen(self, src):
        if not src: 
            return None
        if src.startswith('/'):
            return f"{self.base_url}{src}"
        return src

    # ==========================================
    # MÉTODOS PÚBLICOS (API DEL SCRAPER)
    # ==========================================

    def get_calendario(self):
        headers = self.session.headers.copy()
        headers.update({"RSC": "1"})
        
        response = self.session.get(self.base_url, headers=headers)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"Error HTTP: {response.status_code}")
            return []

        matchdays_data = None
        for linea in response.text.splitlines():
            if '"matchdays"' in linea:
                try:
                    json_puro = linea.split(':', 1)[1]
                    datos_parseados = json.loads(json_puro)
                    matchdays_data = self._buscar_clave_recursiva(datos_parseados, "matchdays")
                    if matchdays_data:
                        break
                except json.JSONDecodeError:
                    continue

        eventos_estructurados = []
        if matchdays_data:
            for evento_crudo in matchdays_data:
                country_data = evento_crudo.get('country') or {}
                pais_lista = country_data.get('translations') or []
                pais = pais_lista[0].get('name') if pais_lista else None

                locacion = evento_crudo.get('location') or {}
                ciudad = locacion.get('name')

                season_data = evento_crudo.get('season') or {}
                competition_data = season_data.get('competition') or {}
                logo_data = competition_data.get('logo') or {}

                comp_logo = logo_data.get('url')
                tournament_name = competition_data.get('name', 'N/A')
                season_name = season_data.get('name', 'N/A')

                evento_limpio = {
                    "event_id": evento_crudo.get('id'),
                    "slug": evento_crudo.get('slug'),
                    "tournament_name": tournament_name,
                    "competition_logo": self._formatear_url_imagen(comp_logo),
                    "season": season_name,
                    "matchday_name": evento_crudo.get('name', 'N/A'),
                    "start_datetime_utc": evento_crudo.get('start_datetime'),
                    "country": pais,
                    "city": ciudad,
                    "status": "scheduled"
                }
                eventos_estructurados.append(evento_limpio)
                
        return eventos_estructurados

    def get_tabla_posiciones(self, url_tabla):
        response = self.session.get(url_tabla)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        tabla = soup.find('table')
        if not tabla:
            return []

        filas = tabla.find('tbody').find_all('tr')
        tabla_estructurada = []

        for fila in filas:
            columnas = fila.find_all('td')
            if len(columnas) >= 10:
                try:
                    mc_cell = columnas[1]
                    mc_name = self._limpiar_texto(mc_cell.text)
                    mc_avatar = None
                    mc_country = None
                    
                    for img in mc_cell.find_all('img'):
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        if 'flag' in src.lower() or src.endswith('.svg'):
                            mc_country = alt if alt else "N/A"
                        else:
                            mc_avatar = self._formatear_url_imagen(src)

                    mc_data = {
                        "position": int(self._limpiar_texto(columnas[0].text)),
                        "mc_name": mc_name,
                        "mc_avatar": mc_avatar,
                        "mc_country": mc_country,
                        "pts": int(self._limpiar_texto(columnas[2].text)),
                        "ptb": float(self._limpiar_texto(columnas[3].text).replace(',', '.')),
                        "battles_played": int(self._limpiar_texto(columnas[4].text)),
                        "wins": int(self._limpiar_texto(columnas[5].text)),
                        "wins_replica": int(self._limpiar_texto(columnas[6].text)),
                        "losses": int(self._limpiar_texto(columnas[7].text)),
                        "losses_replica": int(self._limpiar_texto(columnas[8].text)),
                        "mvp": int(self._limpiar_texto(columnas[9].text))
                    }
                    tabla_estructurada.append(mc_data)
                except ValueError:
                    continue
                    
        return tabla_estructurada

    def get_bracket_data(self, url_torneo):
        response = self.session.get(url_torneo)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        bracket_data = []
        fases = soup.find_all('div', class_='bracket-round') 
        
        for index, fase in enumerate(fases):
            stage_name = fase.find('h3').text.strip() if fase.find('h3') else f"Fase {index+1}"
            batallas = fase.find_all('div', class_='bracket-match')
            
            for order, b in enumerate(batallas):
                mcs = b.find_all('div', class_='mc-name')
                if len(mcs) >= 2:
                    bracket_data.append({
                        "stage": stage_name,
                        "order": order,
                        "mc_1": mcs[0].text.strip(),
                        "mc_2": mcs[1].text.strip(),
                        "battle_url": b.find('a')['href'] if b.find('a') else None
                    })
        return bracket_data

    def get_fixture_jornada(self, url_jornada):
        response = self.session.get(url_jornada)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        enlaces_batallas = soup.find_all('a', href=lambda href: href and href.startswith('/battle/'))
        batallas_estructuradas = []

        for enlace in enlaces_batallas:
            imagenes_mcs = enlace.find_all('img')
            if len(imagenes_mcs) != 2:
                continue

            try:
                img1 = imagenes_mcs[0]
                avatar_1 = self._formatear_url_imagen(img1.get('src'))
                container1 = img1.find_next_sibling('div', class_='relative')
                nombre1 = container1.find('div').text.strip()
                winner1 = 'underline' in container1.find('div').get('class', [])
                score_div1 = img1.find_previous_sibling('div', class_='font-mono')
                score1 = int(score_div1.text.strip()) if score_div1 and score_div1.text.strip().isdigit() else None

                img2 = imagenes_mcs[1]
                avatar_2 = self._formatear_url_imagen(img2.get('src'))
                container2 = img2.find_next_sibling('div', class_='relative')
                nombre2 = container2.find('div').text.strip()
                winner2 = 'underline' in container2.find('div').get('class', [])
                score_div2 = img2.find_previous_sibling('div', class_='font-mono')
                score2 = int(score_div2.text.strip()) if score_div2 and score_div2.text.strip().isdigit() else None

                ganador_nombre = None
                if winner1: ganador_nombre = nombre1
                elif winner2: ganador_nombre = nombre2

                batalla = {
                    "mc_1": nombre1,
                    "mc_1_avatar": avatar_1,
                    "mc_2": nombre2,
                    "mc_2_avatar": avatar_2,
                    "score_1": score1,
                    "score_2": score2,
                    "winner": ganador_nombre,
                    "is_exhibition": 'Exhibición' in enlace.text,
                    "status": "finished" if score1 is not None else "scheduled",
                    "battle_url": f"{self.base_url}{enlace['href']}"
                }
                batallas_estructuradas.append(batalla)
                
            except AttributeError:
                continue

        return batallas_estructuradas

    # === NUEVO MÉTODO ===
    def get_battle_details(self, battle_url):
        """
        Extrae los detalles específicos (Video y recuento de votos) entrando a la batalla.
        """
        response = self.session.get(battle_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        detalles = {
            "video_url": None,
            "votes_mc_1": None,
            "votes_mc_2": None,
            "votes_replica": None,
            "has_replica": False
        }
        
        # 1. Buscamos el video (iframe de YouTube)
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '')
            if 'youtube.com' in src or 'youtu.be' in src:
                detalles["video_url"] = src
                break

        # 2. Buscamos si hubo réplica en el HTML (usualmente mencionan "Réplica" en los resultados)
        text_content = soup.get_text().lower()
        if "réplica" in text_content or "replica" in text_content:
            detalles["has_replica"] = True

        # NOTA: El cálculo exacto de "3 a 2" depende de cómo esté estructurada la tabla de votos
        # en la página de la batalla. Por ahora inicializamos los campos y el scraper detecta la réplica.
        
        return detalles


# ==========================================
# TEST RÁPIDO PARA ASEGURAR QUE TODO ANDA
# ==========================================
if __name__ == "__main__":
    scraper = FreestyleStatsScraper()
    
    print("1. Probando Calendario...")
    calendario = scraper.get_calendario()
    print(f" -> Encontradas {len(calendario)} jornadas.")
    
    print("\n2. Probando Tabla de Posiciones...")
    tabla = scraper.get_tabla_posiciones("https://freestylestats.com/competition/fms-chile/2025-2026/standings")
    print(f" -> Extraídos {len(tabla)} MCs de la tabla.")
    
    print("\n3. Probando Fixture...")
    fixture = scraper.get_fixture_jornada("https://freestylestats.com/competition/fms-chile/2025-2026/jornada-5")
    print(f" -> Extraídas {len(fixture)} batallas.")