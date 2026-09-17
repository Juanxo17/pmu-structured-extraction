"""Frontera con el proveedor del LLM usado para la inferencia.

Separa el servicio de la libreria concreta (Groq): el resto del paquete
depende solo de ProveedorLLM, lo que permite probar con dobles sin red.
"""

import logging
import os
import random
import time
from typing import Protocol

from groq import APIStatusError, Groq

_LOGGER = logging.getLogger(__name__)


class ProveedorLLM(Protocol):
    """Contrato de un proveedor capaz de completar conversaciones."""

    def completar(self, sistema: str, usuario: str) -> str:
        """Devuelve la respuesta cruda del modelo para un turno.

        Args:
            sistema: Instrucciones de sistema que enmarcan la tarea.
            usuario: Contenido del mensaje del usuario.

        Returns:
            Texto crudo con la respuesta del modelo.

        """
        ...


class ProveedorGroq:
    """Proveedor del LLM a traves de la API de Groq.

    Reintenta las llamadas que fallan por limitacion de cuota (HTTP 429) o
    por errores transitorios del servidor (5xx), con retroceso exponencial,
    jitter aleatorio y respeto de la cabecera Retry-After del proveedor.

    Attributes:
        modelo: Identificador del modelo servido por Groq.
        temperatura: Control de aleatoriedad de la generacion.
        intentos: Numero maximo de llamadas por turno.
        espera_base: Segundos base del retroceso exponencial.
        jitter_max: Amplitud maxima del jitter agregado a la espera.

    """

    def __init__(
        self,
        api_key: str | None = None,
        modelo: str | None = None,
        temperatura: float = 0.0,
        intentos: int | None = None,
        espera_base: float | None = None,
        jitter_max: float | None = None,
    ) -> None:
        """Configura el acceso a la API de Groq.

        Args:
            api_key: Clave de la API de Groq. Por defecto, la variable de
                entorno GROQ_API_KEY.
            modelo: Modelo a usar. Por defecto, la variable de entorno
                INFERENCE_MODELO o openai/gpt-oss-20b.
            temperatura: Temperatura de muestreo, entre 0 y 1.
            intentos: Numero maximo de llamadas por turno. Por defecto, la
                variable de entorno INFERENCE_INTENTOS_LLM o 3.
            espera_base: Segundos base del retroceso exponencial. Por
                defecto, la variable de entorno INFERENCE_ESPERA_BASE o 1.0.
            jitter_max: Amplitud maxima del jitter agregado a la espera. Por
                defecto, la variable de entorno INFERENCE_JITTER_MAX o 0.5.

        Raises:
            ValueError: Si no hay clave de API configurada.

        """
        clave = api_key or os.environ.get("GROQ_API_KEY")
        if not clave:
            raise ValueError("GROQ_API_KEY no esta configurada")
        self._api_key = clave
        self._modelo = modelo or os.environ.get("INFERENCE_MODELO", "openai/gpt-oss-20b")
        self.temperatura = temperatura
        self.intentos = (
            intentos if intentos is not None else int(os.environ.get("INFERENCE_INTENTOS_LLM", "3"))
        )
        self.espera_base = (
            espera_base
            if espera_base is not None
            else float(os.environ.get("INFERENCE_ESPERA_BASE", "1.0"))
        )
        self.jitter_max = (
            jitter_max
            if jitter_max is not None
            else float(os.environ.get("INFERENCE_JITTER_MAX", "0.5"))
        )
        self._cliente = Groq(api_key=clave)

    def completar(self, sistema: str, usuario: str) -> str:
        """Devuelve la respuesta cruda del modelo para un turno.

        Si la llamada falla por cuota (429) o por error transitorio (5xx),
        espera segun la cabecera Retry-After o, en su ausencia, con retroceso
        exponencial mas jitter, y reintenta hasta agotar los intentos.

        Args:
            sistema: Instrucciones de sistema que enmarcan la tarea.
            usuario: Contenido del mensaje del usuario.

        Returns:
            Texto crudo con la respuesta del modelo.

        Raises:
            APIStatusError: Si se agotan los intentos o el error no admite
                reintento.

        """
        for intento in range(self.intentos):
            try:
                respuesta = self._cliente.chat.completions.create(
                    model=self._modelo,
                    messages=[
                        {"role": "system", "content": sistema},
                        {"role": "user", "content": usuario},
                    ],
                    temperature=self.temperatura,
                )
            except APIStatusError as error:
                if not self._admite_reintento(error) or intento == self.intentos - 1:
                    _LOGGER.error(
                        "Llamada al LLM fallida tras %s intento(s) con HTTP %s",
                        intento + 1,
                        error.status_code,
                    )
                    raise
                espera = self._calcular_espera(error, intento)
                _LOGGER.warning(
                    "Llamada al LLM fallida con HTTP %s; reintento %s de %s en %.2fs",
                    error.status_code,
                    intento + 1,
                    self.intentos,
                    espera,
                )
                time.sleep(espera)
                continue
            _LOGGER.info(
                "Llamada al LLM exitosa en el intento %s de %s",
                intento + 1,
                self.intentos,
            )
            return respuesta.choices[0].message.content or ""
        raise RuntimeError("Bucle de reintentos sin salida")  # noqa: TRY300

    def _admite_reintento(self, error: APIStatusError) -> bool:
        """Indica si un error de la API admite reintento.

        Args:
            error: Error de estado HTTP devuelto por la API.

        Returns:
            True si es 429 (cuota) o un codigo de error de servidor 5xx.

        """
        return error.status_code == 429 or error.status_code >= 500

    def _calcular_espera(self, error: APIStatusError, intento: int) -> float:
        """Calcula los segundos a esperar antes del siguiente intento.

        Usa la cabecera Retry-After del error si esta presente; de lo
        contrario, retroceso exponencial (espera_base * 2 ** intento) mas un
        jitter aleatorio entre 0 y jitter_max.

        Args:
            error: Error de estado HTTP que disparo el reintento.
            intento: Numero del reintento actual, comenzando en 0.

        Returns:
            Segundos a esperar antes del siguiente intento.

        """
        cabeceras = getattr(error.response, "headers", None)
        retry_after = getattr(cabeceras, "get", lambda _: None)("retry-after")
        if retry_after is not None:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self.espera_base * (2**intento) + random.uniform(0.0, self.jitter_max)
