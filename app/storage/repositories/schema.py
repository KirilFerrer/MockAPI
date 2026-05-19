# Contiene operaciones de persistencia para schemas.
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.storage.models.schema import Schema


def create_schema(db: Session, schema: Schema):
    db.add(schema)
    db.commit()
    db.refresh(schema)

    return schema


def get_db_schemas(db: Session):
    query = select(Schema).order_by(Schema.created_at.desc(), Schema.id.desc())
    return db.scalars(query).all()


def get_db_schema(db: Session, schema_id: int):
    return db.get(Schema, schema_id)
