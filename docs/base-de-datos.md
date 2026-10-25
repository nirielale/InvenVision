# Base de datos

La base `invenvision` (MySQL 9.3, puerto 3306) **ya existe y la aplicación nunca la crea ni la altera**. Los modelos de
`backend/app/models.py` están alineados con el esquema real, inspeccionado el 2026-10-25 con un usuario dedicado
(`SELECT, INSERT, UPDATE, DELETE` solo sobre `invenvision`). Verificación de solo lectura:

```powershell
cd backend
python -m scripts.verificar_esquema
```

## Esquema real y correspondencia con la API
| Tabla | Columnas reales | Notas |
|---|---|---|
| usuarios | id, nombre, **correo**, password_hash, rol (`administrador`/`operador`), negocio, activo, creado_en | La API expone `correo` como `email` |
| categorias | id, nombre (único) | Sin descripción ni estado: eliminar solo si no tiene productos |
| productos | id, nombre, categoria_id, codigo_barras, lote, **fecha_vencimiento (NOT NULL)**, **stock**, imagen_path, **usuario_id (NOT NULL)**, creado_en, actualizado_en | La API expone `stock` como `cantidad`; el producto queda asignado a quien lo crea |
| historial_deteccion | id, producto_id, imagen_path, texto_detectado_ocr, fecha_detectada, confianza_ocr, fue_corregido_manual, creado_en | Una fila por detección **confirmada**; no guarda estados pendiente/descartada ni usuario |
| configuracion_alertas | id, usuario_id (único), dias_alerta | Configuración **por usuario** (30 días por defecto) |
| vista_productos_estado | (vista) | No se usa: el estado se calcula en `services/expiry.py` |

El usuario de la aplicación no tiene `SHOW VIEW`, por lo que la definición de la vista no se inspeccionó.
Productos con varios lotes: hoy hay un lote por producto.
