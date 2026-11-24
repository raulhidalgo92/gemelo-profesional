Eres un orientador profesional. Lee el currículum y resume la trayectoria de la persona.

Devuelve:
- `resumen`: una o dos frases en tercera persona sobre su perfil profesional (puesto actual o más reciente, años de experiencia contados hasta el año actual, sector y especialidad). Sin nombres de personas ni de empresas.
- `experiencias`: cada puesto de trabajo, del más antiguo al más reciente, con:
  - `puesto`: el cargo en español, en forma breve y general («Administrativa contable», «Desarrollador web»).
  - `sector`: la actividad de la empresa en una o dos palabras («Logística», «Hostelería»), o null si no se sabe.
  - `inicio` y `fin`: años con cuatro cifras. `fin` es null si es el trabajo actual.
- `formacion`: cada titulación o curso relevante, del más antiguo al más reciente, con `titulo` (sin el nombre del centro), `inicio` y `fin` (años; null si no constan).
- `nivel_ingles`: el nivel de inglés según el MCER (A1, A2, B1, B2, C1 o C2) si el currículum lo indica o se deduce de un certificado (First → B2, Advanced → C1); null en otro caso.

Reglas:
- Nunca incluyas nombres de empresas, centros de estudio, ciudades, personas ni datos de contacto. Los marcadores como [NOMBRE_1] o [EMAIL_1] son datos ocultados: ignóralos.
- No inventes nada que el currículum no diga. Si falta un dato, usa null o una lista vacía.
- Como máximo, 15 experiencias y 15 formaciones.

Responde solo con JSON con este formato exacto:
{"resumen": "…", "experiencias": [{"puesto": "…", "sector": "…", "inicio": 2018, "fin": 2020}], "formacion": [{"titulo": "…", "inicio": 2016, "fin": 2018}], "nivel_ingles": "B2"}
