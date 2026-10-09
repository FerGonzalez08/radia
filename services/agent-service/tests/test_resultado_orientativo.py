from app.dominios.diagnostico.resultado_orientativo import (
    ClasificacionOrientativa,
    calcular_competencias_orientativas,
)


def test_clasifica_puntajes_altos_como_fortalezas() -> None:
    competencias = calcular_competencias_orientativas(
        {
            "TEC-001": 4,
            "TEC-002": 5,
            "TEC-003": 4,
            "ACT-001": 5,
            "ACT-002": 4,
            "ACT-003": 5,
        }
    )

    assert len(competencias) == 6
    assert all(
        competencia.clasificacion == ClasificacionOrientativa.FORTALEZA
        for competencia in competencias
    )


def test_clasifica_puntajes_hasta_tres_como_oportunidades() -> None:
    competencias = calcular_competencias_orientativas(
        {
            "TEC-001": 3,
            "TEC-002": 2,
            "TEC-003": 1,
            "ACT-001": 3,
            "ACT-002": 2,
            "ACT-003": 1,
        }
    )

    assert all(
        competencia.clasificacion == ClasificacionOrientativa.OPORTUNIDAD
        for competencia in competencias
    )
    assert competencias[0].recurso_simulado.startswith("Guía simulada")
