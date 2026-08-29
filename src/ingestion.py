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


    def get_games_balldontlie(self):

        response = requests.get(url=self.url_balldontlie, headers=self.headers)
        print("Request Status code:", response.status_code)
        response_content = response.json()
        return response_content


def main():

    client_balldontlie = Balldontlie()
    games_balldontlie = client_balldontlie.get_games_balldontlie()

    data_games = games_balldontlie['data']
    meta_games = games_balldontlie['meta']

    print("Cantidad de juegos detectados:", len(data_games))

    utc_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    root_dir = Path(__file__).resolve().parent.parent
    output_dir = root_dir/"data"/"raw"/"balldontlie"/"nba"/"games"

    output_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"games_{utc_timestamp}.json"
    file_path = output_dir / file_name

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(games_balldontlie, f, ensure_ascii=False, indent=4)

    print(f"\n Archivo guardado exitosamente en: {file_path}")


if __name__ == "__main__":
    main()