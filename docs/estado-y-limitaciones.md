# Estado real y limitaciones

## Verificado (pruebas automáticas, SQLite en memoria)
- Autenticación JWT + bcrypt, registro, cambio de contraseña, roles (admin / operador), usuario inactivo bloqueado.
- CRUD de productos y categorías, búsqueda, filtros por estado/categoría, orden, paginación, ajuste de stock.
- Estados vencido / por vencer / vigente / sin fecha calculados en un único lugar (`services/expiry.py`), con umbral configurable.
- Validación de imágenes, extracción de fechas candidatas, distinción vencimiento/fabricación, fechas ambiguas, flujo de confirmación y descarte.
- Dashboard, alertas y estadísticas con datos de la base.
- El servidor sirve el frontend y las rutas `/api` no se pisan.

## NO verificado
1. **Conexión real a MySQL**: aún no hay `.env` probado ni se ha ejecutado la API contra `invenvision`.
2. **Esquema real**: `models.py` es una propuesta. Las columnas reales de `usuarios`, `productos`, `historial_deteccion`,
   `configuracion_alertas` y la vista `vista_productos_estado` no se han contrastado; puede requerir ajustes o una migración
   (que se propondrá antes de ejecutarse). Tampoco se verificó cómo está guardado el hash del administrador existente.
3. **OCR con Tesseract**: no está instalado en el equipo de desarrollo; las pruebas del flujo usan un OCR simulado.
   No hay ninguna cifra de precisión. Use `ml/evaluar_ocr.py` con fotos reales etiquetadas para medirla.
4. **Interfaz en navegador**: los módulos JavaScript pasan la comprobación de sintaxis y se sirven correctamente, pero no se ha
   recorrido la interfaz en un navegador real (ni la cámara, ni los gráficos, ni el diseño responsive).

## Limitaciones conocidas
- Fechas con etiqueta en la línea anterior (`VENC:` arriba, fecha abajo) se clasifican como «sin etiqueta».
- Errores típicos de OCR (`O` por `0`, `l` por `1`) no se corrigen automáticamente.
- Fechas `DD/MM` con ambos valores ≤ 12 se asumen día-mes y se marcan como ambiguas (nunca se sugieren).
- Las alertas se muestran dentro de la aplicación; no se envían correos ni mensajes (no hay servicio externo configurado).
- El registro público crea usuarios con rol *operador*; solo un administrador puede crear otros administradores.
- El selector de producto del escáner muestra los primeros 100 productos.
- No hay protección contra fuerza bruta en el login ni HTTPS: pensado para uso local.
- La «evolución del inventario» usa la fecha de registro de los productos actuales; no es un historial de movimientos.
- Chart.js, Bootstrap e iconos se cargan desde CDN (requiere Internet en el navegador).
