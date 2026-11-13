# Planificación

Desarrollo iterativo e incremental: cada iteración entrega una parte del sistema que funciona de principio a fin.

| Iteración | Contenido | Resultado visible |
|-----------|-----------|-------------------|
| 0 · Base | Infraestructura, esqueleto dockerizado, modelo de datos, ingesta ESCO y O*NET | Buscador de competencias ESCO |
| 1 · Gemelo | Registro con consentimiento, subida de CV/LinkedIn, extracción y normalización a ESCO | Perfil con competencias declaradas |
| 2 · Empleo | Ingesta nocturna de ofertas, extracción de competencias, encaje explicado, oferta pegada | Lista de ofertas con % de encaje |
| 3 · Formarte y Entrenador | Priorización de competencias por ofertas que abren; entrevista por texto y voz; nivel de inglés; evidencias | Competencias demostradas |
| 4 · Mi futuro | Transiciones O*NET ↔ ESCO, Sankey, ruta paso a paso, recálculo | Diagrama de trayectorias |
| 5 · Evaluación | Conjunto etiquetado, métricas, acuerdo con evaluadores humanos, piloto con usuarios (SUS) | Resultados para la memoria |

## Primera entrega de la memoria

Contenido exigido: contexto, estado del arte con bibliografía y objetivos.

| Semana | Memoria | Software |
|--------|---------|----------|
| 9–15 nov | Estructura en la plantilla, búsqueda bibliográfica | Iteración 0 |
| 16–22 nov | Contexto: mercado laboral, competencias, clasificaciones (ESCO, O*NET) | Ingesta de ofertas abiertas (SOC, ECyL), prototipo de extracción con LLM |
| 23–29 nov | Estado del arte: recomendadores de empleo, LLM y ESCO, simuladores de entrevista, trayectorias | Iteración 1 (inicio) |
| 30 nov–6 dic | Objetivos SMART y metodología, revisión de citas APA | Iteración 1 (cierre) |
