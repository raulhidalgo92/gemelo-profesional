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

Requisitos: Docker con Docker Compose v2.

```bash
cp .env.example .env          # y rellena las claves
docker compose up --build
```

- Interfaz: http://localhost:4200
- API y documentación interactiva: http://localhost:8000/api/docs

### Cargar los datos de referencia

```bash
# ESCO completo (≈13.500 competencias, ≈2.900 ocupaciones) desde su API oficial
docker compose exec ingesta python -m ingesta esco-api

# O*NET: descarga «O*NET Database» en formato texto desde https://www.onetcenter.org/database.html
# y copia «Occupation Data.txt» y «Related Occupations.txt» en data/raw/onet/
docker compose exec ingesta python -m ingesta onet

# Ofertas de InfoJobs (requiere credenciales en .env)
docker compose exec ingesta python -m ingesta infojobs --consulta "desarrollador" --paginas 2
```

Como alternativa a la API, ESCO también se puede cargar desde su descarga en CSV (español) colocada en `data/raw/esco/`: `python -m ingesta esco`.

### Tests y calidad

```bash
docker compose exec backend pytest
docker compose exec backend ruff check /srv
docker compose exec ingesta pytest
cd frontend && npm test
```

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
- Servidores dentro de la UE.

## Licencia y datos de terceros

Código bajo licencia Apache 2.0. Los datos de ESCO, O*NET, INE, Cedefop, EURES e InfoJobs **no** se incluyen en el repositorio y se usan según sus propias condiciones (ver [NOTICE](NOTICE)).
