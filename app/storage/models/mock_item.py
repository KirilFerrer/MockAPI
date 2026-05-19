# Define la tabla que guarda items persistidos del runtime mock.
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base


class MockItem(Base):
    __tablename__ = "mock_items"
    __table_args__ = (
        UniqueConstraint("resource_key", "item_id", name="uq_mock_items_resource_item"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    resource_key: Mapped[str] = mapped_column(String, index=True, nullable=False)
    item_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        nullable=False,
    )
