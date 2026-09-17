# Anotación del corpus — manifiesto de partidas

Versión **1.0** · colectivo (4 integrantes) · ventana: 2026-09-04 → 2026-09-09.

## 1. Asignación

- Corpus: **400** mensajes (gold del corpus sintético).
- Semilla de reparto de partidas: `20240901`.
- Semilla de submuestra: `20241826`.
- Submuestra de revisión cruzada: **80** mensajes (20% del corpus), cada uno con **dos** anotadores.

| Integrante | Partida (ids) | Revisor en crosscheck |
|------------|---------------|----------------------|
| cesar | 100 (`5–398`) | 22 mensajes |
| julian | 100 (`2–400`) | 20 mensajes |
| juan | 100 (`1–399`) | 14 mensajes |
| sebas | 100 (`6–397`) | 24 mensajes |

## 2. Cobertura del esquema por anotación

Cada línea de cada partida incluye `texto`, `id` y la capa 1 (compuerta con `es_reporte_accionable`, `temporalidad` e `intencion`); las capas 2 y 3 (`naturaleza` y `ubicacion`) solo en mensajes accionables, según el protocolo, y siempre con los campos del esquema de extracción.

## 3. Distribución del corpus

| Clase | N |
|-------|---|
| pregunta | 44 |
| noticia | 40 |
| rumor | 40 |
| inundacion_subita | 36 |
| incendio_estructural | 34 |
| incendio_cobertura_vegetal | 30 |
| inundacion_lenta | 26 |
| multi_intencion | 26 |
| movimiento_en_masa | 24 |
| salud_ambiental | 22 |
| accionable_sin_ubicacion | 20 |
| falso_evento | 20 |
| aglomeracion_publico | 16 |
| oferta_ayuda | 12 |
| sismo | 10 |

## 4. Criterios de aceptación

- [x] 100% del corpus anotado (4 partidas, solapamiento cero).
- [x] Submuestra al 20% anotada por duplicado (revisión cruzada).
- [x] Cuota de cada integrante documentada (tabla de §1).
- [x] Campos del esquema cubiertos en cada anotación (§2).
