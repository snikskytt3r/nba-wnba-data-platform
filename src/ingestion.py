from datetime import date, datetime, timezone, timedelta
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
        inicio = fecha_inicio
        fin = fecha_fin

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
    max_retries = 5
    season = '2025'

    units_completed = 0
    total_pages_completed = 0
    total_games_collected = 0

    ## Backfill
    inicio_temporada = '2025-10-21'
    fin_temporada = '2026-06-13'
    last_completed_boundary = date(2026, 6, 13)

    ## Incremental state
    root_dir = Path(__file__).resolve().parent.parent
    state_dir = root_dir/"state"
    state_file = state_dir/"nba_incremental_state.json"
    state_temp_file = state_dir/"nba_incremental_state.tmp"

    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                incremental_state = json.load(f)

            last_completed_boundary = date.fromisoformat(incremental_state["last_completed_boundary"])
            print("Persisted state encontrado.")
            print("Last completed boundary:", last_completed_boundary)

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f"Error al leer el persisted state: {error}")
            print(f"Revisar manualmente el archivo: {state_file}")
            return
    else:
        print("No existe persisted state.")
        print("Se utilizará el bootstrap boundary:", last_completed_boundary)
    
    confirmed_boundary_before_execution = last_completed_boundary
    next_start_date = last_completed_boundary + timedelta(days=1)
    current_day = datetime.today().date()
    cutoff = current_day - timedelta(days=1)
    
    if next_start_date > cutoff:
        print("No hay ejecuciones pendientes")
        print("No se realizará ninguna modificación al persisted state.")
        print("\nResumen de ejecución")
        print("Confirmed boundary before execution:", confirmed_boundary_before_execution)
        print("Candidate boundary: None")
        print("Units expected: 0")
        print("Units completed: 0")
        print("Pages completed: 0")
        print("Games collected: 0")
        print("Window status: NO-OP")
        print("Boundary after execution:", last_completed_boundary)
        return

    start_date = next_start_date
    end_date = cutoff
    candidate_boundary = end_date
    window_success = True

    intervalos = client_balldontlie.generar_intervalos_mensuales(fecha_inicio=start_date, fecha_fin=end_date)
    units_expected = len(intervalos)

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

            print("Información de Ejecución")
            print(f"Valor del cursor a usar para la request: {cursor_value}")
            print(f"Número de la página que se usará para los registros: {page_count}")
            print(f"Número de resgistros antes de la ejecución: {total_registros}")
            print(f"Número de retries que se han ejecutado {retry_counts}")

            requested_cursor = cursor_value

            try:
                games_balldontlie, response_metadata = client_balldontlie.get_games_balldontlie(cursor_value=cursor_value, start_date=inicio_consulta, end_date=fin_consulta)
            except requests.RequestException as error:
                print(f"Error durante la request: {error}")
                window_success = False
                break

            status_code_response = response_metadata['http_status']
            ratelimit_remaining_header = response_metadata['ratelimit_remaining']

            print(f"HTTP status: {status_code_response}")

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

                output_dir = root_dir/"data"/"raw"/"balldontlie"/"nba"/"games"
                output_dir.mkdir(parents=True, exist_ok=True)

                file_name = f"games_{season}_{inicio_consulta}_{fin_consulta}_page_{page_count}.json"
                file_path = output_dir / file_name

                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(raw_document, f, ensure_ascii=False, indent=4)
                except (OSError, TypeError, ValueError) as error:
                    print(f"Error al persistir el RAW: {error}")
                    window_success = False
                    break

                print(f"\n Archivo guardado exitosamente en: {file_path}")
                total_registros += registros_extraidos
                total_pages_completed += 1
                total_games_collected += registros_extraidos

                meta_data = games_balldontlie.get('meta', {})
                cursor_value = meta_data.get('next_cursor')

                if not cursor_value:
                    units_completed += 1
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
                    window_success = False
                    break

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
                window_success = False
                break

        if not window_success:
            break

    if window_success:
        incremental_state = {"last_completed_boundary": candidate_boundary.isoformat()}

        try:
            state_dir.mkdir(parents=True, exist_ok=True)

            with open(state_temp_file, "w", encoding="utf-8") as f:
                json.dump(incremental_state, f, ensure_ascii=False, indent=4)

            state_temp_file.replace(state_file)

        except (OSError, TypeError, ValueError) as error:
            print(f"Error al persistir el incremental state: {error}")
            print("Confirmed boundary before execution:", last_completed_boundary)
            print("Candidate boundary procesado exitosamente:", candidate_boundary)
            print("El persisted state no fue actualizado. Se requiere verificación manual.")

        else:
            last_completed_boundary = candidate_boundary
            print("Incremental state actualizado exitosamente.")
            print("New confirmed boundary:", last_completed_boundary)

    print("\nResumen de ejecución")
    print("Confirmed boundary before execution:", confirmed_boundary_before_execution)
    print("Candidate boundary:", candidate_boundary)
    print("Units expected:", units_expected)
    print("Units completed:", units_completed)
    print("Pages completed:", total_pages_completed)
    print("Games collected:", total_games_collected)
    print("Window status:", "SUCCESS" if window_success else "FAILED")
    print("Boundary after execution:", last_completed_boundary)

if __name__ == "__main__":
    main()