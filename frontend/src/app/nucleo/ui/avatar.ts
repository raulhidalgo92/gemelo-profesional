// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, computed, input } from '@angular/core';

/** Avatares de la colección de la app, en el mismo orden en que se ofrecen. */
export const AVATARES = ['gemelo', 'lila', 'montana', 'sol', 'ola', 'luna', 'rombo', 'brote'];

/** Avatar del usuario: el que haya elegido o, si no, su inicial. Nunca una foto. */
@Component({
  selector: 'app-avatar',
  host: {
    class: 'block shrink-0 overflow-hidden rounded-full',
    '[style.width.px]': 'tamano()',
    '[style.height.px]': 'tamano()',
    'aria-hidden': 'true',
  },
  template: `
    @switch (avatar()) {
      @case ('gemelo') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#332c78" />
          <circle cx="16" cy="20" r="8" fill="#8b83ff" />
          <circle cx="24" cy="20" r="8" fill="#efedff" opacity="0.85" />
        </svg>
      }
      @case ('lila') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#efedff" />
          <circle cx="16" cy="20" r="8" fill="#5b4ff5" opacity="0.85" />
          <circle cx="24" cy="20" r="8" fill="#332c78" opacity="0.8" />
        </svg>
      }
      @case ('montana') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#e4f1ea" />
          <circle cx="28" cy="12" r="3" fill="#f2c46d" />
          <path d="M13 40 27 18l15 22z" fill="#9fd0b6" />
          <path d="M-2 40 14 20l16 20z" fill="#4f9a77" />
        </svg>
      }
      @case ('sol') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#fdf0e1" />
          <path d="M10 26a10 10 0 0 1 20 0z" fill="#f1a35c" />
          <path d="M7 29h26M11 33h18" stroke="#f6c79b" stroke-width="2" stroke-linecap="round" />
        </svg>
      }
      @case ('ola') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#e5eefb" />
          <path d="M0 21c5-4 10-4 14 0s9 4 13 0 9-4 13 0v19H0z" fill="#9dbdf2" />
          <path d="M0 28c5-4 10-4 14 0s9 4 13 0 9-4 13 0v12H0z" fill="#4d7fd6" />
        </svg>
      }
      @case ('luna') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#24213a" />
          <circle cx="19" cy="21" r="9" fill="#f4d58d" />
          <circle cx="23.5" cy="17.5" r="8" fill="#24213a" />
          <circle cx="29" cy="27" r="1.2" fill="#f4d58d" opacity="0.7" />
          <circle cx="12" cy="11" r="1" fill="#f4d58d" opacity="0.6" />
        </svg>
      }
      @case ('rombo') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#fdebe7" />
          <path d="m20 8 12 12-12 12L8 20z" fill="#e07a5f" />
          <path d="m20 15 5 5-5 5-5-5z" fill="#fdebe7" />
        </svg>
      }
      @case ('brote') {
        <svg viewBox="0 0 40 40">
          <rect width="40" height="40" fill="#eef5e6" />
          <path d="M20 31V19" stroke="#5b8c42" stroke-width="2" stroke-linecap="round" />
          <path d="M20 22c-6 0-9-3-9-8 6 0 9 3 9 8z" fill="#7fb069" />
          <path d="M20 19c0-5 3-8 9-8 0 5-3 8-9 8z" fill="#5b8c42" />
        </svg>
      }
      @default {
        <span
          class="grid size-full place-items-center bg-tinta font-semibold text-white"
          [style.font-size.px]="tamano() * 0.4"
          >{{ inicial() }}</span
        >
      }
    }
  `,
  styles: `
    svg {
      display: block;
      width: 100%;
      height: 100%;
    }
  `,
})
export class Avatar {
  readonly nombre = input('');
  /** Sin avatar (null): la inicial del nombre */
  readonly avatar = input<string | null | undefined>(null);
  readonly tamano = input(36);

  protected readonly inicial = computed(() => (this.nombre() || '?').charAt(0).toUpperCase());
}
