"""Pruebas del orquestador del pipeline de dos etapas.

Las llamadas HTTP a Inference/Geo/CRUD se simulan reemplazando (monkeypatch)
las funciones internas que las realizan, no con un servidor real -- esos
tres servicios todavia no existen. Cada reemplazo respeta exactamente la
forma de respuesta que define docs/CONTRATOS_SISTEMA.md.
"""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from process import orquestador
from process.orquestador import (
    MOTIVO_DUPLICADO,
    MOTIVO_FALLO_VALIDACION_EXTRACCION,
    MOTIVO_NO_ACCIONABLE,
    _anonimizar_autor,
    _buscar_posible_duplicado,
    _dentro_de_la_ventana,
    _misma_ubicacion,
    procesar_mensaje,
)


def _ejecutar(coroutine):
    """Corre una corrutina en un test sincrono (sin pytest-asyncio)."""
    return asyncio.run(coroutine)


class TestAnonimizarAutor:
    """Pruebas de la pseudonimizacion del autor."""

    def test_mismo_autor_produce_siempre_el_mismo_pseudonimo(self) -> None:
        """Un mismo autor_id_telegram siempre da el mismo resultado."""
        # Arrange / Act
        primero = _anonimizar_autor("user_55210")
        segundo = _anonimizar_autor("user_55210")

        # Assert
        assert primero == segundo

    def test_autores_distintos_producen_pseudonimos_distintos(self) -> None:
        """Dos autores distintos no colisionan en el mismo pseudonimo."""
        # Arrange / Act
        pseudonimo_a = _anonimizar_autor("user_55210")
        pseudonimo_b = _anonimizar_autor("user_99999")

        # Assert
        assert pseudonimo_a != pseudonimo_b

    def test_pseudonimo_no_revela_el_id_original(self) -> None:
        """El pseudonimo no contiene el ID original como subcadena."""
        # Arrange / Act
        pseudonimo = _anonimizar_autor("user_55210")

        # Assert
        assert "55210" not in pseudonimo


