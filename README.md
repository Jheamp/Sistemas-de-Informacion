# ERP-CRM Práctica Académica

Sistema ERP básico con módulo CRM integrado.  
**Stack:** Python 3 · FastAPI · PostgreSQL · HTML5 puro

## Estructura
```
.
├── .env               # Variables de conexión (no subir a Git)
├── requirements.txt   # Dependencias Python
├── schema.sql         # DDL: tablas, índices, triggers
├── seed.sql           # DML: datos de prueba
├── database.py        # Pool de conexiones psycopg3
├── main.py            # API REST FastAPI (todos los endpoints)
├── test_db.py         # Prueba de conexión Python→PostgreSQL
└── static/
    └── index.html     # SPA frontend HTML5+JS
```

## Instalación rápida (Fedora)

```bash
# 1. PostgreSQL
sudo dnf install -y postgresql-server postgresql
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
sudo -u postgres psql -c "CREATE USER erp_user WITH PASSWORD 'erp_pass_2024';"
sudo -u postgres psql -c "CREATE DATABASE erp_crm_db OWNER erp_user;"
sudo -u postgres psql erp_crm_db < schema.sql
sudo -u postgres psql erp_crm_db < seed.sql

# 2. Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Probar conexión
python test_db.py

# 4. Levantar API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints principales
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/dashboard/resumen` | KPIs ejecutivos |
| GET/POST | `/api/clientes` | Gestión de clientes |
| GET/POST | `/api/interacciones` | Seguimiento CRM |
| GET/POST | `/api/productos` | Inventario |
| GET/POST | `/api/ventas` | Ventas |
| POST | `/api/ventas/{id}/detalle` | Ítem + descuento de stock |
| GET | `/docs` | Swagger UI automático |
