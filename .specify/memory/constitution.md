# SIRENA Constitution

## Core Principles

### I. Copiloto, no decisor
El sistema estructura hechos; nunca valora gravedad, prioridad, orden de atención, ni despacha recursos. Toda decisión de despacho la toma un operador humano sobre el registro estructurado.

### II. Trazabilidad obligatoria
Cada registro se persiste y se presenta junto al mensaje original (anonimizado) que lo produjo. Ningún campo estructurado existe sin su evidencia de origen visible al operador.

### III. El modelo no geocodifica ni decide territorio
La extracción entrega texto (`ubicacion_texto_literal`, `punto_referencia`); la resolución a barrio/comuna/coordenadas la hace un componente determinista (Geo), nunca el LLM. Ante ambigüedad, se declara el nivel de granularidad más específico defendible — nunca una suposición de mayor precisión.

### IV. Taxonomía enchufable
`tipo_evento` y `servicio_de_respuesta` se validan contra `config/ontologia.yaml` en tiempo de ejecución, nunca como valores fijos en código. Sustituir la ontología por la de otro dominio no debe requerir tocar el esquema ni los servicios.

### V. Sin entrenamiento, sin GPU local
El modelo se usa zero/few-shot tal como se publica; no hay fine-tuning ni ajuste de pesos. La inferencia corre íntegramente vía API remota (Groq); ningún servicio asume GPU disponible.

## Restricciones de alcance

No incluidos por principio, no por falta de tiempo: valoración de gravedad/prioridad, despacho automático de recursos, verificación factual del contenido del mensaje (el sistema estructura lo que dice el mensaje, no si es cierto). Datos personales (nombres, teléfonos, direcciones exactas) se anonimizan antes de llegar al modelo y antes de persistirse — nunca se envían a un proveedor externo ni se guardan en claro.

## Flujo de desarrollo

Convenciones operativas del día a día (gestor de paquetes, estilo, pruebas, Gitflow, estructura de carpetas) viven en [`AGENTS.md`](../../AGENTS.md), no se duplican aquí. El contrato entre servicios vive en [`docs/CONTRATOS_SISTEMA.md`](../../docs/CONTRATOS_SISTEMA.md).

## Governance

Esta constitución fija principios de producto y ética; no se modifica para acomodar una implementación puntual. Un cambio a los Core Principles requiere acuerdo del equipo completo, igual que un cambio al esquema de extracción.

**Version**: 1.0.0 | **Ratified**: 2026-09-13 | **Last Amended**: 2026-09-13
