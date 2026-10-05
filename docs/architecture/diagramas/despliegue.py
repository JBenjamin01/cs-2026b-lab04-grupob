# Vista de despliegue — San Camilo en Línea (ver ADR-001, ADR-002 y ADR-003)
import os
from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.client import Users
from diagrams.generic.device import Mobile
from diagrams.generic.storage import Storage
from diagrams.onprem.network import Nginx, Internet
from diagrams.programming.framework import Django
from diagrams.onprem.database import PostgreSQL
from diagrams.onprem.inmemory import Redis
from diagrams.onprem.queue import Celery
from diagrams.onprem.monitoring import Grafana

os.makedirs("img", exist_ok=True)

graph_attr = {"fontsize": "22", "bgcolor": "white", "pad": "0.5", "nodesep": "0.8", "ranksep": "1.1"}

with Diagram("San Camilo en Línea - Vista de despliegue", filename="img/despliegue",
             show=False, direction="LR", graph_attr=graph_attr, outformat="png"):

    with Cluster("Usuarios"):
        clientes = Users("Clientes")
        comerciantes = Users("Comerciantes")
        repartidores = Users("Repartidores")

    movil = Mobile("PWA offline-first\ncelular gama baja (3G)\nservice worker + IndexedDB")

    with Cluster("VPS único (2 vCPU / 4 GB RAM) - servicios con systemd"):
        proxy = Nginx("Nginx\nHTTPS + archivos estáticos")

        with Cluster("Monolito modular (Django)"):
            app = Django("Django + Gunicorn\ncatálogo · pedidos · pagos\nnotificaciones · reparto")
            worker = Celery("Celery worker\nenvío con reintentos")
            beat = Celery("Celery beat\nreencola pendientes\ncada 5 min")

        redis = Redis("Redis\ncaché del catálogo\n+ broker de tareas")
        db = PostgreSQL("PostgreSQL\nun esquema por módulo\n+ notificaciones pendientes")
        mon = Grafana("Monitoreo\nalerta si no responde")

    with Cluster("Servicios externos"):
        pagos = Internet("Proveedor de pagos\n(cobro con Yape)")
        whatsapp = Internet("WhatsApp\nBusiness Platform")
        respaldo = Storage("Respaldo externo\npg_dump diario")

    # Usuarios -> aplicación
    [clientes, comerciantes, repartidores] >> movil
    movil >> Edge(label="HTTPS + clave de idempotencia") >> proxy >> app

    # Aplicación -> datos y caché
    app >> Edge(label="SQL: pago + notificación\nen una transacción") >> db
    app >> Edge(label="caché + encola envío") >> redis

    # Procesamiento asíncrono (patrón outbox)
    redis >> Edge(label="entrega tarea") >> worker
    beat >> Edge(label="programa reintento", style="dashed") >> redis
    worker >> Edge(label="lee pendientes /\nmarca enviada") >> db

    # Integraciones externas
    worker >> Edge(label="confirmación al comerciante", style="dashed") >> whatsapp
    app >> Edge(label="solicitud de cobro", style="dashed") >> pagos
    pagos >> Edge(label="webhook idempotente", style="dashed") >> proxy

    # Operación
    db >> Edge(label="cron diario", style="dotted") >> respaldo
    mon >> Edge(label="verifica salud", style="dotted") >> proxy
