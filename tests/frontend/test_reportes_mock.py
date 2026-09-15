"""Pruebas del dataset y el cliente simulado de reportes."""

import pytest
from sirena_schema.ontologia import ONTOLOGIA
from sirena_schema.schema import ReporteEstructurado

from frontend.bff_client import FiltrosReportes
from frontend.comunas import centroide
from frontend.reportes_mock import (
    ClienteReportesSimulado,
    aplicar_correccion,
    coincide_con_filtros,
    reportes_de_ejemplo,
)


class TestDatosSimulados:
    """El dataset de ejemplo debe ser siempre válido contra el contrato compartido."""

    def test_todos_los_registros_son_reporte_estructurado_valido(self) -> None:
        """Cada registro del dataset es una instancia real de ReporteEstructurado."""
        # Arrange
        reportes = reportes_de_ejemplo()

        # Act / Assert
        assert reportes
        assert all(isinstance(r, ReporteEstructurado) for r in reportes)

    def test_todo_tipo_evento_usado_esta_en_la_ontologia_vigente(self) -> None:
        """Ningún registro usa un tipo_evento fuera de config/ontologia.yaml."""
        # Arrange
        reportes = reportes_de_ejemplo()

        # Act
        tipos_usados = {r.naturaleza.tipo_evento for r in reportes if r.naturaleza}

        # Assert
        assert tipos_usados <= ONTOLOGIA.tipos_evento

    def test_toda_comuna_usada_tiene_centroide_para_el_mapa(self) -> None:
        """Cada comuna que aparece en el dataset tiene un centroide local conocido."""
        # Arrange
        reportes = reportes_de_ejemplo()

        # Act
        comunas_usadas = {
            r.ubicacion.comuna for r in reportes if r.ubicacion and r.ubicacion.comuna
        }

        # Assert
        assert comunas_usadas
        for comuna in comunas_usadas:
            assert centroide(comuna) is not None

    def test_incluye_al_menos_un_reporte_con_coordenada_exacta(self) -> None:
        """El dataset cubre el camino de lat/lon real, no solo el respaldo por comuna."""
        # Arrange
        reportes = reportes_de_ejemplo()

        # Act
        con_coordenada = [
            r for r in reportes if r.ubicacion and r.ubicacion.lat and r.ubicacion.lon
        ]

        # Assert
        assert con_coordenada

    def test_incluye_al_menos_un_reporte_exacto_sin_coordenada(self) -> None:
        """Y también cubre el caso de respaldo: granularidad exacta pero sin lat/lon todavía."""
        # Arrange
        reportes = reportes_de_ejemplo()

        # Act
        sin_coordenada = [
            r
            for r in reportes
            if r.ubicacion
            and r.ubicacion.nivel_granularidad == "exacta"
            and r.ubicacion.lat is None
        ]

        # Assert
        assert sin_coordenada


class TestCoincideConFiltros:
    """Pruebas de la función pura de filtrado usada por el cliente simulado."""

    def test_filtro_de_tipo_evento_excluye_lo_que_no_coincide(self) -> None:
        """Filtrar por tipo_evento deja solo reportes de ese tipo."""
        # Arrange
        reportes = reportes_de_ejemplo()
        filtros = FiltrosReportes(tipo_evento=["sismo"])

        # Act
        resultado = [r for r in reportes if coincide_con_filtros(r, filtros)]

        # Assert
        assert resultado
        assert all(r.naturaleza and r.naturaleza.tipo_evento == "sismo" for r in resultado)

    def test_filtro_de_estado_revision_distingue_pendientes_de_revisados(self) -> None:
        """Filtrar por estado_revision deja solo reportes en ese estado."""
        # Arrange
        reportes = reportes_de_ejemplo()
        filtros = FiltrosReportes(estado_revision="revisado")

        # Act
        resultado = [r for r in reportes if coincide_con_filtros(r, filtros)]

        # Assert
        assert resultado
        assert all(r.estado_revision == "revisado" for r in resultado)

    def test_filtro_de_busqueda_q_es_insensible_a_mayusculas(self) -> None:
        """El filtro de texto libre no distingue mayúsculas de minúsculas."""
        # Arrange
        reportes = reportes_de_ejemplo()
        algun_reporte = reportes[0]
        fragmento = algun_reporte.mensaje_anonimizado.split()[0].upper()
        filtros = FiltrosReportes(q=fragmento)

        # Act
        resultado = [r for r in reportes if coincide_con_filtros(r, filtros)]

        # Assert
        assert algun_reporte in resultado

    def test_filtro_de_accionable_deja_solo_los_descartados_en_la_compuerta(self) -> None:
        """accionable=False deja solo los reportes sin naturaleza/ubicación."""
        # Arrange
        reportes = reportes_de_ejemplo()
        filtros = FiltrosReportes(accionable=False)

        # Act
        resultado = [r for r in reportes if coincide_con_filtros(r, filtros)]

        # Assert
        assert resultado
        assert all(not r.compuerta.es_reporte_accionable for r in resultado)
        assert all(r.naturaleza is None for r in resultado)

    def test_filtro_de_accionable_en_true_excluye_los_descartados(self) -> None:
        """accionable=True deja solo los reportes con naturaleza/ubicación resueltas."""
        # Arrange
        reportes = reportes_de_ejemplo()
        filtros = FiltrosReportes(accionable=True)

        # Act
        resultado = [r for r in reportes if coincide_con_filtros(r, filtros)]

        # Assert
        assert resultado
        assert all(r.compuerta.es_reporte_accionable for r in resultado)


