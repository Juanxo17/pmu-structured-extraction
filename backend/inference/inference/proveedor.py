"""Frontera con el proveedor del LLM usado para la inferencia.

Separa el servicio de la libreria concreta (Groq): el resto del paquete
depende solo de ProveedorLLM, lo que permite probar con dobles sin red.
"""

import os
from typing import Protocol

from groq import Groq


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

    Attributes:
        modelo: Identificador del modelo servido por Groq.
        temperatura: Control de aleatoriedad de la generacion.

    """

    def __init__(
        self,
        api_key: str | None = None,
        modelo: str | None = None,
        temperatura: float = 0.0,
    ) -> None:
        """Configura el acceso a la API de Groq.

        Args:
            api_key: Clave de la API de Groq. Por defecto, la variable de
                entorno GROQ_API_KEY.
            modelo: Modelo a usar. Por defecto, la variable de entorno
                INFERENCE_MODELO o llama-3.1-8b-instant.
            temperatura: Temperatura de muestreo, entre 0 y 1.

        Raises:
            ValueError: Si no hay clave de API configurada.

        """
        clave = api_key or os.environ.get("GROQ_API_KEY")
        if not clave:
            raise ValueError("GROQ_API_KEY no esta configurada")
        self._api_key = clave
        self._modelo = modelo or os.environ.get(
            "INFERENCE_MODELO", "llama-3.1-8b-instant"
        )
        self.temperatura = temperatura
        self._cliente = Groq(api_key=clave)

    def completar(self, sistema: str, usuario: str) -> str:
        """Devuelve la respuesta cruda del modelo para un turno.

        Args:
            sistema: Instrucciones de sistema que enmarcan la tarea.
            usuario: Contenido del mensaje del usuario.

        Returns:
            Texto crudo con la respuesta del modelo.

        """
        respuesta = self._cliente.chat.completions.create(
            model=self._modelo,
            messages=[
                {"role": "system", "content": sistema},
                {"role": "user", "content": usuario},
            ],
            temperature=self.temperatura,
        )
        return respuesta.choices[0].message.content or ""