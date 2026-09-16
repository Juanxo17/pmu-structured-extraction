# Contratos del Sistema (arquitectura de 5 servicios)

Este documento define la interfaz HTTP que debe exponer cada uno de los 5 servicios de SIRENA, para que los 4 integrantes puedan trabajar en paralelo contra un contrato fijo, sin bloquearse entre sí.

**Qué fija un contrato:** método HTTP, ruta, cuerpo de request/response (campos, tipo, obligatoriedad), códigos de estado.
**Qué NO fija:** implementación interna de cada servicio, librerías usadas por dentro, funciones privadas — libertad de quien construye el servicio.

**Comunicación:** HTTP/REST síncrono entre los 5 servicios, cada uno un proceso FastAPI independiente.

## Mapa de servicios y puertos

| Servicio | Puerto | Dueño | Issues |
|---|---|---|---|
| **BFF** | 8000 | Cesar | T-19, T-21 |
| **CRUD** | 8001 | Julian | T-20 |
| **Process** (Preprocesamiento + Extracción) | 8002 | Cesar | T-10, T-14, T-17 |
| **Inference** | 8003 | Juan | T-11, T-12, T-13 |
| **Geo** | 8004 | Julian | T-06, T-16 |

## Flujo de llamadas

```
Frontend (Streamlit) ──┐
                        ▼
Telegram ──────────► BFF :8000 ──────► CRUD :8001 (GET /reportes — consulta dashboard)
                        │
                        │ POST /procesar
                        ▼
              Process :8002 (Preprocesamiento + Extracción)
                        │
                        ├──► Inference :8003 (POST /compuerta, luego POST /extraccion si aplica)
                        ├──► Geo :8004 (POST /resolver)
                        └──► CRUD :8001 (POST /reportes — persiste resultado final, directo, sin pasar por BFF)
```

BFF mantiene la interfaz `FuenteDeMensajes` (una implementación hoy: `TelegramSource`; diseñada para admitir otras a futuro, ej. WhatsApp, sin tocar el resto del sistema).

Process decide internamente si ejecuta la llamada 2 (extracción) tras el resultado de la llamada 1 (compuerta) — esto es opaco para quien lo invoca: BFF solo ve un único `POST /procesar` que responde con el resultado final (estructurado o descartado).

---

## Esquema compartido — `ReporteEstructurado` (Pydantic v2)

Fuente de verdad: T-02. Lo consumen Inference (lo produce), Process (lo orquesta), CRUD (lo persiste), BFF/Frontend (lo consultan).

`tipo_evento`/`servicio_de_respuesta` se validan en runtime contra `config/ontologia.yaml` (T-03), no van como `Literal` fijo — así el vocabulario cambia sin tocar código.

```python
class Compuerta(BaseModel):
    es_reporte_accionable: bool
    temporalidad: Literal["ocurriendo_ahora", "ya_ocurrio", "riesgo_previsto", "referencia_noticia"]
    intencion: Literal["solicita_ayuda", "reporta_terceros", "ofrece_ayuda", "solicita_informacion"]
```

Correspondencia de `intencion`/`temporalidad` hacia las clases de HumAID (justificación, no se valida en código):

| HumAID | SIRENA |
|---|---|
| Requests or urgent needs | `intencion = solicita_ayuda` |
| Rescue, volunteering, or donation effort | `intencion = ofrece_ayuda` |
| Displaced people and evacuations | `intencion = reporta_terceros` |
| Injured or dead people | `intencion = reporta_terceros` + `servicio_de_respuesta = G` |
| Missing or found people | `intencion = reporta_terceros` + `servicio_de_respuesta = M` |
| Infrastructure and utility damage | `intencion = reporta_terceros` + `servicio_de_respuesta ∈ {K, L}` |
| Caution and advice | `temporalidad = riesgo_previsto` |
| Other relevant information | `intencion = solicita_informacion` |
| Sympathy and support | `es_reporte_accionable = false` |
| Not humanitarian | `es_reporte_accionable = false` |

