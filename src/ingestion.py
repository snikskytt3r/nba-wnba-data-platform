from datetime import datetime, timezone, timedelta
import calendar
import json
import os
from pathlib import Path
import requests
from time import sleep
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

load_dotenv()

class Balldontlie():

    def __init__(self):
        self.url_balldontlie = 'https://api.balldontlie.io/v1/games'
        self.api_key_balldontlie = os.getenv("API_KEY_BALLDONTLIE")
        self.headers = {"Authorization": self.api_key_balldontlie}


    def get_games_balldontlie(self, cursor_value, start_date, end_date):

        query_params = {"cursor": cursor_value, "per_page":  100, "start_date": start_date, "end_date": end_date}
        response = requests.get(url=self.url_balldontlie, headers=self.headers, params=query_params)

        http_status = response.status_code
        date_header = response.headers.get("Date")
        ratelimit_limit_header = response.headers.get("x-ratelimit-limit")
        ratelimit_remaining_header = response.headers.get("x-ratelimit-remaining")
        ratelimit_reset_header = response.headers.get("x-ratelimit-reset")
        retry_after_header = response.headers.get("retry-after")

        ratelimit_limit_header = int(ratelimit_limit_header) if ratelimit_limit_header is not None else None
        ratelimit_remaining_header = int(ratelimit_remaining_header) if ratelimit_remaining_header is not None else None
        ratelimit_reset_header = int(ratelimit_reset_header) if ratelimit_reset_header is not None else None
        retry_after_header = int(retry_after_header) if retry_after_header is not None else None

        response_metadata = {
            "http_status": http_status,
            "date": date_header,
            "ratelimit_limit": ratelimit_limit_header,
            "ratelimit_remaining": ratelimit_remaining_header,
            "ratelimit_reset": ratelimit_reset_header,
            "retry_after": retry_after_header
        }

        if http_status == 200:
            response_content = response.json()

        else:
            response_content = None
            response_metadata["response_text"] = response.text

        return response_content, response_metadata

    def generar_intervalos_mensuales(self, fecha_inicio, fecha_fin):
        inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()

        intervalos = []
        actual_inicio = inicio

        while actual_inicio <= fin:
            _, ultimo_dia = calendar.monthrange(actual_inicio.year, actual_inicio.month)

            actual_fin = actual_inicio.replace(day=ultimo_dia)

            if actual_fin > fin:
                actual_fin = fin

            intervalos.append([actual_inicio, actual_fin])

            actual_inicio = actual_fin + timedelta(days=1)

        return intervalos

def main():
    client_balldontlie = Balldontlie()

    ## Configuración - Scope Histórico
    inicio_temporada = '2025-10-21'
    fin_temporada = '2026-06-13'
    max_retries = 5

    intervalos = client_balldontlie.generar_intervalos_mensuales(fecha_inicio=inicio_temporada, fecha_fin=fin_temporada)

    for intervalo in intervalos:

        cursor_value = None
        page_count = 1
        total_registros = 0
        retry_counts = 0

        inicio_consulta = intervalo[0].strftime("%Y-%m-%d")
        fin_consulta = intervalo[1].strftime("%Y-%m-%d")
    
        print(f"Fecha de inicio de consulta: {inicio_consulta}.")
        print(f"Fecha fin de consulta: {fin_consulta}.")

        while True:

            requested_cursor = cursor_value

            games_balldontlie, response_metadata = client_balldontlie.get_games_balldontlie(cursor_value=cursor_value, start_date=inicio_consulta, end_date=fin_consulta)

            status_code_response = response_metadata['http_status']
            ratelimit_remaining_header = response_metadata['ratelimit_remaining']

            if status_code_response == 200:
                retry_counts = 0

                data_games = games_balldontlie['data']
                registros_extraidos = len(data_games)
                print("Cantidad de juegos detectados:", registros_extraidos )

                if data_games:
                    games_dates = [game['date'] for game in data_games if game.get('date')]
                    min_game_date = min(games_dates) if games_dates else None
                    max_game_date = max(games_dates) if games_dates else None

                else:
                    min_game_date = None
                    max_game_date = None

                extraction_datetime = datetime.now(timezone.utc)

                extracted_at_utc = extraction_datetime.isoformat()
                utc_timestamp = extraction_datetime.strftime("%Y%m%d_%H%M%S")

                ingestion_metadata = {
                    "source": "balldontlie",
                    "league": "nba",
                    "entity": "games", 
                    "endpoint": client_balldontlie.url_balldontlie,
                    "extracted_at_utc": extracted_at_utc,
                    "http_status_code": status_code_response,
                    "records_received": len(data_games),
                    "min_game_date": min_game_date,
                    "max_game_date": max_game_date
                }

                raw_document = {
                    "ingestion_metadata": ingestion_metadata,
                    "source_response": games_balldontlie
                }

                root_dir = Path(__file__).resolve().parent.parent
                output_dir = root_dir/"data"/"raw"/"balldontlie"/"nba"/"games"
                output_dir.mkdir(parents=True, exist_ok=True)

                file_name = f"games_{utc_timestamp}_page_{page_count}.json"
                file_path = output_dir / file_name

                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_document, f, ensure_ascii=False, indent=4)

                print(f"\n Archivo guardado exitosamente en: {file_path}")
                total_registros += registros_extraidos

                meta_data = games_balldontlie.get('meta', {})
                cursor_value = meta_data.get('next_cursor')

                if not cursor_value:
                    print(f"Extracción completada. No hay más páginas. \nTotal de páginas extraídas: {page_count}.\nTotal de registros extraídos: {total_registros}")
                    break

                page_count += 1

                if ratelimit_remaining_header == 0:
                    date_response = parsedate_to_datetime(response_metadata['date'])
                    ratelimit_reset = datetime.fromtimestamp(response_metadata['ratelimit_reset'], tz=timezone.utc)
                    time_to_wait = (ratelimit_reset - date_response).total_seconds()

                    if time_to_wait > 0:
                        print(f"Rate limit alcanzado. Esperando {time_to_wait} segundos.")
                        sleep(time_to_wait)

            elif status_code_response == 429:
                retry_after = response_metadata['retry_after']
                retry_counts += 1

                if retry_counts > max_retries:
                    print(f"Intento: {retry_counts} fallido. Se han agotado los intentos. Verificar qué está pasando.")
                    return

                if retry_after is None:
                    date_response = response_metadata['date']
                    ratelimit_reset = response_metadata['ratelimit_reset']

                    if date_response is not None and ratelimit_reset is not None:
                        date_response = parsedate_to_datetime(date_response)
                        ratelimit_reset = datetime.fromtimestamp(ratelimit_reset, tz=timezone.utc)
                        retry_after = (ratelimit_reset - date_response).total_seconds()
                        retry_after = retry_after if retry_after > 0 else 0
                        print(f"HTTP 429 sin Retry-After. Se utilizará x-ratelimit-reset como alternativa: {retry_after} segundos.")

                    else:
                        retry_after = 120
                        print("HTTP 429 sin Retry-After ni información suficiente de x-ratelimit-reset. Se utilizará una espera default de 120 segundos.")

                print(f"Intento: {retry_counts} fallido. Esperando {retry_after} segundos para volverlo a intentar.")
                sleep(retry_after)
                continue


            else:
                print(f"Error HTTP {status_code_response}: {response_metadata.get('response_text')}")
                return


if __name__ == "__main__":
    main()