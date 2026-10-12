# ADR-004: Los puertos entre módulos usan tipos neutrales para evitar dependencias cíclicas

- Estado: Aceptado
- Fecha: 2026-10-11
- Decisores: Jhonatan Benjamin Mamani Céspedes, Jafet Martin Llave Aguilar
- Relacionado con: ADR-001 (monolito modular, puertos y adaptadores), Lab 05 (E1, E5 y E7)

## Contexto

Al revisar el primer borrador del diagrama de clases del Laboratorio 05 con la regla C4, se
encontraron dos ciclos entre paquetes:

1. `NotificadorMensajeria.notificarComerciante(subpedido: PedidoPuesto, comerciante: Comerciante)`:
   el puerto vive en `notificaciones`, pero recibía una clase de `pedidos`. Como `pedidos` usa el
   puerto, quedaba `pedidos → notificaciones → pedidos`.
2. La asociación navegable `Pedido → Repartidor`: `reparto` ya depende de `pedidos` para consultar
   los pedidos, por lo que quedaba `pedidos → reparto → pedidos`.

ADR-001 exige que los módulos se comuniquen solo por interfaces públicas y que no se importen
modelos de otro módulo. Un ciclo hace que los dos módulos se comporten como uno solo y rompe la
posibilidad de extraer Notificaciones en el futuro (la primera candidata, según el Lab 04).

## Alternativas consideradas

1. **Mover el puerto a `pedidos`** (el consumidor es dueño del puerto, estilo hexagonal estricto).
   Elimina el ciclo, pero contradice la convención ya fijada en el Lab 04 (cada módulo expone su
   `services.py`) y obliga a `notificaciones` a depender de `pedidos`.
2. **Crear un DTO compartido en `comun`** (`MensajeComerciante`). Funciona, pero agrega una clase
   que hoy solo tendría dos campos.
3. **Firmas con tipos neutrales** (`UUID`, `Decimal`, `String`) en los puertos, y asociaciones
   navegables solo en el sentido permitido. Elegida.

## Decisión

- Los puertos de `pagos` y `notificaciones` reciben solo tipos neutrales:
  `notificarComerciante(celular: String, resumen: String)`,
  `iniciarCobro(pedidoId: UUID, monto: Decimal, celular: String, codigoAprobacion: String)`.
- `Pago` guarda `pedidoId: UUID`, no una referencia a `Pedido`.
- La asociación con el repartidor es navegable solo desde `reparto`
  (`Repartidor "0..1" --> "0..*" Pedido`). Desde `pedidos` solo se conoce el `repartidorId`
  que llega como parámetro de `marcarRecogido()`.
- El orden permitido queda: `reparto → pedidos → {catalogo, pagos, notificaciones} → comun`.
  Se agrega un contrato `layers` de import-linter con ese orden.

## Consecuencias

- **Positivas:** el grafo de paquetes es acíclico (verificado con `pyreverse` sobre `src/`);
  Notificaciones y Pagos pueden extraerse sin tocar `pedidos`; los adaptadores se prueban sin
  construir objetos de dominio de otro módulo.
- **Negativas:** el servicio de pedidos debe armar el texto del resumen antes de llamar al puerto;
  si el mensaje crece (plantillas de WhatsApp con muchos campos), convendrá pasar a la
  alternativa 2 (DTO en `comun`).
