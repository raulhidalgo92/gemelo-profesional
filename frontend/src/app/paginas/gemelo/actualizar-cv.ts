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
  OnDestroy,
  output,
  signal,
  viewChild,
} from '@angular/core';
import {
  Check,
  Equal,
  FileText,
  FileUp,
  LoaderCircle,
  LucideAngularModule,
  Minus,
  Pencil,
  Plus,
  ShieldCheck,
  X,
} from 'lucide-angular';
import { Subscription } from 'rxjs';

import {
  AnalisisCv,
  CompetenciaGemelo,
  errorDeArchivoCv,
  GemeloService,
  MAX_MB_CV,
  PerfilCv,
} from '../../nucleo/gemelo.service';
import { mensajeDeError } from '../../nucleo/sesion.service';
import { cambiosTrayectoria, resumenCambios } from './cambios';
import { ALCANCES, alcanceDe } from './panel';

type Fase = 'subir' | 'leyendo' | 'revisar' | 'al-dia';

/** Lo que se ha guardado, para que el panel se actualice sin recargar */
export interface CvAplicado {
  perfil: PerfilCv;
  competencias: CompetenciaGemelo[];
}

const PASOS = ['Leyendo tu CV', 'Ocultando tus datos personales', 'Comparándolo con tu gemelo'];
const DURACION_PASO = 1400;
const DURACION_AVISO = 5000;

/** Panel lateral «Actualizar tu CV»: subir, analizar y revisar los cambios antes de aplicarlos. */
@Component({
  selector: 'app-actualizar-cv',
  imports: [LucideAngularModule],
  templateUrl: './actualizar-cv.html',
  styleUrl: './actualizar-cv.css',
})
export class ActualizarCv implements OnDestroy {
  private readonly gemelo = inject(GemeloService);
  private readonly injector = inject(Injector);
  private readonly cajon = viewChild.required<ElementRef<HTMLDialogElement>>('cajon');
  private readonly cuerpo = viewChild<ElementRef<HTMLElement>>('cuerpo');
  private readonly entendido = viewChild<ElementRef<HTMLButtonElement>>('entendido');

  /** Trayectoria guardada, para comparar */
  readonly perfil = input.required<PerfilCv | null>();
  /** «hace 3 días», «hoy»… */
  readonly actualizado = input<string>();
  readonly aplicado = output<CvAplicado>();

  protected readonly iconos = {
    Check,
    Equal,
    FileText,
    FileUp,
    LoaderCircle,
    Minus,
    Pencil,
    Plus,
    ShieldCheck,
    X,
  };
  protected readonly pasos = PASOS;
  protected readonly maxMb = MAX_MB_CV;

  protected readonly fase = signal<Fase>('subir');
  protected readonly arrastrando = signal(false);
  protected readonly nombreArchivo = signal('');
  protected readonly error = signal('');
  protected readonly paso = signal(0);
  protected readonly analisis = signal<AnalisisCv | null>(null);
  /** Competencias nuevas que el usuario desmarca */
  protected readonly descartadas = signal(new Set<string>());
  /** Competencias que ya no trae el CV y el usuario desmarca para quitarlas */
  protected readonly quitadas = signal(new Set<string>());
  protected readonly guardando = signal(false);
  protected readonly aviso = signal('');

  private peticion?: Subscription;
  private relojPasos?: ReturnType<typeof setInterval>;
  private relojAviso?: ReturnType<typeof setTimeout>;

  protected readonly cambios = computed(() => {
    const a = this.analisis();
    return a ? cambiosTrayectoria(this.perfil(), a.perfil) : [];
  });
  protected readonly nuevas = computed(
    () => this.analisis()?.competencias.filter((c) => c.nueva) ?? [],
  );
  protected readonly yaNo = computed(() => this.analisis()?.ya_no ?? []);
  protected readonly siguenIgual = computed(
    () => this.analisis()?.competencias.filter((c) => !c.nueva).length ?? 0,
  );

  abrir(): void {
    this.reiniciar();
    this.cajon().nativeElement.showModal();
  }

