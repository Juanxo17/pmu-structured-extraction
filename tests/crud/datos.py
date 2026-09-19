from __future__ import annotations

from typing import Any


class ReportesFabrica:
    """Genera `ReporteEstructurado` con valores unicos para las pruebas.

    Cada llamada incrementa un contador interno para que el `id` sea
    unico entre tests y entre creaciones dentro del mismo test.
    """

    def __init__(self) -> None:
        """Inicializa el contador."""
        self._contador = 0

    def reporte(
        self,
        *,
        id_fijo: str | None = None,
        fecha_fija: str | None = None,
        tipo_evento: str = "sismo",
        servicios: list[str] | None = None,
        comuna: str | None = "1",
        barrio: str | None = "Bellavista",
        nivel_granularidad: str = "barrio",
        accionable: bool = True,
        temporalidad: str = "ocurriendo_ahora",
        intencion: str = "solicita_ayuda",
        estado_revision: str = "pendiente",
        lat: float | None = 3.45,
        lon: float | None = -76.55,
    ) -> dict[str, Any]:
        """Crea un dict con la forma completa de `ReporteEstructurado`.

        Args:
            id_fijo: `id` del reporte; si no se da, se genera `rpt-{n}`.
            fecha_fija: `creado_en` en ISO; si no se da, `2025-09-15T0{n}:00:00Z`.
            tipo_evento: Tipo de evento a incluir en `naturaleza`.
            servicios: Servicios de respuesta a incluir.
            comuna: Comuna de la ubicacion.
            barrio: Barrio de la ubicacion.
            nivel_granularidad: Nivel de granularidad.
            accionable: Si el reporte es accionable.
            temporalidad: Temporalidad de la compuerta.
            intencion: Intencion de la compuerta.
            estado_revision: Estado de revision.
            lat: Coordenada latitude.
            lon: Coordenada longitude.

        Returns:
            Dict listo para pasar a `ReporteEstructurado(**d)` o al endpoint.

        """
        self._contador += 1
        contador = self._contador
        servicios_list = servicios or ["A", "G"]
        return {
            "id": id_fijo or f"rpt-{contador}",
            "fuente": "telegram",
            "id_externo": id_fijo or f"tg-{contador}",
            "autor_anonimizado_id": f"u-{contador}",
            "mensaje_anonimizado": f"reporte de prueba {contador}",
            "estado_revision": estado_revision,
            "creado_en": fecha_fija or f"2025-09-15T0{contador}:00:00Z",
            "compuerta": {
                "es_reporte_accionable": accionable,
                "temporalidad": temporalidad,
                "intencion": intencion,
            },
            "naturaleza": {
                "tipo_evento": tipo_evento,
                "servicio_de_respuesta": servicios_list,
            },
            "ubicacion": {
                "ubicacion_texto_literal": f"Lugar de prueba {contador}",
                "barrio": barrio,
                "comuna": comuna,
                "punto_referencia": None,
                "nivel_granularidad": nivel_granularidad,
                "lat": lat,
                "lon": lon,
            },
        }

    def reporte_dict(self, **kwargs) -> dict[str, Any]:
        """Alias directo para `self.reporte(**kwargs)`.

        Args:
            **kwargs: Parametros a pasar a `self.reporte`.

        Returns:
            El dict con la forma completa.

        """
        return self.reporte(**kwargs)
