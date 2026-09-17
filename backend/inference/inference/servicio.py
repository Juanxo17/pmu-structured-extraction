"""Orquestacion de las etapas de clasificacion y extraccion.

El servicio coordina el proveedor del LLM con los prompts y el validador:
aplica cada etapa devolviendo el modelo del esquema ya validado. Cuando el
LLM no genera una salida conforme, el servicio reintenta alimentando al
modelo con el detalle del rechazo para que corrija la respuesta.
"""

import logging
from typing import Protocol

from sirena_schema.schema import Compuerta, Naturaleza, Ubicacion

from inference.prompts import sistema_compuerta, sistema_extraccion
from inference.validador import RechazoSalida, validar_compuerta, validar_extraccion

_LOGGER = logging.getLogger(__name__)


class _Proveedor(Protocol):
    """Contrato minimo del proveedor del LLM usado por el servicio."""

    def completar(self, sistema: str, usuario: str) -> str:
        """Devuelve la respuesta cruda del modelo para un turno.

        Args:
            sistema: Instrucciones de sistema que enmarcan la tarea.
            usuario: Contenido del mensaje del usuario.

        Returns:
            Texto crudo con la respuesta del modelo.

        """
        ...


class ServicioInferencia:
    """Aplica las etapas de inferencia usando un proveedor del LLM.

    Attributes:
        proveedor: Proveedor del LLM que completa las conversaciones.
        intentos_maximos: Numero de intentos permitidos por etapa.

    """

    def __init__(self, proveedor: _Proveedor, intentos_maximos: int = 3) -> None:
        """Configura el proveedor y el limite de intentos.

        Args:
            proveedor: Proveedor del LLM que completa las conversaciones.
            intentos_maximos: Cuantas veces se intenta cada etapa antes de
                rechazar la salida.

        """
        self.proveedor = proveedor
        self.intentos_maximos = intentos_maximos

    def clasificar(self, texto: str) -> Compuerta:
        """Aplica la etapa de compuerta sobre un texto de reporte.

        Args:
            texto: Texto crudo del mensaje ciudadano.

        Returns:
            Compuerta validada con la clasificacion del reporte.

        Raises:
            RechazoSalida: Si ninguna salida del proveedor conforma al
                esquema tras los intentos permitidos.

        """
        retroalimentacion: str | None = None
        for intento in range(self.intentos_maximos):
            usuario = self._armar_usuario(texto, retroalimentacion)
            salida = self.proveedor.completar(sistema_compuerta(), usuario)
            try:
                return validar_compuerta(salida)
            except RechazoSalida as error:
                _LOGGER.warning(
                    "Salida de compuerta rechazada (intento %s de %s): %s",
                    intento + 1,
                    self.intentos_maximos,
                    error.detalle,
                )
                retroalimentacion = error.detalle
        _LOGGER.error(
            "Compuerta descartada tras %s intentos: %s",
            self.intentos_maximos,
            retroalimentacion,
        )
        raise RechazoSalida(
            f"La salida de compuerta no conforma al esquema tras {self.intentos_maximos} intentos"
        )

    def extraer(self, texto: str) -> tuple[Naturaleza, Ubicacion]:
        """Aplica la etapa de extraccion sobre un texto de reporte.

        Args:
            texto: Texto crudo del mensaje ciudadano.

        Returns:
            Tupla con la Naturaleza y la Ubicacion validadas.

        Raises:
            RechazoSalida: Si ninguna salida del proveedor conforma al
                esquema tras los intentos permitidos.

        """
        retroalimentacion: str | None = None
        for intento in range(self.intentos_maximos):
            usuario = self._armar_usuario(texto, retroalimentacion)
            salida = self.proveedor.completar(sistema_extraccion(), usuario)
            try:
                return validar_extraccion(salida)
            except RechazoSalida as error:
                _LOGGER.warning(
                    "Salida de extraccion rechazada (intento %s de %s): %s",
                    intento + 1,
                    self.intentos_maximos,
                    error.detalle,
                )
                retroalimentacion = error.detalle
        _LOGGER.error(
            "Extraccion descartada tras %s intentos: %s",
            self.intentos_maximos,
            retroalimentacion,
        )
        raise RechazoSalida(
            f"La salida de extraccion no conforma al esquema tras {self.intentos_maximos} intentos"
        )

    @staticmethod
    def _armar_usuario(texto: str, retroalimentacion: str | None) -> str:
        """Arma el mensaje del usuario, con retroalimentacion si existe.

        Args:
            texto: Texto crudo del mensaje ciudadano.
            retroalimentacion: Detalle del ultimo rechazo de validacion, o
                None si es el primer intento.

        Returns:
            Mensaje de usuario listo para enviar al proveedor.

        """
        if not retroalimentacion:
            return texto
        return (
            f"{texto}\n\nTu respuesta anterior fue rechazada por el validador. "
            f"Soluciona lo siguiente y responde SOLO con el JSON corregido "
            f"sin texto adicional:\n{retroalimentacion}"
        )
