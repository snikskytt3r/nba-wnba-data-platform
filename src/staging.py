import json
from pathlib import Path
from datetime import date, datetime, timezone
from collections import Counter

directorio_src = Path(__file__).parent

ruta_jsons = directorio_src.parent / "data" / "raw" / "balldontlie" / "nba" / "games"

games_data = []
total_games = 0

campos_enteros = (
    "game_id", "season", "game_period", "home_team_id", "visitor_team_id", "home_team_score", "visitor_team_score", "home_team_q1_score", 
    "home_team_q2_score", "home_team_q3_score", "home_team_q4_score", "visitor_team_q1_score", "visitor_team_q2_score", "visitor_team_q3_score", 
    "visitor_team_q4_score", "home_team_ot1_score", "home_team_ot2_score", "home_team_ot3_score", "visitor_team_ot1_score", "visitor_team_ot2_score", "visitor_team_ot3_score",
    "home_team_timeouts_remaining", "visitor_team_timeouts_remaining"
)

campos_booleanos = ("postseason", "postponed", "home_team_in_bonus", "visitor_team_in_bonus")

campos_strings = (
    "game_status", "game_status_state", "game_time_display", "nba_cup_stage",
    "home_team_conference", "home_team_division", "home_team_city", "home_team_name", "home_team_full_name", "home_team_abbreviation",
    "visitor_team_conference", "visitor_team_division", "visitor_team_city", "visitor_team_name", "visitor_team_full_name", "visitor_team_abbreviation"
)


