import pytest
import calendar
from datetime import date
from src.extraction_scope import determinar_scope_incremental, generar_intervalos_mensuales


@pytest.mark.parametrize("last_completed_boundary, current_day, esperado", [
    (date(2026, 11, 21), date(2026, 11, 26), (date(2026, 11, 22), date(2026, 11, 25), date(2026, 11, 25))),
    (date(2026, 11, 24), date(2026, 11, 26), (date(2026, 11, 25), date(2026, 11, 25), date(2026, 11, 25))),
    (date(2026, 11, 25), date(2026, 11, 26), (date(2026, 11, 26), date(2026, 11, 25), None)),
    (date(2026, 11, 30), date(2026, 12, 2), (date(2026, 12, 1), date(2026, 12, 1), date(2026, 12, 1))),
    (date(2026, 12, 31), date(2027, 1, 2), (date(2027, 1, 1), date(2027, 1, 1), date(2027, 1, 1)))
], ids=["normal", "single_day", "no_op", "month_change", "year_change"])
def test_scope_incremental(last_completed_boundary, current_day, esperado):
    resultado = determinar_scope_incremental(last_completed_boundary, current_day)
    assert resultado == esperado

@pytest.mark.parametrize("fecha_inicio, fecha_fin, esperado", [
    (date(2026, 11, 5), date(2026, 11, 20), [[date(2026, 11, 5), date(2026, 11, 20)]]),
    (date(2026, 10, 21), date(2026, 12, 15), [[date(2026, 10, 21), date(2026, 10, 31)], [date(2026, 11, 1), date(2026, 11, 30)], [date(2026, 12, 1), date(2026, 12, 15)]]),
    (date(2026, 12, 20), date(2027, 1, 10), [[date(2026, 12, 20), date(2026, 12, 31)], [date(2027, 1, 1), date(2027, 1, 10)]]),
    (date(2024, 2, 25), date(2024, 3, 5), [[date(2024, 2, 25), date(2024, 2, 29)], [date(2024, 3, 1), date(2024, 3, 5)]]),
    (date(2026, 2, 25), date(2026, 3, 5), [[date(2026, 2, 25), date(2026, 2, 28)], [date(2026, 3, 1), date(2026, 3, 5)]]),
    (date(2026, 11, 26), date(2026, 11, 26), [[date(2026, 11, 26), date(2026, 11, 26)]]),
    (date(2026, 11, 26), date(2026, 11, 20), []),
], ids=["same_month", "multiple_months", "year_boundary_crossing", "leap_year_february", "non_leap_year_february", "single_day_range", "inverted_range"])
def test_intervalos_mensuales(fecha_inicio, fecha_fin, esperado):
    resultado = generar_intervalos_mensuales(fecha_inicio, fecha_fin)
    assert resultado == esperado