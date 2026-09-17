# Gold standard v1

Freeze **2026-09-10** · corpus consolidado de los 400 reportes anotados en partidas y revisión cruzada. Es la referencia de evaluación: nadie lo edita después de este punto.

- Total: **400** mensajes.
- Desarrollo: **60** · Evaluación: **340**.
- Semilla del split: `20239626`.

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

## Checksums

| Archivo | SHA-256 |
|---------|---------|
| `gold_standard_v1.jsonl` | `63dbf721a384bba92a3b160d3172c80b2e44286af1a2740829278cec0b85a992` |
| `dev.jsonl` | `57b034dd1c7a4bf8b03eb5fef8f8c151d2d3ad4f020cf93bab44e1695099a32c` |
| `eval.jsonl` | `20c53e5a6efbd5511d1bb151c654e47941bfaf8ed5b3a34095dabe4e67738912` |

## Criterios de aceptación

- [x] Discrepancias de la submuestra del 20% resueltas y documentadas (**80** mensajes en revisión; desempate en `resoluciones.md`).
- [x] Gold standard v1 congelado como archivo versionado.
- [x] Métricas de concordancia inter-anotador calculadas y reportadas en `concordancia_interanotador.md`.
