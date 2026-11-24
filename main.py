"""
main.py — API REST ERP-CRM con FastAPI + psycopg3 (SQL puro)
=============================================================
Endpoints:
  CRM:
    GET/POST        /api/clientes
    GET/PUT/DELETE  /api/clientes/{id}
    GET/POST        /api/interacciones
    GET             /api/interacciones/{cliente_id}

  ERP:
    GET/POST        /api/productos
    GET/PUT/DELETE  /api/productos/{id}
    GET/POST        /api/ventas
    GET             /api/ventas/{id}
    POST            /api/ventas/{id}/detalle   ← descuenta stock (transacción)

  Dashboard:
    GET             /api/dashboard/resumen
"""

import os
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, field_validator
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()

# ─────────────────────────── Pool ────────────────────────────
DSN = (
    f"host={os.getenv('DB_HOST','localhost')} "
    f"port={os.getenv('DB_PORT','5432')} "
    f"dbname={os.getenv('DB_NAME','erp_crm_db')} "
    f"user={os.getenv('DB_USER','erp_user')} "
    f"password={os.getenv('DB_PASSWORD','')} "
)

pool: ConnectionPool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = ConnectionPool(conninfo=DSN, min_size=2, max_size=10,
                          kwargs={"row_factory": dict_row})
    yield
    pool.close()


app = FastAPI(
    title="ERP-CRM API",
    description="Sistema ERP básico con módulo CRM integrado — Práctica Académica",
    version="1.0.0",
    lifespan=lifespan,
)

# ─────────────────────────── Helper ──────────────────────────
def db():
    return pool.connection()


def not_found(entity: str, id: int):
    raise HTTPException(status_code=404, detail=f"{entity} con id={id} no encontrado.")


# ══════════════════════════════════════════════════════════════
# MODELOS PYDANTIC
# ══════════════════════════════════════════════════════════════

class ClienteIn(BaseModel):
    nombre: str
    empresa: Optional[str] = None
    email: str
    telefono: Optional[str] = None
    estado: str = "prospecto"

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        if v not in ("prospecto", "activo", "inactivo"):
            raise ValueError("estado debe ser prospecto, activo o inactivo")
        return v


class InteraccionIn(BaseModel):
    cliente_id: int
    tipo: str
    notas: Optional[str] = None

    @field_validator("tipo")
    @classmethod
    def validar_tipo(cls, v):
        if v not in ("llamada", "email", "reunion", "demo", "otro"):
            raise ValueError("tipo inválido")
        return v


