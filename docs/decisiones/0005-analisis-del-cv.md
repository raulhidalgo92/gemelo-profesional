# 0005 · Análisis del currículum

- **Estado**: aceptada
- **Fecha**: 2026-11-20

## Contexto

El gemelo se construye a partir del currículum del usuario. Hay que convertir un PDF o un Word en competencias ESCO declaradas, con una explicación de cada una, cumpliendo los compromisos de la propuesta: minimización (el archivo no se guarda) y seudonimización antes de usar un modelo de lenguaje.

## Decisión

1. **Lectura en memoria**: el endpoint de análisis lee el archivo (máximo 5 MB) y reconoce el formato por su contenido, no por la extensión: PDF con `pypdf` y Word (.docx) con `python-docx`, incluidas las tablas. El archivo no se escribe en disco ni en la base de datos. Si el texto es casi nulo (por ejemplo, un PDF escaneado como imagen) se pide otro formato.
2. **Seudonimización**: antes del modelo se sustituyen correo, teléfono, DNI/NIE, perfil de LinkedIn y nombres por marcadores. Además del nombre de la cuenta, se oculta la cabecera del CV cuando parece un nombre completo (de 2 a 5 palabras, sin cifras ni arrobas).
3. **Extracción**: el mismo procedimiento en tres pasos que las ofertas ([decisión 0003](0003-extraccion-competencias.md)), con un prompt propio para currículums (`prompts/extraccion_competencias_cv.md`) que pide también las competencias que se deducen de las funciones, ignora los marcadores y admite hasta 30 términos.
4. **Almacenamiento**: cada competencia se guarda en `gemelo_competencia` como declarada (`nivel_declarado = 0,5`) y con una `evidencia` de origen `cv` cuyo fragmento es el término del CV. Los fragmentos no se revierten a los datos originales, para que nunca vuelvan datos personales a la base de datos. Un CV nuevo sustituye al anterior, pero se conserva lo demostrado en entrevistas.
5. **Revisión**: el asistente de bienvenida muestra las competencias con su origen («En tu CV: «Excel avanzado»») y el usuario puede quitar las que no le representen (`DELETE /api/gemelo/competencias?uri=`).

## Actualización (24-11-2026): trayectoria y revisión de cambios

- **Trayectoria**: además de las competencias, el modelo extrae del texto seudonimizado un resumen del perfil, los puestos (cargo, sector y años), la formación (titulación y años) y el nivel de inglés MCER si consta (`prompts/trayectoria_cv.md`, `gemelo_core/trayectoria.py`). Por minimización no se guardan nombres de empresas ni de centros, y se eliminan de la respuesta los marcadores de datos ocultados que el modelo pudiera copiar. Se guarda en `gemelo.trayectoria` (JSONB) y `gemelo.nivel_ingles`.
- **Dos pasos**: `POST /api/gemelo/cv/analizar` lee el CV y devuelve los cambios sin guardar nada (trayectoria, competencias con marca de nuevas y competencias que solo venían del CV anterior y el nuevo ya no trae). `POST /api/gemelo/cv/aplicar` guarda lo que el usuario confirma. Así, al actualizar el CV, nada desaparece sin que el usuario lo vea.
- **Qué se sustituye**: la trayectoria se reemplaza por la del CV nuevo. De las competencias, nunca se tocan las demostradas ni las que tengan otra evidencia (por ejemplo, añadidas a mano); las que solo venían del CV anterior se quitan salvo que el usuario pida conservarlas. Las conservadas pasan a tener una evidencia de origen `conservada` (con el mismo término del CV) y no se vuelve a preguntar por ellas: como el modelo no siempre asocia un mismo término a la misma competencia ESCO, sin esto el usuario tendría que confirmar las mismas competencias en cada actualización. Las URI que no existen en ESCO se ignoran.
- **Primer CV**: no hay nada que comparar, así que la bienvenida analiza y aplica todo directamente y después el usuario revisa las competencias.
- **Coste**: una llamada más al modelo ligero por CV.
- **Corrección manual** (panel «Ver todas»): el usuario puede añadir competencias del catálogo ESCO que su CV no recogía (`POST /api/gemelo/competencias`, evidencia de origen `manual`), y un CV nuevo no las quita. Al quitar una competencia se ofrece «Deshacer» durante seis segundos y el borrado solo se envía al servidor cuando ya no se puede deshacer, de modo que deshacer conserva su evidencia original.

## Primera prueba (CV sintético de administrativa contable, 20-11-2026)

15 competencias en unos 4 segundos, todas razonables; por ejemplo, «Excel avanzado → utilizar software de hojas de cálculo», «Conciliación bancaria → llevar registro de transacciones financieras», «SAP → gestionar sistemas estándar de planificación de recursos empresariales». No se asoció «valenciano», que habrá que revisar en la evaluación con el conjunto etiquetado.

## Consecuencias

- El análisis es síncrono (unos segundos); la interfaz muestra las fases del proceso mientras tanto.
- La seudonimización por patrones no detecta todos los nombres (por ejemplo, de referencias o empresas pequeñas); su cobertura se medirá en la evaluación.