```python
class Naturaleza(BaseModel):
    tipo_evento: str  # validado en tiempo de ejecución contra config/ontologia.yaml
    servicio_de_respuesta: list[str]  # idem — multietiqueta

    @field_validator("tipo_evento")
    @classmethod
    def _validar_tipo_evento(cls, v: str) -> str:
        if v not in ONTOLOGIA.tipos_evento:
            raise ValueError(f"tipo_evento no está en la ontología vigente: {v}")
        return v

    @field_validator("servicio_de_respuesta")
    @classmethod
    def _validar_servicios(cls, v: list[str]) -> list[str]:
        invalidos = set(v) - ONTOLOGIA.servicios_de_respuesta
        if invalidos:
            raise ValueError(f"servicio_de_respuesta no reportable: {invalidos}")
        return v
```

Vocabulario vigente hoy en `config/ontologia.yaml` (Anexo C, fuente: ERE de Cali):

- **`tipo_evento`** (8): `sismo` · `movimiento_en_masa` · `inundacion_subita` · `inundacion_lenta` · `incendio_cobertura_vegetal` · `incendio_estructural` · `aglomeracion_publico` · `salud_ambiental`
- **`servicio_de_respuesta`** (16 reportables, código de letra): `A` Búsqueda y Rescate · `B` Extinción de Incendios · `C` Telecomunicaciones para la comunidad · `D` Manejo de Materiales Peligrosos · `E` Seguridad y Convivencia · `F` Accesibilidad y Transporte · `G` Salud · `H` Agua Potable · `I` Asistencia Humanitaria · `J` Alojamientos Temporales · `K` Energía y Gas · `L` Saneamiento Básico · `M` Reencuentro Familiar · `N` Fauna Doméstica · `O` Fauna Silvestre · `R` Manejo de Residuos Sólidos (se excluyen `P`/`Q`, funciones institucionales no reportables por la ciudadanía)

**No hay mapeo fijo `tipo_evento` → `servicio_de_respuesta`** — son campos independientes, el modelo los extrae cada uno de lo que dice el mensaje concreto. Tabla orientativa (no oficial, no validada por la ERE) para guiar T-04 (protocolo de anotación):

| `tipo_evento` | Servicios más probables | Menos probables, no descartar |
|---|---|---|
| `sismo` | A, G, J, K, H, M | C, F, D, N, O, L |
| `movimiento_en_masa` | A, G, J, F, K | M, N, O |
| `inundacion_subita` | A, G, J, H, L | K, F, N, O, M |
| `inundacion_lenta` | J, H, L, G | I, F |
| `incendio_cobertura_vegetal` | B, G, N, O | A, F, K |
| `incendio_estructural` | B, A, G | J, K, D, M |
| `aglomeracion_publico` | E, G, A | F, C |
| `salud_ambiental` | G, H, L | D, I, R |

Un mensaje puede salirse de esta tabla — es guía para anotadores, no una regla de validación del esquema.

```python
class Ubicacion(BaseModel):
    ubicacion_texto_literal: str
    barrio: str | None
    comuna: str | None
    punto_referencia: str | None
    nivel_granularidad: Literal["exacta", "barrio", "comuna", "ciudad", "indeterminada"]
    lat: float | None
    lon: float | None


class ReporteEstructurado(BaseModel):
    id: str
    fuente: Literal["telegram"]
    id_externo: str  # id del mensaje en la fuente — usado para idempotencia
    autor_anonimizado_id: str  # hash del autor
    mensaje_anonimizado: str  # nunca el texto crudo con PII
    estado_revision: Literal["pendiente", "revisado"]
    compuerta: Compuerta
    naturaleza: Naturaleza | None  # None si es_reporte_accionable = False
    ubicacion: Ubicacion | None  # None si es_reporte_accionable = False
    creado_en: datetime
```

`pii_removida` no se persiste ni viaja en el esquema.

---

## 1. BFF — puerto 8000 (Cesar)

BFF es *gateway* puro hacia `reportes`: reenvía a CRUD sin lógica propia. El Frontend nunca necesita saber que CRUD existe como servicio separado.

