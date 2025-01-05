from models import db

with db.engine.connect() as connection:
    connection.execute("DROP TABLE IF EXISTS _alembic_tmp_rounds")