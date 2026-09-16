"""Pruebas del servicio de inferencia con un proveedor falso."""

import pytest

from inference.servicio import ServicioInferencia
from inference.validador import RechazoSalida
from sirena_schema.schema import Compuerta, Ubicacion


class ProveedorFalso:
    """Proveedor que devuelve respuestas preprogramadas sin red.

    Attributes:
        respuestas: Cola de respuestas crudas del "LLM".
        llamadas: Registro de los pares (sistema, usuario) enviados.

    """

    def __init__(self, *respuestas: str) -> None:
        """Guarda las respuestas que devolvera y prepara el registro.

        Args:
            respuestas: Salidas crudas que se devolveran de a una.

        """
        self._respuestas = list(respuestas)
        self.llamadas: list[tuple[str, str]] = []

    def completar(self, sistema: str, usuario: str) -> str:
        """Devuelve la siguiente respuesta programada.

        Args:
            sistema: Instrucciones de sistema (se registran).
            usuario: Mensaje de usuario (se registran).

        Returns:
            Ultima respuesta programada o la siguiente de la cola.

        """
        self.llamadas.append((sistema, usuario))
        if len(self._respuestas) > 1:
            return self._respuestas.pop(0)
        return self._respuestas[0]


COMPUERTA_OK = (
    '{"es_reporte_accionable": true, "temporalidad": "ocurriendo_ahora", '
    '"intencion": "solicita_ayuda"}'
)
COMPUERTA_MALA = '{"es_reporte_accionable": "si"}'
EXTRACCION_OK = (
    '{"naturaleza": {"tipo_evento": "sismo", "servicio_de_respuesta": ["A"]}, '
    '"ubicacion": {"ubicacion_texto_literal": "Calle 5", "barrio": "Centro", '
    '"comuna": "3", "punto_referencia": null, "nivel_granularidad": "exacta", '
    '"lat": null, "lon": null}}'
)


class TestClasificar:
    """Pruebas de ServicioInferencia.clasificar."""

    def test_retorna_compuerta_valida(self) -> None:
        """Devuelve la Compuerta cuando la salida ya es conforme."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_OK)
        servicio = ServicioInferencia(proveedor)

        # Act
        resultado = servicio.clasificar("hay un incendio")

        # Assert
        assert isinstance(resultado, Compuerta)
        assert resultado.es_reporte_accionable is True

    def test_reintenta_hasta_conformar(self) -> None:
        """Usa la retroalimentacion cuando la primera salida es invalida."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_MALA, COMPUERTA_OK)
        servicio = ServicioInferencia(proveedor)

        # Act
        resultado = servicio.clasificar("hay un incendio")

        # Assert
        assert resultado.es_reporte_accionable is True
        assert len(proveedor.llamadas) == 2
        assert "rechazada por el validador" in proveedor.llamadas[1][1]

    def test_agota_intentos_y_lanza_rechazo(self) -> None:
        """Lanza RechazoSalida cuando ninguna salida conforma."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_MALA)
        servicio = ServicioInferencia(proveedor, intentos_maximos=3)

        # Act / Assert
        with pytest.raises(RechazoSalida):
            servicio.clasificar("hay un incendio")


class TestExtraer:
    """Pruebas de ServicioInferencia.extraer."""

    def test_retorna_naturaleza_y_ubicacion(self) -> None:
        """Devuelve Naturaleza y Ubicacion cuando la salida es conforme."""
        # Arrange
        proveedor = ProveedorFalso(EXTRACCION_OK)
        servicio = ServicioInferencia(proveedor)

        # Act
        naturaleza, ubicacion = servicio.extraer("tiembla en cali")

        # Assert
        assert naturaleza.tipo_evento == "sismo"
        assert isinstance(ubicacion, Ubicacion)

    def test_agota_intentos_y_lanza_rechazo(self) -> None:
        """Lanza RechazoSalida cuando ninguna salida conforma."""
        # Arrange
        proveedor = ProveedorFalso(COMPUERTA_MALA)
        servicio = ServicioInferencia(proveedor, intentos_maximos=3)

        # Act / Assert
        with pytest.raises(RechazoSalida):
            servicio.extraer("tiembla en cali")