from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VaultItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=150)
    website_url: str | None = Field(default=None, max_length=2048)
    username: str | None = Field(default=None, max_length=320)
    password: str = Field(min_length=1)
    notes: str | None = None


class VaultItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=150)
    website_url: str | None = Field(default=None, max_length=2048)
    username: str | None = Field(default=None, max_length=320)
    password: str | None = Field(default=None, min_length=1)
    notes: str | None = None


class VaultItemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    website_url: str | None
    username: str | None
    created_at: datetime
    updated_at: datetime


class VaultItemDetail(VaultItemSummary):
    password: str
    notes: str | None