# Round-trip: diseño ↔ código (E6)

## 1. Ingeniería directa

Se adaptó el Prompt IA 2 de la guía al diagrama `clases.puml` (ver `bitacora-ia.md`, interacción 6) y se
generó el esqueleto en Python 3.10+ (dataclasses, type hints, `Enum` y `ABC`), separado por módulo:

| Archivo | Contenido |
|---------|-----------|
| `src/pedidos/dominio.py` | `Cliente`, `Pedido`, `PedidoPuesto`, `LineaPedido` y sus enumeraciones |
| `src/pedidos/puertos.py` | `RepositorioPedidos` (puerto de persistencia) |
| `src/pedidos/servicio.py` | `ServicioPedidos` (orquesta el flujo del diagrama de secuencia) |
| `src/catalogo/modelos.py` | `Comerciante`, `Producto` |
| `src/pagos/modelos.py` | `Pago`, `EstadoPago`, `PasarelaPago`, `YapeAdapter` |
| `src/notificaciones/puertos.py` | `NotificadorMensajeria`, `WhatsAppAdapter` |
| `src/reparto/modelos.py` | `Repartidor` |
| `src/comun/excepciones.py` | `ReglaNegocioError`, `EstadoInvalidoError` |

Revisión humana del código generado: se exigió que cada operación de `PedidoPuesto` valide el estado de
origen (si no, lanza `EstadoInvalidoError`), que `confirmar()` exija al menos un subpedido (C3) y que
libere lo ya reservado si una reserva falla. Los adaptadores lanzan `NotImplementedError`.

Pruebas: `python -m pytest -q tests` → **15 pruebas aprobadas** (7 transiciones válidas y 4 inválidas de
la máquina de estados, 3 pruebas de los criterios CA-1, CA-2 y CA-3 con dobles de los puertos, y 1 del webhook duplicado).

## 2. Ingeniería inversa

```bash
pip install pylint
cd src
pyreverse -o puml -p pedidos pedidos                                            # clases del módulo
pyreverse -o puml -p sancamilo comun catalogo pagos notificaciones pedidos reparto  # paquetes
java -jar plantuml.jar -tpng classes_pedidos.puml packages_sancamilo.puml
```

Resultados versionados: `classes_pedidos_pyreverse.puml` (img/classes_pedidos.png) y
`packages_sancamilo_pyreverse.puml` (img/packages_sancamilo.png).

## 3. Diferencias entre el diagrama de diseño y el obtenido del código

| # | Diferencia observada | Causa | Acción |
|---|----------------------|-------|--------|
| 1 | No aparecen las composiciones `Pedido *-- PedidoPuesto` ni `PedidoPuesto *-- LineaPedido`; figuran como atributos `subpedidos: list[PedidoPuesto]` y `lineas: list[LineaPedido]`. | pyreverse no infiere asociaciones desde colecciones tipadas, y Python no distingue composición de agregación. | Documentar la limitación; el diagrama de diseño se mantiene como fuente de verdad. |
| 2 | No hay multiplicidades (`1..*`, `0..1`). | Los tipos de Python no expresan cardinalidades. | Corregir el código: `confirmar()` lanza `ReglaNegocioError` si el pedido no tiene subpedidos (C3); cubierto por las pruebas. |
| 3 | `Pedido → Cliente` aparece como asociación dirigida (atributo `cliente`), mientras el diseño tenía `Cliente "1" -- "0..*" Pedido` sin dirección. | El código solo navega de Pedido a Cliente; ningún caso de uso pide la lista de pedidos de un cliente. | Corregir el diagrama: `Pedido "0..*" --> "1" Cliente`. Lo mismo para `Producto "0..*" --> "1" Comerciante`. |
| 4 | `ServicioPedidos` aparece sin atributos ni dependencias hacia `RepositorioPedidos`, `PasarelaPago` y `NotificadorMensajeria`. | Las dependencias se inyectan en atributos privados (`_repositorio`…), que pyreverse oculta por defecto (filtro `PUB_ONLY`). | Documentar; con `pyreverse -f ALL` se ven los atributos. Las dependencias `..>` siguen en el diseño. |
| 5 | `RepositorioPedidos` (y `PasarelaPago`, `NotificadorMensajeria`) aparecen como clases con métodos abstractos, sin estereotipo `<<puerto>>`. | Python implementa interfaces con `abc.ABC`; el estereotipo es una decisión de arquitectura que no existe en el lenguaje. | Aceptable en Python; se documenta la equivalencia puerto = clase abstracta. |
| 6 | Algunos atributos pierden su tipo (`cantidad`, `precio_unitario`, `costo_envio`, `estado`). | pyreverse solo muestra el tipo cuando lo infiere; con anotaciones `Decimal` o un `Enum` como valor por defecto no lo muestra (se comprobó con una clase mínima de prueba). | Limitación de la herramienta; los type hints siguen en el código y el diseño conserva los tipos. |
| 7 | Todos los atributos aparecen públicos; en el diseño son privados (`-`). Los nombres están en snake_case. | Python no tiene modificadores de acceso reales; PEP 8 usa snake_case. | Documentar la equivalencia de nombres `calcularTotal() = calcular_total()` (C5); los cambios de estado solo se hacen mediante métodos. |
| 8 | El primer esqueleto importaba `catalogo.modelos` y `pagos.modelos` desde `pedidos`; el diagrama de paquetes de pyreverse lo mostraba como flechas hacia módulos internos de otro paquete. | ADR-001 exige que ningún módulo importe los modelos internos de otro, solo su interfaz pública; la IA generó imports directos. | Corregir el código: cada módulo expone su interfaz en `__init__.py` (`from catalogo import Producto`) y se regeneró el diagrama de paquetes. |

## 4. Verificación de C4 desde el código

El diagrama de paquetes obtenido del código (`img/packages_sancamilo.png`) confirma las dependencias del
diseño: `reparto → pedidos → {catalogo, pagos, notificaciones} → comun`. Ni `pagos` ni `notificaciones`
importan nada de `pedidos`, por lo que no hay ciclos (ADR-004), y desde fuera de un módulo solo se importa
su paquete (interfaz pública), nunca `modelos.py`.
