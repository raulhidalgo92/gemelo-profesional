# 0003 · Extracción de competencias ESCO de las ofertas

- **Estado**: aceptada
- **Fecha**: 2026-11-13

## Contexto

Para calcular el encaje entre el gemelo y una oferta, y para saber qué competencias pide el mercado, cada oferta debe expresarse como un conjunto de competencias ESCO. Las ofertas están en texto libre, en español o en catalán, y con redacciones muy variadas («domini d'Excel», «manejo de hojas de cálculo»).

Requisitos: asociar siempre a un concepto ESCO existente (nunca inventar competencias), coste bajo para procesar miles de ofertas y poder explicar al usuario por qué se detectó cada competencia.

## Alternativas consideradas

| Alternativa | Inconveniente |
|---|---|
| Pedir al modelo de lenguaje la URI ESCO directamente | Inventa URI o títulos que no existen |
| Términos del modelo + competencia ESCO más parecida por embeddings con un umbral | Las similitudes de parejas correctas e incorrectas se solapan (ver calibración) |
| Clasificador entrenado (por ejemplo, ESCOXLM-R) | Requiere datos etiquetados y GPU; queda como comparación para la evaluación |
| **Términos del modelo + candidatas por embeddings + elección por el modelo** | Una llamada más al modelo por oferta |

## Decisión

Procedimiento en tres pasos, en la línea de Clavié y Soulié (2023), implementado en `gemelo_core.extraccion`:

1. **Propuesta**: `gemini-3.1-flash-lite` lee la oferta y devuelve hasta 20 términos breves en español (prompt `prompts/extraccion_competencias.md`).
2. **Candidatas**: cada término se convierte en vector (`RETRIEVAL_QUERY`) y se recuperan las 5 competencias ESCO más cercanas con similitud ≥ 0,55.
3. **Elección**: el mismo modelo recibe el título de la oferta, los términos y sus candidatas numeradas, y elige la candidata correcta de cada término o ninguna (prompt `prompts/eleccion_competencias.md`).

Se guarda la competencia, la similitud y el término original (`oferta_competencia.termino`) para poder explicar el resultado.

La ocupación ESCO de la oferta sigue el mismo esquema: el modelo nombra el puesto en español a partir del título (prompt `prompts/puesto_oferta.md`), se recuperan las 5 ocupaciones ESCO más cercanas a ese nombre y el modelo elige una o ninguna (prompt `prompts/eleccion_ocupacion.md`).

## Calibración (20 ofertas reales, 13-11-2026)

- Solo con umbral: las similitudes de los 175 términos estaban entre 0,63 y 0,79. Parejas correctas como «español → español» (0,68) o «contabilidad mercantil → contabilidad» (0,69) quedaban por debajo de parejas erróneas como «comunicación de incidencias → informar sobre incidencias en el casino» (0,75). Ningún umbral separaba bien ambos grupos.
- Con el paso de elección: el modelo descarta esas parejas erróneas y acepta las correctas («castellano → español», «Excel → utilizar software de hojas de cálculo»). En 17 ofertas se aceptaron 110 de 123 términos.
- Consumo medido: unos 1.200 tokens de entrada y 250 de salida por oferta.

La precisión y la cobertura se medirán con un conjunto de ofertas etiquetado a mano en la fase de evaluación, comparando al menos esta configuración con la de solo umbral.

## Resultado de la carga inicial (13-11-2026)

- 5.761 de 5.784 ofertas procesadas; 23 quedaron pendientes por límites de uso de la API (429) y se reintentan en la siguiente ejecución.
- 49.631 competencias: 9,5 por oferta en Feina Activa y 3,5 en el ECyL, cuyos textos son más cortos.
- Consumo real: 8,07 M tokens de entrada y 1,89 M de salida (unos 4,90 $).
- Con la primera versión (ocupación más parecida al título, similitud ≥ 0,7) solo se estimó la ocupación del 19 % de las ofertas de Feina Activa (75 % en el ECyL): los títulos en catalán quedan lejos de las ocupaciones en español («FUSTERS/ES» quedaba más cerca de «cartero» que de «carpintero»).

## Ocupación de las ofertas (13-11-2026)

Con el paso previo de nombrar el puesto en español y la elección entre candidatas:

- Muestra de 24 títulos al azar: 23 con una ocupación correcta o razonable; el restante mezcla dos puestos («XOFER/XOFERA + OPERARI/ÀRIA TALLER») y queda sin ocupación.
- Cobertura: 93 % en Feina Activa y 96 % en el ECyL. Las que quedan sin ocupación son títulos genéricos («Empleo privado en otras Comunidades Autónomas») o fallos por límites de la API, que se pueden repetir con `ocupaciones-ofertas --solo-sin-ocupacion`.
- Consumo: unos 450 tokens de entrada por oferta; 2,64 M de entrada y 0,11 M de salida para todas (unos 0,80 $).

## Consecuencias

- Coste medido de unos 0,001 $ por oferta, ocupación incluida: como mucho unos 0,25 $ al día con el límite `EXTRACCION_MAX_OFERTAS` (300 ofertas nuevas por noche).
- La misma función (`extraer_competencias`) servirá para analizar una oferta pegada por el usuario.
- Los tokens consumidos se registran en cada ejecución (`ClienteIA.uso`) para documentar el coste real.