class TestAplicarCorreccion:
    """Pruebas de la aplicación de correcciones de triaje."""

    def test_corrige_tipo_evento_dentro_de_naturaleza(self) -> None:
        """Corregir tipo_evento actualiza naturaleza sin tocar el resto del reporte."""
        # Arrange
        reporte = reportes_de_ejemplo()[0]

        # Act
        corregido = aplicar_correccion(reporte, {"tipo_evento": "salud_ambiental"})

        # Assert
        assert corregido.naturaleza is not None
        assert corregido.naturaleza.tipo_evento == "salud_ambiental"
        assert corregido.id == reporte.id

    def test_corrige_campos_de_secciones_distintas_a_la_vez(self) -> None:
        """Una corrección puede tocar compuerta y ubicación en la misma llamada."""
        # Arrange
        reporte = reportes_de_ejemplo()[0]

        # Act
        corregido = aplicar_correccion(
            reporte, {"intencion": "solicita_informacion", "comuna": "Comuna 3"}
        )

        # Assert
        assert corregido.compuerta.intencion == "solicita_informacion"
        assert corregido.ubicacion is not None
        assert corregido.ubicacion.comuna == "Comuna 3"

    def test_rechaza_campo_de_correccion_desconocido(self) -> None:
        """Una llave que no pertenece a ninguna sección conocida lanza ValueError."""
        # Arrange
        reporte = reportes_de_ejemplo()[0]

        # Act / Assert
        with pytest.raises(ValueError):
            aplicar_correccion(reporte, {"campo_inexistente": "x"})


class TestClienteReportesSimulado:
    """Pruebas del cliente simulado como implementación de ClienteReportes."""

    def test_listar_respeta_el_tamano_de_pagina_y_cuenta_el_total_filtrado(self) -> None:
        """listar pagina los resultados pero total refleja todo lo filtrado."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act
        pagina = cliente.listar(FiltrosReportes(estado_revision="pendiente", tamano_pagina=2))

        # Assert
        assert len(pagina.resultados) <= 2
        assert pagina.total >= len(pagina.resultados)
        assert all(r.estado_revision == "pendiente" for r in pagina.resultados)

    def test_actualizar_cambia_estado_revision_y_persiste_en_memoria(self) -> None:
        """actualizar deja el nuevo estado disponible en obtener posteriores."""
        # Arrange
        cliente = ClienteReportesSimulado()
        reporte = cliente.listar(FiltrosReportes(tamano_pagina=1)).resultados[0]

        # Act
        actualizado = cliente.actualizar(reporte.id, estado_revision="revisado")

        # Assert
        assert actualizado.estado_revision == "revisado"
        assert cliente.obtener(reporte.id).estado_revision == "revisado"

    def test_obtener_reporte_inexistente_lanza_keyerror(self) -> None:
        """obtener un id que no existe en el dataset lanza KeyError."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act / Assert
        with pytest.raises(KeyError):
            cliente.obtener("no-existe")

    def test_resumen_reparte_pendientes_y_revisados_sobre_el_total(self) -> None:
        """pendientes + revisados == total en el resumen del cliente simulado."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act
        resumen = cliente.resumen()

        # Assert
        assert resumen.pendientes + resumen.revisados == resumen.total

    def test_resumen_por_accionable_cuadra_con_el_total(self) -> None:
        """accionables + no_accionables == total, y por_tipo_evento solo cuenta accionables."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act
        resumen = cliente.resumen()

        # Assert
        accionables = resumen.por_accionable["accionable"]
        no_accionables = resumen.por_accionable["no_accionable"]
        assert accionables + no_accionables == resumen.total
        assert no_accionables > 0
        assert sum(resumen.por_tipo_evento.values()) == accionables

    def test_resumen_por_temporalidad_e_intencion_cuadran_con_el_total(self) -> None:
        """A diferencia de por_tipo_evento, estos dos sí cuentan a los no accionables."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act
        resumen = cliente.resumen()

        # Assert
        assert sum(resumen.por_temporalidad.values()) == resumen.total
        assert sum(resumen.por_intencion.values()) == resumen.total

    def test_resumen_por_servicio_de_respuesta_no_esta_vacio(self) -> None:
        """El resumen cuenta al menos un servicio de respuesta reportado."""
        # Arrange
        cliente = ClienteReportesSimulado()

        # Act
        resumen = cliente.resumen()

        # Assert
        assert resumen.por_servicio_de_respuesta
        assert all(conteo > 0 for conteo in resumen.por_servicio_de_respuesta.values())
