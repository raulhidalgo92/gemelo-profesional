# 0004 · Registro en dos pasos, sesiones y sistema de diseño

- **Estado**: aceptada
- **Fecha**: 2026-11-20

## Contexto

La iteración 1 necesita cuentas de usuario para construir el gemelo de cada persona. Requisitos: registro sencillo, confirmación de que el correo pertenece al usuario, consentimiento explícito (RGPD, con fecha y versión), posibilidad de borrar la cuenta y una seguridad razonable sin depender de servicios de terceros para la identidad. La interfaz debe ser moderna, minimalista y accesible.

## Decisiones

### Registro y activación

1. **Paso 1**: nombre, correo, contraseña (mínimo 10 caracteres) y aceptación de la política de privacidad. La respuesta es siempre la misma, exista o no la cuenta; si el correo ya tiene una cuenta activa, se avisa por correo a su titular (no a quien rellena el formulario), para no revelar qué correos están registrados.
2. **Paso 2**: un único correo con un **código de 6 cifras** y un **botón de activación**. El código sirve aunque el correo se lea en otro dispositivo; el botón activa con un clic. Ambos caducan a los 15 minutos; se permiten 5 intentos y un reenvío cada 60 segundos.
3. El botón abre la web, que envía el token por `POST`: algunos filtros de correo abren los enlaces para analizarlos y no deben activar la cuenta por sí solos.

| Alternativa | Inconveniente |
|---|---|
| Solo enlace | Falla si el correo se abre en otro dispositivo y con los filtros que visitan enlaces |
| Solo código | Obliga siempre a copiar el código |
| Proveedor de identidad (Google, etc.) | Dependencia externa y envío de datos a un tercero |

### Almacenamiento seguro

- Contraseñas con **argon2id** (`pwdlib`).
- Códigos, tokens de activación y sesiones guardados como **HMAC-SHA256** con la clave del servidor: una copia de la base de datos no permite usarlos ni averiguar los códigos de 6 cifras por fuerza bruta.
- **Sesiones en servidor** (tabla `sesion_usuario`) con un token aleatorio en una cookie `httpOnly`, `SameSite=Lax` y `Secure` en producción, limitada a `/api`. Frente a JWT, permite cerrar sesiones y desaparece con la cuenta.
- **CSRF**: las peticiones que modifican datos deben llevar la cabecera `X-Requested-With`, que un formulario de otra web no puede añadir.
- Límites de peticiones por IP en registro, reenvío e inicio de sesión.

### Correo

SMTP genérico con plantillas HTML y texto plano (Jinja2). En desarrollo, **Mailpit** recoge los correos y los muestra en `http://localhost:8025`; en producción se usará un proveedor con servidores en la UE. Nunca se registra en los logs el destinatario ni el contenido.

### Bienvenida

Tras activar la cuenta, un asistente de tres pasos (bienvenida → subir CV → revisar competencias) guía al usuario. Se puede posponer («Lo haré luego»); `usuario.bienvenida_en` registra que lo ha terminado o pospuesto.

### Recuperación de la contraseña (24-11-2026)

Sigue el mismo patrón que la activación, para que la experiencia sea coherente:

1. En «Entrar», «¿La has olvidado?» lleva a pedir un código (`POST /api/cuenta/recuperar`). La respuesta es siempre la misma, exista o no la cuenta, y solo las cuentas activas reciben el correo; si se pidió otro hace menos de un minuto, no se envía nada.
2. El correo trae un **código de 6 cifras** y un **enlace** (`/restablecer?token=…`), con la misma caducidad (15 minutos), el mismo límite de intentos y solo sus resúmenes guardados. Ambos viven en `codigo_verificacion` con `proposito = "recuperacion"` (migración 0008), de modo que un enlace de recuperación no sirve para activar una cuenta ni al revés.
3. Con el código (y el correo) o con el enlace se elige la nueva contraseña (`POST /api/cuenta/restablecer`). Se cierran **todas** las sesiones abiertas, por si alguien más tenía acceso, y se entra directamente en la aplicación: el código ya demuestra que el correo es del usuario.

### Mi cuenta (24-11-2026)

Página `/cuenta`, accesible desde el menú del usuario:

- **Avatar**: el usuario elige uno de una colección propia de ilustraciones abstractas (o su inicial, por defecto); se guarda solo su identificador en `usuario.avatar` (`PATCH /api/cuenta`). **No se permite subir una foto**: la aplicación no la necesita y sería un dato personal más, contra el principio de minimización de la propuesta.
- **Nombre**: editable (`PATCH /api/cuenta`). El **correo no se puede cambiar** porque identifica la cuenta; para usar otro, se crea una cuenta nueva.
- **Contraseña** (`POST /api/cuenta/contrasena`): pide la actual, exige al menos 10 caracteres y cierra las sesiones de los demás dispositivos. Comparte el límite de intentos por IP con el inicio de sesión.
- **Sesiones abiertas**: muestra cuántas hay en otros dispositivos y permite cerrarlas (`POST /api/cuenta/cerrar-sesiones`); la actual sigue abierta.
- **Descargar mis datos** (`GET /api/cuenta/exportar`): un JSON con la cuenta, el consentimiento, la trayectoria, las competencias, las evidencias y las entrevistas (derechos de acceso y portabilidad, arts. 15 y 20 del RGPD). Nunca incluye los resúmenes de la contraseña, de las sesiones ni de los códigos.
- **Eliminar cuenta** (`DELETE /api/cuenta`): pide la contraseña y borra en cascada todos los datos.

### Sistema de diseño

- **Tailwind CSS 4** con una paleta propia (tinta, acento índigo, superficies) definida como variables en `styles.css`.
- Tipografía **Inter** alojada en el propio proyecto (`@fontsource-variable/inter`): no se hacen peticiones a servicios de fuentes externos.
- Iconos **Lucide** (`lucide-angular`).
- Transiciones entre páginas con la View Transitions API del router de Angular y animaciones que respetan `prefers-reduced-motion`.

## Consecuencias

- Los tests de la API de cuenta usan una base de datos PostgreSQL real (`TEST_DATABASE_URL`); la integración continua levanta un servicio de PostgreSQL para ejecutarlos.
- El limitador de peticiones vive en memoria: es suficiente con un único proceso; con varios, habría que moverlo a la base de datos o a Redis.
