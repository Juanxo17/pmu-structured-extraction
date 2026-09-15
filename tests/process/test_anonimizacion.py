"""Pruebas del modulo de anonimizacion de datos personales."""

import pytest

from process.anonimizacion import anonimizar_texto


class TestAnonimizarTexto:
    """Pruebas de anonimizar_texto contra los distintos tipos de PII."""

    def test_enmascara_telefono(self) -> None:
        """Un numero de telefono colombiano se reemplaza por la mascara."""
        # Arrange
        texto = "Mi telefono es 3204567890, llamenme"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "3204567890" not in resultado
        assert "[DATO_PERSONAL]" in resultado

    def test_no_enmascara_direccion_exacta(self) -> None:
        """Una direccion con numero de vivienda exacto NO se anonimiza (decision de equipo)."""
        # Arrange
        texto = "Vivo en Calle 5 # 23-10, estamos atrapados"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "Calle 5 # 23-10" in resultado

    def test_enmascara_nombre_de_persona(self) -> None:
        """Un nombre propio (con tildes correctas) se reemplaza por la mascara."""
        # Arrange
        texto = "Me llamo Andrés y necesito ayuda urgente"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "Andrés" not in resultado
        assert "[DATO_PERSONAL]" in resultado

    @pytest.mark.xfail(
        reason=(
            "Limitacion conocida de es_core_news_md: sin tildes, el modelo "
            "no siempre reconoce el nombre como entidad PER. Mensajeria "
            "informal suele omitir tildes. Revisar impacto real con el "
            "corpus anotado antes de invertir en un modelo mas "
            "grande o normalizacion de tildes."
        ),
        strict=False,
    )
    def test_nombre_sin_tilde_no_siempre_se_detecta(self) -> None:
        """Documenta que un nombre sin tilde puede no anonimizarse -- no es un bug oculto."""
        # Arrange
        texto = "Me llamo Andres y necesito ayuda urgente"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "Andres" not in resultado

    def test_no_enmascara_ubicacion_general(self) -> None:
        """Barrio/comuna/punto de referencia NO se anonimizan -- Geo los necesita."""
        # Arrange
        texto = "Auxilio, hay un derrumbe cerca al puente de la Carrera 1"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "puente de la Carrera 1" in resultado

    def test_no_enmascara_via_sin_numero_de_vivienda(self) -> None:
        """Una mencion general de via, sin numero-#-numero, no se anonimiza."""
        # Arrange
        texto = "Estamos en la Carrera 1 con Calle 5, cerca del parque"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "[DATO_PERSONAL]" not in resultado

    def test_mensaje_combinado_anonimiza_nombre_y_telefono_pero_no_direccion(self) -> None:
        """Un mensaje realista: nombre y telefono se anonimizan, direccion y barrio no."""
        # Arrange
        texto = (
            "Habla Andrés, mi telefono es 3204567890, vivo en Calle 5 # 23-10 "
            "y hay un incendio en el barrio Siloé"
        )

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "Andrés" not in resultado
        assert "3204567890" not in resultado
        assert "Calle 5 # 23-10" in resultado  # direccion, se conserva
        assert "Siloé" in resultado  # ubicacion general, se conserva

    def test_mensaje_sin_pii_queda_igual(self) -> None:
        """Un mensaje sin datos personales no se modifica de forma visible."""
        # Arrange
        texto = "Hay una aglomeracion de personas en el parque, todo tranquilo"

        # Act
        resultado = anonimizar_texto(texto)

        # Assert
        assert "[DATO_PERSONAL]" not in resultado
