-- ============================================================
-- ERP-CRM PRACTICA ACADEMICA - ESQUEMA DE BASE DE DATOS
-- Base de datos: erp_crm_db
-- Motor: PostgreSQL 16+
-- ============================================================

-- Limpiar si existe (útil en re-ejecuciones)
DROP TABLE IF EXISTS detalle_ventas CASCADE;
DROP TABLE IF EXISTS ventas        CASCADE;
DROP TABLE IF EXISTS interacciones_crm CASCADE;
DROP TABLE IF EXISTS clientes      CASCADE;
DROP TABLE IF EXISTS productos     CASCADE;

-- ============================================================
-- MÓDULO CRM
-- ============================================================

CREATE TABLE clientes (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    empresa         VARCHAR(120),
    email           VARCHAR(120) UNIQUE NOT NULL,
    telefono        VARCHAR(30),
    estado          VARCHAR(20) NOT NULL DEFAULT 'prospecto'
                    CHECK (estado IN ('prospecto','activo','inactivo')),
    fecha_registro  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE interacciones_crm (
    id              SERIAL PRIMARY KEY,
    cliente_id      INTEGER NOT NULL REFERENCES clientes(id) ON DELETE CASCADE,
    tipo            VARCHAR(30) NOT NULL
                    CHECK (tipo IN ('llamada','email','reunion','demo','otro')),
    notas           TEXT,
    fecha           TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ============================================================
-- MÓDULO ERP
-- ============================================================

CREATE TABLE productos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(120) NOT NULL,
    descripcion     TEXT,
    precio          NUMERIC(12,2) NOT NULL CHECK (precio >= 0),
    stock           INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),
    categoria       VARCHAR(60),
    fecha_creacion  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE ventas (
    id              SERIAL PRIMARY KEY,
    cliente_id      INTEGER REFERENCES clientes(id) ON DELETE SET NULL,
    total           NUMERIC(14,2) NOT NULL DEFAULT 0,
    estado          VARCHAR(20) NOT NULL DEFAULT 'pendiente'
                    CHECK (estado IN ('pendiente','pagada','cancelada')),
    fecha_venta     TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE detalle_ventas (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id     INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(12,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal        NUMERIC(14,2) GENERATED ALWAYS AS (cantidad * precio_unitario) STORED
);

-- ============================================================
-- ÍNDICES DE RENDIMIENTO
-- ============================================================

CREATE INDEX idx_interacciones_cliente ON interacciones_crm(cliente_id);
CREATE INDEX idx_detalle_venta         ON detalle_ventas(venta_id);
CREATE INDEX idx_detalle_producto      ON detalle_ventas(producto_id);
CREATE INDEX idx_ventas_cliente        ON ventas(cliente_id);
CREATE INDEX idx_clientes_email        ON clientes(email);

-- ============================================================
-- FUNCIÓN + TRIGGER: Descuento de stock automático al insertar
-- detalle_ventas. Lanza error si stock resultante < 0.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_descontar_stock()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE productos
    SET    stock = stock - NEW.cantidad
    WHERE  id    = NEW.producto_id;

    -- Verificar que el stock no quedó negativo
    IF (SELECT stock FROM productos WHERE id = NEW.producto_id) < 0 THEN
        RAISE EXCEPTION 'Stock insuficiente para el producto id=% (solicitado: %)',
              NEW.producto_id, NEW.cantidad;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_descontar_stock
    AFTER INSERT ON detalle_ventas
    FOR EACH ROW EXECUTE FUNCTION fn_descontar_stock();

-- ============================================================
-- FUNCIÓN + TRIGGER: Recalcula el total de la venta al insertar
-- o borrar un detalle.
-- ============================================================

CREATE OR REPLACE FUNCTION fn_actualizar_total_venta()
RETURNS TRIGGER AS $$
DECLARE
    v_id INTEGER;
BEGIN
    v_id := COALESCE(NEW.venta_id, OLD.venta_id);
    UPDATE ventas
    SET    total = (
        SELECT COALESCE(SUM(subtotal), 0)
        FROM   detalle_ventas
        WHERE  venta_id = v_id
    )
    WHERE id = v_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_total_venta
    AFTER INSERT OR DELETE ON detalle_ventas
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_total_venta();

-- Confirmación visual
SELECT 'Schema ERP-CRM creado exitosamente.' AS resultado;