  protected cerrar(): void {
    this.cajon().nativeElement.close();
  }

  /** Al cerrar se cancela el análisis en curso: no se guarda nada */
  protected alCerrar(): void {
    this.reiniciar();
  }

  protected clicFuera(e: MouseEvent): void {
    if (e.target === this.cajon().nativeElement && !this.guardando()) this.cerrar();
  }

  protected elegir(evento: Event): void {
    const entrada = evento.target as HTMLInputElement;
    const archivo = entrada.files?.[0];
    entrada.value = '';
    if (archivo) this.leer(archivo);
  }

  protected soltar(evento: DragEvent): void {
    evento.preventDefault();
    this.arrastrando.set(false);
    const archivo = evento.dataTransfer?.files?.[0];
    if (archivo) this.leer(archivo);
  }

  protected alterna(conjunto: typeof this.descartadas, uri: string): void {
    conjunto.update((s) => {
      const copia = new Set(s);
      if (!copia.delete(uri)) copia.add(uri);
      return copia;
    });
  }

  protected alcance(clave: string | null): string {
    return ALCANCES.find((a) => a.clave === alcanceDe(clave))!.titulo;
  }

  protected aplicar(): void {
    const a = this.analisis();
    if (!a) return;
    const competencias = a.competencias.filter((c) => !this.descartadas().has(c.uri));
    const conservar = a.ya_no.filter((c) => !this.quitadas().has(c.uri)).map((c) => c.uri);
    const texto = resumenCambios(
      this.cambios().filter((c) => c.tipo === 'nueva' && c.experiencia).length,
      this.nuevas().length - this.descartadas().size,
      this.quitadas().size,
    );
    this.guardando.set(true);
    this.error.set('');
    this.peticion = this.gemelo.aplicarCv(a.perfil, competencias, conservar).subscribe({
      next: (lista) => {
        this.aplicado.emit({ perfil: a.perfil, competencias: lista });
        this.cerrar();
        this.avisar(texto);
      },
      error: (e) => {
        this.guardando.set(false);
        this.error.set(mensajeDeError(e));
      },
    });
  }

  private leer(archivo: File): void {
    const error = errorDeArchivoCv(archivo);
    this.error.set(error ?? '');
    if (error) return;

    this.nombreArchivo.set(archivo.name);
    this.paso.set(0);
    this.fase.set('leyendo');
    // El análisis es una sola petición: los pasos avanzan mientras tanto
    this.relojPasos = setInterval(
      () => this.paso.update((p) => Math.min(p + 1, PASOS.length - 1)),
      DURACION_PASO,
    );
    this.peticion = this.gemelo.analizarCv(archivo).subscribe({
      next: (a) => {
        clearInterval(this.relojPasos);
        this.analisis.set(a);
        const hayCambios = this.cambios().length || this.nuevas().length || a.ya_no.length;
        this.fase.set(hayCambios ? 'revisar' : 'al-dia');
        afterNextRender(
          () => {
            const cuerpo = this.cuerpo()?.nativeElement;
            if (cuerpo) cuerpo.scrollTop = 0;
            this.entendido()?.nativeElement.focus();
          },
          { injector: this.injector },
        );
      },
      error: (e) => {
        clearInterval(this.relojPasos);
        this.fase.set('subir');
        this.error.set(mensajeDeError(e));
      },
    });
  }

  private reiniciar(): void {
    this.peticion?.unsubscribe();
    clearInterval(this.relojPasos);
    this.fase.set('subir');
    this.error.set('');
    this.analisis.set(null);
    this.descartadas.set(new Set());
    this.quitadas.set(new Set());
    this.guardando.set(false);
  }

  private avisar(texto: string): void {
    clearTimeout(this.relojAviso);
    this.aviso.set(texto);
    this.relojAviso = setTimeout(() => this.aviso.set(''), DURACION_AVISO);
  }

  ngOnDestroy(): void {
    this.peticion?.unsubscribe();
    clearInterval(this.relojPasos);
    clearTimeout(this.relojAviso);
  }
}
