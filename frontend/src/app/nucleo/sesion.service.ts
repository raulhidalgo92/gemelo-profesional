// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, catchError, firstValueFrom, map, of, tap } from 'rxjs';

export interface Usuario {
  nombre: string;
  email: string;
  /** Avatar de la colección de la app; null: la inicial */
  avatar: string | null;
  bienvenida_pendiente: boolean;
}

export interface Cuenta {
  nombre: string;
  email: string;
  verificada_en: string | null;
  consentimiento_en: string | null;
  consentimiento_version: string | null;
  /** Sesiones abiertas en otros dispositivos */
  otras_sesiones: number;
}

export interface DatosRegistro {
  nombre: string;
  email: string;
  contrasena: string;
  acepta_privacidad: true;
}

const BASE = '/api/cuenta';
const CLAVE_EMAIL = 'gemelo.email_pendiente';

/** Cuenta del usuario: registro en dos pasos, sesión (cookie httpOnly) y bienvenida. */
@Injectable({ providedIn: 'root' })
export class SesionService {
  private readonly http = inject(HttpClient);

  /** undefined: aún no se sabe · null: sin sesión */
  readonly usuario = signal<Usuario | null | undefined>(undefined);
  readonly conSesion = computed(() => !!this.usuario());
  /** Correo pendiente de activar (sobrevive a una recarga de la pestaña). */
  readonly emailPendiente = signal<string>(leer(CLAVE_EMAIL));

  recordarEmail(email: string): void {
    this.emailPendiente.set(email);
    guardar(CLAVE_EMAIL, email);
  }

  /** Consulta la sesión una sola vez (la usan las guardas de las rutas). */
  cargar(): Promise<Usuario | null> {
    const actual = this.usuario();
    if (actual !== undefined) return Promise.resolve(actual);
    return firstValueFrom(
      this.http.get<Usuario>(`${BASE}/yo`).pipe(
        catchError(() => of(null)),
        tap((u) => this.usuario.set(u)),
      ),
    );
  }

  registrar(datos: DatosRegistro): Observable<void> {
    return this.http.post(`${BASE}/registro`, datos).pipe(map(() => undefined));
  }

  reenviar(email: string): Observable<void> {
    return this.http.post(`${BASE}/reenviar`, { email }).pipe(map(() => undefined));
  }

  verificarCodigo(email: string, codigo: string): Observable<Usuario> {
    return this.http
      .post<Usuario>(`${BASE}/verificar`, { email, codigo })
      .pipe(tap((u) => this.usuario.set(u)));
  }

  verificarEnlace(token: string): Observable<Usuario> {
    return this.http
      .post<Usuario>(`${BASE}/verificar-enlace`, { token })
      .pipe(tap((u) => this.usuario.set(u)));
  }

  entrar(email: string, contrasena: string): Observable<Usuario> {
    return this.http
      .post<Usuario>(`${BASE}/entrar`, { email, contrasena })
      .pipe(tap((u) => this.usuario.set(u)));
  }

  /** Contraseña olvidada: la respuesta es la misma exista o no la cuenta. */
  recuperar(email: string): Observable<void> {
    return this.http.post(`${BASE}/recuperar`, { email }).pipe(map(() => undefined));
  }

  /** Nueva contraseña con el código (y el correo) o con el enlace; después se entra. */
  restablecer(datos: {
    contrasena: string;
    email?: string;
    codigo?: string;
    token?: string;
  }): Observable<Usuario> {
    return this.http
      .post<Usuario>(`${BASE}/restablecer`, datos)
      .pipe(tap((u) => this.usuario.set(u)));
  }

  salir(): Observable<void> {
    return this.http.post<void>(`${BASE}/salir`, {}).pipe(tap(() => this.usuario.set(null)));
  }

  cuenta(): Observable<Cuenta> {
    return this.http.get<Cuenta>(BASE);
  }

