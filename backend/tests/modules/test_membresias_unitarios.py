from datetime import date

import pytest

from app.modules.membresias.service import _sumar_meses, calcular_proxima_renovacion

# Tests unitarios: sin base de datos ni HTTP real, llaman a las funciones
# directamente. Ver convencion documentada en test_accesos.py.
pytestmark = pytest.mark.unit


class TestSumarMeses:
    def test_caso_normal(self):
        assert _sumar_meses(date(2026, 3, 15), 1) == date(2026, 4, 15)

    def test_fin_de_mes_no_bisiesto(self):
        # 31 de enero + 1 mes: febrero no tiene dia 31, se ajusta al ultimo
        # dia valido del mes destino (28 en un anio no bisiesto).
        assert _sumar_meses(date(2025, 1, 31), 1) == date(2025, 2, 28)

    def test_fin_de_mes_bisiesto(self):
        # Mismo caso que arriba pero en un anio bisiesto: el ultimo dia
        # valido de febrero es el 29.
        assert _sumar_meses(date(2024, 1, 31), 1) == date(2024, 2, 29)

    def test_cruce_de_anio(self):
        assert _sumar_meses(date(2026, 12, 5), 1) == date(2027, 1, 5)


class TestCalcularProximaRenovacion:
    def test_mensual(self):
        assert calcular_proxima_renovacion(date(2026, 3, 15), "mensual") == date(
            2026, 4, 15
        )

    def test_trimestral(self):
        assert calcular_proxima_renovacion(date(2026, 3, 15), "trimestral") == date(
            2026, 6, 15
        )

    def test_anual(self):
        assert calcular_proxima_renovacion(date(2026, 3, 15), "anual") == date(
            2027, 3, 15
        )

    def test_fin_de_mes_bisiesto_via_calcular_proxima_renovacion(self):
        assert calcular_proxima_renovacion(date(2024, 1, 31), "mensual") == date(
            2024, 2, 29
        )

    def test_duracion_invalida_lanza_valueerror_con_mensaje_claro(self):
        # T16: antes lanzaba un KeyError sin controlar al buscar la clave
        # directamente en MESES_POR_DURACION; ahora se valida explicitamente
        # antes de acceder al diccionario.
        with pytest.raises(ValueError, match="Duración de membresía no válida: 'quincenal'"):
            calcular_proxima_renovacion(date(2026, 3, 15), "quincenal")
