// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
import { HttpInterceptorFn } from '@angular/common/http';

/**
 * Añade una cabecera propia a las peticiones a la API. El backend rechaza las peticiones
 * que modifican datos sin ella: un formulario de otra web no puede añadirla (CSRF).
 */
export const csrfInterceptor: HttpInterceptorFn = (req, next) =>
  next(
    req.url.startsWith('/api') ? req.clone({ setHeaders: { 'X-Requested-With': 'gemelo' } }) : req,
  );
