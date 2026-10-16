# Defines the table that stores each registered mock endpoint.
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base

if TYPE_CHECKING:
    from app.storage.models.schema import Schema

class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable = True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    schema_id: Mapped[int] = mapped_column(
        ForeignKey("schemas.id")
    )
    schema: Mapped["Schema"] = relationship(
        "Schema",
        back_populates = "endpoints"
    )