class TestProcesarMensaje:
    """Pruebas del pipeline completo, con Inference/Geo/CRUD simulados."""

    def test_mensaje_no_accionable_se_descarta_pero_se_persiste(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si la compuerta dice que no es accionable, se descarta sin llamar a extraccion,

        pero el reporte se persiste igual (naturaleza/ubicacion en None) -- el
        filtro por accionable lo aplica el frontend, no Process.
        """
        llamadas_a_crud: list[dict] = []

        # Arrange
        async def _compuerta_no_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": False,
                "temporalidad": "referencia_noticia",
                "intencion": "solicita_informacion",
            }

        async def _extraccion_no_deberia_llamarse(cliente, texto):  # noqa: ARG001
            raise AssertionError("no deberia llamarse a extraccion si no es accionable")

        async def _crud_persiste(cliente, reporte):  # noqa: ARG001
            llamadas_a_crud.append(reporte)
            return {**reporte, "id": "rep_1", "creado_en": "2026-09-15T10:00:00"}

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_no_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_no_deberia_llamarse)
        monkeypatch.setattr(orquestador, "_persistir_reporte", _crud_persiste)

        # Act
        resultado = _ejecutar(
            procesar_mensaje(
                mensaje_id="msg_1",
                texto_crudo="Escribime al 3101234567, soy Maria Jose",
                fuente="telegram",
                id_externo="msg_1",
                autor_id_telegram="user_1",
            )
        )

        # Assert
        assert resultado["estado"] == "descartado"
        assert resultado["motivo"] == MOTIVO_NO_ACCIONABLE
        assert resultado["reporte"]["id"] == "rep_1"
        assert len(llamadas_a_crud) == 1
        assert llamadas_a_crud[0]["naturaleza"] is None
        assert llamadas_a_crud[0]["ubicacion"] is None

    def test_fallo_de_validacion_en_extraccion_se_descarta_pero_se_persiste(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si Inference agota sus reintentos (422), se descarta con motivo distinto,

        pero tambien se persiste igual que el caso no accionable.
        """
        llamadas_a_crud: list[dict] = []

        # Arrange
        async def _compuerta_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": True,
                "temporalidad": "ocurriendo_ahora",
                "intencion": "solicita_ayuda",
            }

        async def _extraccion_falla_validacion(cliente, texto):  # noqa: ARG001
            return None

        async def _crud_persiste(cliente, reporte):  # noqa: ARG001
            llamadas_a_crud.append(reporte)
            return {**reporte, "id": "rep_2", "creado_en": "2026-09-15T10:00:00"}

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_falla_validacion)
        monkeypatch.setattr(orquestador, "_persistir_reporte", _crud_persiste)

        # Act
        resultado = _ejecutar(
            procesar_mensaje(
                mensaje_id="msg_2",
                texto_crudo="Hay algo raro pasando por aca",
                fuente="telegram",
                id_externo="msg_2",
                autor_id_telegram="user_2",
            )
        )

        # Assert
        assert resultado["estado"] == "descartado"
        assert resultado["motivo"] == MOTIVO_FALLO_VALIDACION_EXTRACCION
        assert resultado["reporte"]["id"] == "rep_2"
        assert len(llamadas_a_crud) == 1
        assert llamadas_a_crud[0]["naturaleza"] is None
        assert llamadas_a_crud[0]["ubicacion"] is None

    def test_mensaje_accionable_se_estructura_y_persiste(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Camino feliz: compuerta accionable -> extraccion -> geo -> persistencia."""
        llamadas_a_crud: list[dict] = []

        # Arrange
        async def _compuerta_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": True,
                "temporalidad": "ocurriendo_ahora",
                "intencion": "solicita_ayuda",
            }

        async def _extraccion_con_ubicacion(cliente, texto):  # noqa: ARG001
            return {
                "naturaleza": {
                    "tipo_evento": "incendio",
                    "servicio_de_respuesta": ["bomberos"],
                },
                "ubicacion": {
                    "ubicacion_texto_literal": "barrio Siloe",
                    "punto_referencia": "cerca al puente",
                },
            }

        async def _geo_resuelve(cliente, ubicacion_texto_literal, punto_referencia):  # noqa: ARG001
            return {
                "barrio": "Siloe",
                "comuna": "20",
                "nivel_granularidad": "barrio",
            }

        async def _crud_persiste(cliente, reporte):  # noqa: ARG001
            llamadas_a_crud.append(reporte)
            return {**reporte, "id": "rep_123", "creado_en": "2026-09-15T10:00:00"}

        async def _sin_duplicado(cliente, tipo_evento, comuna, barrio):  # noqa: ARG001
            return False

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_con_ubicacion)
        monkeypatch.setattr(orquestador, "_llamar_geo", _geo_resuelve)
        monkeypatch.setattr(orquestador, "_persistir_reporte", _crud_persiste)
        monkeypatch.setattr(orquestador, "_buscar_posible_duplicado", _sin_duplicado)

        # Act
        resultado = _ejecutar(
            procesar_mensaje(
                mensaje_id="msg_3",
                texto_crudo="Habla Andrés, hay un incendio en Siloe cerca al puente",
                fuente="telegram",
                id_externo="msg_3",
                autor_id_telegram="user_55210",
            )
        )

        # Assert
        assert resultado["estado"] == "estructurado"
        assert "motivo" not in resultado
        assert resultado["reporte"]["id"] == "rep_123"
        reporte_enviado_a_crud = llamadas_a_crud[0]
        assert "Andrés" not in reporte_enviado_a_crud["mensaje_anonimizado"]
        assert reporte_enviado_a_crud["ubicacion"]["barrio"] == "Siloe"
        assert reporte_enviado_a_crud["ubicacion"]["ubicacion_texto_literal"] == "barrio Siloe"
        assert reporte_enviado_a_crud["autor_anonimizado_id"] == _anonimizar_autor("user_55210")
        assert reporte_enviado_a_crud["estado_revision"] == "pendiente"

    def test_mensaje_accionable_con_posible_duplicado_se_persiste_igual(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si se detecta un posible duplicado, el reporte se persiste igual y se marca."""
        llamadas_a_crud: list[dict] = []

        # Arrange
        async def _compuerta_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": True,
                "temporalidad": "ocurriendo_ahora",
                "intencion": "solicita_ayuda",
            }

        async def _extraccion_con_ubicacion(cliente, texto):  # noqa: ARG001
            return {
                "naturaleza": {
                    "tipo_evento": "incendio",
                    "servicio_de_respuesta": ["bomberos"],
                },
                "ubicacion": {
                    "ubicacion_texto_literal": "barrio Siloe",
                    "punto_referencia": None,
                },
            }

        async def _geo_resuelve(cliente, ubicacion_texto_literal, punto_referencia):  # noqa: ARG001
            return {
                "barrio": "Siloe",
                "comuna": "20",
                "nivel_granularidad": "barrio",
            }

        async def _crud_persiste(cliente, reporte):  # noqa: ARG001
            llamadas_a_crud.append(reporte)
            return {**reporte, "id": "rep_456", "creado_en": "2026-09-15T10:05:00"}

        async def _con_duplicado(cliente, tipo_evento, comuna, barrio):  # noqa: ARG001
            return True

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_con_ubicacion)
        monkeypatch.setattr(orquestador, "_llamar_geo", _geo_resuelve)
        monkeypatch.setattr(orquestador, "_persistir_reporte", _crud_persiste)
        monkeypatch.setattr(orquestador, "_buscar_posible_duplicado", _con_duplicado)

        # Act
        resultado = _ejecutar(
            procesar_mensaje(
                mensaje_id="msg_4",
                texto_crudo="Otra persona reportando el mismo incendio en Siloe",
                fuente="telegram",
                id_externo="msg_4",
                autor_id_telegram="user_99999",
            )
        )

        # Assert: se marca como posible duplicado PERO se persiste igual que cualquier otro
        assert resultado == {
            "estado": "estructurado",
            "reporte": llamadas_a_crud[0] | {"id": "rep_456", "creado_en": "2026-09-15T10:05:00"},
            "motivo": MOTIVO_DUPLICADO,
        }
        assert len(llamadas_a_crud) == 1


