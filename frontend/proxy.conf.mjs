// Gemelo digital profesional · TFG Grado en Ingeniería Informática (UNIR)
// SPDX-License-Identifier: Apache-2.0
// En desarrollo, redirige /api al backend (en Docker: http://backend:8000).
export default {
  '/api': {
    target: process.env['API_URL'] ?? 'http://localhost:8000',
    secure: false,
    changeOrigin: true,
  },
};
