import json

from datetime import date


def load_incremental_state(state_file, bootstrap_boundary):
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                incremental_state = json.load(f)

            last_completed_boundary = date.fromisoformat(incremental_state["last_completed_boundary"])
            print("Persisted state encontrado.")
            print("Last completed boundary:", last_completed_boundary)
            return last_completed_boundary

        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
            print(f"Error al leer el persisted state: {error}")
            print(f"Revisar manualmente el archivo: {state_file}")
            return None

    print("No existe persisted state.")
    print("Se utilizará el bootstrap boundary:", bootstrap_boundary)
    return bootstrap_boundary


def persist_incremental_state(state_file, state_temp_file, candidate_boundary):
    incremental_state = {"last_completed_boundary": candidate_boundary.isoformat()}

    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)

        with open(state_temp_file, "w", encoding="utf-8") as f:
            json.dump(incremental_state, f, ensure_ascii=False, indent=4)

        state_temp_file.replace(state_file)

    except (OSError, TypeError, ValueError) as error:
        print(f"Error al persistir el incremental state: {error}")
        return False

    return True