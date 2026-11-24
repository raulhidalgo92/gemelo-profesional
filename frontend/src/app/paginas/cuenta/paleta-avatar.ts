// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, input, output } from '@angular/core';

import { Avatar, AVATARES } from '../../nucleo/ui/avatar';

const NOMBRES: Record<string, string> = {
  gemelo: 'Gemelo',
  lila: 'Lila',
  montana: 'Montaña',
  sol: 'Sol',
  ola: 'Ola',
  luna: 'Luna',
  rombo: 'Rombo',
  brote: 'Brote',
};

/** Colección de avatares para elegir: la inicial y las ilustraciones de la app. */
@Component({
  selector: 'app-paleta-avatar',
  imports: [Avatar],
  host: { role: 'group', 'aria-label': 'Elige un avatar' },
  template: `
    <p class="mb-2.5 text-[13px] font-medium text-tinta-suave">Elige un avatar</p>
    <div class="grid grid-cols-3 gap-2">
      @for (a of opciones; track $index) {
        <button
          type="button"
          class="opcion"
          [class.elegida]="a === avatar()"
          [attr.aria-pressed]="a === avatar()"
          [attr.aria-label]="nombreDe(a)"
          [title]="nombreDe(a)"
          (click)="elegido.emit(a)"
        >
          <app-avatar [nombre]="nombre()" [avatar]="a" [tamano]="44" />
        </button>
      }
    </div>
  `,
  styles: `
    :host {
      display: block;
      width: max-content;
      padding: 14px;
      border: 1px solid var(--color-borde);
      border-radius: 16px;
      background: var(--color-superficie);
      box-shadow: 0 18px 40px -18px rgb(23 23 28 / 35%);
    }
    .opcion {
      display: block;
      padding: 3px;
      border-radius: 50%;
      transition:
        box-shadow 0.15s ease,
        transform 0.15s ease;
    }
    .opcion:hover {
      transform: scale(1.06);
    }
    .opcion:focus-visible {
      outline: none;
      box-shadow: 0 0 0 3px rgb(91 79 245 / 25%);
    }
    .opcion.elegida {
      box-shadow: 0 0 0 2px var(--color-acento);
    }
  `,
})
export class PaletaAvatar {
  readonly nombre = input('');
  readonly avatar = input<string | null>(null);
  readonly elegido = output<string | null>();

  /** La inicial (null) y los avatares de la colección */
  protected readonly opciones: (string | null)[] = [null, ...AVATARES];

  protected nombreDe(a: string | null): string {
    return a ? NOMBRES[a] : 'Tu inicial';
  }
}
