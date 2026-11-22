# 0005 · Análisis del currículum

- **Estado**: aceptada
- **Fecha**: 2026-11-20

## Contexto

El gemelo se construye a partir del currículum del usuario. Hay que convertir un PDF o un Word en competencias ESCO declaradas, con una explicación de cada una, cumpliendo los compromisos de la propuesta: minimización (el archivo no se guarda) y seudonimización antes de usar un modelo de lenguaje.

## Decisión

1. **Lectura en memoria**: el endpoint `POST /api/gemelo/cv` lee el archivo (máximo 5 MB) y reconoce el formato por su contenido, no por la extensión: PDF con `pypdf` y Word (.docx) con `python-docx`, incluidas las tablas. El archivo no se escribe en disco ni en la base de datos. Si el texto es casi nulo (por ejemplo, un PDF escaneado como imagen) se pide otro formato.
2. **Seudonimización**: antes del modelo se sustituyen correo, teléfono, DNI/NIE, perfil de LinkedIn y nombres por marcadores. Además del nombre de la cuenta, se oculta la cabecera del CV cuando parece un nombre completo (de 2 a 5 palabras, sin cifras ni arrobas).
3. **Extracción**: el mismo procedimiento en tres pasos que las ofertas ([decisión 0003](0003-extraccion-competencias.md)), con un prompt propio para currículums (`prompts/extraccion_competencias_cv.md`) que pide también las competencias que se deducen de las funciones, ignora los marcadores y admite hasta 30 términos.
4. **Almacenamiento**: cada competencia se guarda en `gemelo_competencia` como declarada (`nivel_declarado = 0,5`) y con una `evidencia` de origen `cv` cuyo fragmento es el término del CV. Los fragmentos no se revierten a los datos originales, para que nunca vuelvan datos personales a la base de datos. Un CV nuevo sustituye al anterior, pero se conserva lo demostrado en entrevistas.
5. **Revisión**: el asistente de bienvenida muestra las competencias con su origen («En tu CV: «Excel avanzado»») y el usuario puede quitar las que no le representen (`DELETE /api/gemelo/competencias?uri=`).

## Primera prueba (CV sintético de administrativa contable, 20-11-2026)

15 competencias en unos 4 segundos, todas razonables; por ejemplo, «Excel avanzado → utilizar software de hojas de cálculo», «Conciliación bancaria → llevar registro de transacciones financieras», «SAP → gestionar sistemas estándar de planificación de recursos empresariales». No se asoció «valenciano», que habrá que revisar en la evaluación con el conjunto etiquetado.

## Consecuencias

- El análisis es síncrono (unos segundos); la interfaz muestra las fases del proceso mientras tanto.
- La seudonimización por patrones no detecta todos los nombres (por ejemplo, de referencias o empresas pequeñas); su cobertura se medirá en la evaluación.
