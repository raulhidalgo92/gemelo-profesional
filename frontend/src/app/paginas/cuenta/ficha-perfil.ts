// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  input,
  output,
  signal,
  viewChild,
} from '@angular/core';
import { BadgeCheck, LucideAngularModule, Pencil } from 'lucide-angular';

import { mensajeDeError, SesionService } from '../../nucleo/sesion.service';
import { Avatar } from '../../nucleo/ui/avatar';
import { PaletaAvatar } from './paleta-avatar';

/**
 * Ficha de perfil de Mi cuenta: avatar, nombre y correo.
 * Todo se edita en su sitio: el avatar con su paleta y el nombre convertido en campo.
 */
@Component({
  selector: 'app-ficha-perfil',
  imports: [Avatar, LucideAngularModule, PaletaAvatar],
  templateUrl: './ficha-perfil.html',
  styleUrl: './ficha-perfil.css',
  host: {
    class: 'block',
    '(document:click)': 'alPulsarFuera($event)',
    '(document:keydown.escape)': 'eligiendo.set(false)',
  },
})
export class FichaPerfil {
  private readonly sesion = inject(SesionService);
  private readonly injector = inject(Injector);
  private readonly elemento = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly campoNombre = viewChild<ElementRef<HTMLInputElement>>('campoNombre');

  readonly email = input.required<string>();
  readonly verificado = input(false);
  /** Texto para el aviso flotante de la página */
  readonly aviso = output<string>();
  /** Empieza a editarse el nombre: la página cierra lo demás (una edición cada vez) */
  readonly editando = output();

  protected readonly iconos = { BadgeCheck, Pencil };
  protected readonly nombre = computed(() => this.sesion.usuario()?.nombre ?? '');
  protected readonly avatar = computed(() => this.sesion.usuario()?.avatar ?? null);

  /** Paleta de avatares abierta */
  protected readonly eligiendo = signal(false);

  protected readonly editandoNombre = signal(false);
  protected readonly nombreNuevo = signal('');
  protected readonly errorNombre = signal('');
  private readonly guardando = signal(false);
  protected readonly puedeGuardarNombre = computed(() => {
    const nombre = this.nombreNuevo().trim();
    return !!nombre && nombre !== this.nombre() && !this.guardando();
  });

  /** Se guarda al momento, sin botón de guardar */
  protected elegirAvatar(a: string | null): void {
    this.eligiendo.set(false);
    if (a === this.avatar()) return;
    this.sesion.cambiarAvatar(a).subscribe({
      next: () => this.aviso.emit('Avatar actualizado'),
      error: (e) => this.aviso.emit(mensajeDeError(e)),
    });
  }

  /** La paleta se cierra al pulsar fuera de la ficha */
  protected alPulsarFuera(e: Event): void {
    if (this.eligiendo() && !this.elemento.nativeElement.contains(e.target as Node)) {
      this.eligiendo.set(false);
    }
  }

  editarNombre(): void {
    this.nombreNuevo.set(this.nombre());
    this.errorNombre.set('');
    this.editandoNombre.set(true);
    this.editando.emit();
    // El cursor entra en el campo con el nombre ya seleccionado
    afterNextRender(
      () => {
        const campo = this.campoNombre()?.nativeElement;
        campo?.focus();
        campo?.select();
      },
      { injector: this.injector },
    );
  }

  cancelarNombre(): void {
    this.editandoNombre.set(false);
    this.errorNombre.set('');
  }

  protected guardarNombre(): void {
    const nombre = this.nombreNuevo().trim();
    if (!nombre) return this.errorNombre.set('El nombre no puede estar vacío.');
    if (nombre === this.nombre()) return this.cancelarNombre();
    this.guardando.set(true);
    this.sesion.cambiarNombre(nombre).subscribe({
      next: () => {
        this.guardando.set(false);
        this.editandoNombre.set(false);
        this.aviso.emit('Nombre actualizado');
      },
      error: (e) => {
        this.guardando.set(false);
        this.errorNombre.set(mensajeDeError(e));
      },
    });
  }
}
