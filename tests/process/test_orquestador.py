"""Pruebas del orquestador del pipeline de dos etapas.

Las llamadas HTTP a Inference/Geo/CRUD se simulan reemplazando (monkeypatch)
las funciones internas que las realizan, no con un servidor real -- esos
tres servicios todavia no existen. Cada reemplazo respeta exactamente la
forma de respuesta que define docs/CONTRATOS_SISTEMA.md.
"""

import asyncio

import pytest

from process import orquestador
from process.orquestador import (
    MOTIVO_FALLO_VALIDACION_EXTRACCION,
    MOTIVO_NO_ACCIONABLE,
    _anonimizar_autor,
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

    def test_mensaje_no_accionable_se_descarta(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Si la compuerta dice que no es accionable, se descarta sin llamar a extraccion."""

        # Arrange
        async def _compuerta_no_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": False,
                "temporalidad": "referencia_noticia",
                "intencion": "solicita_informacion",
            }

        async def _extraccion_no_deberia_llamarse(cliente, texto):  # noqa: ARG001
            raise AssertionError("no deberia llamarse a extraccion si no es accionable")

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_no_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_no_deberia_llamarse)

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
        assert resultado == {"estado": "descartado", "motivo": MOTIVO_NO_ACCIONABLE}

    def test_fallo_de_validacion_en_extraccion_se_descarta(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Si Inference agota sus reintentos (422), se descarta con motivo distinto."""

        # Arrange
        async def _compuerta_accionable(cliente, texto):  # noqa: ARG001
            return {
                "es_reporte_accionable": True,
                "temporalidad": "ocurriendo_ahora",
                "intencion": "solicita_ayuda",
            }

        async def _extraccion_falla_validacion(cliente, texto):  # noqa: ARG001
            return None

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_falla_validacion)

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
        assert resultado == {
            "estado": "descartado",
            "motivo": MOTIVO_FALLO_VALIDACION_EXTRACCION,
        }

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

        monkeypatch.setattr(orquestador, "_llamar_compuerta", _compuerta_accionable)
        monkeypatch.setattr(orquestador, "_llamar_extraccion", _extraccion_con_ubicacion)
        monkeypatch.setattr(orquestador, "_llamar_geo", _geo_resuelve)
        monkeypatch.setattr(orquestador, "_persistir_reporte", _crud_persiste)

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
        assert resultado["reporte"]["id"] == "rep_123"
        reporte_enviado_a_crud = llamadas_a_crud[0]
        assert "Andrés" not in reporte_enviado_a_crud["mensaje_anonimizado"]
        assert reporte_enviado_a_crud["ubicacion"]["barrio"] == "Siloe"
        assert reporte_enviado_a_crud["ubicacion"]["ubicacion_texto_literal"] == "barrio Siloe"
        assert reporte_enviado_a_crud["autor_anonimizado_id"] == _anonimizar_autor("user_55210")
        assert reporte_enviado_a_crud["estado_revision"] == "pendiente"