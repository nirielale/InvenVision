from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

ROOT_DIR = Path(__file__).resolve().parents[2]
JWT_SECRET_MIN = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True
    )

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "invenvision"
    db_user: str = ""
    db_password: str = ""

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    tesseract_cmd: str = ""

    # "development" (por defecto) o "production". En producción: JWT_SECRET obligatorio,
    # sin documentación de la API y sin registro público salvo ALLOW_REGISTRATION=true.
    environment: str = "development"
    allow_registration: bool | None = None
    # Carpeta de fotos y escaneos. Vacío = backend/uploads. En Railway: ruta de un volumen persistente.
    upload_dir: str = ""

    @property
    def es_produccion(self) -> bool:
        return self.environment.strip().lower() in ("production", "prod", "produccion", "producción")

    @property
    def registro_habilitado(self) -> bool:
        """Si no se define ALLOW_REGISTRATION: habilitado en desarrollo, deshabilitado en producción."""
        return self.allow_registration if self.allow_registration is not None else not self.es_produccion

    @property
    def upload_path(self) -> Path:
        if not self.upload_dir.strip():
            return ROOT_DIR / "backend" / "uploads"
        return Path(self.upload_dir.strip()).expanduser().resolve()

    def verificar_produccion(self) -> None:
        """Detiene el arranque (RuntimeError) si la configuración de producción es insegura. No hace nada en desarrollo."""
        if not self.es_produccion:
            return
        if len(self.jwt_secret) < JWT_SECRET_MIN:
            raise RuntimeError(
                f"JWT_SECRET no está definido o es demasiado corto (mínimo {JWT_SECRET_MIN} caracteres). "
                "Defínalo como variable de entorno del servicio; genere uno con: "
                'python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if not self.db_user:
            raise RuntimeError("DB_USER no está definido: configure las variables DB_* de la base de datos.")

    @property
    def database_url(self) -> URL:
        # URL.create escapa caracteres especiales de la contraseña
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        )


settings = Settings()
