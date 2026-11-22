// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';

import { ModuloPendiente } from '../../nucleo/modulo-pendiente';

@Component({
  selector: 'app-formacion',
  imports: [ModuloPendiente],
  template: `<app-modulo-pendiente
    titulo="Formarte"
    descripcion="Qué aprender primero y cuántas ofertas te abre cada competencia."
    [funcionalidades]="[
      'Ranking de competencias por número de ofertas que desbloquean',
      'Impacto estimado en salario y en trayectorias alcanzables',
      'Explicación de cada recomendación',
    ]"
    datos="Ofertas por competencia, catálogo de formación del SEPE y salarios del INE."
  />`,
})
export class FormacionPagina {}
