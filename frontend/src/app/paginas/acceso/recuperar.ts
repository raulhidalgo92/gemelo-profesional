// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { mensajeDeError, SesionService } from '../../nucleo/sesion.service';

/** Contraseña olvidada, paso 1: el correo al que enviar el código. */
@Component({
  selector: 'app-recuperar',
  imports: [ReactiveFormsModule, RouterLink, LucideAngularModule],
  template: `
    <div class="mb-8">
      <h1 class="titulo-acceso">¿Has olvidado tu contraseña?</h1>
      <p class="mt-2 text-tinta-suave">
        Escribe tu correo y te enviaremos un código para elegir una nueva.
      </p>
    </div>

    <form [formGroup]="form" (ngSubmit)="enviar()" novalidate class="space-y-5">
      <div>
        <label for="email" class="etiqueta-campo">Correo electrónico</label>
        <input id="email" type="email" formControlName="email" class="campo" autocomplete="email" />
      </div>
      @if (error()) {
        <p class="rounded-xl bg-error/8 px-4 py-3 text-sm text-error" role="alert">{{ error() }}</p>
      }
      <button type="submit" class="boton-primario w-full" [disabled]="enviando()">
        @if (enviando()) {
          <lucide-icon [img]="iconos.LoaderCircle" [size]="18" class="animate-spin" />
        }
        Enviar el código
      </button>
    </form>

    <p class="mt-8 text-center text-sm text-tinta-suave">
      ¿Te has acordado? <a routerLink="/entrar" class="enlace">Volver a entrar</a>
    </p>
  `,
})
export class RecuperarPagina {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);

  protected readonly iconos = { LoaderCircle };
  protected readonly enviando = signal(false);
  protected readonly error = signal('');
  protected readonly form = inject(NonNullableFormBuilder).group({
    email: [this.sesion.emailPendiente(), [Validators.required, Validators.email]],
  });

  protected enviar(): void {
    if (this.form.invalid) {
      this.error.set('Escribe tu correo electrónico.');
      return;
    }
    const { email } = this.form.getRawValue();
    this.enviando.set(true);
    this.error.set('');
    this.sesion.recuperar(email).subscribe({
      next: () => {
        this.sesion.recordarEmail(email);
        this.router.navigateByUrl('/recuperar/codigo');
      },
      error: (e) => {
        this.enviando.set(false);
        this.error.set(mensajeDeError(e));
      },
    });
  }
}
