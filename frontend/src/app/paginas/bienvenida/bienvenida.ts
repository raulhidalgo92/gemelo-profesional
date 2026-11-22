// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { Component, DestroyRef, computed, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import {
  ArrowRight,
  Check,
  FileText,
  FileUp,
  ListChecks,
  LoaderCircle,
  LockKeyhole,
  LucideAngularModule,
  Sparkles,
  X,
} from 'lucide-angular';

import { CompetenciaGemelo, GemeloService } from '../../nucleo/gemelo.service';
import { SesionService, mensajeDeError } from '../../nucleo/sesion.service';
import { Logo } from '../../nucleo/ui/logo';

const TIPOS = [
  'application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
];
const MAX_MB = 5;
const FASES_ANALISIS = [
  'Leyendo tu CV',
  'Ocultando tus datos personales',
  'Identificando tus competencias',
  'Traduciéndolas al vocabulario europeo ESCO',
];

/** Asistente tras activar la cuenta: bienvenida → CV → revisión de competencias. */
@Component({
  selector: 'app-bienvenida',
  imports: [LucideAngularModule, Logo],
  templateUrl: './bienvenida.html',
})
export class BienvenidaPagina {
  protected readonly sesion = inject(SesionService);
  private readonly gemelo = inject(GemeloService);
  private readonly router = inject(Router);
  private readonly destroyRef = inject(DestroyRef);

  protected readonly iconos = { ArrowRight, Check, FileText, FileUp, LoaderCircle, LockKeyhole, X };
  protected readonly fases = FASES_ANALISIS;
  protected readonly pasos = [
    { titulo: 'Bienvenida', icono: Sparkles },
    { titulo: 'Tu CV', icono: FileUp },
    { titulo: 'Tus competencias', icono: ListChecks },
  ];
  protected readonly paso = signal(0);
  protected readonly archivo = signal<File | null>(null);
  protected readonly arrastrando = signal(false);
  protected readonly errorArchivo = signal('');
  protected readonly nombre = computed(() => this.sesion.usuario()?.nombre ?? '');
  protected readonly analizando = signal(false);
  protected readonly fase = signal(0);
  protected readonly competencias = signal<CompetenciaGemelo[]>([]);

  /** Sube el CV y pasa a revisar las competencias detectadas. */
  protected analizar(): void {
    const archivo = this.archivo();
    if (!archivo) return;
    this.analizando.set(true);
    this.errorArchivo.set('');
    this.fase.set(0);
    const reloj = setInterval(
      () => this.fase.update((f) => Math.min(f + 1, FASES_ANALISIS.length - 1)),
      1400,
    );
    this.destroyRef.onDestroy(() => clearInterval(reloj));
    this.gemelo.subirCv(archivo).subscribe({
      next: (competencias) => {
        clearInterval(reloj);
        this.competencias.set(competencias);
        this.analizando.set(false);
        this.archivo.set(null);
        this.paso.set(2);
      },
      error: (e) => {
        clearInterval(reloj);
        this.analizando.set(false);
        this.errorArchivo.set(mensajeDeError(e));
      },
    });
  }

  protected quitar(c: CompetenciaGemelo): void {
    this.competencias.update((lista) => lista.filter((x) => x.uri !== c.uri));
    this.gemelo.quitar(c.uri).subscribe({
      error: () => this.competencias.update((lista) => [...lista, c]),
    });
  }

  protected elegir(evento: Event): void {
    const entrada = evento.target as HTMLInputElement;
    this.validar(entrada.files?.[0] ?? null);
    entrada.value = '';
  }

  protected soltar(evento: DragEvent): void {
    evento.preventDefault();
    this.arrastrando.set(false);
    this.validar(evento.dataTransfer?.files?.[0] ?? null);
  }

  protected tamano(bytes: number): string {
    return bytes < 1024 * 1024
      ? `${Math.round(bytes / 1024)} KB`
      : `${(bytes / 1048576).toFixed(1)} MB`;
  }

  protected despues(): void {
    this.sesion.terminarBienvenida().subscribe(() => this.router.navigateByUrl('/gemelo'));
  }

  private validar(archivo: File | null): void {
    this.errorArchivo.set('');
    if (!archivo) return;
    if (!TIPOS.includes(archivo.type)) {
      this.errorArchivo.set('Sube el CV en PDF o en Word (.docx).');
    } else if (archivo.size > MAX_MB * 1024 * 1024) {
      this.errorArchivo.set(`El archivo pesa más de ${MAX_MB} MB.`);
    } else {
      this.archivo.set(archivo);
    }
  }
}