class TestMismaUbicacion:
    """Pruebas de _misma_ubicacion (comparacion de barrio con respaldo a comuna)."""

    def test_mismo_barrio_es_la_misma_ubicacion(self) -> None:
        """Si ambos reportes tienen barrio y coincide, es la misma ubicacion."""
        # Arrange
        candidato = {"barrio": "Siloe"}

        # Act / Assert
        assert _misma_ubicacion("Siloe", candidato) is True

    def test_barrio_distinto_no_es_la_misma_ubicacion(self) -> None:
        """Si ambos reportes tienen barrio pero es distinto, no coinciden."""
        # Arrange
        candidato = {"barrio": "San Antonio"}

        # Act / Assert
        assert _misma_ubicacion("Siloe", candidato) is False

    def test_usa_comuna_como_respaldo_si_al_nuevo_le_falta_barrio(self) -> None:
        """Si el reporte nuevo no tiene barrio resuelto, se confia en la comuna ya filtrada."""
        # Arrange
        candidato = {"barrio": "Siloe"}

        # Act / Assert
        assert _misma_ubicacion(None, candidato) is True

    def test_usa_comuna_como_respaldo_si_al_candidato_le_falta_barrio(self) -> None:
        """Si el candidato no tiene barrio resuelto, se confia en la comuna ya filtrada."""
        # Arrange
        candidato = {"barrio": None}

        # Act / Assert
        assert _misma_ubicacion("Siloe", candidato) is True


class TestDentroDeLaVentana:
    """Pruebas de _dentro_de_la_ventana (ventana de 15 minutos por creado_en)."""

    def test_diez_minutos_de_diferencia_esta_dentro_de_la_ventana(self) -> None:
        """Una diferencia menor a 15 minutos cuenta como dentro de la ventana."""
        # Arrange
        ahora = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        creado_en_candidato = (ahora - timedelta(minutes=10)).isoformat()

        # Act / Assert
        assert _dentro_de_la_ventana(creado_en_candidato, ahora) is True

    def test_veinte_minutos_de_diferencia_esta_fuera_de_la_ventana(self) -> None:
        """Una diferencia mayor a 15 minutos ya no cuenta como posible duplicado."""
        # Arrange
        ahora = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        creado_en_candidato = (ahora - timedelta(minutes=20)).isoformat()

        # Act / Assert
        assert _dentro_de_la_ventana(creado_en_candidato, ahora) is False

    def test_marca_de_tiempo_sin_huso_se_asume_utc(self) -> None:
        """Un creado_en sin informacion de huso horario se interpreta como UTC."""
        # Arrange
        ahora = datetime(2026, 9, 17, 10, 0, 0, tzinfo=timezone.utc)
        creado_en_candidato = "2026-09-17T09:55:00"  # 5 minutos antes, sin tzinfo

        # Act / Assert
        assert _dentro_de_la_ventana(creado_en_candidato, ahora) is True


