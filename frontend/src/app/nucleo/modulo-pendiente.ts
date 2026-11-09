// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, input } from '@angular/core';

/** Tarjeta que describe un módulo aún en desarrollo y lo que hará. */
@Component({
  selector: 'app-modulo-pendiente',
  template: `
    <h1>{{ icono() }} {{ titulo() }}</h1>
    <p class="suave">{{ descripcion() }}</p>
    <section class="tarjeta">
      <span class="etiqueta">En desarrollo · {{ iteracion() }}</span>
      <h3>Funcionalidades previstas</h3>
      <ul>
        @for (f of funcionalidades(); track f) {
          <li>{{ f }}</li>
        }
      </ul>
      <h3>Datos que utiliza</h3>
      <p class="suave">{{ datos() }}</p>
    </section>
  `,
})
export class ModuloPendiente {
  readonly icono = input.required<string>();
  readonly titulo = input.required<string>();
  readonly descripcion = input.required<string>();
  readonly iteracion = input.required<string>();
  readonly funcionalidades = input.required<string[]>();
  readonly datos = input.required<string>();
}
