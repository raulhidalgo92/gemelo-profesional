# Gemelo digital profesional

Aplicación web que construye un **gemelo digital profesional** de cada usuario a partir de su currículum y le ayuda a explorar y planificar su trayectoria laboral con datos reales del mercado español.

> Proyecto desarrollado como parte del **Trabajo de Fin de Grado** del **Grado en Ingeniería Informática** de la **Universidad Internacional de La Rioja (UNIR)**.
> Autor: Raúl Hidalgo Calvo · Licencia [Apache 2.0](LICENSE)

## Qué hace

```
                   REGISTRO: sube CV + LinkedIn (PDF)
                                  │
                                  ▼
                        GEMELO PROFESIONAL
              (competencias ESCO, nivel y evidencias)
      ┌──────────────┬────────────┴──────┬──────────────────┐
      ▼              ▼                   ▼                  ▼
  MI FUTURO       EMPLEO             FORMARTE          ENTRENADOR
  Sankey de       Ofertas con        Qué aprender      Entrevista para
  trayectorias    % de encaje        primero y cuánto  una oferta + test
  + ruta          explicado          te abre           de inglés
      └──────────────┴─────────┬─────────┴──────────────────┘
                               ▼
         Cada acción ACTUALIZA el gemelo → se recalcula todo
```

La novedad es el **ciclo cerrado**: las respuestas de las entrevistas simuladas sirven como evidencia de las competencias del CV, de modo que el sistema distingue entre lo que el usuario **declara** y lo que **demuestra**, y cada recomendación se acompaña de una explicación.

## Arquitectura

| Carpeta     | Servicio  | Tecnología                                   | Función |
|-------------|-----------|----------------------------------------------|---------|
| `core/`     | —         | Python 3.12, SQLAlchemy 2, pgvector          | Modelo de datos, configuración, cliente de IA y seudonimización compartidos |
| `ingesta/`  | `ingesta` | Python, APScheduler                          | Carga de ESCO, O*NET, INE, Cedefop y ofertas nocturnas (EURES, InfoJobs) |
| `backend/`  | `backend` | FastAPI, Alembic                             | API REST (`/api`), migraciones |
| `frontend/` | `frontend`| Angular 21                                   | Interfaz web |
| `db/`       | `db`      | PostgreSQL 17 + pgvector + pg_trgm           | Mercado laboral y gemelos de usuario |

Más detalle en [docs/arquitectura.md](docs/arquitectura.md) y [docs/fuentes-de-datos.md](docs/fuentes-de-datos.md).

## Puesta en marcha (desarrollo)

Requisitos: Docker con Docker Compose v2 y un proyecto de Google Cloud con Vertex AI habilitado.

```bash
cp .env.example .env          # y revisa los valores
mkdir -p secretos             # copia aquí la clave JSON de la cuenta de servicio como vertex.json
docker compose up --build
```

- Interfaz: http://localhost:4200
- API y documentación interactiva: http://localhost:8000/api/docs
- Visor de la base de datos (Adminer): http://localhost:8090 (servidor `db`, usuario y contraseña de `.env`)

### Cargar los datos de referencia

```bash
# ESCO completo (≈13.500 competencias, ≈2.900 ocupaciones) desde su API oficial
docker compose exec ingesta python -m ingesta esco-api

# O*NET 31.0 (descarga automática del zip oficial)
docker compose exec ingesta python -m ingesta onet

# Correspondencias ESCO ↔ O*NET (necesita las dos anteriores)
docker compose exec ingesta python -m ingesta esco-onet

# Vectores semánticos de ESCO (necesita Vertex AI configurado)
docker compose exec ingesta python -m ingesta embeddings

# Salarios por ocupación del INE (API pública, sin registro)
docker compose exec ingesta python -m ingesta ine

# Ofertas de InfoJobs (requiere credenciales en .env)
docker compose exec ingesta python -m ingesta infojobs --consulta "desarrollador" --paginas 2
```

Las descargas se guardan en `data/` (no se versiona). Como alternativa a la API, ESCO también se puede cargar desde su descarga en CSV (español) colocada en `data/raw/esco/`: `python -m ingesta esco`.

### Tests y calidad

```bash
docker compose exec backend pytest
docker compose exec backend ruff check /srv
docker compose exec ingesta pytest
cd frontend && npm test
```

## Flujo de trabajo

- `main`: versiones estables (lo que se despliega).
- `develop`: integración del trabajo en curso.
- `feature/<descripcion>`, `fix/<descripcion>`, `docs/<descripcion>`: una rama por cambio, creada desde `develop`.

Cada rama se integra en `develop` mediante pull request, y `develop` se integra en `main` también mediante pull request. La integración continua (lint, tests y compilación) se ejecuta en cada pull request.

## Despliegue

En un servidor con Docker (alojado en la UE):

```bash
cp .env.example .env    # valores de producción
DOMINIO=midominio.es docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Caddy obtiene automáticamente el certificado HTTPS para el dominio.

## Protección de datos

- Consentimiento explícito en el registro y borrado completo de la cuenta.
- El archivo original del CV se elimina tras extraer la información.
- Los datos identificativos se **seudonimizan** antes de enviarse a un modelo de lenguaje.
- No se guarda audio: la voz se transcribe y se descarta.
- Servidores y procesamiento de los modelos de lenguaje dentro de la UE (Vertex AI, región europea).

## Licencia y datos de terceros

Código bajo licencia Apache 2.0. Los datos de ESCO, O*NET, INE, Cedefop, EURES e InfoJobs **no** se incluyen en el repositorio y se usan según sus propias condiciones (ver [NOTICE](NOTICE)).
