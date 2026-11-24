"""
test_db.py — Prueba de conexión a PostgreSQL desde Python
Fase 2: ejecutar con:  python test_db.py
"""

import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DSN = (
    f"host={os.getenv('DB_HOST','localhost')} "
    f"port={os.getenv('DB_PORT','5432')} "
    f"dbname={os.getenv('DB_NAME','erp_crm_db')} "
    f"user={os.getenv('DB_USER','erp_user')} "
    f"password={os.getenv('DB_PASSWORD','')} "
)

SEP = "─" * 55

def seccion(titulo: str):
    print(f"\n{SEP}")
    print(f"  {titulo}")
    print(SEP)

try:
    with psycopg.connect(DSN, row_factory=dict_row) as conn:
        print("\n✅  Conexión a PostgreSQL exitosa!\n")

        # ── 1. Versión de PostgreSQL ─────────────────────────
        seccion("Versión de PostgreSQL")
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            print(" ", cur.fetchone()["version"])

        # ── 2. Clientes ──────────────────────────────────────
        seccion("Clientes (CRM)")
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre, empresa, email, estado FROM clientes ORDER BY id;")
            for row in cur.fetchall():
                print(f"  [{row['id']}] {row['nombre']:<20} | {str(row['empresa']):<18} | {row['estado']}")

        # ── 3. Interacciones por cliente (JOIN) ──────────────
        seccion("Interacciones CRM (JOIN clientes)")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.nombre AS cliente, i.tipo, i.notas, i.fecha::date AS fecha
                FROM   interacciones_crm i
                JOIN   clientes c ON c.id = i.cliente_id
                ORDER  BY i.fecha DESC
                LIMIT  5;
            """)
            for row in cur.fetchall():
                print(f"  {row['cliente']:<20} | {row['tipo']:<10} | {str(row['notas'])[:35]:<35} | {row['fecha']}")

        # ── 4. Productos con stock ───────────────────────────
        seccion("Productos / Inventario (ERP)")
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre, precio, stock, categoria FROM productos ORDER BY id;")
            for row in cur.fetchall():
                print(f"  [{row['id']}] {row['nombre']:<25} | ${row['precio']:>10,.2f} | stock: {row['stock']:>3} | {row['categoria']}")

        # ── 5. Ventas con total calculado por trigger ────────
        seccion("Ventas y totales (trigger calculó el total)")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT v.id, c.nombre AS cliente, v.total, v.estado, v.fecha_venta::date
                FROM   ventas v
                LEFT JOIN clientes c ON c.id = v.cliente_id
                ORDER  BY v.id;
            """)
            for row in cur.fetchall():
                print(f"  Venta #{row['id']} | {str(row['cliente']):<20} | Total: ${row['total']:>10,.2f} | {row['estado']}")

        # ── 6. Detalle de ventas (triple JOIN) ───────────────
        seccion("Detalle de ventas (JOIN ventas+clientes+productos)")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    v.id  AS venta_id,
                    c.nombre AS cliente,
                    p.nombre AS producto,
                    dv.cantidad,
                    dv.precio_unitario,
                    dv.subtotal
                FROM   detalle_ventas dv
                JOIN   ventas    v ON v.id = dv.venta_id
                JOIN   productos p ON p.id = dv.producto_id
                LEFT JOIN clientes c ON c.id = v.cliente_id
                ORDER  BY v.id, dv.id;
            """)
            for row in cur.fetchall():
                print(f"  Venta #{row['venta_id']} | {str(row['cliente']):<18} | {row['producto']:<25} | "
                      f"x{row['cantidad']} @ ${row['precio_unitario']:,.2f} = ${row['subtotal']:,.2f}")

        print(f"\n{SEP}")
        print("  ✅  Todas las consultas ejecutadas con éxito.")
        print(f"{SEP}\n")

except psycopg.OperationalError as e:
    print(f"\n❌  Error de conexión: {e}")
    raise
