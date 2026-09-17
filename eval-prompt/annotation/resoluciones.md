# Desempate de la revisión cruzada

Discrepancias entre la pasada original y el revisor, resueltas con el criterio del protocolo de anotación. Nada se inventa: ante la duda se elige el valor menos preciso pero defendible.

Submuestra: **80** mensajes · distintas: **8** (~10%).

| id | clase | campo | anotación 1 | anotación 2 | resolución (gold) |
| 5 | sismo | compuerta.intencion | `"reporta_terceros"` | `"solicita_informacion"` | `"reporta_terceros"` |
| 123 | incendio_cobertura_vegetal | compuerta.intencion | `"solicita_ayuda"` | `"reporta_terceros"` | `"solicita_ayuda"` |
| 202 | oferta_ayuda | compuerta.temporalidad | `"ya_ocurrio"` | `"ocurriendo_ahora"` | `"ya_ocurrio"` |
| 213 | accionable_sin_ubicacion | compuerta.temporalidad | `"ocurriendo_ahora"` | `"ya_ocurrio"` | `"ocurriendo_ahora"` |
| 235 | multi_intencion | ubicacion.nivel_granularidad | `"ciudad"` | `"indeterminada"` | `"ciudad"` |
| 305 | falso_evento | compuerta.intencion | `"reporta_terceros"` | `"solicita_informacion"` | `"reporta_terceros"` |
| 365 | rumor | compuerta.intencion | `"solicita_informacion"` | `"reporta_terceros"` | `"solicita_informacion"` |
| 383 | rumor | compuerta.intencion | `"reporta_terceros"` | `"solicita_informacion"` | `"reporta_terceros"` |

En todos los casos la resolución es el valor **gold** (vino de la anotación que mantuvo el dato más específico defendible).
