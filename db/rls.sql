-- Lab 08, iteración 2 de ADD (QA-05, ADR-007): aislamiento entre mercados con Row-Level Security.
-- Se aplica como migración de Django (RunSQL) sobre cada tabla que tiene la columna mercado_id.
-- El rol de la aplicación NO es dueño de las tablas ni tiene BYPASSRLS: las políticas siempre se aplican.

CREATE ROLE app_sancamilo NOLOGIN NOSUPERUSER NOBYPASSRLS;   -- en producción: LOGIN con contraseña en el .env

CREATE SCHEMA IF NOT EXISTS pedidos;                           -- un esquema por módulo (ADR-002)
CREATE TABLE pedidos.pedido (
    id              bigserial PRIMARY KEY,
    mercado_id      text        NOT NULL,                      -- código del mercado (ADR-006)
    numero_puesto   text        NOT NULL,
    celular_cliente text        NOT NULL,
    total           numeric(10,2) NOT NULL,
    creado          timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX pedido_mercado_creado ON pedidos.pedido (mercado_id, creado DESC);   -- QA-04 con 3 mercados

ALTER TABLE pedidos.pedido ENABLE ROW LEVEL SECURITY;
ALTER TABLE pedidos.pedido FORCE ROW LEVEL SECURITY;           -- también para el dueño de la tabla

-- Sin la variable app.mercado_id, current_setting(..., true) devuelve NULL y la consulta no ve
-- ninguna fila: si alguien olvida fijar el mercado, el sistema falla CERRADO, no abierto.
CREATE POLICY aislamiento_por_mercado ON pedidos.pedido
    USING      (mercado_id = current_setting('app.mercado_id', true))
    WITH CHECK (mercado_id = current_setting('app.mercado_id', true));

GRANT USAGE ON SCHEMA pedidos TO app_sancamilo;
GRANT SELECT, INSERT, UPDATE ON pedidos.pedido TO app_sancamilo;
GRANT USAGE ON SEQUENCE pedidos.pedido_id_seq TO app_sancamilo;

-- En cada petición, un middleware de Django abre la transacción y fija el mercado del token:
--   SET LOCAL ROLE app_sancamilo;
--   SELECT set_config('app.mercado_id', <claim "mercado" del token>, true);   -- true = solo esta transacción
