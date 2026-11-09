# 0001 · Stack tecnológico

- **Estado**: aceptada
- **Fecha**: 2026-11-09

## Contexto

La aplicación combina procesamiento de datos, modelos de lenguaje y una interfaz rica (diagramas de Sankey, entrevistas por voz). Debe desplegarse en un servidor de la UE con recursos modestos y ser reproducible para la evaluación.

## Decisión

- **Frontend**: Angular, por experiencia profesional previa y por su estructura adecuada para una aplicación con varios módulos.
- **Backend e ingesta**: Python con FastAPI, por su ecosistema de datos e IA y la documentación automática de la API (OpenAPI).
- **Base de datos**: PostgreSQL con pgvector para combinar datos relacionales y búsqueda semántica en un solo sistema.
- **Modelos de lenguaje**: acceso por API con formato compatible con OpenAI, con proveedor configurable.
- **Despliegue**: Docker Compose, con un servicio por responsabilidad y Caddy para HTTPS.
- **Estructura**: monorepositorio con un paquete compartido (`core`) para el modelo de datos.

## Consecuencias

- Un único `docker compose up` levanta el sistema completo.
- Cambiar de proveedor de LLM no requiere cambios de código.
- La dimensión de los embeddings (1024) queda fijada en el esquema; cambiar a un modelo con otra dimensión exige una migración.
