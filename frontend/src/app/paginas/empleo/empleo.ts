// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';

import { ModuloPendiente } from '../../nucleo/modulo-pendiente';

@Component({
  selector: 'app-empleo',
  imports: [ModuloPendiente],
  template: `<app-modulo-pendiente
    icono="🔎"
    titulo="Empleo"
    descripcion="Ofertas reales con el porcentaje de encaje y la explicación de en qué se basa."
    iteracion="iteración 2"
    [funcionalidades]="[
      'Buscador de ofertas de EURES e InfoJobs actualizado cada noche',
      'Porcentaje de encaje con competencias que cumples y que te faltan',
      'Analizar una oferta pegada por el usuario (LinkedIn u otra web)',
    ]"
    datos="Ofertas normalizadas a competencias ESCO y competencias del gemelo."
  />`,
})
export class EmpleoPagina {}
