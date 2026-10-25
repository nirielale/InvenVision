# Estado real y limitaciones

## Verificado (pruebas automáticas, SQLite en memoria)
- Autenticación JWT + bcrypt, registro, cambio de contraseña, roles (admin / operador), usuario inactivo bloqueado.
- CRUD de productos y categorías, búsqueda, filtros por estado/categoría, orden, paginación, ajuste de stock.
- Estados vencido / por vencer / vigente / sin fecha calculados en un único lugar (`services/expiry.py`), con umbral configurable.
- Validación de imágenes, extracción de fechas candidatas, distinción vencimiento/fabricación, fechas ambiguas, flujo de confirmación y descarte.
- Dashboard, alertas y estadísticas con datos de la base.
- El servidor sirve el frontend y las rutas `/api` no se pisan.

## Verificado contra MySQL real (solo lecturas, 2026-10-25)
- Conexión con `invenvision` y `/api/health`; `scripts.verificar_esquema` confirma que modelos y columnas coinciden.
- Los endpoints GET (perfil, categorías, productos, dashboard, alertas, estadísticas, historial, usuarios) responden 200 con el usuario existente.
- No se escribió nada en la base real: las escrituras (crear producto, confirmar escaneo) solo se probaron con SQLite.

## NO verificado
1. **Inicio de sesión real**: se desconoce la contraseña del administrador existente; el hash es bcrypt (`$2b$`), compatible con el backend.
2. **OCR con Tesseract**: no está instalado en el equipo; las pruebas del flujo usan un OCR simulado. No hay cifra de precisión.
   Use `ml/evaluar_ocr.py` con fotos reales etiquetadas para medirla.
3. **Interfaz en navegador**: los módulos JavaScript pasan la comprobación de sintaxis y se sirven bien, pero no se recorrió la interfaz
   (cámara, gráficos, diseño responsive) en un navegador real.

## Limitaciones conocidas
- Fechas con etiqueta en la línea anterior (`VENC:` arriba, fecha abajo) se clasifican como «sin etiqueta».
- Errores típicos de OCR (`O` por `0`, `l` por `1`) no se corrigen automáticamente.
- Fechas `DD/MM` con ambos valores ≤ 12 se asumen día-mes y se marcan como ambiguas (nunca se sugieren).
- Las alertas se muestran dentro de la aplicación; no se envían correos ni mensajes (no hay servicio externo configurado).
- El registro público crea usuarios con rol *operador*; solo un administrador puede crear otros administradores.
- El esquema real exige fecha de vencimiento en todo producto y no guarda precio, marca, proveedor ni SKU; esos campos se eliminaron de la API.
- Un escaneo no confirmado vive solo como archivos en `backend/uploads/scans`; no hay registro en MySQL hasta confirmar.
- El selector de producto del escáner muestra los primeros 100 productos.
- No hay protección contra fuerza bruta en el login ni HTTPS: pensado para uso local.
- La «evolución del inventario» usa la fecha de registro de los productos actuales; no es un historial de movimientos.
- Chart.js, Bootstrap e iconos se cargan desde CDN (requiere Internet en el navegador).
