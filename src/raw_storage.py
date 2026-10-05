from datetime import datetime, timezone

import json


def persist_raw_games(source_response, endpoint, root_dir, season, start_date, end_date, page_count, http_status_code):
    data_games = source_response['data']

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
        "endpoint": endpoint,
        "extracted_at_utc": extracted_at_utc,
        "http_status_code": http_status_code,
        "records_received": len(data_games),
        "min_game_date": min_game_date,
        "max_game_date": max_game_date
    }

    raw_document = {
        "ingestion_metadata": ingestion_metadata,
        "source_response": source_response
    }

    output_dir = root_dir/"data"/"raw"/"balldontlie"/"nba"/"games"
    output_dir.mkdir(parents=True, exist_ok=True)

    file_name = f"games_{season}_{start_date}_{end_date}_page_{page_count}.json"
    file_path = output_dir / file_name

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_document, f, ensure_ascii=False, indent=4)
    except (OSError, TypeError, ValueError) as error:
        print(f"Error al persistir el RAW: {error}")
        return False

    print(f"\n Archivo guardado exitosamente en: {file_path}")
    return True