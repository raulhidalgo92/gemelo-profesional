// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';

import { ModuloPendiente } from '../../nucleo/modulo-pendiente';

@Component({
  selector: 'app-entrenador',
  imports: [ModuloPendiente],
  template: `<app-modulo-pendiente
    icono="🎤"
    titulo="Entrenador"
    descripcion="Entrevista simulada para una oferta concreta, por texto o voz, y estimación del nivel de inglés."
    iteracion="iteración 3"
    [funcionalidades]="[
      'Preguntas generadas a partir de la oferta y del gemelo',
      'Evaluación de cada respuesta (método STAR) con explicación',
      'Las respuestas se guardan como evidencia: competencia declarada → demostrada',
      'Estimación del nivel de inglés (MCER)',
    ]"
    datos="Transcripción de la entrevista (el audio se descarta) y competencias de la oferta."
  />`,
})
export class EntrenadorPagina {}
