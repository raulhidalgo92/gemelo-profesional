// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { NgTemplateOutlet } from '@angular/common';
import { Component, computed, inject, linkedSignal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterLink } from '@angular/router';
import {
  ArrowRight,
  Award,
  BadgeCheck,
  Briefcase,
  FileUp,
  Flag,
  GraduationCap,
  LucideAngularModule,
  MessageCircle,
  Mic,
  Mountain,
  Sparkles,
} from 'lucide-angular';
import { catchError, forkJoin, of } from 'rxjs';

import { GemeloService } from '../../nucleo/gemelo.service';
import { SesionService } from '../../nucleo/sesion.service';
import { Avatar } from '../../nucleo/ui/avatar';
import {
  aniosExperiencia,
  EstadoGemelo,
  haceCuanto,
  IconoLogro,
  logros,
  porAlcance,
  puestoActual,
  tareas,
} from './panel';
import { ActualizarCv, CvAplicado } from './actualizar-cv';
import { TodasCompetencias } from './todas';
import { Trayectoria } from './trayectoria';

const ICONOS_LOGRO = {
  creado: Sparkles,
  destino: Flag,
  evidencia: BadgeCheck,
  entrevista: MessageCircle,
  cinco: Award,
  meta: Mountain,
} satisfies Record<IconoLogro, unknown>;

/** Panel «Mi gemelo»: punto de encuentro de la aplicación. */
@Component({
  selector: 'app-gemelo',
  imports: [
    ActualizarCv,
    Avatar,
    LucideAngularModule,
    NgTemplateOutlet,
    RouterLink,
    TodasCompetencias,
    Trayectoria,
  ],
  templateUrl: './gemelo.html',
  styleUrl: './gemelo.css',
})
export class GemeloPagina {
  private readonly sesion = inject(SesionService);
  private readonly gemelo = inject(GemeloService);

  protected readonly iconos = { ArrowRight, FileUp };
  protected readonly iconosLogro = ICONOS_LOGRO;
  protected readonly accesos = [
    { titulo: 'Ofertas para ti', icono: Briefcase },
    { titulo: 'Formaciones clave', icono: GraduationCap },
    { titulo: 'Entrevistas por practicar', icono: Mic },
  ];

  /** undefined: cargando · null: error */
  protected readonly datos = toSignal(
    forkJoin({ resumen: this.gemelo.resumen(), competencias: this.gemelo.competencias() }).pipe(
      catchError(() => of(null)),
    ),
    { initialValue: undefined },
  );

  private readonly hoy = new Date();
  protected readonly nombre = computed(() => this.sesion.usuario()?.nombre ?? '');
  protected readonly avatar = computed(() => this.sesion.usuario()?.avatar);
  // Editables: «Actualizar CV» y «Ver todas» los cambian sin recargar la página
  protected readonly perfil = linkedSignal(() => this.datos()?.resumen.perfil ?? null);
  private readonly actualizadoEn = linkedSignal(() => this.datos()?.resumen.actualizado_en);
  protected readonly competencias = linkedSignal(() => this.datos()?.competencias ?? []);

  /** Puesto · años de experiencia · inglés */
  protected readonly datosPerfil = computed(() => {
    const p = this.perfil();
    if (!p) return [];
    const anios = aniosExperiencia(p.experiencias, this.hoy.getFullYear());
    return [
      puestoActual(p.experiencias)?.puesto,
      anios ? `${anios} ${anios === 1 ? 'año' : 'años'} de experiencia` : undefined,
      p.nivel_ingles ? `Inglés ${p.nivel_ingles}` : undefined,
    ].filter((d): d is string => !!d);
  });

  protected readonly actualizado = computed(() => {
    const fecha = this.actualizadoEn();
    return fecha ? haceCuanto(new Date(fecha), this.hoy) : undefined;
  });

  protected readonly columnas = computed(() => porAlcance(this.competencias()));
  protected readonly demostradas = computed(
    () => this.competencias().filter((c) => c.demostrada).length,
  );

  private readonly estado = computed<EstadoGemelo>(() => ({
    // El gemelo está creado cuando hay un CV analizado, que siempre deja su trayectoria
    // (las competencias solas pueden venir de añadirlas a mano o de un CV antiguo)
    conCv: !!this.perfil(),
    conDestino: false, // el destino llega en la siguiente fase
    demostradas: this.demostradas(),
    entrevistas: 0,
  }));
  protected readonly tareas = computed(() => tareas(this.estado()));
  protected readonly hechas = computed(() => this.tareas().filter((t) => t.hecha).length);
  protected readonly siguiente = computed(() => this.tareas().find((t) => !t.hecha));
  protected readonly logros = computed(() => logros(this.estado()));
  protected readonly conseguidos = computed(() => this.logros().filter((l) => l.conseguido));

  protected alAplicarCv(cv: CvAplicado): void {
    this.perfil.set(cv.perfil);
    this.competencias.set(cv.competencias);
    this.actualizadoEn.set(new Date().toISOString());
  }

  /** Marcas de la barra: una por competencia o, si son muchas, una barra continua */
  protected marcas(total: number): number[] {
    return Array.from({ length: total <= 12 ? total : 0 }, (_, i) => i);
  }
}
