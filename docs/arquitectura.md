# Arquitectura

## Visión general

```
 ① REFERENCIA (1 vez)     ② OFERTAS (cada noche)   ③ USUARIO (al usarla)       ④ BAJO DEMANDA
 ESCO · O*NET · INE        EURES · InfoJobs          CV · LinkedIn (PDF)          "Pega la oferta"
 Cedefop                                             Entrevistas · Inglés         (LinkedIn u otra web)
        └──────────┬───────────┘                           └──────────┬──────────────┘
                   ▼                                                  ▼
        servicio INGESTA                                     servicio BACKEND
        normalizar + IA: todo                                normalizar + IA: CV → competencias,
        pasa a "idioma" ESCO                                 entrevista → nota y evidencias
                   └────────────────────┬─────────────────────────────┘
                                        ▼
                         BASE DE DATOS (PostgreSQL + pgvector)
                   Mercado: ofertas, competencias, transiciones, salarios
                   Usuario: GEMELO PROFESIONAL (competencias + evidencias)
                                        │
                                        ▼
                              FRONTEND (Angular)
              Mi futuro · Empleo · Formarte · Entrenador
```

## Servicios

| Servicio  | Responsabilidad | Se comunica con |
|-----------|-----------------|-----------------|
| `db`      | Persistencia. Extensiones `vector` (similitud semántica), `pg_trgm` (búsqueda aproximada) y `unaccent`. | — |
| `ingesta` | Datos de referencia (entrada ①) y ofertas nocturnas (entrada ②). Idempotente: relanzar no duplica. | `db`, APIs externas, LLM |
| `backend` | API REST, autenticación, entradas ③ y ④, cálculo de encaje, recomendaciones y trayectorias. Ejecuta las migraciones al arrancar. | `db`, LLM, STT |
| `frontend`| Interfaz de usuario. En producción, nginx sirve los estáticos y redirige `/api` al backend. | `backend` |
| `caddy`   | (solo producción) HTTPS automático y proxy inverso. | `frontend` |

`core/` es un paquete Python compartido por `backend` e `ingesta` para que ambos usen exactamente el mismo modelo de datos.

## Modelo de datos

**Mercado**
- `ocupacion`, `competencia`, `ocupacion_competencia`: clasificación ESCO (vocabulario común).
- `ocupacion_onet`, `transicion_onet`, `mapeo_esco_onet`: matriz de ocupaciones relacionadas de O*NET y su enlace con ESCO. Es la base del diagrama de Sankey.
- `oferta`, `oferta_competencia`: ofertas normalizadas y sus competencias ESCO.
- `estadistica_salarial`, `correspondencia_cno_isco`: salarios agregados del INE por ocupación CNO-11 y su enlace con ISCO-08 (y, por tanto, con ESCO).

**Usuario**
- `usuario`: cuenta y consentimiento RGPD.
- `gemelo`: gemelo profesional (ocupación actual, nivel de inglés, trayectoria seudonimizada).
- `gemelo_competencia`: nivel **declarado** y **demostrado** de cada competencia.
- `evidencia`: qué respalda cada nivel (fragmento de CV, respuesta de entrevista, test).
- `entrevista`: transcripción de las entrevistas simuladas (sin audio).

## Uso de modelos de lenguaje

El acceso a los modelos se encapsula en `core/src/gemelo_core/ia.py` con la interfaz `ClienteIA`. La implementación por defecto usa Gemini en Vertex AI con región europea; otra implementación admite cualquier API compatible con OpenAI, lo que permite comparar modelos en la evaluación. Antes de cualquier llamada con datos de usuario se aplica `seudonimizacion.py`. Ver [decisión 0002](decisiones/0002-proveedor-ia.md).

## Decisiones

Ver [docs/decisiones](decisiones/).