  /** El correo no se puede cambiar: identifica la cuenta. */
  cambiarNombre(nombre: string): Observable<Usuario> {
    return this.http.patch<Usuario>(BASE, { nombre }).pipe(tap((u) => this.usuario.set(u)));
  }

  /** null vuelve a la inicial. */
  cambiarAvatar(avatar: string | null): Observable<Usuario> {
    return this.http.patch<Usuario>(BASE, { avatar }).pipe(tap((u) => this.usuario.set(u)));
  }

  /** Cierra también las sesiones de otros dispositivos. */
  cambiarContrasena(actual: string, nueva: string): Observable<void> {
    return this.http.post<void>(`${BASE}/contrasena`, { actual, nueva });
  }

  cerrarOtrasSesiones(): Observable<void> {
    return this.http.post<void>(`${BASE}/cerrar-sesiones`, {});
  }

  /** Borra la cuenta, el gemelo y todos sus datos. */
  darDeBaja(contrasena: string): Observable<void> {
    return this.http
      .delete<void>(BASE, { body: { contrasena } })
      .pipe(tap(() => this.usuario.set(null)));
  }

  terminarBienvenida(): Observable<void> {
    return this.http.post<void>(`${BASE}/bienvenida`, {}).pipe(
      tap(() => {
        const u = this.usuario();
        if (u) this.usuario.set({ ...u, bienvenida_pendiente: false });
      }),
    );
  }
}

function leer(clave: string): string {
  try {
    return sessionStorage.getItem(clave) ?? '';
  } catch {
    return '';
  }
}

function guardar(clave: string, valor: string): void {
  try {
    sessionStorage.setItem(clave, valor);
  } catch {
    /* almacenamiento no disponible: solo se pierde tras recargar */
  }
}

const MENSAJES: Record<string, string> = {
  credenciales: 'El correo o la contraseña no son correctos.',
  contrasena_actual: 'La contraseña actual no es correcta.',
  contrasena_incorrecta: 'La contraseña no es correcta.',
  cuenta_no_verificada: 'Tu cuenta aún no está activada. Te hemos enviado un código nuevo.',
  codigo_incorrecto: 'Ese código no es correcto. Revísalo e inténtalo de nuevo.',
  codigo_caducado: 'El código ha caducado. Pide uno nuevo.',
  demasiados_intentos: 'Demasiados intentos. Pide un código nuevo.',
  enlace_no_valido: 'El enlace no es válido o ha caducado.',
  espera: 'Espera unos segundos antes de pedir otro código.',
  demasiadas_peticiones: 'Demasiados intentos seguidos. Prueba de nuevo en unos minutos.',
  formato_no_admitido: 'Sube el CV en PDF o en Word (.docx).',
  archivo_grande: 'El archivo pesa más de 5 MB.',
  archivo_ilegible: 'No hemos podido abrir el archivo. ¿Está dañado o protegido con contraseña?',
  sin_texto:
    'No encontramos texto en el archivo. Si es un PDF escaneado, súbelo en Word o como PDF con texto.',
  ia_no_disponible: 'El análisis no está disponible ahora mismo. Inténtalo en unos minutos.',
};

/** Traduce un error de la API a un mensaje para el usuario. */
export function mensajeDeError(e: unknown): string {
  if (e instanceof HttpErrorResponse) {
    const codigo = typeof e.error?.detail === 'string' ? e.error.detail : '';
    if (MENSAJES[codigo]) return MENSAJES[codigo];
    if (e.status === 0) return 'No hay conexión con el servidor. Inténtalo de nuevo.';
  }
  return 'Algo ha fallado. Inténtalo de nuevo en unos segundos.';
}

/** Código de error de la API (`detail`), si lo hay. */
export function codigoDeError(e: unknown): string | null {
  return e instanceof HttpErrorResponse && typeof e.error?.detail === 'string'
    ? e.error.detail
    : null;
}
