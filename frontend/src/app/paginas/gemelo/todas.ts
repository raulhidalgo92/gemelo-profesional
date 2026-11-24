// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import {
  afterNextRender,
  Component,
  computed,
  ElementRef,
  inject,
  Injector,
  model,
  OnDestroy,
  signal,
  viewChild,
} from '@angular/core';
import { toObservable, toSignal } from '@angular/core/rxjs-interop';
import { Check, Layers, LucideAngularModule, Plus, Search, Trash2, X } from 'lucide-angular';
import { catchError, debounceTime, distinctUntilChanged, map, of, switchMap } from 'rxjs';

import { ApiService, Competencia } from '../../nucleo/api.service';
import { CompetenciaGemelo, GemeloService } from '../../nucleo/gemelo.service';
import { ALCANCES, alcanceDe, buscar, procedencia } from './panel';

type Estado = 'todas' | 'demostradas' | 'pendientes';

/** Aviso con «Deshacer»: si no se deshace, la acción se confirma al cerrarlo. */
interface Aviso {
  texto: string;
  deshacer?: () => void;
  confirmar?: () => void;
}

const DURACION_AVISO = 6000;

/** Los títulos de ESCO van en minúscula */
const mayuscula = (texto: string) => texto.charAt(0).toUpperCase() + texto.slice(1);
const MAX_RESULTADOS = 6;

/** Panel lateral «Ver todas»: buscar, filtrar, quitar y añadir competencias del gemelo. */
@Component({
  selector: 'app-todas-competencias',
  imports: [LucideAngularModule],
  templateUrl: './todas.html',
  styleUrl: './todas.css',
})
export class TodasCompetencias implements OnDestroy {
  private readonly gemelo = inject(GemeloService);
  private readonly api = inject(ApiService);
  private readonly injector = inject(Injector);
  private readonly cajon = viewChild.required<ElementRef<HTMLDialogElement>>('cajon');
  private readonly buscadorCatalogo = viewChild<ElementRef<HTMLInputElement>>('buscadorCatalogo');

  /** La misma lista que pintan las tarjetas del panel: los cambios se ven a la vez */
  readonly competencias = model.required<CompetenciaGemelo[]>();

  protected readonly iconos = { Check, Layers, Plus, Search, Trash2, X };
  protected readonly alcances = ALCANCES;
  protected readonly estados = [
    { clave: 'todas', texto: 'Todas' },
    { clave: 'demostradas', texto: 'Demostradas' },
    { clave: 'pendientes', texto: 'Por demostrar' },
  ] as const;
  protected readonly procedencia = procedencia;

  protected readonly texto = signal('');
  protected readonly estado = signal<Estado>('todas');
  protected readonly alcance = signal<string | null>(null);
  /** URI de la competencia demostrada que se va a quitar, pendiente de confirmar */
  protected readonly confirmando = signal<string | null>(null);
  protected readonly anadiendo = signal(false);
  protected readonly consulta = signal('');
  protected readonly aviso = signal<Aviso | null>(null);
  private reloj?: ReturnType<typeof setTimeout>;

  protected readonly demostradas = computed(
    () => this.competencias().filter((c) => c.demostrada).length,
  );
  private readonly filtradas = computed(() =>
    buscar(this.competencias(), this.texto(), this.alcance()),
  );
  protected readonly cuentas = computed(() => {
    const todas = this.filtradas().length;
    const demostradas = this.filtradas().filter((c) => c.demostrada).length;
    return { todas, demostradas, pendientes: todas - demostradas };
  });
  protected readonly lista = computed(() => {
    const e = this.estado();
    return this.filtradas().filter((c) => e === 'todas' || c.demostrada === (e === 'demostradas'));
  });
  protected readonly indiceEstado = computed(() =>
    this.estados.findIndex((e) => e.clave === this.estado()),
  );

