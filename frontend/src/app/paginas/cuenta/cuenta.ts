// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import {
  Component,
  computed,
  DestroyRef,
  ElementRef,
  inject,
  linkedSignal,
  signal,
  viewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NonNullableFormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { Check, Download, LoaderCircle, LucideAngularModule } from 'lucide-angular';
import { catchError, Observable, of } from 'rxjs';

import { mensajeDeError, SesionService } from '../../nucleo/sesion.service';
import { FichaPerfil } from './ficha-perfil';

const MIN_CLAVE = 10;
const DURACION_AVISO = 3500;
const FECHA = new Intl.DateTimeFormat('es', { dateStyle: 'long' });

/** Mi cuenta: datos, seguridad, descarga de los datos y baja. El correo no se puede cambiar. */
@Component({
  selector: 'app-cuenta',
  imports: [FichaPerfil, LucideAngularModule, ReactiveFormsModule, RouterLink],
  templateUrl: './cuenta.html',
  styleUrl: './cuenta.css',
})
export class CuentaPagina {
  private readonly sesion = inject(SesionService);
  private readonly router = inject(Router);
  private readonly fb = inject(NonNullableFormBuilder);
  private readonly dialogoBaja = viewChild.required<ElementRef<HTMLDialogElement>>('dialogoBaja');
  private readonly ficha = viewChild(FichaPerfil);

  protected readonly iconos = { Check, Download, LoaderCircle };
  protected readonly minClave = MIN_CLAVE;

  /** undefined: cargando · null: error */
  protected readonly cuenta = toSignal(this.sesion.cuenta().pipe(catchError(() => of(null))), {
    initialValue: undefined,
  });
  protected readonly otrasSesiones = linkedSignal(() => this.cuenta()?.otras_sesiones ?? 0);
  protected readonly consentimiento = computed(() => {
    const c = this.cuenta();
    if (!c?.consentimiento_en) return 'Aceptado al crear tu cuenta';
    const fecha = FECHA.format(new Date(c.consentimiento_en));
    return (
      `Aceptado el ${fecha}` +
      (c.consentimiento_version ? ` · versión ${c.consentimiento_version}` : '')
    );
  });

  /** Formulario de cambio de contraseña desplegado */
  protected readonly cambiandoClave = signal(false);
  protected readonly enviando = signal(false);
  protected readonly cerrandoSesiones = signal(false);
  protected readonly error = signal('');
  protected readonly aviso = signal('');
  private reloj?: ReturnType<typeof setTimeout>;

  constructor() {
    inject(DestroyRef).onDestroy(() => clearTimeout(this.reloj));
  }

  protected readonly formClave = this.fb.group({
    actual: ['', Validators.required],
    nueva: ['', [Validators.required, Validators.minLength(MIN_CLAVE)]],
  });
  protected readonly formBorrar = this.fb.group({ contrasena: ['', Validators.required] });

  protected alternarClave(): void {
    this.error.set('');
    this.ficha()?.cancelarNombre();
    this.formClave.reset();
    this.cambiandoClave.set(!this.cambiandoClave());
  }

  protected guardarClave(): void {
    const { actual, nueva } = this.formClave.getRawValue();
    if (!actual) return this.error.set('Escribe tu contraseña actual.');
    if (nueva.length < MIN_CLAVE) {
      return this.error.set(`La nueva contraseña debe tener al menos ${MIN_CLAVE} caracteres.`);
    }
    this.enviar(this.sesion.cambiarContrasena(actual, nueva), 'Contraseña cambiada', () =>
      this.otrasSesiones.set(0),
    );
  }

  protected cerrarSesiones(): void {
    this.cerrandoSesiones.set(true);
    this.sesion.cerrarOtrasSesiones().subscribe({
      next: () => {
        this.cerrandoSesiones.set(false);
        this.otrasSesiones.set(0);
        this.avisar('Has cerrado la sesión en tus otros dispositivos');
      },
      error: (e) => {
        this.cerrandoSesiones.set(false);
        this.avisar(mensajeDeError(e));
      },
    });
  }

  protected abrirBaja(): void {
    this.cambiandoClave.set(false);
    this.error.set('');
    this.formBorrar.reset();
    this.dialogoBaja().nativeElement.showModal();
  }

  protected cerrarBaja(): void {
    this.dialogoBaja().nativeElement.close();
  }

  /** Esc cierra el diálogo, salvo mientras se está borrando la cuenta */
  protected alCancelarBaja(e: Event): void {
    if (this.enviando()) e.preventDefault();
  }

  /** Un clic en el fondo oscuro llega al propio <dialog> */
  protected clicFueraBaja(e: MouseEvent): void {
    if (e.target === this.dialogoBaja().nativeElement && !this.enviando()) this.cerrarBaja();
  }

  protected borrar(): void {
    const { contrasena } = this.formBorrar.getRawValue();
    if (!contrasena) return;
    this.enviando.set(true);
    this.error.set('');
    this.sesion.darDeBaja(contrasena).subscribe({
      next: () =>
        this.router.navigateByUrl('/entrar', {
          state: { aviso: 'Hemos eliminado tu cuenta y todos tus datos.' },
        }),
      error: (e) => {
        this.enviando.set(false);
        this.error.set(mensajeDeError(e));
      },
    });
  }

  private enviar(peticion: Observable<unknown>, texto: string, despues?: () => void): void {
    this.enviando.set(true);
    this.error.set('');
    peticion.subscribe({
      next: () => {
        this.enviando.set(false);
        this.cambiandoClave.set(false);
        despues?.();
        this.avisar(texto);
      },
      error: (e) => {
        this.enviando.set(false);
        this.error.set(mensajeDeError(e));
      },
    });
  }

  protected avisar(texto: string): void {
    clearTimeout(this.reloj);
    this.aviso.set(texto);
    this.reloj = setTimeout(() => this.aviso.set(''), DURACION_AVISO);
  }
}
