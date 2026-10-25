# Base de datos

## Esquema real: pendiente de inspección
La base `invenvision` ya existe (tablas `usuarios`, `categorias`, `productos`, `historial_deteccion`, `configuracion_alertas` y la vista
`vista_productos_estado`). Los archivos de la base están en el MySQL de XAMPP (`C:\xampp\mysql\data\invenvision`, puerto 3307 según su `my.ini`).

Para exportar solo la estructura (no modifica nada y no incluye datos):
```powershell
& "C:\xampp\mysql\bin\mysqldump.exe" -h 127.0.0.1 -P 3307 -u TU_USUARIO -p --no-data --routines invenvision > database\schema.sql
```
(`-p` sin valor pide la contraseña por teclado.)

## Modelo que asume el backend (`backend/app/models.py`) — PROPUESTA no contrastada
| Tabla | Columnas |
|---|---|
| usuarios | id, nombre, email (único), password_hash, rol (`admin`/`operador`), activo, creado_en |
| categorias | id, nombre (único), descripcion, activa, creado_en |
| productos | id, nombre, sku (único), categoria_id → categorias, marca, lote, cantidad, precio_costo, proveedor, fecha_vencimiento, imagen, creado_en, actualizado_en |
| historial_deteccion | id, producto_id → productos (SET NULL), usuario_id → usuarios, imagen, texto_ocr, fecha_detectada, resultado, confirmada, creado_en |
| configuracion_alertas | id, dias_alerta |

Cuando se tenga `schema.sql`, se compararán columna por columna. Cualquier diferencia se resolverá ajustando los modelos o con una migración
**aditiva** (`ALTER TABLE ... ADD COLUMN`) que se mostrará antes de ejecutarse. No se eliminarán tablas ni datos.
Productos con varios lotes: hoy hay un lote por producto; manejar múltiples lotes requeriría una tabla adicional (no implementada).
