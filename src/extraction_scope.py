import calendar

from datetime import timedelta


def determinar_scope_incremental(last_completed_boundary, current_day):
    next_start_date = last_completed_boundary + timedelta(days=1)
    cutoff = current_day - timedelta(days=1)

    if next_start_date > cutoff:
        return next_start_date, cutoff, None

    candidate_boundary = cutoff
    return next_start_date, cutoff, candidate_boundary


def generar_intervalos_mensuales(fecha_inicio, fecha_fin):
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