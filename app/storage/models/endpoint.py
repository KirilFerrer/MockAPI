# Define la tabla que guarda cada endpoint mock registrado.
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base

class Endpoint(Base):
    __tablename__ = "endpoints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable = True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    path: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    schema_id: Mapped[int] = mapped_column(
        ForeignKey("schemas.id")
    )
    schema: Mapped["Schema"] = relationship(
        "Schema",
        back_populates = "endpoints"
    )