class ProductoIn(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    stock: int = 0
    categoria: Optional[str] = None


class VentaIn(BaseModel):
    cliente_id: Optional[int] = None
    estado: str = "pendiente"


class DetalleVentaIn(BaseModel):
    producto_id: int
    cantidad: int
    precio_unitario: float


# ══════════════════════════════════════════════════════════════
# CRM — CLIENTES
# ══════════════════════════════════════════════════════════════

@app.get("/api/clientes", tags=["CRM"])
def listar_clientes(estado: Optional[str] = None):
    with db() as conn, conn.cursor() as cur:
        if estado:
            cur.execute(
                "SELECT * FROM clientes WHERE estado = %s ORDER BY nombre;",
                (estado,)
            )
        else:
            cur.execute("SELECT * FROM clientes ORDER BY nombre;")
        return cur.fetchall()


@app.post("/api/clientes", tags=["CRM"], status_code=201)
def crear_cliente(data: ClienteIn):
    with db() as conn, conn.cursor() as cur:
        try:
            cur.execute(
                """INSERT INTO clientes (nombre, empresa, email, telefono, estado)
                   VALUES (%s, %s, %s, %s, %s) RETURNING *;""",
                (data.nombre, data.empresa, data.email, data.telefono, data.estado)
            )
            conn.commit()
            return cur.fetchone()
        except psycopg.errors.UniqueViolation:
            raise HTTPException(409, f"Ya existe un cliente con el email {data.email}")


@app.get("/api/clientes/{id}", tags=["CRM"])
def obtener_cliente(id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM clientes WHERE id = %s;", (id,))
        row = cur.fetchone()
        if not row:
            not_found("Cliente", id)
        return row


@app.put("/api/clientes/{id}", tags=["CRM"])
def actualizar_cliente(id: int, data: ClienteIn):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """UPDATE clientes
               SET nombre=%s, empresa=%s, email=%s, telefono=%s, estado=%s
               WHERE id=%s RETURNING *;""",
            (data.nombre, data.empresa, data.email, data.telefono, data.estado, id)
        )
        row = cur.fetchone()
        if not row:
            not_found("Cliente", id)
        conn.commit()
        return row


@app.delete("/api/clientes/{id}", tags=["CRM"], status_code=204)
def eliminar_cliente(id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM clientes WHERE id=%s RETURNING id;", (id,))
        if not cur.fetchone():
            not_found("Cliente", id)
        conn.commit()


# ══════════════════════════════════════════════════════════════
# CRM — INTERACCIONES
# ══════════════════════════════════════════════════════════════

@app.get("/api/interacciones", tags=["CRM"])
def listar_interacciones():
    with db() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT i.*, c.nombre AS cliente_nombre
            FROM   interacciones_crm i
            JOIN   clientes c ON c.id = i.cliente_id
            ORDER  BY i.fecha DESC;
        """)
        return cur.fetchall()


@app.get("/api/interacciones/{cliente_id}", tags=["CRM"])
def interacciones_de_cliente(cliente_id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT i.*, c.nombre AS cliente_nombre
            FROM   interacciones_crm i
            JOIN   clientes c ON c.id = i.cliente_id
            WHERE  i.cliente_id = %s
            ORDER  BY i.fecha DESC;
        """, (cliente_id,))
        return cur.fetchall()


@app.post("/api/interacciones", tags=["CRM"], status_code=201)
def crear_interaccion(data: InteraccionIn):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO interacciones_crm (cliente_id, tipo, notas)
               VALUES (%s, %s, %s) RETURNING *;""",
            (data.cliente_id, data.tipo, data.notas)
        )
        conn.commit()
        return cur.fetchone()


# ══════════════════════════════════════════════════════════════
# ERP — PRODUCTOS
# ══════════════════════════════════════════════════════════════

@app.get("/api/productos", tags=["ERP"])
def listar_productos(categoria: Optional[str] = None):
    with db() as conn, conn.cursor() as cur:
        if categoria:
            cur.execute(
                "SELECT * FROM productos WHERE categoria = %s ORDER BY nombre;",
                (categoria,)
            )
        else:
            cur.execute("SELECT * FROM productos ORDER BY nombre;")
        return cur.fetchall()


@app.post("/api/productos", tags=["ERP"], status_code=201)
def crear_producto(data: ProductoIn):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """INSERT INTO productos (nombre, descripcion, precio, stock, categoria)
               VALUES (%s, %s, %s, %s, %s) RETURNING *;""",
            (data.nombre, data.descripcion, data.precio, data.stock, data.categoria)
        )
        conn.commit()
        return cur.fetchone()


@app.get("/api/productos/{id}", tags=["ERP"])
def obtener_producto(id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("SELECT * FROM productos WHERE id=%s;", (id,))
        row = cur.fetchone()
        if not row:
            not_found("Producto", id)
        return row


@app.put("/api/productos/{id}", tags=["ERP"])
def actualizar_producto(id: int, data: ProductoIn):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            """UPDATE productos
               SET nombre=%s, descripcion=%s, precio=%s, stock=%s, categoria=%s
               WHERE id=%s RETURNING *;""",
            (data.nombre, data.descripcion, data.precio, data.stock, data.categoria, id)
        )
        row = cur.fetchone()
        if not row:
            not_found("Producto", id)
        conn.commit()
        return row


@app.delete("/api/productos/{id}", tags=["ERP"], status_code=204)
def eliminar_producto(id: int):
    with db() as conn, conn.cursor() as cur:
        cur.execute("DELETE FROM productos WHERE id=%s RETURNING id;", (id,))
        if not cur.fetchone():
            not_found("Producto", id)
        conn.commit()


# ══════════════════════════════════════════════════════════════
# ERP — VENTAS
# ══════════════════════════════════════════════════════════════

@app.get("/api/ventas", tags=["ERP"])
def listar_ventas():
    with db() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT v.*, c.nombre AS cliente_nombre
            FROM   ventas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            ORDER  BY v.fecha_venta DESC;
        """)
        return cur.fetchall()


