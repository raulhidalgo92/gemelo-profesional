// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, computed, input } from '@angular/core';

const ETIQUETAS = ['Muy débil', 'Débil', 'Aceptable', 'Buena', 'Muy buena'];
const COLORES = ['bg-error', 'bg-error', 'bg-amber-500', 'bg-ok', 'bg-ok'];

/** Puntuación orientativa de 0 a 4: longitud y variedad de caracteres. */
export function fortaleza(clave: string): number {
  if (clave.length < 10) return clave.length ? 0 : -1;
  const variedad = [/[a-z]/, /[A-Z]/, /\d/, /[^\w\s]/].filter((r) => r.test(clave)).length;
  return Math.min(4, 1 + (clave.length >= 14 ? 1 : 0) + Math.max(0, variedad - 1));
}

/** Barra de fortaleza de la contraseña. */
@Component({
  selector: 'app-fortaleza',
  template: `
    @if (nivel() >= 0) {
      <div class="mt-2 flex items-center gap-3" aria-live="polite">
        <div class="flex flex-1 gap-1">
          @for (i of [0, 1, 2, 3]; track i) {
            <span
              class="h-1 flex-1 rounded-full transition-colors duration-300"
              [class]="i < Math.max(1, nivel()) ? color() : 'bg-borde'"
            ></span>
          }
        </div>
        <span class="w-20 text-right text-xs text-tinta-tenue">{{ etiqueta() }}</span>
      </div>
    }
  `,
})
export class Fortaleza {
  readonly clave = input('');
  protected readonly Math = Math;
  protected readonly nivel = computed(() => fortaleza(this.clave()));
  protected readonly etiqueta = computed(() => ETIQUETAS[Math.max(0, this.nivel())]);
  protected readonly color = computed(() => COLORES[Math.max(0, this.nivel())]);
}
