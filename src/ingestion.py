from datetime import datetime, timezone
import json
import os
from pathlib import Path
import requests
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
        print("Request Status code:", http_status)
        response_txt = response.text
        print(f"Aquí comienza el txt: {response_txt}. Y aquí termina")
        print(f"Aquí inicia el headers: {response.headers}. Y aquí termina")
        response_content = response.json()
        return response_content, http_status


def main():

    client_balldontlie = Balldontlie()
    cursor_value = None
    start_date = '2025-02-01'
    end_date = '2025-02-15'
    page_count = 1
    total_registros = 0

    while True:
        games_balldontlie, status_code_response = client_balldontlie.get_games_balldontlie(cursor_value=cursor_value, start_date=start_date, end_date=end_date)

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

        meta_data = games_balldontlie.get('meta', {})
        cursor_value = meta_data.get('next_cursor')

        total_registros += registros_extraidos

        if not cursor_value:
            print(f"Extracción completada. No hay más páginas. \nTotal de páginas extraídas: {page_count}.\nTotal de registros extraídos: {total_registros}")
            break

        page_count += 1


if __name__ == "__main__":
    main()