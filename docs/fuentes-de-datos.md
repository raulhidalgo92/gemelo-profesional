# Fuentes de datos

| Fuente | Qué aporta | Acceso | Frecuencia | Estado |
|--------|-----------|--------|-----------|--------|
| ESCO (Comisión Europea) | Ocupaciones, competencias y relaciones en español | API REST (`esco-api`) o descarga CSV (`esco`) | Una vez por versión | Cargado (13.479 competencias, 2.938 ocupaciones, 113.656 relaciones) |
| O*NET 31.0 | Matriz de ocupaciones relacionadas (transiciones) | Descarga automática del zip oficial, CC BY 4.0 | Una vez por versión | Cargado (1.016 ocupaciones, 18.460 transiciones) |
| Correspondencia ESCO ↔ O*NET (v1, 2022) | Enlace entre ambas clasificaciones | Descarga automática del CSV oficial de ESCO | Una vez | Cargado (4.128 correspondencias; 2.549 ocupaciones ESCO enlazadas) |
| InfoJobs | Ofertas de empleo en España | API con registro de aplicación | Cada noche | Cliente implementado, falta probar con credenciales |
| EURES (incluye SEPE) | Ofertas europeas y del SEPE | Por confirmar | Cada noche | Pendiente de confirmar vía de acceso |
| INE | Ganancia bruta anual por ocupación CNO-11: percentiles por subgrupo (Encuesta Cuatrienal 2022) y media por gran grupo 2015-2024 (Encuesta Anual) | API JSON pública (Tempus), sin registro (`ine`) | Anual | Cargado (608 datos; 98,7 % de las ocupaciones ESCO con salario de su subgrupo) |
| Correspondencia CNO-11 ↔ CIUO-08 (INE) | Enlace entre la clasificación española de ocupaciones y la ISCO-08 que usa ESCO | Descarga automática del XLS oficial | Una vez | Cargado (541 correspondencias) |
| Cedefop | Indicadores de competencias y demanda | Descarga | Anual | Pendiente |
| Usuario | CV, perfil de LinkedIn en PDF, entrevistas | Subida en la aplicación | Al usarla | Pendiente |

## Salarios del INE

Cada ocupación ESCO tiene un código ISCO-08 de 4 dígitos. Con la correspondencia oficial del INE se obtienen sus códigos CNO-11 y, de ellos, el subgrupo principal (2 dígitos), que es el nivel más detallado con percentiles publicados. Si un código ISCO corresponde a varios subgrupos se elige el más frecuente que tenga datos; si ninguno los tiene, el gran grupo (letra). Solo se cargan datos de ambos sexos y del total nacional.

El INE no publica cifras con menos de 100 observaciones y marca con un signo negativo las que tienen entre 100 y 500. Estas se guardan en positivo con `precision_baja = true` para que la interfaz las muestre como orientativas.

Endpoint: `GET /api/mercado/salarios?ocupacion=<URI ESCO>`.

## Restricciones

- **LinkedIn**: no se extraen datos de forma automatizada porque sus condiciones de uso lo prohíben. Solo se usa el PDF que descarga el propio usuario y el texto de ofertas que el usuario pega.
- Los datos descargados no se suben al repositorio: se guardan en `data/raw/`, que está excluido.
- Los experimentos de evaluación se ejecutan sobre una copia congelada de los datos en `data/snapshots/`.
