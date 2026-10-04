# ADR-003: Construir el frontend como PWA offline-first

- Estado: Aceptado
- Fecha: 2026-10-04
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar

## Contexto

El atributo crítico del caso es que un comerciante con poca experiencia digital publique un
producto en ≤ 3 toques desde un celular de gama baja (QA-01, RF-01). Los comerciantes trabajan
dentro del mercado con 3G intermitente, y sus publicaciones o cambios de disponibilidad no
pueden perderse (QA-02, RF-06). Usan celulares Android con poca RAM y poco almacenamiento
(R-06). El equipo tiene 1 mes (R-01) y domina Python/Django, no desarrollo móvil nativo (R-02).

En una prueba previa, un flujo que abría la cámara como paso obligatorio sumó 5 toques: la
cámara nativa de Android pide confirmar la foto. Por eso tomar la foto no puede ser parte del
camino mínimo.

## Alternativas consideradas

1. **App nativa Android (Kotlin):** el mejor acceso a la cámara y al almacenamiento, pero el
   equipo no domina Kotlin, se requiere publicar en Play Store y el comerciante debe instalar
   la app.
2. **Web responsive sin soporte offline:** la más rápida de construir, pero incumple QA-02:
   sin señal, la publicación se pierde.
3. **Publicación mediante un bot de WhatsApp:** el comerciante ya conoce WhatsApp, pero los
   flujos conversacionales son complejos de construir en 1 mes y los mensajes tienen costo.
   Queda como evolución futura.
4. **PWA offline-first:** elegida.

## Decisión

Construiremos una PWA ligera con plantillas Django y JavaScript mínimo, sin framework pesado.

1. **Flujo de publicación en 3 toques:** (1) "+ Producto" → (2) tocar el producto en una lista
   predefinida de su rubro, con foto de referencia y el último precio usado → (3) "Publicar".
   Tomar una foto propia o editar el precio son opcionales y quedan fuera del camino mínimo.
2. **Funcionamiento sin conexión:**
   - El service worker guarda en caché la interfaz y el último catálogo consultado.
   - Las acciones del comerciante (publicar, marcar agotado) se guardan en una cola local en
     IndexedDB, cada una con un UUID generado en el celular para que el servidor descarte
     duplicados.
3. **Sincronización:** se intenta al recuperar la conexión y al abrir la app. Background Sync
   se usa donde esté disponible (Chrome en Android). Cada acción muestra su estado:
   *pendiente*, *enviado* o *error, reintentar*.
4. **Imágenes:** cuando el comerciante sube una foto propia, se reduce en el celular a un
   máximo de 1280 px por lado (≈ 200 KB). Si la reducción falla, se sube la original y el
   servidor la reduce en segundo plano.
5. **Degradación progresiva:** si el service worker o el JavaScript fallan (p. ej., en un
   navegador antiguo), los formularios siguen funcionando como HTML estándar, con
   `<input type="file" accept="image/*" capture="environment">` para la foto.
6. **Interfaz:** botones grandes, íconos acompañados de texto y lenguaje simple.

## Consecuencias

- **Positivas:**
  - Cumple QA-01 y QA-02 sin tienda de aplicaciones.
  - Un solo código para los 3 actores, en la tecnología que el equipo domina.
  - Liviana para celulares de gama baja.
  - Sigue siendo usable aunque el navegador no soporte funciones avanzadas.
- **Negativas / riesgos:**
  - Hay que preparar la lista predefinida de productos típicos del mercado, con sus fotos de
    referencia; es un costo de contenido que no es código.
  - iOS Safari no soporta Background Sync y puede borrar los datos locales si la app no se usa
    por varios días. Se mitiga sincronizando al abrir la app (los comerciantes usan mayormente
    Android).
  - Pueden surgir conflictos si se edita sin conexión (p. ej., el precio). Se resuelven con
    "gana la última edición" según la marca de tiempo.
  - Se requieren pruebas en celulares de gama baja reales, no solo en el emulador.