class TestBuscarPosibleDuplicado:
    """Pruebas de _buscar_posible_duplicado (consulta a CRUD + criterios combinados)."""

    def test_sin_comuna_resuelta_no_busca_duplicado(self) -> None:
        """Si Geo no resolvio ni siquiera la comuna, no hay nada confiable con que comparar."""

        # Arrange
        class _ClienteFalso:
            async def get(self, url: str, params: dict) -> None:  # noqa: ARG002
                raise AssertionError("no deberia consultar a CRUD sin comuna resuelta")

        # Act
        resultado = _ejecutar(_buscar_posible_duplicado(_ClienteFalso(), "incendio", None, None))

        # Assert
        assert resultado is False

    def test_encuentra_duplicado_por_barrio_igual_y_tiempo_cercano(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Mismo tipo_evento, mismo barrio, creado_en reciente -> posible duplicado."""

        # Arrange
        class _RespuestaFalsa:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                ahora_iso = datetime.now(timezone.utc).isoformat()
                return {
                    "total": 1,
                    "pagina": 1,
                    "tamano_pagina": 20,
                    "resultados": [
                        {"barrio": "Siloe", "creado_en": ahora_iso},
                    ],
                }

        class _ClienteFalso:
            def __init__(self) -> None:
                self.peticiones: list[tuple[str, dict]] = []

            async def get(self, url: str, params: dict) -> _RespuestaFalsa:
                self.peticiones.append((url, params))
                return _RespuestaFalsa()

        cliente = _ClienteFalso()

        # Act
        resultado = _ejecutar(_buscar_posible_duplicado(cliente, "incendio", "20", "Siloe"))

        # Assert
        assert resultado is True
        _url, parametros = cliente.peticiones[0]
        assert parametros == {"tipo_evento": "incendio", "comuna": "20"}

    def test_no_encuentra_duplicado_si_barrio_no_coincide(self) -> None:
        """Mismo tipo_evento y comuna, pero barrio distinto -> no es duplicado."""

        # Arrange
        class _RespuestaFalsa:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                ahora_iso = datetime.now(timezone.utc).isoformat()
                return {
                    "resultados": [
                        {"barrio": "San Antonio", "creado_en": ahora_iso},
                    ]
                }

        class _ClienteFalso:
            async def get(self, url: str, params: dict) -> _RespuestaFalsa:  # noqa: ARG002
                return _RespuestaFalsa()

        # Act
        resultado = _ejecutar(_buscar_posible_duplicado(_ClienteFalso(), "incendio", "20", "Siloe"))

        # Assert
        assert resultado is False

    def test_no_encuentra_duplicado_si_esta_fuera_de_la_ventana_de_tiempo(self) -> None:
        """Mismo tipo_evento, mismo barrio, pero creado_en hace mas de 15 minutos."""

        # Arrange
        class _RespuestaFalsa:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                hace_una_hora = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
                return {
                    "resultados": [
                        {"barrio": "Siloe", "creado_en": hace_una_hora},
                    ]
                }

        class _ClienteFalso:
            async def get(self, url: str, params: dict) -> _RespuestaFalsa:  # noqa: ARG002
                return _RespuestaFalsa()

        # Act
        resultado = _ejecutar(_buscar_posible_duplicado(_ClienteFalso(), "incendio", "20", "Siloe"))

        # Assert
        assert resultado is False

    def test_sin_candidatos_no_es_duplicado(self) -> None:
        """Si CRUD no devuelve ningun reporte con ese tipo_evento y comuna, no es duplicado."""

        # Arrange
        class _RespuestaFalsa:
            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return {"resultados": []}

        class _ClienteFalso:
            async def get(self, url: str, params: dict) -> _RespuestaFalsa:  # noqa: ARG002
                return _RespuestaFalsa()

        # Act
        resultado = _ejecutar(_buscar_posible_duplicado(_ClienteFalso(), "incendio", "20", "Siloe"))

        # Assert
        assert resultado is False
