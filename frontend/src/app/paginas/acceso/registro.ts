// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, inject, signal } from '@angular/core';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { ArrowRight, Eye, EyeOff, LoaderCircle, LucideAngularModule } from 'lucide-angular';

import { SesionService, mensajeDeError } from '../../nucleo/sesion.service';
import { Fortaleza } from '../../nucleo/ui/fortaleza';

/** Registro, paso 1: nombre, correo, contraseña y consentimiento. */
@Component({
  selector: 'app-registro',
  imports: [ReactiveFormsModule, RouterLink, LucideAngularModule, Fortaleza],
  templateUrl: './registro.html',
})
export class RegistroPagina {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);

  protected readonly iconos = { ArrowRight, Eye, EyeOff, LoaderCircle };
  protected readonly enviando = signal(false);
  protected readonly error = signal('');
  protected readonly verClave = signal(false);

  protected readonly form = inject(NonNullableFormBuilder).group({
    nombre: ['', [Validators.required, Validators.maxLength(80)]],
    email: ['', [Validators.required, Validators.email]],
    contrasena: ['', [Validators.required, Validators.minLength(10), Validators.maxLength(128)]],
    acepta: [false, Validators.requiredTrue],
  });

  protected invalido(campo: keyof typeof this.form.controls): boolean {
    const c = this.form.controls[campo];
    return c.invalid && (c.touched || c.dirty);
  }

  protected enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { nombre, email, contrasena } = this.form.getRawValue();
    this.enviando.set(true);
    this.error.set('');
    this.sesion
      .registrar({ nombre: nombre.trim(), email, contrasena, acepta_privacidad: true })
      .subscribe({
        next: () => {
          this.sesion.recordarEmail(email);
          this.router.navigateByUrl('/registro/codigo');
        },
        error: (e) => {
          this.error.set(mensajeDeError(e));
          this.enviando.set(false);
        },
      });
  }
}
