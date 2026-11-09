# 0002 · Proveedor de modelos de lenguaje y embeddings

- **Estado**: aceptada
- **Fecha**: 2026-11-09

## Contexto

El sistema necesita un modelo de lenguaje para extraer competencias de currículums y ofertas, conducir y evaluar entrevistas y redactar explicaciones, y un modelo de embeddings para la búsqueda semántica sobre ESCO. Requisitos:

- Tratamiento de datos personales conforme al RGPD, con procesamiento dentro de la UE, tal y como se indica en la propuesta.
- Buena calidad en español y salida estructurada (JSON).
- Coste mínimo durante el desarrollo y el piloto.
- Posibilidad de comparar varios modelos en la evaluación.

## Alternativas consideradas

| Alternativa | Ventajas | Inconvenientes |
|---|---|---|
| Mistral (API propia) | Empresa europea, precio bajo | Condiciones de acceso para particulares poco claras |
| Gemini API (AI Studio) | Configuración mínima, API compatible con OpenAI | Sin garantía de procesamiento en la UE; saldo prepago independiente de los créditos de Google Cloud |
| **Gemini en Vertex AI** | Región europea, contrato de encargado del tratamiento, se factura con la cuenta de Google Cloud | Configuración inicial con cuenta de servicio |
| Modelos abiertos en local | Sin coste por uso, datos en el propio servidor | Demasiado lentos en un servidor modesto para las entrevistas |

## Decisión

Usar **Gemini en Vertex AI** con ubicaciones europeas: la multirregión `eu` para los modelos Gemini y `europe-west1` (Bélgica) para los embeddings, que no se sirven en la multirregión:

- `gemini-3.8-flash` como modelo principal (entrevistas y explicaciones).
- `gemini-3.1-flash-lite` como modelo ligero (extracción de competencias).
- `gemini-embedding-001` con la salida reducida a 1024 dimensiones para los embeddings.

El acceso se encapsula en la interfaz `ClienteIA` (`core/src/gemelo_core/ia.py`), con una implementación para Vertex AI y otra para cualquier API compatible con OpenAI. El proveedor se elige con la variable `LLM_PROVEEDOR`.

## Consecuencias

- Los datos se procesan en la UE y se seudonimizan antes de enviarse al modelo.
- La clave de la cuenta de servicio se guarda en `secretos/`, que no se versiona.
- Cambiar de proveedor o comparar modelos en la evaluación solo requiere cambiar la configuración.
- Si en el futuro se usa un modelo de embeddings de otra dimensión, hay que recalcular los vectores y migrar el esquema.
