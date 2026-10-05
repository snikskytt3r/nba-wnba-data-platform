from datetime import date, datetime

from pathlib import Path

from balldontlie import Balldontlie
from extraction_scope import determinar_scope_incremental, generar_intervalos_mensuales
from state_storage import load_incremental_state, persist_incremental_state


def main():
    client_balldontlie = Balldontlie()

    max_retries = 5
    season = '2025'
    bootstrap_boundary = date(2026, 6, 13)

    units_completed = 0
    total_pages_completed = 0
    total_games_collected = 0

    root_dir = Path(__file__).resolve().parent.parent
    state_dir = root_dir/"state"
    state_file = state_dir/"nba_incremental_state.json"
    state_temp_file = state_dir/"nba_incremental_state.tmp"

    last_completed_boundary = load_incremental_state(state_file=state_file, bootstrap_boundary=bootstrap_boundary)

    if last_completed_boundary is None:
        return

    confirmed_boundary_before_execution = last_completed_boundary
    current_day = datetime.today().date()

    next_start_date, cutoff, candidate_boundary = determinar_scope_incremental(
        last_completed_boundary=last_completed_boundary,
        current_day=current_day
    )

    if candidate_boundary is None:
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
    window_success = True

    intervalos = generar_intervalos_mensuales(fecha_inicio=start_date, fecha_fin=end_date)
    units_expected = len(intervalos)

    for intervalo in intervalos:
        unit_success, pages_completed, games_collected = client_balldontlie.extract_games_balldontlie(
            intervalo=intervalo,
            season=season,
            root_dir=root_dir,
            max_retries=max_retries
        )

        total_pages_completed += pages_completed
        total_games_collected += games_collected

        if unit_success:
            units_completed += 1
        else:
            window_success = False
            break

    if window_success:
        state_persisted = persist_incremental_state(
            state_file=state_file,
            state_temp_file=state_temp_file,
            candidate_boundary=candidate_boundary
        )

        if not state_persisted:
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
    print("Next start date:", next_start_date)
    print("Cutoff:", cutoff)


if __name__ == "__main__":
    main()