# Fuentes de datos

| Fuente | Qué aporta | Acceso | Frecuencia | Estado |
|--------|-----------|--------|-----------|--------|
| ESCO (Comisión Europea) | Ocupaciones, competencias y relaciones en español | API REST (`esco-api`) o descarga CSV (`esco`) | Una vez por versión | Cargado (13.479 competencias, 2.938 ocupaciones, 113.656 relaciones) |
| O*NET 31.0 | Matriz de ocupaciones relacionadas (transiciones) | Descarga automática del zip oficial, CC BY 4.0 | Una vez por versión | Cargado (1.016 ocupaciones, 18.460 transiciones) |
| Correspondencia ESCO ↔ O*NET (v1, 2022) | Enlace entre ambas clasificaciones | Descarga automática del CSV oficial de ESCO | Una vez | Cargado (4.128 correspondencias; 2.549 ocupaciones ESCO enlazadas) |
| InfoJobs | Ofertas de empleo en España | API con registro de aplicación | Cada noche | Cliente implementado, falta probar con credenciales |
| EURES (incluye SEPE) | Ofertas europeas y del SEPE | Por confirmar | Cada noche | Pendiente de confirmar vía de acceso |
| INE | Salarios por ocupación (Encuesta de Estructura Salarial) | API JSON (Tempus) | Anual | Pendiente |
| Cedefop | Indicadores de competencias y demanda | Descarga | Anual | Pendiente |
| Usuario | CV, perfil de LinkedIn en PDF, entrevistas | Subida en la aplicación | Al usarla | Pendiente |

## Restricciones

- **LinkedIn**: no se extraen datos de forma automatizada porque sus condiciones de uso lo prohíben. Solo se usa el PDF que descarga el propio usuario y el texto de ofertas que el usuario pega.
- Los datos descargados no se suben al repositorio: se guardan en `data/raw/`, que está excluido.
- Los experimentos de evaluación se ejecutan sobre una copia congelada de los datos en `data/snapshots/`.