| Método | Ruta | Request | Response | Descripción |
|---|---|---|---|---|
| `POST` | `/mensajes` | ver abajo | `202 {id_mensaje: str, estado: "recibido"}` | Recibe un mensaje desde `FuenteDeMensajes` (hoy: Telegram) y dispara `POST /procesar` en Process |
| `GET` | `/reportes` | filtros + paginación, ver CRUD | `200 {total, pagina, tamano_pagina, resultados: [...]}` | Proxy directo a CRUD — consumido por la bandeja del tablero (T-22) |
| `GET` | `/reportes/{id}` | — | `200 ReporteEstructurado` \| `404` | Proxy directo a CRUD — vista de detalle (T-23) |
| `PATCH` | `/reportes/{id}` | `{estado_revision, correccion?}` | `200 ReporteEstructurado` \| `404` \| `422` | Proxy directo a CRUD — mecanismo del triaje asistido (1.4): el operador marca "revisado" o corrige un campo mal extraído |
| `GET` | `/reportes/resumen` | `desde?`, `hasta?` | `200 {total, pendientes, revisados, por_tipo_evento, por_comuna}` | Proxy directo a CRUD — agregados para las tarjetas del encabezado del tablero |

**`POST /mensajes` — request:**

| Campo | Tipo | Obligatorio | Notas |
|---|---|---|---|
| `fuente` | `"telegram"` | sí | Fijo por ahora — más adelante puede haber otras vía `FuenteDeMensajes` |
| `id_externo` | `string` | sí | ID del mensaje en Telegram — usado para idempotencia |
| `texto` | `string` | sí | Contenido crudo. La anonimización (T-10) ocurre dentro de Process, no en BFF |
| `marca_temporal_origen` | `datetime ISO 8601` | sí | Hora del mensaje en Telegram, no la de recepción |

**Errores de `POST /mensajes`:** `400` si falta `fuente`/`texto`/`marca_temporal_origen`; `409` si `id_externo` ya fue recibido antes (duplicado exacto); `503` si el pipeline está saturado (cuota de Groq agotada, 4.6) — el cliente reintenta con backoff.

Internamente implementa la interfaz:

```python
class FuenteDeMensajes(Protocol):
    def escuchar(self) -> Iterator[MensajeCrudo]: ...


class TelegramSource(FuenteDeMensajes): ...
```

## 2. CRUD — puerto 8001 (Julian)

Único componente que toca SQLite. No conoce Telegram ni el LLM: solo guarda, lista, obtiene y actualiza registros.

| Método | Ruta | Request | Response | Descripción |
|---|---|---|---|---|
| `POST` | `/reportes` | `ReporteEstructurado` (sin `id`/`creado_en`) | `201 ReporteEstructurado` | Llamado por Process al final del pipeline |
| `GET` | `/reportes` | ver filtros abajo | `200 {total, pagina, tamano_pagina, resultados: [...]}` | Llamado por BFF. Devuelve la **versión resumida** (sin `mensaje_anonimizado` ni `punto_referencia`/coordenadas), para que la bandeja cargue rápido |
| `GET` | `/reportes/{id}` | — | `200 ReporteEstructurado` (completo) \| `404` | Llamado por BFF |
| `PATCH` | `/reportes/{id}` | `{estado_revision, correccion?}` | `200 ReporteEstructurado` \| `404` \| `422` | Llamado por BFF. `correccion` es un objeto parcial con cualquier campo de `compuerta`/`naturaleza`/`ubicacion` |
| `GET` | `/reportes/resumen` | `desde?`, `hasta?` | `200 {total, pendientes, revisados, por_tipo_evento, por_comuna}` | Llamado por BFF |

**Filtros de `GET /reportes`:** `tipo_evento`, `servicio_de_respuesta` (repetible, OR), `comuna`, `barrio`, `temporalidad`, `intencion`, `estado_revision`, `nivel_granularidad`, `desde`/`hasta` (por `creado_en`), `q` (búsqueda libre sobre `mensaje_anonimizado`), `pagina` (≥1, default 1), `tamano_pagina` (máx. 100, default 20).

## 3. Process (Preprocesamiento + Extracción) — puerto 8002 (Cesar)

