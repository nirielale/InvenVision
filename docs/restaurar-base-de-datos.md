# Restaurar la base de datos de prueba (MySQL Workbench)

El archivo `database/invenvision_backup_compartible.sql` contiene la estructura completa (tablas, claves foráneas y la vista
`vista_productos_estado`), las 9 categorías, un producto y un registro de historial de prueba, y **un usuario de demostración**
(`admin@invenvision.demo`). No contiene datos personales, hashes reales ni secretos.

> **Atención:** el script ejecuta `DROP TABLE IF EXISTS` sobre las tablas de `invenvision` y las recrea. Si ya tiene datos que le
> importan en esa base, **no lo importe encima**: haga un respaldo antes o use otra instancia de MySQL.

## Pasos
1. Abra **MySQL Workbench** y conéctese a su servidor local (por ejemplo `root@localhost:3306`).
2. Menú **Server → Data Import**.
3. Elija **Import from Self-Contained File** y seleccione `database/invenvision_backup_compartible.sql`.
4. En *Default Target Schema* puede dejar vacío: el script crea `invenvision` por sí mismo (`CREATE DATABASE IF NOT EXISTS`).
5. Seleccione **Dump Structure and Data** y pulse **Start Import**. Debe terminar sin errores.
6. Pulse el icono de refrescar en *Schemas* y compruebe que `invenvision` tiene 5 tablas y 1 vista.

Alternativa por consola:
```powershell
& "C:\Program Files\MySQL\MySQL Server 9.3\bin\mysql.exe" -u root -p --default-character-set=utf8mb4 < database\invenvision_backup_compartible.sql
```

## Usuario para la aplicación
La aplicación no debe usar `root`. En Workbench, ejecute (cambiando la clave):
```sql
CREATE USER 'invenvision_app'@'localhost' IDENTIFIED BY 'PON_AQUI_UNA_CLAVE_LARGA';
GRANT SELECT, INSERT, UPDATE, DELETE ON invenvision.* TO 'invenvision_app'@'localhost';
FLUSH PRIVILEGES;
```
Luego copie `.env.example` a `.env` y complete `DB_USER`, `DB_PASSWORD` y `JWT_SECRET`
(`python -c "import secrets; print(secrets.token_hex(32))"`). El `.env` nunca se sube a Git.

## Iniciar sesión
- Correo: `admin@invenvision.demo`
- Contraseña: se la entrega por privado quien compartió el repositorio. **No está en el repositorio.**
  Para fijar una propia: `cd backend; python -m scripts.restablecer_password`.

## Comprobar
```powershell
cd backend
python -m scripts.verificar_esquema      # debe decir: Esquema compatible.
python -m uvicorn app.main:app --reload  # http://127.0.0.1:8000
```
Las imágenes de ejemplo (`productos/1.png`, `scans/...`) no se versionan; la aplicación muestra "Imagen no disponible" y sigue funcionando.
