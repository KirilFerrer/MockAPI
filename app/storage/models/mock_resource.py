"""Track collection initialization independently of the number of mock items."""
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.storage.database import Base


class MockResource(Base):
    __tablename__ = "mock_resources"

    resource_key: Mapped[str] = mapped_column(String, primary_key=True)
