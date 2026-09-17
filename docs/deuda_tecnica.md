# Deuda técnica registrada

Inventario de decisiones asumidas deliberadamente o pendientes de refactor, para que queden visibles y no se olviden. Un ítem sale de aquí cuando se resuelve en un PR.

## Servicio Geo

Registrado en la revisión del PR #45 (prototipo; no bloquea el merge dado el tráfico esperado).

1. **Inicialización a nivel de módulo en `backend/geo/geo/main.py`**: `_gazetteer_inicial`/`_externo_inicial` se construyen al importar el módulo (abre y parsea `gazetteer.json`, ~57 KB). Inconsistente con el patrón de inicialización perezosa del CRUD (PR #44) para no tocar el sistema de archivos al importar. Conviene moverlos a una inicialización perezosa (con caché) cuando se integre con el resto del sistema.

2. **Cliente de Nominatim y RateLimiter**: se crean en `NominatimResolver.__init__` (un `geopy` `Nominatim` por resolver) — el `geocode` no reabre clientes por llamada, pero el armado del resolutor repite configuración si hubiera muchos. No es incorrecto; solo duplicado de configuración si se llega a instanciar más de un resolver por proceso (hoy hay exactamente uno).