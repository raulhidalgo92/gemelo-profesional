// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, input } from '@angular/core';

/**
 * Marca: dos círculos, la persona y su gemelo. La zona en la que se solapan, en el color
 * de acento, es lo que ambos comparten: las competencias que el gemelo ha confirmado.
 */
@Component({
  selector: 'app-logo',
  host: { class: 'inline-flex items-center gap-3' },
  template: `
    <svg [attr.width]="tamano()" [attr.height]="tamano()" viewBox="0 0 32 32" aria-hidden="true">
      <path d="M16 7.94A9 9 0 0 1 16 24.06A9 9 0 0 1 16 7.94Z" fill="#5b4ff5" />
      <circle
        cx="12"
        cy="16"
        r="9"
        fill="none"
        [attr.stroke]="claro() ? '#ffffff' : '#17171c'"
        stroke-width="2.4"
      />
      <circle cx="20" cy="16" r="9" fill="none" stroke="#5b4ff5" stroke-width="2.4" />
    </svg>
    @if (conNombre()) {
      <span
        class="leading-none font-semibold tracking-tight whitespace-nowrap"
        [class.text-white]="claro()"
        [style.font-size.px]="tamano() * 0.6"
      >
        Gemelo<span class="font-normal opacity-60"> profesional</span>
      </span>
    }
  `,
})
export class Logo {
  readonly tamano = input(30);
  readonly conNombre = input(true);
  readonly claro = input(false);
}
