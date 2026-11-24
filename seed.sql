-- ============================================================
-- ERP-CRM PRACTICA ACADEMICA - DATOS DE PRUEBA (SEED)
-- ============================================================

-- ---------------------- CRM: Clientes ----------------------
INSERT INTO clientes (nombre, empresa, email, telefono, estado) VALUES
  ('Ana García',      'TechVentures SA',   'ana.garcia@techventures.com',   '+52-55-1001',  'activo'),
  ('Carlos López',    'Innovasoft Ltda',   'carlos.lopez@innovasoft.com',   '+52-55-1002',  'activo'),
  ('María Rodríguez', NULL,                'maria.rod@gmail.com',           '+52-55-1003',  'prospecto'),
  ('Jorge Martínez',  'GlobalTrade MX',    'jorge.m@globaltrade.mx',        '+52-55-1004',  'activo'),
  ('Laura Sánchez',   'StartUp Hub',       'laura.s@startuphub.io',         '+52-55-1005',  'inactivo'),
  ('Roberto Silva',   'DataDriven Corp',   'roberto.s@datadriven.com',      '+52-55-1006',  'prospecto');

-- ---------------------- CRM: Interacciones -----------------
INSERT INTO interacciones_crm (cliente_id, tipo, notas, fecha) VALUES
  (1, 'llamada',  'Primera llamada de bienvenida. Interesado en plan Enterprise.', NOW() - INTERVAL '10 days'),
  (1, 'demo',     'Demo del módulo ERP. Muy positiva. Solicita propuesta formal.',  NOW() - INTERVAL '5 days'),
  (2, 'email',    'Envío de catálogo de productos y precios actualizados.',          NOW() - INTERVAL '8 days'),
  (2, 'reunion',  'Reunión presencial. Acuerdan piloto de 3 meses.',                NOW() - INTERVAL '2 days'),
  (3, 'llamada',  'Primer contacto. Prospecto frío, enviar material informativo.',  NOW() - INTERVAL '15 days'),
  (4, 'email',    'Seguimiento post-venta. Cliente satisfecho con la integración.', NOW() - INTERVAL '1 day'),
  (6, 'llamada',  'Contacto inicial. Necesita solución para inventario.',           NOW() - INTERVAL '3 days');

-- ---------------------- ERP: Productos ---------------------
INSERT INTO productos (nombre, descripcion, precio, stock, categoria) VALUES
  ('Laptop ProBook 15',   'Laptop empresarial Intel i7, 16GB RAM, 512GB SSD',   18500.00, 25, 'Computadoras'),
  ('Monitor UltraWide 34','Monitor curvo 34" 3440x1440 IPS, 144Hz',              9800.00, 40, 'Monitores'),
  ('Teclado Mecánico MX', 'Teclado mecánico RGB Cherry MX Red switches',         1850.00, 60, 'Periféricos'),
  ('Mouse Ergonómico Pro','Mouse inalámbrico ergonómico 4000 DPI',                750.00, 80, 'Periféricos'),
  ('Headset Studio 7.1',  'Audífonos gaming surround 7.1, micrófono integrado',  2200.00, 35, 'Audio'),
  ('SSD NVMe 1TB',        'Unidad SSD M.2 NVMe 1TB, 7000MB/s lectura',           2800.00, 50, 'Almacenamiento'),
  ('Router WiFi 6 AX3000','Router doble banda WiFi 6, 3000Mbps, 4 antenas',      3200.00, 20, 'Redes'),
  ('Webcam 4K Pro',       'Cámara web 4K 30fps, autoenfoque, micrófono dual',    1600.00, 45, 'Periféricos');

-- ---------------------- ERP: Venta 1 (cliente Ana García = id 1) -----
-- Se crea la venta primero (total se calcula con trigger)
INSERT INTO ventas (cliente_id, estado) VALUES (1, 'pagada');

-- Detalles de venta 1 (el trigger descuenta stock automáticamente)
INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES
  (1, 1, 1, 18500.00),   -- 1 Laptop ProBook 15
  (1, 3, 2,  1850.00),   -- 2 Teclados Mecánicos
  (1, 4, 2,   750.00);   -- 2 Mouse Ergonómico

-- ---------------------- ERP: Venta 2 (cliente Carlos López = id 2) ---
INSERT INTO ventas (cliente_id, estado) VALUES (2, 'pagada');

INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES
  (2, 2, 2,  9800.00),   -- 2 Monitores UltraWide
  (2, 6, 3,  2800.00);   -- 3 SSD NVMe 1TB

-- ---------------------- ERP: Venta 3 (cliente Jorge Martínez = id 4) -
INSERT INTO ventas (cliente_id, estado) VALUES (4, 'pendiente');

INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES
  (3, 7, 2,  3200.00),   -- 2 Router WiFi 6
  (3, 8, 3,  1600.00);   -- 3 Webcam 4K

-- ============================================================
-- VERIFICACIÓN INMEDIATA DE INTEGRIDAD
-- ============================================================

-- Ver stock después de las ventas (debe reflejar los descuentos)
SELECT
    p.id,
    p.nombre,
    p.categoria,
    p.stock                           AS stock_actual,
    p.precio                          AS precio_unitario,
    COALESCE(SUM(dv.cantidad), 0)     AS total_vendido
FROM productos p
LEFT JOIN detalle_ventas dv ON dv.producto_id = p.id
GROUP BY p.id, p.nombre, p.categoria, p.stock, p.precio
ORDER BY p.id;