| Método | Ruta | Request | Response | Descripción |
|---|---|---|---|---|
| `POST` | `/procesar` | `{mensaje_id: str, texto_crudo: str}` | `200 {estado: "estructurado", reporte: ReporteEstructurado}` \| `200 {estado: "descartado", motivo: str}` | Orquesta: anonimiza → detecta duplicado (T-17) → llama Inference (compuerta, y extracción si aplica) → llama Geo → persiste en CRUD → retorna resultado |

Las llamadas 1/2 a Inference y la llamada a Geo son **invisibles para quien invoca este endpoint** (BFF) — Process decide el flujo interno.

## 4. Inference — puerto 8003 (Juan)

| Método | Ruta | Request | Response | Descripción |
|---|---|---|---|---|
| `POST` | `/compuerta` | `{texto: str}` | `200 Compuerta` | Llamada 1 — clasifica si el mensaje es accionable |
| `POST` | `/extraccion` | `{texto: str}` | `200 {naturaleza: Naturaleza, ubicacion: Ubicacion}` | Llamada 2 — solo se invoca si `compuerta.es_reporte_accionable = true` |

Internamente incluye el validador/reparador (T-13): si la salida cruda del modelo no conforma al esquema, reintenta (máx. 3) antes de responder; si tras los reintentos sigue sin conformar, responde `422` con el detalle del rechazo.

## 5. Geo — puerto 8004 (Julian)

| Método | Ruta | Request | Response | Descripción |
|---|---|---|---|---|
| `POST` | `/resolver` | `{ubicacion_texto_literal: str, punto_referencia: str \| None}` | `200 {barrio: str \| None, comuna: str \| None, nivel_granularidad: str, lat: float \| None, lon: float \| None}` | Determinista, no invoca al LLM. Ante ambigüedad retorna el nivel más específico defendible; ante irresolubilidad, `nivel_granularidad = "indeterminada"` — nunca inventa un valor |

`nivel_granularidad` usa los mismos valores que `Ubicacion:` `"exacta"`, `"barrio"`, `"comuna"`, `"ciudad"`, `"indeterminada"`.

**Resolución (determinista, sin LLM):**
1. **Gazetteer local del IDESC** (22 comunas, 324 barrios y 18 sectores, con centroides EPSG:4326 — `backend/geo/data/gazetteer.json`): gana el nombre de barrio/sector más largo que aparezca completo en el texto; si no hay barrio, vale una `comuna N` explícita; si solo se menciona Cali, `"ciudad"`.
2. **Respaldo externo** (Nominatim vía geopy, acotado a Colombia y a la caja urbana de Cali; cache y tasa mínima de 1 s; configurable con `NOMINATIM_URL`, `NOMINATIM_USER_AGENT`, `NOMINATIM_COUNTRY_CODES`, `NOMINATIM_TIMEOUT`, `NOMINATIM_MIN_INTERVAL`): solo si el gazetteer no resolvió; si entrega coordenadas, `nivel_granularidad = "exacta"`.
3. Si ninguno convence, `{barrio: null, comuna: null, nivel_granularidad: "indeterminada", lat: null, lon: null}`.

`lat`/`lon` acompañan la resolución cuando el nivel lo permite (centroide del barrio, de la comuna o de la ciudad). El nombre canónico de la comuna es `"Comuna N"` sin ceros a la izquierda (ej. `"Comuna 13"`); el formato lo usa también el Frontend (`frontend/frontend/comunas.py`).

---

## Cómo desarrollar en paralelo sin bloquearse

Cada servicio se mockea contra este contrato mientras los demás no estén listos: un `TestClient` o un stub HTTP que responda con la forma exacta de arriba. Cuando el servicio real esté listo, se reemplaza la URL mockeada por la real (vía variable de entorno, ej. `INFERENCE_URL`), sin tocar el código del que consume.

## Cambios a este contrato

Si necesitas cambiar una ruta, un campo del esquema o un código de estado ya listado aquí:

1. Actualiza este archivo en el mismo PR.
2. Avisa al equipo — quien depende de ese contrato puede estar mockeando contra la versión anterior.