@app.post("/api/ventas", tags=["ERP"], status_code=201)
def crear_venta(data: VentaIn):
    with db() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ventas (cliente_id, estado) VALUES (%s, %s) RETURNING *;",
            (data.cliente_id, data.estado)
        )
        conn.commit()
        return cur.fetchone()


@app.get("/api/ventas/{id}", tags=["ERP"])
def obtener_venta(id: int):
    with db() as conn, conn.cursor() as cur:
        # Cabecera
        cur.execute("""
            SELECT v.*, c.nombre AS cliente_nombre
            FROM   ventas v
            LEFT JOIN clientes c ON c.id = v.cliente_id
            WHERE  v.id = %s;
        """, (id,))
        venta = cur.fetchone()
        if not venta:
            not_found("Venta", id)
        # Detalles
        cur.execute("""
            SELECT dv.*, p.nombre AS producto_nombre
            FROM   detalle_ventas dv
            JOIN   productos p ON p.id = dv.producto_id
            WHERE  dv.venta_id = %s
            ORDER  BY dv.id;
        """, (id,))
        venta["detalles"] = cur.fetchall()
        return venta


@app.post("/api/ventas/{id}/detalle", tags=["ERP"], status_code=201)
def agregar_detalle_venta(id: int, data: DetalleVentaIn):
    """
    Agrega un ítem a una venta existente.
    El TRIGGER fn_descontar_stock descuenta el stock automáticamente
    y lanza una excepción si el stock es insuficiente.
    """
    with db() as conn, conn.cursor() as cur:
        # Verificar que la venta existe
        cur.execute("SELECT id FROM ventas WHERE id=%s;", (id,))
        if not cur.fetchone():
            not_found("Venta", id)
        try:
            cur.execute(
                """INSERT INTO detalle_ventas
                     (venta_id, producto_id, cantidad, precio_unitario)
                   VALUES (%s, %s, %s, %s) RETURNING *;""",
                (id, data.producto_id, data.cantidad, data.precio_unitario)
            )
            detalle = cur.fetchone()
            conn.commit()
            return detalle
        except psycopg.errors.RaiseException as e:
            conn.rollback()
            raise HTTPException(status_code=409, detail=str(e))
        except psycopg.errors.CheckViolation as e:
            conn.rollback()
            raise HTTPException(status_code=422, detail="Stock insuficiente o cantidad inválida.")


# ══════════════════════════════════════════════════════════════
# DASHBOARD — RESUMEN EJECUTIVO
# ══════════════════════════════════════════════════════════════

@app.get("/api/dashboard/resumen", tags=["Dashboard"])
def resumen_dashboard():
    with db() as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT
                (SELECT COUNT(*)                        FROM clientes)             AS total_clientes,
                (SELECT COUNT(*) FROM clientes WHERE estado='activo')              AS clientes_activos,
                (SELECT COUNT(*) FROM clientes WHERE estado='prospecto')           AS prospectos,
                (SELECT COUNT(*)                        FROM productos)            AS total_productos,
                (SELECT COALESCE(SUM(stock),0)          FROM productos)            AS unidades_en_stock,
                (SELECT COUNT(*)                        FROM ventas)               AS total_ventas,
                (SELECT COALESCE(SUM(total),0) FROM ventas WHERE estado='pagada') AS ingresos_pagados,
                (SELECT COUNT(*)                        FROM interacciones_crm)   AS total_interacciones;
        """)
        return cur.fetchone()


# ══════════════════════════════════════════════════════════════
# FRONTEND — Servir index.html estático
# ══════════════════════════════════════════════════════════════

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return FileResponse("static/index.html")
