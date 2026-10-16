"""Persist collection initialization so deleting the last item does not reseed it."""
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.storage.models.mock_resource import MockResource


def is_resource_initialized(db: Session, resource_key: str) -> bool:
    return db.get(MockResource, resource_key) is not None


def mark_resource_initialized(db: Session, resource_key: str) -> None:
    if not is_resource_initialized(db, resource_key):
        db.add(MockResource(resource_key=resource_key))
        db.commit()


def clear_initialized_resources(db: Session, resource_key: str | None = None) -> None:
    query = delete(MockResource)
    if resource_key is not None:
        query = query.where(MockResource.resource_key == resource_key)
    db.execute(query)
    db.commit()
