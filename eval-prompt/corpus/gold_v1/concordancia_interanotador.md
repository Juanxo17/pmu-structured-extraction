# Concordancia inter-anotador (Kappa de Cohen)

Calculada sobre la submuestra de revisión cruzada (cada mensaje con dos anotadores). Kappa no ponderado; `acuerdo` es la proporción de coincidencias sobre los pares comparables.

| Campo | n | Acuerdo % | Kappa |
|-------|---|--------|-------|
| es_reporte_accionable | 80 | 100.0% | 1.000 |
| intencion | 80 | 93.8% | 0.879 |
| temporalidad | 80 | 97.5% | 0.963 |
| tipo_evento | 52 | 100.0% | 1.000 |
| servicio | 52 | 100.0% | 1.000 |
| nivel_granularidad | 52 | 98.1% | 0.975 |

**Promedio (macro) de Kappa por campo: 0.970**

Lectura: los campos de compuerta, servicio y tipo de evento alcanzan concordancia casi perfecta; las diferencias observadas se concentran en intención, temporalidad y granularidad y quedaron documentadas en `resoluciones.md`.