for ruta_json in ruta_jsons.glob('*.json'):

    try:
        with open(ruta_json, 'r', encoding='utf-8') as archivo:
            datos = json.load(archivo)

    except (OSError, json.JSONDecodeError) as error:
        print(f"Error al leer el RAW {ruta_json.name}: {error}")
        raise

    if not isinstance(datos, dict) or not isinstance(datos.get("source_response"), dict) or not isinstance(datos["source_response"].get("data"), list):
        raise ValueError(f"Estructura RAW inválida en {ruta_json.name}.")

    registros = datos["source_response"]["data"]
    total_games += len(registros)

    metadata = datos.get("ingestion_metadata")
    if not isinstance(metadata, dict) or not isinstance(metadata.get("extracted_at_utc"), str) or not metadata["extracted_at_utc"].strip():
        raise ValueError(f"Metadata RAW inválida en {ruta_json.name}: extracted_at_utc ausente o vacío.")
    
    try:
        extracted_at_utc = datetime.fromisoformat(metadata["extracted_at_utc"].replace("Z", "+00:00"))
        if extracted_at_utc.utcoffset() is None:
            raise ValueError("Timestamp sin zona horaria")
        extracted_at_utc = extracted_at_utc.astimezone(timezone.utc)
    except ValueError as error:
        raise ValueError(f"Metadata RAW inválida en {ruta_json.name}: extracted_at_utc inválido ({error}).") from error

    
    for raw_record_index, game in enumerate(registros):
        if not isinstance(game, dict):
            raise ValueError(f"Registro RAW inválido en {ruta_json.name}, índice {raw_record_index}.")

        home_team = game.get("home_team")
        visitor_team = game.get("visitor_team")

        if not isinstance(home_team, dict):
            if home_team is not None:
                print(f"WARNING: home_team inválido en {ruta_json.name}, índice {raw_record_index}.")
            home_team = {}

        if not isinstance(visitor_team, dict):
            if visitor_team is not None:
                print(f"WARNING: visitor_team inválido en {ruta_json.name}, índice {raw_record_index}.")
            visitor_team = {}


        game_date = game.get("date")

        if game_date is not None:
            if isinstance(game_date, str):
                try:
                    game_date = date.fromisoformat(game_date)
                except ValueError:
                    print(f"WARNING: game_date inválida en {ruta_json.name}, índice {raw_record_index}: {game_date}")
                    game_date = None
            else:
                print(f"WARNING: game_date con tipo incompatible en {ruta_json.name}, índice {raw_record_index}: {game_date}")
                game_date = None


        game_datetime_utc = game.get("datetime")

        if game_datetime_utc is not None:
            if isinstance(game_datetime_utc, str):
                try:
                    game_datetime_utc = datetime.fromisoformat(game_datetime_utc.replace("Z", "+00:00"))
                    if game_datetime_utc.utcoffset() is None:
                        raise ValueError("Timestamp sin zona horaria")
                    game_datetime_utc = game_datetime_utc.astimezone(timezone.utc)
                except ValueError:
                    print(f"WARNING: game_datetime_utc inválido en {ruta_json.name}, índice {raw_record_index}.")
                    game_datetime_utc = None
            else:
                print(f"WARNING: game_datetime_utc con tipo incompatible en {ruta_json.name}, índice {raw_record_index}.")
                game_datetime_utc = None

        game_staging = {
            "game_id": game.get("id"),
            "game_date": game_date,
            "game_datetime_utc": game_datetime_utc,
            "season": game.get("season"),
            "game_status": game.get("status"),
            "game_status_state": game.get("status_state"),
            "game_period": game.get("period"),
            "game_time_display": game.get("time"),
            "postseason": game.get("postseason"),
            "postponed": game.get("postponed"),
            "nba_cup_stage": game.get("ist_stage"),
            "home_team_id": home_team.get("id"),
            "home_team_conference": home_team.get("conference"),
            "home_team_division": home_team.get("division"),
            "home_team_city": home_team.get("city"),
            "home_team_name": home_team.get("name"),
            "home_team_full_name": home_team.get("full_name"),
            "home_team_abbreviation": home_team.get("abbreviation"),
            "visitor_team_id": visitor_team.get("id"),
            "visitor_team_conference": visitor_team.get("conference"),
            "visitor_team_division": visitor_team.get("division"),
            "visitor_team_city": visitor_team.get("city"),
            "visitor_team_name": visitor_team.get("name"),
            "visitor_team_full_name": visitor_team.get("full_name"),
            "visitor_team_abbreviation": visitor_team.get("abbreviation"),
            "home_team_score": game.get("home_team_score"),
            "visitor_team_score": game.get("visitor_team_score"),
            "home_team_q1_score": game.get("home_q1"),
            "home_team_q2_score": game.get("home_q2"),
            "home_team_q3_score": game.get("home_q3"),
            "home_team_q4_score": game.get("home_q4"),
            "visitor_team_q1_score": game.get("visitor_q1"),
            "visitor_team_q2_score": game.get("visitor_q2"),
            "visitor_team_q3_score": game.get("visitor_q3"),
            "visitor_team_q4_score": game.get("visitor_q4"),
            "home_team_ot1_score": game.get("home_ot1"),
            "home_team_ot2_score": game.get("home_ot2"),
            "home_team_ot3_score": game.get("home_ot3"),
            "visitor_team_ot1_score": game.get("visitor_ot1"),
            "visitor_team_ot2_score": game.get("visitor_ot2"),
            "visitor_team_ot3_score": game.get("visitor_ot3"),
            "home_team_timeouts_remaining": game.get("home_timeouts_remaining"),
            "visitor_team_timeouts_remaining": game.get("visitor_timeouts_remaining"),
            "home_team_in_bonus": game.get("home_in_bonus"),
            "visitor_team_in_bonus": game.get("visitor_in_bonus"),
            "raw_file_path": ruta_json.relative_to(directorio_src.parent).as_posix(),
            "raw_record_index": raw_record_index,
            "raw_extracted_at_utc": extracted_at_utc
        }

        for campo in campos_enteros:
            valor = game_staging[campo]
            if valor is not None and (type(valor) is not int):
                print(f"TIPO INVÁLIDO: {campo} en {ruta_json.name}, índice {raw_record_index}: {valor!r}")
                game_staging[campo] = None

        for campo in campos_booleanos:
            valor = game_staging[campo]
            if valor is not None and type(valor) is not bool:
                print(f"TIPO INVÁLIDO: {campo} en {ruta_json.name}, índice {raw_record_index}: {valor!r}")
                game_staging[campo] = None

        for campo in campos_strings:
            valor = game_staging[campo]
            if valor is not None and type(valor) is not str:
                print(f"TIPO INVÁLIDO: {campo} en {ruta_json.name}, índice {raw_record_index}: {valor!r}")
                game_staging[campo] = None


        score_breakdown_matches_total = None
        periodo = game_staging["game_period"]

        if game_staging["game_status_state"] == "final" and type(periodo) is int and 4 <= periodo <= 7:
            periodos = ("q1_score", "q2_score", "q3_score", "q4_score", "ot1_score", "ot2_score", "ot3_score")[:periodo]
            comprobaciones = []

            for equipo in ("home_team", "visitor_team"):
                marcador = game_staging[f"{equipo}_score"]
                parciales = [game_staging[f"{equipo}_{parcial}"] for parcial in periodos]

                if type(marcador) is int and all(type(valor) is int for valor in parciales):
                    comprobaciones.append(marcador == sum(parciales))

            if False in comprobaciones:
                score_breakdown_matches_total = False
            elif len(comprobaciones) == 2:
                score_breakdown_matches_total = True

        game_staging["score_breakdown_matches_total"] = score_breakdown_matches_total
            
        games_data.append(game_staging)

    print(f"Leído con correctamente: {ruta_json.name}")

print("Partidos leídos:", total_games)
print("Extracted at UTC:", games_data[0]["raw_extracted_at_utc"])
print("Tipo:", type(games_data[0]["raw_extracted_at_utc"]))
print("Registros transformados:", len(games_data))
print("Columnas STAGING:", len(games_data[0]))
print("Consistencia de marcadores:", Counter(game["score_breakdown_matches_total"] for game in games_data))

print("Estados:", Counter(game["game_status_state"] for game in games_data))
print("Periodos:", Counter(game["game_period"] for game in games_data))

conteo_ids = Counter(game["game_id"] for game in games_data if game["game_id"] is not None)
duplicados = {game_id: cantidad for game_id, cantidad in conteo_ids.items() if cantidad > 1}

print("Game IDs únicos:", len(conteo_ids))
print("Game IDs repetidos:", len(duplicados))
print("Ejemplos de duplicados:", list(duplicados.items())[:5])