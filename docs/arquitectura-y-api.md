# Arquitectura, API y flujo OCR

## Arquitectura
```
Navegador (frontend/, módulos ES + Bootstrap + Chart.js)
   │  fetch /api/*  (JWT en cabecera Authorization)
FastAPI (backend/app)
   ├─ routers/   auth, users, categories, products, scan, reports
   ├─ services/  expiry (estados), date_parser (fechas), vision (OpenCV + Tesseract)
   ├─ models.py / schemas.py / security.py / config.py / database.py
   └─ SQLAlchemy ──► MySQL `invenvision`
Archivos subidos: backend/uploads/ (ignorado por Git)
```

## Endpoints (Swagger completo en `/docs`)
| Área | Endpoints | Acceso |
|---|---|---|
| Auth | `POST /api/auth/login`, `POST /api/auth/register`, `GET/PUT /api/auth/me`, `POST /api/auth/cambiar-password` | público (login/registro) / autenticado |
| Usuarios | `GET/POST /api/usuarios`, `PUT /api/usuarios/{id}` | admin |
| Categorías | `GET /api/categorias` · `POST/PUT/DELETE` (DELETE = desactivar) | autenticado · admin |
| Productos | `GET/POST /api/productos`, `GET/PUT /api/productos/{id}`, `PATCH .../stock`, `GET .../detecciones`, `POST/GET .../foto` | autenticado |
| | `DELETE /api/productos/{id}` | admin |
| OCR | `GET /api/ocr/estado`, `POST /api/scan`, `POST /api/scan/{id}/confirmar`, `POST /api/scan/{id}/descartar` | autenticado |
| Historial | `GET /api/historial`, `GET /api/historial/{id}/imagen` | autenticado |
| Alertas | `GET /api/alertas`, `GET /api/config-alertas` · `PUT /api/config-alertas` | autenticado · admin |
| Reportes | `GET /api/dashboard`, `GET /api/estadisticas` | autenticado |
| Sistema | `GET /api/health` | público |

## Estados de vencimiento
`dias = fecha_vencimiento − hoy`. `dias < 0` → **vencido**; `0 ≤ dias ≤ umbral` → **por vencer**; `dias > umbral` → **vigente**;
sin fecha → **sin_fecha**. El día de vencimiento todavía cuenta como «por vencer». El umbral (por defecto 30) se guarda en
`configuracion_alertas`. Las consultas SQL (`filtro_estado`) y el cálculo en Python (`clasificar`) viven juntos en `services/expiry.py`.

## Flujo OCR
1. `POST /api/scan`: valida tamaño (≤ 8 MB), formato real por firma (JPEG/PNG/WEBP) y dimensiones; preprocesa (grises, ampliación,
   reducción de ruido, CLAHE, umbral adaptativo); lee con Tesseract (`spa+eng`).
2. `date_parser` extrae fechas candidatas con su texto de origen; clasifica cada una como vencimiento / fabricación / sin etiqueta
   según la palabra que la precede (`VENC`, `EXP`, `CAD`… frente a `FAB`, `ELAB`, `ENV`…); marca las ambiguas.
3. Se crea una detección **pendiente**. Solo se sugiere una fecha si hay exactamente una de vencimiento y no es ambigua.
4. `POST /api/scan/{id}/confirmar`: el usuario confirma o corrige; solo entonces se escribe la fecha en el producto
   (`confirmada` si coincide con una fecha leída, `corregida` si la escribió el usuario). `.../descartar` la rechaza.
5. Imágenes ilegibles se registran como `ilegible`; nunca se inventa una fecha.

## Seguridad
Contraseñas con bcrypt; JWT firmado con `JWT_SECRET`; mensajes de login genéricos; las rutas de archivos subidos se validan contra
salida del directorio; el orden de listados usa una lista blanca de columnas; la salida de la API no incluye hashes.
