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

        conteo_ids = Counter(game["game_id"] for game in games_data if game["game_id"] is not None)

        staging_data = []
        quarantine_data = []
        incidencias_dq = []

        for game in games_data:
            errores = []
            game_id = game["game_id"]

            if game_id is None or type(game_id) is not int or not -(2**63) <= game_id < 2**63:
                errores.append(("DQ-02", "game_id", "Identificador ausente o inválido"))
            elif conteo_ids[game_id] > 1:
                errores.append(("DQ-03", "game_id", "Identificador duplicado"))

            if game["home_team_id"] is not None and game["visitor_team_id"] is not None and game["home_team_id"] == game["visitor_team_id"]:
                errores.append(("DQ-05", "home_team_id, visitor_team_id", "Ambos equipos tienen el mismo identificador"))

            if game["game_date"] is None and game["game_datetime_utc"] is None:
                errores.append(("DQ-06", "game_date, game_datetime_utc", "Sin referencia temporal válida"))

            if errores:
                quarantine_data.append({**game, "dq_errors": [
                    {"rule_id": regla, "field": campo, "reason": motivo}
                    for regla, campo, motivo in errores
                ]})
                for regla, campo, motivo in errores:
                    incidencias_dq.append({
                        "raw_file_path": game["raw_file_path"],
                        "raw_record_index": game["raw_record_index"],
                        "game_id": game_id,
                        "rule_id": regla,
                        "field": campo,
                        "reason": motivo
                    })
            else:
                staging_data.append(game)

        advertencias_dq = []
        registros_advertidos = 0

        estados_validos = ("scheduled", "in_progress", "final", "postponed", "canceled", "delayed", "suspended", "abandoned", "unknown")

        for game in staging_data:
            advertencias = []

            if game["game_status_state"] == "final":
                for campo in ("home_team_score", "visitor_team_score"):
                    valor = game[campo]
                    if type(valor) is not int or valor < 0:
                        advertencias.append(("DQ-01", campo, "Marcador final ausente, inválido o negativo"))

            for campo in ("home_team_id", "visitor_team_id"):
                if game[campo] is None:
                    advertencias.append(("DQ-04", campo, "Identificador de equipo ausente o inválido"))

            if game["game_status_state"] == "final" and game["score_breakdown_matches_total"] is not True:
                periodo = game["game_period"]

                if type(periodo) is int and 4 <= periodo <= 7:
                    periodos = ("q1_score", "q2_score", "q3_score", "q4_score", "ot1_score", "ot2_score", "ot3_score")[:periodo]

                    for equipo in ("home_team", "visitor_team"):
                        marcador = game[f"{equipo}_score"]
                        parciales = [game[f"{equipo}_{parcial}"] for parcial in periodos]

                        if type(marcador) is int and all(type(valor) is int for valor in parciales):
                            if marcador != sum(parciales):
                                advertencias.append(("DQ-07", equipo, "El marcador no coincide con la suma de periodos"))
                        else:
                            advertencias.append(("DQ-07", equipo, "Información insuficiente para verificar marcadores"))
                else:
                    advertencias.append(("DQ-07", "game_period", "Periodo inválido o insuficiente para verificar marcadores"))

            if game["game_status_state"] not in estados_validos:
                advertencias.append(("DQ-08", "game_status_state", "Estado ausente o no reconocido"))
            elif game["game_status_state"] == "unknown":
                advertencias.append(("DQ-08", "game_status_state", "Estado indeterminado"))

            if (game["game_date"] is None) != (game["game_datetime_utc"] is None):
                advertencias.append(("DQ-06", "game_date, game_datetime_utc", "Solo una referencia temporal válida"))

            if advertencias:
                registros_advertidos += 1

            for regla, campo, motivo in advertencias:
                advertencias_dq.append({
                    "raw_file_path": game["raw_file_path"],
                    "raw_record_index": game["raw_record_index"],
                    "game_id": game["game_id"],
                    "rule_id": regla,
                    "field": campo,
                    "reason": motivo
                })

    print(f"Leído con correctamente: {ruta_json.name}")

reporte_dq = {
    "raw_records": total_games,
    "staging_records": len(staging_data),
    "quarantine_records": len(quarantine_data),
    "reconciled": total_games == len(staging_data) + len(quarantine_data),
    "records_with_warnings": registros_advertidos,
    "critical_by_rule": dict(Counter(error["rule_id"] for error in incidencias_dq)),
    "warnings_by_rule": dict(Counter(error["rule_id"] for error in advertencias_dq)),
    "critical_incidents": incidencias_dq,
    "warning_incidents": advertencias_dq
}

if not reporte_dq["reconciled"]:
    raise ValueError("Error de reconciliación: RAW != STAGING + QUARANTINE")

directorio_salida = directorio_src.parent / "data" / "processed" / "nba" / "games"
directorio_salida.mkdir(parents=True, exist_ok=True)

for nombre, registros_salida in (("staging", staging_data), ("quarantine", quarantine_data)):
    registros_json = [
        {campo: valor.isoformat() if isinstance(valor, (date, datetime)) else valor for campo, valor in registro.items()}
        for registro in registros_salida
    ]

    with open(directorio_salida / f"{nombre}.json", "w", encoding="utf-8") as archivo:
        json.dump(registros_json, archivo, ensure_ascii=False, indent=2, allow_nan=False)

with open(directorio_salida / "dq_report.json", "w", encoding="utf-8") as archivo:
    json.dump(reporte_dq, archivo, ensure_ascii=False, indent=2, allow_nan=False)

print(f"Archivos generados en: {directorio_salida}")