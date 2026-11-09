// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component } from '@angular/core';

import { ModuloPendiente } from '../../nucleo/modulo-pendiente';

@Component({
  selector: 'app-futuro',
  imports: [ModuloPendiente],
  template: `<app-modulo-pendiente
    icono="🧭"
    titulo="Mi futuro"
    descripcion="Explorador de trayectorias: de dónde vienes, a dónde puedes ir y qué te falta para llegar."
    iteracion="iteración 4"
    [funcionalidades]="[
      'Diagrama de Sankey con la trayectoria pasada y los destinos posibles',
      'Ruta paso a paso hacia el destino elegido: competencias que faltan, formación y nivel de idioma',
      'Recálculo automático cuando el gemelo cambia',
    ]"
    datos="Matriz de ocupaciones relacionadas de O*NET enlazada con ESCO, salarios del INE y demanda de ofertas."
  />`,
})
export class FuturoPagina {}
