# Defines the table that stores JSON schema definitions.
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base

if TYPE_CHECKING:
    from app.storage.models.endpoint import Endpoint

class Schema(Base):
    __tablename__ = "schemas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )

    endpoints: Mapped[list["Endpoint"]] = relationship(
        "Endpoint",
        back_populates = "schema"
    )
