# Define la tabla que guarda definiciones JSON de schemas.
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.storage.database import Base

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
