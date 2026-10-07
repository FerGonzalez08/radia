from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infraestructura.persistencia.base import Base
from app.infraestructura.persistencia import modelos  # noqa: F401


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option(
    "sqlalchemy.url",
    os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url")),
)
target_metadata = Base.metadata


def ejecutar_migraciones_fuera_de_linea() -> None:
    """Ejecuta migraciones sin establecer una conexión."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def ejecutar_migraciones_en_linea() -> None:
    """Ejecuta migraciones mediante la conexión configurada."""
    configuracion = config.get_section(config.config_ini_section, {})
    conexion = engine_from_config(
        configuracion,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with conexion.connect() as conexion_activa:
        context.configure(connection=conexion_activa, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_migraciones_fuera_de_linea()
else:
    ejecutar_migraciones_en_linea()
