workspace "San Camilo en Línea" "Modelo C4 de la plataforma de pedidos del Mercado San Camilo (Arequipa)" {

    !identifiers hierarchical

    model {
        // ---------- Personas (drivers.md, Lab 04) ----------
        cliente = person "Cliente" "Compra productos de varios puestos del Mercado San Camilo en un solo pedido, con recojo o delivery."
        comerciante = person "Comerciante" "Dueño o encargado de un puesto; publica sus productos y atiende su parte de cada pedido."
        repartidor = person "Repartidor" "Recoge los productos en los puestos y los entrega al cliente."

        // ---------- Sistema propio ----------
        sc = softwareSystem "San Camilo en Línea" "Permite pedir a varios puestos del mercado en un solo pedido y pagarlo una sola vez con Yape." {

            // ---------- Contenedores (ADR-001, ADR-002, ADR-003; despliegue.py del Lab 04) ----------
            pwa = container "PWA offline-first" "Interfaz de cliente, comerciante y repartidor. Publica un producto en 3 toques y guarda las acciones sin conexión para sincronizarlas después." "Plantillas Django + JavaScript, Service Worker, IndexedDB" "Web Browser"
            api = container "API San Camilo" "Monolito modular con 5 módulos de dominio; expone los casos de uso y los webhooks." "Python / Django + Gunicorn" {
                // ---------- Componentes = paquetes de docs/design/paquetes.puml (el paquete comun solo tiene tipos base y no se modela) ----------
                catalogo = component "Módulo Catálogo" "Publica productos, gestiona la disponibilidad y reserva o libera stock." "Django app"
                pedidos = component "Módulo Pedidos" "Arma el pedido multipuesto, lo confirma y controla los estados del pedido y de cada subpedido." "Django app"
                pagos = component "Módulo Pagos" "Cobra con Yape mediante el puerto PasarelaPago y guarda el estado del pago." "Django app"
                notificaciones = component "Módulo Notificaciones" "Registra los avisos pendientes a los comerciantes (patrón outbox) mediante el puerto de mensajería." "Django app"
                reparto = component "Módulo Reparto" "Asigna pedidos a repartidores, arma la lista de puestos y registra las entregas." "Django app"
            }
            worker = container "Worker de notificaciones" "Envía los avisos pendientes a WhatsApp con reintentos y espera creciente." "Celery"
            beat = container "Planificador" "Reencola cada 5 min los avisos pendientes y cancela los pedidos sin pago a los 15 min." "Celery beat"
            cola = container "Cola y caché" "Broker de tareas de Celery y caché del catálogo." "Redis" "Queue"
            db = container "Base de datos" "Una base con un esquema por módulo; guarda pedidos, pagos y avisos pendientes en una sola transacción." "PostgreSQL" "Database"
        }

        // ---------- Sistemas externos ----------
        pasarela = softwareSystem "Proveedor de pagos" "Procesa el cobro con Yape; Yape no ofrece una API pública abierta (R-05)." "Externo"
        whatsapp = softwareSystem "WhatsApp Business Platform" "Entrega al comerciante la confirmación de su parte del pedido (plantillas aprobadas)." "Externo"

        // ---------- Relaciones nivel 1 ----------
        cliente -> sc "Arma pedidos con productos de varios puestos y los paga con Yape"
        comerciante -> sc "Publica sus productos y marca cuáles se agotaron"
        repartidor -> sc "Consulta los puestos a recorrer y marca las entregas"
        sc -> pasarela "Solicita el cobro del pedido" "HTTPS/JSON"
        pasarela -> sc "Notifica el resultado del cobro" "HTTPS/JSON"
        sc -> whatsapp "Envía la confirmación de cada subpedido" "HTTPS/JSON"
        whatsapp -> comerciante "Entrega el aviso del pedido en su WhatsApp"

        // ---------- Relaciones nivel 2 ----------
        cliente -> sc.pwa "Explora el catálogo, arma su pedido y paga" "HTTPS"
        comerciante -> sc.pwa "Publica productos y marca agotados, incluso sin conexión" "HTTPS"
        repartidor -> sc.pwa "Consulta su ruta y marca entregas" "HTTPS"
        sc.pwa -> sc.api "Envía solicitudes y sincroniza las acciones guardadas" "HTTPS/JSON (con clave de idempotencia)"
        sc.api -> sc.db "Lee y escribe en el esquema de cada módulo" "SQL/TCP"
        sc.api -> sc.cola "Cachea el catálogo y encola los envíos" "Redis protocol"
        sc.worker -> sc.cola "Consume las tareas de envío" "Redis protocol"
        sc.worker -> sc.db "Lee los avisos pendientes y los marca como enviados" "SQL/TCP"
        sc.beat -> sc.cola "Programa los reintentos cada 5 minutos" "Redis protocol"
        sc.worker -> whatsapp "Envía la confirmación al comerciante" "HTTPS/JSON"
        sc.api -> pasarela "Solicita el cobro" "HTTPS/JSON"
        pasarela -> sc.api "Notifica el resultado del cobro (webhook idempotente)" "HTTPS/JSON"

        // ---------- Relaciones nivel 3 (sin ciclos: reparto -> pedidos -> {catalogo, pagos, notificaciones}) ----------
        sc.pwa -> sc.api.catalogo "Consulta el catálogo y publica productos" "HTTPS/JSON"
        sc.pwa -> sc.api.pedidos "Arma, confirma y consulta pedidos" "HTTPS/JSON"
        sc.pwa -> sc.api.reparto "Consulta la ruta y marca entregas" "HTTPS/JSON"
        sc.api.reparto -> sc.api.pedidos "Consulta pedidos y marca subpedidos como recogidos"
        sc.api.pedidos -> sc.api.catalogo "Reserva y libera stock"
        sc.api.pedidos -> sc.api.pagos "Solicita el cobro mediante el puerto PasarelaPago"
        sc.api.pedidos -> sc.api.notificaciones "Pide avisar al comerciante mediante el puerto NotificadorMensajeria"
        sc.api.pagos -> pasarela "Cobra con Yape (adaptador)" "HTTPS/JSON"
        pasarela -> sc.api.pedidos "Notifica el resultado del cobro (webhook idempotente)" "HTTPS/JSON"
        sc.api.catalogo -> sc.db "Lee y escribe el esquema catalogo" "SQL"
        sc.api.pedidos -> sc.db "Lee y escribe el esquema pedidos" "SQL"
        sc.api.pagos -> sc.db "Lee y escribe el esquema pagos" "SQL"
        sc.api.notificaciones -> sc.db "Guarda el aviso pendiente (outbox) en el esquema notificaciones" "SQL"
        sc.api.reparto -> sc.db "Lee y escribe el esquema reparto" "SQL"
        sc.api.catalogo -> sc.cola "Cachea el catálogo" "Redis protocol"
        sc.api.notificaciones -> sc.cola "Encola el envío" "Redis protocol"
    }

    views {
        systemContext sc "Contexto" "Nivel 1: San Camilo en Línea y su entorno." {
            include *
            autolayout lr
        }
        container sc "Contenedores" "Nivel 2: contenedores de San Camilo en Línea." {
            include *
            autolayout lr
        }
        component sc.api "Componentes" "Nivel 3: módulos de la API (coinciden con docs/design/paquetes.puml)." {
            include *
            autolayout lr
        }

        styles {
            element "Person" {
                shape person
                background #08427B
                color #ffffff
            }
            element "Software System" {
                background #1168BD
                color #ffffff
            }
            element "Externo" {
                background #999999
            }
            element "Container" {
                background #438DD5
                color #ffffff
            }
            element "Component" {
                background #85BBF0
                color #000000
            }
            element "Database" {
                shape cylinder
            }
            element "Queue" {
                shape pipe
            }
            element "Web Browser" {
                shape WebBrowser
            }
        }
    }
}
