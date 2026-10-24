from alembic import context

from common.db.engine import engine

# Kein autogenerate: das Projekt nutzt keine ORM-Modelle, Migrationen werden von Hand geschrieben.
target_metadata = None


def run_migrations_offline():
    context.configure(url=engine.url.render_as_string(hide_password=False), literal_binds=True,
                      target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connection = context.config.attributes.get("connection")
    if connection is not None:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
