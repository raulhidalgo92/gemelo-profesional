# Fuentes de datos

| Fuente | Qué aporta | Acceso | Frecuencia | Estado |
|--------|-----------|--------|-----------|--------|
| ESCO (Comisión Europea) | Ocupaciones, competencias y relaciones en español | API REST (`esco-api`) o descarga CSV (`esco`) | Una vez por versión | Cargado (13.479 competencias, 2.938 ocupaciones, 113.656 relaciones) |
| O*NET 31.0 | Matriz de ocupaciones relacionadas (transiciones) | Descarga automática del zip oficial, CC BY 4.0 | Una vez por versión | Cargado (1.016 ocupaciones, 18.460 transiciones) |
| Correspondencia ESCO ↔ O*NET (v1, 2022) | Enlace entre ambas clasificaciones | Descarga automática del CSV oficial de ESCO | Una vez | Cargado (4.128 correspondencias; 2.549 ocupaciones ESCO enlazadas) |
| Feina Activa (SOC, Generalitat de Catalunya) | Ofertas vigentes en Cataluña con texto completo y salario | XML abierto, sin registro (`ofertas`) | Cada noche | Cargado (≈4.900 ofertas) |
| Ofertas de empleo del ECyL (Junta de Castilla y León) | Ofertas vigentes en Castilla y León, CC BY 4.0 | JSON abierto, sin registro (`ofertas`) | Cada noche | Cargado (≈920 ofertas) |
| InfoJobs | Ofertas de empleo en España | API con registro de aplicación | — | Registro de aplicaciones cerrado; cliente implementado sin credenciales |
| Empléate (SEPE) | Ofertas públicas y privadas de toda España | Sin datos abiertos | — | Solicitada su publicación en datos.gob.es (Ley 37/2007), asignada al SEPE |
| EURES | Ofertas europeas | Sin API pública documentada | — | Sin vía de acceso autorizada |
| INE | Ganancia bruta anual por ocupación CNO-11: percentiles por subgrupo (Encuesta Cuatrienal 2022) y media por gran grupo 2015-2024 (Encuesta Anual) | API JSON pública (Tempus), sin registro (`ine`) | Anual | Cargado (608 datos; 98,7 % de las ocupaciones ESCO con salario de su subgrupo) |
| Correspondencia CNO-11 ↔ CIUO-08 (INE) | Enlace entre la clasificación española de ocupaciones y la ISCO-08 que usa ESCO | Descarga automática del XLS oficial | Una vez | Cargado (541 correspondencias) |
| Catálogo de Especialidades Formativas (SEPE) | 7.544 especialidades y 151 itinerarios oficiales, con sus ocupaciones relacionadas (CNO-11) | Exportación a Excel desde el buscador oficial del SEPE (`sepe-formacion`) | Al cambiar el catálogo | Cargado (exportación del 13-11-2026) |
| Cursos del SOC (Generalitat de Catalunya) | Cursos programados de formación ocupacional y continua | JSON abierto, sin registro (`ofertas`) | Cada noche | Cargado (≈390 cursos) |
| Cedefop | Indicadores de competencias y demanda | Descarga | Anual | Pendiente |
| Usuario | CV, perfil de LinkedIn en PDF, entrevistas | Subida en la aplicación | Al usarla | Pendiente |

## Salarios del INE

Cada ocupación ESCO tiene un código ISCO-08 de 4 dígitos. Con la correspondencia oficial del INE se obtienen sus códigos CNO-11 y, de ellos, el subgrupo principal (2 dígitos), que es el nivel más detallado con percentiles publicados. Si un código ISCO corresponde a varios subgrupos se elige el más frecuente que tenga datos; si ninguno los tiene, el gran grupo (letra). Solo se cargan datos de ambos sexos y del total nacional.

El INE no publica cifras con menos de 100 observaciones y marca con un signo negativo las que tienen entre 100 y 500. Estas se guardan en positivo con `precision_baja = true` para que la interfaz las muestre como orientativas.

Endpoint: `GET /api/mercado/salarios?ocupacion=<URI ESCO>`.

## Ofertas de empleo

No existe una fuente nacional de ofertas abierta y oficial, así que se usan los conjuntos de datos abiertos de servicios públicos de empleo autonómicos. Cada fuente es un módulo de `ingesta/src/ingesta/fuentes/` que normaliza al esquema común `oferta`; añadir otra comunidad (o el SEPE, si publica sus datos) no afecta al resto.

En cada carga nocturna:

- Se eliminan del texto emails, teléfonos, documentos de identidad y nombres de contacto (`gemelo_core.seudonimizacion.eliminar_datos_contacto`). Son datos de terceros que el sistema no necesita.
- Se guarda la fuente, el enlace a la oferta original y la fecha de publicación, como exigen las licencias.
- Se borran las ofertas que ya no aparecen en la fuente: solo se conservan las vigentes.
- Feina Activa no indica el periodo del salario; las cifras inferiores a 6.000 € se consideran mensuales (`salario_periodo`).

Además, el usuario puede pegar cualquier oferta para analizarla («pega la oferta»).

## Formación

El SEPE no publica su catálogo como datos abiertos (se ha solicitado en datos.gob.es), pero su buscador oficial permite exportarlo y su aviso legal autoriza la reutilización citando «Origen de los datos: SEPE» y la fecha. Para actualizarlo:

1. Entrar en el [buscador del catálogo](https://sede.sepe.gob.es/FOET_CATALOGO_EEFF_SEDE/flows/main), pestaña ESPECIALIDADES, sin filtros y con «Solo última versión».
2. Buscar, pulsar «Exportar» y marcar «Ocupaciones relacionadas» y «Duración total de la parte presencial».
3. Repetir en la pestaña ITINERARIOS.
4. Guardar los ficheros en `data/raw/sepe/` como `especialidades-formativas-AAAAMMDD.xlsx` e `itinerarios-formativos-AAAAMMDD.xlsx` y ejecutar `python -m ingesta sepe-formacion` (usa el más reciente).

Cada especialidad declara sus ocupaciones con un código de 8 dígitos cuyos 4 primeros son la CNO-11. Con la correspondencia CNO-11 ↔ ISCO-08 del INE se enlaza con las ocupaciones ESCO sin necesidad de IA: el 93,9 % de las ocupaciones ESCO tiene formación oficial relacionada.

Endpoint: `GET /api/formacion/especialidades?ocupacion=<URI ESCO>`, con el motivo de cada recomendación.

## Restricciones

- **LinkedIn**: no se extraen datos de forma automatizada porque sus condiciones de uso lo prohíben. Solo se usa el PDF que descarga el propio usuario y el texto de ofertas que el usuario pega.
- Los datos descargados no se suben al repositorio: se guardan en `data/raw/`, que está excluido.
- Los experimentos de evaluación se ejecutan sobre una copia congelada de los datos en `data/snapshots/`.