  /** Búsqueda por significado en el catálogo ESCO. null: todavía no se ha buscado */
  private readonly encontradas = toSignal(
    toObservable(this.consulta).pipe(
      map((q) => q.trim()),
      debounceTime(300),
      distinctUntilChanged(),
      switchMap((q) =>
        q.length < 2
          ? of(null)
          : this.api.buscarCompetencias(q, 'semantico').pipe(
              map((r) => r.resultados),
              catchError(() => of([])),
            ),
      ),
    ),
    { initialValue: null },
  );
  protected readonly catalogo = computed(() => {
    const tengo = new Set(this.competencias().map((c) => c.uri));
    return this.encontradas()
      ?.filter((c) => !tengo.has(c.uri))
      .slice(0, MAX_RESULTADOS);
  });

  abrir(): void {
    this.texto.set('');
    this.estado.set('todas');
    this.alcance.set(null);
    this.confirmando.set(null);
    this.anadiendo.set(false);
    this.cajon().nativeElement.showModal();
  }

  protected cerrar(): void {
    this.cajon().nativeElement.close();
  }

  /** Al cerrar (botón, Esc o fuera del panel) se confirma lo pendiente */
  protected alCerrar(): void {
    this.cerrarAviso();
    this.consulta.set('');
  }

  /** Un clic en el fondo oscuro llega al propio <dialog> */
  protected clicFuera(e: MouseEvent): void {
    if (e.target === this.cajon().nativeElement) this.cerrar();
  }

  protected buscarTexto(valor: string): void {
    this.texto.set(valor);
    this.confirmando.set(null);
  }

  protected cambiarAlcance(clave: string | null): void {
    this.alcance.set(this.alcance() === clave ? null : clave);
  }

  protected corto(alcance: string | null): string {
    return ALCANCES.find((a) => a.clave === alcanceDe(alcance))!.corto;
  }

  /** Quitar una demostrada pide confirmación: se pierde la evidencia */
  protected quitar(c: CompetenciaGemelo): void {
    if (c.demostrada && this.confirmando() !== c.uri) {
      this.confirmando.set(c.uri);
      return;
    }
    this.confirmando.set(null);
    this.competencias.update((l) => l.filter((x) => x.uri !== c.uri));
    const volver = () => this.competencias.update((l) => [...l, c]);
    // Se borra en el servidor solo cuando ya no se puede deshacer
    this.avisar(`Has quitado «${mayuscula(c.titulo)}»`, {
      deshacer: volver,
      confirmar: () =>
        this.gemelo.quitar(c.uri).subscribe({
          error: () => {
            volver();
            this.avisar('No se ha podido quitar. Inténtalo de nuevo.');
          },
        }),
    });
  }

  protected abrirAnadir(): void {
    this.consulta.set('');
    this.anadiendo.set(true);
    afterNextRender(() => this.buscadorCatalogo()?.nativeElement.focus(), {
      injector: this.injector,
    });
  }

  protected cerrarAnadir(): void {
    this.anadiendo.set(false);
    this.consulta.set('');
  }

  protected anadir(r: Competencia): void {
    this.gemelo.anadir(r.uri).subscribe({
      next: (c) => {
        this.competencias.update((l) => [...l, c]);
        this.avisar(`Has añadido «${mayuscula(c.titulo)}»`, {
          deshacer: () => {
            this.competencias.update((l) => l.filter((x) => x.uri !== c.uri));
            this.gemelo.quitar(c.uri).subscribe();
          },
        });
      },
      error: () => this.avisar('No se ha podido añadir. Inténtalo de nuevo.'),
    });
  }

  protected deshacer(): void {
    clearTimeout(this.reloj);
    const a = this.aviso();
    this.aviso.set(null);
    a?.deshacer?.();
  }

  private avisar(texto: string, acciones: Omit<Aviso, 'texto'> = {}): void {
    this.cerrarAviso();
    this.aviso.set({ texto, ...acciones });
    this.reloj = setTimeout(() => this.cerrarAviso(), DURACION_AVISO);
  }

  private cerrarAviso(): void {
    clearTimeout(this.reloj);
    const a = this.aviso();
    this.aviso.set(null);
    a?.confirmar?.();
  }

  ngOnDestroy(): void {
    this.cerrarAviso();
  }
}
