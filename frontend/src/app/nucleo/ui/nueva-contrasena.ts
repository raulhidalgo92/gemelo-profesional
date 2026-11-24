// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, input, model, signal } from '@angular/core';
import { Eye, EyeOff, LucideAngularModule } from 'lucide-angular';

import { Fortaleza } from './fortaleza';

/** Campo «Nueva contraseña» con botón para mostrarla y medidor de fortaleza. */
@Component({
  selector: 'app-nueva-contrasena',
  imports: [Fortaleza, LucideAngularModule],
  template: `
    <label for="nueva-contrasena" class="etiqueta-campo">Nueva contraseña</label>
    <div class="relative">
      <input
        id="nueva-contrasena"
        class="campo pr-11"
        autocomplete="new-password"
        [type]="ver() ? 'text' : 'password'"
        [value]="valor()"
        [attr.aria-invalid]="invalido() || null"
        (input)="valor.set($any($event.target).value)"
      />
      <button
        type="button"
        class="absolute inset-y-0 right-0 grid w-11 place-items-center text-tinta-tenue transition hover:text-tinta"
        [attr.aria-label]="ver() ? 'Ocultar contraseña' : 'Mostrar contraseña'"
        (click)="ver.set(!ver())"
      >
        <lucide-icon [img]="ver() ? iconos.EyeOff : iconos.Eye" [size]="18" />
      </button>
    </div>
    <app-fortaleza [clave]="valor()" />
    <p class="ayuda-campo">Al menos 10 caracteres.</p>
  `,
})
export class NuevaContrasena {
  readonly valor = model('');
  readonly invalido = input(false);

  protected readonly iconos = { Eye, EyeOff };
  protected readonly ver = signal(false);
}
