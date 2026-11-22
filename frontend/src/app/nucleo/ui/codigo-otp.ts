// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, ElementRef, effect, input, output, signal, viewChildren } from '@angular/core';

const LONGITUD = 6;

/**
 * Código de verificación de 6 cifras: una casilla por cifra, avance automático,
 * pegado del código completo y retroceso con la tecla de borrar.
 */
@Component({
  selector: 'app-codigo-otp',
  template: `
    <div
      class="flex justify-between gap-2"
      [class.animate-temblar]="error()"
      role="group"
      aria-label="Código de verificación"
    >
      @for (i of posiciones; track i) {
        <input
          #casilla
          type="text"
          inputmode="numeric"
          [attr.autocomplete]="i === 0 ? 'one-time-code' : 'off'"
          maxlength="1"
          [value]="cifras()[i]"
          [disabled]="deshabilitado()"
          [attr.aria-label]="'Cifra ' + (i + 1)"
          [attr.aria-invalid]="error() || null"
          (input)="escribir(i, $event)"
          (keydown)="tecla(i, $event)"
          (paste)="pegar($event)"
          (focus)="$any($event.target).select()"
          class="h-14 w-full min-w-0 rounded-xl border border-borde bg-superficie text-center text-2xl font-semibold tabular-nums transition outline-none focus:border-acento focus:ring-4 focus:ring-acento/15 disabled:opacity-60 aria-invalid:border-error"
        />
      }
    </div>
  `,
})
export class CodigoOtp {
  readonly deshabilitado = input(false);
  /** Al pasar a true, el código se borra y las casillas tiemblan. */
  readonly error = input(false);
  readonly completo = output<string>();

  protected readonly posiciones = Array.from({ length: LONGITUD }, (_, i) => i);
  protected readonly cifras = signal<string[]>(Array(LONGITUD).fill(''));
  private readonly casillas = viewChildren<ElementRef<HTMLInputElement>>('casilla');

  constructor() {
    effect(() => {
      if (this.error()) {
        this.cifras.set(Array(LONGITUD).fill(''));
        queueMicrotask(() => this.enfocar(0));
      }
    });
  }

  enfocar(i: number): void {
    this.casillas()[Math.max(0, Math.min(i, LONGITUD - 1))]?.nativeElement.focus();
  }

  protected escribir(i: number, evento: Event): void {
    const campo = evento.target as HTMLInputElement;
    const cifra = campo.value.replace(/\D/g, '').slice(-1);
    campo.value = cifra;
    this.poner(i, cifra);
    if (cifra) this.enfocar(i + 1);
  }

  protected tecla(i: number, evento: KeyboardEvent): void {
    if (evento.key === 'Backspace' && !this.cifras()[i]) {
      evento.preventDefault();
      this.poner(i - 1, '');
      this.enfocar(i - 1);
    } else if (evento.key === 'ArrowLeft') {
      this.enfocar(i - 1);
    } else if (evento.key === 'ArrowRight') {
      this.enfocar(i + 1);
    }
  }

  protected pegar(evento: ClipboardEvent): void {
    const texto = (evento.clipboardData?.getData('text') ?? '').replace(/\D/g, '');
    if (!texto) return;
    evento.preventDefault();
    const cifras = texto
      .slice(0, LONGITUD)
      .padEnd(LONGITUD, ' ')
      .split('')
      .map((c) => c.trim());
    this.cifras.set(cifras);
    this.enfocar(Math.min(texto.length, LONGITUD - 1));
    this.emitirSiCompleto();
  }

  private poner(i: number, cifra: string): void {
    if (i < 0) return;
    this.cifras.update((c) => c.map((v, j) => (j === i ? cifra : v)));
    this.emitirSiCompleto();
  }

  private emitirSiCompleto(): void {
    const codigo = this.cifras().join('');
    if (codigo.length === LONGITUD) this.completo.emit(codigo);
  }
}
