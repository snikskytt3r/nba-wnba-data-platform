from datetime import datetime, timezone
import os
import requests

from time import sleep
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv

from raw_storage import persist_raw_games


load_dotenv()


class Balldontlie():

    def __init__(self):
        self.url_balldontlie = 'https://api.balldontlie.io/v1/games'
        self.api_key_balldontlie = os.getenv("API_KEY_BALLDONTLIE")
        self.headers = {"Authorization": self.api_key_balldontlie}

    def get_games_balldontlie(self, cursor_value, start_date, end_date):
        query_params = {"cursor": cursor_value, "per_page": 100, "start_date": start_date, "end_date": end_date}
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

    def extract_games_balldontlie(self, intervalo, season, root_dir, max_retries):
        cursor_value = None
        page_count = 1
        total_registros = 0
        retry_counts = 0
        pages_completed = 0
        games_collected = 0

        inicio_consulta = intervalo[0].strftime("%Y-%m-%d")
        fin_consulta = intervalo[1].strftime("%Y-%m-%d")

        print(f"Fecha de inicio de consulta: {inicio_consulta}.")
        print(f"Fecha fin de consulta: {fin_consulta}.")

        while True:
            print("Información de Ejecución")
            print(f"Valor del cursor a usar para la request: {cursor_value}")
            print(f"Número de la página que se usará para los registros: {page_count}")
            print(f"Número de resgistros antes de la ejecución: {total_registros}")
            print(f"Número de retries que se han ejecutado {retry_counts}")

            try:
                games_balldontlie, response_metadata = self.get_games_balldontlie(cursor_value=cursor_value, start_date=inicio_consulta, end_date=fin_consulta)
            except requests.RequestException as error:
                print(f"Error durante la request: {error}")
                return False, pages_completed, games_collected

            status_code_response = response_metadata['http_status']
            ratelimit_remaining_header = response_metadata['ratelimit_remaining']

            print(f"HTTP status: {status_code_response}")

            if status_code_response == 200:
                retry_counts = 0

                data_games = games_balldontlie['data']
                registros_extraidos = len(data_games)
                print("Cantidad de juegos detectados:", registros_extraidos)

                raw_persisted = persist_raw_games(
                    source_response=games_balldontlie,
                    endpoint=self.url_balldontlie,
                    root_dir=root_dir,
                    season=season,
                    start_date=inicio_consulta,
                    end_date=fin_consulta,
                    page_count=page_count,
                    http_status_code=status_code_response
                )

                if not raw_persisted:
                    return False, pages_completed, games_collected

                total_registros += registros_extraidos
                pages_completed += 1
                games_collected += registros_extraidos

                meta_data = games_balldontlie.get('meta', {})
                cursor_value = meta_data.get('next_cursor')

                if not cursor_value:
                    print(f"Extracción completada. No hay más páginas. \nTotal de páginas extraídas: {page_count}.\nTotal de registros extraídos: {total_registros}")
                    return True, pages_completed, games_collected

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
                    return False, pages_completed, games_collected

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
                return False, pages_completed, games_collected