import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VaultItem(Base):
    __tablename__ = "vault_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    website_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(320),
        nullable=True,
    )

    encrypted_password: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    encrypted_notes: Mapped[bytes | None] = mapped_column(
        LargeBinary,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )